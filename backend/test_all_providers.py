"""
Test that test generation works with all three providers.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def test_provider(provider_name, provider_config):
    """Test generation with a specific provider"""
    print(f"\n{'='*80}")
    print(f"Testing: {provider_name}")
    print(f"{'='*80}")
    
    # Login
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Set provider
    print(f"Setting generation provider to {provider_config['provider']}...")
    update_response = requests.put(
        f"{BASE_URL}/settings/provider",
        headers=headers,
        json=provider_config
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update settings: {update_response.text}")
        return False
    
    settings = update_response.json()
    print(f"✅ Provider configured: {settings['generation_provider']} / {settings['generation_model']}")
    
    # Generate test
    print(f"Generating test case...")
    gen_response = requests.post(
        f"{BASE_URL}/tests/generate",
        headers=headers,
        json={
            "requirement": "User can view dashboard",
            "test_type": "e2e",
            "num_tests": 1
        }
    )
    
    if gen_response.status_code == 200:
        result = gen_response.json()
        print(f"✅ Test generation successful!")
        print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
        print(f"   Tests: {len(result.get('test_cases', []))}")
        print(f"   Tokens: {result.get('metadata', {}).get('tokens', 0)}")
        return True
    else:
        print(f"❌ Test generation failed!")
        print(f"   Status: {gen_response.status_code}")
        print(f"   Error: {gen_response.text}")
        return False

def main():
    print("=" * 80)
    print("Multi-Provider Test Generation Validation")
    print("=" * 80)
    
    providers = {
        "Google Gemini": {
            "generation_provider": "google",
            "generation_model": "gemini-2.5-flash",
            "generation_temperature": 0.7,
            "generation_max_tokens": 2000
        },
        "Cerebras": {
            "generation_provider": "cerebras",
            "generation_model": "llama3.3-70b",
            "generation_temperature": 0.5,
            "generation_max_tokens": 8192
        },
        "OpenRouter": {
            "generation_provider": "openrouter",
            "generation_model": "meta-llama/llama-3.3-70b-instruct:free",
            "generation_temperature": 0.7,
            "generation_max_tokens": 4096
        }
    }
    
    results = {}
    for name, config in providers.items():
        try:
            results[name] = test_provider(name, config)
        except Exception as e:
            print(f"❌ Exception testing {name}: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL PROVIDERS WORKING!")
    else:
        print("❌ SOME PROVIDERS FAILED")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
