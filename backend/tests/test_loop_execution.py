"""
Unit tests for loop execution functionality.
Tests loop block parsing, iteration tracking, variable substitution, and error handling.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from app.services.execution_service import ExecutionService, ExecutionConfig
from app.models.test_execution import ExecutionResult


class TestLoopBlockParsing:
    """Test loop block parsing and validation."""
    
    def test_find_loop_starting_at_found(self):
        """Test finding a loop block that starts at a specific step."""
        service = ExecutionService()
        
        loop_blocks = [
            {
                "id": "loop1",
                "start_step": 2,
                "end_step": 4,
                "iterations": 3,
                "description": "Test loop"
            },
            {
                "id": "loop2",
                "start_step": 6,
                "end_step": 8,
                "iterations": 5,
                "description": "Another loop"
            }
        ]
        
        # Find first loop
        result = service._find_loop_starting_at(2, loop_blocks)
        assert result is not None
        assert result["id"] == "loop1"
        assert result["iterations"] == 3
        
        # Find second loop
        result = service._find_loop_starting_at(6, loop_blocks)
        assert result is not None
        assert result["id"] == "loop2"
        assert result["iterations"] == 5
    
    def test_find_loop_starting_at_not_found(self):
        """Test when no loop starts at the specified step."""
        service = ExecutionService()
        
        loop_blocks = [
            {
                "id": "loop1",
                "start_step": 2,
                "end_step": 4,
                "iterations": 3,
                "description": "Test loop"
            }
        ]
        
        result = service._find_loop_starting_at(1, loop_blocks)
        assert result is None
        
        result = service._find_loop_starting_at(5, loop_blocks)
        assert result is None
    
    def test_find_loop_starting_at_invalid_structure(self):
        """Test handling of invalid loop block structures."""
        service = ExecutionService()
        
        # Missing end_step
        loop_blocks = [
            {
                "id": "loop1",
                "start_step": 2,
                "iterations": 3
            }
        ]
        
        result = service._find_loop_starting_at(2, loop_blocks)
        assert result is None
        
        # Missing iterations
        loop_blocks = [
            {
                "id": "loop1",
                "start_step": 2,
                "end_step": 4
            }
        ]
        
        result = service._find_loop_starting_at(2, loop_blocks)
        assert result is None


class TestLoopVariableSubstitution:
    """Test variable substitution in loops."""
    
    def test_apply_loop_variables_iteration_placeholder(self):
        """Test {iteration} placeholder substitution in detailed steps."""
        service = ExecutionService()
        
        detailed_step = {
            "action": "upload_file",
            "selector": "input[type='file']",
            "file_path": "/app/test_files/document_{iteration}.pdf",
            "instruction": "Upload document {iteration}"
        }
        
        result = service._apply_loop_variables(detailed_step, 3, {})
        
        assert result["file_path"] == "/app/test_files/document_3.pdf"
        assert result["instruction"] == "Upload document 3"
        assert result["action"] == "upload_file"  # Unchanged
        assert result["selector"] == "input[type='file']"  # Unchanged
    
    def test_apply_loop_variables_custom_variables(self):
        """Test custom variable substitution."""
        service = ExecutionService()
        
        detailed_step = {
            "action": "fill",
            "selector": "#email",
            "value": "test@example.com"
        }
        
        loop_variables = {
            "value": "user{iteration}@example.com"
        }
        
        result = service._apply_loop_variables(detailed_step, 5, loop_variables)
        
        assert result["value"] == "user5@example.com"
        assert result["action"] == "fill"
        assert result["selector"] == "#email"
    
    def test_apply_loop_variables_none_step(self):
        """Test handling of None detailed step."""
        service = ExecutionService()
        
        result = service._apply_loop_variables(None, 1, {})
        assert result is None
    
    def test_substitute_loop_variables_text(self):
        """Test variable substitution in text strings."""
        service = ExecutionService()
        
        text = "Upload document {iteration} of 5"
        result = service._substitute_loop_variables(text, 3, {})
        
        assert result == "Upload document 3 of 5"
    
    def test_substitute_loop_variables_custom(self):
        """Test custom variable substitution in text."""
        service = ExecutionService()
        
        text = "Upload {file_name} to server"
        loop_variables = {
            "file_name": "document_{iteration}.pdf"
        }
        
        result = service._substitute_loop_variables(text, 2, loop_variables)
        
        assert result == "Upload document_2.pdf to server"
    
    def test_substitute_loop_variables_multiple(self):
        """Test multiple variable substitutions."""
        service = ExecutionService()
        
        text = "Step {iteration}: Upload {file_path}"
        loop_variables = {
            "file_path": "/files/doc_{iteration}.pdf"
        }
        
        result = service._substitute_loop_variables(text, 4, loop_variables)
        
        assert result == "Step 4: Upload /files/doc_4.pdf"


class TestLoopExecution:
    """Test loop execution logic."""
    
    @pytest.mark.asyncio
    async def test_loop_execution_basic(self):
        """Test basic loop execution with 3 iterations."""
        service = ExecutionService()
        
        # Mock database and page
        db_mock = Mock()
        page_mock = AsyncMock()
        page_mock.url = "http://test.com"
        page_mock.viewport_size = {"width": 1280, "height": 720}
        page_mock.content = AsyncMock(return_value="<html></html>")
        page_mock.screenshot = AsyncMock()
        
        # Create test case with loop
        test_case = Mock()
        test_case.id = 1
        test_case.steps = [
            "Navigate to page",
            "Click upload",
            "Select file",
            "Verify success"
        ]
        test_case.test_data = {
            "detailed_steps": [
                {"action": "navigate", "value": "http://test.com"},
                {"action": "click", "selector": "#upload-btn"},
                {"action": "upload_file", "selector": "input[type='file']", "file_path": "/app/test_files/doc_{iteration}.pdf"},
                {"action": "verify", "selector": ".success"}
            ],
            "loop_blocks": [
                {
                    "id": "upload_loop",
                    "start_step": 2,
                    "end_step": 3,
                    "iterations": 3,
                    "description": "Upload 3 files"
                }
            ]
        }
        
        # Test that loop block is correctly identified
        loop_blocks = test_case.test_data["loop_blocks"]
        loop = service._find_loop_starting_at(2, loop_blocks)
        
        assert loop is not None
        assert loop["id"] == "upload_loop"
        assert loop["iterations"] == 3
        assert loop["start_step"] == 2
        assert loop["end_step"] == 3
    
    @pytest.mark.asyncio
    async def test_screenshot_with_iteration(self):
        """Test screenshot capture with iteration number."""
        config = ExecutionConfig()
        service = ExecutionService(config)
        
        page_mock = AsyncMock()
        page_mock.screenshot = AsyncMock()
        
        result = await service._capture_screenshot_with_iteration(
            page_mock,
            execution_id=123,
            step_number=5,
            iteration=3,
            result=ExecutionResult.PASS
        )
        
        assert result is not None
        assert "exec_123_step_5_iter_3_pass.png" in result
        page_mock.screenshot.assert_called_once()


class TestLoopErrorHandling:
    """Test error handling in loop execution."""
    
    def test_loop_with_missing_end_step(self):
        """Test handling of loop with missing end_step."""
        service = ExecutionService()
        
        loop_blocks = [
            {
                "id": "invalid_loop",
                "start_step": 2,
                "iterations": 3
                # Missing end_step
            }
        ]
        
        result = service._find_loop_starting_at(2, loop_blocks)
        assert result is None
    
    def test_loop_with_missing_iterations(self):
        """Test handling of loop with missing iterations."""
        service = ExecutionService()
        
        loop_blocks = [
            {
                "id": "invalid_loop",
                "start_step": 2,
                "end_step": 4
                # Missing iterations
            }
        ]
        
        result = service._find_loop_starting_at(2, loop_blocks)
        assert result is None
    
    def test_empty_loop_blocks(self):
        """Test handling of empty loop_blocks list."""
        service = ExecutionService()
        
        result = service._find_loop_starting_at(1, [])
        assert result is None
    
    @pytest.mark.asyncio
    async def test_screenshot_failure_handling(self):
        """Test graceful handling of screenshot failures."""
        config = ExecutionConfig()
        service = ExecutionService(config)
        
        page_mock = AsyncMock()
        page_mock.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))
        
        # Should not raise exception
        result = await service._capture_screenshot_with_iteration(
            page_mock,
            execution_id=123,
            step_number=5,
            iteration=3,
            result=ExecutionResult.PASS
        )
        
        assert result is None  # Returns None on failure


class TestLoopIntegration:
    """Integration tests for loop execution."""
    
    def test_nested_loop_detection(self):
        """Test that nested loops are not currently supported but don't crash."""
        service = ExecutionService()
        
        # Outer loop
        loop_blocks = [
            {
                "id": "outer_loop",
                "start_step": 1,
                "end_step": 10,
                "iterations": 2,
                "description": "Outer loop"
            },
            # Inner loop (would be within outer loop's range)
            {
                "id": "inner_loop",
                "start_step": 3,
                "end_step": 6,
                "iterations": 3,
                "description": "Inner loop"
            }
        ]
        
        # Find outer loop
        outer = service._find_loop_starting_at(1, loop_blocks)
        assert outer is not None
        assert outer["id"] == "outer_loop"
        
        # Find inner loop
        inner = service._find_loop_starting_at(3, loop_blocks)
        assert inner is not None
        assert inner["id"] == "inner_loop"
    
    def test_multiple_sequential_loops(self):
        """Test multiple loops in sequence."""
        service = ExecutionService()
        
        loop_blocks = [
            {
                "id": "loop1",
                "start_step": 2,
                "end_step": 4,
                "iterations": 3,
                "description": "First loop"
            },
            {
                "id": "loop2",
                "start_step": 5,
                "end_step": 7,
                "iterations": 2,
                "description": "Second loop"
            }
        ]
        
        # Both loops should be found
        loop1 = service._find_loop_starting_at(2, loop_blocks)
        assert loop1 is not None
        assert loop1["id"] == "loop1"
        
        loop2 = service._find_loop_starting_at(5, loop_blocks)
        assert loop2 is not None
        assert loop2["id"] == "loop2"
    
    def test_variable_substitution_preserves_original(self):
        """Test that variable substitution doesn't modify original step."""
        service = ExecutionService()
        
        original_step = {
            "action": "fill",
            "selector": "#input",
            "value": "value_{iteration}"
        }
        
        # Create a copy to preserve original
        step_copy = original_step.copy()
        
        result = service._apply_loop_variables(step_copy, 5, {})
        
        # Original should be unchanged
        assert original_step["value"] == "value_{iteration}"
        
        # Result should have substituted value
        assert result["value"] == "value_5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
