"""Product workspace loader (UF-1)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "product-workspaces.yaml"


class ProductWorkspaceError(ValueError):
    pass


def _load_config() -> dict[str, Any]:
    if not _CONFIG_PATH.is_file():
        return {"products": []}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {"products": []}


def list_products() -> list[dict[str, Any]]:
    return list(_load_config().get("products") or [])


def get_product(product_id: str) -> dict[str, Any]:
    for p in list_products():
        if p.get("id") == product_id:
            return dict(p)
    raise ProductWorkspaceError(f"Product not found: {product_id}")


def product_summary(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product["id"],
        "title": product.get("title") or product["id"],
        "title_zh": product.get("title_zh"),
        "locale": product.get("locale"),
        "pilot": bool(product.get("pilot")),
        "program_slug": product.get("program_slug"),
        "wiki_profile": product.get("wiki_profile"),
    }
