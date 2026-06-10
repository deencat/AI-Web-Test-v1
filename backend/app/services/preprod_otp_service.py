"""
PreprodOtpService — Sprint 10.21 Three HK preprod API OTP retrieval.

Polls the QA diagnostic endpoint getOtpInfoListFor1Hour via httpx in the backend
process. No browser involvement — OTP fetch is out-of-band HTTP.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Field aliases observed / expected from QA API (tolerant parser — spike 10.21-B7)
_OTP_VALUE_KEYS = ("otp", "otpCode", "otp_code", "verificationCode", "verification_code", "code")
_MSISDN_KEYS = ("msisdn", "contactNumber", "contact_number", "mobile", "phone")
_OTP_TYPE_KEYS = ("otpType", "otp_type", "type", "purpose")
_CREATED_AT_KEYS = ("createdAt", "created_at", "createTime", "create_time", "timestamp")


def _first_value(record: dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _normalize_msisdn(msisdn: str) -> str:
    return "".join(ch for ch in msisdn if ch.isdigit())


def _parse_created_at(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1_000_000_000_000:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return _parse_created_at(int(text))
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        try:
            dt = parsedate_to_datetime(text)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return None
    return None


def _normalize_record(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    otp = _first_value(raw, _OTP_VALUE_KEYS)
    if not otp:
        return None
    msisdn = _first_value(raw, _MSISDN_KEYS) or ""
    otp_type = (_first_value(raw, _OTP_TYPE_KEYS) or "").lower()
    created_at = None
    for key in _CREATED_AT_KEYS:
        if key in raw:
            created_at = _parse_created_at(raw[key])
            if created_at:
                break
    return {
        "otp": otp,
        "msisdn": msisdn,
        "otp_type": otp_type,
        "created_at": created_at,
    }


def parse_preprod_otp_records(payload: Any) -> list[dict[str, Any]]:
    """Parse API JSON into normalized OTP record dicts."""
    if payload is None:
        return []
    if isinstance(payload, dict):
        for key in ("data", "result", "records", "otpList", "otp_list"):
            if key in payload:
                return parse_preprod_otp_records(payload[key])
        payload = [payload]
    if not isinstance(payload, list):
        return []

    records: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            normalized = _normalize_record(item)
            if normalized:
                records.append(normalized)
    return records


def _otp_type_matches(record_type: str, requested_type: Optional[str]) -> bool:
    if not requested_type:
        return True
    record_type = (record_type or "").lower()
    requested = requested_type.lower().replace("_", " ").replace("-", " ")
    if record_type == requested:
        return True
    if "contact" in requested and "contact" in record_type:
        return True
    if requested == "login" and "login" in record_type:
        return True
    return requested in record_type or record_type in requested


def select_matching_otp(
    records: list[dict[str, Any]],
    msisdn: str,
    otp_type: Optional[str],
    poll_start_time: datetime,
    grace_seconds: int = 5,
) -> Optional[str]:
    """
    Return the newest OTP matching msisdn/type that is not stale.

    Stale = created_at < poll_start_time - grace_seconds.
    """
    target_msisdn = _normalize_msisdn(msisdn)
    cutoff = poll_start_time - timedelta(seconds=grace_seconds)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    candidates: list[tuple[datetime, str]] = []
    for record in records:
        record_msisdn = _normalize_msisdn(record.get("msisdn", ""))
        if target_msisdn and record_msisdn and record_msisdn != target_msisdn:
            continue
        if not _otp_type_matches(record.get("otp_type", ""), otp_type):
            continue

        created_at = record.get("created_at")
        if created_at is not None:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at < cutoff:
                continue
            candidates.append((created_at, record["otp"]))
        else:
            # No timestamp — accept only if we have no better signal
            candidates.append((poll_start_time, record["otp"]))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


class PreprodOtpService:
    """Poll Three HK preprod OTP diagnostic API until a matching OTP appears."""

    def poll_otp(
        self,
        api_url: str,
        msisdn: str,
        otp_type: Optional[str] = None,
        poll_start_time: Optional[datetime] = None,
        timeout: int = 60,
        interval: int = 3,
        grace_seconds: int = 5,
    ) -> str:
        """
        Poll *api_url* until a matching OTP is found or *timeout* elapses.

        Returns:
            OTP string (e.g. "482019").

        Raises:
            TimeoutError: No matching OTP within timeout.
        """
        if poll_start_time is None:
            poll_start_time = datetime.now(timezone.utc)
        elif poll_start_time.tzinfo is None:
            poll_start_time = poll_start_time.replace(tzinfo=timezone.utc)

        deadline = time.monotonic() + timeout
        masked_msisdn = _mask_msisdn(msisdn)

        with httpx.Client(timeout=30.0) as client:
            while time.monotonic() < deadline:
                try:
                    response = client.get(api_url)
                    response.raise_for_status()
                    records = parse_preprod_otp_records(response.json())
                    otp = select_matching_otp(
                        records,
                        msisdn=msisdn,
                        otp_type=otp_type,
                        poll_start_time=poll_start_time,
                        grace_seconds=grace_seconds,
                    )
                    if otp:
                        logger.info(
                            "PreprodOtpService: OTP found for msisdn=%s type=%s",
                            masked_msisdn,
                            otp_type or "any",
                        )
                        return otp
                except Exception as exc:
                    logger.warning(
                        "PreprodOtpService: poll error for msisdn=%s: %s",
                        masked_msisdn,
                        exc,
                    )

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(interval, remaining))

        raise TimeoutError(
            f"No OTP found via preprod API for {masked_msisdn} within {timeout} seconds."
        )


def _mask_msisdn(msisdn: str) -> str:
    digits = _normalize_msisdn(msisdn)
    if len(digits) <= 4:
        return "****"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


# Module-level singleton used by execution engines
preprod_otp_service = PreprodOtpService()
