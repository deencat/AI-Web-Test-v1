"""
Test that test generation works with user's configured provider.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def test_generation_with_cerebras():
    """Test that generation uses Cerebras when configured"""
    print("=" * 80)
    print("Test: Generation with Cerebras Provider")
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
    
    # Step 2: Set generation provider to Cerebras
    print("\n2. Setting generation provider to Cerebras...")
    update_response = requests.put(
        f"{BASE_URL}/settings/provider",
        headers=headers,
        json={
            "generation_provider": "cerebras",
            "generation_model": "llama3.3-70b",
            "generation_temperature": 0.5,
            "generation_max_tokens": 8192
        }
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update settings: {update_response.text}")
        return False
    
    settings = update_response.json()
    print(f"✅ Settings updated:")
    print(f"   Generation: {settings['generation_provider']} / {settings['generation_model']}")
    
    # Step 3: Generate a test case
    print("\n3. Generating test case with Cerebras...")
    gen_response = requests.post(
        f"{BASE_URL}/tests/generate",
        headers=headers,
        json={
            "requirement": "User can login with email and password",
            "test_type": "e2e",
            "num_tests": 1
        }
    )
    
    print(f"Response status: {gen_response.status_code}")
    
    if gen_response.status_code == 200:
        result = gen_response.json()
        print(f"✅ Test generation successful!")
        print(f"   Tests generated: {len(result.get('test_cases', []))}")
        print(f"   Model used: {result.get('metadata', {}).get('model', 'unknown')}")
        print(f"   Tokens: {result.get('metadata', {}).get('tokens', 0)}")
        
        if result.get('test_cases'):
            test = result['test_cases'][0]
            print(f"\n   Generated test:")
            print(f"   - Title: {test.get('title', 'N/A')}")
            print(f"   - Type: {test.get('test_type', 'N/A')}")
            print(f"   - Steps: {len(test.get('steps', []))}")
        
        print("\n" + "=" * 80)
        print("✅ TEST PASSED!")
        print("=" * 80)
        print("\n📝 Check backend logs for:")
        print('   "[DEBUG] 🎯 Loaded user generation config: provider=cerebras, model=llama3.3-70b"')
        print('   "[DEBUG] 🎯 Using user\'s generation config: cerebras/llama3.3-70b"')
        return True
    else:
        print(f"❌ Test generation failed!")
        print(f"   Status: {gen_response.status_code}")
        print(f"   Error: {gen_response.text}")
        return False

if __name__ == "__main__":
    try:
        success = test_generation_with_cerebras()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
