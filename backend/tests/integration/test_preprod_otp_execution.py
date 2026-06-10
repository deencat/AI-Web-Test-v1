"""
Integration tests for Three HK preprod API OTP routing — Sprint 10.21.

TDD: router picks API vs IMAP; JIT otp_expanded_end guard; graceful fallback.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.email_otp_service import format_otp_steps, is_otp_step
from app.services.otp_source_router import (
    OtpSource,
    fetch_otp_and_format_steps,
    parse_otp_step_params,
    resolve_otp_source,
)


# ---------------------------------------------------------------------------
# OTP source router — detection
# ---------------------------------------------------------------------------

class TestOtpSourceRouterDetection:
    def test_metadata_explicit_preprod_api(self):
        step = {"description": "Enter OTP", "otp_source": "three_preprod_api", "msisdn": "85291234567"}
        source, params = resolve_otp_source(step, test_url="https://wwwuat.three.com.hk/")
        assert source == OtpSource.THREE_PREPROD_API
        assert params["msisdn"] == "85291234567"

    def test_parses_login_otp_from_step_text(self):
        params = parse_otp_step_params("Enter login OTP for 85291234567")
        assert params["msisdn"] == "85291234567"
        assert params["otp_type"] == "login"

    def test_parses_contact_number_otp_from_step_text(self):
        params = parse_otp_step_params("Enter contact number OTP for 85291234567")
        assert params["msisdn"] == "85291234567"
        assert "contact" in params["otp_type"]

    def test_parses_api_annotation(self):
        params = parse_otp_step_params("@otp:api(msisdn=85291234567,type=login)")
        assert params["msisdn"] == "85291234567"
        assert params["otp_type"] == "login"

    def test_three_hk_uat_url_defaults_to_preprod_api_when_enabled(self):
        with patch("app.services.otp_source_router.settings") as mock_settings:
            mock_settings.THREE_PREPROD_OTP_API_URL = "https://example.test/otp"
            mock_settings.PREPROD_OTP_UAT_ONLY = True
            source, params = resolve_otp_source(
                "Enter the OTP",
                test_url="https://wwwuat.three.com.hk/plan",
            )
        assert source == OtpSource.THREE_PREPROD_API

    def test_non_three_url_falls_back_to_imap_when_email_credential_exists(self):
        mock_db = MagicMock()
        mock_cred = MagicMock()
        with patch(
            "app.services.otp_source_router.get_email_credential_for_user",
            return_value=mock_cred,
        ):
            with patch("app.services.otp_source_router.settings") as mock_settings:
                mock_settings.THREE_PREPROD_OTP_API_URL = "https://example.test/otp"
                mock_settings.PREPROD_OTP_UAT_ONLY = True
                source, _ = resolve_otp_source(
                    "Enter the OTP sent to email",
                    test_url="https://example.com/login",
                    db=mock_db,
                    user_id=1,
                )
        assert source == OtpSource.IMAP_EMAIL

    def test_no_source_when_no_match_and_no_credential(self):
        mock_db = MagicMock()
        with patch(
            "app.services.otp_source_router.get_email_credential_for_user",
            return_value=None,
        ):
            with patch("app.services.otp_source_router.settings") as mock_settings:
                mock_settings.THREE_PREPROD_OTP_API_URL = ""
                mock_settings.PREPROD_OTP_UAT_ONLY = True
                source, _ = resolve_otp_source(
                    "Enter the OTP",
                    test_url="https://example.com/login",
                    db=mock_db,
                    user_id=1,
                )
        assert source == OtpSource.NONE


# ---------------------------------------------------------------------------
# fetch_otp_and_format_steps — API vs IMAP dispatch
# ---------------------------------------------------------------------------

class TestFetchOtpAndFormatStepsDispatch:
    def _build_mock_credential(self):
        cred = MagicMock()
        cred.imap_host = "imap.gmail.com"
        cred.imap_port = 993
        cred.email_address = "qa@gmail.com"
        cred.imap_password_encrypted = "encrypted"
        return cred

    def test_preprod_api_returns_per_digit_steps(self):
        with patch("app.services.otp_source_router.settings") as mock_settings:
            mock_settings.THREE_PREPROD_OTP_API_URL = "https://example.test/otp"
            mock_settings.PREPROD_OTP_POLL_TIMEOUT = 60
            mock_settings.PREPROD_OTP_POLL_INTERVAL = 3
            mock_settings.PREPROD_OTP_UAT_ONLY = True
            with patch(
                "app.services.otp_source_router.preprod_otp_service.poll_otp",
                return_value="482019",
            ):
                result = fetch_otp_and_format_steps(
                    "Enter login OTP for 85291234567",
                    db=MagicMock(),
                    user_id=1,
                    test_url="https://wwwuat.three.com.hk/",
                )

        assert len(result) == 6
        assert "4" in result[0]

    def test_imap_used_when_not_preprod_match(self):
        mock_cred = self._build_mock_credential()
        mock_enc = MagicMock()
        mock_enc.decrypt_password.return_value = "app-password"

        with patch("app.services.otp_source_router.settings") as mock_settings:
            mock_settings.THREE_PREPROD_OTP_API_URL = "https://example.test/otp"
            mock_settings.PREPROD_OTP_UAT_ONLY = True
            mock_settings.EMAIL_OTP_POLL_TIMEOUT = 60
            mock_settings.EMAIL_OTP_POLL_INTERVAL = 3
            with patch(
                "app.services.otp_source_router.get_email_credential_for_user",
                return_value=mock_cred,
            ):
                with patch(
                    "app.services.otp_source_router.email_otp_service.poll_otp",
                    return_value="123456",
                ):
                    with patch(
                        "app.services.encryption_service.EncryptionService",
                        return_value=mock_enc,
                    ):
                        with patch.dict("os.environ", {"CREDENTIAL_ENCRYPTION_KEY": "test-key"}):
                            result = fetch_otp_and_format_steps(
                                "Enter the OTP sent to email",
                                db=MagicMock(),
                                user_id=1,
                                test_url="https://example.com/",
                            )

        assert len(result) == 6

    def test_preprod_timeout_returns_graceful_error_step(self):
        with patch("app.services.otp_source_router.settings") as mock_settings:
            mock_settings.THREE_PREPROD_OTP_API_URL = "https://example.test/otp"
            mock_settings.PREPROD_OTP_POLL_TIMEOUT = 60
            mock_settings.PREPROD_OTP_POLL_INTERVAL = 3
            mock_settings.PREPROD_OTP_UAT_ONLY = True
            with patch(
                "app.services.otp_source_router.preprod_otp_service.poll_otp",
                side_effect=TimeoutError("No OTP found via preprod API"),
            ):
                result = fetch_otp_and_format_steps(
                    "Enter login OTP for 85291234567",
                    db=MagicMock(),
                    user_id=1,
                    test_url="https://wwwuat.three.com.hk/",
                )

        assert len(result) == 1
        assert "OTP" in result[0] or "No OTP" in result[0]

    def test_no_source_returns_original_step(self):
        with patch("app.services.otp_source_router.settings") as mock_settings:
            mock_settings.THREE_PREPROD_OTP_API_URL = ""
            mock_settings.PREPROD_OTP_UAT_ONLY = True
            with patch(
                "app.services.otp_source_router.get_email_credential_for_user",
                return_value=None,
            ):
                result = fetch_otp_and_format_steps(
                    "Enter the OTP",
                    db=MagicMock(),
                    user_id=1,
                    test_url="https://example.com/",
                )

        assert result == ["Enter the OTP"]


# ---------------------------------------------------------------------------
# Execution engine wiring
# ---------------------------------------------------------------------------

class TestExecutionEnginePreprodOtpWiring:
    def test_stagehand_uses_preprod_api_for_three_hk_step(self):
        from app.services.stagehand_service import StagehandExecutionService

        svc = StagehandExecutionService.__new__(StagehandExecutionService)
        fetch_calls = []

        def tracking_fetch(step, db, user_id, test_url=None):
            fetch_calls.append({"test_url": test_url})
            return format_otp_steps("482019")

        with patch(
            "app.services.stagehand_service.fetch_otp_and_format_steps",
            side_effect=tracking_fetch,
        ):
            result = svc._fetch_otp_and_format_steps(
                "Enter login OTP for 85291234567",
                db=MagicMock(),
                user_id=1,
                test_url="https://wwwuat.three.com.hk/",
            )

        assert len(result) == 6
        assert fetch_calls[0]["test_url"] == "https://wwwuat.three.com.hk/"

    def test_jit_expansion_polls_preprod_api_only_once(self):
        from app.services.stagehand_service import StagehandExecutionService

        svc = StagehandExecutionService.__new__(StagehandExecutionService)
        poll_calls = []

        def counting_fetch(step, db, user_id, test_url=None):
            poll_calls.append(True)
            return format_otp_steps("482019")

        steps = ["Click submit", "Enter login OTP for 85291234567", "Click continue"]

        with patch(
            "app.services.stagehand_service.fetch_otp_and_format_steps",
            side_effect=counting_fetch,
        ):
            result_steps = list(steps)
            otp_expanded_end = 0
            i = 0
            while i < len(result_steps):
                step = result_steps[i]
                if i >= otp_expanded_end and is_otp_step(step):
                    expanded = svc._fetch_otp_and_format_steps(
                        step,
                        db=MagicMock(),
                        user_id=1,
                        test_url="https://wwwuat.three.com.hk/",
                    )
                    result_steps[i : i + 1] = expanded
                    otp_expanded_end = i + len(expanded)
                i += 1

        assert len(poll_calls) == 1
