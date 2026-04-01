"""Unit tests for 3-tier orchestration behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.execution_settings import ExecutionSettings
from app.services.three_tier_execution_service import ThreeTierExecutionService


def _make_settings(strategy: str = "option_c", timeout_seconds: int = 30) -> ExecutionSettings:
    settings = ExecutionSettings()
    settings.fallback_strategy = strategy
    settings.timeout_per_tier_seconds = timeout_seconds
    settings.track_strategy_effectiveness = True
    return settings


@pytest.mark.asyncio
async def test_execute_step_waits_for_step_boundary_readiness_before_tier1():
    service = ThreeTierExecutionService(
        db=MagicMock(),
        page=MagicMock(),
        user_settings=_make_settings(),
    )

    calls = []

    async def wait_side_effect(page, timeout_ms, logger):
        calls.append(("wait", timeout_ms))

    async def tier1_side_effect(page, step):
        calls.append(("tier1", step["instruction"]))
        return {
            "success": True,
            "tier": 1,
            "execution_time_ms": 5,
            "error": None,
        }

    service.tier1_executor.execute_step = AsyncMock(side_effect=tier1_side_effect)

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(side_effect=wait_side_effect),
    ) as wait_mock:
        result = await service.execute_step(
            {
                "action": "click",
                "selector": "#submit",
                "instruction": "Click the submit button",
            }
        )

    assert result["success"] is True
    assert calls == [
        ("wait", 30000),
        ("tier1", "Click the submit button"),
    ]
    wait_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_step_waits_once_before_fallbacks():
    service = ThreeTierExecutionService(
        db=MagicMock(),
        page=MagicMock(),
        user_settings=_make_settings(strategy="option_c"),
    )

    service.tier1_executor.execute_step = AsyncMock(
        return_value={
            "success": False,
            "tier": 1,
            "execution_time_ms": 5,
            "error": "selector not found",
            "error_type": "ValueError",
        }
    )
    service.tier2_executor = MagicMock()
    service.tier2_executor.execute_step = AsyncMock(
        return_value={
            "success": True,
            "tier": 2,
            "execution_time_ms": 12,
            "error": None,
        }
    )
    service._ensure_tier2_initialized = AsyncMock(return_value=None)

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ) as wait_mock:
        result = await service.execute_step(
            {
                "action": "click",
                "selector": "#missing",
                "instruction": "Click the missing button",
            }
        )

    assert result["success"] is True
    assert result["tier"] == 2
    wait_mock.assert_awaited_once()