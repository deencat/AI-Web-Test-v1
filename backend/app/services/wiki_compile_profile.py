"""Wiki compile profiles for Product workspace (UF-3)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_PROFILES_DIR = Path(__file__).resolve().parents[2] / "config" / "wiki-profiles"


class WikiProfileError(ValueError):
    pass


def list_wiki_profiles() -> list[str]:
    if not _PROFILES_DIR.is_dir():
        return []
    return sorted(p.stem for p in _PROFILES_DIR.glob("*.yaml"))


def load_wiki_profile(name: str) -> dict[str, Any]:
    path = _PROFILES_DIR / f"{name}.yaml"
    if not path.is_file():
        raise WikiProfileError(f"Unknown wiki profile: {name}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not data.get("feature"):
        raise WikiProfileError(f"Wiki profile '{name}' missing feature prompt")
    return data


def get_compile_feature(profile_name: str) -> str:
    return str(load_wiki_profile(profile_name)["feature"])
