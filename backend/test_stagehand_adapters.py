"""
Unit tests for Stagehand adapter pattern.

Tests:
1. Factory creates correct adapter based on user settings
2. Python adapter delegates to StagehandExecutionService
3. TypeScript adapter makes HTTP calls (mocked)
4. Factory handles invalid provider gracefully
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.stagehand_factory import StagehandFactory, get_stagehand_adapter
from app.services.python_stagehand_adapter import PythonStagehandAdapter
from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter
from app.models.user_settings import UserSetting


class TestStagehandFactory:
    """Test suite for StagehandFactory."""
    
    def test_create_adapter_python(self):
        """Test factory creates Python adapter when user setting is 'python'."""
        # Mock database session
        db = Mock(spec=Session)
        
        # Mock user settings with python provider
        mock_settings = Mock(spec=UserSetting)
        mock_settings.stagehand_provider = "python"
        
        with patch('app.services.stagehand_factory.user_settings_service') as mock_service:
            mock_service.get_user_settings.return_value = mock_settings
            
            factory = StagehandFactory()
            adapter = factory.create_adapter(db, user_id=1)
            
            assert isinstance(adapter, PythonStagehandAdapter)
            assert adapter.provider_name == "python"
            mock_service.get_user_settings.assert_called_once_with(db, 1)
    
    def test_create_adapter_typescript(self):
        """Test factory creates TypeScript adapter when user setting is 'typescript'."""
        # Mock database session
        db = Mock(spec=Session)
        
        # Mock user settings with typescript provider
        mock_settings = Mock(spec=UserSetting)
        mock_settings.stagehand_provider = "typescript"
        
        with patch('app.services.stagehand_factory.user_settings_service') as mock_service:
            mock_service.get_user_settings.return_value = mock_settings
            
            factory = StagehandFactory()
            adapter = factory.create_adapter(db, user_id=1)
            
            assert isinstance(adapter, TypeScriptStagehandAdapter)
            assert adapter.provider_name == "typescript"
            mock_service.get_user_settings.assert_called_once_with(db, 1)
    
    def test_create_adapter_default_python(self):
        """Test factory defaults to Python when no user settings exist."""
        # Mock database session
        db = Mock(spec=Session)
        
        with patch('app.services.stagehand_factory.user_settings_service') as mock_service:
            mock_service.get_user_settings.return_value = None  # No settings
            
            factory = StagehandFactory()
            adapter = factory.create_adapter(db, user_id=1)
            
            assert isinstance(adapter, PythonStagehandAdapter)
            assert adapter.provider_name == "python"
    
    def test_create_adapter_invalid_provider(self):
        """Test factory raises ValueError for invalid provider."""
        # Mock database session
        db = Mock(spec=Session)
        
        # Mock user settings with invalid provider
        mock_settings = Mock(spec=UserSetting)
        mock_settings.stagehand_provider = "invalid"
        
        with patch('app.services.stagehand_factory.user_settings_service') as mock_service:
            mock_service.get_user_settings.return_value = mock_settings
            
            factory = StagehandFactory()
            
            with pytest.raises(ValueError, match="Invalid stagehand provider: invalid"):
                factory.create_adapter(db, user_id=1)
    
    def test_create_adapter_explicit_python(self):
        """Test explicit adapter creation for Python."""
        factory = StagehandFactory()
        adapter = factory.create_adapter_explicit("python")
        
        assert isinstance(adapter, PythonStagehandAdapter)
        assert adapter.provider_name == "python"
    
    def test_create_adapter_explicit_typescript(self):
        """Test explicit adapter creation for TypeScript."""
        factory = StagehandFactory()
        adapter = factory.create_adapter_explicit("typescript")
        
        assert isinstance(adapter, TypeScriptStagehandAdapter)
        assert adapter.provider_name == "typescript"
    
    def test_create_adapter_explicit_invalid(self):
        """Test explicit adapter creation raises ValueError for invalid provider."""
        factory = StagehandFactory()
        
        with pytest.raises(ValueError, match="Invalid stagehand provider: invalid"):
            factory.create_adapter_explicit("invalid")
    
    def test_get_stagehand_adapter_convenience(self):
        """Test convenience function creates adapter."""
        db = Mock(spec=Session)
        
        mock_settings = Mock(spec=UserSetting)
        mock_settings.stagehand_provider = "python"
        
        with patch('app.services.stagehand_factory.user_settings_service') as mock_service:
            mock_service.get_user_settings.return_value = mock_settings
            
            adapter = get_stagehand_adapter(db, user_id=1)
            
            assert isinstance(adapter, PythonStagehandAdapter)


class TestPythonStagehandAdapter:
    """Test suite for PythonStagehandAdapter."""
    
    @pytest.mark.asyncio
    async def test_initialize_delegates_to_service(self):
        """Test initialize method delegates to StagehandExecutionService."""
        adapter = PythonStagehandAdapter()
        
        # Mock the underlying service
        adapter._service.initialize = AsyncMock()
        
        user_config = {"provider": "cerebras"}
        await adapter.initialize(user_config)
        
        adapter._service.initialize.assert_called_once_with(user_config)
    
    @pytest.mark.asyncio
    async def test_cleanup_delegates_to_service(self):
        """Test cleanup method delegates to StagehandExecutionService."""
        adapter = PythonStagehandAdapter()
        
        # Mock the underlying service
        adapter._service.cleanup = AsyncMock()
        
        await adapter.cleanup()
        
        adapter._service.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_single_step_delegates_to_service(self):
        """Test execute_single_step delegates to StagehandExecutionService."""
        adapter = PythonStagehandAdapter()
        
        # Mock the underlying service
        expected_result = {
            "success": True,
            "error": None,
            "actual": "Clicked button",
            "expected": "Click login button",
            "screenshot_path": "/path/to/screenshot.png",
            "duration_seconds": 1.5,
            "tokens_used": 100
        }
        adapter._service.execute_single_step = AsyncMock(return_value=expected_result)
        
        result = await adapter.execute_single_step(
            step_description="Click login button",
            step_number=1,
            execution_id=123
        )
        
        assert result == expected_result
        adapter._service.execute_single_step.assert_called_once_with(
            step_description="Click login button",
            step_number=1,
            execution_id=123
        )
    
    def test_provider_name(self):
        """Test provider_name property returns 'python'."""
        adapter = PythonStagehandAdapter()
        assert adapter.provider_name == "python"


class TestTypeScriptStagehandAdapter:
    """Test suite for TypeScriptStagehandAdapter."""
    
    @pytest.mark.asyncio
    async def test_initialize_makes_http_request(self):
        """Test initialize makes HTTP POST to TypeScript service."""
        adapter = TypeScriptStagehandAdapter(service_url="http://localhost:3001")
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"session_id": "test-session-123"})
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            await adapter.initialize(user_config={"provider": "cerebras"})
            
            assert adapter._browser_session_id == "test-session-123"
    
    @pytest.mark.asyncio
    async def test_initialize_handles_error(self):
        """Test initialize raises ValueError on HTTP error."""
        adapter = TypeScriptStagehandAdapter(service_url="http://localhost:3001")
        
        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(ValueError, match="Failed to initialize TypeScript Stagehand"):
                await adapter.initialize()
    
    @pytest.mark.asyncio
    async def test_cleanup_makes_http_request(self):
        """Test cleanup makes HTTP POST to TypeScript service."""
        adapter = TypeScriptStagehandAdapter(service_url="http://localhost:3001")
        adapter._browser_session_id = "test-session-123"
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock session close
            adapter._session = MagicMock()
            adapter._session.closed = False
            adapter._session.close = AsyncMock()
            
            await adapter.cleanup()
            
            assert adapter._browser_session_id is None
    
    @pytest.mark.asyncio
    async def test_execute_single_step_makes_http_request(self):
        """Test execute_single_step makes HTTP POST to TypeScript service."""
        adapter = TypeScriptStagehandAdapter(service_url="http://localhost:3001")
        adapter._browser_session_id = "test-session-123"
        
        # Mock HTTP response
        expected_result = {
            "success": True,
            "error": None,
            "actual": "Clicked button",
            "expected": "Click login button",
            "screenshot_path": "/path/to/screenshot.png",
            "duration_seconds": 1.5,
            "tokens_used": 100
        }
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_result)
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await adapter.execute_single_step(
                step_description="Click login button",
                step_number=1,
                execution_id=123
            )
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_execute_single_step_requires_initialization(self):
        """Test execute_single_step raises error if not initialized."""
        adapter = TypeScriptStagehandAdapter(service_url="http://localhost:3001")
        
        with pytest.raises(ValueError, match="Browser not initialized"):
            await adapter.execute_single_step(
                step_description="Click button",
                step_number=1,
                execution_id=123
            )
    
    def test_provider_name(self):
        """Test provider_name property returns 'typescript'."""
        adapter = TypeScriptStagehandAdapter()
        assert adapter.provider_name == "typescript"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
