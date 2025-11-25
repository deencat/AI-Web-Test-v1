"""
End-to-End Integration Test for Sprint 3

Tests the complete user flow from test creation to execution results viewing.
This simulates what a frontend user would do.
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

class TestRunner:
    """Integration test runner."""
    
    def __init__(self):
        self.token = None
        self.test_id = None
        self.execution_id = None
        self.passed = 0
        self.failed = 0
    
    def print_status(self, message, status="INFO"):
        """Print formatted message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "[INFO]",
            "OK": "[✓]",
            "FAIL": "[✗]",
            "TEST": "[TEST]"
        }
        symbol = symbols.get(status, "[INFO]")
        print(f"{timestamp} {symbol} {message}")
    
    def assert_status(self, response, expected_status, test_name):
        """Assert response status code."""
        if response.status_code == expected_status:
            self.passed += 1
            self.print_status(f"{test_name}: PASS", "OK")
            return True
        else:
            self.failed += 1
            self.print_status(f"{test_name}: FAIL (expected {expected_status}, got {response.status_code})", "FAIL")
            if response.text:
                self.print_status(f"  Response: {response.text[:200]}", "INFO")
            return False
    
    def test_01_login(self):
        """Test 1: User logs in."""
        self.print_status("Test 1: Login", "TEST")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "admin@aiwebtest.com",
                "password": "admin123"
            }
        )
        
        if self.assert_status(response, 200, "Login"):
            data = response.json()
            self.token = data.get("access_token")
            self.print_status(f"  Token obtained: {self.token[:20]}...", "INFO")
            return True
        return False
    
    def test_02_health_check(self):
        """Test 2: Check API health."""
        self.print_status("Test 2: Health Check", "TEST")
        
        response = requests.get(f"{BASE_URL}/health")
        return self.assert_status(response, 200, "Health Check")
    
    def test_03_list_tests(self):
        """Test 3: List existing tests."""
        self.print_status("Test 3: List Tests", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/tests", headers=headers)
        
        if self.assert_status(response, 200, "List Tests"):
            data = response.json()
            test_count = len(data)
            self.print_status(f"  Found {test_count} test(s)", "INFO")
            
            if test_count > 0:
                self.test_id = data[0]["id"]
                self.print_status(f"  Using test ID: {self.test_id}", "INFO")
            return True
        return False
    
    def test_04_create_test(self):
        """Test 4: Create a new test case."""
        if self.test_id:
            self.print_status("Test 4: Create Test (SKIPPED - using existing)", "INFO")
            self.passed += 1
            return True
        
        self.print_status("Test 4: Create Test", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        test_data = {
            "name": "Integration Test - E2E Flow",
            "description": "Test created by integration test suite",
            "test_type": "e2e",
            "url": "https://example.com",
            "steps": [
                {
                    "order": 0,
                    "action": "Navigate to homepage",
                    "expected_result": "Page loads successfully"
                },
                {
                    "order": 1,
                    "action": "Verify page title",
                    "expected_result": "Title is 'Example Domain'"
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/tests",
            headers=headers,
            json=test_data
        )
        
        if self.assert_status(response, 201, "Create Test"):
            data = response.json()
            self.test_id = data.get("id")
            self.print_status(f"  Created test ID: {self.test_id}", "INFO")
            return True
        return False
    
    def test_05_get_test_details(self):
        """Test 5: Get test case details."""
        self.print_status("Test 5: Get Test Details", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/tests/{self.test_id}",
            headers=headers
        )
        
        if self.assert_status(response, 200, "Get Test Details"):
            data = response.json()
            self.print_status(f"  Test name: {data.get('name')}", "INFO")
            self.print_status(f"  Steps: {len(data.get('steps', []))}", "INFO")
            return True
        return False
    
    def test_06_check_queue_status(self):
        """Test 6: Check queue status before execution."""
        self.print_status("Test 6: Check Queue Status", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/executions/queue/status",
            headers=headers
        )
        
        if self.assert_status(response, 200, "Queue Status"):
            data = response.json()
            self.print_status(f"  Queue status: {data.get('status')}", "INFO")
            self.print_status(f"  Active: {data.get('active_count')}/{data.get('max_concurrent')}", "INFO")
            self.print_status(f"  Pending: {data.get('pending_count')}", "INFO")
            return True
        return False
    
    def test_07_execute_test(self):
        """Test 7: Execute the test."""
        self.print_status("Test 7: Execute Test", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{BASE_URL}/tests/{self.test_id}/run",
            headers=headers,
            json={"priority": 5}
        )
        
        if self.assert_status(response, 201, "Execute Test"):
            data = response.json()
            self.execution_id = data.get("id")
            self.print_status(f"  Execution ID: {self.execution_id}", "INFO")
            self.print_status(f"  Status: {data.get('status')}", "INFO")
            self.print_status(f"  Priority: {data.get('priority')}", "INFO")
            return True
        return False
    
    def test_08_poll_execution(self):
        """Test 8: Poll execution status until complete."""
        self.print_status("Test 8: Poll Execution Progress", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        max_polls = 30
        poll_interval = 2
        
        for poll in range(max_polls):
            response = requests.get(
                f"{BASE_URL}/executions/{self.execution_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                self.print_status(f"  Poll {poll+1}: Failed to get execution", "FAIL")
                continue
            
            data = response.json()
            status = data.get("status")
            steps_passed = data.get("steps_passed", 0)
            steps_total = data.get("steps_total", 0)
            
            self.print_status(f"  Poll {poll+1}: Status={status}, Steps={steps_passed}/{steps_total}", "INFO")
            
            if status == "completed":
                result = data.get("result")
                duration = data.get("duration")
                self.print_status(f"  Execution completed: {result} ({duration}s)", "INFO")
                
                if result in ["passed", "failed"]:
                    self.passed += 1
                    self.print_status("Poll Execution: PASS", "OK")
                    return True
                break
            
            elif status == "failed":
                error = data.get("error_message")
                self.print_status(f"  Execution failed: {error}", "FAIL")
                self.failed += 1
                return False
            
            time.sleep(poll_interval)
        
        self.print_status("  Execution did not complete in time", "FAIL")
        self.failed += 1
        return False
    
    def test_09_get_execution_details(self):
        """Test 9: Get detailed execution results."""
        self.print_status("Test 9: Get Execution Details", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/executions/{self.execution_id}",
            headers=headers
        )
        
        if self.assert_status(response, 200, "Get Execution Details"):
            data = response.json()
            self.print_status(f"  Result: {data.get('result')}", "INFO")
            self.print_status(f"  Duration: {data.get('duration')}s", "INFO")
            self.print_status(f"  Steps passed: {data.get('steps_passed')}/{data.get('steps_total')}", "INFO")
            
            steps = data.get("steps", [])
            for step in steps:
                step_status = step.get("status")
                step_action = step.get("action")
                screenshot = step.get("screenshot_path")
                self.print_status(f"    Step {step.get('step_order')}: {step_status} - {step_action}", "INFO")
                if screenshot:
                    self.print_status(f"      Screenshot: {screenshot}", "INFO")
            
            return True
        return False
    
    def test_10_list_executions(self):
        """Test 10: List all executions."""
        self.print_status("Test 10: List Executions", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/executions?skip=0&limit=10",
            headers=headers
        )
        
        if self.assert_status(response, 200, "List Executions"):
            data = response.json()
            items = data.get("items", [])
            total = data.get("total", 0)
            self.print_status(f"  Found {total} total execution(s)", "INFO")
            self.print_status(f"  Showing {len(items)} execution(s)", "INFO")
            return True
        return False
    
    def test_11_execution_statistics(self):
        """Test 11: Get execution statistics."""
        self.print_status("Test 11: Get Execution Statistics", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/executions/stats",
            headers=headers
        )
        
        if self.assert_status(response, 200, "Get Statistics"):
            data = response.json()
            self.print_status(f"  Total executions: {data.get('total_count')}", "INFO")
            self.print_status(f"  Completed: {data.get('completed_count')}", "INFO")
            self.print_status(f"  Pass rate: {data.get('pass_rate')}%", "INFO")
            self.print_status(f"  Avg duration: {data.get('average_duration')}s", "INFO")
            return True
        return False
    
    def test_12_filter_executions(self):
        """Test 12: Filter executions by status and result."""
        self.print_status("Test 12: Filter Executions", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test status filter
        response = requests.get(
            f"{BASE_URL}/executions?status=completed",
            headers=headers
        )
        
        if not self.assert_status(response, 200, "Filter by Status"):
            return False
        
        completed_count = response.json().get("total", 0)
        self.print_status(f"  Completed executions: {completed_count}", "INFO")
        
        # Test result filter
        response = requests.get(
            f"{BASE_URL}/executions?result=passed",
            headers=headers
        )
        
        if not self.assert_status(response, 200, "Filter by Result"):
            return False
        
        passed_count = response.json().get("total", 0)
        self.print_status(f"  Passed executions: {passed_count}", "INFO")
        
        self.passed -= 1  # Adjust for combined test
        return True
    
    def test_13_queue_operations(self):
        """Test 13: Queue management operations."""
        self.print_status("Test 13: Queue Operations", "TEST")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get queue statistics
        response = requests.get(
            f"{BASE_URL}/executions/queue/statistics",
            headers=headers
        )
        
        if not self.assert_status(response, 200, "Queue Statistics"):
            return False
        
        stats = response.json()
        self.print_status(f"  Total processed: {stats.get('total_processed')}", "INFO")
        self.print_status(f"  Success rate: {stats.get('success_rate')}%", "INFO")
        
        # Get active executions
        response = requests.get(
            f"{BASE_URL}/executions/queue/active",
            headers=headers
        )
        
        if not self.assert_status(response, 200, "Active Executions"):
            return False
        
        active = response.json()
        self.print_status(f"  Active executions: {active.get('count')}", "INFO")
        
        self.passed -= 1  # Adjust for combined test
        return True
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("=" * 70)
        print("  End-to-End Integration Test - Sprint 3")
        print("=" * 70)
        print()
        
        start_time = time.time()
        
        tests = [
            self.test_01_login,
            self.test_02_health_check,
            self.test_03_list_tests,
            self.test_04_create_test,
            self.test_05_get_test_details,
            self.test_06_check_queue_status,
            self.test_07_execute_test,
            self.test_08_poll_execution,
            self.test_09_get_execution_details,
            self.test_10_list_executions,
            self.test_11_execution_statistics,
            self.test_12_filter_executions,
            self.test_13_queue_operations,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.failed += 1
                self.print_status(f"{test.__name__}: EXCEPTION - {str(e)}", "FAIL")
            print()
        
        duration = time.time() - start_time
        
        print("=" * 70)
        print("  Test Results")
        print("=" * 70)
        print(f"  Total tests: {self.passed + self.failed}")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Duration: {duration:.1f}s")
        print()
        
        if self.failed == 0:
            print("  [✓] ALL TESTS PASSED!")
            print("  System is working correctly end-to-end.")
        else:
            print(f"  [✗] {self.failed} TEST(S) FAILED")
            print("  Please check errors above.")
        
        print("=" * 70)
        
        return self.failed == 0

def main():
    """Main entry point."""
    try:
        runner = TestRunner()
        success = runner.run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[FAIL] Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()

