"""
Quick API test script for Browser Profiles endpoints.
Run this to verify all endpoints are working.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials (from your existing database)
LOGIN_DATA = {
    "username": "admin",  # or your test user
    "password": "admin123"  # update with correct password
}

def get_token():
    """Login and get JWT token."""
    print("🔐 Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", data=LOGIN_DATA)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_create_profile(token):
    """Test POST /browser-profiles - Create profile."""
    print("\n📝 Testing: Create Browser Profile")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "profile_name": "Test Profile - Windows 11",
        "os_type": "windows",
        "browser_type": "chromium",
        "description": "Automated test profile"
    }
    
    response = requests.post(
        f"{BASE_URL}/browser-profiles",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        profile = response.json()
        print(f"✅ Profile created successfully!")
        print(f"   ID: {profile['id']}")
        print(f"   Name: {profile['profile_name']}")
        print(f"   OS: {profile['os_type']}")
        print(f"   Browser: {profile['browser_type']}")
        return profile['id']
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None

def test_list_profiles(token):
    """Test GET /browser-profiles - List profiles."""
    print("\n📋 Testing: List Browser Profiles")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/browser-profiles", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} profile(s)")
        for profile in data['profiles']:
            print(f"   - {profile['profile_name']} ({profile['os_type']}/{profile['browser_type']})")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

def test_get_profile(token, profile_id):
    """Test GET /browser-profiles/{id} - Get specific profile."""
    print(f"\n🔍 Testing: Get Profile #{profile_id}")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/browser-profiles/{profile_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile retrieved successfully!")
        print(f"   Name: {profile['profile_name']}")
        print(f"   Created: {profile['created_at']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

def test_update_profile(token, profile_id):
    """Test PATCH /browser-profiles/{id} - Update profile."""
    print(f"\n✏️  Testing: Update Profile #{profile_id}")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "description": "Updated description via API test"
    }
    
    response = requests.patch(
        f"{BASE_URL}/browser-profiles/{profile_id}",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile updated successfully!")
        print(f"   Description: {profile['description']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

def test_delete_profile(token, profile_id):
    """Test DELETE /browser-profiles/{id} - Delete profile."""
    print(f"\n🗑️  Testing: Delete Profile #{profile_id}")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BASE_URL}/browser-profiles/{profile_id}",
        headers=headers
    )
    
    if response.status_code == 204:
        print(f"✅ Profile deleted successfully!")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run all API tests."""
    print("=" * 60)
    print("Browser Profiles API Test Suite")
    print("=" * 60)
    
    # Get authentication token
    token = get_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # Test create profile
    profile_id = test_create_profile(token)
    if not profile_id:
        print("\n❌ Cannot proceed without profile ID")
        return
    
    # Test list profiles
    test_list_profiles(token)
    
    # Test get specific profile
    test_get_profile(token, profile_id)
    
    # Test update profile
    test_update_profile(token, profile_id)
    
    # Test delete profile (cleanup)
    test_delete_profile(token, profile_id)
    
    print("\n" + "=" * 60)
    print("✅ All API tests completed!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Open Swagger UI: http://localhost:8000/docs")
    print("   2. Click 'Authorize' button")
    print("   3. Login with your credentials")
    print("   4. Try the browser-profiles endpoints")
    print("   5. Test profile export/upload workflows")

if __name__ == "__main__":
    main()
