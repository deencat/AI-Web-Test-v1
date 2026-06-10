"""
Unit tests for PreprodOtpService — Sprint 10.21 Three HK preprod API OTP.

TDD: mock HTTP responses; msisdn/type filter; newest-first; stale rejection; timeout.
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.preprod_otp_service import (
    PreprodOtpService,
    parse_preprod_otp_records,
    select_matching_otp,
)


def _dt(seconds_ago: float = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

class TestParsePreprodOtpRecords:
    def test_parses_list_payload_with_field_aliases(self):
        payload = [
            {
                "otpCode": "482019",
                "msisdn": "85291234567",
                "otpType": "login",
                "createdAt": "2026-06-10T10:00:00Z",
            }
        ]
        records = parse_preprod_otp_records(payload)
        assert len(records) == 1
        assert records[0]["otp"] == "482019"
        assert records[0]["msisdn"] == "85291234567"
        assert records[0]["otp_type"] == "login"
        assert records[0]["created_at"] is not None

    def test_parses_wrapped_data_key(self):
        payload = {
            "data": [
                {
                    "verificationCode": "123456",
                    "contactNumber": "85291234567",
                    "type": "contact",
                    "createTime": "2026-06-10T10:05:00Z",
                }
            ]
        }
        records = parse_preprod_otp_records(payload)
        assert len(records) == 1
        assert records[0]["otp"] == "123456"
        assert records[0]["msisdn"] == "85291234567"
        assert records[0]["otp_type"] == "contact"


# ---------------------------------------------------------------------------
# Record selection
# ---------------------------------------------------------------------------

class TestSelectMatchingOtp:
    def test_filters_by_msisdn_and_otp_type(self):
        records = [
            {
                "otp": "111111",
                "msisdn": "85290000000",
                "otp_type": "login",
                "created_at": _dt(10),
            },
            {
                "otp": "482019",
                "msisdn": "85291234567",
                "otp_type": "login",
                "created_at": _dt(5),
            },
        ]
        poll_start = _dt(0)
        result = select_matching_otp(
            records,
            msisdn="85291234567",
            otp_type="login",
            poll_start_time=poll_start,
        )
        assert result == "482019"

    def test_picks_newest_when_multiple_match(self):
        records = [
            {
                "otp": "111111",
                "msisdn": "85291234567",
                "otp_type": "login",
                "created_at": _dt(30),
            },
            {
                "otp": "999999",
                "msisdn": "85291234567",
                "otp_type": "login",
                "created_at": _dt(5),
            },
        ]
        poll_start = _dt(0)
        result = select_matching_otp(
            records,
            msisdn="85291234567",
            otp_type="login",
            poll_start_time=poll_start,
        )
        assert result == "999999"

    def test_rejects_stale_otp_before_poll_start_grace_window(self):
        records = [
            {
                "otp": "482019",
                "msisdn": "85291234567",
                "otp_type": "login",
                "created_at": _dt(120),
            },
        ]
        poll_start = _dt(0)
        result = select_matching_otp(
            records,
            msisdn="85291234567",
            otp_type="login",
            poll_start_time=poll_start,
            grace_seconds=5,
        )
        assert result is None

    def test_accepts_otp_within_grace_window_before_poll_start(self):
        records = [
            {
                "otp": "482019",
                "msisdn": "85291234567",
                "otp_type": "login",
                "created_at": _dt(0) + timedelta(seconds=2),
            },
        ]
        poll_start = _dt(0)
        result = select_matching_otp(
            records,
            msisdn="85291234567",
            otp_type="login",
            poll_start_time=poll_start,
            grace_seconds=5,
        )
        assert result == "482019"


# ---------------------------------------------------------------------------
# PreprodOtpService.poll_otp
# ---------------------------------------------------------------------------

class TestPreprodOtpServicePollOtp:
    def test_poll_otp_returns_matching_value(self):
        service = PreprodOtpService()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    "otp": "482019",
                    "msisdn": "85291234567",
                    "otpType": "login",
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        with patch("app.services.preprod_otp_service.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = response
            mock_client_cls.return_value = mock_client

            otp = service.poll_otp(
                api_url="https://example.test/otp",
                msisdn="85291234567",
                otp_type="login",
                timeout=10,
                interval=1,
            )

        assert otp == "482019"
        assert mock_client.get.call_count >= 1

    def test_poll_otp_times_out_when_no_match(self):
        service = PreprodOtpService()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": []}

        with patch("app.services.preprod_otp_service.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = response
            mock_client_cls.return_value = mock_client

            with patch("app.services.preprod_otp_service.time.sleep"):
                with pytest.raises(TimeoutError, match="No OTP found"):
                    service.poll_otp(
                        api_url="https://example.test/otp",
                        msisdn="85291234567",
                        otp_type="login",
                        timeout=3,
                        interval=1,
                    )

    def test_poll_otp_raises_on_http_error(self):
        service = PreprodOtpService()
        response = MagicMock()
        response.status_code = 503
        response.raise_for_status.side_effect = Exception("503 Service Unavailable")

        with patch("app.services.preprod_otp_service.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = response
            mock_client_cls.return_value = mock_client

            with patch("app.services.preprod_otp_service.time.sleep"):
                with pytest.raises(TimeoutError):
                    service.poll_otp(
                        api_url="https://example.test/otp",
                        msisdn="85291234567",
                        otp_type="login",
                        timeout=2,
                        interval=1,
                    )
