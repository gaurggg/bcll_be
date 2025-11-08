"""
Script to update existing routes with proper place names instead of coordinates
Run this after fixing the geocoding to update all existing routes in the database
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_database
from app.utils.schedule_generator import schedule_generator
from bson import ObjectId


def update_route_place_names():
    """Update all routes in database with proper place names"""
    db = get_database()
    routes_collection = db["routes"]
    
    # Get all routes
    routes = list(routes_collection.find({}))
    
    print(f"\n🔍 Found {len(routes)} routes to update\n")
    
    updated_count = 0
    failed_count = 0
    
    for route in routes:
        route_id = str(route["_id"])
        route_name = route.get("name", "Unknown")
        
        print(f"📍 Processing route: {route_name} (ID: {route_id})")
        
        # Check if route has intermediate_stops
        if "intermediate_stops" not in route or not route["intermediate_stops"]:
            print(f"  ⚠️  No intermediate stops found, skipping...")
            continue
        
        intermediate_stops = route["intermediate_stops"]
        updated_stops = []
        
        # Update each stop
        for i, stop in enumerate(intermediate_stops):
            lat = stop.get("lat")
            lng = stop.get("lng")
            old_name = stop.get("name", "")
            
            # Only update if current name is coordinates
            if old_name.startswith("Stop at"):
                print(f"  🔄 Updating stop {i}: {old_name}")
                
                # Get new place name
                new_name = schedule_generator._get_location_name(lat, lng)
                
                # Update stop
                stop["name"] = new_name
                
                if not new_name.startswith("Stop at"):
                    print(f"     ✅ Updated to: {new_name}")
                else:
                    print(f"     ⚠️  Still coordinates: {new_name}")
            else:
                print(f"  ✓ Stop {i} already has place name: {old_name}")
            
            updated_stops.append(stop)
        
        # Update route in database
        try:
            result = routes_collection.update_one(
                {"_id": ObjectId(route_id)},
                {"$set": {"intermediate_stops": updated_stops}}
            )
            
            if result.modified_count > 0:
                print(f"  ✅ Route updated successfully!\n")
                updated_count += 1
            else:
                print(f"  ℹ️  No changes needed\n")
        except Exception as e:
            print(f"  ❌ Error updating route: {e}\n")
            failed_count += 1
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   Total routes: {len(routes)}")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   ℹ️  Skipped: {len(routes) - updated_count - failed_count}")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Route Place Names Update Script")
    print("="*60)
    
    try:
        update_route_place_names()
        print("✅ Script completed successfully!")
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()

