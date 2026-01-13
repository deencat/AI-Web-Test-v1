"""
Utility to manually create feedback for false positive test results.
Use this when a test passed but shouldn't have (wrong action, wrong element, etc.)
"""

import requests
import sys
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"


def login() -> str:
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]


def report_false_positive(
    execution_id: int,
    step_index: int,
    token: str,
    description: str,
    expected_action: str,
    actual_action: str,
    correct_selector: Optional[str] = None
) -> dict:
    """
    Report a false positive result.
    
    Args:
        execution_id: The execution that had the false positive
        step_index: Which step number had the issue
        token: Auth token
        description: What went wrong
        expected_action: What should have happened
        actual_action: What actually happened
        correct_selector: The corrected selector (optional)
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create feedback entry
    feedback_data = {
        "execution_id": execution_id,
        "step_index": step_index,
        "failure_type": "other",
        "error_message": f"FALSE POSITIVE: {description}",
        "notes": f"""
FALSE POSITIVE REPORT (Manual Review)
=====================================

Expected Action: {expected_action}
Actual Action: {actual_action}

Issue: Test reported success but the actual behavior was incorrect.
This is a false positive that needs attention.

Details: {description}
""",
        "tags": ["false-positive", "manual-review", "needs-correction"]
    }
    
    # Get execution details to populate more fields
    exec_response = requests.get(
        f"{BASE_URL}/executions/{execution_id}",
        headers=headers
    )
    
    if exec_response.status_code == 200:
        execution = exec_response.json()
        feedback_data["browser_type"] = execution.get("browser", "chromium")
        
        # Find the step details
        if "steps" in execution and len(execution["steps"]) > step_index:
            step = execution["steps"][step_index]
            feedback_data["failed_selector"] = step.get("selector", "")
            feedback_data["selector_type"] = "css"  # Default
            feedback_data["page_url"] = step.get("page_url", "")
    
    # Create the feedback
    response = requests.post(
        f"{BASE_URL}/feedback",
        headers=headers,
        json=feedback_data
    )
    
    if response.status_code == 201:
        feedback = response.json()
        print(f"\n✅ Created feedback entry #{feedback['id']}")
        print(f"   Execution: #{execution_id}")
        print(f"   Step: {step_index}")
        print(f"   Type: FALSE POSITIVE")
        
        # If correct selector provided, submit correction immediately
        if correct_selector:
            print(f"\n   Submitting correction with selector: {correct_selector}")
            correction = submit_correction(
                feedback['id'],
                token,
                correct_selector,
                expected_action
            )
            if correction:
                print(f"   ✅ Correction submitted")
        
        return feedback
    else:
        print(f"\n❌ Failed to create feedback: {response.status_code}")
        print(f"   {response.text}")
        return None


def submit_correction(
    feedback_id: int,
    token: str,
    correct_selector: str,
    description: str
) -> dict:
    """Submit a correction for the false positive."""
    headers = {"Authorization": f"Bearer {token}"}
    
    correction_data = {
        "corrected_step": {
            "action": "click",  # Most common, adjust as needed
            "selector": correct_selector,
            "value": "",
            "description": description
        },
        "correction_source": "human",
        "correction_confidence": 0.90,
        "notes": "Manual correction after identifying false positive"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback/{feedback_id}/correction",
        headers=headers,
        json=correction_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to submit correction: {response.text}")
        return None


def interactive_report():
    """Interactive mode to report false positives."""
    print("=" * 70)
    print("Report False Positive Test Result")
    print("=" * 70)
    print()
    
    token = login()
    print("✅ Logged in\n")
    
    # Get execution ID
    execution_id = input("Execution ID: ").strip()
    if not execution_id.isdigit():
        print("❌ Invalid execution ID")
        return
    execution_id = int(execution_id)
    
    # Get step index
    step_index = input("Step number (that had false positive): ").strip()
    if not step_index.isdigit():
        print("❌ Invalid step number")
        return
    step_index = int(step_index)
    
    # Get details
    print("\nDescribe the false positive:")
    description = input("What went wrong? ").strip()
    
    expected = input("What SHOULD have happened? ").strip()
    actual = input("What ACTUALLY happened? ").strip()
    
    # Optional correction
    print("\nDo you know the correct selector?")
    has_correction = input("(y/n): ").strip().lower()
    correct_selector = None
    if has_correction == 'y':
        correct_selector = input("Enter correct selector: ").strip()
    
    # Confirm
    print("\n" + "=" * 70)
    print("Review Your Report:")
    print("=" * 70)
    print(f"Execution ID: {execution_id}")
    print(f"Step: {step_index}")
    print(f"Issue: {description}")
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    if correct_selector:
        print(f"Correction: {correct_selector}")
    print("=" * 70)
    
    confirm = input("\nSubmit this report? (y/n): ").strip().lower()
    if confirm == 'y':
        feedback = report_false_positive(
            execution_id,
            step_index,
            token,
            description,
            expected,
            actual,
            correct_selector
        )
        
        if feedback:
            print("\n✅ Report submitted successfully!")
            print(f"\nView in UI: http://localhost:3000/executions/{execution_id}")
            print(f"View feedback API: {BASE_URL}/executions/{execution_id}/feedback")
    else:
        print("\n❌ Report cancelled")


def quick_report(execution_id: int, step_index: int, description: str):
    """Quick report without interactive prompts."""
    token = login()
    feedback = report_false_positive(
        execution_id,
        step_index,
        token,
        description,
        "Unknown - see description",
        "Unknown - see description"
    )
    return feedback


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Quick mode: python report_false_positive.py <execution_id> <step_index> "<description>"
        if len(sys.argv) >= 4:
            quick_report(
                int(sys.argv[1]),
                int(sys.argv[2]),
                sys.argv[3]
            )
        else:
            print("Usage: python report_false_positive.py <execution_id> <step_index> \"<description>\"")
            print("   OR: python report_false_positive.py    (for interactive mode)")
    else:
        # Interactive mode
        interactive_report()
