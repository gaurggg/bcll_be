"""
Demo script to test the Bhopal Bus POC API
This script demonstrates the complete workflow
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_json(data):
    print(json.dumps(data, indent=2))

def admin_workflow():
    """Test admin workflow"""
    print_section("ADMIN WORKFLOW")
    
    # 1. Admin Login
    print("\n1. Admin Login...")
    response = requests.post(
        f"{BASE_URL}/auth/admin/login",
        json={"email": "admin@bcll.com", "password": "admin123"}
    )
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return None
    
    admin_token = response.json()["access_token"]
    print(f"✅ Admin logged in successfully")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 2. Plan Route (MP Nagar to BHEL)
    print("\n2. Planning route from MP Nagar to BHEL...")
    route_plan = {
        "source_lat": 23.2599,
        "source_lng": 77.4126,
        "dest_lat": 23.2759,
        "dest_lng": 77.4011,
        "peak_hour": "morning"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/route/plan",
        headers=headers,
        json=route_plan
    )
    
    if response.status_code == 200:
        print("✅ Route planning successful!")
        result = response.json()
        print(f"\nFound {result['total_routes']} routes:")
        for route in result['routes'][:3]:  # Show top 3
            print(f"\n  Route {route.get('rank', 'N/A')}:")
            print(f"  - Distance: {route.get('distance_km', 0):.2f} km")
            print(f"  - Duration: {route.get('duration_min', 0):.1f} min")
            print(f"  - Gemini Score: {route.get('gemini_score', 0):.1f}/10")
            print(f"  - Reasoning: {route.get('reasoning', 'N/A')[:100]}...")
    else:
        print(f"❌ Route planning failed: {response.text}")
        return headers
    
    # 3. Create Route
    print("\n3. Creating a route...")
    if result and result.get('routes'):
        best_route = result['routes'][0]
        route_data = {
            "name": "MP Nagar to BHEL Express",
            "source_stop_id": "mp_nagar_1",
            "dest_stop_id": "bhel_1",
            "distance_km": best_route.get('distance_km', 0),
            "duration_min": best_route.get('duration_min', 0),
            "gemini_score": best_route.get('gemini_score', 0),
            "traffic_score": best_route.get('traffic_score', 0),
            "path": []
        }
        
        response = requests.post(
            f"{BASE_URL}/admin/route/create",
            headers=headers,
            json=route_data
        )
        
        if response.status_code == 200:
            route_result = response.json()
            route_id = route_result['route_id']
            print(f"✅ Route created: {route_id}")
            
            # 4. Create Schedule
            print("\n4. Creating schedule with AI predictions...")
            schedule_data = {
                "route_id": route_id,
                "peak_hour": "morning"
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/schedule/create",
                headers=headers,
                json=schedule_data
            )
            
            if response.status_code == 200:
                schedule = response.json()
                print("✅ Schedule created!")
                prediction = schedule.get('ai_prediction', {})
                print(f"\n  AI Predictions:")
                print(f"  - Bus Frequency: {prediction.get('frequency_min', 'N/A')} minutes")
                print(f"  - Buses Needed: {prediction.get('buses_needed', 'N/A')}")
                print(f"  - Expected Passengers/Hour: {prediction.get('expected_passengers_per_hour', 'N/A')}")
                print(f"  - Reasoning: {prediction.get('reasoning', 'N/A')}")
            else:
                print(f"❌ Schedule creation failed: {response.text}")
        else:
            print(f"❌ Route creation failed: {response.text}")
    
    # 5. Get All Routes
    print("\n5. Fetching all routes...")
    response = requests.get(f"{BASE_URL}/admin/routes", headers=headers)
    if response.status_code == 200:
        routes = response.json()
        print(f"✅ Total routes: {routes['total']}")
    
    return headers

def passenger_workflow():
    """Test passenger workflow"""
    print_section("PASSENGER WORKFLOW")
    
    # 1. Register Passenger
    print("\n1. Registering new passenger...")
    passenger_data = {
        "name": "Test User",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "phone": "+919876543210",
        "password": "password123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/passenger/register",
        json=passenger_data
    )
    
    if response.status_code != 200:
        print(f"❌ Passenger registration failed: {response.text}")
        return None
    
    passenger_token = response.json()["access_token"]
    print(f"✅ Passenger registered successfully")
    
    headers = {"Authorization": f"Bearer {passenger_token}"}
    
    # 2. Search Buses
    print("\n2. Searching for buses (Habibganj to TT Nagar)...")
    search_data = {
        "source_lat": 23.2295,
        "source_lng": 77.4385,
        "dest_lat": 23.2447,
        "dest_lng": 77.4056
    }
    
    response = requests.post(
        f"{BASE_URL}/passenger/search",
        headers=headers,
        json=search_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Bus search successful!")
        print(f"\n  Distance: {result['distance_km']} km")
        print(f"  Available Routes: {len(result['available_routes'])}")
        
        fare = result.get('fare_details', {})
        print(f"\n  Fare Details:")
        print(f"  - Base Fare: ₹{fare.get('base_fare', 0)}")
        print(f"  - Final Fare: ₹{fare.get('final_fare', 0)}")
        print(f"  - Peak Hour: {fare.get('is_peak_hour', False)}")
        print(f"  - Slab: {fare.get('slab', 'N/A')}")
        
        if result['available_routes']:
            print(f"\n  Sample Route:")
            route = result['available_routes'][0]
            print(f"  - {route['route_name']}")
            print(f"  - ETA: {route['eta_min']} minutes")
            print(f"  - Fare: ₹{route['fare']}")
    else:
        print(f"❌ Bus search failed: {response.text}")
    
    # 3. Log Travel
    print("\n3. Logging a trip...")
    travel_data = {
        "route_id": "R1",
        "source_stop_id": "habibganj_1",
        "dest_stop_id": "tt_nagar_1"
    }
    
    response = requests.post(
        f"{BASE_URL}/passenger/history/log",
        headers=headers,
        json=travel_data
    )
    
    if response.status_code == 200:
        print("✅ Trip logged successfully")
    else:
        print(f"❌ Logging trip failed: {response.text}")
    
    # 4. Get Recommendations
    print("\n4. Getting personalized recommendations...")
    response = requests.get(
        f"{BASE_URL}/passenger/recommendations",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Recommendations fetched!")
        
        if result['recommendations']:
            print(f"\n  AI Recommendations:")
            for rec in result['recommendations']:
                print(f"  - {rec.get('route_name', 'N/A')}")
                print(f"    Confidence: {rec.get('confidence', 0)*100:.0f}%")
                print(f"    Reasoning: {rec.get('reasoning', 'N/A')}")
        else:
            print("  No recommendations yet (log more trips to get personalized suggestions)")
        
        patterns = result.get('travel_patterns', {})
        print(f"\n  Travel Stats:")
        print(f"  - Total Trips: {patterns.get('total_trips', 0)}")
    else:
        print(f"❌ Getting recommendations failed: {response.text}")
    
    # 5. Calculate Fare
    print("\n5. Calculating fare for 15km trip...")
    fare_data = {
        "distance_km": 15.0,
        "is_peak_hour": True
    }
    
    response = requests.post(
        f"{BASE_URL}/passenger/fare/calculate",
        json=fare_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Fare calculated!")
        print(f"  - Distance: {result['distance_km']} km")
        print(f"  - Base Fare: ₹{result['base_fare']}")
        print(f"  - Final Fare: ₹{result['final_fare']} (Peak Hour)")
        print(f"  - Slab: {result['slab']}")
    else:
        print(f"❌ Fare calculation failed: {response.text}")
    
    return headers

def main():
    """Run complete demo"""
    print("\n" + "🚌"*30)
    print("  BHOPAL BUS POC - API DEMONSTRATION")
    print("🚌"*30)
    
    print("\nMake sure:")
    print("1. MongoDB is running")
    print("2. API server is running (uvicorn app.main:app --reload)")
    print("3. Sample data is seeded (python scripts/seed_bhopal_data.py)")
    
    input("\nPress Enter to continue...")
    
    # Test health
    print_section("HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            print_json(response.json())
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn app.main:app --reload")
        return
    
    # Run workflows
    admin_workflow()
    passenger_workflow()
    
    print_section("DEMO COMPLETED")
    print("\n✨ All tests completed successfully!")
    print("\nNext steps:")
    print("1. Open http://localhost:8000/docs for interactive API testing")
    print("2. Try different Bhopal locations (see QUICKSTART.md)")
    print("3. Test peak vs off-peak hour scheduling")
    print("4. Log multiple trips to see AI recommendations improve")
    print("\n" + "🚌"*30 + "\n")

if __name__ == "__main__":
    main()

