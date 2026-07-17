"""
Unit tests for Feature 5: Signature Pad Ink Verification.

Covers shared helper (locate / stroke / verify), Tier 3 soft-act false-success
path (#1120/#1122), and Sprint 13 click-vs-draw action detection.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.signature_pad import (
    SignResult,
    draw_signature_stroke,
    infer_signature_step_action,
    is_soft_act_method,
    locate_signature_canvas,
    sign_canvas,
    verify_signature_ink,
)
from app.services.tier3_stagehand import Tier3StagehandExecutor


# ---------------------------------------------------------------------------
# Soft-act method helpers
# ---------------------------------------------------------------------------


class TestSoftActMethods:
    def test_scrollintoview_is_soft(self):
        assert is_soft_act_method("scrollIntoView") is True
        assert is_soft_act_method("scroll_into_view") is True
        assert is_soft_act_method("scroll") is True

    def test_locator_focus_are_soft(self):
        assert is_soft_act_method("locator") is True
        assert is_soft_act_method("focus") is True
        assert is_soft_act_method("highlight") is True

    def test_draw_like_not_soft(self):
        assert is_soft_act_method("click") is False
        assert is_soft_act_method("type") is False
        assert is_soft_act_method(None) is False


# ---------------------------------------------------------------------------
# Action detection (Sprint 13)
# ---------------------------------------------------------------------------


class TestInferSignatureStepAction:
    def test_click_signature_is_click(self):
        assert (
            infer_signature_step_action("Click the Signature button") == "click"
        )

    def test_click_signature_short(self):
        assert infer_signature_step_action("Click Signature") == "click"

    def test_open_signature_pad_is_click(self):
        assert infer_signature_step_action("Open the signature pad") == "click"

    def test_complete_the_signature_is_draw(self):
        assert (
            infer_signature_step_action("Complete the signature")
            == "draw_signature"
        )

    def test_please_sign_alone_is_draw(self):
        assert infer_signature_step_action("Please sign") == "draw_signature"

    def test_click_and_sign_is_draw(self):
        # Has click + sign but is not "Click Signature button"
        assert infer_signature_step_action("Click and sign") == "draw_signature"

    def test_sign_under_is_draw(self):
        assert (
            infer_signature_step_action('Sign under "Please sign here"')
            == "draw_signature"
        )

    def test_sign_it_is_draw(self):
        assert infer_signature_step_action("Sign it") == "draw_signature"

    def test_draw_signature_is_draw(self):
        assert infer_signature_step_action("Draw signature") == "draw_signature"

    def test_sign_here_is_draw(self):
        assert (
            infer_signature_step_action("Please sign here on the pad")
            == "draw_signature"
        )

    def test_unrelated_is_none(self):
        assert infer_signature_step_action("Click Login") is None
        assert infer_signature_step_action("Fill email") is None
        assert infer_signature_step_action("") is None


# ---------------------------------------------------------------------------
# Ink verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_ink_empty_fails():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(
        return_value={"source": "pixels", "empty": True}
    )
    assert await verify_signature_ink(MagicMock(), canvas) is False


@pytest.mark.asyncio
async def test_verify_ink_after_stroke_passes():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(
        return_value={"source": "pixels", "empty": False}
    )
    assert await verify_signature_ink(MagicMock(), canvas) is True


@pytest.mark.asyncio
async def test_signaturepad_isempty_false():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(
        return_value={"source": "signaturepad", "empty": False}
    )
    assert await verify_signature_ink(MagicMock(), canvas) is True


@pytest.mark.asyncio
async def test_signaturepad_isempty_true_fails():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(
        return_value={"source": "signaturepad", "empty": True}
    )
    assert await verify_signature_ink(MagicMock(), canvas) is False


@pytest.mark.asyncio
async def test_verify_ink_evaluate_exception_fails():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(side_effect=RuntimeError("boom"))
    assert await verify_signature_ink(MagicMock(), canvas) is False


# ---------------------------------------------------------------------------
# Locate heuristics
# ---------------------------------------------------------------------------


def _mock_locator(count=1, visible=True):
    loc = AsyncMock()
    loc.count = AsyncMock(return_value=count)
    loc.is_visible = AsyncMock(return_value=visible)
    loc.first = loc
    return loc


@pytest.mark.asyncio
async def test_locate_via_signature_selector():
    page = MagicMock()
    canvas_loc = _mock_locator()

    def locator_side_effect(sel, **kwargs):
        loc = _mock_locator(count=0)
        if "signature" in str(sel).lower() or sel == "canvas.signature-pad":
            return canvas_loc
        return loc

    page.locator = MagicMock(side_effect=locator_side_effect)
    # First selector is canvas.signature-pad
    canvas_loc.count = AsyncMock(return_value=1)
    canvas_loc.is_visible = AsyncMock(return_value=True)

    found = await locate_signature_canvas(page)
    assert found is canvas_loc


@pytest.mark.asyncio
async def test_locate_via_xpath():
    page = MagicMock()
    canvas_loc = _mock_locator()
    page.locator = MagicMock(return_value=canvas_loc)

    found = await locate_signature_canvas(page, xpath="//canvas[@id='sig']")
    assert found is canvas_loc
    page.locator.assert_called_with("xpath=//canvas[@id='sig']")


@pytest.mark.asyncio
async def test_locate_largest_visible_canvas():
    page = AsyncMock()
    # All named selectors miss
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)
    page.evaluate_handle = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value=0)  # largest index

    largest = _mock_locator(count=1)
    # nth() returns largest
    miss.nth = MagicMock(return_value=largest)
    page.locator = MagicMock(return_value=miss)

    found = await locate_signature_canvas(page, instruction="sign it")
    assert found is largest


@pytest.mark.asyncio
async def test_locate_near_please_sign_here():
    """Near-label path: evaluate_handle returns element; index resolves to canvas."""
    page = AsyncMock()
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)

    handle = MagicMock()
    element = MagicMock()
    handle.as_element = MagicMock(return_value=element)
    page.evaluate_handle = AsyncMock(return_value=handle)
    page.evaluate = AsyncMock(return_value=0)

    near = _mock_locator(count=1)
    miss.nth = MagicMock(return_value=near)

    found = await locate_signature_canvas(
        page, instruction='Sign under "CustomPadLabelXYZ"'
    )
    assert found is near
    # Quoted phrase should be tried first via evaluate_handle
    assert page.evaluate_handle.await_count >= 1


@pytest.mark.asyncio
async def test_locate_raises_when_no_canvas():
    page = AsyncMock()
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)
    page.evaluate_handle = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value=-1)

    with pytest.raises(ValueError, match="No signature canvas found"):
        await locate_signature_canvas(page)


# ---------------------------------------------------------------------------
# Stroke strategies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stroke_uses_pointer_events():
    page = AsyncMock()
    page.mouse = AsyncMock()
    canvas = AsyncMock()
    canvas.scroll_into_view_if_needed = AsyncMock()
    canvas.focus = AsyncMock()
    canvas.bounding_box = AsyncMock(
        return_value={"x": 10, "y": 20, "width": 300, "height": 150}
    )
    canvas.dispatch_event = AsyncMock()
    canvas.evaluate = AsyncMock(return_value=True)

    await draw_signature_stroke(page, canvas)

    page.mouse.down.assert_awaited()
    page.mouse.up.assert_awaited()
    # Pointer events preferred
    event_names = [c.args[0] for c in canvas.dispatch_event.await_args_list]
    assert "pointerdown" in event_names
    assert "pointermove" in event_names
    assert "pointerup" in event_names
    assert "mousedown" in event_names
    # ctx paint was also invoked (supplement)
    assert canvas.evaluate.await_count >= 1


@pytest.mark.asyncio
async def test_stroke_raises_without_bbox():
    page = AsyncMock()
    canvas = AsyncMock()
    canvas.scroll_into_view_if_needed = AsyncMock()
    canvas.focus = AsyncMock()
    canvas.bounding_box = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="bounding box"):
        await draw_signature_stroke(page, canvas)


@pytest.mark.asyncio
async def test_ctx_only_insufficient_when_signaturepad_empty():
    """
    Even if pixels look painted, SignaturePad isEmpty===true → verify fails.
    Events are required for library state; ctx alone must not PASS.
    """
    canvas = AsyncMock()
    # Library still empty after ctx-only paint
    canvas.evaluate = AsyncMock(
        return_value={"source": "signaturepad", "empty": True}
    )
    assert await verify_signature_ink(MagicMock(), canvas) is False


# ---------------------------------------------------------------------------
# sign_canvas orchestration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sign_canvas_success():
    page = MagicMock()
    canvas = AsyncMock()

    with (
        patch(
            "app.services.signature_pad.locate_signature_canvas",
            new_callable=AsyncMock,
            return_value=canvas,
        ),
        patch(
            "app.services.signature_pad.draw_signature_stroke",
            new_callable=AsyncMock,
        ) as stroke,
        patch(
            "app.services.signature_pad.verify_signature_ink",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        canvas.evaluate = AsyncMock(return_value="//canvas[1]")
        result = await sign_canvas(page, instruction="Sign it")

    assert result.success is True
    assert result.ink_verified is True
    stroke.assert_awaited_once()


@pytest.mark.asyncio
async def test_sign_canvas_empty_ink_fails():
    page = MagicMock()
    canvas = AsyncMock()

    with (
        patch(
            "app.services.signature_pad.locate_signature_canvas",
            new_callable=AsyncMock,
            return_value=canvas,
        ),
        patch(
            "app.services.signature_pad.draw_signature_stroke",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.signature_pad.verify_signature_ink",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        result = await sign_canvas(page, instruction="Sign it")

    assert result.success is False
    assert result.ink_verified is False
    assert "empty" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_sign_canvas_no_canvas_fails():
    with patch(
        "app.services.signature_pad.locate_signature_canvas",
        new_callable=AsyncMock,
        side_effect=ValueError("No signature canvas found"),
    ):
        result = await sign_canvas(MagicMock(), instruction="Sign it")

    assert result.success is False
    assert "No signature canvas found" in (result.error or "")


@pytest.mark.asyncio
async def test_sign_canvas_stroke_failure():
    canvas = AsyncMock()
    with (
        patch(
            "app.services.signature_pad.locate_signature_canvas",
            new_callable=AsyncMock,
            return_value=canvas,
        ),
        patch(
            "app.services.signature_pad.draw_signature_stroke",
            new_callable=AsyncMock,
            side_effect=RuntimeError("drag failed"),
        ),
    ):
        result = await sign_canvas(MagicMock())

    assert result.success is False
    assert "stroke failed" in (result.error or "").lower()


# ---------------------------------------------------------------------------
# Tier 3: soft act() must NOT PASS blank pad (#1120 / #1122)
# ---------------------------------------------------------------------------


def _make_tier3(page=None):
    stagehand = MagicMock()
    stagehand.page = page or AsyncMock()
    return Tier3StagehandExecutor(stagehand=stagehand, timeout_ms=5000)


@pytest.mark.asyncio
async def test_tier3_soft_act_scrollintoview_does_not_pass():
    """
    act() returns soft success (scrollIntoView) without throw + empty ink
    → step must FAIL and helper must be invoked.
    """
    page = AsyncMock()
    page.url = "https://example.com/consent"
    page.act = AsyncMock(
        return_value={"success": True, "method": "scrollIntoView"}
    )
    executor = _make_tier3(page)

    with patch(
        "app.services.tier3_stagehand.sign_canvas",
        new_callable=AsyncMock,
        return_value=SignResult(
            success=False,
            error="Signature pad appears empty after stroke (ink verification failed)",
            ink_verified=False,
        ),
    ) as mock_sign:
        result = await executor.execute_step(
            {
                "action": "draw_signature",
                "instruction": 'Sign under "Please sign here"',
            }
        )

    mock_sign.assert_awaited_once()
    assert result["success"] is False
    assert "empty" in (result.get("error") or "").lower()


@pytest.mark.asyncio
async def test_tier3_soft_act_then_stroke_and_verify_passes():
    page = AsyncMock()
    page.url = "https://example.com/consent"
    page.act = AsyncMock(
        return_value={"success": True, "method": "scrollIntoView"}
    )
    executor = _make_tier3(page)

    with patch(
        "app.services.tier3_stagehand.sign_canvas",
        new_callable=AsyncMock,
        return_value=SignResult(success=True, ink_verified=True),
    ) as mock_sign:
        result = await executor.execute_step(
            {
                "action": "sign",
                "instruction": "Sign it",
            }
        )

    mock_sign.assert_awaited_once()
    assert result["success"] is True
    assert result["tier"] == 3


@pytest.mark.asyncio
async def test_fallback_not_exception_only():
    """Helper runs when act() does not throw (soft success path)."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.act = AsyncMock(return_value={"method": "locator", "success": True})
    executor = _make_tier3(page)

    with patch.object(
        executor,
        "_execute_draw_signature_fallback",
        new_callable=AsyncMock,
    ) as fallback:
        result = await executor.execute_step(
            {
                "action": "draw_signature",
                "instruction": "Sign under Please sign here",
            }
        )

    fallback.assert_awaited_once()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_tier3_act_throws_still_runs_programmatic_stroke():
    page = AsyncMock()
    page.url = "https://example.com"
    page.act = AsyncMock(side_effect=RuntimeError("act failed"))
    executor = _make_tier3(page)

    with patch(
        "app.services.tier3_stagehand.sign_canvas",
        new_callable=AsyncMock,
        return_value=SignResult(success=True, ink_verified=True),
    ) as mock_sign:
        result = await executor.execute_step(
            {"action": "draw_signature", "instruction": "Sign it"}
        )

    mock_sign.assert_awaited_once()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_tier3_fallback_raises_on_empty_ink():
    executor = _make_tier3()
    with patch(
        "app.services.tier3_stagehand.sign_canvas",
        new_callable=AsyncMock,
        return_value=SignResult(
            success=False,
            error="Signature pad appears empty after stroke (ink verification failed)",
            ink_verified=False,
        ),
    ):
        with pytest.raises(ValueError, match="empty"):
            await executor._execute_draw_signature_fallback(
                instruction="Sign it"
            )


# ---------------------------------------------------------------------------
# Tier 2 empty-observe heuristics (Sprint 12)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_ink_non_dict_truthy():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(return_value=True)
    assert await verify_signature_ink(MagicMock(), canvas) is True


@pytest.mark.asyncio
async def test_verify_ink_non_dict_falsy():
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(return_value=0)
    assert await verify_signature_ink(MagicMock(), canvas) is False


@pytest.mark.asyncio
async def test_locate_selector_exception_continues():
    page = AsyncMock()
    page.locator = MagicMock(side_effect=RuntimeError("bad selector"))
    page.evaluate_handle = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value=-1)
    with pytest.raises(ValueError, match="No signature canvas found"):
        await locate_signature_canvas(page)


@pytest.mark.asyncio
async def test_locate_largest_canvas_evaluate_raises():
    page = AsyncMock()
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)
    page.evaluate_handle = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(side_effect=RuntimeError("no dom"))
    with pytest.raises(ValueError, match="No signature canvas found"):
        await locate_signature_canvas(page)


@pytest.mark.asyncio
async def test_is_visible_enough_fallback_to_count():
    from app.services.signature_pad import _is_visible_enough

    loc = AsyncMock()
    # is_visible raises → fall back to count
    loc.is_visible = AsyncMock(side_effect=RuntimeError("gone"))
    loc.count = AsyncMock(return_value=1)
    assert await _is_visible_enough(loc) is True


@pytest.mark.asyncio
async def test_is_visible_enough_all_fail():
    from app.services.signature_pad import _is_visible_enough

    loc = AsyncMock()
    loc.is_visible = AsyncMock(side_effect=RuntimeError("gone"))
    loc.count = AsyncMock(side_effect=RuntimeError("gone"))
    assert await _is_visible_enough(loc) is False


@pytest.mark.asyncio
async def test_index_of_element_on_error():
    from app.services.signature_pad import _index_of_element

    page = AsyncMock()
    page.evaluate = AsyncMock(side_effect=RuntimeError("x"))
    assert await _index_of_element(page, MagicMock()) == 0


@pytest.mark.asyncio
async def test_stroke_continues_when_focus_fails():
    page = AsyncMock()
    page.mouse = AsyncMock()
    canvas = AsyncMock()
    canvas.scroll_into_view_if_needed = AsyncMock()
    canvas.focus = AsyncMock(side_effect=RuntimeError("not focusable"))
    canvas.bounding_box = AsyncMock(
        return_value={"x": 0, "y": 0, "width": 200, "height": 100}
    )
    canvas.dispatch_event = AsyncMock()
    canvas.evaluate = AsyncMock(return_value=True)
    await draw_signature_stroke(page, canvas, include_ctx_paint=False)
    page.mouse.down.assert_awaited()


@pytest.mark.asyncio
async def test_sign_canvas_xpath_resolve_exception_still_succeeds():
    page = MagicMock()
    canvas = AsyncMock()
    canvas.evaluate = AsyncMock(side_effect=RuntimeError("no xpath"))

    with (
        patch(
            "app.services.signature_pad.locate_signature_canvas",
            new_callable=AsyncMock,
            return_value=canvas,
        ),
        patch(
            "app.services.signature_pad.draw_signature_stroke",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.signature_pad.verify_signature_ink",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await sign_canvas(page, instruction="Sign it")

    assert result.success is True
    assert result.xpath is None


@pytest.mark.asyncio
async def test_near_label_inner_exception_continues():
    """Inner mark/xpath resolve raises → continue to largest-canvas path."""
    page = AsyncMock()
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)

    handle = MagicMock()
    element = MagicMock()
    handle.as_element = MagicMock(return_value=element)
    page.evaluate_handle = AsyncMock(return_value=handle)

    largest = _mock_locator(count=1)
    miss.nth = MagicMock(return_value=largest)

    call_count = {"n": 0}

    async def eval_fn(*args, **kwargs):
        call_count["n"] += 1
        # near-label uses evaluate for mark; largest uses evaluate for index
        if call_count["n"] <= 8:
            raise RuntimeError("mark failed")
        return 0

    page.evaluate = AsyncMock(side_effect=eval_fn)
    found = await locate_signature_canvas(page, instruction="Please sign here")
    assert found is largest


@pytest.mark.asyncio
async def test_near_label_evaluate_handle_raises_continues():
    page = AsyncMock()
    miss = _mock_locator(count=0)
    page.locator = MagicMock(return_value=miss)
    page.evaluate_handle = AsyncMock(side_effect=RuntimeError("no handle"))
    page.evaluate = AsyncMock(return_value=0)
    largest = _mock_locator(count=1)
    miss.nth = MagicMock(return_value=largest)
    found = await locate_signature_canvas(page, instruction="sign")
    assert found is largest


@pytest.mark.asyncio
async def test_tier2_empty_observe_uses_canvas_heuristics():
    """When observe returns no xpath for sign, Tier 2 tries sign_canvas."""
    from app.services.tier2_hybrid import Tier2HybridExecutor

    page = AsyncMock()
    page.url = "https://example.com/consent"

    executor = Tier2HybridExecutor.__new__(Tier2HybridExecutor)
    executor.timeout_ms = 5000
    executor.cache_service = MagicMock()
    executor.cache_service.get_cached_xpath = MagicMock(return_value=None)
    executor.cache_service.cache_xpath = MagicMock()
    executor.xpath_extractor = MagicMock()
    executor.xpath_extractor.extract_xpath_with_page = AsyncMock(
        return_value={"success": False, "error": "observe() returned no results"}
    )
    executor.payment_gateway_ready = False
    executor.payment_gateway_url = None
    executor._verify_and_clear_pending_tab_check = AsyncMock()
    executor._is_payment_instruction = MagicMock(return_value=False)
    executor._should_wait_for_three_hk_observe_readiness = MagicMock(
        return_value=False
    )
    executor._should_retry_observe_extraction = MagicMock(return_value=False)
    executor._looks_like_three_hk_promotion_page = MagicMock(return_value=False)

    with patch(
        "app.services.tier2_hybrid.sign_canvas",
        new_callable=AsyncMock,
        return_value=SignResult(
            success=True, ink_verified=True, xpath="//canvas[1]"
        ),
    ) as mock_sign:
        with patch.object(
            executor,
            "_is_three_hk_promotion_card_click",
            return_value=False,
            create=True,
        ):
            result = await executor.execute_step(
                page,
                {
                    "action": "draw_signature",
                    "instruction": 'Sign under "Please sign here"',
                },
            )

    mock_sign.assert_awaited()
    assert result["success"] is True
    assert result["tier"] == 2
