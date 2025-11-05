from typing import Optional
from app.db.mongodb import mongodb


class FareCalculator:
    def __init__(self):
        self.fare_config = None
        self._load_config()
    
    def _load_config(self):
        """Load fare configuration from database"""
        config_collection = mongodb.get_collection("fare_config")
        self.fare_config = config_collection.find_one()
        
        # If no config exists, create default
        if not self.fare_config:
            self.fare_config = {
                "distance_slab_km": [0, 5, 10, 20, 50],
                "base_fare_inr": [10, 15, 25, 40],
                "peak_multiplier": 1.2
            }
            config_collection.insert_one(self.fare_config)
    
    def calculate_fare(self, distance_km: float, is_peak_hour: bool = False) -> dict:
        """
        Calculate fare based on distance and peak hour
        Returns fare details
        """
        if not self.fare_config:
            self._load_config()
        
        slabs = self.fare_config.get("distance_slab_km", [0, 5, 10, 20, 50])
        fares = self.fare_config.get("base_fare_inr", [10, 15, 25, 40])
        peak_multiplier = self.fare_config.get("peak_multiplier", 1.2)
        
        # Find applicable slab
        base_fare = fares[-1]  # Default to highest slab
        slab_index = 0
        
        for i in range(len(slabs) - 1):
            if slabs[i] <= distance_km < slabs[i + 1]:
                base_fare = fares[i]
                slab_index = i
                break
        
        # Apply peak hour multiplier
        final_fare = base_fare
        if is_peak_hour:
            final_fare = base_fare * peak_multiplier
        
        return {
            "distance_km": round(distance_km, 2),
            "base_fare": base_fare,
            "peak_multiplier": peak_multiplier if is_peak_hour else 1.0,
            "final_fare": round(final_fare, 2),
            "is_peak_hour": is_peak_hour,
            "slab": f"{slabs[slab_index]}-{slabs[slab_index + 1] if slab_index + 1 < len(slabs) else '+'} km"
        }
    
    def is_peak_hour(self, hour: int) -> bool:
        """
        Check if given hour is peak hour
        Peak hours: 8-12 (morning) and 18-21 (evening)
        """
        return (8 <= hour < 12) or (18 <= hour < 21)
    
    def estimate_fare_for_route(self, route_id: str, is_peak_hour: bool = False) -> Optional[dict]:
        """
        Estimate fare for a complete route
        """
        routes_collection = mongodb.get_collection("routes")
        route = routes_collection.find_one({"route_id": route_id})
        
        if not route:
            return None
        
        distance_km = route.get("total_distance_km", 0)
        return self.calculate_fare(distance_km, is_peak_hour)


# Singleton instance
fare_calculator = FareCalculator()

