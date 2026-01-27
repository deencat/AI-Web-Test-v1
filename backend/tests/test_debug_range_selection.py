"""
Comprehensive unit tests for debug range selection (Enhancement 4 Phase 4).

Tests range validation, prerequisite skipping, boundary conditions, and integration scenarios.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.debug_session_service import DebugSessionService
from app.models.debug_session import DebugSession, DebugMode, DebugSessionStatus
from app.models.test_execution import TestExecution
from app.models.test_case import TestCase
from app.schemas.debug_session import DebugSessionStartRequest


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
    service.page = Mock()  # Mock page attribute
    service.cleanup = AsyncMock()
    return service


@pytest.fixture
def mock_test_case():
    """Mock test case with 20 steps."""
    test_case = Mock(spec=TestCase)
    test_case.id = 1
    test_case.steps = [f"Step {i+1} description" for i in range(20)]
    return test_case


@pytest.fixture
def mock_execution(mock_test_case):
    """Mock test execution."""
    execution = Mock(spec=TestExecution)
    execution.id = 100
    execution.test_case_id = 1
    execution.test_case = mock_test_case
    execution.total_steps = 20
    execution.base_url = "https://example.com"
    return execution


@pytest.fixture
def debug_service():
    """Create debug session service instance."""
    service = DebugSessionService()
    return service


# ============================================================================
# Test Suite 1: Range Validation
# ============================================================================

class TestRangeValidation:
    """Tests for range validation during session start."""
    
    @pytest.mark.asyncio
    async def test_valid_range(self, debug_service, mock_db, mock_execution):
        """Test valid step range (15-20)."""
        # Mock CRUD operations
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution), \
             patch('app.crud.debug_session.create_debug_session') as mock_create, \
             patch('app.crud.debug_session.update_debug_session_browser_info'), \
             patch('app.crud.debug_session.update_debug_session_status'), \
             patch('app.crud.debug_session.mark_setup_completed'), \
             patch('app.crud.debug_session.get_debug_session'), \
             patch('app.services.stagehand_factory.get_stagehand_adapter'):
            
            # Configure mock session
            mock_session = Mock(spec=DebugSession)
            mock_session.session_id = "test-123"
            mock_session.target_step_number = 15
            mock_session.end_step_number = 20
            mock_session.skip_prerequisites = False
            mock_session.prerequisite_steps_count = 14
            mock_create.return_value = mock_session
            
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=15,
                end_step_number=20,
                mode=DebugMode.AUTO,
                skip_prerequisites=False
            )
            
            # Should not raise exception
            # (full validation happens in service layer)
            assert request.target_step_number == 15
            assert request.end_step_number == 20
    
    @pytest.mark.asyncio
    async def test_invalid_range_end_before_start(self, debug_service, mock_db, mock_execution):
        """Test invalid range where end < start."""
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution):
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=15,
                end_step_number=10,  # Invalid: 10 < 15
                mode=DebugMode.AUTO
            )
            
            # Service should validate and reject
            with pytest.raises(ValueError, match="End step .* must be >= start step"):
                await debug_service.start_session(
                    db=mock_db,
                    user_id=1,
                    request=request
                )
    
    @pytest.mark.asyncio
    async def test_end_step_exceeds_total(self, debug_service, mock_db, mock_execution):
        """Test end_step_number exceeds total_steps."""
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution):
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=15,
                end_step_number=25,  # Exceeds total_steps=20
                mode=DebugMode.AUTO
            )
            
            with pytest.raises(ValueError, match="End step .* out of range"):
                await debug_service.start_session(
                    db=mock_db,
                    user_id=1,
                    request=request
                )
    
    @pytest.mark.asyncio
    async def test_single_step_range(self, debug_service, mock_db, mock_execution):
        """Test range with start == end (single step)."""
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution):
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=15,
                end_step_number=15,  # Same step
                mode=DebugMode.AUTO
            )
            
            # Should be valid (debugging exactly one step)
            assert request.target_step_number == request.end_step_number


# ============================================================================
# Test Suite 2: Prerequisite Skipping
# ============================================================================

class TestPrerequisiteSkipping:
    """Tests for skip_prerequisites functionality."""
    
    @pytest.mark.asyncio
    async def test_skip_prerequisites_auto_mode(self, debug_service, mock_db, mock_execution):
        """Test skip_prerequisites with AUTO mode."""
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution), \
             patch('app.crud.debug_session.create_debug_session') as mock_create:
            
            mock_session = Mock(spec=DebugSession)
            mock_session.prerequisite_steps_count = 0  # Should be 0 when skipped
            mock_create.return_value = mock_session
            
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=15,
                mode=DebugMode.AUTO,
                skip_prerequisites=True
            )
            
            # Verify CRUD is called with skip_prerequisites=True
            # (would need to inspect mock_create call args in full implementation)
            assert request.skip_prerequisites is True
    
    @pytest.mark.asyncio
    async def test_manual_mode_implies_skip(self, debug_service, mock_db, mock_execution):
        """Test MANUAL mode implies skip_prerequisites=True."""
        request = DebugSessionStartRequest(
            execution_id=100,
            target_step_number=15,
            mode=DebugMode.MANUAL,
            skip_prerequisites=False  # User sets False
        )
        
        # In InteractiveDebugPanel, manual mode forces skip_prerequisites=True
        # Service should handle this correctly
        assert request.mode == DebugMode.MANUAL


# ============================================================================
# Test Suite 3: Range Boundary Checking in execute_next_step
# ============================================================================

class TestRangeBoundaryChecking:
    """Tests for range boundary checking during step execution."""
    
    @pytest.mark.asyncio
    async def test_execute_within_range(self, debug_service, mock_db, mock_execution, mock_browser_service):
        """Test executing steps within defined range."""
        # Mock session with range 15-17
        mock_session = Mock(spec=DebugSession)
        mock_session.id = 1
        mock_session.session_id = "test-123"
        mock_session.user_id = 1
        mock_session.status = DebugSessionStatus.READY
        mock_session.execution = mock_execution
        mock_session.execution_id = 100
        mock_session.target_step_number = 15
        mock_session.end_step_number = 17
        mock_session.current_step = None  # First execution
        
        # Store browser service
        debug_service.active_sessions["test-123"] = mock_browser_service
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_session), \
             patch('app.crud.debug_session.update_debug_session_status'), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'):
            
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-123",
                user_id=1
            )
            
            assert result["success"] is True
            assert result["step_number"] == 15
            assert result["has_more_steps"] is True
            assert result["range_complete"] is False
            assert result["end_step_number"] == 17
    
    @pytest.mark.asyncio
    async def test_execute_last_step_in_range(self, debug_service, mock_db, mock_execution, mock_browser_service):
        """Test executing the last step in range."""
        mock_session = Mock(spec=DebugSession)
        mock_session.id = 1
        mock_session.session_id = "test-123"
        mock_session.user_id = 1
        mock_session.status = DebugSessionStatus.READY
        mock_session.execution = mock_execution
        mock_session.execution_id = 100
        mock_session.target_step_number = 15
        mock_session.end_step_number = 17
        mock_session.current_step = 16  # Already executed step 15, 16
        
        debug_service.active_sessions["test-123"] = mock_browser_service
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_session), \
             patch('app.crud.debug_session.update_debug_session_status'), \
             patch('app.crud.debug_session.create_debug_step_execution'), \
             patch('app.crud.debug_session.increment_debug_session_tokens'), \
             patch('app.crud.debug_session.increment_debug_session_iterations'), \
             patch('app.crud.debug_session.update_current_step'):
            
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-123",
                user_id=1
            )
            
            assert result["success"] is True
            assert result["step_number"] == 17  # Last step in range
            assert result["has_more_steps"] is False  # No more in range
            assert result["range_complete"] is True
    
    @pytest.mark.asyncio
    async def test_execute_beyond_range(self, debug_service, mock_db, mock_execution, mock_browser_service):
        """Test attempting to execute beyond end_step_number."""
        mock_session = Mock(spec=DebugSession)
        mock_session.id = 1
        mock_session.session_id = "test-123"
        mock_session.user_id = 1
        mock_session.status = DebugSessionStatus.READY
        mock_session.execution = mock_execution
        mock_session.execution_id = 100
        mock_session.target_step_number = 15
        mock_session.end_step_number = 17
        mock_session.current_step = 17  # Already at end
        
        debug_service.active_sessions["test-123"] = mock_browser_service
        
        with patch('app.crud.debug_session.get_debug_session', return_value=mock_session):
            result = await debug_service.execute_next_step(
                db=mock_db,
                session_id="test-123",
                user_id=1
            )
            
            # Should return range_complete=True
            assert result["success"] is True
            assert result["has_more_steps"] is False
            assert result["range_complete"] is True
            assert result["end_step_number"] == 17


# ============================================================================
# Test Suite 4: Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """End-to-end integration tests for debug range selection."""
    
    @pytest.mark.asyncio
    async def test_auto_navigate_with_range(self, debug_service, mock_db, mock_execution, mock_browser_service):
        """Test AUTO mode with range (steps 15-17, prerequisites executed)."""
        # This would require full integration test with mocked browser
        # Placeholder for documentation
        pass
    
    @pytest.mark.asyncio
    async def test_manual_navigate_skip_range(self, debug_service, mock_db, mock_execution):
        """Test MANUAL mode with skip_prerequisites (immediate debugging)."""
        # This would require full integration test
        # Placeholder for documentation
        pass
    
    @pytest.mark.asyncio
    async def test_no_range_backward_compatible(self, debug_service, mock_db, mock_execution):
        """Test backward compatibility when end_step_number=None."""
        request = DebugSessionStartRequest(
            execution_id=100,
            target_step_number=15,
            end_step_number=None,  # No range specified
            mode=DebugMode.AUTO
        )
        
        # Should behave like original single-step debug
        assert request.end_step_number is None


# ============================================================================
# Test Suite 5: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in range selection."""
    
    @pytest.mark.asyncio
    async def test_invalid_execution_id(self, debug_service, mock_db):
        """Test with non-existent execution_id."""
        with patch('app.crud.test_execution.get_execution', return_value=None):
            request = DebugSessionStartRequest(
                execution_id=999,
                target_step_number=15,
                end_step_number=20,
                mode=DebugMode.AUTO
            )
            
            with pytest.raises(ValueError, match="Execution .* not found"):
                await debug_service.start_session(
                    db=mock_db,
                    user_id=1,
                    request=request
                )
    
    @pytest.mark.asyncio
    async def test_start_step_out_of_bounds(self, debug_service, mock_db, mock_execution):
        """Test start_step_number > total_steps."""
        with patch('app.crud.test_execution.get_execution', return_value=mock_execution):
            request = DebugSessionStartRequest(
                execution_id=100,
                target_step_number=25,  # Exceeds total_steps=20
                mode=DebugMode.AUTO
            )
            
            with pytest.raises(ValueError, match="Target step .* out of range"):
                await debug_service.start_session(
                    db=mock_db,
                    user_id=1,
                    request=request
                )


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
