"""
End-to-End Integration Tests for Test Data Generation
Tests the complete flow: Test data generation → Variable substitution → Execution
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.execution_service import ExecutionService
from app.utils.test_data_generator import TestDataGenerator


class TestE2ETestDataGeneration:
    """End-to-end tests for test data generation in execution flow"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = TestDataGenerator()
    
    @pytest.mark.asyncio
    async def test_split_hkid_field_execution(self):
        """Test HKID split fields (main + check) in actual execution flow"""
        # Simulate a test case with split HKID fields
        steps = [
            "Enter HKID main part",
            "Enter HKID check digit"
        ]
        
        detailed_steps = [
            {
                "action": "fill",
                "selector": "input[name='hkid_main']",
                "value": "{generate:hkid:main}",
                "instruction": "Enter HKID main part"
            },
            {
                "action": "fill",
                "selector": "input[name='hkid_check']",
                "value": "{generate:hkid:check}",
                "instruction": "Enter HKID check digit"
            }
        ]
        
        execution_id = 12345  # Test execution ID for caching
        
        # Apply test data generation
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Substitute step 1 (main part)
        step1_data = {
            'action': 'fill',
            'selector': 'input[name="hkid_main"]',
            'value': '{generate:hkid:main}',
            'instruction': 'Enter HKID main part'
        }
        result1 = service._apply_test_data_generation(step1_data, execution_id)
        
        # Substitute step 2 (check digit)
        step2_data = {
            'action': 'fill',
            'selector': 'input[name="hkid_check"]',
            'value': '{generate:hkid:check}',
            'instruction': 'Enter HKID check digit'
        }
        result2 = service._apply_test_data_generation(step2_data, execution_id)
        
        # Assertions
        # 1. Both values should be substituted (not contain {generate:...})
        assert '{generate' not in result1['value']
        assert '{generate' not in result2['value']
        
        # 2. Main part should be in format A123456 (letter + 6 digits)
        main_part = result1['value']
        assert len(main_part) == 7
        assert main_part[0].isalpha()
        assert main_part[1:].isdigit()
        
        # 3. Check digit should be single character (digit or 'A')
        check_digit = result2['value']
        assert len(check_digit) == 1
        assert check_digit.isdigit() or check_digit == 'A'
        
        # 4. Verify check digit is valid for the main part
        # Reconstruct full HKID and validate
        full_hkid = f"{main_part}({check_digit})"
        letter = main_part[0]
        digits = main_part[1:]
        expected_check = self.generator._calculate_hkid_check_digit(letter, digits)
        assert check_digit == expected_check, f"Check digit mismatch: {check_digit} != {expected_check}"
        
        print(f"✅ Generated HKID: {full_hkid}")
        print(f"   Main part (field 1): {main_part}")
        print(f"   Check digit (field 2): {check_digit}")
    
    @pytest.mark.asyncio
    async def test_multiple_data_types_in_single_test(self):
        """Test generating HKID, phone, and email in same test execution"""
        execution_id = 67890
        
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Step 1: HKID
        step1 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid}'},
            execution_id
        )
        
        # Step 2: Phone
        step2 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:phone}'},
            execution_id
        )
        
        # Step 3: Email
        step3 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:email}'},
            execution_id
        )
        
        # Assertions
        # HKID format: A123456(3)
        hkid = step1['value']
        assert len(hkid) >= 9  # A123456(3)
        assert '(' in hkid and ')' in hkid
        
        # Phone format: 91234567 (8 digits, starts with 5-9)
        phone = step2['value']
        assert len(phone) == 8
        assert phone.isdigit()
        assert phone[0] in '56789'
        
        # Email format: testuser123@example.com
        email = step3['value']
        assert '@' in email
        assert email.startswith('testuser')
        assert email.endswith('@example.com')
        
        print(f"✅ Generated data for test execution {execution_id}:")
        print(f"   HKID: {hkid}")
        print(f"   Phone: {phone}")
        print(f"   Email: {email}")
    
    @pytest.mark.asyncio
    async def test_value_caching_across_steps(self):
        """Test that same data type uses cached value within same execution"""
        execution_id = 11111
        
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Generate HKID main part (should create new HKID)
        step1 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid:main}'},
            execution_id
        )
        main_part1 = step1['value']
        
        # Generate HKID check digit (should use cached HKID)
        step2 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid:check}'},
            execution_id
        )
        check_digit = step2['value']
        
        # Generate HKID main part again (should use same cached HKID)
        step3 = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid:main}'},
            execution_id
        )
        main_part2 = step3['value']
        
        # Assertions
        # 1. Both main part extractions should be identical (same cached HKID)
        assert main_part1 == main_part2, "Main part should be consistent across steps"
        
        # 2. Check digit should match the main part
        letter = main_part1[0]
        digits = main_part1[1:]
        expected_check = self.generator._calculate_hkid_check_digit(letter, digits)
        assert check_digit == expected_check
        
        print(f"✅ Caching verified for execution {execution_id}:")
        print(f"   Step 1 main part: {main_part1}")
        print(f"   Step 2 check digit: {check_digit}")
        print(f"   Step 3 main part: {main_part2}")
        print(f"   Consistency: {main_part1 == main_part2}")
    
    @pytest.mark.asyncio
    async def test_different_executions_get_different_values(self):
        """Test that different execution IDs generate different values"""
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Execution 1
        exec1_step = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid}'},
            99991  # test_id
        )
        hkid1 = exec1_step['value']
        
        # Execution 2
        exec2_step = service._apply_test_data_generation(
            {'action': 'fill', 'value': '{generate:hkid}'},
            99992  # test_id
        )
        hkid2 = exec2_step['value']
        
        # Assertions
        # Different executions should get different HKIDs
        assert hkid1 != hkid2, "Different executions should generate unique values"
        
        print(f"✅ Uniqueness verified:")
        print(f"   Execution 99991 HKID: {hkid1}")
        print(f"   Execution 99992 HKID: {hkid2}")
    
    @pytest.mark.asyncio
    async def test_no_substitution_for_normal_values(self):
        """Test that normal values without {generate:...} are not modified"""
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Normal value (no placeholder)
        step_data = {
            'action': 'fill',
            'value': 'A123456(3)',  # Looks like HKID but no {generate:...}
            'instruction': 'Enter HKID'
        }
        
        result = service._apply_test_data_generation(step_data, 12345)
        
        # Should remain unchanged
        assert result['value'] == 'A123456(3)'
        
        print(f"✅ Normal values preserved: {result['value']}")
    
    @pytest.mark.asyncio
    async def test_step_description_substitution(self):
        """Test that step descriptions can also use test data generation"""
        from app.services.execution_service import ExecutionService
        service = ExecutionService()
        
        # Step description with placeholder
        step_description = "Enter HKID: {generate:hkid}"
        
        result = service._substitute_test_data_patterns(
            step_description,
            12345  # test_id
        )
        
        # Should be substituted
        assert '{generate' not in result
        assert len(result) > len("Enter HKID: ")
        
        print(f"✅ Step description substituted: {result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
