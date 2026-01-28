#!/usr/bin/env python3
"""Test value extraction from step descriptions"""
import re

# Test cases
test_cases = [
    ("Step 21: input hkid number Q496157 on id no. first field.", "Q496157"),
    ("Step 22: input hkid number 5 on id no. second field.", "5"),
    ("input hkid number (3) on check digit", "(3)"),
    ("contact number 90457537", "90457537"),
]

# Current patterns from the code
value_patterns = [
    # HKID patterns - Extract specific values mentioned in the description
    # Pattern 1: "input hkid number Q496157 on id no. first field" -> Extract Q496157
    r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?([A-Z]\d{6})\s+',  # Alphanumeric HKID (e.g., Q496157)
    # Pattern 2: "input hkid number 5 on id no. second field" -> Extract 5
    r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?(\d{1,2})\s+(?:on|in)',  # 1-2 digit number (e.g., 5)
    # Pattern 3: Check digit patterns (e.g., "(3)")
    r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?\((\d{1})\)',  # Check digit in parentheses
    
    # Contact/phone number - more flexible pattern
    r'(?:contact|phone|mobile).*?(\d{8})\s*$',  # "contact number 90457537"
    
    # Name patterns
    r'(?:surname|first\s+name)\s+([a-zA-Z]+)\s*$',  # "surname test" or "first name abc"
    r'(?:chinese\s+name)\s+([\u4e00-\u9fff]+)\s*$',  # "chinese name 陳小文"
    
    # Date pattern
    r'(?:birth|date).*?([\d/]+)\s*$',  # "birth 2000/01/01"
    
    # Generic fallback patterns
    r'(?:input|enter|fill|type)\s+([A-Z]\d{6})\s+',  # Generic: "input A123456 on"
    r'(?:input|enter|fill|type)\s+(\d{8})\s+',  # Generic: "input 12345678 on"
]

print("Testing Value Extraction Patterns:")
print("=" * 80)

for step_desc, expected in test_cases:
    print(f"\nTest: {step_desc}")
    print(f"Expected: {expected}")
    
    extracted = None
    for i, pattern in enumerate(value_patterns):
        match = re.search(pattern, step_desc, re.IGNORECASE)
        if match:
            potential_value = match.group(1)
            if "field" not in potential_value.lower():
                extracted = potential_value
                print(f"✓ Matched pattern {i}: {pattern}")
                print(f"  Extracted: {extracted}")
                break
    
    if extracted == expected:
        print(f"✓ SUCCESS: Extracted '{extracted}' matches expected '{expected}'")
    else:
        print(f"✗ FAILED: Extracted '{extracted}' does not match expected '{expected}'")

print("\n" + "=" * 80)
