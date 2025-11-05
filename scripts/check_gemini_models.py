"""
Script to check available Gemini models and diagnose API issues
"""
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def check_gemini_setup():
    """Check Gemini API setup and list available models"""
    
    print("=" * 70)
    print("GEMINI API DIAGNOSTIC TOOL")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY not found in .env file")
        return
    
    print(f"\n✅ API Key found: {api_key[:20]}...{api_key[-10:]}")
    print(f"   Key length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:10]}")
    
    # Check library version
    print(f"\n📦 google-generativeai version: {genai.__version__}")
    
    # Configure API
    try:
        genai.configure(api_key=api_key)
        print("✅ API configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure API: {e}")
        return
    
    # List all available models
    print("\n" + "=" * 70)
    print("AVAILABLE MODELS")
    print("=" * 70)
    
    try:
        models = genai.list_models()
        
        generative_models = []
        for model in models:
            # Check if model supports generateContent
            if 'generateContent' in model.supported_generation_methods:
                generative_models.append(model)
                print(f"\n✅ {model.name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description}")
                print(f"   Supported methods: {', '.join(model.supported_generation_methods)}")
        
        if not generative_models:
            print("\n❌ No models found that support generateContent")
        else:
            print("\n" + "=" * 70)
            print(f"SUMMARY: Found {len(generative_models)} models supporting generateContent")
            print("=" * 70)
            
            print("\n📋 Recommended models for your use case:")
            for model in generative_models:
                if 'flash' in model.name.lower():
                    print(f"   ⚡ {model.name} (FAST - Recommended)")
                elif 'pro' in model.name.lower():
                    print(f"   🎯 {model.name} (POWERFUL)")
                else:
                    print(f"   • {model.name}")
    
    except Exception as e:
        print(f"\n❌ Error listing models: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Full error: {str(e)}")
        
        # Try to provide helpful suggestions
        if "403" in str(e):
            print("\n💡 Suggestion: API key might not have proper permissions")
            print("   - Check if API key is enabled in Google AI Studio")
            print("   - Verify billing is set up (if required)")
        elif "404" in str(e):
            print("\n💡 Suggestion: API endpoint might be incorrect")
            print("   - Check if you're using the correct API version")
        elif "401" in str(e):
            print("\n💡 Suggestion: API key is invalid or expired")
            print("   - Generate a new API key from Google AI Studio")
            print("   - URL: https://makersuite.google.com/app/apikey")
    
    # Test a simple generation
    print("\n" + "=" * 70)
    print("TESTING MODEL GENERATION")
    print("=" * 70)
    
    # Try different model names (updated for 2025)
    test_models = [
        "models/gemini-2.5-flash",
        "models/gemini-flash-latest",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-pro",
        "models/gemini-pro-latest"
    ]
    
    for model_name in test_models:
        try:
            print(f"\n🧪 Testing: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello' in one word")
            print(f"   ✅ SUCCESS! Response: {response.text.strip()}")
            print(f"\n🎉 WORKING MODEL FOUND: {model_name}")
            break
        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                print(f"   ❌ Model not found")
            elif "403" in error_str:
                print(f"   ❌ Permission denied")
            else:
                print(f"   ❌ Error: {error_str[:100]}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    check_gemini_setup()

