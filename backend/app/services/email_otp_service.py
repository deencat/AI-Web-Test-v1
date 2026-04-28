"""
EmailOTPService — Sprint 10.10 IMAP Email OTP retrieval.

Connects to an IMAP mailbox over TLS, searches for unseen emails from a sender
received today, and extracts a numeric OTP using regex. Polls every `interval`
seconds until an OTP is found or `timeout` seconds elapse.

Supported providers (out of the box):
  Gmail:    imap.gmail.com:993   (requires App Password, not account password)
  Outlook:  outlook.office365.com:993
  Yahoo:    imap.mail.yahoo.com:993
  Any IMAP: user-configurable imap_host + imap_port
"""
import imaplib
import logging
import re
import time
from datetime import date
from email import message_from_bytes
from email.policy import default as email_policy
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Known IMAP hosts reference (for frontend dropdowns / docs)
# ----------------------------------------------------------------------------

KNOWN_IMAP_HOSTS: dict[str, int] = {
    "imap.gmail.com": 993,
    "outlook.office365.com": 993,
    "imap.mail.yahoo.com": 993,
}

# ----------------------------------------------------------------------------
# OTP step detection patterns
# ----------------------------------------------------------------------------

OTP_PATTERNS: list[str] = [
    r"enter.*otp",
    r"enter.*one.?time.*password",
    r"enter.*verification.*code",
    r"type.*otp",
    r"input.*otp",
    r"fill.*verification.*code",
]

_OTP_STEP_RE = re.compile("|".join(OTP_PATTERNS), re.IGNORECASE)

# Context-aware regex: digit sequence near OTP/code/verification keywords
# Try this FIRST to avoid picking up phone numbers, dates, prices, etc.
_OTP_CONTEXT_RE = re.compile(
    r"(?:code|otp|one.?time|password|pin|token|verification)\b.{0,40}?(\d{4,8})(?!\d)",
    re.IGNORECASE | re.DOTALL,
)

# Fallback: any standalone 4–8 digit number
_OTP_VALUE_RE = re.compile(r"\b(\d{4,8})\b")


def is_otp_step(step_description: str) -> bool:
    """Return True if the step description matches an OTP entry pattern."""
    return bool(_OTP_STEP_RE.search(step_description))


def extract_otp_from_text(text: str) -> Optional[str]:
    """
    Return the OTP found in *text*, or None.

    Strategy:
    1. Context-aware match — digits appearing within 40 chars of a keyword
       (code, otp, verification, pin, token, password).  This avoids picking
       up phone numbers, prices, or other incidental digit sequences.
    2. Fallback — first standalone 4–8 digit number in the body.
    """
    if not text:
        return None
    match = _OTP_CONTEXT_RE.search(text)
    if match:
        return match.group(1)
    match = _OTP_VALUE_RE.search(text)
    return match.group(1) if match else None


def format_otp_step(otp: str) -> str:
    """
    Return a step description that instructs the execution engine to type
    each OTP digit into an individual input box.

    Stagehand interprets this as N sequential single-character fills instead
    of a single `fill(otp)` call, which is required for UIs (e.g. Three HK
    registration) that use separate <input maxlength="1"> boxes per digit.
    """
    digits_spaced = " ".join(list(otp))
    return (
        f"Enter the one-time password '{otp}' into the verification code inputs. "
        f"There are {len(otp)} individual digit input boxes — type each digit "
        f"one at a time in order: {digits_spaced}"
    )


def get_email_credential_for_user(db: Session, user_id: int):
    """Return the first EmailCredential for *user_id*, or None."""
    from app.models.email_credential import EmailCredential

    return (
        db.query(EmailCredential)
        .filter(EmailCredential.user_id == user_id)
        .first()
    )


# ----------------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------------

class EmailOTPService:
    """
    Retrieves one-time passwords from a real email inbox via IMAP over TLS.

    Usage::

        service = EmailOTPService()
        otp = service.poll_otp(
            imap_host="imap.gmail.com",
            imap_port=993,
            email_address="qa@gmail.com",
            app_password="xxxx-xxxx-xxxx-xxxx",
            sender_filter="noreply@three.com.hk",
            timeout=60,
            interval=3,
        )
        # → "482019"
    """

    def poll_otp(
        self,
        imap_host: str,
        imap_port: int,
        email_address: str,
        app_password: str,
        sender_filter: Optional[str] = None,
        to_filter: Optional[str] = None,
        timeout: int = 60,
        interval: int = 3,
    ) -> str:
        """
        Poll the IMAP mailbox until an OTP email arrives or *timeout* seconds elapse.

        Args:
            imap_host: IMAP server hostname (e.g. "imap.gmail.com").
            imap_port: IMAP port (default 993 for TLS).
            email_address: Mailbox login address.
            app_password: App password (not account password for Gmail/Outlook).
            sender_filter: Optional FROM address to narrow the search.
            to_filter: Optional TO address (useful for +alias routing).
            timeout: Maximum seconds to wait for an OTP email.
            interval: Seconds between polls.

        Returns:
            The OTP string extracted from the email body.

        Raises:
            TimeoutError: When no OTP email is found within *timeout* seconds.
        """
        today_str = date.today().strftime("%d-%b-%Y")
        deadline = time.monotonic() + timeout

        with imaplib.IMAP4_SSL(imap_host, imap_port) as imap:
            imap.login(email_address, app_password)
            imap.select("INBOX")

            while time.monotonic() < deadline:
                criteria = self._build_search_criteria(today_str, sender_filter, to_filter)

                status, data = imap.search(None, *criteria)
                if status == "OK" and data and data[0]:
                    uid_list = data[0].split()
                    # Iterate newest-first (highest UID = most recently delivered
                    # email) so we always pick up the latest OTP even when
                    # previous emails from the same session are still unread.
                    for uid in reversed(uid_list):
                        otp = self._fetch_and_extract_otp(imap, uid)
                        if otp:
                            logger.info(
                                "EmailOTPService: OTP found in message uid=%s", uid.decode()
                            )
                            return otp

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(interval, remaining))

        raise TimeoutError(
            f"No OTP email found in {email_address} within {timeout} seconds."
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_search_criteria(
        self,
        today_str: str,
        sender_filter: Optional[str],
        to_filter: Optional[str],
    ) -> list[str]:
        """
        Build IMAP SEARCH criteria list.

        Uses ALL (not UNSEEN) so that emails already opened in the Gmail web
        UI are still found.  The newest-first UID iteration ensures we always
        pick the latest OTP even when multiple OTP emails from the same test
        session are in the inbox.
        """
        criteria: list[str] = [f"SINCE {today_str}"]
        if sender_filter:
            criteria += ["FROM", sender_filter]
        if to_filter:
            criteria += ["TO", to_filter]
        return criteria

    def _fetch_and_extract_otp(self, imap, uid: bytes) -> Optional[str]:
        """Fetch a message by uid and return the first OTP found, or None."""
        status, msg_data = imap.fetch(uid, "(RFC822)")
        if status != "OK" or not msg_data:
            return None

        raw = msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
        if not isinstance(raw, bytes):
            return None

        msg = message_from_bytes(raw, policy=email_policy)
        body = self._extract_body(msg)
        return extract_otp_from_text(body)

    @staticmethod
    def _extract_body(msg) -> str:
        """Extract plain-text body from an email.Message."""
        if msg.is_multipart():
            parts: list[str] = []
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype in ("text/plain", "text/html"):
                    try:
                        parts.append(part.get_content())
                    except Exception:
                        pass
            return "\n".join(parts)
        try:
            return msg.get_content()
        except Exception:
            return str(msg.get_payload(decode=True) or "")


# Module-level singleton used by execution engines
email_otp_service = EmailOTPService()
