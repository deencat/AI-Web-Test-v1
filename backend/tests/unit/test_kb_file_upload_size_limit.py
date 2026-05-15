"""
Unit tests for KB FileUploadService file size limit (ADR-005).

Verifies that the upload limit is 25 MB and that boundary conditions
at and around that limit behave correctly.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from io import BytesIO

from app.services.file_upload import FileUploadService


MB = 1024 * 1024
EXPECTED_MAX_MB = 25
EXPECTED_MAX_BYTES = EXPECTED_MAX_MB * MB


def _make_upload_file(size_bytes: int, filename: str = "test.pdf") -> MagicMock:
    """Return a mock UploadFile whose read() returns `size_bytes` bytes."""
    mock = MagicMock()
    mock.filename = filename
    content = b"x" * size_bytes
    mock.read = AsyncMock(return_value=content)
    mock.seek = AsyncMock()
    return mock


class TestFileUploadServiceMaxSize:
    """Verify the max_size constant on FileUploadService."""

    def test_max_size_is_25mb(self):
        service = FileUploadService()
        assert service.max_size == EXPECTED_MAX_BYTES, (
            f"Expected max_size to be {EXPECTED_MAX_BYTES} bytes (25 MB), "
            f"got {service.max_size} bytes ({service.max_size / MB:.1f} MB)"
        )

    def test_max_size_greater_than_10mb(self):
        """Regression: must be strictly above the old 10 MB ceiling."""
        service = FileUploadService()
        assert service.max_size > 10 * MB


class TestFileUploadValidationBoundary:
    """Boundary tests around the 25 MB limit."""

    @pytest.mark.asyncio
    async def test_file_at_exact_limit_passes(self):
        """A file of exactly 25 MB must be accepted."""
        service = FileUploadService()
        mock_file = _make_upload_file(EXPECTED_MAX_BYTES, "boundary.pdf")

        # Should not raise
        file_type, file_size = await service._validate_file(mock_file)
        assert file_size == EXPECTED_MAX_BYTES

    @pytest.mark.asyncio
    async def test_file_one_byte_over_limit_raises(self):
        """A file 1 byte above 25 MB must raise HTTPException 400."""
        from fastapi import HTTPException

        service = FileUploadService()
        mock_file = _make_upload_file(EXPECTED_MAX_BYTES + 1, "too_big.pdf")

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert "25.0MB" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_file_just_under_limit_passes(self):
        """A file 1 byte below 25 MB must be accepted."""
        service = FileUploadService()
        mock_file = _make_upload_file(EXPECTED_MAX_BYTES - 1, "under_limit.pdf")

        file_type, file_size = await service._validate_file(mock_file)
        assert file_size == EXPECTED_MAX_BYTES - 1

    @pytest.mark.asyncio
    async def test_old_11mb_file_now_passes(self):
        """A file that was previously rejected at 10 MB (11 MB) must now pass."""
        service = FileUploadService()
        mock_file = _make_upload_file(11 * MB, "was_rejected.pdf")

        file_type, file_size = await service._validate_file(mock_file)
        assert file_size == 11 * MB

    @pytest.mark.asyncio
    async def test_error_message_states_correct_limit(self):
        """Error detail must reference the new 25 MB limit, not the old 10 MB."""
        from fastapi import HTTPException

        service = FileUploadService()
        mock_file = _make_upload_file(EXPECTED_MAX_BYTES + 1, "too_big.pdf")

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(mock_file)

        detail = exc_info.value.detail
        assert "10.0MB" not in detail, "Error message still references old 10 MB limit"
        assert "25.0MB" in detail
