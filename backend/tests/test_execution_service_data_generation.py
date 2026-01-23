"""
Unit Tests for Test Data Generation Integration in ExecutionService

Tests the variable substitution and test data generation in execution flow:
- Test data pattern detection and substitution
- HKID part extraction for split fields
- Caching consistency across multiple steps
- Integration with loop variables
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from app.services.execution_service import ExecutionService, ExecutionConfig
from app.utils.test_data_generator import TestDataGenerator


class TestDataGenerationSubstitution:
    """Test test data pattern substitution in text strings"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = ExecutionConfig()
        self.service = ExecutionService(self.config)
    
    def test_hkid_full_generation(self):
        """Test full HKID generation with {generate:hkid}"""
        text = "Enter HKID: {generate:hkid}"
        test_id = 1
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should replace with full HKID format: A123456(3)
        assert "{generate:hkid}" not in result
        assert "Enter HKID:" in result
        
        # Extract generated HKID
        generated_hkid = result.replace("Enter HKID: ", "")
        
        # Validate format: L######(C)
        assert len(generated_hkid) == 10
        assert generated_hkid[0].isalpha()
        assert generated_hkid[1:7].isdigit()
        assert generated_hkid[7] == '('
        assert generated_hkid[9] == ')'
        
        # Validate check digit
        assert TestDataGenerator.validate_hkid(generated_hkid)
    
    def test_hkid_main_part_extraction(self):
        """Test HKID main part extraction with {generate:hkid:main}"""
        text = "Enter main: {generate:hkid:main}"
        test_id = 2
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should replace with main part only: A123456
        assert "{generate:hkid:main}" not in result
        assert "Enter main:" in result
        
        # Extract main part
        main_part = result.replace("Enter main: ", "")
        
        # Validate format: L######
        assert len(main_part) == 7
        assert main_part[0].isalpha()
        assert main_part[1:7].isdigit()
        assert '(' not in main_part
    
    def test_hkid_check_digit_extraction(self):
        """Test HKID check digit extraction with {generate:hkid:check}"""
        text = "Enter check: {generate:hkid:check}"
        test_id = 3
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should replace with check digit only: 3 or A
        assert "{generate:hkid:check}" not in result
        assert "Enter check:" in result
        
        # Extract check digit
        check_digit = result.replace("Enter check: ", "")
        
        # Validate: single character (0-9 or A)
        assert len(check_digit) == 1
        assert check_digit.isdigit() or check_digit == 'A'
    
    def test_hkid_consistency_across_parts(self):
        """Test that main and check digit come from same HKID"""
        test_id = 4
        
        # Generate main part
        text_main = "Main: {generate:hkid:main}"
        result_main = self.service._substitute_test_data_patterns(text_main, test_id)
        main_part = result_main.replace("Main: ", "")
        
        # Generate check digit (should use same cached HKID)
        text_check = "Check: {generate:hkid:check}"
        result_check = self.service._substitute_test_data_patterns(text_check, test_id)
        check_digit = result_check.replace("Check: ", "")
        
        # Reconstruct full HKID
        reconstructed_hkid = f"{main_part}({check_digit})"
        
        # Should be valid
        assert TestDataGenerator.validate_hkid(reconstructed_hkid)
    
    def test_phone_generation(self):
        """Test phone number generation with {generate:phone}"""
        text = "Phone: {generate:phone}"
        test_id = 5
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should replace with phone number
        assert "{generate:phone}" not in result
        assert "Phone:" in result
        
        # Extract phone
        phone = result.replace("Phone: ", "")
        
        # Validate format: 8 digits starting with 5-9
        assert len(phone) == 8
        assert phone.isdigit()
        assert phone[0] in ['5', '6', '7', '8', '9']
    
    def test_email_generation(self):
        """Test email generation with {generate:email}"""
        text = "Email: {generate:email}"
        test_id = 6
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should replace with email
        assert "{generate:email}" not in result
        assert "Email:" in result
        
        # Extract email
        email = result.replace("Email: ", "")
        
        # Validate format: testuser{id}@example.com
        assert '@' in email
        assert email.endswith('@example.com')
        assert email.startswith('testuser')
    
    def test_multiple_patterns_in_text(self):
        """Test multiple generation patterns in same text"""
        text = "HKID: {generate:hkid:main}, Check: {generate:hkid:check}, Phone: {generate:phone}"
        test_id = 7
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # All patterns should be replaced
        assert "{generate:" not in result
        assert "HKID:" in result
        assert "Check:" in result
        assert "Phone:" in result
        
        # Extract parts
        parts = result.split(", ")
        main_part = parts[0].replace("HKID: ", "")
        check_digit = parts[1].replace("Check: ", "")
        phone = parts[2].replace("Phone: ", "")
        
        # Validate HKID consistency
        reconstructed_hkid = f"{main_part}({check_digit})"
        assert TestDataGenerator.validate_hkid(reconstructed_hkid)
        
        # Validate phone
        assert len(phone) == 8
        assert phone.isdigit()
    
    def test_caching_across_calls(self):
        """Test that generated values are cached per test_id"""
        test_id = 8
        
        # First call
        result1 = self.service._substitute_test_data_patterns("{generate:hkid}", test_id)
        
        # Second call (should return same HKID)
        result2 = self.service._substitute_test_data_patterns("{generate:hkid}", test_id)
        
        # Should be identical
        assert result1 == result2
    
    def test_different_test_ids_generate_different_values(self):
        """Test that different test_ids generate different values"""
        # Test ID 9
        result1 = self.service._substitute_test_data_patterns("{generate:hkid}", 9)
        
        # Test ID 10
        result2 = self.service._substitute_test_data_patterns("{generate:hkid}", 10)
        
        # Should be different
        assert result1 != result2
    
    def test_unknown_data_type(self):
        """Test handling of unknown data type"""
        text = "Unknown: {generate:passport}"
        test_id = 11
        
        result = self.service._substitute_test_data_patterns(text, test_id)
        
        # Should return original pattern unchanged
        assert "{generate:passport}" in result
    
    def test_unknown_hkid_part(self):
        """Test handling of unknown HKID part"""
        # Generate HKID first to populate cache
        self.service._substitute_test_data_patterns("{generate:hkid}", 12)
        
        # Try to extract invalid part
        text = "Invalid: {generate:hkid:invalid}"
        
        result = self.service._substitute_test_data_patterns(text, 12)
        
        # Should return original pattern on error
        assert "{generate:hkid:invalid}" in result
    
    def test_empty_text(self):
        """Test handling of empty text"""
        result = self.service._substitute_test_data_patterns("", 13)
        assert result == ""
    
    def test_none_text(self):
        """Test handling of None text"""
        result = self.service._substitute_test_data_patterns(None, 14)
        assert result is None
    
    def test_text_without_patterns(self):
        """Test text without any generation patterns"""
        text = "Regular text without patterns"
        result = self.service._substitute_test_data_patterns(text, 15)
        
        # Should return unchanged
        assert result == text


class TestDetailedStepDataGeneration:
    """Test test data generation in detailed step dictionaries"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = ExecutionConfig()
        self.service = ExecutionService(self.config)
    
    def test_apply_to_value_field(self):
        """Test generation applied to value field"""
        detailed_step = {
            "action": "fill",
            "selector": "#hkid",
            "value": "{generate:hkid}"
        }
        test_id = 20
        
        result = self.service._apply_test_data_generation(detailed_step, test_id)
        
        # Value should be replaced
        assert "{generate:hkid}" not in result["value"]
        assert TestDataGenerator.validate_hkid(result["value"])
        
        # Other fields unchanged
        assert result["action"] == "fill"
        assert result["selector"] == "#hkid"
    
    def test_apply_to_selector_field(self):
        """Test generation applied to selector field (edge case)"""
        detailed_step = {
            "action": "click",
            "selector": "button[data-hkid='{generate:hkid:main}']",
            "value": ""
        }
        test_id = 21
        
        result = self.service._apply_test_data_generation(detailed_step, test_id)
        
        # Selector should be replaced
        assert "{generate:hkid:main}" not in result["selector"]
        assert "button[data-hkid='" in result["selector"]
    
    def test_apply_to_multiple_fields(self):
        """Test generation applied to multiple fields"""
        detailed_step = {
            "action": "fill",
            "selector": "input[name='hkid_{generate:hkid:letter}']",
            "value": "{generate:hkid:main}"
        }
        test_id = 22
        
        result = self.service._apply_test_data_generation(detailed_step, test_id)
        
        # Both should be replaced with same HKID
        assert "{generate:" not in result["selector"]
        assert "{generate:" not in result["value"]
        
        # Extract values
        # Selector: input[name='hkid_A']
        # Value: A123456
        selector_letter = result["selector"].split("hkid_")[1][0]
        value_letter = result["value"][0]
        
        # Should match (both from same cached HKID)
        assert selector_letter == value_letter
    
    def test_none_detailed_step(self):
        """Test handling of None detailed step"""
        result = self.service._apply_test_data_generation(None, 23)
        assert result is None
    
    def test_empty_detailed_step(self):
        """Test handling of empty detailed step"""
        result = self.service._apply_test_data_generation({}, 24)
        assert result == {}
    
    def test_non_string_fields(self):
        """Test handling of non-string fields"""
        detailed_step = {
            "action": "click",
            "selector": "#button",
            "timeout": 5000,  # integer
            "retry": True  # boolean
        }
        test_id = 25
        
        result = self.service._apply_test_data_generation(detailed_step, test_id)
        
        # Non-string fields should be unchanged
        assert result["timeout"] == 5000
        assert result["retry"] is True
    
    def test_original_not_modified(self):
        """Test that original detailed_step dict is not modified"""
        original = {
            "action": "fill",
            "selector": "#hkid",
            "value": "{generate:hkid}"
        }
        test_id = 26
        
        result = self.service._apply_test_data_generation(original, test_id)
        
        # Original should still have pattern
        assert original["value"] == "{generate:hkid}"
        
        # Result should have generated value
        assert "{generate:hkid}" not in result["value"]


class TestSplitFieldScenario:
    """Test real-world split field scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = ExecutionConfig()
        self.service = ExecutionService(self.config)
    
    def test_split_hkid_two_fields(self):
        """Test split HKID: main in field 1, check in field 2"""
        test_id = 30
        
        # Step 1: Fill main part
        step1 = {
            "action": "fill",
            "selector": "#hkid_main",
            "value": "{generate:hkid:main}"
        }
        result1 = self.service._apply_test_data_generation(step1, test_id)
        main_value = result1["value"]
        
        # Step 2: Fill check digit
        step2 = {
            "action": "fill",
            "selector": "#hkid_check",
            "value": "{generate:hkid:check}"
        }
        result2 = self.service._apply_test_data_generation(step2, test_id)
        check_value = result2["value"]
        
        # Reconstruct and validate
        full_hkid = f"{main_value}({check_value})"
        assert TestDataGenerator.validate_hkid(full_hkid)
    
    def test_split_hkid_three_fields(self):
        """Test split HKID: letter, digits, check in 3 separate fields"""
        test_id = 31
        
        # Field 1: Letter
        step1 = {
            "action": "fill",
            "selector": "#hkid_letter",
            "value": "{generate:hkid:letter}"
        }
        result1 = self.service._apply_test_data_generation(step1, test_id)
        letter = result1["value"]
        
        # Field 2: Digits
        step2 = {
            "action": "fill",
            "selector": "#hkid_digits",
            "value": "{generate:hkid:digits}"
        }
        result2 = self.service._apply_test_data_generation(step2, test_id)
        digits = result2["value"]
        
        # Field 3: Check digit
        step3 = {
            "action": "fill",
            "selector": "#hkid_check",
            "value": "{generate:hkid:check}"
        }
        result3 = self.service._apply_test_data_generation(step3, test_id)
        check = result3["value"]
        
        # Reconstruct and validate
        full_hkid = f"{letter}{digits}({check})"
        assert TestDataGenerator.validate_hkid(full_hkid)
    
    def test_full_then_split(self):
        """Test generating full HKID then extracting parts"""
        test_id = 32
        
        # Generate full HKID first
        text_full = "{generate:hkid}"
        full_hkid = self.service._substitute_test_data_patterns(text_full, test_id)
        
        # Extract main part (should use same cached HKID)
        step_main = {
            "action": "fill",
            "selector": "#main",
            "value": "{generate:hkid:main}"
        }
        result_main = self.service._apply_test_data_generation(step_main, test_id)
        
        # Verify consistency
        assert full_hkid.startswith(result_main["value"][:-1])  # Full starts with main (excluding check)


class TestIntegrationWithLoopVariables:
    """Test that test data generation works alongside loop variables"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = ExecutionConfig()
        self.service = ExecutionService(self.config)
    
    def test_combine_loop_and_test_data(self):
        """Test combining loop variables and test data generation"""
        test_id = 40
        
        # Simulate: Fill document {iteration} with HKID {generate:hkid}
        text = "Upload document {iteration} for HKID: {generate:hkid:main}"
        
        # Apply loop variables first (iteration = 3)
        text_with_iteration = text.replace("{iteration}", "3")
        
        # Apply test data generation
        result = self.service._substitute_test_data_patterns(text_with_iteration, test_id)
        
        # Should have both substitutions
        assert "document 3" in result
        assert "HKID:" in result
        assert "{generate:" not in result
        assert "{iteration}" not in result


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = ExecutionConfig()
        self.service = ExecutionService(self.config)
    
    def test_malformed_pattern(self):
        """Test malformed pattern syntax"""
        text = "Bad: {generate:hkid"  # Missing closing brace
        result = self.service._substitute_test_data_patterns(text, 50)
        
        # Should return unchanged (pattern not matched)
        assert result == text
    
    def test_nested_patterns(self):
        """Test nested patterns (not supported)"""
        text = "Nested: {generate:{generate:hkid}}"
        result = self.service._substitute_test_data_patterns(text, 51)
        
        # Inner pattern replaced, outer stays
        assert "{generate:{generate:hkid}}" not in result
    
    def test_case_sensitivity(self):
        """Test pattern case sensitivity"""
        text = "Upper: {GENERATE:HKID}"  # Uppercase
        result = self.service._substitute_test_data_patterns(text, 52)
        
        # Should not match (case sensitive)
        assert "{GENERATE:HKID}" in result
    
    def test_whitespace_in_pattern(self):
        """Test whitespace handling in patterns"""
        text = "Spaces: { generate : hkid }"  # Spaces inside braces
        result = self.service._substitute_test_data_patterns(text, 53)
        
        # Should not match (no whitespace in pattern)
        assert "{ generate : hkid }" in result
    
    def test_very_large_test_id(self):
        """Test with very large test_id"""
        test_id = 999999999
        result = self.service._substitute_test_data_patterns("{generate:hkid}", test_id)
        
        # Should work normally
        assert "{generate:hkid}" not in result
        assert TestDataGenerator.validate_hkid(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
