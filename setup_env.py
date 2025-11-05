#!/usr/bin/env python3
"""
Setup environment file for Bhopal Bus POC
"""
import os
import shutil

def setup_env():
    """Setup .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('dev.env'):
            print("Creating .env file from dev.env template...")
            shutil.copy('dev.env', '.env')
            print("[OK] .env file created!")
            print("\nNext steps:")
            print("1. Edit .env file and add your API keys:")
            print("   - GOOGLE_MAPS_API_KEY (from Google Cloud Console)")
            print("   - GEMINI_API_KEY (from Google AI Studio)")
            print("2. Start MongoDB: net start MongoDB")
            print("3. Seed data: python scripts/seed_bhopal_data.py")
            print("4. Run server: uvicorn app.main:app --reload")
        else:
            print("[ERROR] dev.env template not found!")
    else:
        print("[OK] .env file already exists")
        
    print("\nCurrent environment status:")
    
    # Check MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("[OK] MongoDB: Connected")
        client.close()
    except:
        print("[ERROR] MongoDB: Not running (run: net start MongoDB)")
    
    # Check API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if google_key and google_key != "your_google_maps_api_key_here":
        print("[OK] Google Maps API: Configured")
    else:
        print("[WARN] Google Maps API: Not configured (will use mock data)")
    
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print("[OK] Gemini AI API: Configured")
    else:
        print("[WARN] Gemini AI API: Not configured (will use mock responses)")

if __name__ == "__main__":
    setup_env()
