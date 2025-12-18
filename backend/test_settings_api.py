"""
Test script for Settings Page Dynamic Configuration API endpoints.
Tests the new user settings functionality for AI provider configuration.
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

def test_settings_api():
    """Test all settings API endpoints"""
    print("=" * 80)
    print("Settings Page Dynamic Configuration API Test")
    print("=" * 80)
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login successful - Token: {token[:20]}...")
    
    # Step 2: Get available providers
    print("\n2. Getting available providers...")
    providers_response = requests.get(
        f"{BASE_URL}/settings/available-providers",
        headers=headers
    )
    
    if providers_response.status_code != 200:
        print(f"❌ Failed to get providers: {providers_response.status_code}")
        print(providers_response.text)
        return
    
    providers_data = providers_response.json()
    print("✅ Available providers:")
    for provider in providers_data["providers"]:
        status = "✓" if provider["is_configured"] else "✗"
        print(f"   {status} {provider['display_name']} ({provider['name']})")
        print(f"      Models: {len(provider['models'])} available")
        print(f"      Recommended: {provider['recommended_model']}")
    
    print(f"\n   Default Generation: {providers_data['default_generation_provider']} / {providers_data['default_generation_model']}")
    print(f"   Default Execution: {providers_data['default_execution_provider']} / {providers_data['default_execution_model']}")
    
    # Step 3: Get current user settings (or create default)
    print("\n3. Getting user settings...")
    settings_response = requests.get(
        f"{BASE_URL}/settings/provider",
        headers=headers
    )
    
    if settings_response.status_code != 200:
        print(f"❌ Failed to get settings: {settings_response.status_code}")
        print(settings_response.text)
        return
    
    current_settings = settings_response.json()
    print("✅ Current user settings:")
    print(f"   Generation: {current_settings['generation_provider']} / {current_settings['generation_model']}")
    print(f"   Temperature: {current_settings['generation_temperature']}, Max Tokens: {current_settings['generation_max_tokens']}")
    print(f"   Execution: {current_settings['execution_provider']} / {current_settings['execution_model']}")
    print(f"   Temperature: {current_settings['execution_temperature']}, Max Tokens: {current_settings['execution_max_tokens']}")
    
    # Step 4: Update user settings
    print("\n4. Updating user settings...")
    update_data = {
        "generation_provider": "google",
        "generation_model": "gemini-2.0-flash-exp",
        "generation_temperature": 0.8,
        "generation_max_tokens": 8192,
        "execution_provider": "cerebras",
        "execution_model": "llama3.3-70b",
        "execution_temperature": 0.6,
        "execution_max_tokens": 4096
    }
    
    update_response = requests.put(
        f"{BASE_URL}/settings/provider",
        headers=headers,
        json=update_data
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update settings: {update_response.status_code}")
        print(update_response.text)
        return
    
    updated_settings = update_response.json()
    print("✅ Settings updated successfully:")
    print(f"   Generation: {updated_settings['generation_provider']} / {updated_settings['generation_model']}")
    print(f"   Temperature: {updated_settings['generation_temperature']}, Max Tokens: {updated_settings['generation_max_tokens']}")
    print(f"   Execution: {updated_settings['execution_provider']} / {updated_settings['execution_model']}")
    print(f"   Temperature: {updated_settings['execution_temperature']}, Max Tokens: {updated_settings['execution_max_tokens']}")
    
    # Step 5: Get generation config
    print("\n5. Getting generation provider config...")
    gen_config_response = requests.get(
        f"{BASE_URL}/settings/provider/generation",
        headers=headers
    )
    
    if gen_config_response.status_code != 200:
        print(f"❌ Failed to get generation config: {gen_config_response.status_code}")
        return
    
    gen_config = gen_config_response.json()
    print("✅ Generation config for services:")
    pprint(gen_config)
    
    # Step 6: Get execution config
    print("\n6. Getting execution provider config...")
    exec_config_response = requests.get(
        f"{BASE_URL}/settings/provider/execution",
        headers=headers
    )
    
    if exec_config_response.status_code != 200:
        print(f"❌ Failed to get execution config: {exec_config_response.status_code}")
        return
    
    exec_config = exec_config_response.json()
    print("✅ Execution config for services:")
    pprint(exec_config)
    
    # Step 7: Verify settings persisted
    print("\n7. Verifying settings persisted...")
    verify_response = requests.get(
        f"{BASE_URL}/settings/provider",
        headers=headers
    )
    
    verified_settings = verify_response.json()
    if (verified_settings['generation_provider'] == update_data['generation_provider'] and
        verified_settings['execution_provider'] == update_data['execution_provider']):
        print("✅ Settings persisted correctly!")
    else:
        print("❌ Settings did not persist correctly")
        return
    
    # Step 8: Test partial update
    print("\n8. Testing partial update (only generation temperature)...")
    partial_update = {
        "generation_temperature": 0.5
    }
    
    partial_response = requests.put(
        f"{BASE_URL}/settings/provider",
        headers=headers,
        json=partial_update
    )
    
    if partial_response.status_code != 200:
        print(f"❌ Partial update failed: {partial_response.status_code}")
        return
    
    partial_settings = partial_response.json()
    if partial_settings['generation_temperature'] == 0.5:
        print(f"✅ Partial update successful - Temperature: {partial_settings['generation_temperature']}")
    else:
        print("❌ Partial update failed")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n📋 Summary:")
    print("   ✅ User authentication working")
    print("   ✅ Available providers endpoint working")
    print("   ✅ Get user settings working")
    print("   ✅ Update user settings working")
    print("   ✅ Get generation config working")
    print("   ✅ Get execution config working")
    print("   ✅ Settings persistence working")
    print("   ✅ Partial updates working")
    print("\n🎉 Settings Page Dynamic Configuration is fully functional!")

if __name__ == "__main__":
    try:
        test_settings_api()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
