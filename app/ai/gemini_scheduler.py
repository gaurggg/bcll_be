from typing import Dict, Any
from app.external.gemini_client import gemini_client


class GeminiScheduler:
    def __init__(self):
        self.gemini = gemini_client
    
    def predict_schedule(self, route_data: Dict[str, Any], peak_hour: str) -> Dict[str, Any]:
        """
        Use Gemini AI to predict optimal bus scheduling
        Returns recommendations for frequency and fleet size
        """
        prediction = self.gemini.predict_bus_schedule(route_data, peak_hour)
        
        # Add default values if Gemini doesn't provide them
        result = {
            "frequency_min": prediction.get("frequency_min", self._default_frequency(peak_hour)),
            "buses_needed": prediction.get("buses_needed", self._estimate_buses(route_data, peak_hour)),
            "expected_passengers_per_hour": prediction.get("expected_passengers_per_hour", 400),
            "reasoning": prediction.get("reasoning", "AI-based prediction"),
            "peak_hour": peak_hour
        }
        
        return result
    
    def _default_frequency(self, peak_hour: str) -> int:
        """Default frequency based on peak hour"""
        if peak_hour in ["morning", "evening"]:
            return 8  # 8 minutes during peak
        return 12  # 12 minutes off-peak
    
    def _estimate_buses(self, route_data: Dict[str, Any], peak_hour: str) -> int:
        """
        Estimate number of buses needed
        Based on route duration and desired frequency
        """
        duration = route_data.get("estimated_duration_min", 45)
        frequency = self._default_frequency(peak_hour)
        
        # Number of buses = (round trip time) / frequency + buffer
        # Round trip = 2 * duration + layover time (10 min)
        round_trip = (2 * duration) + 10
        buses = (round_trip / frequency) + 1  # +1 for buffer
        
        return int(buses)
    
    def optimize_fleet_allocation(self, routes: list, total_buses: int) -> Dict[str, int]:
        """
        Optimize bus allocation across multiple routes
        """
        prompt = f"""
You are optimizing bus fleet allocation for Bhopal city public transport.

Total available buses: {total_buses}
Routes to serve: {len(routes)}

Route details:
{routes}

How should we allocate buses to maximize coverage and minimize wait times?
Provide allocation as JSON: {{"route_id": bus_count}}
"""
        
        response = self.gemini.generate_content(prompt)
        # Parse and return allocation
        return {}


# Singleton instance
gemini_scheduler = GeminiScheduler()

