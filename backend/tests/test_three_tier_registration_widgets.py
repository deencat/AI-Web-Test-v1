"""3-tier integration tests for Exec #990 registration widget handlers.

Routes through ThreeTierExecutionService (Tier 1 miss → Tier 2 handlers)
to verify dispatch, tier assignment, and Tier 3 escalation boundaries.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.models.execution_settings import ExecutionSettings
from app.services.three_tier_execution_service import ThreeTierExecutionService
from app.services.tier2_hybrid import Tier2HybridExecutor


def _make_settings(strategy: str = "option_c", timeout_seconds: int = 30) -> ExecutionSettings:
    settings = ExecutionSettings()
    settings.fallback_strategy = strategy
    settings.timeout_per_tier_seconds = timeout_seconds
    settings.track_strategy_effectiveness = True
    return settings


def _make_three_tier_service() -> ThreeTierExecutionService:
    page = MagicMock()
    page.url = "https://ogp-ppd.example.com/register"
    service = ThreeTierExecutionService(
        db=MagicMock(),
        page=page,
        user_settings=_make_settings(),
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
    service.tier3_executor = MagicMock()
    service.tier3_executor.execute_step = AsyncMock(
        return_value={
            "success": False,
            "tier": 3,
            "execution_time_ms": 10,
            "error": "tier3 should not run",
            "error_type": "ValueError",
        }
    )
    service._ensure_tier3_initialized = AsyncMock(return_value=None)
    return service


def _wire_real_tier2(service: ThreeTierExecutionService) -> Tier2HybridExecutor:
    tier2 = Tier2HybridExecutor(
        db=MagicMock(),
        xpath_extractor=MagicMock(),
        timeout_ms=30000,
    )
    tier2.cache_service.get_cached_xpath = MagicMock(return_value=None)
    tier2.cache_service.cache_xpath = MagicMock()
    tier2.cache_service.validate_and_update = MagicMock()
    tier2._wait_for_page_interactable_for_observe = AsyncMock(return_value=None)
    service.tier2_executor = tier2
    service._ensure_tier2_initialized = AsyncMock(return_value=None)
    return tier2


@pytest.mark.asyncio
async def test_tier1_miss_routes_to_tier2_custom_dropdown_without_tier3():
    """Tier 1 miss → Tier 2 custom dropdown path; Tier 3 not invoked on success."""
    service = _make_three_tier_service()
    tier2 = _wire_real_tier2(service)

    tier2.xpath_extractor.extract_xpath_with_page = AsyncMock(
        return_value={
            "success": True,
            "xpath": "//div[@class='area-trigger']",
            "page_title": "Register",
            "element_text": "Select an Area",
        }
    )
    tier2._try_custom_dropdown_select = AsyncMock(return_value=True)

    element = AsyncMock()
    element.wait_for = AsyncMock(return_value=None)
    element_locator = MagicMock()
    element_locator.first = element
    service.page.locator = MagicMock(return_value=element_locator)

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ):
        result = await service.execute_step(
            {
                "action": "select",
                "instruction": "select area 'Hong Kong'",
                "value": "Hong Kong",
            },
            execution_id=990,
            step_index=35,
        )

    assert result["success"] is True
    assert result["tier"] == 2
    tier2._try_custom_dropdown_select.assert_awaited_once()
    service.tier3_executor.execute_step.assert_not_awaited()


@pytest.mark.asyncio
async def test_tier1_miss_routes_to_tier2_date_picker_without_tier3():
    """Tier 1 miss → Tier 2 date picker fill path; Tier 3 not invoked on success."""
    service = _make_three_tier_service()
    tier2 = _wire_real_tier2(service)

    tier2.xpath_extractor.extract_xpath_with_page = AsyncMock(
        return_value={
            "success": True,
            "xpath": "//input[@id='birth-date']",
            "page_title": "Register",
            "element_text": "",
        }
    )
    tier2._fill_date_picker_field = AsyncMock(return_value=True)

    element = AsyncMock()
    element.wait_for = AsyncMock(return_value=None)
    element_locator = MagicMock()
    element_locator.first = element
    service.page.locator = MagicMock(return_value=element_locator)

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ):
        result = await service.execute_step(
            {
                "action": "fill",
                "instruction": "Input birth date 2000/01/01",
                "value": "2000/01/01",
            },
            execution_id=990,
            step_index=23,
        )

    assert result["success"] is True
    assert result["tier"] == 2
    tier2._fill_date_picker_field.assert_awaited_once()
    service.tier3_executor.execute_step.assert_not_awaited()


@pytest.mark.asyncio
async def test_tier1_miss_anchor_cache_invalidation_retries_observe_before_success():
    """Tier 1 miss → cached anchor rejected → observe augmented retry → Tier 2 success."""
    service = _make_three_tier_service()
    tier2 = _wire_real_tier2(service)

    tier2.cache_service.get_cached_xpath = MagicMock(
        return_value={"xpath": "//button[@id='nav-toggle']"}
    )
    tier2.cache_service.invalidate_cache = MagicMock()
    tier2._validate_cached_xpath_for_step = AsyncMock(return_value=False)
    tier2._execute_action_with_xpath = AsyncMock(return_value=None)

    tier2.xpath_extractor.extract_xpath_with_page = AsyncMock(
        return_value={
            "success": True,
            "xpath": "//button[@class='eye-icon']",
            "page_title": "Register",
            "element_text": "eye",
        }
    )

    instruction = "Click the eye icon next to 'Collect Personal Info:'"

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ):
        result = await service.execute_step(
            {
                "action": "click",
                "instruction": instruction,
                "value": None,
            },
            execution_id=990,
            step_index=14,
        )

    assert result["success"] is True
    assert result["tier"] == 2
    tier2.cache_service.invalidate_cache.assert_called_once()
    observe_instruction = tier2.xpath_extractor.extract_xpath_with_page.await_args.kwargs[
        "instruction"
    ]
    assert "Collect Personal Info" in observe_instruction
    assert "NOT header/nav" in observe_instruction
    service.tier3_executor.execute_step.assert_not_awaited()


@pytest.mark.asyncio
async def test_tier2_widget_verification_failure_escalates_to_tier3_option_c():
    """Tier 2 verification failure escalates to Tier 3 under option_c cascade."""
    service = _make_three_tier_service()
    tier2 = _wire_real_tier2(service)

    tier2.execute_step = AsyncMock(
        return_value={
            "success": False,
            "tier": 2,
            "execution_time_ms": 20,
            "error": "Date picker fill did not persist for step: Input birth date 2000/01/01",
            "error_type": "ValueError",
        }
    )
    service.tier3_executor.execute_step = AsyncMock(
        return_value={
            "success": True,
            "tier": 3,
            "execution_time_ms": 50,
            "error": None,
        }
    )

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ):
        result = await service.execute_step(
            {
                "action": "fill",
                "instruction": "Input birth date 2000/01/01",
                "value": "2000/01/01",
            },
            execution_id=990,
            step_index=23,
        )

    assert result["success"] is True
    assert result["tier"] == 3
    service.tier3_executor.execute_step.assert_awaited_once()
    tier2.execute_step.assert_awaited_once()


@pytest.mark.asyncio
async def test_tier2_widget_verification_failure_does_not_false_pass_without_tier3():
    """When Tier 2 and Tier 3 both fail verification, step fails without false PASS."""
    service = _make_three_tier_service()
    tier2 = _wire_real_tier2(service)

    tier2.execute_step = AsyncMock(
        return_value={
            "success": False,
            "tier": 2,
            "execution_time_ms": 20,
            "error": "Custom dropdown verification failed: expected 'Hong Kong'",
            "error_type": "ValueError",
        }
    )
    service.tier3_executor.execute_step = AsyncMock(
        return_value={
            "success": False,
            "tier": 3,
            "execution_time_ms": 50,
            "error": "Could not select area",
            "error_type": "ValueError",
        }
    )

    with patch(
        "app.services.three_tier_execution_service.wait_for_step_boundary_readiness",
        AsyncMock(return_value=None),
    ):
        result = await service.execute_step(
            {
                "action": "select",
                "instruction": "select area 'Hong Kong'",
                "value": "Hong Kong",
            },
            execution_id=990,
            step_index=35,
        )

    assert result["success"] is False
    assert result["error_type"] == "all_tiers_exhausted"
    service.tier3_executor.execute_step.assert_awaited_once()
    assert all(entry["success"] is False for entry in result["execution_history"] if entry["tier"] in (2, 3))


@pytest.mark.asyncio
async def test_execution_service_dispatches_registration_step_to_three_tier():
    """ExecutionService routes step execution through ThreeTierExecutionService."""
    from app.services.execution_service import ExecutionService, ExecutionConfig

    service = ExecutionService(ExecutionConfig())
    service.three_tier_service = MagicMock()
    service.three_tier_service.execute_step = AsyncMock(
        return_value={
            "success": True,
            "tier": 2,
            "execution_time_ms": 15,
            "error": None,
            "total_time_ms": 20,
            "execution_history": [],
            "strategy_used": "option_c",
        }
    )

    page = MagicMock()
    result = await service._execute_step(
        page=page,
        step_description="select area 'Hong Kong'",
        step_number=35,
        base_url="https://ogp-ppd.example.com",
        detailed_step=None,
        execution_id=990,
    )

    assert result["success"] is True
    service.three_tier_service.execute_step.assert_awaited_once()
    call_kwargs = service.three_tier_service.execute_step.await_args.kwargs
    assert call_kwargs["execution_id"] == 990
    assert call_kwargs["step_index"] == 34
    assert call_kwargs["step"]["action"] == "select"
    assert call_kwargs["step"]["value"] == "Hong Kong"
