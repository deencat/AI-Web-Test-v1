"""Tests for ExecutionService integration with 3-tier tier logging."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.execution_service import ExecutionConfig, ExecutionService


def _build_service_with_mocked_three_tier() -> ExecutionService:
    service = ExecutionService(ExecutionConfig())
    service.three_tier_service = MagicMock()
    service.three_tier_service.execute_step = AsyncMock(
        return_value={
            "success": True,
            "tier": 2,
            "execution_time_ms": 123,
            "strategy_used": "option_c",
        }
    )
    service._apply_test_data_generation = MagicMock(side_effect=lambda step, _: step)
    service._substitute_test_data_patterns = MagicMock(side_effect=lambda text, _: text)
    return service


@pytest.mark.asyncio
async def test_execute_step_passes_execution_id_to_three_tier_service():
    service = _build_service_with_mocked_three_tier()

    result = await service._execute_step(
        page=MagicMock(),
        step_description="Step 4: Click the 'Login' button on popup to proceed to the password input page",
        step_number=4,
        base_url="https://example.com",
        detailed_step={
            "action": "click",
            "selector": "#login",
            "value": "",
            "file_path": "",
        },
        execution_id=637,
    )

    assert result["success"] is True
    service.three_tier_service.execute_step.assert_awaited_once_with(
        step={
            "action": "click",
            "selector": "#login",
            "value": "",
            "file_path": "",
            "instruction": "Step 4: Click the 'Login' button on popup to proceed to the password input page",
        },
        execution_id=637,
        step_index=3,
    )


@pytest.mark.asyncio
async def test_execute_step_extracts_windows_upload_path_from_step_description():
    service = _build_service_with_mocked_three_tier()
    expected_path = "C:\\old_Drive\\RNR\\test_RNR\\HKID-Sample-Blank-66.jpeg"

    result = await service._execute_step(
        page=MagicMock(),
        step_description=(
            "Upload the HKID document from the local file system "
            f"{expected_path}"
        ),
        step_number=7,
        base_url="https://example.com",
        detailed_step=None,
    )

    assert result["success"] is True
    service.three_tier_service.execute_step.assert_awaited_once_with(
        step={
            "action": "upload_file",
            "selector": "input[type='file']",
            "value": None,
            "file_path": expected_path,
            "instruction": (
                "Upload the HKID document from the local file system "
                f"{expected_path}"
            ),
        },
        execution_id=None,
        step_index=6,
    )


@pytest.mark.asyncio
async def test_execute_step_extracts_quoted_windows_upload_path_with_spaces():
    service = _build_service_with_mocked_three_tier()
    expected_path = "C:\\Test User\\My Documents\\passport sample.jpg"

    result = await service._execute_step(
        page=MagicMock(),
        step_description=f'Upload the passport image from "{expected_path}".',
        step_number=8,
        base_url="https://example.com",
        detailed_step=None,
    )

    assert result["success"] is True
    service.three_tier_service.execute_step.assert_awaited_once_with(
        step={
            "action": "upload_file",
            "selector": "input[type='file']",
            "value": None,
            "file_path": expected_path,
            "instruction": f'Upload the passport image from "{expected_path}".',
        },
        execution_id=None,
        step_index=7,
    )


@pytest.mark.asyncio
async def test_execute_step_preserves_posix_upload_path_from_step_description():
    service = _build_service_with_mocked_three_tier()
    expected_path = "/app/test_files/hkid_sample.pdf"

    result = await service._execute_step(
        page=MagicMock(),
        step_description=f"Upload the HKID document from {expected_path}",
        step_number=9,
        base_url="https://example.com",
        detailed_step=None,
    )

    assert result["success"] is True
    service.three_tier_service.execute_step.assert_awaited_once_with(
        step={
            "action": "upload_file",
            "selector": "input[type='file']",
            "value": None,
            "file_path": expected_path,
            "instruction": f"Upload the HKID document from {expected_path}",
        },
        execution_id=None,
        step_index=8,
    )