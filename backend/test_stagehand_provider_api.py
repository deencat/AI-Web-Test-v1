"""
Quick test script for stagehand provider API endpoints
Sprint 5: Dual Stagehand Provider System
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# You'll need to get an actual token from login
# For now, this is just to show how to test

def test_get_stagehand_provider(token):
    """Test GET /settings/stagehand-provider"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/settings/stagehand-provider", headers=headers)
    
    print(f"\n📋 GET /settings/stagehand-provider")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response


def test_update_stagehand_provider(token, provider):
    """Test PUT /settings/stagehand-provider"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"provider": provider}
    
    response = requests.put(
        f"{BASE_URL}/settings/stagehand-provider",
        headers=headers,
        json=data
    )
    
    print(f"\n📝 PUT /settings/stagehand-provider (provider={provider})")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response


def test_full_workflow():
    """Test the complete workflow"""
    print("=" * 60)
    print("🧪 Testing Stagehand Provider API Endpoints")
    print("=" * 60)
    
    # First, login to get token
    print("\n🔐 Step 1: Login")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful, got token")
    
    # Test GET endpoint
    print("\n🔍 Step 2: Get current stagehand provider")
    get_response = test_get_stagehand_provider(token)
    
    if get_response.status_code == 200:
        current_provider = get_response.json()["provider"]
        print(f"✅ Current provider: {current_provider}")
    else:
        print(f"❌ Failed to get provider")
        return
    
    # Test PUT endpoint - switch to typescript
    print("\n🔄 Step 3: Switch to TypeScript provider")
    update_response = test_update_stagehand_provider(token, "typescript")
    
    if update_response.status_code == 200:
        new_provider = update_response.json()["provider"]
        print(f"✅ Successfully switched to: {new_provider}")
    else:
        print(f"❌ Failed to update provider")
        print(update_response.text)
        return
    
    # Verify the change
    print("\n✅ Step 4: Verify the change")
    verify_response = test_get_stagehand_provider(token)
    
    if verify_response.status_code == 200:
        verified_provider = verify_response.json()["provider"]
        if verified_provider == "typescript":
            print(f"✅ Verification successful: {verified_provider}")
        else:
            print(f"❌ Verification failed: expected 'typescript', got '{verified_provider}'")
    
    # Switch back to python
    print("\n🔄 Step 5: Switch back to Python provider")
    revert_response = test_update_stagehand_provider(token, "python")
    
    if revert_response.status_code == 200:
        final_provider = revert_response.json()["provider"]
        print(f"✅ Successfully switched back to: {final_provider}")
    else:
        print(f"❌ Failed to revert provider")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_full_workflow()
