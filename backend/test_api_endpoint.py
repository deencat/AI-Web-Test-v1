"""Test the /api/v1/tests endpoint to verify JSON parsing fix"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from requests.auth import HTTPBasicAuth

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"
BASE_URL = "http://localhost:8000"

def test_list_tests():
    """Test the list tests endpoint"""
    print("\n" + "="*60)
    print("Testing GET /api/v1/tests endpoint")
    print("="*60)
    
    try:
        # First, get auth token
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
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
        print(f"✅ Login successful, got token")
        
        # Now test the /tests endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/tests", headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Endpoint returned data without Pydantic errors")
            print(f"\nTotal tests: {data['total']}")
            print(f"Tests returned: {len(data['items'])}")
            
            # Check the merged test cases (IDs 67 and 68)
            for item in data['items']:
                if item['id'] in [67, 68]:
                    print(f"\n--- Merged Test Case ID: {item['id']} ---")
                    print(f"Title: {item['title']}")
                    print(f"Steps type: {type(item['steps']).__name__}")
                    print(f"Steps value: {item['steps'][:2] if isinstance(item['steps'], list) else 'NOT A LIST!'}...")
                    print(f"Tags type: {type(item['tags']).__name__}")
                    print(f"Tags value: {item['tags']}")
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_list_tests()
