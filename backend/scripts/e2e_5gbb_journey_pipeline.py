"""E2E smoke: seed UX images → compile-wiki → verify Purchase journeys → generate-tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
UXUI = ROOT / "docs" / "5G 流動寬頻" / "UXUI"
PRODUCT_ID = "5g-mobile-broadband"
BASE = "http://127.0.0.1:8000/api/v1"

# Seed one high-res board + one smaller promo board for multi-flow coverage
SEED_IMAGES = [
    "5GBB Wi-Fi 7 Unlimited Plans.png",
    "5GBB Wi-Fi 6 & 7 Unlimited Plan - HSBC Offer.png",
]


def main() -> int:
    print("=== Login ===")
    login = requests.post(
        f"{BASE}/auth/login",
        data={"username": "admin", "password": "admin123"},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== Upload UX/UI to product workspace + ReqIQ ===")
    files = []
    for name in SEED_IMAGES:
        src = UXUI / name
        if not src.is_file():
            print(f"SKIP missing: {src}")
            continue
        files.append(
            (
                "files",
                (name, src.read_bytes(), "image/png"),
            )
        )
    if not files:
        print("FAIL: no seed images found")
        return 1

    upload_resp = requests.post(
        f"{BASE}/products/{PRODUCT_ID}/upload",
        headers=headers,
        files=files,
        timeout=120,
    )
    print(f"  upload status: {upload_resp.status_code}")
    if not upload_resp.ok:
        print(upload_resp.text[:2000])
        return 1
    print(f"  upload: {upload_resp.json()}")

    print("\n=== Compile wiki (vision extraction) ===")
    compile_resp = requests.post(
        f"{BASE}/products/{PRODUCT_ID}/compile-wiki",
        headers=headers,
        timeout=600,
    )
    print(f"  status: {compile_resp.status_code}")
    if not compile_resp.ok:
        print(compile_resp.text[:2000])
        return 1

    body = compile_resp.json()
    print(f"  journeys_extracted: {body.get('journeys_extracted')}")
    print(f"  ux_sources_processed: {body.get('ux_sources_processed')}")
    print(f"  vision_used: {body.get('vision_used')}")
    print(f"  message: {body.get('message')}")

    wiki = body.get("wiki") or {}
    wiki_md = str(wiki.get("markdown") or wiki.get("content") or "")
    has_pj = "## Purchase journeys" in wiki_md
    print(f"  wiki has Purchase journeys: {has_pj}")
    if has_pj:
        idx = wiki_md.index("## Purchase journeys")
        print("  excerpt:\n", wiki_md[idx : idx + 600], "\n...")

    if body.get("ux_sources_processed", 0) < 1:
        print("FAIL: no UX sources processed")
        return 1
    if not has_pj:
        print("FAIL: wiki missing ## Purchase journeys")
        return 1

    print("\n=== Generate tests ===")
    gen_resp = requests.post(
        f"{BASE}/products/{PRODUCT_ID}/generate-tests",
        headers=headers,
        timeout=300,
    )
    print(f"  status: {gen_resp.status_code}")
    if not gen_resp.ok:
        print(gen_resp.text[:2000])
        return 1

    gen = gen_resp.json()
    print(f"  created: {gen.get('created')}")
    print(f"  journey_guided: {gen.get('journey_guided')}")
    print(f"  message: {gen.get('message')}")

    if not gen.get("journey_guided"):
        print("WARN: journey_guided is false (wiki may lack section at read time)")

    print("\n=== PASS ===")
    print(json.dumps({"compile": body, "generate": gen}, indent=2, default=str)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
