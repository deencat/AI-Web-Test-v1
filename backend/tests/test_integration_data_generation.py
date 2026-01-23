"""
Integration Test for Test Data Generation in Execution Flow

Tests the complete flow of test data generation through the execution service:
- Test with HKID split fields
- Test with phone and email
- Test with loop integration
"""

import pytest
from app.services.execution_service import ExecutionService, ExecutionConfig
from app.utils.test_data_generator import TestDataGenerator


def test_split_hkid_execution_flow():
    """
    Integration test: Split HKID fields in a test case
    
    Simulates a test with:
    - Step 1: Fill HKID main part (A123456)
    - Step 2: Fill HKID check digit (3)
    """
    # Setup
    config = ExecutionConfig()
    service = ExecutionService(config)
    test_id = 100
    
    # Simulate test steps with split HKID fields
    steps = [
        {
            "step": "Fill HKID main part",
            "detailed_step": {
                "action": "fill",
                "selector": "#hkid_main",
                "value": "{generate:hkid:main}"
            }
        },
        {
            "step": "Fill HKID check digit",
            "detailed_step": {
                "action": "fill",
                "selector": "#hkid_check",
                "value": "{generate:hkid:check}"
            }
        }
    ]
    
    # Apply test data generation to both steps
    processed_steps = []
    for step in steps:
        detailed_step = service._apply_test_data_generation(
            step["detailed_step"],
            test_id
        )
        step_desc = service._substitute_test_data_patterns(
            step["step"],
            test_id
        )
        processed_steps.append({
            "step": step_desc,
            "detailed_step": detailed_step
        })
    
    # Verify results
    main_value = processed_steps[0]["detailed_step"]["value"]
    check_value = processed_steps[1]["detailed_step"]["value"]
    
    # Validate format
    assert len(main_value) == 7  # A123456
    assert main_value[0].isalpha()
    assert main_value[1:7].isdigit()
    
    assert len(check_value) == 1  # 3 or A
    assert check_value.isdigit() or check_value == 'A'
    
    # Reconstruct and validate HKID
    full_hkid = f"{main_value}({check_value})"
    assert TestDataGenerator.validate_hkid(full_hkid)
    
    print(f"\n✅ Split HKID Test Passed:")
    print(f"   Step 1: Fill HKID main → {main_value}")
    print(f"   Step 2: Fill check digit → {check_value}")
    print(f"   Reconstructed: {full_hkid} (Valid: {TestDataGenerator.validate_hkid(full_hkid)})")


def test_multiple_data_types_execution_flow():
    """
    Integration test: Multiple data types in one test
    
    Simulates a test with:
    - Step 1: Fill HKID
    - Step 2: Fill phone
    - Step 3: Fill email
    """
    # Setup
    config = ExecutionConfig()
    service = ExecutionService(config)
    test_id = 101
    
    # Simulate test steps
    steps = [
        {
            "step": "Enter HKID: {generate:hkid}",
            "detailed_step": {
                "action": "fill",
                "selector": "#hkid",
                "value": "{generate:hkid}"
            }
        },
        {
            "step": "Enter phone: {generate:phone}",
            "detailed_step": {
                "action": "fill",
                "selector": "#phone",
                "value": "{generate:phone}"
            }
        },
        {
            "step": "Enter email: {generate:email}",
            "detailed_step": {
                "action": "fill",
                "selector": "#email",
                "value": "{generate:email}"
            }
        }
    ]
    
    # Apply test data generation
    processed_steps = []
    for step in steps:
        detailed_step = service._apply_test_data_generation(
            step["detailed_step"],
            test_id
        )
        step_desc = service._substitute_test_data_patterns(
            step["step"],
            test_id
        )
        processed_steps.append({
            "step": step_desc,
            "detailed_step": detailed_step
        })
    
    # Verify HKID
    hkid = processed_steps[0]["detailed_step"]["value"]
    assert TestDataGenerator.validate_hkid(hkid)
    assert hkid in processed_steps[0]["step"]
    
    # Verify phone
    phone = processed_steps[1]["detailed_step"]["value"]
    assert len(phone) == 8
    assert phone.isdigit()
    assert phone[0] in ['5', '6', '7', '8', '9']
    assert phone in processed_steps[1]["step"]
    
    # Verify email
    email = processed_steps[2]["detailed_step"]["value"]
    assert '@' in email
    assert email.endswith('@example.com')
    assert email in processed_steps[2]["step"]
    
    print(f"\n✅ Multiple Data Types Test Passed:")
    print(f"   HKID: {hkid}")
    print(f"   Phone: {phone}")
    print(f"   Email: {email}")


def test_loop_with_test_data_execution_flow():
    """
    Integration test: Loop with test data generation
    
    Simulates uploading 3 documents with unique HKIDs
    """
    # Setup
    config = ExecutionConfig()
    service = ExecutionService(config)
    base_test_id = 102
    
    # Simulate loop: Upload 3 documents
    iterations = 3
    results = []
    
    for iteration in range(1, iterations + 1):
        # Each iteration uses different test_id to generate unique HKID
        test_id = base_test_id + iteration
        
        step = {
            "step": "Upload document {iteration} for HKID: {generate:hkid:main}",
            "detailed_step": {
                "action": "upload_file",
                "selector": "#file_upload",
                "file_path": "/app/test_files/passport_sample.jpg",
                "value": "{generate:hkid:main}"
            }
        }
        
        # Apply loop variable substitution
        step_desc = step["step"].replace("{iteration}", str(iteration))
        
        # Apply test data generation
        detailed_step = service._apply_test_data_generation(
            step["detailed_step"],
            test_id
        )
        step_desc = service._substitute_test_data_patterns(
            step_desc,
            test_id
        )
        
        results.append({
            "iteration": iteration,
            "step": step_desc,
            "hkid_main": detailed_step["value"]
        })
    
    # Verify each iteration has unique HKID
    hkids = [r["hkid_main"] for r in results]
    assert len(hkids) == len(set(hkids))  # All unique
    
    # Verify format
    for r in results:
        assert len(r["hkid_main"]) == 7
        assert r["hkid_main"][0].isalpha()
        assert r["hkid_main"][1:7].isdigit()
    
    print(f"\n✅ Loop with Test Data Test Passed:")
    for r in results:
        print(f"   Iteration {r['iteration']}: {r['step']}")
        print(f"      HKID Main: {r['hkid_main']}")


def test_consistency_across_test_execution():
    """
    Integration test: Verify consistency within a single test execution
    
    Multiple steps referencing same HKID should get consistent values
    """
    # Setup
    config = ExecutionConfig()
    service = ExecutionService(config)
    test_id = 200
    
    # Simulate test steps that reference HKID multiple times
    steps = [
        {"step": "Display: {generate:hkid}"},
        {"step": "Main part: {generate:hkid:main}"},
        {"step": "Check digit: {generate:hkid:check}"},
        {"step": "Full HKID again: {generate:hkid}"}
    ]
    
    # Process all steps
    results = []
    for step in steps:
        step_desc = service._substitute_test_data_patterns(
            step["step"],
            test_id
        )
        results.append(step_desc)
    
    # Extract values
    full_hkid_1 = results[0].replace("Display: ", "")
    main_part = results[1].replace("Main part: ", "")
    check_digit = results[2].replace("Check digit: ", "")
    full_hkid_2 = results[3].replace("Full HKID again: ", "")
    
    # Verify consistency
    assert full_hkid_1 == full_hkid_2  # Same full HKID
    assert full_hkid_1.startswith(main_part.replace("(", "")[:-1])  # Main matches
    assert full_hkid_1.endswith(f"({check_digit})")  # Check matches
    
    # Validate reconstructed HKID
    reconstructed = f"{main_part}({check_digit})"
    assert TestDataGenerator.validate_hkid(reconstructed)
    
    print(f"\n✅ Consistency Test Passed:")
    print(f"   Full HKID (1st): {full_hkid_1}")
    print(f"   Main part: {main_part}")
    print(f"   Check digit: {check_digit}")
    print(f"   Full HKID (2nd): {full_hkid_2}")
    print(f"   ✓ All values consistent from same cached HKID")


if __name__ == "__main__":
    # Run tests individually for clear output
    print("=" * 70)
    print("INTEGRATION TESTS: Test Data Generation in Execution Flow")
    print("=" * 70)
    
    test_split_hkid_execution_flow()
    test_multiple_data_types_execution_flow()
    test_loop_with_test_data_execution_flow()
    test_consistency_across_test_execution()
    
    print("\n" + "=" * 70)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 70)
