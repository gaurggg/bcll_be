"""
Setup verification script for Bhopal Bus POC
Checks all prerequisites and configurations
"""
import sys
import os

def check_python_version():
    """Check Python version"""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (Need 3.8+)")
        return False

def check_mongodb():
    """Check MongoDB connection"""
    print("Checking MongoDB connection...", end=" ")
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ Connected")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Cannot connect")
        print(f"   Error: {e}")
        print("   Make sure MongoDB is installed and running")
        return False

def check_env_file():
    """Check .env file exists"""
    print("Checking .env file...", end=" ")
    if os.path.exists(".env"):
        print("✅ Found")
        return True
    else:
        print("❌ Not found")
        print("   Create .env file from env_template.txt")
        return False

def check_env_variables():
    """Check environment variables"""
    print("\nChecking environment variables:")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        print("  ❌ Cannot load dotenv")
        return False
    
    required_vars = [
        "MONGODB_URI",
        "MONGODB_DB", 
        "GOOGLE_MAPS_API_KEY",
        "GEMINI_API_KEY",
        "JWT_SECRET"
    ]
    
    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here" and len(value) > 10:
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - Not configured")
            all_good = False
    
    return all_good

def check_dependencies():
    """Check required Python packages"""
    print("\nChecking Python dependencies:")
    
    packages = [
        "fastapi",
        "uvicorn",
        "pymongo",
        "pydantic",
        "jose",
        "passlib",
        "googlemaps",
        "google.generativeai",
        "networkx",
        "dotenv"
    ]
    
    all_installed = True
    for package in packages:
        try:
            if package == "jose":
                __import__("jose")
            elif package == "dotenv":
                __import__("dotenv")
            elif package == "google.generativeai":
                __import__("google.generativeai")
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - Not installed")
            all_installed = False
    
    return all_installed

def check_project_structure():
    """Check project structure"""
    print("\nChecking project structure:")
    
    required_dirs = [
        "app",
        "app/api",
        "app/db",
        "app/routing",
        "app/ai",
        "app/fares",
        "app/external",
        "app/utils",
        "scripts"
    ]
    
    required_files = [
        "app/main.py",
        "app/config.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - Missing")
            all_good = False
    
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing")
            all_good = False
    
    return all_good

def check_seeded_data():
    """Check if data is seeded"""
    print("\nChecking seeded data...", end=" ")
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        load_dotenv()
        
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB", "bcll_poc")
        
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        
        stops_count = db.stops.count_documents({})
        buses_count = db.buses.count_documents({})
        
        if stops_count > 0 and buses_count > 0:
            print(f"✅ Data seeded ({stops_count} stops, {buses_count} buses)")
            client.close()
            return True
        else:
            print("❌ No data found")
            print("   Run: python scripts/seed_bhopal_data.py")
            client.close()
            return False
    except Exception as e:
        print(f"❌ Cannot check")
        print(f"   Error: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("  BHOPAL BUS POC - SETUP VERIFICATION")
    print("="*60 + "\n")
    
    results = []
    
    # Run all checks
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Project Structure", check_project_structure()))
    results.append(("MongoDB", check_mongodb()))
    results.append((".env File", check_env_file()))
    results.append(("Environment Variables", check_env_variables()))
    results.append(("Seeded Data", check_seeded_data()))
    
    # Summary
    print("\n" + "="*60)
    print("  VERIFICATION SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print("\n" + "-"*60)
    print(f"  Result: {passed}/{total} checks passed")
    print("-"*60 + "\n")
    
    if passed == total:
        print("🎉 All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Run: uvicorn app.main:app --reload")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Or run: python scripts/test_api.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Create .env file: copy env_template.txt to .env and configure")
        print("  - Start MongoDB: net start MongoDB (Windows)")
        print("  - Seed data: python scripts/seed_bhopal_data.py")
    
    print()

if __name__ == "__main__":
    main()

