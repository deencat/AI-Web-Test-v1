"""Capture and diff URL snapshots for Loop C (HF-4)."""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.crud import url_snapshot as crud_snapshots
from app.models.url_snapshot import UrlSnapshot

logger = logging.getLogger(__name__)

_INTERACTIVE_RE = re.compile(
    r"<(button|input|select|textarea|a)\b[^>]*>",
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).lower().encode()).hexdigest()[:32]


def html_summary(html: str, max_len: int = 2000) -> str:
    cleaned = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", cleaned)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def element_fingerprint(html: str) -> str:
    signatures: list[str] = []
    for match in _INTERACTIVE_RE.finditer(html):
        tag = re.sub(r"\s+", " ", match.group(0).lower())
        signatures.append(tag[:240])
    payload = "\n".join(sorted(set(signatures)))
    return hashlib.sha256(payload.encode()).hexdigest()


def text_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def fetch_page_html(
    url: str,
    http_credentials: Optional[dict[str, str]] = None,
    timeout: float = 30.0,
) -> Tuple[str, int, Optional[str]]:
    auth = None
    if http_credentials:
        auth = (
            http_credentials.get("username") or http_credentials.get("user"),
            http_credentials.get("password"),
        )
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, auth=auth)
        response.raise_for_status()
        title_match = _TITLE_RE.search(response.text)
        title = title_match.group(1).strip() if title_match else None
        return response.text, response.status_code, title


def capture_snapshot(
    db: Session,
    url: str,
    *,
    http_credentials: Optional[dict[str, str]] = None,
) -> UrlSnapshot:
    html, status_code, title = fetch_page_html(url, http_credentials=http_credentials)
    row = UrlSnapshot(
        url=normalize_url(url),
        url_hash=url_hash(url),
        page_title=title,
        html_summary=html_summary(html),
        element_fingerprint=element_fingerprint(html),
        status_code=status_code,
        capture_meta={"method": "httpx"},
    )
    return crud_snapshots.create_snapshot(db, row)


def diff_snapshot_records(
    baseline: UrlSnapshot,
    current: UrlSnapshot,
    *,
    similarity_threshold: float = 0.85,
) -> Dict[str, Any]:
    fingerprint_changed = baseline.element_fingerprint != current.element_fingerprint
    similarity = text_similarity(baseline.html_summary or "", current.html_summary or "")
    material = fingerprint_changed or similarity < similarity_threshold

    parts: list[str] = []
    if fingerprint_changed:
        parts.append("Interactive element fingerprint changed.")
    if similarity < similarity_threshold:
        parts.append(f"Visible text similarity dropped to {similarity:.0%}.")
    if baseline.page_title != current.page_title:
        parts.append(
            f"Title changed: '{baseline.page_title or ''}' → '{current.page_title or ''}'."
        )
    if not parts:
        parts.append("No material change detected.")

    return {
        "material_change": material,
        "summary": " ".join(parts),
        "url": current.url,
        "url_hash": current.url_hash,
        "baseline_snapshot_id": baseline.id,
        "current_snapshot_id": current.id,
        "baseline_fingerprint": baseline.element_fingerprint,
        "current_fingerprint": current.element_fingerprint,
        "similarity_score": round(similarity, 4),
    }
