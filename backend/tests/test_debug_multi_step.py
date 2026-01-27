"""
Comprehensive unit tests for multi-step debug mode (Enhancement 4 Phase 2).

Tests sequential step execution, bounds checking, state management, and error handling.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.debug_session_service import DebugSessionService
from app.models.debug_session import DebugSession, DebugMode, DebugSessionStatus
from app.models.test_execution import TestExecution
from app.models.test_case import TestCase


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_browser_service():
    """Mock browser service with execute_single_step."""
    service = AsyncMock()
    service.execute_single_step = AsyncMock(return_value={
        "success": True,
        "error": None,
        "screenshot_path": "/path/to/screenshot.png",
        "duration_seconds": 0.5,
        "tokens_used": 100
    })
    return service


@pytest.fixture
def mock_test_case():
    """Mock test case with 10 steps."""
    test_case = Mock(spec=TestCase)
    test_case.id = 1
    test_case.steps = [
        "Navigate to login page",
        "Click login button",
        "Enter username",
        "Enter password",
        "Click submit",
        "Wait for dashboard",
        "Enter HKID main part",
        "Enter HKID check digit",
        "Click Submit button",
        "Verify success message"
    ]
    return test_case


@pytest.fixture
def mock_execution(mock_test_case):
    """Mock test execution."""
    execution = Mock(spec=TestExecution)
    execution.id = 100
    execution.test_case_id = 1
    execution.test_case = mock_test_case
    execution.total_steps = 10
    return execution


@pytest.fixture
def mock_debug_session(mock_execution):
    """Mock debug session."""
    session = Mock(spec=DebugSession)
    session.id = 1
    session.session_id = "test-session-123"
    session.user_id = 1
    session.mode = DebugMode.AUTO
    session.status = DebugSessionStatus.READY
    session.execution_id = 100
    session.execution = mock_execution
    session.target_step_number = 7
    session.current_step = None  # Not set yet
    session.tokens_used = 0
    session.iterations_count = 0
    return session


@pytest.fixture
def debug_service():
    """Create debug session service instance."""
    return DebugSessionService()


# ============================================================================
# Test Suite 1: Sequential Step Execution
# ============================================================================

class TestSequentialStepExecution:
    """Test sequential execution of multiple steps."""
    
    @pytest.mark.asyncio
    async def test_execute_next_step_first_time(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test executing next step for the first time (should execute target step)."""
        # Setup
        mock_debug_session.current_step = None  # First execution
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(return_value="Enter HKID main part")
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify
            assert result["success"] is True
            assert result["step_number"] == 7  # Target step
            assert result["step_description"] == "Enter HKID main part"
            assert result["has_more_steps"] is True
            assert result["next_step_preview"] == "Enter HKID check digit"
            assert result["total_steps"] == 10
            assert result["tokens_used"] == 100
    
    @pytest.mark.asyncio
    async def test_execute_next_step_second_time(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test executing next step after first execution (should execute step+1)."""
        # Setup - current_step already set to 7
        mock_debug_session.current_step = 7
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(return_value="Enter HKID check digit")
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify
            assert result["success"] is True
            assert result["step_number"] == 8  # Next step
            assert result["step_description"] == "Enter HKID check digit"
            assert result["has_more_steps"] is True
            assert result["next_step_preview"] == "Click Submit button"
            assert result["total_steps"] == 10
    
    @pytest.mark.asyncio
    async def test_execute_three_steps_sequentially(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test executing three consecutive steps (7, 8, 9)."""
        steps_executed = []
        
        def track_step(db, session_id, step_number):
            steps_executed.append(step_number)
            mock_debug_session.current_step = step_number
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step', side_effect=track_step), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(side_effect=lambda x, y: x)
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute step 7 (first time, current_step=None)
            mock_debug_session.current_step = None
            result1 = await debug_service.execute_next_step(
                db=mock_db, session_id="test-session-123", user_id=1
            )
            
            # Execute step 8 (current_step=7)
            result2 = await debug_service.execute_next_step(
                db=mock_db, session_id="test-session-123", user_id=1
            )
            
            # Execute step 9 (current_step=8)
            result3 = await debug_service.execute_next_step(
                db=mock_db, session_id="test-session-123", user_id=1
            )
            
            # Verify sequence
            assert steps_executed == [7, 8, 9]
            assert result1["step_number"] == 7
            assert result2["step_number"] == 8
            assert result3["step_number"] == 9
            assert result3["has_more_steps"] is True
            assert result3["next_step_preview"] == "Verify success message"


# ============================================================================
# Test Suite 2: Bounds Checking
# ============================================================================

class TestBoundsChecking:
    """Test boundary conditions and edge cases."""
    
    @pytest.mark.asyncio
    async def test_execute_next_beyond_last_step(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test executing next step when already at last step."""
        # Setup - at last step
        mock_debug_session.current_step = 10
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session):
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute (should fail gracefully)
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify
            assert result["success"] is False
            assert result["error_message"] == "No more steps to execute (total: 10)"
            assert result["has_more_steps"] is False
            assert result["next_step_preview"] is None
            assert result["step_number"] == 10  # Still at last step
    
    @pytest.mark.asyncio
    async def test_execute_next_at_last_step(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test executing last step (should have no more steps after)."""
        # Setup - at second-to-last step
        mock_debug_session.current_step = 9
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(return_value="Verify success message")
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify
            assert result["success"] is True
            assert result["step_number"] == 10  # Last step
            assert result["has_more_steps"] is False  # No more steps
            assert result["next_step_preview"] is None


# ============================================================================
# Test Suite 3: State Management
# ============================================================================

class TestStateManagement:
    """Test session state tracking and browser persistence."""
    
    @pytest.mark.asyncio
    async def test_current_step_updated_after_execution(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test that current_step is updated in database after each execution."""
        update_calls = []
        
        def capture_update(db, session_id, step_number):
            update_calls.append((session_id, step_number))
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step', side_effect=capture_update), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(side_effect=lambda x, y: x)
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute
            mock_debug_session.current_step = None
            await debug_service.execute_next_step(
                db=mock_db, session_id="test-session-123", user_id=1
            )
            
            # Verify update_current_step was called with correct step
            assert len(update_calls) == 1
            assert update_calls[0] == ("test-session-123", 7)
    
    @pytest.mark.asyncio
    async def test_browser_session_reused(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test that same browser service is reused across multiple steps."""
        execute_calls = []
        
        async def track_execution(*args, **kwargs):
            execute_calls.append(id(mock_browser_service))
            return {
                "success": True,
                "error": None,
                "screenshot_path": "/path/to/screenshot.png",
                "duration_seconds": 0.5,
                "tokens_used": 100
            }
        
        mock_browser_service.execute_single_step = AsyncMock(side_effect=track_execution)
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(side_effect=lambda x, y: x)
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute multiple steps
            mock_debug_session.current_step = 7
            await debug_service.execute_next_step(mock_db, "test-session-123", 1)
            
            mock_debug_session.current_step = 8
            await debug_service.execute_next_step(mock_db, "test-session-123", 1)
            
            # Verify same browser instance ID used
            assert len(execute_calls) == 2
            assert execute_calls[0] == execute_calls[1]


# ============================================================================
# Test Suite 4: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_session_not_found(self, debug_service, mock_db):
        """Test executing next step with invalid session ID."""
        with patch('app.crud.debug_session.get_debug_session', return_value=None):
            
            with pytest.raises(ValueError, match="Debug session .* not found"):
                await debug_service.execute_next_step(
                    db=mock_db,
                    session_id="invalid-session",
                    user_id=1
                )
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, debug_service, mock_db, mock_debug_session):
        """Test accessing another user's debug session."""
        mock_debug_session.user_id = 999  # Different user
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session):
            
            with pytest.raises(PermissionError, match="Not authorized"):
                await debug_service.execute_next_step(
                    db=mock_db,
                    session_id="test-session-123",
                    user_id=1  # Requesting user ID
                )
    
    @pytest.mark.asyncio
    async def test_session_not_ready(self, debug_service, mock_db, mock_debug_session):
        """Test executing next step when session is not in ready state."""
        mock_debug_session.status = DebugSessionStatus.FAILED
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session):
            
            with pytest.raises(ValueError, match="Debug session not ready"):
                await debug_service.execute_next_step(
                    db=mock_db,
                    session_id="test-session-123",
                    user_id=1
                )
    
    @pytest.mark.asyncio
    async def test_browser_session_expired(self, debug_service, mock_db, mock_debug_session):
        """Test executing next step when browser session has expired."""
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session):
            
            # Don't add browser service to active_sessions
            # debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            with pytest.raises(ValueError, match="Browser session .* not found"):
                await debug_service.execute_next_step(
                    db=mock_db,
                    session_id="test-session-123",
                    user_id=1
                )
    
    @pytest.mark.asyncio
    async def test_step_execution_failure(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test handling of step execution failure."""
        # Setup browser to fail
        mock_browser_service.execute_single_step = AsyncMock(
            side_effect=Exception("Element not found")
        )
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(return_value="Enter HKID main part")
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute (should return error response instead of raising)
            mock_debug_session.current_step = None
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify error response
            assert result["success"] is False
            assert "Element not found" in result["error_message"]
            assert result["step_number"] == 7


# ============================================================================
# Test Suite 5: Test Data Substitution
# ============================================================================

class TestDataSubstitution:
    """Test integration with test data generator."""
    
    @pytest.mark.asyncio
    async def test_hkid_data_substitution(
        self, 
        debug_service, 
        mock_db, 
        mock_debug_session, 
        mock_browser_service
    ):
        """Test that test data patterns are substituted in steps."""
        substituted_values = []
        
        def capture_substitution(step_desc, execution_id):
            if "{generate:hkid:main}" in step_desc:
                substituted = step_desc.replace("{generate:hkid:main}", "G197611")
                substituted_values.append(substituted)
                return substituted
            return step_desc
        
        # Update test case steps to include test data patterns
        mock_debug_session.execution.test_case.steps = [
            "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6",
            "Enter HKID main: {generate:hkid:main}",
            "Enter HKID check: {generate:hkid:check}",
            "Step 9", "Step 10"
        ]
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_debug_session), \
             patch('app.crud.debug_session.update_debug_session_status', return_value=mock_debug_session), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'), \
             patch('app.services.execution_service.ExecutionService') as mock_exec_service:
            
            # Mock test data substitution
            mock_exec_instance = Mock()
            mock_exec_instance._substitute_test_data_patterns = Mock(side_effect=capture_substitution)
            mock_exec_service.return_value = mock_exec_instance
            
            # Add browser service to active sessions
            debug_service.active_sessions["test-session-123"] = mock_browser_service
            
            # Execute
            mock_debug_session.current_step = None
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-session-123",
                user_id=1
            )
            
            # Verify substitution occurred
            assert len(substituted_values) == 1
            assert "G197611" in substituted_values[0]
            assert "{generate:hkid:main}" not in substituted_values[0]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
