"""
Manual Test Script for Loop Execution Enhancement 2
Creates a test case with loop blocks and executes it.
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin@example.com"  # Change to your username
PASSWORD = "admin123"  # Change to your password

def login():
    """Login and get authentication token."""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def create_test_with_loop(token):
    """Create a test case with loop blocks."""
    print("\n📝 Creating test case with loop blocks...")
    
    test_data = {
        "title": "Manual Test: Upload 3 HKID Documents (Loop)",
        "description": "Test loop execution with 3 file upload iterations",
        "test_type": "e2e",
        "priority": "high",
        "steps": [
            "Navigate to document upload page",
            "Click upload button",
            "Select file from dialog",
            "Click confirm button",
            "Verify all documents uploaded successfully"
        ],
        "expected_result": "All 3 documents uploaded successfully",
        "preconditions": "User is logged in and has access to upload page",
        "test_data": {
            "detailed_steps": [
                {
                    "action": "navigate",
                    "value": "http://localhost:3000/upload"
                },
                {
                    "action": "click",
                    "selector": "#upload-btn"
                },
                {
                    "action": "upload_file",
                    "selector": "input[type='file']",
                    "file_path": "/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/test_files/hkid_sample.pdf",
                    "instruction": "Upload HKID document {iteration}"
                },
                {
                    "action": "click",
                    "selector": "#confirm-btn"
                },
                {
                    "action": "verify",
                    "selector": ".success-message",
                    "expected": "Upload successful"
                }
            ],
            "loop_blocks": [
                {
                    "id": "file_upload_loop",
                    "start_step": 2,
                    "end_step": 4,
                    "iterations": 3,
                    "description": "Upload 3 HKID documents",
                    "variables": {
                        "file_path": "/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/test_files/hkid_sample.pdf"
                    }
                }
            ]
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/tests",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=test_data
    )
    
    if response.status_code in [200, 201]:
        test = response.json()
        test_id = test.get("id")
        print(f"✅ Test case created successfully!")
        print(f"   Test ID: {test_id}")
        print(f"   Title: {test['title']}")
        print(f"   Steps: {len(test['steps'])}")
        
        # Show loop block info
        if test.get("test_data") and test["test_data"].get("loop_blocks"):
            loop = test["test_data"]["loop_blocks"][0]
            print(f"\n🔁 Loop Block Details:")
            print(f"   ID: {loop['id']}")
            print(f"   Steps: {loop['start_step']}-{loop['end_step']}")
            print(f"   Iterations: {loop['iterations']}")
            print(f"   Description: {loop['description']}")
        
        return test_id
    else:
        print(f"❌ Failed to create test: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def execute_test(token, test_id):
    """Execute the test case."""
    print(f"\n▶️  Executing test case {test_id}...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/executions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "test_case_id": test_id
        }
    )
    
    if response.status_code in [200, 201]:
        execution = response.json()
        execution_id = execution.get("id")
        print(f"✅ Execution started!")
        print(f"   Execution ID: {execution_id}")
        print(f"   Status: {execution.get('status')}")
        
        return execution_id
    else:
        print(f"❌ Failed to execute test: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def check_execution_status(token, execution_id, max_attempts=30):
    """Poll execution status until complete."""
    print(f"\n⏳ Monitoring execution {execution_id}...")
    
    for attempt in range(max_attempts):
        response = requests.get(
            f"{BASE_URL}/api/v1/executions/{execution_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 200:
            execution = response.json()
            status = execution.get("status")
            
            if status in ["completed", "failed", "error"]:
                print(f"\n✅ Execution finished!")
                print(f"   Status: {status}")
                print(f"   Result: {execution.get('result')}")
                print(f"   Total Steps: {execution.get('total_steps')}")
                print(f"   Passed Steps: {execution.get('passed_steps')}")
                print(f"   Failed Steps: {execution.get('failed_steps')}")
                
                # Show execution steps
                if execution.get("steps"):
                    print(f"\n📋 Execution Steps:")
                    for step in execution["steps"][:10]:  # Show first 10
                        iter_info = "(iter)" if "iter" in step.get("step_description", "") else ""
                        print(f"   Step {step['step_number']}: {step['step_description'][:60]}... {iter_info} - {step['result']}")
                    
                    if len(execution["steps"]) > 10:
                        print(f"   ... and {len(execution['steps']) - 10} more steps")
                
                return execution
            else:
                print(f"   [{attempt+1}/{max_attempts}] Status: {status} - waiting...")
                time.sleep(2)
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return None
    
    print("⚠️ Timeout waiting for execution to complete")
    return None

def main():
    """Main test flow."""
    print("=" * 60)
    print("LOOP EXECUTION MANUAL TEST")
    print("Sprint 5.5 Enhancement 2: Step Group Loop Support")
    print("=" * 60)
    
    # Step 1: Login
    token = login()
    if not token:
        return
    
    # Step 2: Create test with loop
    test_id = create_test_with_loop(token)
    if not test_id:
        return
    
    # Step 3: Execute test
    execution_id = execute_test(token, test_id)
    if not execution_id:
        return
    
    # Step 4: Monitor execution
    execution = check_execution_status(token, execution_id)
    
    # Step 5: Show where to find results
    if execution:
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        print(f"\n✅ Loop execution test completed!")
        print(f"\n📁 Check these locations for detailed results:")
        print(f"   1. Backend logs: Look for lines containing '[LOOP]'")
        print(f"   2. Screenshots: /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/screenshots/")
        print(f"      - Look for: exec_{execution_id}_step_*_iter_*_pass.png")
        print(f"   3. Execution details in database: execution_id = {execution_id}")
        print(f"   4. Frontend: http://localhost:3000/tests/{test_id}")
        
        print(f"\n🔍 What to verify:")
        print(f"   ✓ Backend logs show '[LOOP] Iteration 1/3', '[LOOP] Iteration 2/3', etc.")
        print(f"   ✓ Step descriptions include '(iter 1/3)', '(iter 2/3)', etc.")
        print(f"   ✓ Screenshot files have iteration numbers in filename")
        print(f"   ✓ Total steps executed = 11 (1 + 3*3 + 1)")
        print(f"   ✓ All steps should pass if using mock/simple selectors")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
