"""
Day 7 Test Generation Engine - Automated Test Script
Tests all Day 7 features: Templates, Scenarios, Faker, and Validation
"""
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime


class Day7TestRunner:
    """Automated test runner for Day 7 features"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.created_template_id: Optional[int] = None
        self.created_scenario_id: Optional[int] = None
    
    def print_header(self, title: str):
        """Print a formatted test section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {name}")
        if details:
            print(f"        {details}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{name}: {details}")
    
    def login(self) -> bool:
        """Login and get access token"""
        self.print_header("STEP 1: Authentication")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={
                    "username": "admin",
                    "password": "admin123"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                self.print_test("Login", True, f"Token received: {self.token[:20]}...")
                return True
            else:
                self.print_test("Login", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_test("Login", False, str(e))
            return False
    
    def test_view_templates(self) -> bool:
        """Test viewing all templates"""
        self.print_header("STEP 2: View Templates")
        
        try:
            response = requests.get(
                f"{self.base_url}/test-templates/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                templates = data.get("templates", [])
                
                self.print_test("Get all templates", True, f"Found {total} templates")
                
                # List template names
                if templates:
                    print("\n    Available Templates:")
                    for t in templates[:6]:  # Show first 6
                        print(f"      - {t['name']} (ID: {t['id']}, Type: {t['template_type']})")
                
                return total > 0
            else:
                self.print_test("Get all templates", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Get all templates", False, str(e))
            return False
    
    def test_faker_fields(self) -> bool:
        """Test getting Faker fields"""
        self.print_header("STEP 3: Faker Fields")
        
        try:
            response = requests.get(
                f"{self.base_url}/scenarios/faker-fields",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                categories = list(fields.keys())
                total_fields = sum(len(v) for v in fields.values())
                
                self.print_test("Get Faker fields", True, 
                              f"Found {len(categories)} categories with {total_fields} total fields")
                
                # Show categories
                print("\n    Categories:")
                for cat, field_list in fields.items():
                    print(f"      - {cat}: {len(field_list)} fields")
                    if field_list:
                        print(f"        Examples: {', '.join(field_list[:3])}")
                
                return len(categories) > 0
            else:
                self.print_test("Get Faker fields", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Get Faker fields", False, str(e))
            return False
    
    def test_generate_faker_data(self) -> bool:
        """Test generating Faker data"""
        self.print_header("STEP 4: Generate Faker Data")
        
        try:
            test_data_req = {
                "data_requirements": {
                    "user": ["email", "name", "phone"],
                    "address": ["street", "city", "country"],
                    "product": ["name", "price"]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/scenarios/generate-data",
                headers=self.headers,
                json=test_data_req
            )
            
            if response.status_code == 200:
                data = response.json()
                generated = data.get("data", {})
                
                self.print_test("Generate Faker data", True, 
                              f"Generated data for {len(generated)} categories")
                
                # Show sample data
                print("\n    Generated Sample Data:")
                for category, fields in generated.items():
                    print(f"      {category}:")
                    for field_name, value in fields.items():
                        print(f"        - {field_name}: {value}")
                
                return len(generated) > 0
            else:
                self.print_test("Generate Faker data", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Generate Faker data", False, str(e))
            return False
    
    def test_create_template(self) -> bool:
        """Test creating a custom template"""
        self.print_header("STEP 5: Create Custom Template")
        
        try:
            template_data = {
                "name": f"Test Template - {datetime.now().strftime('%H:%M:%S')}",
                "description": "Automated test template for checkout flow",
                "template_type": "e2e",
                "category_id": 1,
                "steps_template": [
                    {
                        "step_number": 1,
                        "action": "navigate",
                        "target": "${base_url}/products",
                        "description": "Navigate to products page"
                    },
                    {
                        "step_number": 2,
                        "action": "click",
                        "target": ".product-card:first-child .add-to-cart",
                        "description": "Add first product to cart"
                    },
                    {
                        "step_number": 3,
                        "action": "navigate",
                        "target": "${base_url}/checkout",
                        "description": "Go to checkout"
                    },
                    {
                        "step_number": 4,
                        "action": "fill",
                        "target": "#email",
                        "value": "${user.email}",
                        "description": "Enter email"
                    },
                    {
                        "step_number": 5,
                        "action": "fill",
                        "target": "#address",
                        "value": "${address.street}",
                        "description": "Enter address"
                    }
                ],
                "assertion_template": {
                    "type": "url_contains",
                    "expected": "/order-confirmation",
                    "message": "Should redirect to order confirmation"
                },
                "data_requirements": {
                    "base_url": ["url"],
                    "user": ["email", "name"],
                    "address": ["street", "city", "zip"]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/test-templates/",
                headers=self.headers,
                json=template_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.created_template_id = data.get("id")
                
                self.print_test("Create template", True, 
                              f"Template created with ID: {self.created_template_id}")
                print(f"        Name: {data.get('name')}")
                print(f"        Type: {data.get('template_type')}")
                print(f"        Steps: {len(data.get('steps_template', []))}")
                
                return True
            else:
                self.print_test("Create template", False, 
                              f"Status {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_test("Create template", False, str(e))
            return False
    
    def test_generate_scenario(self) -> bool:
        """Test generating scenario from template"""
        self.print_header("STEP 6: Generate Scenario from Template")
        
        if not self.created_template_id:
            self.print_test("Generate scenario", False, "No template ID available")
            return False
        
        try:
            scenario_req = {
                "template_id": self.created_template_id,
                "context": {
                    "base_url": "https://demo-shop.example.com",
                    "test_name": "Checkout Flow Test"
                },
                "use_ai": False,
                "generate_data": True
            }
            
            response = requests.post(
                f"{self.base_url}/scenarios/generate",
                headers=self.headers,
                json=scenario_req
            )
            
            if response.status_code == 201:
                data = response.json()
                self.created_scenario_id = data.get("id")
                
                self.print_test("Generate scenario", True, 
                              f"Scenario created with ID: {self.created_scenario_id}")
                print(f"        Name: {data.get('name')}")
                print(f"        Status: {data.get('status')}")
                print(f"        Steps: {len(data.get('steps', []))}")
                
                # Show first step with expanded variables
                steps = data.get('steps', [])
                if steps:
                    print(f"\n        First Step (expanded):")
                    first_step = steps[0]
                    print(f"          Action: {first_step.get('action')}")
                    print(f"          Target: {first_step.get('target')}")
                
                return True
            else:
                self.print_test("Generate scenario", False, 
                              f"Status {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_test("Generate scenario", False, str(e))
            return False
    
    def test_validate_scenario(self) -> bool:
        """Test scenario validation"""
        self.print_header("STEP 7: Validate Scenario")
        
        if not self.created_scenario_id:
            self.print_test("Validate scenario", False, "No scenario ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/scenarios/{self.created_scenario_id}/validate",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("is_valid", False)
                errors = data.get("errors", [])
                warnings = data.get("warnings", [])
                suggestions = data.get("suggestions", [])
                
                self.print_test("Validate scenario", True, 
                              f"Valid: {is_valid}, Errors: {len(errors)}, Warnings: {len(warnings)}")
                
                if errors:
                    print(f"\n        Errors:")
                    for err in errors[:3]:
                        print(f"          - {err}")
                
                if warnings:
                    print(f"\n        Warnings:")
                    for warn in warnings[:3]:
                        print(f"          - {warn}")
                
                if suggestions:
                    print(f"\n        Suggestions:")
                    for sug in suggestions[:3]:
                        print(f"          - {sug}")
                
                return True
            else:
                self.print_test("Validate scenario", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Validate scenario", False, str(e))
            return False
    
    def test_template_statistics(self) -> bool:
        """Test template statistics"""
        self.print_header("STEP 8: Template Statistics")
        
        try:
            # Test popular templates
            response = requests.get(
                f"{self.base_url}/test-templates/popular",
                headers=self.headers,
                params={"limit": 5}
            )
            
            if response.status_code == 200:
                templates = response.json()  # Direct list response
                
                self.print_test("Get popular templates", True, 
                              f"Found {len(templates)} popular templates")
                
                if templates:
                    print("\n        Top Templates by Usage:")
                    for t in templates[:3]:
                        print(f"          - {t['name']}: {t.get('usage_count', 0)} uses")
                
            else:
                self.print_test("Get popular templates", False, f"Status {response.status_code}")
                return False
            
            # Test best templates
            response = requests.get(
                f"{self.base_url}/test-templates/best",
                headers=self.headers,
                params={"limit": 5}
            )
            
            if response.status_code == 200:
                templates = response.json()  # Direct list response
                
                self.print_test("Get best templates", True, 
                              f"Found {len(templates)} high-performing templates")
                
                if templates:
                    print("\n        Top Templates by Success Rate:")
                    for t in templates[:3]:
                        print(f"          - {t['name']}: {t.get('success_rate', 0):.1%} success")
                
                return True
            else:
                self.print_test("Get best templates", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Template statistics", False, str(e))
            return False
    
    def test_batch_generation(self) -> bool:
        """Test batch scenario generation"""
        self.print_header("STEP 9: Batch Scenario Generation")
        
        if not self.created_template_id:
            self.print_test("Batch generation", False, "No template ID available")
            return False
        
        try:
            batch_req = {
                "template_ids": [self.created_template_id],
                "base_context": {
                    "base_url": "https://demo-shop.example.com"
                },
                "variations": [
                    {"variation_name": "Chrome Desktop"},
                    {"variation_name": "Firefox Desktop"},
                    {"variation_name": "Safari Mobile"}
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/scenarios/batch-generate",
                headers=self.headers,
                json=batch_req
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_requested", 0)
                generated = data.get("generated", 0)
                failed = data.get("failed", 0)
                
                self.print_test("Batch generation", True, 
                              f"Generated {generated}/{total} scenarios ({failed} failed)")
                
                scenarios = data.get("scenarios", [])
                if scenarios:
                    print(f"\n        Generated Scenarios:")
                    for s in scenarios[:3]:
                        print(f"          - {s.get('name')} (ID: {s.get('id')})")
                
                return generated > 0
            else:
                self.print_test("Batch generation", False, 
                              f"Status {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_test("Batch generation", False, str(e))
            return False
    
    def test_template_filtering(self) -> bool:
        """Test template filtering"""
        self.print_header("STEP 10: Template Filtering")
        
        try:
            # Filter by type
            response = requests.get(
                f"{self.base_url}/test-templates/type/e2e",
                headers=self.headers
            )
            
            if response.status_code == 200:
                templates = response.json()  # Direct list response
                
                self.print_test("Filter templates by type (e2e)", True, 
                              f"Found {len(templates)} E2E templates")
                
                return True
            else:
                self.print_test("Filter templates", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Filter templates", False, str(e))
            return False
    
    def test_clone_template(self) -> bool:
        """Test cloning a template"""
        self.print_header("STEP 11: Clone Template")
        
        if not self.created_template_id:
            self.print_test("Clone template", False, "No template ID available")
            return False
        
        try:
            clone_req = {
                "new_name": f"Cloned Template - {datetime.now().strftime('%H:%M:%S')}"
            }
            
            response = requests.post(
                f"{self.base_url}/test-templates/{self.created_template_id}/clone",
                headers=self.headers,
                json=clone_req
            )
            
            if response.status_code == 201:
                data = response.json()
                cloned_id = data.get("id")
                
                self.print_test("Clone template", True, 
                              f"Template cloned with new ID: {cloned_id}")
                print(f"        Original: {self.created_template_id}")
                print(f"        Clone: {cloned_id}")
                print(f"        New Name: {data.get('name')}")
                
                return True
            else:
                self.print_test("Clone template", False, 
                              f"Status {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_test("Clone template", False, str(e))
            return False
    
    def test_update_scenario(self) -> bool:
        """Test updating a scenario"""
        self.print_header("STEP 12: Update Scenario")
        
        if not self.created_scenario_id:
            self.print_test("Update scenario", False, "No scenario ID available")
            return False
        
        try:
            update_data = {
                "description": "Updated description - automated test"
            }
            
            response = requests.put(
                f"{self.base_url}/scenarios/{self.created_scenario_id}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_test("Update scenario", True, 
                              f"Scenario {self.created_scenario_id} updated")
                print(f"        Description: {data.get('description')}")
                
                return True
            else:
                self.print_test("Update scenario", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Update scenario", False, str(e))
            return False
    
    def cleanup(self):
        """Clean up created test data"""
        self.print_header("CLEANUP")
        
        # Delete created scenario
        if self.created_scenario_id:
            try:
                response = requests.delete(
                    f"{self.base_url}/scenarios/{self.created_scenario_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    print(f"✅ Deleted scenario {self.created_scenario_id}")
                else:
                    print(f"⚠️  Could not delete scenario {self.created_scenario_id}")
            except Exception as e:
                print(f"⚠️  Error deleting scenario: {e}")
        
        # Delete created template (will cascade delete scenarios)
        if self.created_template_id:
            try:
                response = requests.delete(
                    f"{self.base_url}/test-templates/{self.created_template_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    print(f"✅ Deleted template {self.created_template_id}")
                else:
                    print(f"⚠️  Could not delete template {self.created_template_id}")
            except Exception as e:
                print(f"⚠️  Error deleting template: {e}")
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n  Total Tests: {total}")
        print(f"  ✅ Passed: {self.test_results['passed']}")
        print(f"  ❌ Failed: {self.test_results['failed']}")
        print(f"  Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            print(f"\n  Failed Tests:")
            for error in self.test_results["errors"]:
                print(f"    - {error}")
        
        print("\n" + "="*70)
        
        if self.test_results["failed"] == 0:
            print("  🎉 ALL TESTS PASSED! Day 7 is working perfectly!")
        else:
            print(f"  ⚠️  {self.test_results['failed']} test(s) need attention")
        
        print("="*70 + "\n")
        
        return self.test_results["failed"] == 0
    
    def run_all_tests(self):
        """Run all Day 7 tests"""
        print("\n" + "="*70)
        print("  DAY 7 TEST GENERATION ENGINE - AUTOMATED TESTS")
        print("  Testing: Templates, Scenarios, Faker, Validation")
        print("="*70)
        
        # Run tests in sequence
        if not self.login():
            print("\n❌ Login failed. Cannot continue tests.")
            return False
        
        self.test_view_templates()
        self.test_faker_fields()
        self.test_generate_faker_data()
        self.test_create_template()
        self.test_generate_scenario()
        self.test_validate_scenario()
        self.test_template_statistics()
        self.test_batch_generation()
        self.test_template_filtering()
        self.test_clone_template()
        self.test_update_scenario()
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        return self.print_summary()


def main():
    """Main entry point"""
    runner = Day7TestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
