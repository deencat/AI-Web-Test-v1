"""
Unit tests for EmailOTPService — Sprint 10.10 IMAP Email OTP.

TDD RED phase: tests are written before the implementation.
"""
import asyncio
import imaplib
import re
import time
from datetime import date
from email.message import EmailMessage
from unittest.mock import MagicMock, patch, call

import pytest

from app.services.email_otp_service import EmailOTPService, extract_otp_from_text, format_otp_step, is_otp_step


# ---------------------------------------------------------------------------
# extract_otp_from_text unit tests
# ---------------------------------------------------------------------------

class TestExtractOtpFromText:
    """Verify OTP extraction regex behaves correctly."""

    def test_extracts_6_digit_otp(self):
        assert extract_otp_from_text("Your OTP is 483921") == "483921"

    def test_extracts_4_digit_otp(self):
        assert extract_otp_from_text("Use code 1234 to verify") == "1234"

    def test_extracts_8_digit_otp(self):
        assert extract_otp_from_text("Verification code: 87654321") == "87654321"

    def test_prefers_context_aware_match_over_first_number(self):
        # A phone number appears before the OTP keyword — context match wins
        assert extract_otp_from_text("Call 12345678 or use code 482019") == "482019"

    def test_prefers_first_match(self):
        # When multiple keyword-adjacent sequences exist, return first matching OTP
        assert extract_otp_from_text("Code 123456 for order 789") == "123456"

    def test_ignores_9_digit_numbers(self):
        # 9-digit numbers are too long (phone numbers, etc.) unless keyword context
        assert extract_otp_from_text("Number 123456789 found") is None

    def test_ignores_3_digit_numbers(self):
        # 3-digit numbers are too short to be OTPs
        assert extract_otp_from_text("Use 123 as code") is None

    def test_returns_none_when_no_otp(self):
        assert extract_otp_from_text("Hello, welcome to the service!") is None

    def test_handles_html_body(self):
        html = "<html><body><p>Your verification code is <strong>982347</strong></p></body></html>"
        assert extract_otp_from_text(html) == "982347"

    def test_handles_empty_string(self):
        assert extract_otp_from_text("") is None

    def test_handles_otp_with_surrounding_punctuation(self):
        assert extract_otp_from_text("OTP: [234567]") == "234567"


# ---------------------------------------------------------------------------
# is_otp_step unit tests
# ---------------------------------------------------------------------------

class TestIsOtpStep:
    """Verify step description pattern detection."""

    def test_enter_otp(self):
        assert is_otp_step("Enter the OTP")

    def test_enter_one_time_password(self):
        assert is_otp_step("Enter the one-time password received via email")

    def test_enter_one_time_password_no_hyphen(self):
        assert is_otp_step("Enter the one time password received via email")

    def test_enter_verification_code(self):
        assert is_otp_step("Enter the verification code sent to your email")

    def test_type_otp(self):
        assert is_otp_step("Type the OTP in the field")

    def test_input_otp(self):
        assert is_otp_step("Input the OTP received")

    def test_case_insensitive(self):
        assert is_otp_step("ENTER THE OTP")
        assert is_otp_step("enter the otp")

    def test_non_otp_step(self):
        assert not is_otp_step("Click the submit button")

    def test_non_otp_with_number(self):
        assert not is_otp_step("Navigate to page 3")

    def test_fill_in_code(self):
        assert is_otp_step("Fill in the verification code from email")


# ---------------------------------------------------------------------------
# EmailOTPService.poll_otp tests (IMAP mocked)
# ---------------------------------------------------------------------------

def _make_email_message(from_addr: str, subject: str, body: str) -> bytes:
    """Build a minimal RFC-2822 email as bytes."""
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg.set_content(body)
    return msg.as_bytes()


class TestEmailOTPServicePollOtp:
    """Tests for EmailOTPService.poll_otp() with a mocked IMAP connection."""

    def _make_imap_mock(self, email_bytes: bytes, uid: bytes = b"1"):
        """Return a MagicMock that mimics IMAP4_SSL search + fetch success."""
        imap = MagicMock()
        imap.__enter__ = MagicMock(return_value=imap)
        imap.__exit__ = MagicMock(return_value=False)
        imap.select.return_value = ("OK", [b"1"])
        imap.search.return_value = ("OK", [uid])
        imap.fetch.return_value = ("OK", [(uid, email_bytes)])
        return imap

    def test_returns_otp_on_first_poll(self):
        """IMAP has a matching email immediately; poll_otp returns the OTP."""
        email_bytes = _make_email_message(
            "noreply@example.com",
            "Your OTP",
            "Your one-time password is 482019"
        )

        service = EmailOTPService()
        imap_mock = self._make_imap_mock(email_bytes)

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            otp = service.poll_otp(
                imap_host="imap.gmail.com",
                imap_port=993,
                email_address="user@gmail.com",
                app_password="secret",
                timeout=5,
                interval=1,
            )

        assert otp == "482019"

    def test_returns_otp_after_delay(self):
        """IMAP returns no email on first poll, then finds email on second."""
        email_bytes = _make_email_message(
            "noreply@example.com",
            "Verify",
            "Code: 990011"
        )

        service = EmailOTPService()
        imap_mock = MagicMock()
        imap_mock.__enter__ = MagicMock(return_value=imap_mock)
        imap_mock.__exit__ = MagicMock(return_value=False)
        imap_mock.select.return_value = ("OK", [b"1"])

        # First search returns empty, second returns an email
        imap_mock.search.side_effect = [
            ("OK", [b""]),
            ("OK", [b"2"]),
        ]
        imap_mock.fetch.return_value = ("OK", [(b"2", email_bytes)])

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            with patch("time.sleep"):  # speed up polling
                otp = service.poll_otp(
                    imap_host="imap.gmail.com",
                    imap_port=993,
                    email_address="user@gmail.com",
                    app_password="secret",
                    timeout=10,
                    interval=1,
                )

        assert otp == "990011"

    def test_raises_timeout_when_no_email(self):
        """poll_otp raises TimeoutError when no email arrives within timeout."""
        service = EmailOTPService()
        imap_mock = MagicMock()
        imap_mock.__enter__ = MagicMock(return_value=imap_mock)
        imap_mock.__exit__ = MagicMock(return_value=False)
        imap_mock.select.return_value = ("OK", [b"1"])
        imap_mock.search.return_value = ("OK", [b""])  # always empty

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            with patch("time.sleep"):
                with patch("time.monotonic", side_effect=[0.0, 0.5, 999.0]):
                    with pytest.raises(TimeoutError, match="No OTP email"):
                        service.poll_otp(
                            imap_host="imap.gmail.com",
                            imap_port=993,
                            email_address="user@gmail.com",
                            app_password="secret",
                            timeout=1,
                            interval=1,
                        )

    def test_uses_sender_filter(self):
        """When sender_filter is set, the IMAP SEARCH includes a FROM criterion."""
        email_bytes = _make_email_message(
            "otp@three.com.hk",
            "Verification",
            "OTP: 112233"
        )

        service = EmailOTPService()
        imap_mock = self._make_imap_mock(email_bytes)

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            otp = service.poll_otp(
                imap_host="imap.gmail.com",
                imap_port=993,
                email_address="user@gmail.com",
                app_password="secret",
                sender_filter="otp@three.com.hk",
                timeout=5,
                interval=1,
            )

        assert otp == "112233"
        # Verify the SEARCH criteria contains the sender filter
        search_args = imap_mock.search.call_args
        search_criteria = str(search_args)
        assert "otp@three.com.hk" in search_criteria

    def test_uses_today_since_filter(self):
        """SEARCH criteria includes SINCE today but NOT UNSEEN (Gmail marks emails read)."""
        email_bytes = _make_email_message(
            "noreply@example.com",
            "OTP",
            "777888"
        )
        service = EmailOTPService()
        imap_mock = self._make_imap_mock(email_bytes)
        today_str = date.today().strftime("%d-%b-%Y")

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            service.poll_otp(
                imap_host="imap.gmail.com",
                imap_port=993,
                email_address="user@gmail.com",
                app_password="secret",
                timeout=5,
                interval=1,
            )

        search_args = imap_mock.search.call_args
        criteria_str = str(search_args)
        assert today_str in criteria_str
        # Must NOT require UNSEEN — emails may be marked read in Gmail web UI
        assert "UNSEEN" not in criteria_str

    def test_logs_in_with_credentials(self):
        """Verify login() is called with the provided email + app_password."""
        email_bytes = _make_email_message("a@b.com", "OTP", "Test 999888")
        service = EmailOTPService()
        imap_mock = self._make_imap_mock(email_bytes)

        with patch("imaplib.IMAP4_SSL", return_value=imap_mock):
            service.poll_otp(
                imap_host="imap.gmail.com",
                imap_port=993,
                email_address="qa@gmail.com",
                app_password="mysecret",
                timeout=5,
                interval=1,
            )

        imap_mock.login.assert_called_once_with("qa@gmail.com", "mysecret")


# ---------------------------------------------------------------------------
# format_otp_step tests
# ---------------------------------------------------------------------------

class TestFormatOtpStep:
    """Verify the per-digit step description generator."""

    def test_6_digit_otp_contains_digits_spaced(self):
        result = format_otp_step("482019")
        assert "4 8 2 0 1 9" in result

    def test_4_digit_otp_mentions_count(self):
        result = format_otp_step("1234")
        assert "4" in result
        assert "1 2 3 4" in result

    def test_contains_otp_value(self):
        result = format_otp_step("999888")
        assert "999888" in result

    def test_mentions_individual_boxes(self):
        result = format_otp_step("123456")
        result_lower = result.lower()
        assert "input" in result_lower or "box" in result_lower or "digit" in result_lower

    def test_returns_string(self):
        assert isinstance(format_otp_step("482019"), str)
