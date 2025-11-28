"""
Scenario to Test Converter Service
Converts AI-generated TestScenario to executable TestCase for Sprint 3 execution
"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.test_scenario import TestScenario
from app.models.test_case import TestCase, TestType, Priority
from app.schemas.test_case import TestCaseCreate
from app.crud import test_case as crud_tests


class ScenarioConverter:
    """Convert TestScenario (Day 7) to executable TestCase (Sprint 3)"""
    
    @staticmethod
    def convert_scenario_to_test(
        scenario: TestScenario,
        user_id: int,
        db: Session
    ) -> TestCase:
        """
        Convert generated scenario to executable test case.
        
        This bridges the template/scenario system (Day 7) with
        the execution system (Sprint 3).
        
        Args:
            scenario: TestScenario with AI-generated steps
            user_id: User creating the test
            db: Database session
            
        Returns:
            TestCase ready for execution with Playwright/Stagehand
        """
        # Map scenario steps to Playwright actions
        playwright_steps = ScenarioConverter._map_steps_to_playwright(scenario.steps)
        
        # Determine test type from template
        test_type = ScenarioConverter._get_test_type(scenario)
        
        # Extract category from template (may be None)
        try:
            category_id = scenario.template.category_id if scenario.template else None
        except Exception as e:
            print(f"Warning: Could not get category_id from template: {e}")
            category_id = None
        
        # Build test case data
        test_data = TestCaseCreate(
            title=scenario.name,
            description=f"{scenario.description}\n\n[Generated from template: {scenario.template.name if scenario.template else 'N/A'}]",
            category_id=category_id,
            test_type=test_type,
            priority=Priority.MEDIUM,  # Default, can be customized
            steps=playwright_steps,
            expected_result=scenario.expected_results.get("summary", "Test should pass") if scenario.expected_results else "Test should pass",
            tags=["generated", f"template:{scenario.template_id}"] if scenario.template_id else ["generated"],
            test_metadata={
                "generated_from_scenario": scenario.id,
                "template_id": scenario.template_id,
                "template_name": scenario.template.name if scenario.template else None,
                "faker_data": scenario.test_data,
                "original_dependencies": scenario.dependencies,
                "generated_at": str(scenario.created_at)
            }
        )
        
        # Create test case using existing CRUD
        test_case = crud_tests.create_test_case(db, test_data, user_id)
        
        # Set scenario and template IDs (foreign keys)
        test_case.scenario_id = scenario.id
        test_case.template_id = scenario.template_id
        db.commit()
        db.refresh(test_case)
        
        return test_case
    
    @staticmethod
    def _map_steps_to_playwright(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert scenario steps to Playwright-compatible format.
        
        Maps Day 7 scenario step structure to Sprint 3 execution format.
        """
        playwright_steps = []
        
        for i, step in enumerate(steps):
            action = step.get("action", "")
            
            # Map different action types to Playwright commands
            pw_step = {
                "step_number": i + 1,
                "description": step.get("description", f"Step {i + 1}"),
            }
            
            if action == "navigate":
                pw_step.update({
                    "action": "navigate",
                    "url": step.get("url") or step.get("target"),
                    "wait_for": "networkidle"
                })
            
            elif action in ["click", "click_button"]:
                pw_step.update({
                    "action": "click",
                    "selector": step.get("selector") or step.get("target"),
                    "description": step.get("description", f"Click on {step.get('target')}")
                })
            
            elif action in ["fill", "fill_field", "type"]:
                pw_step.update({
                    "action": "fill",
                    "selector": step.get("selector") or step.get("target"),
                    "value": step.get("value") or step.get("data"),
                    "description": step.get("description", f"Fill {step.get('target')}")
                })
            
            elif action == "assert_element":
                pw_step.update({
                    "action": "assert_visible",
                    "selector": step.get("selector") or step.get("target"),
                    "description": step.get("description", f"Verify {step.get('target')} is visible")
                })
            
            elif action == "wait_for_navigation":
                pw_step.update({
                    "action": "wait_for_url",
                    "url_pattern": step.get("expected_url") or step.get("url"),
                    "description": step.get("description", "Wait for navigation")
                })
            
            elif action in ["request", "api_call"]:
                # API test step
                pw_step.update({
                    "action": "api_request",
                    "method": step.get("method", "GET"),
                    "endpoint": step.get("endpoint") or step.get("url"),
                    "headers": step.get("headers", {}),
                    "body": step.get("body") or step.get("data"),
                    "description": step.get("description", f"{step.get('method', 'GET')} request")
                })
            
            elif action == "assert_response":
                pw_step.update({
                    "action": "assert_status",
                    "expected_status": step.get("status_code") or step.get("expected_status"),
                    "response_schema": step.get("response_schema"),
                    "description": step.get("description", "Verify response")
                })
            
            else:
                # Generic step
                pw_step.update({
                    "action": action,
                    "target": step.get("target"),
                    "value": step.get("value") or step.get("data"),
                    "assertion": step.get("assertion")
                })
            
            # Add any additional fields
            if "wait_time" in step:
                pw_step["wait_time"] = step["wait_time"]
            
            if "screenshot" in step:
                pw_step["take_screenshot"] = step["screenshot"]
            
            playwright_steps.append(pw_step)
        
        return playwright_steps
    
    @staticmethod
    def _get_test_type(scenario: TestScenario) -> TestType:
        """Determine test type from scenario template"""
        if not scenario.template:
            return TestType.E2E
        
        template_type = scenario.template.template_type.lower()
        
        type_mapping = {
            "api": TestType.API,
            "e2e": TestType.E2E,
            "mobile": TestType.E2E,  # Map mobile to E2E
            "performance": TestType.E2E,  # Map performance to E2E
            "ui": TestType.E2E
        }
        
        return type_mapping.get(template_type, TestType.E2E)
    
    @staticmethod
    def batch_convert_scenarios(
        scenario_ids: List[int],
        user_id: int,
        db: Session
    ) -> List[TestCase]:
        """
        Convert multiple scenarios to test cases.
        
        Useful for batch generation workflows.
        """
        from app.crud import test_scenario as crud_scenarios
        
        test_cases = []
        
        for scenario_id in scenario_ids:
            scenario = crud_scenarios.get_scenario(db, scenario_id)
            if scenario and scenario.status == "validated":
                test_case = ScenarioConverter.convert_scenario_to_test(
                    scenario, user_id, db
                )
                test_cases.append(test_case)
        
        return test_cases
