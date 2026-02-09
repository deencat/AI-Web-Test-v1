#!/usr/bin/env python3
"""
Fix test case #101:
1. Remove {generate:*} patterns from step descriptions
2. Ensure detailed_steps instructions match the cleaned step descriptions
3. Change action from 'input' to 'fill' for compatibility
"""

import sqlite3
import json

def main():
    conn = sqlite3.connect('aiwebtest.db')
    cursor = conn.cursor()
    
    # Get test case #101
    cursor.execute('SELECT id, title, steps, test_data FROM test_cases WHERE id = 101')
    row = cursor.fetchone()
    
    if not row:
        print("❌ Test case #101 not found")
        return
    
    test_id, title, steps_json, test_data_json = row
    steps = json.loads(steps_json)
    test_data = json.loads(test_data_json) if test_data_json else {}
    
    print(f"Fixing test case #{test_id}: {title}\n")
    
    # Fix step descriptions: Remove {generate:*} patterns
    import re
    pattern = r'\{generate:\w+(?::\w+)?\}'
    
    print("Step descriptions before:")
    for i in [20, 21]:  # Steps 21, 22 (0-indexed: 20, 21)
        print(f"  Step {i+1}: {steps[i]}")
    
    for i in range(len(steps)):
        steps[i] = re.sub(pattern, '', steps[i]).strip()
        # Clean up double spaces
        steps[i] = re.sub(r'\s+', ' ', steps[i])
    
    print("\nStep descriptions after:")
    for i in [20, 21]:
        print(f"  Step {i+1}: {steps[i]}")
    
    # Fix detailed_steps: Match instructions to cleaned steps and change 'input' to 'fill'
    if 'detailed_steps' in test_data:
        print(f"\nFixing {len(test_data['detailed_steps'])} detailed_steps...")
        
        for ds in test_data['detailed_steps']:
            # Update instructions to match cleaned step descriptions
            instruction = ds.get('instruction', '')
            
            # Find matching step
            for step_desc in steps:
                if instruction.strip().rstrip('.') in step_desc:
                    ds['instruction'] = step_desc
                    break
            
            # Change 'input' action to 'fill' for compatibility
            if ds.get('action') == 'input':
                ds['action'] = 'fill'
                print(f"  Changed action 'input' → 'fill' for: {ds.get('instruction', '')[:50]}...")
    
    # Update database
    steps_json_updated = json.dumps(steps, ensure_ascii=False)
    test_data_json_updated = json.dumps(test_data, ensure_ascii=False)
    
    cursor.execute(
        "UPDATE test_cases SET steps = ?, test_data = ? WHERE id = ?",
        (steps_json_updated, test_data_json_updated, test_id)
    )
    
    conn.commit()
    print(f"\n✅ Test case #{test_id} fixed successfully!")
    
    # Verify
    cursor.execute('SELECT steps, test_data FROM test_cases WHERE id = 101')
    row = cursor.fetchone()
    steps_verify = json.loads(row[0])
    test_data_verify = json.loads(row[1])
    
    print("\n=== Verification ===")
    print(f"Step 21: {steps_verify[20]}")
    print(f"Step 22: {steps_verify[21]}")
    print(f"\nDetailed_steps[0]:")
    print(f"  instruction: {test_data_verify['detailed_steps'][0]['instruction']}")
    print(f"  action: {test_data_verify['detailed_steps'][0]['action']}")
    print(f"  value: {test_data_verify['detailed_steps'][0]['value']}")
    print(f"\nDetailed_steps[1]:")
    print(f"  instruction: {test_data_verify['detailed_steps'][1]['instruction']}")
    print(f"  action: {test_data_verify['detailed_steps'][1]['action']}")
    print(f"  value: {test_data_verify['detailed_steps'][1]['value']}")
    
    conn.close()

if __name__ == "__main__":
    main()
