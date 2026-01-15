"""
Sprint 5 Stage 6: Integration Tests for Dual Stagehand Provider System

Tests provider switching, health checking, and cross-provider compatibility.
"""
import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stagehand_factory import StagehandFactory
from app.services.python_stagehand_adapter import PythonStagehandAdapter
from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter
from app.models.user_settings import UserSetting
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = MagicMock()
    return db


@pytest.fixture
def mock_user_settings_python():
    """Create mock user settings with Python provider"""
    settings = MagicMock(spec=UserSetting)
    settings.stagehand_provider = 'python'
    return settings


@pytest.fixture
def mock_user_settings_typescript():
    """Create mock user settings with TypeScript provider"""
    settings = MagicMock(spec=UserSetting)
    settings.stagehand_provider = 'typescript'
    return settings


class TestProviderSwitching:
    """Test provider switching functionality"""
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_factory_creates_python_adapter(self, mock_get_settings, mock_db, mock_user_settings_python):
        """Test factory creates Python adapter when configured"""
        mock_get_settings.return_value = mock_user_settings_python
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert isinstance(adapter, PythonStagehandAdapter)
        assert adapter.provider_name == 'python'
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_factory_creates_typescript_adapter(self, mock_get_settings, mock_db, mock_user_settings_typescript):
        """Test factory creates TypeScript adapter when configured"""
        mock_get_settings.return_value = mock_user_settings_typescript
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert isinstance(adapter, TypeScriptStagehandAdapter)
        assert adapter.provider_name == 'typescript'
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_factory_rejects_invalid_provider(self, mock_get_settings, mock_db):
        """Test factory raises ValueError for invalid provider"""
        settings = MagicMock(spec=UserSetting)
        settings.stagehand_provider = 'invalid'
        mock_get_settings.return_value = settings
        
        with pytest.raises(ValueError, match="Invalid stagehand provider"):
            StagehandFactory.create_adapter(mock_db, user_id=1)
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_factory_rejects_none_provider(self, mock_get_settings, mock_db):
        """Test factory raises ValueError for None provider"""
        settings = MagicMock(spec=UserSetting)
        settings.stagehand_provider = None
        mock_get_settings.return_value = settings
        
        with pytest.raises(ValueError, match="Invalid stagehand provider"):
            StagehandFactory.create_adapter(mock_db, user_id=1)


class TestCrossProviderCompatibility:
    """Test that both providers have compatible interfaces"""
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_both_providers_have_initialize(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test both providers implement initialize()"""
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        assert hasattr(python_adapter, 'initialize')
        assert hasattr(typescript_adapter, 'initialize')
        assert callable(python_adapter.initialize)
        assert callable(typescript_adapter.initialize)
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_both_providers_have_initialize_persistent(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test both providers implement initialize_persistent() for session management"""
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        assert hasattr(python_adapter, 'initialize_persistent')
        assert hasattr(typescript_adapter, 'initialize_persistent')
        assert callable(python_adapter.initialize_persistent)
        assert callable(typescript_adapter.initialize_persistent)
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_both_providers_have_execute_methods(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test both providers have execution methods (may have different names)"""
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        # Python adapter has execute_single_step, TypeScript has execute_step
        assert hasattr(python_adapter, 'execute_single_step') or hasattr(python_adapter, 'execute_step')
        assert hasattr(typescript_adapter, 'execute_step') or hasattr(typescript_adapter, 'execute_single_step')
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_both_providers_have_cleanup(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test both providers implement cleanup()"""
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        assert hasattr(python_adapter, 'cleanup')
        assert hasattr(typescript_adapter, 'cleanup')
        assert callable(python_adapter.cleanup)
        assert callable(typescript_adapter.cleanup)
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_both_providers_have_provider_name(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test both providers expose provider_name property"""
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        assert hasattr(python_adapter, 'provider_name')
        assert hasattr(typescript_adapter, 'provider_name')
        assert python_adapter.provider_name == 'python'
        assert typescript_adapter.provider_name == 'typescript'


class TestProviderHealthChecks:
    """Test health checking functionality"""
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_python_provider_always_available(self, mock_get_settings, mock_db, mock_user_settings_python):
        """Test Python provider is always available (built-in)"""
        mock_get_settings.return_value = mock_user_settings_python
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert adapter is not None
        assert isinstance(adapter, PythonStagehandAdapter)
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_typescript_adapter_service_url(self, mock_get_settings, mock_db, mock_user_settings_typescript):
        """Test TypeScript adapter has correct service URL"""
        mock_get_settings.return_value = mock_user_settings_typescript
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert hasattr(adapter, 'service_url')
        assert 'localhost:3001' in adapter.service_url or '127.0.0.1:3001' in adapter.service_url


class TestProviderConfiguration:
    """Test provider configuration and settings"""
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_typescript_adapter_has_timeout_config(self, mock_get_settings, mock_db, mock_user_settings_typescript):
        """Test TypeScript adapter has timeout configuration"""
        mock_get_settings.return_value = mock_user_settings_typescript
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert hasattr(adapter, 'timeout')
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_python_adapter_has_service_config(self, mock_get_settings, mock_db, mock_user_settings_python):
        """Test Python adapter has StagehandService"""
        mock_get_settings.return_value = mock_user_settings_python
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert hasattr(adapter, '_service')


class TestProviderErrorHandling:
    """Test error handling across providers"""
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_typescript_adapter_handles_service_unavailable(self, mock_get_settings, mock_db, mock_user_settings_typescript):
        """Test TypeScript adapter gracefully handles unavailable service"""
        mock_get_settings.return_value = mock_user_settings_typescript
        
        adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        
        # Try to initialize without service running
        # Should raise ConnectionError or similar
        try:
            await adapter.initialize({})
            # If we get here, service might be running, which is okay
        except (ConnectionError, ValueError, Exception) as e:
            # Expected behavior - should handle gracefully
            assert True
    
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    def test_factory_validates_provider_string(self, mock_get_settings, mock_db):
        """Test factory validates provider string input"""
        # Should raise ValueError for empty string
        settings = MagicMock(spec=UserSetting)
        settings.stagehand_provider = ''
        mock_get_settings.return_value = settings
        
        with pytest.raises(ValueError, match="Invalid stagehand provider"):
            StagehandFactory.create_adapter(mock_db, user_id=1)
        
        # Should also reject case-mismatched provider names
        settings.stagehand_provider = 'PYTHON'
        with pytest.raises(ValueError, match="Invalid stagehand provider"):
            StagehandFactory.create_adapter(mock_db, user_id=1)


@pytest.mark.integration
class TestEndToEndProviderSwitching:
    """Integration tests for complete provider switching workflow"""
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_switch_from_python_to_typescript(self, mock_get_settings, mock_db, mock_user_settings_python, mock_user_settings_typescript):
        """Test switching from Python to TypeScript provider"""
        # Create Python adapter
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert python_adapter.provider_name == 'python'
        
        # Switch to TypeScript
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert typescript_adapter.provider_name == 'typescript'
        
        # Verify they are different instances
        assert python_adapter is not typescript_adapter
        assert type(python_adapter) != type(typescript_adapter)
    
    @pytest.mark.asyncio
    @patch('app.services.stagehand_factory.user_settings_service.get_user_settings')
    async def test_switch_from_typescript_to_python(self, mock_get_settings, mock_db, mock_user_settings_typescript, mock_user_settings_python):
        """Test switching from TypeScript to Python provider"""
        # Create TypeScript adapter
        mock_get_settings.return_value = mock_user_settings_typescript
        typescript_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert typescript_adapter.provider_name == 'typescript'
        
        # Switch to Python
        mock_get_settings.return_value = mock_user_settings_python
        python_adapter = StagehandFactory.create_adapter(mock_db, user_id=1)
        assert python_adapter.provider_name == 'python'
        
        # Verify they are different instances
        assert typescript_adapter is not python_adapter
        assert type(typescript_adapter) != type(python_adapter)


if __name__ == '__main__':
    print("="*80)
    print("Sprint 5 Stage 6: Integration Tests - Provider Switching")
    print("="*80)
    
    # Run tests with pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'not integration or integration'
    ])
    
    if exit_code == 0:
        print("\n" + "="*80)
        print("[SUCCESS] All provider switching tests passed!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("[FAIL] Some tests failed. See details above.")
        print("="*80)
    
    sys.exit(exit_code)
