import google.generativeai as genai
from typing import List, Dict, Any
import json
from app.config import settings


class GeminiClient:
    def __init__(self):
        try:
            # Validate Gemini API key
            if not settings.gemini_api_key:
                self.model = None
                self.enabled = False
                print("[WARN] Gemini API key not configured - using mock responses")
                return

            # Check for placeholder values
            if settings.gemini_api_key in [
                "demo_key_replace_with_real",
                "your_gemini_api_key_here"
            ]:
                self.model = None
                self.enabled = False
                print("[WARN] Gemini API key is a placeholder - using mock responses")
                return

            # Validate key format (Gemini API keys start with "AIza")
            if not settings.gemini_api_key.startswith("AIza"):
                self.model = None
                self.enabled = False
                print(f"[ERROR] Invalid Gemini API key format!")
                print(f"[ERROR] Your key starts with: '{settings.gemini_api_key[:10]}...'")
                print(f"[ERROR] Valid Gemini API keys start with 'AIza'")
                print(f"[WARN] Using mock responses instead")
                return

            # Configure Gemini with the API key
            genai.configure(api_key=settings.gemini_api_key)

            # Use Gemini 2.5 Flash (latest stable model as of 2025)
            # This is the fastest and most efficient model for structured JSON responses
            # Alternative: 'models/gemini-2.5-pro' for more complex reasoning
            # Alternative: 'models/gemini-flash-latest' to always use the latest
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
            self.enabled = True
            print("[OK] Gemini AI client initialized successfully (using gemini-2.5-flash)")

        except Exception as e:
            self.model = None
            self.enabled = False
            print(f"[ERROR] Gemini client initialization failed: {e}")
            print(f"[WARN] Using mock responses instead")
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini"""
        if not self.enabled:
            return "Mock AI response (API key needed for real analysis)"

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages based on error type
            if "429" in error_msg or "quota" in error_msg.lower() or "ResourceExhausted" in str(type(e).__name__):
                print("[ERROR] ⚠️  GEMINI API QUOTA EXCEEDED!")
                print("[ERROR] You've hit your rate limit or daily quota.")
                print("[ERROR] Solutions:")
                print("[ERROR]   1. Wait a few minutes and try again (rate limit resets)")
                print("[ERROR]   2. Check usage: https://ai.dev/usage?tab=rate-limit")
                print("[ERROR]   3. Upgrade your plan if needed")
                print("[WARN] Falling back to mock AI responses")
                self.enabled = False  # Disable to avoid repeated quota errors
            elif "404" in error_msg or "not found" in error_msg.lower():
                print(f"[ERROR] Gemini model not found: {error_msg}")
                print("[ERROR] Using model: models/gemini-2.5-flash")
            elif "403" in error_msg or "permission" in error_msg.lower():
                print("[ERROR] Permission denied. Check API key permissions.")
            elif "API key" in error_msg or "401" in error_msg:
                print("[ERROR] Invalid API key. Please check your GEMINI_API_KEY in .env")
            else:
                print(f"[ERROR] Gemini API error: {error_msg[:200]}")

            return "AI service temporarily unavailable"
    
    def rank_routes(self, routes: List[Dict[str, Any]], traffic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank bus routes using Gemini AI
        Returns ranked routes with scores and reasoning
        """
        prompt = f"""
You are an expert in public transportation planning for Bhopal, India.

I have {len(routes)} potential bus routes between two points. Please analyze and rank them based on:
1. Total distance and travel time efficiency
2. Traffic conditions (current traffic ratio: {traffic_data.get('traffic_ratio', 1.0)})
3. Number of major roads and connectivity
4. Suitability for public bus transport
5. Passenger coverage potential

Routes data:
{json.dumps(routes, indent=2)}

Traffic information:
{json.dumps(traffic_data, indent=2)}

Please provide a JSON response with the following structure:
{{
  "ranked_routes": [
    {{
      "route_index": 0,
      "score": 9.2,
      "traffic_score": 8.5,
      "reasoning": "Brief explanation of why this route is ranked here"
    }}
  ]
}}

Rank all routes from best to worst. Provide scores out of 10.
"""
        
        if not self.enabled:
            # Return mock rankings for development
            return self._get_mock_route_rankings(routes)
        
        try:
            response = self.generate_content(prompt)
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result.get("ranked_routes", [])
            return self._get_mock_route_rankings(routes)
        except Exception as e:
            print(f"Error ranking routes: {e}")
            return self._get_mock_route_rankings(routes)
    
    def predict_bus_schedule(self, route_data: Dict[str, Any], peak_hour: str) -> Dict[str, Any]:
        """
        Predict optimal bus scheduling using Gemini AI
        """
        prompt = f"""
You are an expert in public transportation planning for Bhopal, India.

I need to create a bus schedule for the following route:
- Route: {route_data.get('name')}
- Distance: {route_data.get('total_distance_km')} km
- Estimated Duration: {route_data.get('estimated_duration_min')} minutes
- Peak Hour: {peak_hour}
- Traffic Score: {route_data.get('traffic_score', 7.0)}

Peak hour constraints:
- Morning (8 AM - 12 PM): High demand, target 5-10 min headway
- Evening (6 PM - 9 PM): High demand, target 5-10 min headway
- Off-peak: Moderate demand, target 12-15 min headway

Please analyze and recommend:
1. Optimal bus frequency (in minutes)
2. Number of buses needed for this route
3. Expected passenger load
4. Any scheduling considerations

Provide a JSON response:
{{
  "frequency_min": 8,
  "buses_needed": 12,
  "expected_passengers_per_hour": 500,
  "reasoning": "Brief explanation"
}}
"""
        
        if not self.enabled:
            return self._get_mock_schedule_prediction(route_data, peak_hour)
        
        try:
            response = self.generate_content(prompt)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            return self._get_mock_schedule_prediction(route_data, peak_hour)
        except Exception as e:
            print(f"Error predicting schedule: {e}")
            return self._get_mock_schedule_prediction(route_data, peak_hour)
    
    def recommend_buses(self, travel_history: List[Dict[str, Any]], current_time: str) -> List[Dict[str, Any]]:
        """
        Recommend buses based on passenger travel history
        """
        prompt = f"""
You are an AI assistant for a public bus system in Bhopal, India.

A passenger has the following travel history:
{json.dumps(travel_history[-10:], indent=2)}  # Last 10 trips

Current time: {current_time}

Based on their patterns, recommend relevant buses they might need today.
Consider:
1. Frequent time slots and days
2. Common origin-destination pairs
3. Regular travel patterns

Provide a JSON response:
{{
  "recommendations": [
    {{
      "route_id": "R1",
      "confidence": 0.9,
      "reasoning": "You usually take this route at this time on weekdays"
    }}
  ]
}}
"""
        
        try:
            response = self.generate_content(prompt)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result.get("recommendations", [])
            return []
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def _get_mock_route_rankings(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock route rankings for development"""
        rankings = []
        for i, route in enumerate(routes):
            # Simple scoring based on distance and duration
            distance = route.get('distance_km', 10)
            duration = route.get('duration_min', 30)
            
            # Shorter and faster routes get higher scores
            distance_score = max(1, 10 - (distance / 5))
            duration_score = max(1, 10 - (duration / 10))
            overall_score = (distance_score + duration_score) / 2
            
            rankings.append({
                "route_index": i,
                "score": round(overall_score, 1),
                "traffic_score": round(overall_score * 0.9, 1),
                "reasoning": f"Mock analysis: {distance:.1f}km route with {duration:.0f}min duration. Score based on efficiency."
            })
        
        # Sort by score (highest first)
        rankings.sort(key=lambda x: x['score'], reverse=True)
        return rankings
    
    def _get_mock_schedule_prediction(self, route_data: Dict[str, Any], peak_hour: str) -> Dict[str, Any]:
        """Generate mock schedule predictions"""
        duration = route_data.get('estimated_duration_min', 45)
        
        # Simple logic for frequency and bus count
        if peak_hour in ['morning', 'evening']:
            frequency = 8  # 8 minutes during peak
            expected_passengers = 500
        else:
            frequency = 12  # 12 minutes off-peak
            expected_passengers = 300
        
        # Calculate buses needed: (round trip time) / frequency
        round_trip_time = (duration * 2) + 10  # 10 min layover
        buses_needed = max(1, int(round_trip_time / frequency) + 1)
        
        return {
            "frequency_min": frequency,
            "buses_needed": buses_needed,
            "expected_passengers_per_hour": expected_passengers,
            "reasoning": f"Mock prediction: {duration}min route needs {buses_needed} buses for {frequency}min frequency during {peak_hour}"
        }


# Singleton instance
gemini_client = GeminiClient()

