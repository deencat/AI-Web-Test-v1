"""Tests for Three HK registration widget handlers (Exec #990 fixes)."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier2_hybrid import Tier2HybridExecutor


class TestDropdownInstructionHelpers:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_parse_date_value_slash_format(self):
        assert self.executor._parse_date_value("2000/01/01") == (2000, 1, 1)

    def test_parse_date_value_dash_format(self):
        assert self.executor._parse_date_value("2000-01-01") == (2000, 1, 1)

    def test_normalize_date_for_compare(self):
        assert self.executor._normalize_date_for_compare("2000/01/01") == "2000-01-01"

    def test_is_date_instruction_birth_date(self):
        assert self.executor._is_date_instruction("Enter birth date 2000/01/01", "2000/01/01") is True

    def test_extract_click_anchor_phrases_quoted(self):
        instruction = "Click the eye icon next to 'Collect Personal Info:'"
        assert self.executor._extract_click_anchor_phrases(instruction) == ["Collect Personal Info:"]

    def test_augment_observe_instruction_with_anchors(self):
        instruction = "Click the eye icon next to 'Collect Personal Info:'"
        augmented = self.executor._augment_observe_instruction_with_anchors(instruction)
        assert "Collect Personal Info" in augmented
        assert "NOT header/nav" in augmented


class TestCustomDropdownSelect:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    @pytest.mark.asyncio
    async def test_custom_dropdown_select_two_phase(self):
        page = MagicMock()

        trigger = AsyncMock()
        trigger.wait_for = AsyncMock(return_value=None)
        trigger.evaluate = AsyncMock(return_value="div")
        trigger.click = AsyncMock(return_value=None)
        trigger.inner_text = AsyncMock(return_value="Hong Kong")

        trigger_locator = MagicMock()
        trigger_locator.first = trigger

        listbox = AsyncMock()
        listbox.wait_for = AsyncMock(return_value=None)
        listbox_locator = MagicMock()
        listbox_locator.first = listbox

        option = AsyncMock()
        option.click = AsyncMock(return_value=None)
        option_locator = MagicMock()
        option_locator.count = AsyncMock(return_value=1)
        option_locator.first = option

        def locator_side_effect(selector):
            if selector.startswith("xpath="):
                return trigger_locator
            if selector == "[role='listbox']":
                return listbox_locator
            return MagicMock(first=MagicMock())

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_role = MagicMock(return_value=option_locator)
        page.get_by_text = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = await self.executor._try_custom_dropdown_select(
            page,
            "select area 'Hong Kong'",
            "Hong Kong",
            "//div[@class='area-trigger']",
        )

        assert result is True
        trigger.click.assert_awaited_once()
        option.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_custom_dropdown_falls_back_for_native_select(self):
        page = MagicMock()

        trigger = AsyncMock()
        trigger.wait_for = AsyncMock(return_value=None)
        trigger.evaluate = AsyncMock(return_value="select")

        trigger_locator = MagicMock()
        trigger_locator.first = trigger
        page.locator = MagicMock(return_value=trigger_locator)

        result = await self.executor._try_custom_dropdown_select(
            page,
            "Select region",
            "Hong Kong",
            "//select[@id='region']",
        )

        assert result is False
        trigger.click.assert_not_awaited()


class TestDatePickerFill:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    @pytest.mark.asyncio
    async def test_fill_date_picker_verifies_persisted_value(self):
        page = MagicMock()
        locator = AsyncMock()
        locator.wait_for = AsyncMock(return_value=None)
        locator.click = AsyncMock(return_value=None)
        locator.fill = AsyncMock(return_value=None)
        locator.press = AsyncMock(return_value=None)
        locator.evaluate = AsyncMock(return_value=None)
        locator.input_value = AsyncMock(return_value="2000/01/01")

        self.executor._navigate_date_picker_to = AsyncMock(return_value=None)
        self.executor._read_date_picker_header_month_year = AsyncMock(return_value=(2000, 1))

        day_cell = AsyncMock()
        day_cell.inner_text = AsyncMock(return_value="1")
        day_cell.click = AsyncMock(return_value=None)
        day_group = MagicMock()
        day_group.count = AsyncMock(return_value=1)
        day_group.nth = MagicMock(return_value=day_cell)
        page.get_by_role = MagicMock(return_value=day_group)
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = await self.executor._fill_date_picker_field(locator, "2000/01/01", page)

        assert result is True
        day_cell.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fill_date_picker_rejects_wrong_calendar_month(self):
        page = MagicMock()
        locator = AsyncMock()
        locator.wait_for = AsyncMock(return_value=None)
        locator.click = AsyncMock(return_value=None)
        locator.fill = AsyncMock(return_value=None)
        locator.press = AsyncMock(return_value=None)
        locator.evaluate = AsyncMock(return_value=None)
        locator.input_value = AsyncMock(return_value="2000/01/01")

        self.executor._navigate_date_picker_to = AsyncMock(return_value=None)
        self.executor._read_date_picker_header_month_year = AsyncMock(return_value=(2026, 6))

        day_cell = AsyncMock()
        day_cell.inner_text = AsyncMock(return_value="1")
        day_cell.click = AsyncMock(return_value=None)
        day_group = MagicMock()
        day_group.count = AsyncMock(return_value=1)
        day_group.nth = MagicMock(return_value=day_cell)
        page.get_by_role = MagicMock(return_value=day_group)
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = await self.executor._fill_date_picker_field(locator, "2000/01/01", page)

        assert result is False


class TestClickAnchorValidation:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    @pytest.mark.asyncio
    async def test_validate_click_rejects_header_target_for_main_anchor(self):
        page = MagicMock()
        locator = AsyncMock()

        anchor_locator = AsyncMock()
        anchor_locator.count = AsyncMock(return_value=1)
        anchor_locator.is_visible = AsyncMock(return_value=True)
        page.get_by_text = MagicMock(return_value=MagicMock(first=anchor_locator))

        self.executor._element_in_header_or_nav = AsyncMock(return_value=True)
        self.executor._anchor_text_in_main_content = AsyncMock(return_value=True)

        instruction = "Click the eye icon next to 'Collect Personal Info:'"
        result = await self.executor._validate_click_target_for_instruction(
            page,
            locator,
            instruction,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_click_accepts_proximate_target(self):
        page = MagicMock()
        locator = AsyncMock()
        locator.bounding_box = AsyncMock(return_value={"x": 100, "y": 200, "width": 20, "height": 20})

        anchor_locator = AsyncMock()
        anchor_locator.count = AsyncMock(return_value=1)
        anchor_locator.is_visible = AsyncMock(return_value=True)
        anchor_locator.bounding_box = AsyncMock(return_value={"x": 150, "y": 210, "width": 200, "height": 20})
        page.get_by_text = MagicMock(return_value=MagicMock(first=anchor_locator))

        self.executor._element_in_header_or_nav = AsyncMock(return_value=False)
        self.executor._anchor_text_in_main_content = AsyncMock(return_value=True)

        instruction = "Click the eye icon next to 'Collect Personal Info:'"
        result = await self.executor._validate_click_target_for_instruction(
            page,
            locator,
            instruction,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_action_with_xpath_rejects_bad_click_target(self):
        page = MagicMock()
        element = AsyncMock()
        element.wait_for = AsyncMock(return_value=None)

        locator = MagicMock()
        locator.first = element
        page.locator = MagicMock(return_value=locator)

        self.executor._validate_click_target_for_instruction = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="anchor validation"):
            await self.executor._execute_action_with_xpath(
                page,
                "click",
                "//button[@id='hamburger']",
                "",
                "Click the eye icon next to 'Collect Personal Info:'",
            )

    @pytest.mark.asyncio
    async def test_validate_cached_xpath_rejects_bad_click_anchor(self):
        page = MagicMock()
        element = AsyncMock()
        locator = MagicMock()
        locator.first = element
        locator.wait_for = AsyncMock(return_value=None)
        page.locator = MagicMock(return_value=locator)

        self.executor._validate_click_target_for_instruction = AsyncMock(return_value=False)

        result = await self.executor._validate_cached_xpath_for_step(
            page=page,
            xpath="//button[@id='nav-toggle']",
            action="click",
            instruction="Click the eye icon next to 'Collect Personal Info:'",
            value=None,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_step_augments_observe_after_anchor_cache_rejection(self):
        page = MagicMock()
        page.url = "https://www.three.com.hk/register"

        self.executor.cache_service.get_cached_xpath = MagicMock(
            return_value={"xpath": "//button[@id='nav-toggle']"}
        )
        self.executor.cache_service.invalidate_cache = MagicMock()
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor._validate_cached_xpath_for_step = AsyncMock(return_value=False)
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._maybe_wait_for_payment_gateway = AsyncMock(return_value=None)

        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(
            return_value={
                "success": True,
                "xpath": "//button[@class='eye-icon']",
                "page_title": "Register",
                "element_text": "eye",
            }
        )

        instruction = "Click the eye icon next to 'Collect Personal Info:'"
        result = await self.executor.execute_step(
            page,
            {
                "action": "click",
                "instruction": instruction,
                "value": None,
            },
        )

        assert result["success"] is True
        observe_instruction = self.executor.xpath_extractor.extract_xpath_with_page.await_args.kwargs[
            "instruction"
        ]
        assert "Collect Personal Info" in observe_instruction
        assert "NOT header/nav" in observe_instruction
        self.executor.cache_service.invalidate_cache.assert_called_once()
