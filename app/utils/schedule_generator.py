"""
Schedule Generator - Creates detailed stop-level schedules with timing
"""
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from app.external.google_maps_client import google_maps_client


class ScheduleGenerator:
    """Generate detailed schedules with stop-level timing"""
    
    def generate_intermediate_stops(
        self, 
        waypoints: List[Tuple[float, float]], 
        total_duration_min: int,
        num_stops: int = 10
    ) -> List[Dict]:
        """
        Generate intermediate stops along a route with ETAs
        
        Args:
            waypoints: List of (lat, lng) coordinates along the route
            total_duration_min: Total route duration
            num_stops: Number of intermediate stops to generate
            
        Returns:
            List of stops with name, location, and timing
        """
        if len(waypoints) < 2:
            return []
        
        stops = []
        total_points = len(waypoints)
        
        # Calculate interval for stop placement
        interval = max(1, total_points // (num_stops + 1))
        
        cumulative_distance = 0.0
        cumulative_time = 0
        
        for i in range(0, total_points, interval):
            if i >= total_points:
                break
                
            lat, lng = waypoints[i]
            
            # Get location name using reverse geocoding
            location_name = self._get_location_name(lat, lng)
            
            # Calculate distance from start
            if i > 0:
                prev_lat, prev_lng = waypoints[i - interval] if i >= interval else waypoints[0]
                segment_distance = self._calculate_distance(
                    (prev_lat, prev_lng), 
                    (lat, lng)
                )
                cumulative_distance += segment_distance
                
                # Estimate time proportionally
                cumulative_time = int(
                    (cumulative_distance / self._total_route_distance(waypoints)) * total_duration_min
                )
            
            stops.append({
                "name": location_name,
                "lat": lat,
                "lng": lng,
                "sequence": len(stops),
                "distance_from_start_km": round(cumulative_distance, 2),
                "estimated_time_from_start_min": cumulative_time
            })
            
            if len(stops) >= num_stops:
                break
        
        # Always add the final destination
        if waypoints:
            final_lat, final_lng = waypoints[-1]
            final_name = self._get_location_name(final_lat, final_lng)
            
            stops.append({
                "name": final_name,
                "lat": final_lat,
                "lng": final_lng,
                "sequence": len(stops),
                "distance_from_start_km": round(
                    self._total_route_distance(waypoints), 2
                ),
                "estimated_time_from_start_min": total_duration_min
            })
        
        return stops
    
    def generate_stop_timings(
        self,
        intermediate_stops: List[Dict],
        start_time: str,
        dwell_time_min: int = 2
    ) -> List[Dict]:
        """
        Generate arrival/departure times for each stop
        
        Args:
            intermediate_stops: List of stops with ETAs from start
            start_time: Starting time in HH:MM format
            dwell_time_min: Time bus stays at each stop
            
        Returns:
            List of stops with arrival and departure times
        """
        stop_timings = []
        
        # Parse start time
        start_hour, start_min = map(int, start_time.split(':'))
        base_time = datetime.now().replace(
            hour=start_hour, 
            minute=start_min, 
            second=0, 
            microsecond=0
        )
        
        for stop in intermediate_stops:
            eta_min = stop.get("estimated_time_from_start_min", 0)
            
            arrival_time = base_time + timedelta(minutes=eta_min)
            departure_time = arrival_time + timedelta(minutes=dwell_time_min)
            
            stop_timings.append({
                "stop_name": stop["name"],
                "stop_lat": stop["lat"],
                "stop_lng": stop["lng"],
                "arrival_time": arrival_time.strftime("%H:%M"),
                "departure_time": departure_time.strftime("%H:%M")
            })
        
        return stop_timings
    
    def generate_multi_bus_schedules(
        self,
        route_id: str,
        num_buses: int,
        frequency_min: int,
        start_time: str,
        end_time: str,
        intermediate_stops: List[Dict]
    ) -> List[Dict]:
        """
        Generate schedules for multiple buses on the same route
        
        Args:
            route_id: Route identifier
            num_buses: Number of buses to deploy
            frequency_min: Minutes between bus departures
            start_time: First bus departure time
            end_time: Last bus departure time
            intermediate_stops: Stops along the route
            
        Returns:
            List of bus schedules with timings
        """
        schedules = []
        
        # Parse times
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        start_dt = datetime.now().replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        end_dt = datetime.now().replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        # Calculate offset between buses
        offset_min = frequency_min
        
        for bus_num in range(num_buses):
            bus_start_time = start_dt + timedelta(minutes=bus_num * offset_min)
            
            # Generate departure times for this bus throughout the day
            departure_times = []
            current_time = bus_start_time
            
            while current_time <= end_dt:
                departure_times.append(current_time.strftime("%H:%M"))
                # Add frequency interval for next trip
                current_time += timedelta(minutes=frequency_min * num_buses)
            
            # Generate stop timings for first departure
            stop_timings = self.generate_stop_timings(
                intermediate_stops,
                bus_start_time.strftime("%H:%M")
            )
            
            schedules.append({
                "bus_instance_id": f"{route_id}-B{bus_num + 1}",
                "deployment_sequence": bus_num + 1,
                "schedule_offset_min": bus_num * offset_min,
                "departure_times": departure_times,
                "stop_timings": stop_timings,
                "total_trips": len(departure_times)
            })
        
        return schedules
    
    def _get_location_name(self, lat: float, lng: float) -> str:
        """Get human-readable location name from coordinates"""
        try:
            result = google_maps_client.reverse_geocode(lat, lng)
            if result and len(result) > 0:
                # Try to get a meaningful name from address components
                address_components = result[0].get('address_components', [])

                # Priority order: neighborhood > sublocality_level_1 > sublocality > locality
                priority_types = [
                    'neighborhood',
                    'sublocality_level_1',
                    'sublocality_level_2',
                    'sublocality',
                    'locality',
                    'administrative_area_level_2'
                ]

                for priority_type in priority_types:
                    for component in address_components:
                        types = component.get('types', [])
                        if priority_type in types:
                            place_name = component.get('long_name', '')
                            if place_name and place_name.strip():
                                print(f"✅ Found place name: {place_name} for ({lat:.4f}, {lng:.4f})")
                                return place_name

                # Fallback to formatted address (first part)
                formatted = result[0].get('formatted_address', '')
                if formatted:
                    # Get first meaningful part before comma
                    parts = formatted.split(',')
                    if parts and parts[0].strip():
                        place_name = parts[0].strip()
                        print(f"✅ Using formatted address: {place_name} for ({lat:.4f}, {lng:.4f})")
                        return place_name

                print(f"⚠️ No meaningful name found, using coordinates for ({lat:.4f}, {lng:.4f})")
        except Exception as e:
            print(f"❌ Error getting location name for ({lat:.4f}, {lng:.4f}): {e}")

        return f"Stop at {lat:.4f}, {lng:.4f}"
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in km using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        R = 6371  # Earth's radius in km
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _total_route_distance(self, waypoints: List[Tuple[float, float]]) -> float:
        """Calculate total distance of route"""
        total = 0.0
        for i in range(1, len(waypoints)):
            total += self._calculate_distance(waypoints[i-1], waypoints[i])
        return total


# Singleton instance
schedule_generator = ScheduleGenerator()

