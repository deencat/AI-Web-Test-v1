#!/usr/bin/env python3
"""
Update test case #101 with HKID generation patterns
"""

import sqlite3
import json

conn = sqlite3.connect('aiwebtest.db')
cursor = conn.cursor()

# Use test_case_id = 101 directly
test_case_id = 101
print(f"Updating test case {test_case_id}...")

# Now update the test case
detailed_steps = [
    {
        "action": "input",
        "selector": None,
        "value": "{generate:hkid:main}",
        "instruction": "Step 21: input hkid number on id no. first field"
    },
    {
        "action": "input",
        "selector": None,
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

# Get current test_data
cursor.execute("SELECT test_data FROM test_cases WHERE id = ?", (test_case_id,))
result = cursor.fetchone()

if result and result[0]:
    test_data = json.loads(result[0])
else:
    test_data = {}

# Update detailed_steps
test_data['detailed_steps'] = detailed_steps

# Save back to database
cursor.execute(
    "UPDATE test_cases SET test_data = ? WHERE id = ?",
    (json.dumps(test_data), test_case_id)
)
conn.commit()

print(f"✅ Updated test case {test_case_id} with detailed_steps")
print(f"\nVerification:")
print(f"  Step 21 value: {detailed_steps[0]['value']}")
print(f"  Step 22 value: {detailed_steps[1]['value']}")
print(f"  Step 24 value: {detailed_steps[3]['value']}")
print(f"  Step 28 value: {detailed_steps[7]['value']}")

print("\n" + "="*60)
print("✅ Test case updated successfully!")
print("="*60)
print("\nNext step: Re-run your test execution")
print("The system will now:")
print("  1. Generate a valid HKID (e.g., A123456(3))")
print("  2. Extract main part → A123456 for field 1")
print("  3. Extract check digit → 3 for field 2")
print("  4. Use hardcoded values for other fields")
print("="*60)

conn.close()
