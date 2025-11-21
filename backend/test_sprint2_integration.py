#!/usr/bin/env python3
"""
Sprint 2 Integration Test Suite

This comprehensive test suite validates all Sprint 2 features working together:
1. Test Generation (with KB context)
2. Test Management (CRUD operations)
3. KB Management (upload, categorization)
4. Test Execution Tracking (full lifecycle)

Tests real-world workflows end-to-end.
"""

import requests
import json
import sys
import time
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


def print_header(text):
    """Print a colored header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")


def print_test(text):
    """Print test name."""
    print(f"\n{CYAN}TEST: {text}{RESET}")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}  [OK] {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}  [FAIL] {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}  - {text}{RESET}")


class TestResults:
    """Track test results."""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self):
        self.total += 1
        self.passed += 1
    
    def add_fail(self, error_msg):
        self.total += 1
        self.failed += 1
        self.errors.append(error_msg)
    
    def print_summary(self):
        print_header("TEST SUMMARY")
        print(f"\n  Total Tests: {self.total}")
        print(f"  {GREEN}Passed: {self.passed}{RESET}")
        print(f"  {RED}Failed: {self.failed}{RESET}")
        
        if self.failed > 0:
            print(f"\n{RED}FAILURES:{RESET}")
            for error in self.errors:
                print(f"  {RED}- {error}{RESET}")
        
        pass_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\n  Pass Rate: {pass_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{GREEN}[SUCCESS] ALL TESTS PASSED!{RESET}")
            return 0
        else:
            print(f"\n{RED}[FAILURE] SOME TESTS FAILED{RESET}")
            return 1


results = TestResults()


def login():
    """Login and get access token."""
    print_header("AUTHENTICATION")
    print_test("Admin Login")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"Logged in as {TEST_USERNAME}")
        results.add_pass()
        return token
    else:
        print_error(f"Login failed: {response.text}")
        results.add_fail("Authentication failed")
        sys.exit(1)


def test_kb_upload_and_categorization(token):
    """Test KB document upload with category assignment."""
    print_header("KNOWLEDGE BASE - UPLOAD & CATEGORIZATION")
    
    # Test 1: Get categories
    print_test("Get predefined categories")
    response = requests.get(
        f"{BASE_URL}/kb/categories",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        categories = response.json()
        if len(categories) >= 8:
            print_success(f"Found {len(categories)} categories")
            print_info(f"Categories: {', '.join([c['name'] for c in categories[:5]])}...")
            results.add_pass()
            test_category_id = categories[0]['id']
        else:
            print_error(f"Expected at least 8 categories, found {len(categories)}")
            results.add_fail("Insufficient categories")
            return None
    else:
        print_error(f"Failed to get categories: {response.status_code}")
        results.add_fail("Category retrieval failed")
        return None
    
    # Test 2: Create test document
    print_test("Create test document with category")
    
    test_content = """# E-Commerce Test Documentation
    
## Login Feature Test Cases

1. **Valid Login Test**
   - Navigate to login page
   - Enter valid username and password
   - Click login button
   - Verify dashboard loads

2. **Invalid Password Test**
   - Navigate to login page
   - Enter valid username
   - Enter invalid password
   - Verify error message displays

3. **Empty Fields Test**
   - Navigate to login page
   - Leave fields empty
   - Click login button
   - Verify validation messages

## Shopping Cart Test Cases

1. **Add to Cart**
   - Browse product catalog
   - Click "Add to Cart"
   - Verify cart counter updates
   - Verify product appears in cart
"""
    
    # Create a test file
    test_file = Path("test_kb_doc.md")
    test_file.write_text(test_content)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_kb_doc.md', f, 'text/markdown')}
            data = {
                'title': 'E-Commerce Test Documentation',
                'category_id': test_category_id,
                'description': 'E-Commerce test documentation for Sprint 2 integration testing'
            }
            
            response = requests.post(
                f"{BASE_URL}/kb/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data=data
            )
        
        if response.status_code == 201:
            doc = response.json()
            print_success(f"Document uploaded: {doc['filename']}")
            print_info(f"Category: {doc.get('category', {}).get('name', 'N/A')}")
            print_info(f"Size: {doc['file_size']} bytes")
            results.add_pass()
            return doc['id']
        else:
            print_error(f"Upload failed: {response.text}")
            results.add_fail("Document upload failed")
            return None
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_generate_tests_with_kb(token, kb_doc_id):
    """Test test generation using KB context."""
    print_header("TEST GENERATION WITH KB CONTEXT")
    
    print_test("Generate tests from requirements with KB context")
    
    requirements = """Test the login functionality of an e-commerce website:
- User should be able to log in with valid credentials
- Invalid credentials should show error message
- Empty fields should trigger validation
- After login, user should see their dashboard
"""
    
    response = requests.post(
        f"{BASE_URL}/tests/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "requirement": requirements,
            "test_types": ["e2e"],
            "max_tests": 3,
            "priority": "high"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        test_cases = result.get("test_cases", [])
        
        if len(test_cases) >= 2:
            print_success(f"Generated {len(test_cases)} test cases")
            for i, test in enumerate(test_cases[:2], 1):
                title = test.get('title', 'N/A')
                test_type = test.get('test_type', 'N/A')
                print_info(f"{i}. {title} [{test_type}]")
            results.add_pass()
        else:
            print_error(f"Expected at least 2 tests, got {len(test_cases)}")
            results.add_fail("Insufficient tests generated")
        
        # Generation worked, now get existing tests from DB for further testing
        print_test("Get existing tests from database")
        list_response = requests.get(
            f"{BASE_URL}/tests",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 5}
        )
        
        if list_response.status_code == 200:
            tests_result = list_response.json()
            if tests_result["items"]:
                test_ids = [t['id'] for t in tests_result["items"]]
                print_success(f"Found {len(test_ids)} existing test(s) in database")
                results.add_pass()
                return test_ids
            else:
                print_error("No tests found in database")
                results.add_fail("No tests in database")
                return []
        else:
            print_error(f"Failed to get tests: {list_response.status_code}")
            results.add_fail("Test retrieval failed")
            return []
    else:
        print_error(f"Test generation failed: {response.text[:200]}")
        results.add_fail("Test generation failed")
        return []


def test_test_management(token, test_ids):
    """Test CRUD operations on test cases."""
    print_header("TEST MANAGEMENT - CRUD OPERATIONS")
    
    if not test_ids:
        print_error("No test IDs provided, skipping CRUD tests")
        results.add_fail("No test IDs available")
        return
    
    test_id = test_ids[0]
    
    # Test 1: Get single test
    print_test(f"Get test case details (ID: {test_id})")
    response = requests.get(
        f"{BASE_URL}/tests/{test_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        test = response.json()
        print_success(f"Retrieved: {test['title']}")
        print_info(f"Type: {test['test_type']}, Priority: {test['priority']}, Status: {test['status']}")
        print_info(f"Steps: {len(test.get('steps', []))}")
        results.add_pass()
    else:
        print_error(f"Failed to get test: {response.status_code}")
        results.add_fail(f"Test retrieval failed for ID {test_id}")
        return
    
    # Test 2: Update test
    print_test(f"Update test case (ID: {test_id})")
    response = requests.put(
        f"{BASE_URL}/tests/{test_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "in_progress"
        }
    )
    
    if response.status_code == 200:
        updated_test = response.json()
        if updated_test['status'] == 'in_progress':
            print_success("Test updated successfully")
            print_info(f"New status: {updated_test['status']}")
            results.add_pass()
        else:
            print_error("Test update did not apply changes correctly")
            results.add_fail("Test update incomplete")
    else:
        print_error(f"Failed to update test: {response.status_code} - {response.text[:100]}")
        results.add_fail(f"Test update failed for ID {test_id}")
    
    # Test 3: List tests with filters
    print_test("List tests with filters (status=in_progress)")
    response = requests.get(
        f"{BASE_URL}/tests",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "in_progress", "limit": 10}
    )
    
    if response.status_code == 200:
        result = response.json()
        in_progress_tests = [t for t in result["items"] if t["status"] == "in_progress"]
        print_success(f"Found {len(in_progress_tests)} test(s) in progress")
        results.add_pass()
    else:
        print_error(f"Failed to list tests: {response.status_code}")
        results.add_fail("Test listing failed")


def test_execution_lifecycle(token, test_ids):
    """Test complete execution lifecycle."""
    print_header("TEST EXECUTION - COMPLETE LIFECYCLE")
    
    if not test_ids:
        print_error("No test IDs provided, skipping execution tests")
        results.add_fail("No test IDs available")
        return
    
    test_id = test_ids[0]
    
    # Test 1: Start execution
    print_test(f"Start test execution (Test ID: {test_id})")
    response = requests.post(
        f"{BASE_URL}/tests/{test_id}/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "browser": "chromium",
            "environment": "staging",
            "base_url": "https://staging.example.com",
            "triggered_by": "integration_test"
        }
    )
    
    if response.status_code == 201:
        execution = response.json()
        execution_id = execution['id']
        print_success(f"Execution started: ID {execution_id}")
        print_info(f"Status: {execution['status']}")
        results.add_pass()
    else:
        print_error(f"Failed to start execution: {response.text}")
        results.add_fail(f"Execution start failed for test {test_id}")
        return
    
    # Test 2: Get execution details
    print_test(f"Get execution details (ID: {execution_id})")
    response = requests.get(
        f"{BASE_URL}/executions/{execution_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        exec_detail = response.json()
        print_success("Retrieved execution details")
        print_info(f"Test Case: {exec_detail['test_case_id']}")
        print_info(f"Status: {exec_detail['status']}, Result: {exec_detail.get('result', 'N/A')}")
        print_info(f"Browser: {exec_detail['browser']}, Environment: {exec_detail['environment']}")
        print_info(f"Steps: {exec_detail['total_steps']} total")
        results.add_pass()
    else:
        print_error(f"Failed to get execution: {response.status_code}")
        results.add_fail(f"Execution retrieval failed for ID {execution_id}")
    
    # Test 3: Get execution history
    print_test(f"Get execution history for test {test_id}")
    response = requests.get(
        f"{BASE_URL}/tests/{test_id}/executions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        history = response.json()
        print_success(f"Retrieved {history['total']} execution(s)")
        if history['items']:
            latest = history['items'][0]
            print_info(f"Latest: Execution {latest['id']} - {latest['status']}")
        results.add_pass()
    else:
        print_error(f"Failed to get execution history: {response.status_code}")
        results.add_fail(f"Execution history failed for test {test_id}")
    
    # Test 4: List all executions with filters
    print_test("List all executions (filtered by environment)")
    response = requests.get(
        f"{BASE_URL}/executions",
        headers={"Authorization": f"Bearer {token}"},
        params={"environment": "staging", "limit": 10}
    )
    
    if response.status_code == 200:
        result = response.json()
        staging_execs = [e for e in result["items"] if e["environment"] == "staging"]
        print_success(f"Found {len(staging_execs)} staging execution(s)")
        results.add_pass()
    else:
        print_error(f"Failed to list executions: {response.status_code}")
        results.add_fail("Execution listing failed")


def test_execution_statistics(token):
    """Test execution statistics endpoint."""
    print_header("EXECUTION STATISTICS")
    
    print_test("Get comprehensive execution statistics")
    response = requests.get(
        f"{BASE_URL}/executions/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print_success("Retrieved execution statistics")
        print_info(f"Total Executions: {stats['total_executions']}")
        print_info(f"Pass Rate: {stats['pass_rate']}%")
        print_info(f"Last 24h: {stats['executions_last_24h']}")
        print_info(f"By Status: {', '.join([f'{k}={v}' for k, v in list(stats['by_status'].items())[:3]])}")
        results.add_pass()
    else:
        print_error(f"Failed to get statistics: {response.status_code}")
        results.add_fail("Statistics retrieval failed")


def test_kb_statistics(token):
    """Test KB statistics endpoint."""
    print_header("KB STATISTICS")
    
    print_test("Get KB statistics")
    response = requests.get(
        f"{BASE_URL}/kb/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print_success("Retrieved KB statistics")
        print_info(f"Total Documents: {stats['total_documents']}")
        print_info(f"Total Size: {stats['total_size_mb']:.2f} MB")
        print_info(f"By Category: {len(stats.get('by_category', {}))} categories")
        if 'by_type' in stats and stats['by_type']:
            print_info(f"By Type: {', '.join([f'{k}={v}' for k, v in list(stats['by_type'].items())[:3]])}")
        results.add_pass()
    else:
        print_error(f"Failed to get KB statistics: {response.status_code}")
        results.add_fail("KB statistics retrieval failed")


def test_test_statistics(token):
    """Test test case statistics endpoint."""
    print_header("TEST CASE STATISTICS")
    
    print_test("Get test case statistics")
    response = requests.get(
        f"{BASE_URL}/tests/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print_success("Retrieved test case statistics")
        
        # Handle different field names
        total = stats.get('total_tests', stats.get('total', 0))
        print_info(f"Total Tests: {total}")
        
        if 'by_type' in stats:
            print_info(f"By Type: {', '.join([f'{k}={v}' for k, v in stats['by_type'].items()])}")
        if 'by_status' in stats:
            print_info(f"By Status: {', '.join([f'{k}={v}' for k, v in list(stats['by_status'].items())[:3]])}")
        if 'by_priority' in stats:
            print_info(f"By Priority: {', '.join([f'{k}={v}' for k, v in stats['by_priority'].items()])}")
        
        results.add_pass()
    else:
        print_error(f"Failed to get test statistics: {response.status_code}")
        results.add_fail("Test statistics retrieval failed")


def main():
    """Run all integration tests."""
    print(f"\n{BLUE}{'=' * 70}")
    print("SPRINT 2 INTEGRATION TEST SUITE")
    print("Testing Complete Workflow: KB -> Generation -> Management -> Execution")
    print(f"{'=' * 70}{RESET}\n")
    
    # Login
    token = login()
    
    # KB Upload & Categorization
    kb_doc_id = test_kb_upload_and_categorization(token)
    
    # Test Generation with KB
    test_ids = test_generate_tests_with_kb(token, kb_doc_id)
    
    # Test Management (CRUD)
    test_test_management(token, test_ids)
    
    # Execution Lifecycle
    test_execution_lifecycle(token, test_ids)
    
    # Statistics
    test_execution_statistics(token)
    test_kb_statistics(token)
    test_test_statistics(token)
    
    # Summary
    return results.print_summary()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests cancelled by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

