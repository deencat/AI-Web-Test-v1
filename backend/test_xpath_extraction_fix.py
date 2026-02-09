#!/usr/bin/env python3
"""
Test XPath and Value Extraction from Instructions
Tests the fixes for Sprint 5.5 3-Tier Execution
"""
import re


def extract_selector_from_instruction(step_description: str) -> str:
    """
    Extract XPath or CSS selector from instruction text.
    
    Args:
        step_description: Test step description
        
    Returns:
        Extracted selector or empty string
    """
    selector = None
    
    # Try to extract XPath first (pattern: xpath "//..." or with xpath "//...")
    xpath_patterns = [
        r'xpath\s*"([^"]+)"',  # xpath "//button[@class='btn']" - double quotes
        r"xpath\s*'([^']+)'",  # xpath '//button[@class="btn"]' - single quotes
        r'with\s+xpath\s*"([^"]+)"',  # with xpath "//button"
        r"with\s+xpath\s*'([^']+)'",  # with xpath '//button'
        r'(//[\w\-/@\[\]()=\'"\s,\.]+)',  # raw XPath like //button[@id='login']
    ]
    for pattern in xpath_patterns:
        xpath_match = re.search(pattern, step_description)
        if xpath_match:
            selector = xpath_match.group(1)
            print(f"  ✅ Extracted XPath: {selector}")
            return selector
    
    # If no XPath found, try CSS selector (pattern: selector "..." or css "...")
    css_patterns = [
        r'selector\s*["\']([^"\']+)["\']',
        r'css\s*["\']([^"\']+)["\']',
    ]
    for pattern in css_patterns:
        css_match = re.search(pattern, step_description)
        if css_match:
            selector = css_match.group(1)
            print(f"  ✅ Extracted CSS selector: {selector}")
            return selector
    
    print(f"  ❌ No selector found")
    return ""


def extract_value_from_instruction(step_description: str, action: str) -> str:
    """
    Extract value (email, password, text) from instruction text.
    
    Args:
        step_description: Test step description
        action: Action type (fill, type, etc.)
        
    Returns:
        Extracted value or empty string
    """
    if action not in ["fill", "type", "enter", "input"]:
        return ""
    
    # Pattern 1: "Enter email: value" or "Enter password: value" (any value after colon)
    field_value_match = re.search(
        r'(?:enter|fill|type|input)\s+(?:email|password|username|name|text):\s*([^\s,;"\']+)',
        step_description,
        re.IGNORECASE
    )
    if field_value_match:
        value = field_value_match.group(1)
        print(f"  ✅ Extracted field value: {value}")
        return value
    
    # Pattern 2: Generic field pattern "field: value" (for any field type)
    generic_field_match = re.search(
        r':\s*([^\s,;"\']+)(?:\s+with\s+xpath|\s+with\s+selector|$)',
        step_description
    )
    if generic_field_match:
        potential_value = generic_field_match.group(1)
        # Make sure it's not a URL or selector
        if not potential_value.startswith('//') and not potential_value.startswith('http'):
            print(f"  ✅ Extracted value from generic pattern: {potential_value}")
            return potential_value
    
    # Pattern 3: Look for any text in quotes (could be password, username, etc.)
    quoted_values = re.findall(r'["\']([^"\']+)["\']', step_description)
    # Filter out XPath/CSS selectors from quoted values
    for quoted_value in quoted_values:
        if not quoted_value.startswith('//') and not quoted_value.startswith('.') and not quoted_value.startswith('#'):
            # Check if it looks like text input (not a selector)
            if not quoted_value.startswith('http') and len(quoted_value) < 100:
                print(f"  ✅ Extracted value from quotes: {quoted_value}")
                return quoted_value
    
    print(f"  ❌ No value found, using default")
    return "test input"


def test_extraction():
    """Test extraction with various instruction formats."""
    
    print("\n" + "="*80)
    print("Testing XPath and Value Extraction from Instructions")
    print("="*80 + "\n")
    
    # Test cases from the user's logs
    test_cases = [
        {
            "step": 'Step 2: Click Login button with xpath "//button[@class=\'btn btn-light\']"',
            "action": "click",
            "expected_selector": "//button[@class='btn btn-light']",
            "expected_value": ""
        },
        {
            "step": "Step 3: Enter email: pmo.andrewchan+010@gmail.com with xpath \"//input[@name='id']\"",
            "action": "fill",
            "expected_selector": "//input[@name='id']",
            "expected_value": "pmo.andrewchan+010@gmail.com"
        },
        {
            "step": "Step 4: Click Login button with xpath \"//div[contains(text(),'Login')]\"",
            "action": "click",
            "expected_selector": "//div[contains(text(),'Login')]",
            "expected_value": ""
        },
        # Additional test cases
        {
            "step": "Click the submit button //button[@id='submit']",
            "action": "click",
            "expected_selector": "//button[@id='submit']",
            "expected_value": ""
        },
        {
            "step": "Fill password: 'MySecretPass123' in field with xpath \"//input[@type='password']\"",
            "action": "fill",
            "expected_selector": "//input[@type='password']",
            "expected_value": "MySecretPass123"
        },
        {
            "step": "Type 'John Doe' into name field",
            "action": "fill",
            "expected_selector": "",
            "expected_value": "John Doe"
        },
        # New test cases for non-email values
        {
            "step": "Step 3: Enter email: invalid.email",
            "action": "fill",
            "expected_selector": "",
            "expected_value": "invalid.email"
        },
        {
            "step": "Enter username: testuser123",
            "action": "fill",
            "expected_selector": "",
            "expected_value": "testuser123"
        },
        {
            "step": "Fill password: secret123 with xpath \"//input[@type='password']\"",
            "action": "fill",
            "expected_selector": "//input[@type='password']",
            "expected_value": "secret123"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['step']}")
        print("-" * 80)
        
        # Extract selector
        actual_selector = extract_selector_from_instruction(test['step'])
        
        # Extract value
        actual_value = extract_value_from_instruction(test['step'], test['action'])
        
        # Check results
        selector_match = actual_selector == test['expected_selector']
        value_match = actual_value == test['expected_value']
        
        print(f"\n  Expected selector: {test['expected_selector'] or '(none)'}")
        print(f"  Actual selector:   {actual_selector or '(none)'}")
        print(f"  Selector match:    {'✅ PASS' if selector_match else '❌ FAIL'}")
        
        print(f"\n  Expected value:    {test['expected_value'] or '(none)'}")
        print(f"  Actual value:      {actual_value or '(none)'}")
        print(f"  Value match:       {'✅ PASS' if value_match else '❌ FAIL'}")
        
        if selector_match and value_match:
            passed += 1
            print(f"\n  ✅ Test {i} PASSED")
        else:
            failed += 1
            print(f"\n  ❌ Test {i} FAILED")
    
    print("\n" + "="*80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = test_extraction()
    exit(0 if success else 1)
