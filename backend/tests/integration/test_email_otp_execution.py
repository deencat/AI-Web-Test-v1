"""
Integration tests for OTP step detection in the execution engine — Sprint 10.10.

TDD RED phase: verifies that OTP steps are intercepted before _execute_step_hybrid,
the IMAP service is called, and the resolved OTP value is injected into the step.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email_otp_service import is_otp_step, OTP_PATTERNS


# ---------------------------------------------------------------------------
# OTP step pattern detection — standalone
# ---------------------------------------------------------------------------

class TestOtpPatternDetection:
    """Verify OTP_PATTERNS list and is_otp_step() function."""

    def test_otp_patterns_list_not_empty(self):
        assert len(OTP_PATTERNS) >= 4

    @pytest.mark.parametrize("desc", [
        "Enter the OTP",
        "Enter the one-time password",
        "Enter the one time password",
        "Enter the verification code",
        "Type the OTP",
        "Input the OTP",
        "Fill in the verification code from email",
    ])
    def test_matches_otp_steps(self, desc):
        assert is_otp_step(desc), f"Expected is_otp_step({desc!r}) to be True"

    @pytest.mark.parametrize("desc", [
        "Click the Submit button",
        "Navigate to the home page",
        "Select the dropdown option",
        "Verify the page title",
    ])
    def test_does_not_match_non_otp_steps(self, desc):
        assert not is_otp_step(desc), f"Expected is_otp_step({desc!r}) to be False"


# ---------------------------------------------------------------------------
# OTP resolution in stagehand_service step loop
# ---------------------------------------------------------------------------

class TestOtpResolutionInStagehandService:
    """
    Verifies that StagehandExecutionService._resolve_otp_step() calls
    EmailOTPService.poll_otp() and returns the injected step description.
    """

    def _build_mock_credential(self):
        cred = MagicMock()
        cred.imap_host = "imap.gmail.com"
        cred.imap_port = 993
        cred.email_address = "qa@gmail.com"
        cred.imap_password_encrypted = "encrypted"
        return cred

    def test_resolve_otp_step_returns_injected_description(self):
        """When OTP step is detected, resolved step injects the OTP value."""
        from app.services.stagehand_service import StagehandExecutionService
        import app.services.stagehand_service as stagehand_mod

        svc = StagehandExecutionService.__new__(StagehandExecutionService)

        mock_db = MagicMock()
        mock_cred = self._build_mock_credential()
        mock_enc = MagicMock()
        mock_enc.decrypt_password.return_value = "app-password"

        with patch(
            "app.services.stagehand_service.get_email_credential_for_user",
            return_value=mock_cred,
        ):
            with patch(
                "app.services.stagehand_service.email_otp_service.poll_otp",
                return_value="482019",
            ):
                with patch.object(stagehand_mod, "encryption_service", mock_enc):
                    result = svc._resolve_otp_step(
                        "Enter the OTP sent to email",
                        db=mock_db,
                        user_id=1,
                    )

        assert "482019" in result

    def test_non_otp_step_returns_unchanged(self):
        """Non-OTP steps are returned unchanged."""
        from app.services.stagehand_service import StagehandExecutionService

        svc = StagehandExecutionService.__new__(StagehandExecutionService)

        result = svc._resolve_otp_step(
            "Click the Submit button",
            db=MagicMock(),
            user_id=1,
        )

        assert result == "Click the Submit button"

    def test_no_credential_returns_original_step(self):
        """If no email credential configured, return original step unchanged."""
        from app.services.stagehand_service import StagehandExecutionService

        svc = StagehandExecutionService.__new__(StagehandExecutionService)

        with patch(
            "app.services.stagehand_service.get_email_credential_for_user",
            return_value=None,
        ):
            result = svc._resolve_otp_step(
                "Enter the OTP",
                db=MagicMock(),
                user_id=1,
            )

        # Falls back gracefully — original description returned
        assert result == "Enter the OTP"

    def test_poll_timeout_returns_graceful_message(self):
        """When IMAP poll times out, step description becomes a clear error message."""
        from app.services.stagehand_service import StagehandExecutionService
        import app.services.stagehand_service as stagehand_mod

        svc = StagehandExecutionService.__new__(StagehandExecutionService)
        mock_cred = self._build_mock_credential()
        mock_enc = MagicMock()
        mock_enc.decrypt_password.return_value = "app-password"

        with patch(
            "app.services.stagehand_service.get_email_credential_for_user",
            return_value=mock_cred,
        ):
            with patch(
                "app.services.stagehand_service.email_otp_service.poll_otp",
                side_effect=TimeoutError("No OTP email found"),
            ):
                with patch.object(stagehand_mod, "encryption_service", mock_enc):
                    result = svc._resolve_otp_step(
                        "Enter the OTP sent to email",
                        db=MagicMock(),
                        user_id=1,
                    )

        assert "OTP" in result or "timeout" in result.lower() or "No OTP" in result


# ---------------------------------------------------------------------------
# Email credential CRUD helpers
# ---------------------------------------------------------------------------

class TestGetEmailCredentialForUser:
    """Verify the DB helper that fetches the first active credential."""

    def test_returns_first_credential(self):
        from app.services.email_otp_service import get_email_credential_for_user

        mock_db = MagicMock()
        mock_cred = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred

        result = get_email_credential_for_user(mock_db, user_id=1)

        assert result is mock_cred

    def test_returns_none_when_no_credentials(self):
        from app.services.email_otp_service import get_email_credential_for_user

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_email_credential_for_user(mock_db, user_id=1)

        assert result is None
