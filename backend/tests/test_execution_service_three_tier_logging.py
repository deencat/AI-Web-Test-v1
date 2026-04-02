"""Tests for ExecutionService integration with 3-tier tier logging."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.execution_service import ExecutionConfig, ExecutionService


@pytest.mark.asyncio
async def test_execute_step_passes_execution_id_to_three_tier_service():
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