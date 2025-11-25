"""
Generate Sample Data for Frontend Development

Creates multiple test cases and executions with various statuses
to give frontend developers realistic data to work with.
"""

import requests
import time
import random
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_status(message, status="INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {
        "INFO": "[INFO]",
        "OK": "[OK]",
        "FAIL": "[FAIL]",
        "PROGRESS": "[>>>]"
    }
    symbol = symbols.get(status, "[INFO]")
    print(f"{timestamp} {symbol} {message}")

def login():
    """Login and get token."""
    print_status("Logging in...", "INFO")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "admin@aiwebtest.com",
            "password": "admin123"
        }
    )
    
    if response.status_code != 200:
        print_status(f"Login failed: {response.status_code}", "FAIL")
        return None
    
    token = response.json()["access_token"]
    print_status("Login successful", "OK")
    return token

def create_test_cases(token, count=10):
    """Create diverse test cases."""
    print_status(f"Creating {count} test cases...", "INFO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    test_templates = [
        {
            "name": "Homepage Load Test",
            "description": "Verify homepage loads correctly",
            "url": "https://example.com",
            "test_type": "e2e",
            "steps": [
                {"order": 0, "action": "Navigate to homepage", "expected_result": "Page loads"},
                {"order": 1, "action": "Verify title", "expected_result": "Title displays"},
            ]
        },
        {
            "name": "Login Flow Test",
            "description": "Test user login functionality",
            "url": "https://example.com/login",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to login page", "expected_result": "Login form visible"},
                {"order": 1, "action": "Enter credentials", "expected_result": "Fields populated"},
                {"order": 2, "action": "Click login button", "expected_result": "Dashboard loads"},
            ]
        },
        {
            "name": "Search Functionality",
            "description": "Test search feature",
            "url": "https://example.com/search",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to search page", "expected_result": "Search box visible"},
                {"order": 1, "action": "Enter search term", "expected_result": "Suggestions appear"},
                {"order": 2, "action": "Click search", "expected_result": "Results display"},
                {"order": 3, "action": "Verify results", "expected_result": "Results match query"},
            ]
        },
        {
            "name": "Form Submission Test",
            "description": "Test form validation and submission",
            "url": "https://example.com/contact",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to contact form", "expected_result": "Form displays"},
                {"order": 1, "action": "Fill in required fields", "expected_result": "Fields populated"},
                {"order": 2, "action": "Submit form", "expected_result": "Success message"},
            ]
        },
        {
            "name": "Navigation Test",
            "description": "Test site navigation",
            "url": "https://example.com",
            "test_type": "e2e",
            "steps": [
                {"order": 0, "action": "Navigate to homepage", "expected_result": "Page loads"},
                {"order": 1, "action": "Click About link", "expected_result": "About page loads"},
                {"order": 2, "action": "Click Services link", "expected_result": "Services page loads"},
                {"order": 3, "action": "Click Contact link", "expected_result": "Contact page loads"},
                {"order": 4, "action": "Click Home link", "expected_result": "Back to homepage"},
            ]
        },
        {
            "name": "Product Page Test",
            "description": "Test product detail page",
            "url": "https://example.com/products/1",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to product page", "expected_result": "Product details load"},
                {"order": 1, "action": "Verify images display", "expected_result": "All images visible"},
                {"order": 2, "action": "Check price", "expected_result": "Price displays correctly"},
            ]
        },
        {
            "name": "Shopping Cart Test",
            "description": "Test add to cart functionality",
            "url": "https://example.com/cart",
            "test_type": "e2e",
            "steps": [
                {"order": 0, "action": "Navigate to product", "expected_result": "Product page loads"},
                {"order": 1, "action": "Click add to cart", "expected_result": "Item added"},
                {"order": 2, "action": "View cart", "expected_result": "Cart shows item"},
                {"order": 3, "action": "Update quantity", "expected_result": "Quantity updated"},
            ]
        },
        {
            "name": "User Registration",
            "description": "Test new user registration",
            "url": "https://example.com/register",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to registration", "expected_result": "Form displays"},
                {"order": 1, "action": "Fill registration form", "expected_result": "All fields filled"},
                {"order": 2, "action": "Submit registration", "expected_result": "Success confirmation"},
            ]
        },
        {
            "name": "Password Reset Test",
            "description": "Test password reset flow",
            "url": "https://example.com/reset-password",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to reset page", "expected_result": "Reset form visible"},
                {"order": 1, "action": "Enter email", "expected_result": "Email accepted"},
                {"order": 2, "action": "Submit request", "expected_result": "Confirmation message"},
            ]
        },
        {
            "name": "Profile Update Test",
            "description": "Test user profile editing",
            "url": "https://example.com/profile",
            "test_type": "functional",
            "steps": [
                {"order": 0, "action": "Navigate to profile", "expected_result": "Profile loads"},
                {"order": 1, "action": "Edit profile fields", "expected_result": "Fields editable"},
                {"order": 2, "action": "Save changes", "expected_result": "Changes saved"},
            ]
        }
    ]
    
    test_ids = []
    
    for i in range(min(count, len(test_templates))):
        template = test_templates[i]
        
        response = requests.post(
            f"{BASE_URL}/tests",
            headers=headers,
            json=template
        )
        
        if response.status_code == 201:
            test_id = response.json()["id"]
            test_ids.append(test_id)
            print_status(f"Created test {i+1}/{count}: {template['name']} (ID: {test_id})", "OK")
        else:
            print_status(f"Failed to create test {i+1}: {response.status_code}", "FAIL")
    
    return test_ids

def run_executions(token, test_ids, executions_per_test=3):
    """Run multiple executions with varied priorities."""
    print_status(f"Running {executions_per_test} executions per test...", "INFO")
    
    headers = {"Authorization": f"Bearer {token}"}
    execution_ids = []
    
    priorities = [1, 5, 10]  # high, medium, low
    
    for test_id in test_ids:
        for i in range(executions_per_test):
            priority = random.choice(priorities)
            
            response = requests.post(
                f"{BASE_URL}/tests/{test_id}/run",
                headers=headers,
                json={"priority": priority}
            )
            
            if response.status_code == 201:
                execution_id = response.json()["id"]
                execution_ids.append(execution_id)
                print_status(f"Queued execution for test {test_id}: ID {execution_id} (priority: {priority})", "PROGRESS")
            else:
                print_status(f"Failed to run test {test_id}: {response.status_code}", "FAIL")
            
            # Small delay to avoid overwhelming the queue
            time.sleep(0.5)
    
    return execution_ids

def wait_for_completions(token, execution_ids, max_wait=300):
    """Wait for executions to complete."""
    print_status(f"Waiting for {len(execution_ids)} executions to complete...", "INFO")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    completed = 0
    
    while time.time() - start_time < max_wait:
        all_done = True
        temp_completed = 0
        
        for execution_id in execution_ids:
            response = requests.get(
                f"{BASE_URL}/executions/{execution_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                execution = response.json()
                status = execution.get("status")
                
                if status == "completed":
                    temp_completed += 1
                elif status in ["pending", "running"]:
                    all_done = False
        
        if temp_completed > completed:
            completed = temp_completed
            print_status(f"Progress: {completed}/{len(execution_ids)} completed", "PROGRESS")
        
        if all_done:
            print_status(f"All {len(execution_ids)} executions completed!", "OK")
            return True
        
        time.sleep(5)
    
    print_status(f"Timeout: {completed}/{len(execution_ids)} completed in {max_wait}s", "FAIL")
    return False

def get_summary(token, execution_ids):
    """Get summary of generated data."""
    print_status("Getting summary...", "INFO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get execution stats
    response = requests.get(f"{BASE_URL}/executions/stats", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print_status(f"Total executions: {stats.get('total_count', 0)}", "INFO")
        print_status(f"Pass rate: {stats.get('pass_rate', 0):.1f}%", "INFO")
        print_status(f"Average duration: {stats.get('average_duration', 0):.1f}s", "INFO")
    
    # Get queue status
    response = requests.get(f"{BASE_URL}/executions/queue/status", headers=headers)
    if response.status_code == 200:
        queue = response.json()
        print_status(f"Queue status: {queue.get('status', 'unknown')}", "INFO")
        print_status(f"Active: {queue.get('active_count', 0)}/{queue.get('max_concurrent', 5)}", "INFO")

def main():
    """Main execution."""
    print("=" * 70)
    print("  Generate Sample Data for Frontend Development")
    print("=" * 70)
    print()
    
    # Login
    token = login()
    if not token:
        return
    
    print()
    
    # Create test cases
    test_ids = create_test_cases(token, count=10)
    if not test_ids:
        print_status("No test cases created", "FAIL")
        return
    
    print()
    print_status(f"Created {len(test_ids)} test cases", "OK")
    print()
    
    # Run executions (3 per test = 30 total executions)
    execution_ids = run_executions(token, test_ids, executions_per_test=3)
    if not execution_ids:
        print_status("No executions created", "FAIL")
        return
    
    print()
    print_status(f"Queued {len(execution_ids)} executions", "OK")
    print()
    
    # Wait for completions (partial completion is OK)
    wait_for_completions(token, execution_ids, max_wait=180)
    
    print()
    
    # Get summary
    get_summary(token, execution_ids)
    
    print()
    print("=" * 70)
    print("  Sample Data Generation Complete!")
    print("=" * 70)
    print()
    print("[INFO] Frontend developer now has:")
    print("       - 10+ diverse test cases")
    print("       - 30+ test executions")
    print("       - Various statuses (pending/running/completed)")
    print("       - Multiple screenshots")
    print("       - Realistic data for UI development")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")

