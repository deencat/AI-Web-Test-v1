"""Local cache of product workspace uploads for vision re-processing (UF-2.7)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_STORE_ROOT = Path(__file__).resolve().parents[2] / "data" / "product-documents"
_MANIFEST = "manifest.json"
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
_MVP_EXT = {".xlsx", ".xls", ".csv", ".json", ".yaml", ".yml"}


def _product_dir(product_id: str) -> Path:
    return _STORE_ROOT / product_id


def _manifest_path(product_id: str) -> Path:
    return _product_dir(product_id) / _MANIFEST


def _load_manifest(product_id: str) -> list[dict[str, Any]]:
    path = _manifest_path(product_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("files") or [])
    except (json.JSONDecodeError, OSError):
        return []


def _save_manifest(product_id: str, files: list[dict[str, Any]]) -> None:
    root = _product_dir(product_id)
    root.mkdir(parents=True, exist_ok=True)
    _manifest_path(product_id).write_text(
        json.dumps({"files": files}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_upload(
    product_id: str,
    filename: str,
    content: bytes,
    *,
    source_type: Optional[str] = None,
) -> Path:
    """Persist upload bytes for later UX vision / offer linking."""
    safe_name = Path(filename or "upload").name
    root = _product_dir(product_id)
    root.mkdir(parents=True, exist_ok=True)
    dest = root / safe_name
    dest.write_bytes(content)

    files = _load_manifest(product_id)
    files = [f for f in files if f.get("filename") != safe_name]
    files.append(
        {
            "filename": safe_name,
            "source_type": source_type,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "size": len(content),
        }
    )
    _save_manifest(product_id, files)
    return dest


def list_uploads(product_id: str, *, source_type: Optional[str] = None) -> list[dict[str, Any]]:
    files = _load_manifest(product_id)
    if source_type:
        return [f for f in files if f.get("source_type") == source_type]
    return files


def list_ux_ui_image_paths(product_id: str) -> list[Path]:
    root = _product_dir(product_id)
    if not root.is_dir():
        return []
    paths: list[Path] = []
    for entry in list_uploads(product_id, source_type="ux_ui"):
        p = root / entry["filename"]
        if p.is_file() and p.suffix.lower() in _IMAGE_EXT:
            paths.append(p)
    return sorted(paths)


def list_mvp_config_paths(product_id: str) -> list[Path]:
    root = _product_dir(product_id)
    if not root.is_dir():
        return []
    paths: list[Path] = []
    for entry in list_uploads(product_id, source_type="mvp_config"):
        p = root / entry["filename"]
        if p.is_file() and p.suffix.lower() in _MVP_EXT:
            paths.append(p)
    return sorted(paths)


def read_upload_bytes(product_id: str, filename: str) -> Optional[bytes]:
    path = _product_dir(product_id) / Path(filename).name
    if path.is_file():
        return path.read_bytes()
    return None
