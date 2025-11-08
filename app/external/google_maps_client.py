import googlemaps
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from app.config import settings


class GoogleMapsClient:
    def __init__(self):
        try:
            # Validate Google Maps API key
            if not settings.google_maps_api_key:
                self.client = None
                print("[WARN] Google Maps API key not configured - using mock responses")
                return

            # Check for placeholder values
            if settings.google_maps_api_key in [
                "demo_key_replace_with_real",
                "your_google_maps_api_key_here"
            ]:
                self.client = None
                print("[WARN] Google Maps API key is a placeholder - using mock responses")
                return

            # Validate key format (Google Maps API keys start with "AIza")
            if not settings.google_maps_api_key.startswith("AIza"):
                self.client = None
                print(f"[ERROR] Invalid Google Maps API key format!")
                print(f"[ERROR] Your key starts with: '{settings.google_maps_api_key[:10]}...'")
                print(f"[ERROR] Valid Google Maps API keys start with 'AIza'")
                print(f"[WARN] Using mock responses instead")
                return

            # Validate key length (typical Google Maps API keys are ~39 chars)
            if len(settings.google_maps_api_key) < 30:
                self.client = None
                print(f"[ERROR] Google Maps API key seems too short (length: {len(settings.google_maps_api_key)})")
                print(f"[WARN] Using mock responses instead")
                return

            # Try to initialize the client
            self.client = googlemaps.Client(key=settings.google_maps_api_key)
            print("[OK] Google Maps API client initialized successfully")

        except Exception as e:
            self.client = None
            print(f"[ERROR] Google Maps client initialization failed: {e}")
            print(f"[WARN] Using mock responses instead")
    
    def get_directions(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        alternatives: bool = True,
        mode: str = "driving",
        departure_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get directions from origin to destination
        Returns list of route alternatives
        """
        if not self.client:
            # Return mock data for development
            return self._get_mock_directions(origin, destination)
        
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                alternatives=alternatives,
                departure_time=departure_time,
                traffic_model="best_guess"
            )
            return result
        except Exception as e:
            print(f"Error getting directions: {e}")
            return self._get_mock_directions(origin, destination)
    
    def get_distance_matrix(
        self,
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        mode: str = "driving",
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get distance matrix for multiple origins and destinations
        """
        if not self.client:
            return self._get_mock_distance_matrix(origins, destinations)
        
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            result = self.client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode=mode,
                departure_time=departure_time,
                traffic_model="best_guess"
            )
            return result
        except Exception as e:
            print(f"Error getting distance matrix: {e}")
            return self._get_mock_distance_matrix(origins, destinations)
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to lat/lng
        """
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]["geometry"]["location"]
                return (location["lat"], location["lng"])
            return None
        except Exception as e:
            print(f"Error geocoding address: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[List[Dict]]:
        """
        Reverse geocode lat/lng to address
        Returns full result with address_components for detailed parsing
        """
        try:
            result = self.client.reverse_geocode((lat, lng))
            if result:
                return result  # Return full result array
            return None
        except Exception as e:
            print(f"Error reverse geocoding: {e}")
            return None
    
    def get_traffic_info(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get traffic information for a route
        Returns duration in traffic vs normal duration
        """
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess"
            )
            
            if result:
                leg = result[0]["legs"][0]
                return {
                    "distance": leg["distance"]["value"],  # meters
                    "duration": leg["duration"]["value"],  # seconds
                    "duration_in_traffic": leg.get("duration_in_traffic", {}).get("value", leg["duration"]["value"]),
                    "traffic_ratio": leg.get("duration_in_traffic", {}).get("value", leg["duration"]["value"]) / leg["duration"]["value"]
                }
            return {}
        except Exception as e:
            print(f"Error getting traffic info: {e}")
            return {}
    
    def _get_mock_directions(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Dict]:
        """Mock directions for development"""
        import math
        
        # Calculate approximate distance using Haversine formula
        lat1, lon1 = origin
        lat2, lon2 = destination
        
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        
        # Estimate duration (assuming 30 km/h average speed)
        duration_min = distance_km / 30 * 60
        
        return [{
            "legs": [{
                "distance": {"value": int(distance_km * 1000), "text": f"{distance_km:.1f} km"},
                "duration": {"value": int(duration_min * 60), "text": f"{duration_min:.0f} mins"},
                "duration_in_traffic": {"value": int(duration_min * 60 * 1.2), "text": f"{duration_min*1.2:.0f} mins"},
                "start_location": {"lat": lat1, "lng": lon1},
                "end_location": {"lat": lat2, "lng": lon2},
                "steps": [
                    {
                        "distance": {"value": int(distance_km * 1000)},
                        "duration": {"value": int(duration_min * 60)},
                        "start_location": {"lat": lat1, "lng": lon1},
                        "end_location": {"lat": lat2, "lng": lon2},
                        "html_instructions": f"Head to destination ({distance_km:.1f} km)"
                    }
                ]
            }],
            "summary": "Mock Route (API key needed for real data)"
        }]
    
    def _get_mock_distance_matrix(self, origins: List[Tuple[float, float]], destinations: List[Tuple[float, float]]) -> Dict:
        """Mock distance matrix for development"""
        if not origins or not destinations:
            return {}
        
        origin = origins[0]
        destination = destinations[0]
        mock_directions = self._get_mock_directions(origin, destination)
        
        if mock_directions:
            leg = mock_directions[0]["legs"][0]
            return {
                "rows": [{
                    "elements": [{
                        "status": "OK",
                        "distance": leg["distance"],
                        "duration": leg["duration"],
                        "duration_in_traffic": leg.get("duration_in_traffic", leg["duration"])
                    }]
                }]
            }
        
        return {"rows": [{"elements": [{"status": "NOT_FOUND"}]}]}


# Singleton instance
google_maps_client = GoogleMapsClient()

