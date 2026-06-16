"""Bypass HTTP proxies for local browser/CDP loopback traffic."""

import logging
import os

logger = logging.getLogger(__name__)


def ensure_loopback_no_proxy() -> None:
    """Bypass proxies for local browser/CDP traffic.

    Some Windows devices inject HTTP_PROXY/HTTPS_PROXY into the backend
    process. When Playwright or browser-use resolves a local CDP endpoint
    through that proxy, Chromium sees a non-loopback client and rejects
    /json/version with "Request on loopback from external IP". Ensure
    loopback hosts are always excluded before local CDP connections.
    """
    required_hosts = ("127.0.0.1", "localhost", "::1")
    existing_entries = []
    seen = set()

    for key in ("NO_PROXY", "no_proxy"):
        raw_value = os.environ.get(key, "")
        for entry in raw_value.split(","):
            cleaned = entry.strip()
            if cleaned and cleaned.lower() not in seen:
                existing_entries.append(cleaned)
                seen.add(cleaned.lower())

    missing_entries = [host for host in required_hosts if host.lower() not in seen]
    if not missing_entries:
        return

    merged_entries = existing_entries + missing_entries
    merged_value = ",".join(merged_entries)
    os.environ["NO_PROXY"] = merged_value
    os.environ["no_proxy"] = merged_value
    logger.info("Added loopback hosts to NO_PROXY for local CDP traffic")
