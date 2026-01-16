"""
Quick test script to verify OpenAI API integration
Run: python test_openai.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.conf import settings

def test_openai_setup():
    print("=" * 50)
    print("OpenAI API Configuration Test")
    print("=" * 50)
    
    # Check if API key is loaded
    api_key = settings.OPENAI_API_KEY
    if api_key:
        # Mask the key for security
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✓ API Key loaded: {masked_key}")
        print(f"✓ Key length: {len(api_key)} characters")
    else:
        print("✗ API Key not found!")
        print("Make sure OPENAI_API_KEY is set in your .env file")
        return
    
    # Test OpenAI connection
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("\nTesting OpenAI API connection...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from School Portal!' in one sentence."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✓ API Connection successful!")
        print(f"✓ Response: {result}")
        print("\n" + "=" * 50)
        print("OpenAI integration is ready! 🎉")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ API Connection failed: {str(e)}")
        print("\nPlease check:")
        print("1. Your API key is correct")
        print("2. You have credits in your OpenAI account")
        print("3. Your internet connection is working")

if __name__ == "__main__":
    test_openai_setup()
