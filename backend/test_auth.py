"""Test authentication flow end-to-end."""
import requests
import json
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("Testing AI Web Test Backend Authentication")
print("=" * 60)

# Step 1: Login
print("\n[Step 1] Testing Login...")
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("[OK] Login successful!")
        print(f"Token Type: {token_data['token_type']}")
        print(f"Access Token: {token_data['access_token'][:50]}...")
        
        access_token = token_data['access_token']
        
        # Step 2: Get current user
        print("\n[Step 2] Testing /auth/me...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        me_response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers
        )
        
        print(f"Status Code: {me_response.status_code}")
        
        if me_response.status_code == 200:
            user_data = me_response.json()
            print("[OK] Authentication successful!")
            print("\nUser Info:")
            print(json.dumps(user_data, indent=2))
        else:
            print(f"[ERROR] Failed to get user info")
            print(f"Response: {me_response.text}")
    else:
        print(f"[ERROR] Login failed")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server!")
    print("Make sure the server is running:")
    print("  cd backend")
    print("  .\\run_server.ps1")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print("\n" + "=" * 60)

