"""
Test script to verify bcrypt password hashing fix
Tests various password lengths including >72 bytes
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.auth_utils import hash_password, verify_password


def test_password_hashing():
    """Test password hashing with various lengths"""
    
    print("\n" + "="*60)
    print("🧪 Testing bcrypt Password Hashing Fix")
    print("="*60 + "\n")
    
    test_cases = [
        ("short", "Short password"),
        ("medium_length_password_123", "Medium length password"),
        ("a" * 50, "50 character password"),
        ("a" * 72, "Exactly 72 character password"),
        ("a" * 100, "100 character password (>72 bytes)"),
        ("a" * 200, "200 character password (>72 bytes)"),
        ("🔐" * 30, "Unicode password (emojis, >72 bytes)"),
        ("P@ssw0rd!2024#VeryLongPasswordThatExceeds72BytesLimit_ThisShouldStillWork_123456789", "Complex long password"),
    ]
    
    passed = 0
    failed = 0
    
    for password, description in test_cases:
        print(f"📝 Test: {description}")
        print(f"   Password length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
        
        try:
            # Test hashing
            hashed = hash_password(password)
            print(f"   ✅ Hashing successful")
            print(f"   Hash: {hashed[:50]}...")
            
            # Test verification with correct password
            is_valid = verify_password(password, hashed)
            if is_valid:
                print(f"   ✅ Verification successful (correct password)")
            else:
                print(f"   ❌ Verification failed (should have passed)")
                failed += 1
                continue
            
            # Test verification with wrong password
            is_invalid = verify_password("wrong_password", hashed)
            if not is_invalid:
                print(f"   ✅ Verification correctly rejected wrong password")
            else:
                print(f"   ❌ Verification incorrectly accepted wrong password")
                failed += 1
                continue
            
            print(f"   ✅ All checks passed!\n")
            passed += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            failed += 1
    
    print("="*60)
    print(f"📊 Test Results:")
    print(f"   ✅ Passed: {passed}/{len(test_cases)}")
    print(f"   ❌ Failed: {failed}/{len(test_cases)}")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 All tests passed! bcrypt fix is working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = test_password_hashing()
    sys.exit(0 if success else 1)

