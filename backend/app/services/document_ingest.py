"""Document ingest helpers for Product workspace (UF-2)."""
from __future__ import annotations

from pathlib import Path

# Extensions accepted for business document upload
ALLOWED_SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".md",
        ".ppt",
        ".pptx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".json",
        ".yaml",
        ".yml",
        ".csv",
        ".xlsx",
        ".xls",
        ".xml",
        ".html",
        ".htm",
    }
)

SOURCE_TYPE_HINTS: dict[str, str] = {
    ".ppt": "marketing_deck",
    ".pptx": "marketing_deck",
    ".png": "ux_ui",
    ".jpg": "ux_ui",
    ".jpeg": "ux_ui",
    ".gif": "ux_ui",
    ".webp": "ux_ui",
    ".json": "mvp_config",
    ".yaml": "mvp_config",
    ".yml": "mvp_config",
    ".csv": "mvp_config",
    ".xlsx": "mvp_config",
}


def validate_filename(filename: str) -> None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_SOURCE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_SOURCE_EXTENSIONS))
        raise ValueError(f"File type '{ext or '(none)'}' not supported. Allowed: {allowed}")


def infer_source_type(filename: str) -> str | None:
    return SOURCE_TYPE_HINTS.get(Path(filename).suffix.lower())
