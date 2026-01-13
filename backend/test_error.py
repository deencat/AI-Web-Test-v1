"""
Test Execution Feedback Collection System - API Integration
Creates test cases with intentional failures and executes them via API
so they appear in the frontend execution history with feedback data.
"""
import requests
import time
from typing import Dict, Any, List
from datetime import datetime
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None


def login() -> str:
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def get_headers() -> Dict[str, str]:
    """Get authorization headers."""
    global TOKEN
    if not TOKEN:
        TOKEN = login()
    return {"Authorization": f"Bearer {TOKEN}"}


class FeedbackTestScenarios:
    """Test scenarios for execution feedback collection via API"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = get_headers()
        
    def create_test_case(self, title: str, description: str, steps: List[Dict], url: str = "https://example.com") -> int:
        """Create a test case via API."""
        # Convert steps to string format (API expects List[str])
        step_strings = [
            f"Step {step['step_number']}: {step['action']} - {step['description']}"
            for step in steps
        ]
        
        test_case_data = {
            "title": title,
            "description": description,
            "test_type": "e2e",  # Required field
            "priority": "medium",
            "steps": step_strings,  # Required field - list of strings
            "expected_result": "Test should execute and capture feedback on failures",  # Required field
            "test_data": {
                "url": url,
                "detailed_steps": steps  # Store detailed steps here
            },
            "tags": ["feedback-testing", "error-scenarios"],
            "status": "pending"
        }
        
        response = requests.post(
            f"{self.base_url}/tests",
            headers=self.headers,
            json=test_case_data
        )
        
        if response.status_code == 201:
            test_id = response.json()["id"]
            print(f"✅ Created test case #{test_id}: {title}")
            return test_id
        else:
            raise Exception(f"Failed to create test: {response.status_code} - {response.text}")
    
    def execute_test(self, test_id: int, headless: bool = True, base_url: str = "https://example.com") -> Dict[str, Any]:
        """Execute a test case and wait for completion."""
        response = requests.post(
            f"{self.base_url}/executions/tests/{test_id}/run",  # Use /run endpoint
            headers=self.headers,
            json={
                "browser": "chromium",
                "environment": "test",
                "base_url": base_url,
                "triggered_by": "error_feedback_test"
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to start execution: {response.status_code} - {response.text}")
        
        execution_id = response.json()["id"]
        print(f"🚀 Started execution #{execution_id}")
        
        # Wait for execution to complete
        for i in range(120):  # 2 minutes max
            response = requests.get(
                f"{self.base_url}/executions/{execution_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"⚠️ Failed to get execution status: {response.status_code}")
                break
            
            execution = response.json()
            status = execution.get("status", "unknown")
            
            if status in ["completed", "failed"]:
                print(f"✅ Execution completed: {status}")
                print(f"   Total steps: {execution.get('total_steps', 0)}")
                print(f"   Passed steps: {execution.get('passed_steps', 0)}")
                print(f"   Failed steps: {execution.get('failed_steps', 0)}")
                return execution
            
            if i % 10 == 0:
                print(f"   Waiting... ({i}s) - Status: {status}")
            
            time.sleep(1)
        
        raise TimeoutError(f"Execution #{execution_id} did not complete within 2 minutes")
    
    def get_execution_feedback(self, execution_id: int) -> List[Dict[str, Any]]:
        """Get feedback entries for an execution."""
        response = requests.get(
            f"{self.base_url}/execution-feedback/",
            headers=self.headers,
            params={"execution_id": execution_id}
        )
        
        if response.status_code == 200:
            feedback_list = response.json()
            print(f"📝 Found {len(feedback_list)} feedback entries")
            return feedback_list
        else:
            print(f"⚠️ Failed to get feedback: {response.status_code}")
            return []
    
    def test_selector_not_found_error(self) -> Dict[str, Any]:
        """Test: Selector not found failure"""
        print("\n" + "="*60)
        print("TEST 1: Selector Not Found Error")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://example.com",
                "description": "Navigate to example.com",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action": "click",
                "selector": "#nonexistent-button-12345",
                "value": "",
                "description": "Click non-existent button",
                "expected_result": "Button clicked"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Selector Not Found",
            description="Test case with invalid selector to trigger selector_not_found error",
            steps=steps
        )
        
        execution = self.execute_test(test_id, base_url="https://example.com")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Selector Not Found",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }
    
    def test_timeout_error(self) -> Dict[str, Any]:
        """Test: Timeout/slow page load"""
        print("\n" + "="*60)
        print("TEST 2: Timeout Error")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://httpstat.us/200?sleep=30000",  # 30s sleep
                "description": "Navigate to slow endpoint",
                "expected_result": "Page loads within timeout"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Timeout Error",
            description="Test case with slow page to trigger timeout error",
            steps=steps,
            url="https://httpstat.us/200?sleep=30000"
        )
        
        execution = self.execute_test(test_id, base_url="https://httpstat.us/200?sleep=30000")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Timeout Error",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }
    
    def test_multiple_selector_failures(self) -> Dict[str, Any]:
        """Test: Multiple selector failures in one test"""
        print("\n" + "="*60)
        print("TEST 3: Multiple Selector Failures")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://example.com",
                "description": "Navigate to example.com",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action": "click",
                "selector": "#fake-button-1",
                "value": "",
                "description": "Click first non-existent button",
                "expected_result": "Button clicked"
            },
            {
                "step_number": 3,
                "action": "fill",
                "selector": "input[name='fake-input']",
                "value": "Test data",
                "description": "Fill non-existent input",
                "expected_result": "Input filled"
            },
            {
                "step_number": 4,
                "action": "click",
                "selector": ".fake-submit-button",
                "value": "",
                "description": "Click non-existent submit",
                "expected_result": "Submit clicked"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Multiple Selector Failures",
            description="Test case with multiple invalid selectors",
            steps=steps
        )
        
        execution = self.execute_test(test_id, base_url="https://example.com")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Multiple Selector Failures",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }
    
    def test_navigation_error(self) -> Dict[str, Any]:
        """Test: Navigation failure (404 error)"""
        print("\n" + "="*60)
        print("TEST 4: Navigation Error (404)")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://example.com/page-that-does-not-exist-404",
                "description": "Navigate to non-existent page",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action": "click",
                "selector": "a",
                "value": "",
                "description": "Click any link on 404 page",
                "expected_result": "Link clicked"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Navigation 404 Error",
            description="Test case navigating to non-existent page",
            steps=steps,
            url="https://example.com/page-that-does-not-exist-404"
        )
        
        execution = self.execute_test(test_id, base_url="https://example.com")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Navigation 404 Error",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }
    
    def test_complex_xpath_failure(self) -> Dict[str, Any]:
        """Test: Complex XPath selector failure"""
        print("\n" + "="*60)
        print("TEST 5: Complex XPath Failure")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://example.com",
                "description": "Navigate to example.com",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action": "click",
                "selector": "//div[@class='container']//button[@id='submit'][contains(text(), 'Submit')]/following-sibling::span[@class='icon']",
                "value": "",
                "description": "Click using complex XPath that doesn't exist",
                "expected_result": "Element clicked"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Complex XPath Failure",
            description="Test case with complex XPath selector that fails",
            steps=steps
        )
        
        execution = self.execute_test(test_id, base_url="https://example.com")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Complex XPath Failure",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }
    
    def test_wrong_action_on_element(self) -> Dict[str, Any]:
        """Test: Wrong action on valid element"""
        print("\n" + "="*60)
        print("TEST 6: Wrong Action on Element")
        print("="*60)
        
        steps = [
            {
                "step_number": 1,
                "action": "navigate",
                "selector": "",
                "value": "https://example.com",
                "description": "Navigate to example.com",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action": "fill",
                "selector": "h1",  # h1 exists but is not an input
                "value": "Try to fill text in heading",
                "description": "Try to fill text in h1 element",
                "expected_result": "Text filled"
            }
        ]
        
        test_id = self.create_test_case(
            title="[ERROR TEST] Wrong Action on Element",
            description="Test case attempting wrong action (fill) on non-input element",
            steps=steps
        )
        
        execution = self.execute_test(test_id, base_url="https://example.com")
        feedback = self.get_execution_feedback(execution["id"])
        
        return {
            "test_name": "Wrong Action on Element",
            "test_id": test_id,
            "execution_id": execution["id"],
            "status": execution["status"],
            "feedback_count": len(feedback),
            "feedback": feedback
        }


def run_all_feedback_tests():
    """Run all feedback collection test scenarios"""
    print("\n" + "="*80)
    print("EXECUTION FEEDBACK COLLECTION TEST SUITE")
    print("Testing error scenarios for Sprint 4 Developer B feature")
    print("="*80)
    
    tester = FeedbackTestScenarios()
    results = []
    
    # Run each test scenario
    test_scenarios = [
        ("Selector Not Found", tester.test_selector_not_found_error),
        ("Timeout Error", tester.test_timeout_error),
        ("Multiple Selector Failures", tester.test_multiple_selector_failures),
        ("Navigation 404 Error", tester.test_navigation_error),
        ("Complex XPath Failure", tester.test_complex_xpath_failure),
        ("Wrong Action on Element", tester.test_wrong_action_on_element)
    ]
    
    for test_name, test_func in test_scenarios:
        try:
            print(f"\n\n{'='*80}")
            print(f"Running: {test_name}")
            print('='*80)
            
            result = test_func()
            results.append({
                "test_name": test_name,
                "status": "pass",
                "test_id": result.get("test_id"),
                "execution_id": result.get("execution_id"),
                "execution_status": result.get("status"),
                "feedback_count": result.get("feedback_count"),
                "details": result
            })
            
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' failed unexpectedly: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test_name": test_name,
                "status": "error",
                "error": str(e)
            })
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for result in results:
        status_icon = "✅" if result["status"] == "pass" else "❌"
        print(f"{status_icon} {result['test_name']}: {result['status'].upper()}")
        
        if result["status"] == "pass":
            print(f"   - Test ID: #{result.get('test_id', 'N/A')}")
            print(f"   - Execution ID: #{result.get('execution_id', 'N/A')}")
            print(f"   - Execution Status: {result.get('execution_status', 'N/A')}")
            print(f"   - Feedback Entries: {result.get('feedback_count', 0)}")
    
    print("\n" + "="*80)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(1 for r in results if r['status'] == 'pass')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'error')}")
    print("="*80)
    
    # Save results to JSON
    results_file = f"feedback_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[INFO] Results saved to: {results_file}")
    print(f"\n💡 Check the frontend execution history at: http://localhost:3000/executions")
    print(f"   All {len(results)} test executions should appear with feedback data!")
    
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AI Web Test v1.0 - Feedback Collection Test Suite")
    print("Sprint 4 - Developer B Feature Testing")
    print("="*80)
    print("\n📋 This will create test cases with intentional errors and execute them")
    print("   so they appear in the frontend execution history with feedback.")
    print("\n🔧 Prerequisites:")
    print("   1. Backend server running at http://localhost:8000")
    print("   2. Frontend running at http://localhost:3000")
    print("   3. Admin credentials: admin / admin123")
    print("\n" + "="*80)
    
    # Check if backend is available
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print("⚠️ Backend server may not be healthy")
    except Exception as e:
        print(f"❌ Cannot connect to backend server: {e}")
        print("   Please start the backend server first!")
        exit(1)
    
    results = run_all_feedback_tests()
    
    # Exit with appropriate code
    all_passed = all(r["status"] == "pass" for r in results)
    exit(0 if all_passed else 1)