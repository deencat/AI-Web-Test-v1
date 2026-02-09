#!/usr/bin/env python3
"""Find recent test cases"""

import sqlite3
import json

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# Get recent test cases
cursor.execute("""
    SELECT id, title, created_at, test_data 
    FROM test_cases 
    ORDER BY created_at DESC 
    LIMIT 10
""")

rows = cursor.fetchall()

print("Recent test cases:")
print("=" * 80)

for row in rows:
    test_id, title, created_at, test_data_json = row
    print(f"\nID: {test_id}")
    print(f"Title: {title}")
    print(f"Created: {created_at}")
    
    if test_data_json:
        test_data = json.loads(test_data_json)
        detailed_steps = test_data.get('detailed_steps', [])
        if detailed_steps:
            print(f"Detailed steps: {len(detailed_steps)} steps")
            # Show first step value if it exists
            if len(detailed_steps) > 0 and 'value' in detailed_steps[0]:
                print(f"First step value: {detailed_steps[0]['value']}")
        else:
            print("Detailed steps: None")
    print("-" * 80)

conn.close()
