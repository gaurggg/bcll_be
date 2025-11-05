from typing import List, Dict, Any
from datetime import datetime
from app.external.gemini_client import gemini_client
from app.db.mongodb import mongodb


class GeminiRecommender:
    def __init__(self):
        self.gemini = gemini_client
    
    def get_personalized_recommendations(self, passenger_id: str) -> List[Dict[str, Any]]:
        """
        Get personalized bus recommendations based on travel history
        """
        # Fetch travel history
        history_collection = mongodb.get_collection("travel_history")
        history = list(history_collection.find(
            {"passenger_id": passenger_id}
        ).sort("timestamp", -1).limit(20))
        
        if not history:
            return []
        
        # Get current time info
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        day_of_week = now.strftime("%A")
        
        # Convert ObjectId to string for JSON serialization
        history_data = []
        for record in history:
            history_data.append({
                "route_id": record.get("route_id"),
                "source_stop_id": record.get("source_stop_id"),
                "dest_stop_id": record.get("dest_stop_id"),
                "travel_time": record.get("travel_time"),
                "day_of_week": record.get("day_of_week"),
                "timestamp": record.get("timestamp").isoformat() if record.get("timestamp") else ""
            })
        
        # Use Gemini to analyze patterns and recommend
        recommendations = self.gemini.recommend_buses(history_data, current_time)
        
        # Enrich recommendations with route details
        routes_collection = mongodb.get_collection("routes")
        enriched = []
        
        for rec in recommendations:
            route_id = rec.get("route_id")
            route = routes_collection.find_one({"route_id": route_id})
            
            if route:
                enriched.append({
                    "route_id": route_id,
                    "route_name": route.get("name"),
                    "confidence": rec.get("confidence", 0.5),
                    "reasoning": rec.get("reasoning", "Based on your travel patterns"),
                    "current_time": current_time,
                    "day": day_of_week
                })
        
        return enriched
    
    def analyze_travel_patterns(self, passenger_id: str) -> Dict[str, Any]:
        """
        Analyze passenger's travel patterns
        Returns insights about frequent routes, times, etc.
        """
        history_collection = mongodb.get_collection("travel_history")
        history = list(history_collection.find(
            {"passenger_id": passenger_id}
        ).sort("timestamp", -1).limit(50))
        
        if not history:
            return {"patterns": "No travel history available"}
        
        # Simple pattern analysis
        route_frequency = {}
        time_slots = {}
        day_frequency = {}
        
        for record in history:
            # Count routes
            route_id = record.get("route_id")
            route_frequency[route_id] = route_frequency.get(route_id, 0) + 1
            
            # Count time slots (hourly)
            travel_time = record.get("travel_time", "")
            if travel_time:
                hour = travel_time.split(":")[0]
                time_slots[hour] = time_slots.get(hour, 0) + 1
            
            # Count days
            day = record.get("day_of_week", "")
            day_frequency[day] = day_frequency.get(day, 0) + 1
        
        return {
            "most_used_routes": sorted(route_frequency.items(), key=lambda x: x[1], reverse=True)[:3],
            "preferred_times": sorted(time_slots.items(), key=lambda x: x[1], reverse=True)[:3],
            "frequent_days": sorted(day_frequency.items(), key=lambda x: x[1], reverse=True)[:3],
            "total_trips": len(history)
        }


# Singleton instance
gemini_recommender = GeminiRecommender()

