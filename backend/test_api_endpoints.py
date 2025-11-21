"""Test API endpoints for Day 3."""
import requests
import json
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

# Global token storage
TOKEN = None


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)


def print_test(name, passed, details=""):
    """Print test result."""
    status = "[OK]" if passed else "[X]"
    print(f"{status} {name}")
    if details:
        print(f"    {details}")


def test_health():
    """Test health endpoint."""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_test("Root endpoint", True, f"Version: {data.get('version', 'N/A')}")
            return True
        else:
            print_test("Root endpoint", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Root endpoint", False, str(e))
        return False


def test_login():
    """Test login and get token."""
    global TOKEN
    print_section("Test 2: Authentication")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{API_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            TOKEN = data["access_token"]
            print_test("Login successful", True, f"Token: {TOKEN[:30]}...")
            return True
        else:
            print_test("Login failed", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Login error", False, str(e))
        return False


def test_generate_tests():
    """Test test generation endpoint."""
    print_section("Test 3: Test Generation")
    
    if not TOKEN:
        print_test("Test generation", False, "No authentication token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        payload = {
            "requirement": "User can login with username and password",
            "test_type": "e2e",
            "num_tests": 2
        }
        
        print("Generating tests (this may take 5-10 seconds)...")
        response = requests.post(
            f"{API_URL}/tests/generate",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            num_tests = len(data.get("test_cases", []))
            model = data.get("metadata", {}).get("model", "unknown")
            tokens = data.get("metadata", {}).get("tokens", 0)
            print_test("Test generation", True, 
                      f"Generated {num_tests} tests using {model} ({tokens} tokens)")
            
            # Show first test
            if data.get("test_cases"):
                first_test = data["test_cases"][0]
                print(f"    First test: {first_test.get('title', 'N/A')}")
            
            return True
        else:
            print_test("Test generation", False, 
                      f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except requests.Timeout:
        print_test("Test generation", False, "Request timed out (>30s)")
        return False
    except Exception as e:
        print_test("Test generation", False, str(e))
        return False


def test_create_test_case():
    """Test creating a test case."""
    print_section("Test 4: Create Test Case")
    
    if not TOKEN:
        print_test("Create test case", False, "No authentication token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        payload = {
            "title": "Test login with valid credentials",
            "description": "Verify user can login with correct username and password",
            "test_type": "e2e",
            "priority": "high",
            "status": "pending",
            "steps": [
                "Navigate to login page",
                "Enter valid username",
                "Enter valid password",
                "Click login button"
            ],
            "expected_result": "User is logged in and redirected to dashboard",
            "preconditions": "User account exists",
            "test_data": {
                "username": "testuser",
                "password": "Test123!"
            }
        }
        
        response = requests.post(
            f"{API_URL}/tests",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 201:
            data = response.json()
            test_id = data.get("id")
            print_test("Create test case", True, f"Created test case ID: {test_id}")
            return test_id
        else:
            print_test("Create test case", False, 
                      f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        print_test("Create test case", False, str(e))
        return None


def test_list_test_cases():
    """Test listing test cases."""
    print_section("Test 5: List Test Cases")
    
    if not TOKEN:
        print_test("List test cases", False, "No authentication token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(
            f"{API_URL}/tests?skip=0&limit=10",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            items = len(data.get("items", []))
            print_test("List test cases", True, f"Found {total} total, showing {items}")
            return True
        else:
            print_test("List test cases", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("List test cases", False, str(e))
        return False


def test_get_test_case(test_id):
    """Test getting a specific test case."""
    print_section("Test 6: Get Test Case")
    
    if not TOKEN or not test_id:
        print_test("Get test case", False, "No token or test ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(
            f"{API_URL}/tests/{test_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "N/A")
            print_test("Get test case", True, f"Retrieved: {title}")
            return True
        else:
            print_test("Get test case", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Get test case", False, str(e))
        return False


def test_update_test_case(test_id):
    """Test updating a test case."""
    print_section("Test 7: Update Test Case")
    
    if not TOKEN or not test_id:
        print_test("Update test case", False, "No token or test ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        payload = {
            "status": "passed",
            "priority": "medium"
        }
        
        response = requests.put(
            f"{API_URL}/tests/{test_id}",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "N/A")
            priority = data.get("priority", "N/A")
            print_test("Update test case", True, f"Updated status={status}, priority={priority}")
            return True
        else:
            print_test("Update test case", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Update test case", False, str(e))
        return False


def test_get_statistics():
    """Test getting statistics."""
    print_section("Test 8: Get Statistics")
    
    if not TOKEN:
        print_test("Get statistics", False, "No authentication token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(
            f"{API_URL}/tests/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            by_status = data.get("by_status", {})
            print_test("Get statistics", True, f"Total: {total}, By status: {by_status}")
            return True
        else:
            print_test("Get statistics", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Get statistics", False, str(e))
        return False


def test_delete_test_case(test_id):
    """Test deleting a test case."""
    print_section("Test 9: Delete Test Case")
    
    if not TOKEN or not test_id:
        print_test("Delete test case", False, "No token or test ID")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.delete(
            f"{API_URL}/tests/{test_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            print_test("Delete test case", True, f"Deleted test case ID: {test_id}")
            return True
        else:
            print_test("Delete test case", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Delete test case", False, str(e))
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("DAY 3 API ENDPOINT TESTS")
    print("=" * 80)
    print("\nWaiting for server to start...")
    time.sleep(3)  # Give server time to start
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: Login
    results.append(("Authentication", test_login()))
    
    if TOKEN:
        # Test 3: Generate tests
        results.append(("Test Generation", test_generate_tests()))
        
        # Test 4: Create test case
        test_id = test_create_test_case()
        results.append(("Create Test Case", test_id is not None))
        
        # Test 5: List test cases
        results.append(("List Test Cases", test_list_test_cases()))
        
        if test_id:
            # Test 6: Get test case
            results.append(("Get Test Case", test_get_test_case(test_id)))
            
            # Test 7: Update test case
            results.append(("Update Test Case", test_update_test_case(test_id)))
            
            # Test 8: Get statistics
            results.append(("Get Statistics", test_get_statistics()))
            
            # Test 9: Delete test case
            results.append(("Delete Test Case", test_delete_test_case(test_id)))
    
    # Summary
    print_section("SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASSED" if result else "[X] FAILED"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 80)
    if passed == total:
        print(f"[OK] ALL TESTS PASSED ({passed}/{total})")
        print("[OK] Day 3 API endpoints are working!")
        print("\nNext steps:")
        print("1. Check Swagger UI at http://localhost:8000/docs")
        print("2. Test endpoints manually if needed")
        print("3. Proceed to commit and Day 3 completion report")
        return True
    else:
        print(f"[X] SOME TESTS FAILED ({passed}/{total} passed)")
        print("[!] Please check the errors above")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

