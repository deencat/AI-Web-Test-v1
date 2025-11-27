"""
Integration Test: Template → Scenario → Test → Execution
Tests the complete Day 7 + Sprint 3 integration flow
"""
import pytest
import requests
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Will be populated during tests
auth_token = None
user_id = None
template_id = None
scenario_id = None
test_case_id = None
execution_id = None


class TestTemplateToExecutionFlow:
    """Test the complete integration flow from template to execution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        global auth_token, user_id
        
        # Login
        response = requests.post(
            f"{API_V1}/auth/login",
            data={
                "username": "admin@example.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        auth_token = data["access_token"]
        user_id = data["user_id"]
        
        print(f"\n✓ Authenticated as user {user_id}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_01_list_templates(self):
        """Step 1: List available system templates"""
        global template_id
        
        response = requests.get(
            f"{API_V1}/test-templates",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        templates = response.json()
        assert len(templates) >= 6, "Should have at least 6 system templates"
        
        # Select REST API template
        api_template = next(
            (t for t in templates if t["name"] == "REST API Endpoint Test"),
            None
        )
        assert api_template is not None, "REST API template should exist"
        
        template_id = api_template["id"]
        print(f"✓ Found {len(templates)} templates, selected template {template_id}: {api_template['name']}")
    
    def test_02_generate_scenario(self):
        """Step 2: Generate test scenario from template"""
        global scenario_id
        
        response = requests.post(
            f"{API_V1}/scenarios/generate",
            headers=self.get_headers(),
            json={
                "template_id": template_id,
                "context_variables": {
                    "api_endpoint": "/api/v1/users",
                    "http_method": "GET",
                    "expected_status": 200
                },
                "use_faker_data": True
            }
        )
        assert response.status_code == 201, f"Scenario generation failed: {response.text}"
        
        scenario = response.json()
        scenario_id = scenario["id"]
        
        assert scenario["template_id"] == template_id
        assert scenario["status"] == "draft"
        assert len(scenario["steps"]) > 0
        assert scenario["test_data"] is not None  # Faker data should be generated
        
        print(f"✓ Generated scenario {scenario_id}: {scenario['name']}")
        print(f"  - Steps: {len(scenario['steps'])}")
        print(f"  - Test data fields: {list(scenario['test_data'].keys())}")
    
    def test_03_validate_scenario(self):
        """Step 3: Validate the generated scenario"""
        response = requests.post(
            f"{API_V1}/scenarios/{scenario_id}/validate",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        validation = response.json()
        assert validation["is_valid"] is True, f"Validation errors: {validation.get('errors')}"
        
        # Check scenario status updated to validated
        scenario_response = requests.get(
            f"{API_V1}/scenarios/{scenario_id}",
            headers=self.get_headers()
        )
        scenario = scenario_response.json()
        assert scenario["status"] == "validated"
        
        print(f"✓ Scenario validated successfully")
        if validation.get("warnings"):
            print(f"  - Warnings: {validation['warnings']}")
        if validation.get("suggestions"):
            print(f"  - Suggestions: {validation['suggestions']}")
    
    def test_04_convert_to_test(self):
        """Step 4: Convert validated scenario to executable test case"""
        global test_case_id
        
        response = requests.post(
            f"{API_V1}/scenarios/{scenario_id}/convert-to-test",
            headers=self.get_headers()
        )
        assert response.status_code == 201, f"Conversion failed: {response.text}"
        
        test_case = response.json()
        test_case_id = test_case["id"]
        
        # Verify test case has correct test_metadata
        assert test_case["test_metadata"] is not None
        assert test_case["test_metadata"]["generated_from_scenario"] == scenario_id
        assert test_case["test_metadata"]["template_id"] == template_id
        
        # Verify steps are Playwright-compatible
        assert isinstance(test_case["steps"], list)
        assert len(test_case["steps"]) > 0
        
        # Check if steps have proper structure
        for step in test_case["steps"]:
            if isinstance(step, dict):
                assert "action" in step or "description" in step
        
        print(f"✓ Converted to test case {test_case_id}: {test_case['title']}")
        print(f"  - Type: {test_case['test_type']}")
        print(f"  - Priority: {test_case['priority']}")
        print(f"  - Steps: {len(test_case['steps'])}")
        print(f"  - Tags: {test_case.get('tags', [])}")
    
    def test_05_execute_test(self):
        """Step 5: Execute the test case (Sprint 3 execution system)"""
        global execution_id
        
        # Note: This will queue the test for execution
        response = requests.post(
            f"{API_V1}/tests/{test_case_id}/run",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Execution failed: {response.text}"
        
        result = response.json()
        execution_id = result.get("execution_id")
        
        print(f"✓ Test queued for execution")
        print(f"  - Execution ID: {execution_id}")
        print(f"  - Status: {result.get('status')}")
        
        # Wait a bit for execution to start
        time.sleep(2)
        
        # Check execution status
        if execution_id:
            exec_response = requests.get(
                f"{API_V1}/executions/{execution_id}",
                headers=self.get_headers()
            )
            if exec_response.status_code == 200:
                execution = exec_response.json()
                print(f"  - Current status: {execution['status']}")
                if execution.get("result"):
                    print(f"  - Result: {execution['result']['status']}")
    
    def test_06_verify_complete_flow(self):
        """Step 6: Verify all components are linked"""
        # Get test case
        response = requests.get(
            f"{API_V1}/tests/{test_case_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        test_case = response.json()
        
        # Verify links
        assert test_case["test_metadata"]["generated_from_scenario"] == scenario_id
        assert test_case["test_metadata"]["template_id"] == template_id
        
        # Get scenario
        response = requests.get(
            f"{API_V1}/scenarios/{scenario_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        scenario = response.json()
        
        # Verify execution count incremented
        assert scenario["execution_count"] >= 1
        
        print(f"\n✓ COMPLETE FLOW VERIFIED:")
        print(f"  Template {template_id} → Scenario {scenario_id} → Test {test_case_id} → Execution {execution_id}")
        print(f"\n  Day 7 (Template/Scenario) + Sprint 3 (Execution) = INTEGRATED! 🎉")
    
    def test_07_batch_conversion(self):
        """Bonus: Test batch conversion"""
        # Generate 2 more scenarios
        scenario_ids = []
        
        for i in range(2):
            response = requests.post(
                f"{API_V1}/scenarios/generate",
                headers=self.get_headers(),
                json={
                    "template_id": template_id,
                    "context_variables": {
                        "api_endpoint": f"/api/v1/test{i}",
                        "http_method": "POST"
                    },
                    "use_faker_data": True
                }
            )
            if response.status_code == 201:
                scenario = response.json()
                
                # Validate
                val_response = requests.post(
                    f"{API_V1}/scenarios/{scenario['id']}/validate",
                    headers=self.get_headers()
                )
                if val_response.status_code == 200:
                    scenario_ids.append(scenario["id"])
        
        if len(scenario_ids) >= 2:
            # Batch convert
            response = requests.post(
                f"{API_V1}/scenarios/batch-convert",
                headers=self.get_headers(),
                json=scenario_ids
            )
            assert response.status_code == 201
            
            test_cases = response.json()
            assert len(test_cases) == 2
            
            print(f"\n✓ Batch conversion successful: {len(test_cases)} test cases created")


def test_faker_data_integration():
    """Test that Faker data is properly integrated"""
    response = requests.get(
        f"{API_V1}/scenarios/faker-fields",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    fields = response.json()["available_fields"]
    assert len(fields) >= 40, "Should have at least 40 Faker fields"
    
    # Verify key categories
    categories = {field.split(".")[0] for field in fields}
    assert "user" in categories
    assert "address" in categories
    assert "product" in categories
    assert "company" in categories
    
    print(f"\n✓ Faker integration: {len(fields)} fields across {len(categories)} categories")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("INTEGRATION TEST: Template → Scenario → Test → Execution")
    print("Testing Day 7 (Template/Scenario) + Sprint 3 (Execution) Integration")
    print("="*80)
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
