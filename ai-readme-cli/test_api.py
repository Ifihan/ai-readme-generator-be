#!/usr/bin/env python3

import os
import sys
import google.generativeai as genai

def test_gemini_api():
    """Test Gemini API connectivity and list available models."""

    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ No GEMINI_API_KEY environment variable found")
        print("Please set it with: export GEMINI_API_KEY=your_key_here")
        return False

    try:
        # Configure Gemini
        genai.configure(api_key=api_key)

        print("🔍 Testing Gemini API connectivity...")

        # List available models
        print("\n📋 Available models:")
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✅ {model.name}")

        # Test with gemini-2.5-pro
        print(f"\n🧪 Testing text generation with gemini-2.5-pro...")
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content("Say hello in a professional manner for a README file.")

        print("✅ API test successful!")
        print(f"📄 Sample response: {response.text[:100]}...")
        return True

    except Exception as e:
        print(f"❌ API test failed: {str(e)}")

        # Try with alternative model names
        alternative_models = ['gemini-1.5-pro', 'gemini-1.0-pro']
        for alt_model in alternative_models:
            try:
                print(f"\n🔄 Trying alternative model: {alt_model}")
                model = genai.GenerativeModel(alt_model)
                response = model.generate_content("Test")
                print(f"✅ {alt_model} works!")
                print(f"💡 Update your GeminiService to use: {alt_model}")
                return True
            except Exception as alt_e:
                print(f"❌ {alt_model} failed: {str(alt_e)}")

        return False

if __name__ == "__main__":
    print("🚀 Gemini API Test")
    print("==================")

    success = test_gemini_api()

    if success:
        print("\n🎉 Your API key is working!")
        print("You can now use the ai-readme CLI.")
    else:
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your API key at: https://makersuite.google.com/app/apikey")
        print("2. Make sure the key has proper permissions")
        print("3. Try regenerating the API key")
        print("4. Check if your region is supported")

    sys.exit(0 if success else 1)