"""
Seed script for Bhopal bus system data
Populates MongoDB with sample stops, buses, and fare configuration
"""
import sys
sys.path.append('.')

from app.db.mongodb import mongodb
from datetime import datetime


def seed_stops():
    """Seed major stops in Bhopal"""
    stops_collection = mongodb.get_collection("stops")
    
    # Clear existing stops
    stops_collection.delete_many({})
    
    bhopal_stops = [
        {
            "name": "MP Nagar Zone-1",
            "location": {"type": "Point", "coordinates": [77.4126, 23.2599]},
            "type": "major",
            "avg_dwell_time_s": 60
        },
        {
            "name": "BHEL",
            "location": {"type": "Point", "coordinates": [77.4011, 23.2759]},
            "type": "major",
            "avg_dwell_time_s": 60
        },
        {
            "name": "Habibganj Railway Station",
            "location": {"type": "Point", "coordinates": [77.4385, 23.2295]},
            "type": "major",
            "avg_dwell_time_s": 90
        },
        {
            "name": "Bhopal Junction Railway Station",
            "location": {"type": "Point", "coordinates": [77.4119, 23.2697]},
            "type": "major",
            "avg_dwell_time_s": 90
        },
        {
            "name": "New Market",
            "location": {"type": "Point", "coordinates": [77.4125, 23.2637]},
            "type": "major",
            "avg_dwell_time_s": 60
        },
        {
            "name": "Bittan Market",
            "location": {"type": "Point", "coordinates": [77.4025, 23.2456]},
            "type": "major",
            "avg_dwell_time_s": 60
        },
        {
            "name": "Roshanpura",
            "location": {"type": "Point", "coordinates": [77.4298, 23.2156]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Arera Colony",
            "location": {"type": "Point", "coordinates": [77.4371, 23.2156]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "TT Nagar",
            "location": {"type": "Point", "coordinates": [77.4056, 23.2447]},
            "type": "major",
            "avg_dwell_time_s": 60
        },
        {
            "name": "Govindpura",
            "location": {"type": "Point", "coordinates": [77.4742, 23.2443]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Ashoka Garden",
            "location": {"type": "Point", "coordinates": [77.4465, 23.2282]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Shahpura",
            "location": {"type": "Point", "coordinates": [77.4289, 23.1963]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Bairagarh",
            "location": {"type": "Point", "coordinates": [77.3561, 23.2611]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Kolar",
            "location": {"type": "Point", "coordinates": [77.4234, 23.1784]},
            "type": "regular",
            "avg_dwell_time_s": 45
        },
        {
            "name": "Danish Kunj",
            "location": {"type": "Point", "coordinates": [77.4658, 23.1890]},
            "type": "regular",
            "avg_dwell_time_s": 45
        }
    ]
    
    result = stops_collection.insert_many(bhopal_stops)
    print(f"Seeded {len(result.inserted_ids)} stops")
    return result.inserted_ids


def seed_buses():
    """Seed bus fleet"""
    buses_collection = mongodb.get_collection("buses")
    
    # Clear existing buses
    buses_collection.delete_many({})
    
    buses = []
    for i in range(1, 51):  # Create 50 buses for POC
        buses.append({
            "bus_number": f"MP-01-{1000+i}",
            "capacity": 50,
            "status": "active"
        })
    
    result = buses_collection.insert_many(buses)
    print(f"Seeded {len(result.inserted_ids)} buses")
    return result.inserted_ids


def seed_fare_config():
    """Seed fare configuration"""
    fare_collection = mongodb.get_collection("fare_config")
    
    # Clear existing config
    fare_collection.delete_many({})
    
    config = {
        "distance_slab_km": [0, 5, 10, 20, 50],
        "base_fare_inr": [10, 15, 25, 40],
        "peak_multiplier": 1.2,
        "created_at": datetime.utcnow()
    }
    
    result = fare_collection.insert_one(config)
    print(f"Seeded fare configuration")
    return result.inserted_id


def main():
    """Main seed function"""
    print("Connecting to MongoDB...")
    mongodb.connect()
    
    print("\nSeeding Bhopal data...")
    print("-" * 50)
    
    seed_stops()
    seed_buses()
    seed_fare_config()
    
    print("-" * 50)
    print("Seeding completed successfully!")
    print("\nYou can now use the API with:")
    print("- Admin login: admin@bcll.com / admin123")
    print("- Create passenger accounts via /auth/passenger/register")
    
    mongodb.close()


if __name__ == "__main__":
    main()

