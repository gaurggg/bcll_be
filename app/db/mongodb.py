from pymongo import MongoClient, GEOSPHERE
from pymongo.database import Database
from typing import Optional
from app.config import settings


class MongoDB:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    @classmethod
    def connect(cls):
        """Connect to MongoDB"""
        cls.client = MongoClient(settings.mongodb_uri)
        cls.db = cls.client[settings.mongodb_db]
        
        # Create indexes
        cls.db.stops.create_index([("location", GEOSPHERE)])
        cls.db.passengers.create_index("email", unique=True)
        cls.db.travel_history.create_index("passenger_id")
        cls.db.routes.create_index("route_id", unique=True)
        
        print(f"Connected to MongoDB: {settings.mongodb_db}")

    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        if cls.db is None:
            cls.connect()
        return cls.db[name]


# Initialize connection
mongodb = MongoDB()

