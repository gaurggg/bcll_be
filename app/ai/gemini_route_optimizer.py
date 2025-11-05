from typing import List, Dict, Any
from app.external.gemini_client import gemini_client
from app.external.google_maps_client import google_maps_client


class GeminiRouteOptimizer:
    def __init__(self):
        self.gemini = gemini_client
        self.maps = google_maps_client
    
    def optimize_and_rank_routes(
        self,
        routes: List[Dict[str, Any]],
        origin: tuple,
        destination: tuple
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini AI to analyze and rank bus routes
        Returns top routes with scores and reasoning
        """
        # Get traffic information
        traffic_data = self.maps.get_traffic_info(origin, destination)
        
        # Use Gemini to rank routes
        ranked = self.gemini.rank_routes(routes, traffic_data)
        
        # Merge rankings with original route data
        result = []
        for rank in ranked:
            route_idx = rank.get("route_index", 0)
            if route_idx < len(routes):
                route_data = routes[route_idx].copy()
                route_data.update({
                    "gemini_score": rank.get("score", 0),
                    "traffic_score": rank.get("traffic_score", 0),
                    "reasoning": rank.get("reasoning", ""),
                    "rank": len(result) + 1
                })
                result.append(route_data)
        
        return result
    
    def analyze_single_route(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detailed analysis of a single route
        """
        prompt = f"""
Analyze this bus route for Bhopal city:
- Distance: {route.get('distance_km', 0)} km
- Duration: {route.get('duration_min', 0)} minutes
- Steps: {route.get('steps', 0)} segments

Rate this route on:
1. Efficiency (distance vs duration)
2. Suitability for bus operation
3. Coverage of major areas

Provide a score out of 10 and brief analysis.
"""
        
        response = self.gemini.generate_content(prompt)
        return {
            "analysis": response,
            "route": route
        }


# Singleton instance
gemini_route_optimizer = GeminiRouteOptimizer()

