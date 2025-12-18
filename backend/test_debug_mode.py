"""
Test script for Local Persistent Browser Debug Mode backend implementation.
Tests both auto and manual modes with the debug session API.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials (using admin user)
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get JWT token."""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def get_test_execution(token):
    """Get the first available test execution."""
    print("\n📋 Getting test execution...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/executions",
        headers=headers,
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data["total"] > 0:
            execution = data["executions"][0]
            print(f"✅ Found execution ID: {execution['id']} with {execution['total_steps']} steps")
            return execution["id"], execution["total_steps"]
    
    print("❌ No test executions found. Please run a test first.")
    return None, None

def test_auto_mode(token, execution_id, total_steps):
    """Test debug session in AUTO mode."""
    print("\n" + "="*60)
    print("🤖 Testing AUTO MODE")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Choose a step to debug (middle of the test)
    target_step = max(2, total_steps // 2)
    
    # Start debug session
    print(f"\n1️⃣ Starting debug session for step {target_step}...")
    response = requests.post(
        f"{BASE_URL}/debug/start",
        headers=headers,
        json={
            "execution_id": execution_id,
            "target_step_number": target_step,
            "mode": "auto"
        }
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to start debug session: {response.status_code}")
        print(response.text)
        return
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Debug session started: {session_id}")
    print(f"   Mode: {session_data['mode']}")
    print(f"   Status: {session_data['status']}")
    print(f"   Target step: {session_data['target_step_number']}")
    print(f"   Prerequisites: {session_data['prerequisite_steps_count']}")
    print(f"   Message: {session_data['message']}")
    
    # Wait for auto setup to complete
    print("\n2️⃣ Waiting for auto-setup to complete...")
    max_wait = 60  # 60 seconds timeout
    waited = 0
    
    while waited < max_wait:
        response = requests.get(
            f"{BASE_URL}/debug/{session_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Status: {status_data['status']} | Setup: {status_data['setup_completed']} | Tokens: {status_data['tokens_used']}")
            
            if status_data["status"] == "ready":
                print(f"✅ Auto-setup complete! Tokens used: {status_data['tokens_used']}")
                break
            elif status_data["status"] == "failed":
                print(f"❌ Auto-setup failed: {status_data.get('error_message')}")
                return
        
        time.sleep(2)
        waited += 2
    
    if waited >= max_wait:
        print("⏱️ Timeout waiting for auto-setup")
        return
    
    # Execute target step (iteration 1)
    print(f"\n3️⃣ Executing target step (iteration 1)...")
    response = requests.post(
        f"{BASE_URL}/debug/execute-step",
        headers=headers,
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Step executed:")
        print(f"   Success: {result['success']}")
        print(f"   Duration: {result['duration_seconds']:.2f}s")
        print(f"   Tokens: {result['tokens_used']}")
        print(f"   Iterations: {result['iterations_count']}")
        if result.get('error_message'):
            print(f"   Error: {result['error_message']}")
    else:
        print(f"❌ Failed to execute step: {response.status_code}")
        print(response.text)
    
    # Execute target step again (iteration 2)
    print(f"\n4️⃣ Executing target step again (iteration 2)...")
    response = requests.post(
        f"{BASE_URL}/debug/execute-step",
        headers=headers,
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Step executed:")
        print(f"   Success: {result['success']}")
        print(f"   Duration: {result['duration_seconds']:.2f}s")
        print(f"   Tokens: {result['tokens_used']}")
        print(f"   Iterations: {result['iterations_count']}")
    
    # Stop debug session
    print(f"\n5️⃣ Stopping debug session...")
    response = requests.post(
        f"{BASE_URL}/debug/stop",
        headers=headers,
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Debug session stopped:")
        print(f"   Total tokens: {result['total_tokens_used']}")
        print(f"   Total iterations: {result['total_iterations']}")
        print(f"   Duration: {result['duration_seconds']:.2f}s")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Failed to stop session: {response.status_code}")

def test_manual_mode(token, execution_id, total_steps):
    """Test debug session in MANUAL mode."""
    print("\n" + "="*60)
    print("👤 Testing MANUAL MODE")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Choose a step to debug
    target_step = max(2, total_steps // 2)
    
    # Start debug session
    print(f"\n1️⃣ Starting debug session for step {target_step} (manual mode)...")
    response = requests.post(
        f"{BASE_URL}/debug/start",
        headers=headers,
        json={
            "execution_id": execution_id,
            "target_step_number": target_step,
            "mode": "manual"
        }
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to start debug session: {response.status_code}")
        print(response.text)
        return
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Debug session started: {session_id}")
    print(f"   Mode: {session_data['mode']}")
    print(f"   Message: {session_data['message']}")
    
    # Get manual instructions
    print(f"\n2️⃣ Getting manual setup instructions...")
    response = requests.get(
        f"{BASE_URL}/debug/{session_id}/instructions",
        headers=headers
    )
    
    if response.status_code == 200:
        instructions_data = response.json()
        print(f"✅ Manual instructions retrieved:")
        print(f"   Steps to complete: {len(instructions_data['prerequisite_steps'])}")
        print(f"   Estimated time: {instructions_data['estimated_time_minutes']} minutes")
        print(f"\n   Instructions:")
        print(f"   {instructions_data['instructions_summary']}")
    else:
        print(f"❌ Failed to get instructions: {response.status_code}")
    
    # Confirm manual setup (simulating user completion)
    print(f"\n3️⃣ Confirming manual setup complete...")
    response = requests.post(
        f"{BASE_URL}/debug/confirm-setup",
        headers=headers,
        json={
            "session_id": session_id,
            "setup_completed": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Manual setup confirmed:")
        print(f"   Status: {result['status']}")
        print(f"   Ready: {result['ready_for_debug']}")
        print(f"   Message: {result['message']}")
    
    # Execute target step
    print(f"\n4️⃣ Executing target step...")
    response = requests.post(
        f"{BASE_URL}/debug/execute-step",
        headers=headers,
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Step executed:")
        print(f"   Success: {result['success']}")
        print(f"   Tokens: {result['tokens_used']}")
        print(f"   Note: Manual mode uses 0 tokens for setup!")
    
    # Stop debug session
    print(f"\n5️⃣ Stopping debug session...")
    response = requests.post(
        f"{BASE_URL}/debug/stop",
        headers=headers,
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Debug session stopped:")
        print(f"   Total tokens: {result['total_tokens_used']}")
        print(f"   Message: Manual mode saved ~600 tokens on setup!")

def main():
    """Main test function."""
    print("🧪 Testing Local Persistent Browser Debug Mode")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        return
    
    # Get test execution
    execution_id, total_steps = get_test_execution(token)
    if not execution_id:
        print("\n⚠️ Please run a test execution first using the frontend or API")
        return
    
    # Test auto mode
    test_auto_mode(token, execution_id, total_steps)
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before testing manual mode...")
    time.sleep(5)
    
    # Test manual mode
    test_manual_mode(token, execution_id, total_steps)
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
