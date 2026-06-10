"""
OtpSourceRouter — Sprint 10.21 OTP source detection and dispatch.

Routes OTP placeholder steps to either the Three HK preprod HTTP API or the
Sprint 10.10 IMAP email service. Shared by ExecutionService and StagehandService.
"""
from __future__ import annotations

import logging
import os
import re
from enum import Enum
from typing import Any, Optional, Union
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.email_otp_service import (
    email_otp_service,
    format_otp_steps,
    get_email_credential_for_user,
)
from app.services.preprod_otp_service import preprod_otp_service

logger = logging.getLogger(__name__)

StepInput = Union[str, dict[str, Any]]

# "Enter login OTP for 85291234567"
_STEP_TEXT_RE = re.compile(
    r"enter\s+(?P<type>login|contact(?:\s+number)?)\s+otp\s+for\s+(?P<msisdn>\d{8,15})",
    re.IGNORECASE,
)
# @otp:api(msisdn=85291234567,type=login)
_ANNOTATION_RE = re.compile(
    r"@otp:api\s*\(\s*msisdn\s*=\s*(?P<msisdn>\d{8,15})\s*,\s*type\s*=\s*(?P<type>\w+)\s*\)",
    re.IGNORECASE,
)


class OtpSource(str, Enum):
    THREE_PREPROD_API = "three_preprod_api"
    IMAP_EMAIL = "imap_email"
    NONE = "none"


def _step_description(step: StepInput) -> str:
    if isinstance(step, dict):
        return str(
            step.get("description")
            or step.get("instruction")
            or step.get("step")
            or ""
        )
    return str(step)


def _step_metadata(step: StepInput) -> dict[str, Any]:
    if isinstance(step, dict):
        return step
    return {}


def _is_three_hk_url(test_url: Optional[str]) -> bool:
    if not test_url:
        return False
    host = (urlparse(test_url).hostname or "").lower()
    return host.endswith("three.com.hk")


def _preprod_api_enabled() -> bool:
    return bool(getattr(settings, "THREE_PREPROD_OTP_API_URL", ""))


def parse_otp_step_params(step_description: str) -> dict[str, Any]:
    """Extract msisdn and otp_type from step text or @otp:api annotation."""
    text = (step_description or "").strip()
    params: dict[str, Any] = {}

    annotation = _ANNOTATION_RE.search(text)
    if annotation:
        params["msisdn"] = annotation.group("msisdn")
        params["otp_type"] = annotation.group("type").lower()
        return params

    match = _STEP_TEXT_RE.search(text)
    if match:
        params["msisdn"] = match.group("msisdn")
        otp_type = match.group("type").lower().replace(" ", "_")
        params["otp_type"] = "contact" if "contact" in otp_type else otp_type
        return params

    return params


def resolve_otp_source(
    step: StepInput,
    test_url: Optional[str] = None,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> tuple[OtpSource, dict[str, Any]]:
    """
    Determine OTP source and parameters for a step.

    Priority:
    1. Step metadata otp_source=three_preprod_api
    2. Parsed msisdn/type from step text or @otp:api annotation
    3. Three HK UAT URL + preprod API configured
    4. IMAP when user has email credential
    5. NONE
    """
    meta = _step_metadata(step)
    description = _step_description(step)
    params = parse_otp_step_params(description)

    if meta.get("msisdn"):
        params.setdefault("msisdn", str(meta["msisdn"]))
    if meta.get("otp_type"):
        params.setdefault("otp_type", str(meta["otp_type"]).lower())

    explicit_source = str(meta.get("otp_source", "")).lower()
    if explicit_source == OtpSource.THREE_PREPROD_API.value:
        return OtpSource.THREE_PREPROD_API, params

    if params.get("msisdn"):
        return OtpSource.THREE_PREPROD_API, params

    uat_only = getattr(settings, "PREPROD_OTP_UAT_ONLY", True)
    if _preprod_api_enabled() and (not uat_only or _is_three_hk_url(test_url)):
        return OtpSource.THREE_PREPROD_API, params

    if db is not None and user_id is not None:
        cred = get_email_credential_for_user(db, user_id)
        if cred is not None:
            return OtpSource.IMAP_EMAIL, params

    return OtpSource.NONE, params


def fetch_otp_and_format_steps(
    step: StepInput,
    db: Optional[Session],
    user_id: int,
    test_url: Optional[str] = None,
) -> list[str]:
    """
    Resolve OTP source, fetch OTP, and return per-digit step descriptions.

    Falls back to a single error/original step on failure.
    """
    description = _step_description(step)
    source, params = resolve_otp_source(step, test_url=test_url, db=db, user_id=user_id)

    if source == OtpSource.THREE_PREPROD_API:
        return _fetch_preprod_api_otp(description, params)

    if source == OtpSource.IMAP_EMAIL:
        return _fetch_imap_otp(description, db, user_id)

    logger.warning(
        "OTP step detected for user %s but no OTP source resolved (url=%s)",
        user_id,
        test_url,
    )
    return [description]


def _fetch_preprod_api_otp(description: str, params: dict[str, Any]) -> list[str]:
    api_url = settings.THREE_PREPROD_OTP_API_URL
    if not api_url:
        logger.warning("Preprod OTP API URL not configured")
        return [description]

    msisdn = params.get("msisdn", "")
    otp_type = params.get("otp_type")

    try:
        otp = preprod_otp_service.poll_otp(
            api_url=api_url,
            msisdn=msisdn,
            otp_type=otp_type,
            timeout=settings.PREPROD_OTP_POLL_TIMEOUT,
            interval=settings.PREPROD_OTP_POLL_INTERVAL,
        )
        return format_otp_steps(otp)
    except TimeoutError as exc:
        logger.warning("Preprod OTP poll timed out: %s", exc)
        return [f"Enter OTP (No OTP received via preprod API — {exc})"]
    except Exception as exc:
        logger.error("Preprod OTP resolution error: %s", exc)
        return [description]


def _fetch_imap_otp(description: str, db: Optional[Session], user_id: int) -> list[str]:
    key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
    if not key:
        logger.warning("OTP step detected but CREDENTIAL_ENCRYPTION_KEY not set; skipping IMAP poll")
        return [description]

    if db is None:
        logger.warning("OTP step detected but db not available; skipping IMAP poll")
        return [description]

    cred = get_email_credential_for_user(db, user_id)
    if cred is None:
        logger.warning(
            "OTP step detected for user %s but no email credential configured", user_id
        )
        return [description]

    try:
        from app.services.encryption_service import EncryptionService

        enc = EncryptionService()
        app_password = enc.decrypt_password(cred.imap_password_encrypted)
        otp = email_otp_service.poll_otp(
            imap_host=cred.imap_host,
            imap_port=cred.imap_port,
            email_address=cred.email_address,
            app_password=app_password,
            timeout=settings.EMAIL_OTP_POLL_TIMEOUT,
            interval=settings.EMAIL_OTP_POLL_INTERVAL,
        )
        logger.info("OTP resolved via IMAP for user %s — expanding into %d steps", user_id, len(otp))
        return format_otp_steps(otp)
    except TimeoutError as exc:
        logger.warning("OTP poll timed out for user %s: %s", user_id, exc)
        return [f"Enter OTP (No OTP email received — {exc})"]
    except Exception as exc:
        logger.error("OTP resolution error for user %s: %s", user_id, exc)
        return [description]
