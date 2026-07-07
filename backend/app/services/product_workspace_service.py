"""Product workspace loader and persistence (UF unified)."""
from __future__ import annotations

import re
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


def _save_config(data: dict[str, Any]) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def slug_from_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        raise ProductWorkspaceError("Product name must contain letters or numbers")
    return slug[:64]


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


def create_product_entry(
    *,
    product_id: str,
    title: str,
    reqiq_project_id: str,
    title_zh: Optional[str] = None,
    webapp_url: Optional[str] = None,
    locale: str = "zh-HK",
) -> dict[str, Any]:
    data = _load_config()
    products = list(data.get("products") or [])
    if any(p.get("id") == product_id for p in products):
        raise ProductWorkspaceError(f"Product already exists: {product_id}")

    entry: dict[str, Any] = {
        "id": product_id,
        "title": title,
        "locale": locale,
        "reqiq_project_id": reqiq_project_id,
        "program_slug": product_id,
        "wiki_profile": "telecom-promo",
        "pilot": False,
    }
    if title_zh:
        entry["title_zh"] = title_zh
    if webapp_url:
        entry["default_urls"] = {"webapp": webapp_url}

    products.append(entry)
    data["products"] = products
    _save_config(data)
    return entry


def update_product_entry(
    product_id: str,
    *,
    title: Optional[str] = None,
    title_zh: Optional[str] = None,
    webapp_url: Optional[str] = None,
) -> dict[str, Any]:
    data = _load_config()
    products = list(data.get("products") or [])
    found: Optional[dict[str, Any]] = None
    for p in products:
        if p.get("id") == product_id:
            found = p
            break
    if not found:
        raise ProductWorkspaceError(f"Product not found: {product_id}")

    if title is not None:
        found["title"] = title
    if title_zh is not None:
        found["title_zh"] = title_zh or None
    if webapp_url is not None:
        urls = dict(found.get("default_urls") or {})
        if webapp_url:
            urls["webapp"] = webapp_url
        else:
            urls.pop("webapp", None)
        found["default_urls"] = urls

    data["products"] = products
    _save_config(data)
    return dict(found)
