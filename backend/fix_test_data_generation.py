#!/usr/bin/env python3
"""
Fix test case to use test data generation properly
Adds detailed_steps with {generate:hkid:main} and {generate:hkid:check} in value fields
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ID = 288  # Adjust this to your actual test ID

# Detailed steps with proper test data generation patterns
detailed_steps = [
    {
        "action": "input",
        "selector": None,  # Let Tier 2 extract XPath
        "value": "{generate:hkid:main}",
        "instruction": "Step 21: input hkid number on id no. first field"
    },
    {
        "action": "input",
        "selector": None,  # Let Tier 2 extract XPath
        "value": "{generate:hkid:check}",
        "instruction": "Step 22: input hkid number on id no. second field"
    },
    {
        "action": "click",
        "selector": None,
        "instruction": "Step 23: Click male button"
    },
    {
        "action": "input",
        "selector": None,
        "value": "test",
        "instruction": "Step 24: Input english surname"
    },
    {
        "action": "input",
        "selector": None,
        "value": "abc",
        "instruction": "Step 25: Input english first name"
    },
    {
        "action": "input",
        "selector": None,
        "value": "陳小文",
        "instruction": "Step 26: Input chinese name"
    },
    {
        "action": "input",
        "selector": None,
        "value": "2000/01/01",
        "instruction": "Step 27: Input date of birth"
    },
    {
        "action": "input",
        "selector": None,
        "value": "90457537",
        "instruction": "Step 28: Input contact number"
    },
    {
        "action": "click",
        "selector": None,
        "instruction": "Step 29: click next button"
    }
]

# Steps array (descriptions only)
steps = [
    "Step 21: input hkid number {generate:hkid:main} on id no. first field",
    "Step 22: input hkid number {generate:hkid:check} on id no. second field",
    "Step 23: Click male button",
    "Step 24: Input english surname test",
    "Step 25: Input english first name abc",
    "Step 26: Input chinese name 陳小文",
    "Step 27: Input date of birth 2000/01/01",
    "Step 28: Input contact number 90457537",
    "Step 29: click next button"
]

def update_test_case():
    """Update test case with proper detailed_steps"""
    
    # First, get current test case
    print(f"Fetching test case {TEST_ID}...")
    response = requests.get(f"{BASE_URL}/tests/{TEST_ID}")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch test case: {response.status_code}")
        print(response.text)
        return
    
    test_case = response.json()
    print(f"✅ Found test: {test_case.get('title', 'Untitled')}")
    
    # Update with detailed_steps
    update_data = {
        "steps": steps,
        "detailed_steps": detailed_steps
    }
    
    print(f"\nUpdating test case with detailed_steps...")
    response = requests.put(
        f"{BASE_URL}/tests/{TEST_ID}",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Test case updated successfully!")
        print("\nVerification:")
        print(f"  Step 21 value: {detailed_steps[0]['value']}")
        print(f"  Step 22 value: {detailed_steps[1]['value']}")
        print(f"  Step 24 value: {detailed_steps[3]['value']}")
        print(f"  Step 28 value: {detailed_steps[7]['value']}")
    else:
        print(f"❌ Failed to update test case: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("=" * 60)
    print("Test Data Generation Fix Script")
    print("=" * 60)
    update_test_case()
    print("\n" + "=" * 60)
    print("Next: Re-run your test to see HKID generation working!")
    print("=" * 60)
