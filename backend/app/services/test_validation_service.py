"""
Test Validation Service
Validates test scenarios before execution
"""
from typing import List, Tuple, Optional
from app.models.test_scenario import TestScenario


class TestValidationService:
    """Service for validating test scenarios"""
    
    @staticmethod
    def validate_scenario(scenario: TestScenario) -> Tuple[bool, List[str], List[str]]:
        """
        Comprehensive scenario validation
        
        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check basic fields
        if not scenario.name:
            errors.append("Scenario name is required")
        
        if not scenario.steps or len(scenario.steps) == 0:
            errors.append("Scenario must have at least one step")
            return (False, errors, warnings)
        
        # Validate each step
        for i, step in enumerate(scenario.steps):
            step_errors = TestValidationService.check_step_completeness(step, i)
            errors.extend(step_errors)
        
        # Check dependencies
        if scenario.dependencies:
            dep_errors = TestValidationService.validate_dependencies(
                scenario.steps,
                scenario.dependencies
            )
            errors.extend(dep_errors)
        
        # Check expected results
        if not scenario.expected_results or len(scenario.expected_results) == 0:
            warnings.append("No expected results defined")
        
        # Check test data
        if not scenario.test_data or len(scenario.test_data) == 0:
            warnings.append("No test data defined")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    @staticmethod
    def check_step_completeness(step: dict, step_index: int) -> List[str]:
        """
        Validate individual step structure
        
        A valid step should have:
        - action: The action to perform
        - Additional fields depend on action type
        """
        errors = []
        
        if not isinstance(step, dict):
            errors.append(f"Step {step_index}: Must be an object")
            return errors
        
        # Check required 'action' field
        if 'action' not in step:
            errors.append(f"Step {step_index}: Missing 'action' field")
            return errors
        
        action = step['action']
        
        # Validate based on action type
        if action == "navigate":
            if 'url' not in step:
                errors.append(f"Step {step_index}: 'navigate' action requires 'url' field")
        
        elif action == "click":
            if 'selector' not in step and 'target' not in step:
                errors.append(f"Step {step_index}: 'click' action requires 'selector' or 'target' field")
        
        elif action == "fill" or action == "fill_field":
            if 'selector' not in step and 'field' not in step:
                errors.append(f"Step {step_index}: 'fill' action requires 'selector' or 'field'")
            if 'value' not in step:
                errors.append(f"Step {step_index}: 'fill' action requires 'value' field")
        
        elif action == "assert" or action == "assert_element":
            if 'selector' not in step and 'target' not in step:
                errors.append(f"Step {step_index}: 'assert' action requires 'selector' or 'target'")
        
        elif action == "wait":
            if 'timeout' not in step and 'condition' not in step:
                errors.append(f"Step {step_index}: 'wait' action requires 'timeout' or 'condition'")
        
        elif action == "request":
            if 'method' not in step:
                errors.append(f"Step {step_index}: 'request' action requires 'method' field")
            if 'endpoint' not in step and 'url' not in step:
                errors.append(f"Step {step_index}: 'request' action requires 'endpoint' or 'url' field")
        
        elif action == "assert_response":
            if 'status_code' not in step:
                warnings = [f"Step {step_index}: 'assert_response' should have 'status_code' field"]
        
        return errors
    
    @staticmethod
    def validate_dependencies(steps: List[dict], dependencies: List[dict]) -> List[str]:
        """
        Check for circular dependencies and missing prerequisites
        
        dependencies format:
        [
            {"step_index": 2, "depends_on": [0, 1]},
            {"step_index": 3, "depends_on": [2]}
        ]
        """
        errors = []
        total_steps = len(steps)
        
        # Build dependency graph
        dep_graph = {}
        for dep in dependencies:
            if not isinstance(dep, dict):
                errors.append("Invalid dependency format: must be object")
                continue
            
            if 'step_index' not in dep or 'depends_on' not in dep:
                errors.append("Dependency missing 'step_index' or 'depends_on' field")
                continue
            
            step_idx = dep['step_index']
            depends_on = dep['depends_on']
            
            # Validate indices
            if step_idx < 0 or step_idx >= total_steps:
                errors.append(f"Invalid step_index: {step_idx}")
                continue
            
            if not isinstance(depends_on, list):
                errors.append(f"Step {step_idx}: 'depends_on' must be an array")
                continue
            
            for dep_idx in depends_on:
                if dep_idx < 0 or dep_idx >= total_steps:
                    errors.append(f"Step {step_idx}: Invalid dependency index {dep_idx}")
                elif dep_idx >= step_idx:
                    errors.append(f"Step {step_idx}: Cannot depend on later step {dep_idx}")
            
            dep_graph[step_idx] = depends_on
        
        # Check for circular dependencies using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            if node in dep_graph:
                for neighbor in dep_graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for step_idx in dep_graph.keys():
            if step_idx not in visited:
                if has_cycle(step_idx):
                    errors.append(f"Circular dependency detected involving step {step_idx}")
        
        return errors
    
    @staticmethod
    def suggest_improvements(scenario: TestScenario) -> List[str]:
        """
        AI suggestions to improve test coverage
        Currently basic suggestions, can be enhanced with AI later
        """
        suggestions = []
        
        # Check if there are assertions
        has_assertions = any(
            step.get('action', '').startswith('assert')
            for step in scenario.steps
        )
        if not has_assertions:
            suggestions.append("Add assertion steps to verify expected behavior")
        
        # Check for error handling
        has_error_handling = any(
            'on_error' in step or 'catch' in step
            for step in scenario.steps
        )
        if not has_error_handling:
            suggestions.append("Consider adding error handling steps")
        
        # Check for cleanup steps
        has_cleanup = any(
            'cleanup' in step.get('action', '').lower()
            for step in scenario.steps
        )
        if len(scenario.steps) > 5 and not has_cleanup:
            suggestions.append("Consider adding cleanup steps for test data")
        
        # Check for wait steps before assertions
        for i, step in enumerate(scenario.steps):
            if step.get('action', '').startswith('assert'):
                if i > 0:
                    prev_step = scenario.steps[i-1]
                    if 'wait' not in prev_step.get('action', ''):
                        suggestions.append(f"Consider adding wait before assertion at step {i}")
        
        # Check for descriptive step names
        for i, step in enumerate(scenario.steps):
            if 'description' not in step and 'name' not in step:
                suggestions.append(f"Add description to step {i} for better readability")
        
        return suggestions
    
    @staticmethod
    def validate_scenario_json(scenario_data: dict) -> Tuple[bool, List[str]]:
        """
        Validate scenario JSON structure before creating scenario object
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['name', 'steps']
        for field in required_fields:
            if field not in scenario_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        if 'steps' in scenario_data:
            if not isinstance(scenario_data['steps'], list):
                errors.append("'steps' must be an array")
            elif len(scenario_data['steps']) == 0:
                errors.append("'steps' cannot be empty")
            else:
                # Validate each step
                for i, step in enumerate(scenario_data['steps']):
                    step_errors = TestValidationService.check_step_completeness(step, i)
                    errors.extend(step_errors)
        
        # Validate dependencies if present
        if 'dependencies' in scenario_data:
            if not isinstance(scenario_data['dependencies'], list):
                errors.append("'dependencies' must be an array")
            elif 'steps' in scenario_data:
                dep_errors = TestValidationService.validate_dependencies(
                    scenario_data['steps'],
                    scenario_data['dependencies']
                )
                errors.extend(dep_errors)
        
        return (len(errors) == 0, errors)
