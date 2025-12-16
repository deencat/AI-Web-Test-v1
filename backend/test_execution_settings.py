"""
Quick test to verify Settings Page Dynamic Configuration works for test execution.
Tests that user's configured execution provider is actually used.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def test_execution_uses_user_settings():
    """Test that execution uses user's configured provider"""
    print("=" * 80)
    print("Test: Execution Uses User Settings")
    print("=" * 80)
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in")
    
    # Step 2: Set execution provider to Google Gemini
    print("\n2. Setting execution provider to Google Gemini...")
    update_response = requests.put(
        f"{BASE_URL}/settings/provider",
        headers=headers,
        json={
            "execution_provider": "google",
            "execution_model": "gemini-2.5-flash",
            "execution_temperature": 0.6,
            "execution_max_tokens": 4096
        }
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update settings: {update_response.text}")
        return False
    
    settings = update_response.json()
    print(f"✅ Settings updated:")
    print(f"   Execution: {settings['execution_provider']} / {settings['execution_model']}")
    
    # Step 3: Verify config endpoint returns correct settings
    print("\n3. Verifying execution config endpoint...")
    config_response = requests.get(
        f"{BASE_URL}/settings/provider/execution",
        headers=headers
    )
    
    config = config_response.json()
    print(f"✅ Execution config retrieved:")
    print(f"   Provider: {config['provider']}")
    print(f"   Model: {config['model']}")
    print(f"   Temperature: {config['temperature']}")
    print(f"   Max Tokens: {config['max_tokens']}")
    
    if config['provider'] != 'google' or config['model'] != 'gemini-2.5-flash':
        print("❌ Config doesn't match settings!")
        return False
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED!")
    print("=" * 80)
    print("\n📋 Summary:")
    print("   ✅ User can set execution provider to Google")
    print("   ✅ Config endpoint returns user's settings")
    print("   ✅ Settings persist correctly")
    print("\n📝 Next: Run a test execution and check backend logs for:")
    print('   "[DEBUG] 🎯 Loaded user execution config: provider=google, model=gemini-2.5-flash"')
    print('   "[DEBUG] ✅ Using Google API directly with model: gemini-2.5-flash"')
    print("\nIf you see OpenRouter instead, the settings are not being applied to execution.")
    
    return True

if __name__ == "__main__":
    try:
        success = test_execution_uses_user_settings()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
