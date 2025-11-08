"""
Route Connector - Finds interconnected routes for multi-leg journeys
"""
from typing import List, Dict, Tuple, Optional
from app.db.mongodb import mongodb
from app.external.google_maps_client import google_maps_client
from math import radians, sin, cos, sqrt, atan2


class RouteConnector:
    """Find connecting routes for seamless multi-leg journeys"""
    
    def find_interconnected_routes(
        self,
        current_lat: float,
        current_lng: float,
        final_dest_lat: float,
        final_dest_lng: float,
        max_transfer_distance_km: float = 0.5
    ) -> List[Dict]:
        """
        Find routes that connect from current location to final destination
        
        Args:
            current_lat: Current location latitude
            current_lng: Current location longitude
            final_dest_lat: Final destination latitude
            final_dest_lng: Final destination longitude
            max_transfer_distance_km: Maximum walking distance for transfers
            
        Returns:
            List of route combinations with transfer points
        """
        routes_collection = mongodb.get_collection("routes")
        schedules_collection = mongodb.get_collection("schedules")
        
        # Get all active routes
        all_routes = list(routes_collection.find({"status": "active"}))
        
        if not all_routes:
            return []
        
        # Find direct routes (no transfer needed)
        direct_routes = self._find_direct_routes(
            all_routes, 
            current_lat, 
            current_lng, 
            final_dest_lat, 
            final_dest_lng,
            max_transfer_distance_km
        )
        
        # Find routes with one transfer
        transfer_routes = self._find_transfer_routes(
            all_routes,
            current_lat,
            current_lng,
            final_dest_lat,
            final_dest_lng,
            max_transfer_distance_km
        )
        
        # Combine and sort by total distance
        all_options = direct_routes + transfer_routes
        all_options.sort(key=lambda x: x.get('total_distance_km', float('inf')))
        
        # Enrich with schedule information
        for option in all_options:
            for leg in option.get('legs', []):
                route_id = leg.get('route_id')
                schedule = schedules_collection.find_one({"route_id": route_id, "active": True})
                if schedule:
                    leg['departure_times'] = schedule.get('departure_times', [])
                    leg['frequency_min'] = schedule.get('frequency_min', 10)
        
        return all_options[:5]  # Return top 5 options
    
    def _find_direct_routes(
        self,
        all_routes: List[Dict],
        current_lat: float,
        current_lng: float,
        dest_lat: float,
        dest_lng: float,
        max_distance_km: float
    ) -> List[Dict]:
        """Find routes that go directly from current location to destination"""
        direct_options = []
        
        for route in all_routes:
            waypoints = route.get('waypoints', [])
            if not waypoints or len(waypoints) < 2:
                continue
            
            # Check if route passes near current location and destination
            boarding_point = self._find_nearest_point_on_route(
                waypoints, 
                current_lat, 
                current_lng
            )
            
            alighting_point = self._find_nearest_point_on_route(
                waypoints,
                dest_lat,
                dest_lng
            )
            
            if not boarding_point or not alighting_point:
                continue
            
            # Check if distances are within acceptable range
            boarding_distance = self._haversine_distance(
                (current_lat, current_lng),
                (boarding_point['lat'], boarding_point['lng'])
            )
            
            alighting_distance = self._haversine_distance(
                (dest_lat, dest_lng),
                (alighting_point['lat'], alighting_point['lng'])
            )
            
            if boarding_distance <= max_distance_km and alighting_distance <= max_distance_km:
                # Ensure boarding comes before alighting
                if boarding_point['index'] < alighting_point['index']:
                    leg_distance = self._calculate_route_segment_distance(
                        waypoints,
                        boarding_point['index'],
                        alighting_point['index']
                    )
                    
                    direct_options.append({
                        'type': 'direct',
                        'total_legs': 1,
                        'total_distance_km': leg_distance,
                        'total_transfers': 0,
                        'legs': [{
                            'route_id': route.get('route_id'),
                            'route_name': route.get('name'),
                            'boarding_point': {
                                'name': self._get_location_name(boarding_point['lat'], boarding_point['lng']),
                                'lat': boarding_point['lat'],
                                'lng': boarding_point['lng'],
                                'walk_distance_km': round(boarding_distance, 2)
                            },
                            'alighting_point': {
                                'name': self._get_location_name(alighting_point['lat'], alighting_point['lng']),
                                'lat': alighting_point['lat'],
                                'lng': alighting_point['lng'],
                                'walk_distance_km': round(alighting_distance, 2)
                            },
                            'distance_km': round(leg_distance, 2)
                        }]
                    })
        
        return direct_options
    
    def _find_transfer_routes(
        self,
        all_routes: List[Dict],
        current_lat: float,
        current_lng: float,
        dest_lat: float,
        dest_lng: float,
        max_distance_km: float
    ) -> List[Dict]:
        """Find routes with one transfer"""
        transfer_options = []
        
        # Try combinations of two routes
        for i, route1 in enumerate(all_routes):
            waypoints1 = route1.get('waypoints', [])
            if not waypoints1:
                continue
            
            # Find boarding point on route 1
            boarding_point = self._find_nearest_point_on_route(
                waypoints1,
                current_lat,
                current_lng
            )
            
            if not boarding_point:
                continue
            
            boarding_distance = self._haversine_distance(
                (current_lat, current_lng),
                (boarding_point['lat'], boarding_point['lng'])
            )
            
            if boarding_distance > max_distance_km:
                continue
            
            # Find potential transfer points on route 1
            for j, route2 in enumerate(all_routes):
                if i == j:  # Skip same route
                    continue
                
                waypoints2 = route2.get('waypoints', [])
                if not waypoints2:
                    continue
                
                # Find transfer point (where routes intersect or come close)
                transfer_point = self._find_transfer_point(waypoints1, waypoints2, max_distance_km)
                
                if not transfer_point:
                    continue
                
                # Find alighting point on route 2
                alighting_point = self._find_nearest_point_on_route(
                    waypoints2,
                    dest_lat,
                    dest_lng
                )
                
                if not alighting_point:
                    continue
                
                alighting_distance = self._haversine_distance(
                    (dest_lat, dest_lng),
                    (alighting_point['lat'], alighting_point['lng'])
                )
                
                if alighting_distance > max_distance_km:
                    continue
                
                # Calculate distances for both legs
                leg1_distance = self._calculate_route_segment_distance(
                    waypoints1,
                    boarding_point['index'],
                    transfer_point['route1_index']
                )
                
                leg2_distance = self._calculate_route_segment_distance(
                    waypoints2,
                    transfer_point['route2_index'],
                    alighting_point['index']
                )
                
                total_distance = leg1_distance + leg2_distance
                
                transfer_options.append({
                    'type': 'transfer',
                    'total_legs': 2,
                    'total_distance_km': round(total_distance, 2),
                    'total_transfers': 1,
                    'legs': [
                        {
                            'route_id': route1.get('route_id'),
                            'route_name': route1.get('name'),
                            'boarding_point': {
                                'name': self._get_location_name(boarding_point['lat'], boarding_point['lng']),
                                'lat': boarding_point['lat'],
                                'lng': boarding_point['lng'],
                                'walk_distance_km': round(boarding_distance, 2)
                            },
                            'alighting_point': {
                                'name': self._get_location_name(transfer_point['lat'], transfer_point['lng']),
                                'lat': transfer_point['lat'],
                                'lng': transfer_point['lng'],
                                'walk_distance_km': 0.0
                            },
                            'distance_km': round(leg1_distance, 2)
                        },
                        {
                            'route_id': route2.get('route_id'),
                            'route_name': route2.get('name'),
                            'boarding_point': {
                                'name': self._get_location_name(transfer_point['lat'], transfer_point['lng']),
                                'lat': transfer_point['lat'],
                                'lng': transfer_point['lng'],
                                'walk_distance_km': round(transfer_point['transfer_walk_km'], 2)
                            },
                            'alighting_point': {
                                'name': self._get_location_name(alighting_point['lat'], alighting_point['lng']),
                                'lat': alighting_point['lat'],
                                'lng': alighting_point['lng'],
                                'walk_distance_km': round(alighting_distance, 2)
                            },
                            'distance_km': round(leg2_distance, 2)
                        }
                    ]
                })
        
        return transfer_options
    
    def _find_nearest_point_on_route(
        self,
        waypoints: List[List[float]],
        lat: float,
        lng: float
    ) -> Optional[Dict]:
        """Find the nearest point on a route to given coordinates"""
        if not waypoints:
            return None
        
        min_distance = float('inf')
        nearest_point = None
        nearest_index = -1
        
        for i, wp in enumerate(waypoints):
            if len(wp) < 2:
                continue
            
            wp_lat, wp_lng = wp[0], wp[1]
            distance = self._haversine_distance((lat, lng), (wp_lat, wp_lng))
            
            if distance < min_distance:
                min_distance = distance
                nearest_point = {'lat': wp_lat, 'lng': wp_lng}
                nearest_index = i
        
        if nearest_point:
            nearest_point['index'] = nearest_index
            return nearest_point
        
        return None
    
    def _find_transfer_point(
        self,
        waypoints1: List[List[float]],
        waypoints2: List[List[float]],
        max_distance_km: float
    ) -> Optional[Dict]:
        """Find a transfer point between two routes"""
        for i, wp1 in enumerate(waypoints1):
            if len(wp1) < 2:
                continue
            
            for j, wp2 in enumerate(waypoints2):
                if len(wp2) < 2:
                    continue
                
                distance = self._haversine_distance(
                    (wp1[0], wp1[1]),
                    (wp2[0], wp2[1])
                )
                
                if distance <= max_distance_km:
                    # Use midpoint as transfer location
                    mid_lat = (wp1[0] + wp2[0]) / 2
                    mid_lng = (wp1[1] + wp2[1]) / 2
                    
                    return {
                        'lat': mid_lat,
                        'lng': mid_lng,
                        'route1_index': i,
                        'route2_index': j,
                        'transfer_walk_km': distance
                    }
        
        return None
    
    def _haversine_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in km"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        R = 6371  # Earth's radius in km
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _calculate_route_segment_distance(
        self,
        waypoints: List[List[float]],
        start_index: int,
        end_index: int
    ) -> float:
        """Calculate distance of a route segment"""
        if start_index >= end_index or end_index >= len(waypoints):
            return 0.0
        
        total_distance = 0.0
        for i in range(start_index, end_index):
            if i + 1 < len(waypoints):
                total_distance += self._haversine_distance(
                    (waypoints[i][0], waypoints[i][1]),
                    (waypoints[i+1][0], waypoints[i+1][1])
                )
        
        return total_distance
    
    def _get_location_name(self, lat: float, lng: float) -> str:
        """Get location name from coordinates"""
        try:
            result = google_maps_client.reverse_geocode(lat, lng)
            if result and len(result) > 0:
                formatted = result[0].get('formatted_address', '')
                return formatted.split(',')[0] if formatted else f"{lat:.4f}, {lng:.4f}"
        except:
            pass
        return f"{lat:.4f}, {lng:.4f}"


# Singleton instance
route_connector = RouteConnector()

