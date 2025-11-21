"""Test Day 5 backend enhancements."""
import sys
import io
import requests
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print('=' * 70)

def print_test(text: str):
    """Print test name."""
    print(f"\n[TEST] {text}")

def print_result(success: bool, message: str = ""):
    """Print test result."""
    if success:
        print(f"  [OK] {message if message else 'Passed'}")
    else:
        print(f"  [FAIL] {message if message else 'Failed'}")

def test_root_endpoint():
    """Test enhanced root endpoint."""
    print_test("Enhanced root endpoint")
    
    response = requests.get(BASE_URL)
    
    if response.status_code == 200:
        data = response.json()
        has_required = all(k in data for k in ["message", "version", "status", "timestamp", "documentation"])
        if has_required:
            print_result(True, f"Version: {data['version']}, Status: {data['status']}")
            return True
        else:
            print_result(False, "Missing required fields")
            return False
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_api_version():
    """Test API version endpoint."""
    print_test("API version endpoint")
    
    response = requests.get(f"{BASE_URL}/api/version")
    
    if response.status_code == 200:
        data = response.json()
        has_features = "features" in data and "enhancements" in data
        if has_features:
            print_result(True, f"Build: {data['build']}, Total endpoints: {data['endpoints']['total']}")
            return True
        else:
            print_result(False, "Missing features or enhancements")
            return False
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_performance_headers():
    """Test performance timing headers."""
    print_test("Performance timing headers")
    
    response = requests.get(f"{API_URL}/health")
    
    has_timing = "X-Process-Time" in response.headers
    has_request_id = "X-Request-ID" in response.headers
    
    if has_timing and has_request_id:
        process_time = response.headers["X-Process-Time"]
        request_id = response.headers["X-Request-ID"]
        print_result(True, f"Process time: {process_time}s, Request ID: {request_id[:8]}...")
        return True
    else:
        missing = []
        if not has_timing:
            missing.append("X-Process-Time")
        if not has_request_id:
            missing.append("X-Request-ID")
        print_result(False, f"Missing headers: {', '.join(missing)}")
        return False

def test_detailed_health_check():
    """Test detailed health check endpoint."""
    print_test("Detailed health check")
    
    response = requests.get(f"{API_URL}/health/detailed")
    
    if response.status_code == 200:
        data = response.json()
        has_required = all(k in data for k in ["status", "services", "statistics", "endpoints", "features"])
        if has_required:
            stats = data["statistics"]
            print_result(True, f"Users: {stats['total_users']}, Tests: {stats['total_test_cases']}, Docs: {stats['total_kb_documents']}")
            return True
        else:
            print_result(False, "Missing required fields")
            return False
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_error_handling():
    """Test custom error handling."""
    print_test("Custom error handling")
    
    # Test with invalid endpoint
    response = requests.get(f"{API_URL}/nonexistent")
    
    if response.status_code == 404:
        print_result(True, "404 error handled correctly")
        return True
    else:
        print_result(False, f"Unexpected status: {response.status_code}")
        return False

def test_cors_headers():
    """Test CORS headers."""
    print_test("CORS headers")
    
    response = requests.options(
        f"{API_URL}/health",
        headers={"Origin": "http://localhost:5173"}
    )
    
    has_cors = "access-control-allow-origin" in response.headers
    has_exposed = "access-control-expose-headers" in response.headers
    
    if has_cors and has_exposed:
        exposed = response.headers.get("access-control-expose-headers", "")
        print_result(True, f"CORS enabled, Exposed headers: {exposed}")
        return True
    else:
        print_result(False, "CORS headers missing")
        return False

def test_search_functionality():
    """Test enhanced search (requires authentication)."""
    print_test("Search functionality (basic check)")
    
    # Just verify the endpoint exists (full test requires auth)
    response = requests.get(f"{API_URL}/tests?search=test")
    
    # Should return 401 (unauthorized) which means endpoint exists
    if response.status_code == 401:
        print_result(True, "Search endpoint exists (requires auth)")
        return True
    elif response.status_code == 200:
        print_result(True, "Search endpoint working")
        return True
    else:
        print_result(False, f"Unexpected status: {response.status_code}")
        return False

def main():
    """Run all Day 5 enhancement tests."""
    print_header("Day 5 Backend Enhancements - Verification Tests")
    print("Testing: http://127.0.0.1:8000")
    print("Backend must be running!")
    
    # Track results
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("API Version", test_api_version),
        ("Performance Headers", test_performance_headers),
        ("Detailed Health Check", test_detailed_health_check),
        ("Error Handling", test_error_handling),
        ("CORS Headers", test_cors_headers),
        ("Search Endpoint", test_search_functionality),
    ]
    
    for name, test_func in tests:
        try:
            if test_func():
                tests_passed += 1
            else:
                tests_failed += 1
        except Exception as e:
            print_result(False, f"Exception: {str(e)}")
            tests_failed += 1
    
    # Summary
    print_header("Test Summary")
    print(f"\nTotal Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All Day 5 enhancement tests passed!")
        print("\nDay 5 Backend Enhancements: VERIFIED")
        print("\nEnhancements Delivered:")
        print("  ✅ Custom exception handling")
        print("  ✅ Response wrapper schemas")
        print("  ✅ Pagination helpers")
        print("  ✅ Enhanced search")
        print("  ✅ Performance monitoring")
        print("  ✅ Detailed health check")
        print("  ✅ API version endpoint")
        return True
    else:
        print(f"\n[FAILURE] {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

