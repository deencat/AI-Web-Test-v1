"""
Unit tests for Sprint 10.17: AI Screenshot Verification in 3-Tier Execution.

TDD approach covers:
  1. ScreenshotVerificationService._parse_verdict — PASS/FAIL/unparseable
  2. ScreenshotVerificationService.verify — calls vision_completion, parses result
  3. VisionNotSupportedError raised for cerebras / local_vllm
  4. vision_completion() dispatches to correct provider
  5. Tier 1 escalates verify_screenshot immediately (error_type = vision_required)
  6. Tier 2 _execute_verify_screenshot — success path and VisionNotSupportedError re-raise
  7. Tier 3 _execute_verify_screenshot_fallback — extract() text match
  8. DB migration: ai_verification_result column added to test_execution_steps
  9. Schema field_validator: JSON string → dict deserialisation
 10. CRUD create_execution_step: accepts ai_verification_result param
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# 1. verdict parsing
# =============================================================================

class TestParseVerdict:
    """_parse_verdict strict regex returns correct verdict / safe FAIL on bad input."""

    def _parse(self, text):
        from app.services.screenshot_verification_service import _parse_verdict
        return _parse_verdict(text)

    def test_pass_verdict_parsed(self):
        result = self._parse("PASS: The 5G 100GB plan is visible at HK$188.")
        assert result["verdict"] == "PASS"
        assert "HK$188" in result["reason"]

    def test_fail_verdict_parsed(self):
        result = self._parse("FAIL: The voucher discount text is not visible on screen.")
        assert result["verdict"] == "FAIL"
        assert "voucher" in result["reason"]

    def test_case_insensitive(self):
        result = self._parse("pass: everything looks good")
        assert result["verdict"] == "PASS"

    def test_unparseable_returns_safe_fail(self):
        result = self._parse("I see the plan information on the page.")
        assert result["verdict"] == "FAIL"
        assert "unparseable" in result["reason"]

    def test_empty_string_returns_safe_fail(self):
        result = self._parse("")
        assert result["verdict"] == "FAIL"

    def test_none_returns_safe_fail(self):
        result = self._parse(None)
        assert result["verdict"] == "FAIL"

    def test_multiline_reason_captured(self):
        result = self._parse("PASS: The plan card shows\n100GB at HK$188.")
        assert result["verdict"] == "PASS"

    def test_missing_reason_returns_fail(self):
        # No colon
        result = self._parse("PASS")
        assert result["verdict"] == "FAIL"


# =============================================================================
# 2. ScreenshotVerificationService.verify — success path
# =============================================================================

class TestScreenshotVerificationServiceVerify:
    """verify() captures screenshot, calls vision_completion, returns verdict dict."""

    @pytest.mark.asyncio
    async def test_verify_pass_returns_verdict_dict(self):
        from app.services.screenshot_verification_service import ScreenshotVerificationService

        fake_page = AsyncMock()
        fake_page.screenshot = AsyncMock(return_value=b"PNG_BYTES")

        mock_llm = AsyncMock()
        mock_llm.vision_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "PASS: Plan information is clearly visible."}}]
        })

        svc = ScreenshotVerificationService(llm_service=mock_llm)
        result = await svc.verify(
            page=fake_page,
            instruction="Verify 5G plan is shown at HK$188",
            expected_items=["5G", "HK$188"],
            provider="openrouter",
        )

        assert result["verdict"] == "PASS"
        assert "visible" in result["reason"].lower()
        assert result["provider"] == "openrouter"
        mock_llm.vision_completion.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_verify_fail_returns_verdict_dict(self):
        from app.services.screenshot_verification_service import ScreenshotVerificationService

        fake_page = AsyncMock()
        fake_page.screenshot = AsyncMock(return_value=b"PNG_BYTES")

        mock_llm = AsyncMock()
        mock_llm.vision_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "FAIL: HK$188 price label not found."}}]
        })

        svc = ScreenshotVerificationService(llm_service=mock_llm)
        result = await svc.verify(
            page=fake_page,
            instruction="Verify plan price visible",
            expected_items=["HK$188"],
            provider="azure",
        )

        assert result["verdict"] == "FAIL"
        assert result["provider"] == "azure"

    @pytest.mark.asyncio
    async def test_verify_fullpage_screenshot(self):
        from app.services.screenshot_verification_service import ScreenshotVerificationService

        fake_page = AsyncMock()
        fake_page.screenshot = AsyncMock(return_value=b"PNG_BYTES")
        mock_llm = AsyncMock()
        mock_llm.vision_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "PASS: Verified."}}]
        })

        svc = ScreenshotVerificationService(llm_service=mock_llm)
        await svc.verify(
            page=fake_page,
            instruction="Verify table",
            screenshot_region="fullpage",
            provider="google",
        )

        fake_page.screenshot.assert_awaited_once_with(full_page=True)

    @pytest.mark.asyncio
    async def test_verify_propagates_vision_not_supported_error(self):
        from app.services.screenshot_verification_service import ScreenshotVerificationService
        from app.services.universal_llm import VisionNotSupportedError

        fake_page = AsyncMock()
        fake_page.screenshot = AsyncMock(return_value=b"PNG_BYTES")

        mock_llm = AsyncMock()
        mock_llm.vision_completion = AsyncMock(side_effect=VisionNotSupportedError("no vision"))

        svc = ScreenshotVerificationService(llm_service=mock_llm)

        with pytest.raises(VisionNotSupportedError):
            await svc.verify(page=fake_page, instruction="Verify plan", provider="cerebras")


# =============================================================================
# 3. VisionNotSupportedError raised for non-vision providers
# =============================================================================

class TestVisionNotSupportedError:
    """vision_completion() raises VisionNotSupportedError for cerebras and local_vllm."""

    @pytest.mark.asyncio
    async def test_cerebras_raises_vision_not_supported(self):
        from app.services.universal_llm import UniversalLLMService, VisionNotSupportedError

        svc = UniversalLLMService()
        with pytest.raises(VisionNotSupportedError):
            await svc.vision_completion(
                image_bytes=b"img",
                system_prompt="sys",
                user_text="user",
                provider="cerebras",
            )

    @pytest.mark.asyncio
    async def test_local_vllm_raises_vision_not_supported(self):
        from app.services.universal_llm import UniversalLLMService, VisionNotSupportedError

        svc = UniversalLLMService()
        with pytest.raises(VisionNotSupportedError):
            await svc.vision_completion(
                image_bytes=b"img",
                system_prompt="sys",
                user_text="user",
                provider="local_vllm",
            )

    def test_vision_not_supported_is_exception(self):
        from app.services.universal_llm import VisionNotSupportedError
        err = VisionNotSupportedError("test")
        assert isinstance(err, Exception)
        assert str(err) == "test"


# =============================================================================
# 4. vision_completion dispatches to correct provider
# =============================================================================

class TestVisionCompletionDispatch:
    """vision_completion routes to the correct internal method."""

    @pytest.mark.asyncio
    async def test_openrouter_vision_called(self):
        from app.services.universal_llm import UniversalLLMService

        svc = UniversalLLMService()
        with patch.object(svc, "_call_openrouter_vision", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"choices": [{"message": {"content": "PASS: ok"}}]}
            await svc.vision_completion(b"img", "sys", "user", provider="openrouter")
            mock_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_azure_vision_called(self):
        from app.services.universal_llm import UniversalLLMService

        svc = UniversalLLMService()
        with patch.object(svc, "_call_azure_vision", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"choices": [{"message": {"content": "PASS: ok"}}]}
            await svc.vision_completion(b"img", "sys", "user", provider="azure")
            mock_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_google_vision_called(self):
        from app.services.universal_llm import UniversalLLMService

        svc = UniversalLLMService()
        with patch.object(svc, "_call_google_vision", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"choices": [{"message": {"content": "PASS: ok"}}]}
            await svc.vision_completion(b"img", "sys", "user", provider="google")
            mock_fn.assert_awaited_once()


# =============================================================================
# 5. Tier 1 escalates verify_screenshot immediately
# =============================================================================

class TestTier1VerifyScreenshotEscalation:
    """Tier 1 returns error_type='vision_required' for verify_screenshot steps."""

    @pytest.mark.asyncio
    async def test_tier1_returns_vision_required_for_verify_screenshot(self):
        from app.services.tier1_playwright import Tier1PlaywrightExecutor

        executor = Tier1PlaywrightExecutor()
        fake_page = AsyncMock()

        result = await executor.execute_step(
            page=fake_page,
            step={"action": "verify_screenshot", "instruction": "Verify plan info"},
        )

        assert result["success"] is False
        assert result["error_type"] == "vision_required"
        assert result["tier"] == 1

    @pytest.mark.asyncio
    async def test_tier1_escalates_without_calling_playwright_selectors(self):
        """Tier 1 should not attempt any DOM actions for verify_screenshot."""
        from app.services.tier1_playwright import Tier1PlaywrightExecutor

        executor = Tier1PlaywrightExecutor()
        fake_page = MagicMock()  # MagicMock (not async) to catch accidental sync calls

        result = await executor.execute_step(
            page=fake_page,
            step={"action": "verify_screenshot", "instruction": "Verify plan"},
        )

        assert result["success"] is False
        assert result["error_type"] == "vision_required"
        # No DOM methods should have been called
        fake_page.locator.assert_not_called()


# =============================================================================
# 6. Tier 2 screenshot verification
# =============================================================================

class TestTier2VerifyScreenshot:
    """Tier 2 _execute_verify_screenshot handles PASS/FAIL and VisionNotSupportedError."""

    def _make_tier2(self, user_ai_config=None):
        from app.services.tier2_hybrid import Tier2HybridExecutor

        db = MagicMock()
        xpath_extractor = MagicMock()
        return Tier2HybridExecutor(
            db=db,
            xpath_extractor=xpath_extractor,
            user_ai_config=user_ai_config or {"execution_provider": "openrouter"},
        )

    @pytest.mark.asyncio
    async def test_execute_verify_screenshot_pass(self):
        executor = self._make_tier2({"execution_provider": "openrouter"})
        fake_page = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.verify = AsyncMock(return_value={
            "verdict": "PASS",
            "reason": "Plan is visible",
            "provider": "openrouter",
            "model": None,
        })

        with patch("app.services.tier2_hybrid.ScreenshotVerificationService", return_value=mock_svc):
            result = await executor._execute_verify_screenshot(
                page=fake_page,
                step={"instruction": "Verify plan", "expected_items": ["5G", "HK$188"]},
                start_time=0.0,
            )

        assert result["success"] is True
        assert result["tier"] == 2
        assert json.loads(result["ai_verification_result"])["verdict"] == "PASS"

    @pytest.mark.asyncio
    async def test_execute_verify_screenshot_fail(self):
        executor = self._make_tier2({"execution_provider": "openrouter"})
        fake_page = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.verify = AsyncMock(return_value={
            "verdict": "FAIL",
            "reason": "Price label not found",
            "provider": "openrouter",
            "model": None,
        })

        with patch("app.services.tier2_hybrid.ScreenshotVerificationService", return_value=mock_svc):
            result = await executor._execute_verify_screenshot(
                page=fake_page,
                step={"instruction": "Verify plan"},
                start_time=0.0,
            )

        assert result["success"] is False
        assert result["error_type"] == "verification_failed"
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_step_reraises_vision_not_supported(self):
        """VisionNotSupportedError must propagate through execute_step for Tier 3 escalation."""
        from app.services.universal_llm import VisionNotSupportedError

        executor = self._make_tier2({"execution_provider": "cerebras"})
        fake_page = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.verify = AsyncMock(side_effect=VisionNotSupportedError("no vision"))

        with patch("app.services.tier2_hybrid.ScreenshotVerificationService", return_value=mock_svc):
            with pytest.raises(VisionNotSupportedError):
                await executor.execute_step(
                    page=fake_page,
                    step={"action": "verify_screenshot", "instruction": "Verify plan"},
                )

    @pytest.mark.asyncio
    async def test_user_ai_config_provider_used(self):
        """Provider from user_ai_config.execution_provider is passed to ScreenshotVerificationService."""
        executor = self._make_tier2({"execution_provider": "azure", "execution_model": "gpt-4o"})
        fake_page = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.verify = AsyncMock(return_value={
            "verdict": "PASS", "reason": "ok", "provider": "azure", "model": "gpt-4o"
        })

        with patch("app.services.tier2_hybrid.ScreenshotVerificationService", return_value=mock_svc) as mock_cls:
            await executor._execute_verify_screenshot(
                page=fake_page,
                step={"instruction": "Verify"},
                start_time=0.0,
            )

        mock_svc.verify.assert_awaited_once()
        call_kwargs = mock_svc.verify.await_args.kwargs
        assert call_kwargs["provider"] == "azure"
        assert call_kwargs["model"] == "gpt-4o"


# =============================================================================
# 7. Tier 3 verify_screenshot fallback via extract()
# =============================================================================

class TestTier3VerifyScreenshotFallback:
    """Tier 3 falls back to stagehand.extract() text-match when vision is unavailable."""

    def _make_tier3(self, extracted_text="5G 100GB HK$188 voucher"):
        from app.services.tier3_stagehand import Tier3StagehandExecutor

        mock_stagehand = MagicMock()
        mock_stagehand.page = AsyncMock()
        mock_stagehand.page.extract = AsyncMock(return_value=extracted_text)

        return Tier3StagehandExecutor(stagehand=mock_stagehand)

    @pytest.mark.asyncio
    async def test_fallback_pass_when_all_items_present(self):
        executor = self._make_tier3("5G 100GB plan at HK$188 with voucher discount")
        result = await executor._execute_verify_screenshot_fallback(
            step={
                "instruction": "Verify 5G plan",
                "expected_items": ["5G", "HK$188", "voucher"],
            },
            start_time=0.0,
        )
        assert result["success"] is True
        assert result["tier"] == 3
        verdict = json.loads(result["ai_verification_result"])
        assert verdict["verdict"] == "PASS"
        assert verdict["provider"] == "tier3_semantic"

    @pytest.mark.asyncio
    async def test_fallback_fail_when_items_missing(self):
        executor = self._make_tier3("5G plan page loaded")
        result = await executor._execute_verify_screenshot_fallback(
            step={
                "instruction": "Verify 5G plan",
                "expected_items": ["HK$188", "voucher"],
            },
            start_time=0.0,
        )
        assert result["success"] is False
        assert result["error_type"] == "verification_failed"
        verdict = json.loads(result["ai_verification_result"])
        assert verdict["verdict"] == "FAIL"
        assert "HK$188" in verdict["reason"] or "voucher" in verdict["reason"]

    @pytest.mark.asyncio
    async def test_fallback_pass_when_no_expected_items(self):
        """Empty expected_items → PASS (instruction only, no item check)."""
        executor = self._make_tier3("any content")
        result = await executor._execute_verify_screenshot_fallback(
            step={"instruction": "Verify page loaded", "expected_items": []},
            start_time=0.0,
        )
        assert result["success"] is True


# =============================================================================
# 8. DB migration: column added to test_execution_steps
# =============================================================================

class TestMigrationSprint1017:
    """Migration adds ai_verification_result to test_execution_steps."""

    def test_migration_adds_column(self, tmp_path):
        import sys
        from sqlalchemy import create_engine, inspect, text

        db_path = tmp_path / "test_migration.db"
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        # Create minimal test_execution_steps table without the new column
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE test_execution_steps (
                    id INTEGER PRIMARY KEY,
                    execution_id INTEGER NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_description TEXT NOT NULL,
                    result TEXT NOT NULL DEFAULT 'pass'
                )
            """))

        # Run migration targeting the temp DB
        with patch.dict("os.environ", {"DATABASE_URL": db_url}):
            import importlib
            import migrate_sprint10_17
            importlib.reload(migrate_sprint10_17)
            migrate_sprint10_17.run_migration()

        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("test_execution_steps")]
        assert "ai_verification_result" in columns

    def test_migration_idempotent(self, tmp_path):
        """Running migration twice does not raise."""
        import os
        from sqlalchemy import create_engine, text

        db_path = tmp_path / "test_idempotent.db"
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE test_execution_steps (
                    id INTEGER PRIMARY KEY,
                    step_description TEXT NOT NULL
                )
            """))
            conn.execute(text(
                "ALTER TABLE test_execution_steps "
                "ADD COLUMN ai_verification_result TEXT NULL"
            ))

        with patch.dict("os.environ", {"DATABASE_URL": db_url}):
            import importlib
            import migrate_sprint10_17
            importlib.reload(migrate_sprint10_17)
            # Should not raise, just print "already exists"
            migrate_sprint10_17.run_migration()


# =============================================================================
# 9. Schema field_validator: JSON string → dict
# =============================================================================

class TestAiVerificationResultSchemaDeserialisation:
    """TestExecutionStepResponse.ai_verification_result deserialises JSON text."""

    def _make_step_response(self, ai_verification_result=None):
        from app.schemas.test_execution import TestExecutionStepResponse
        from app.models.test_execution import ExecutionResult

        return TestExecutionStepResponse(
            id=1,
            execution_id=10,
            step_number=1,
            step_description="Verify plan",
            is_critical=False,
            result=ExecutionResult.PASS,
            actual_result=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            duration_seconds=None,
            screenshot_path=None,
            screenshot_before=None,
            screenshot_after=None,
            retry_count=0,
            ai_verification_result=ai_verification_result,
            created_at="2026-05-27T00:00:00",
        )

    def test_json_string_deserialised_to_dict(self):
        payload = json.dumps({"verdict": "PASS", "reason": "ok"})
        resp = self._make_step_response(ai_verification_result=payload)
        assert isinstance(resp.ai_verification_result, dict)
        assert resp.ai_verification_result["verdict"] == "PASS"

    def test_dict_passes_through_unchanged(self):
        payload = {"verdict": "FAIL", "reason": "missing text"}
        resp = self._make_step_response(ai_verification_result=payload)
        assert resp.ai_verification_result["verdict"] == "FAIL"

    def test_none_allowed(self):
        resp = self._make_step_response(ai_verification_result=None)
        assert resp.ai_verification_result is None

    def test_malformed_json_returns_none(self):
        resp = self._make_step_response(ai_verification_result="not-json{{{")
        assert resp.ai_verification_result is None


# =============================================================================
# 10. CRUD create_execution_step — ai_verification_result param forwarded
# =============================================================================

class TestCreateExecutionStepWithAiVerificationResult:
    """create_execution_step accepts and persists ai_verification_result."""

    def test_ai_verification_result_stored(self):
        from app.crud.test_execution import create_execution_step
        from app.models.test_execution import ExecutionResult

        db = MagicMock()
        captured = {}

        def fake_add(obj):
            captured["obj"] = obj

        db.add.side_effect = fake_add
        db.commit.return_value = None
        db.refresh.return_value = None

        verdict_json = json.dumps({"verdict": "PASS", "reason": "All visible"})
        create_execution_step(
            db=db,
            execution_id=1,
            step_number=3,
            step_description="Verify 5G plan",
            result=ExecutionResult.PASS,
            ai_verification_result=verdict_json,
        )

        assert "obj" in captured
        assert captured["obj"].ai_verification_result == verdict_json

    def test_ai_verification_result_defaults_to_none(self):
        from app.crud.test_execution import create_execution_step
        from app.models.test_execution import ExecutionResult

        db = MagicMock()
        captured = {}
        db.add.side_effect = lambda obj: captured.update({"obj": obj})
        db.commit.return_value = None
        db.refresh.return_value = None

        create_execution_step(
            db=db,
            execution_id=1,
            step_number=1,
            step_description="Navigate to site",
            result=ExecutionResult.PASS,
        )
        assert captured["obj"].ai_verification_result is None
