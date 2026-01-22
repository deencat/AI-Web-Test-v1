"""
Unit tests for file upload functionality across all 3 tiers.
Sprint 5.5 Enhancement 1: File Upload Support
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from playwright.async_api import Page

from app.services.tier1_playwright import Tier1PlaywrightExecutor
from app.services.tier2_hybrid import Tier2HybridExecutor
from app.services.tier3_stagehand import Tier3StagehandExecutor


# Test file paths
TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_files")
HKID_FILE = os.path.join(TEST_FILES_DIR, "hkid_sample.pdf")
PASSPORT_FILE = os.path.join(TEST_FILES_DIR, "passport_sample.jpg")
ADDRESS_FILE = os.path.join(TEST_FILES_DIR, "address_proof.pdf")


class TestTier1FileUpload:
    """Test Tier 1 (Playwright Direct) file upload handler."""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test successful file upload with Tier 1."""
        # Arrange
        executor = Tier1PlaywrightExecutor(timeout_ms=5000)
        mock_page = AsyncMock(spec=Page)
        mock_element = AsyncMock()
        
        # Mock element methods
        mock_element.wait_for = AsyncMock()
        mock_element.evaluate = AsyncMock(side_effect=["INPUT", "file"])
        mock_element.set_input_files = AsyncMock()
        
        # Mock locator chain
        mock_locator = Mock()
        mock_locator.first = mock_element
        mock_page.locator.return_value = mock_locator
        
        step = {
            "action": "upload_file",
            "selector": "input[type='file']",
            "file_path": HKID_FILE,
            "instruction": "Upload HKID document"
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is True
        assert result["tier"] == 1
        assert result["error"] is None
        mock_element.set_input_files.assert_called_once_with(HKID_FILE, timeout=5000)
    
    @pytest.mark.asyncio
    async def test_upload_file_missing_path(self):
        """Test file upload fails when file_path is missing."""
        # Arrange
        executor = Tier1PlaywrightExecutor(timeout_ms=5000)
        mock_page = AsyncMock(spec=Page)
        
        step = {
            "action": "upload_file",
            "selector": "input[type='file']",
            "instruction": "Upload document"
            # Missing file_path
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is False
        assert "file_path" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_file_nonexistent_file(self):
        """Test file upload fails when file doesn't exist."""
        # Arrange
        executor = Tier1PlaywrightExecutor(timeout_ms=5000)
        mock_page = AsyncMock(spec=Page)
        mock_element = AsyncMock()
        
        mock_element.wait_for = AsyncMock()
        
        mock_locator = Mock()
        mock_locator.first = mock_element
        mock_page.locator.return_value = mock_locator
        
        step = {
            "action": "upload_file",
            "selector": "input[type='file']",
            "file_path": "/nonexistent/file.pdf",
            "instruction": "Upload document"
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_file_missing_selector(self):
        """Test file upload fails when selector is missing."""
        # Arrange
        executor = Tier1PlaywrightExecutor(timeout_ms=5000)
        mock_page = AsyncMock(spec=Page)
        
        step = {
            "action": "upload_file",
            "file_path": HKID_FILE,
            "instruction": "Upload document"
            # Missing selector
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is False
        assert "selector" in result["error"].lower()


class TestTier2FileUpload:
    """Test Tier 2 (Hybrid Mode) file upload handler."""
    
    @pytest.mark.asyncio
    async def test_upload_file_with_cached_xpath(self):
        """Test file upload using cached XPath in Tier 2."""
        # Arrange
        mock_db = Mock()
        mock_xpath_extractor = Mock()
        executor = Tier2HybridExecutor(
            db=mock_db,
            xpath_extractor=mock_xpath_extractor,
            timeout_ms=5000
        )
        
        # Mock page and element
        mock_page = AsyncMock(spec=Page)
        mock_page.url = "https://example.com/upload"
        mock_element = AsyncMock()
        
        mock_element.wait_for = AsyncMock()
        mock_element.evaluate = AsyncMock(side_effect=["INPUT", "file"])
        mock_element.set_input_files = AsyncMock()
        
        mock_locator = Mock()
        mock_locator.first = mock_element
        mock_page.locator.return_value = mock_locator
        
        # Mock cache service
        executor.cache_service.get_cached_xpath = Mock(return_value={
            "xpath": "//input[@type='file']",
            "page_url": "https://example.com/upload",
            "instruction": "Upload file"
        })
        executor.cache_service.validate_and_update = Mock()
        
        step = {
            "action": "upload_file",
            "instruction": "Upload HKID document",
            "file_path": HKID_FILE
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is True
        assert result["tier"] == 2
        assert result["cache_hit"] is True
        assert result["extraction_time_ms"] == 0  # No extraction needed (cache hit)
        mock_element.set_input_files.assert_called_once_with(HKID_FILE, timeout=5000)
    
    @pytest.mark.asyncio
    async def test_upload_file_with_xpath_extraction(self):
        """Test file upload with XPath extraction in Tier 2."""
        # Arrange
        mock_db = Mock()
        mock_xpath_extractor = AsyncMock()
        executor = Tier2HybridExecutor(
            db=mock_db,
            xpath_extractor=mock_xpath_extractor,
            timeout_ms=5000
        )
        
        # Mock page and element
        mock_page = AsyncMock(spec=Page)
        mock_page.url = "https://example.com/upload"
        mock_element = AsyncMock()
        
        mock_element.wait_for = AsyncMock()
        mock_element.evaluate = AsyncMock(side_effect=["INPUT", "file"])
        mock_element.set_input_files = AsyncMock()
        
        mock_locator = Mock()
        mock_locator.first = mock_element
        mock_page.locator.return_value = mock_locator
        
        # Mock cache service (cache miss)
        executor.cache_service.get_cached_xpath = Mock(return_value=None)
        executor.cache_service.cache_xpath = Mock()
        executor.cache_service.validate_and_update = Mock()
        
        # Mock XPath extraction
        mock_xpath_extractor.extract_xpath_with_page = AsyncMock(return_value={
            "success": True,
            "xpath": "//input[@type='file']",
            "page_title": "Upload Page",
            "element_text": "Choose file"
        })
        
        step = {
            "action": "upload_file",
            "instruction": "Upload HKID document",
            "file_path": HKID_FILE
        }
        
        # Act
        result = await executor.execute_step(mock_page, step)
        
        # Assert
        assert result["success"] is True
        assert result["tier"] == 2
        assert result["cache_hit"] is False
        assert result["extraction_time_ms"] > 0  # Extraction occurred
        mock_xpath_extractor.extract_xpath_with_page.assert_called_once()
        executor.cache_service.cache_xpath.assert_called_once()
        mock_element.set_input_files.assert_called_once_with(HKID_FILE, timeout=5000)


class TestTier3FileUpload:
    """Test Tier 3 (Stagehand Full AI) file upload handler."""
    
    @pytest.mark.asyncio
    async def test_upload_file_with_ai_act(self):
        """Test file upload using Stagehand AI act() in Tier 3."""
        # Arrange
        mock_stagehand = Mock()
        mock_stagehand.page = AsyncMock()
        mock_stagehand.page.act = AsyncMock(return_value={"success": True})
        
        executor = Tier3StagehandExecutor(
            stagehand=mock_stagehand,
            timeout_ms=5000
        )
        
        step = {
            "action": "upload_file",
            "instruction": "Upload HKID document",
            "file_path": HKID_FILE
        }
        
        # Act
        result = await executor.execute_step(step)
        
        # Assert
        assert result["success"] is True
        assert result["tier"] == 3
        assert result["error"] is None
        mock_stagehand.page.act.assert_called_once()
        call_args = mock_stagehand.page.act.call_args[0][0]
        assert "Upload HKID document" in call_args
        assert HKID_FILE in call_args
    
    @pytest.mark.asyncio
    async def test_upload_file_with_fallback(self):
        """Test file upload falls back to programmatic method when AI fails."""
        # Arrange
        mock_stagehand = Mock()
        mock_stagehand.page = AsyncMock()
        
        # AI act() fails
        mock_stagehand.page.act = AsyncMock(side_effect=Exception("AI act failed"))
        
        # Mock file input element for fallback
        mock_element = AsyncMock()
        mock_element.wait_for = AsyncMock()
        mock_element.set_input_files = AsyncMock()
        
        # Mock locator chain properly
        mock_locator = Mock()
        mock_locator.first = mock_element  # .first is a property, not a method
        
        # The locator() call should return the mock_locator
        mock_stagehand.page.locator = Mock(return_value=mock_locator)
        
        executor = Tier3StagehandExecutor(
            stagehand=mock_stagehand,
            timeout_ms=5000
        )
        
        step = {
            "action": "upload_file",
            "instruction": "Upload passport photo",
            "file_path": PASSPORT_FILE
        }
        
        # Act
        result = await executor.execute_step(step)
        
        # Assert
        assert result["success"] is True
        assert result["tier"] == 3
        mock_stagehand.page.act.assert_called_once()  # Tried AI first
        mock_element.set_input_files.assert_called_once_with(PASSPORT_FILE, timeout=5000)  # Fallback used
    
    @pytest.mark.asyncio
    async def test_upload_file_missing_path(self):
        """Test file upload fails when file_path is missing in Tier 3."""
        # Arrange
        mock_stagehand = Mock()
        mock_stagehand.page = AsyncMock()
        
        executor = Tier3StagehandExecutor(
            stagehand=mock_stagehand,
            timeout_ms=5000
        )
        
        step = {
            "action": "upload_file",
            "instruction": "Upload document"
            # Missing file_path
        }
        
        # Act
        result = await executor.execute_step(step)
        
        # Assert
        assert result["success"] is False
        assert "file_path" in result["error"].lower()


class TestFileValidation:
    """Test file validation across all tiers."""
    
    def test_all_test_files_exist(self):
        """Verify all test files exist in the repository."""
        assert os.path.exists(TEST_FILES_DIR), f"Test files directory not found: {TEST_FILES_DIR}"
        assert os.path.exists(HKID_FILE), f"HKID sample file not found: {HKID_FILE}"
        assert os.path.exists(PASSPORT_FILE), f"Passport sample file not found: {PASSPORT_FILE}"
        assert os.path.exists(ADDRESS_FILE), f"Address proof file not found: {ADDRESS_FILE}"
    
    def test_test_files_are_readable(self):
        """Verify all test files are readable."""
        with open(HKID_FILE, 'rb') as f:
            content = f.read()
            assert len(content) > 0, "HKID file is empty"
        
        with open(PASSPORT_FILE, 'rb') as f:
            content = f.read()
            assert len(content) > 0, "Passport file is empty"
        
        with open(ADDRESS_FILE, 'rb') as f:
            content = f.read()
            assert len(content) > 0, "Address file is empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
