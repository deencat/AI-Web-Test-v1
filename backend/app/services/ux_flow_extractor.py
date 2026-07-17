"""Extract purchase journeys from UX/UI flow images via vision LLM (UF-2.7 … UF-4.5)."""
from __future__ import annotations

import io
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

ProgressCallback = Callable[[str, int, str], Awaitable[None] | None]

from app.services.product_document_store import list_mvp_config_paths, list_ux_ui_image_paths
from app.services.wiki_journey_merge import CUSTOMER_JOURNEYS_HEADING, PURCHASE_JOURNEYS_HEADING

logger = logging.getLogger(__name__)

# Tile wide Figma boards for readable vision input (P4)
_MAX_VISION_WIDTH = 3200
_MAX_VISION_HEIGHT = 3200
_TILE_OVERLAP_PX = 120

_VISION_SYSTEM = """You are a senior telecom DT QA analyst reading My3 app purchase-flow Figma boards.
Extract E2E-testable journeys: exact UI labels (English + Traditional Chinese), buttons, prices, branches.
Output ONLY markdown. Use step tables. Mark [illegible] only when text is truly unreadable — do not invent."""

_VISION_USER = """Analyse this UX/UI flow image for 5G mobile broadband (5GBB) / Wi-Fi plan purchase in the My3 app.

This board may be wide — extract EVERY visible screen in reading order (left→right).

Emit markdown using EXACTLY this structure:

### {Journey name — from image title or filename}
- **Entry point:** (promo banner, 購買 tab, deep link — be specific)
- **Status:** active | ended | unknown
- **Offer track:** (mbase / HSBC / student / dec promo — if visible)

#### Branching
- Login vs Before Login (guest skips 購買 hub?)
- New vs Existing customer
- Payment method variants (Visa, AlipayHK, WeChat Pay, UnionPay)
- Any diamond decision nodes — quote visible label text

#### Steps
| Step | Screen (UI copy) | User action | Expected / assert | UI labels (EN + 繁中) |
|------|------------------|-------------|-------------------|------------------------|
| 1 | … | Tap … | … | … |

Include ALL phases if visible: banner → plan list → 選擇 → configure contract → 總結 → 確認訂單 → 預約日期 → 結賬 accordion (1–7) → 成功付款.
Quote prices ($238, $191, $100 SIM fee, etc.) and contract lengths (12/24/30/48 months) when shown.

#### Payment & completion
- Upfront amount, payment methods, success screen text (e.g. 成功付款)

#### Related offers
- Plan names, promo codes, router types (Wi-Fi 6 / Wi-Fi 7)

If this is a tile segment of a wide board, extract only screens visible in this segment."""

_CUSTOMER_SUMMARY_SYSTEM = """Summarise purchase journeys for business readers in 2-4 short paragraphs per journey."""


@dataclass
class JourneyExtractionResult:
    journeys_markdown: str = ""
    customer_summary_markdown: str = ""
    images_processed: int = 0
    tiles_processed: int = 0
    vision_used: bool = False
    errors: list[str] = field(default_factory=list)
    journey_names: list[str] = field(default_factory=list)


def _vision_provider() -> str:
    return os.getenv("UX_FLOW_VISION_PROVIDER", "openrouter").strip().lower()


def _vision_model() -> Optional[str]:
    return os.getenv("UX_FLOW_VISION_MODEL") or None


def _split_image_tiles(image_bytes: bytes) -> list[bytes]:
    """Split oversized flow boards into horizontal tiles (P4)."""
    try:
        from PIL import Image
    except ImportError:
        return [image_bytes]

    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    if w <= _MAX_VISION_WIDTH and h <= _MAX_VISION_HEIGHT:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return [buf.getvalue()]

    tiles: list[bytes] = []
    if w > _MAX_VISION_WIDTH:
        step = _MAX_VISION_WIDTH - _TILE_OVERLAP_PX
        x = 0
        while x < w:
            x1 = min(x + _MAX_VISION_WIDTH, w)
            crop = img.crop((x, 0, x1, h))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            tiles.append(buf.getvalue())
            if x1 >= w:
                break
            x += step
    else:
        step = _MAX_VISION_HEIGHT - _TILE_OVERLAP_PX
        y = 0
        while y < h:
            y1 = min(y + _MAX_VISION_HEIGHT, h)
            crop = img.crop((0, y, w, y1))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            tiles.append(buf.getvalue())
            if y1 >= h:
                break
            y += step
    return tiles or [image_bytes]


def _parse_response_text(response: dict) -> str:
    """Extract assistant text from unified or OpenAI-style vision responses."""
    if not response:
        return ""

    content = response.get("content") or response.get("message")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        text = "\n".join(parts).strip()
        if text:
            return text
    elif content:
        return str(content).strip()

    choices = response.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        msg_content = message.get("content")
        if isinstance(msg_content, str) and msg_content.strip():
            return msg_content.strip()
        if isinstance(msg_content, list):
            parts = []
            for block in msg_content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                    elif "text" in block:
                        parts.append(str(block["text"]))
            text = "\n".join(parts).strip()
            if text:
                return text

    return ""


def _journey_name_from_markdown(section: str) -> str:
    match = re.search(r"^###\s+(.+)$", section, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _offer_context_from_mvp_files(product_id: str) -> str:
    """Light offer hints from uploaded MVP / offer table files (P4)."""
    paths = list_mvp_config_paths(product_id)
    if not paths:
        return ""
    lines = ["Uploaded offer/config files (link journeys to CRM rows when compiling tests):"]
    for p in paths:
        lines.append(f"- {p.name}")
        if p.suffix.lower() == ".xlsx":
            try:
                import pandas as pd

                xl = pd.ExcelFile(p)
                for sheet in xl.sheet_names[:5]:
                    if any(k in sheet.lower() for k in ("5gbb", "mass", "mkt", "offer")):
                        df = pd.read_excel(p, sheet_name=sheet, header=None)
                        offer_rows = 0
                        for i in range(min(len(df), 120)):
                            val = df.iloc[i, 1] if df.shape[1] > 1 else None
                            if isinstance(val, str) and "5GBB" in val.upper():
                                offer_rows += 1
                        lines.append(f"  - Sheet `{sheet}`: ~{offer_rows} offer name rows detected")
            except Exception as exc:
                lines.append(f"  - (could not parse xlsx: {exc})")
    return "\n".join(lines)


def _placeholder_section(path: Path, reason: str) -> str:
    stem = path.stem.replace("_", " ")
    return f"""### {stem}
- **Entry point:** [Upload vision — {reason}]
- **Status:** unknown

#### Steps
| Step | Screen | User action | Expected | UI labels |
|------|--------|-------------|----------|-----------|
| 1 | Entry | Open flow from banner or promo tile | Journey starts | [Re-run Update summary after fixing vision errors] |
"""


def _resolve_vision_config(
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[str, str]:
    """UX_FLOW_* env overrides; else caller-supplied user generation settings."""
    env_provider = os.getenv("UX_FLOW_VISION_PROVIDER", "").strip().lower()
    env_model = os.getenv("UX_FLOW_VISION_MODEL", "").strip()
    if env_provider:
        return env_provider, env_model or (_vision_model() or "gpt-5.2")
    if provider and model:
        return provider.lower(), model
    return _vision_provider(), _vision_model() or "gpt-5.2"


async def _vision_analyse_tile(
    llm: Any,
    tile_bytes: bytes,
    *,
    filename: str,
    tile_index: int,
    tile_total: int,
    offer_context: str,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
) -> str:
    user_text = _VISION_USER
    if tile_total > 1:
        user_text += f"\n\nNote: This is tile {tile_index + 1} of {tile_total} of a wide flow board `{filename}`. Extract steps visible in this segment only."
    if offer_context:
        user_text += f"\n\n{offer_context}"

    v_provider, v_model = _resolve_vision_config(
        provider=vision_provider,
        model=vision_model,
    )
    response = await llm.vision_completion(
        tile_bytes,
        _VISION_SYSTEM,
        user_text,
        provider=v_provider,
        model=v_model,
        max_tokens=int(os.getenv("UX_FLOW_VISION_MAX_TOKENS", "8192")),
    )
    return _parse_response_text(response)


async def _report_progress(
    progress: Optional[ProgressCallback],
    step: str,
    percent: int,
    detail: str = "",
) -> None:
    if not progress:
        return
    maybe = progress(step, percent, detail)
    if maybe is not None:
        await maybe


async def _extract_single_image(
    llm: Any,
    path: Path,
    *,
    offer_context: str,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
    progress: Optional[ProgressCallback] = None,
    progress_label: str = "",
    progress_base: int = 0,
    progress_span: int = 0,
) -> tuple[str, int, bool]:
    image_bytes = path.read_bytes()
    tiles = _split_image_tiles(image_bytes)
    sections: list[str] = []
    vision_ok = False
    for i, tile in enumerate(tiles):
        if progress and progress_span:
            tile_pct = progress_base + int(progress_span * i / max(len(tiles), 1))
            tile_detail = progress_label
            if len(tiles) > 1:
                tile_detail = f"{progress_label} — section {i + 1}/{len(tiles)}"
            await _report_progress(progress, "Analysing UX/UI flows", tile_pct, tile_detail)
        try:
            text = await _vision_analyse_tile(
                llm,
                tile,
                filename=path.name,
                tile_index=i,
                tile_total=len(tiles),
                offer_context=offer_context,
                vision_provider=vision_provider,
                vision_model=vision_model,
            )
            if text:
                sections.append(text)
                vision_ok = True
        except Exception as exc:
            exc_name = type(exc).__name__
            if exc_name == "VisionNotSupportedError":
                logger.warning("Vision not available for %s: %s", path.name, exc)
                return _placeholder_section(path, str(exc)), len(tiles), False
            logger.warning("Vision failed for %s tile %s: %s", path.name, i, exc)
            sections.append(f"<!-- tile {i + 1} error: {exc} -->")

    if not sections:
        return _placeholder_section(path, "no vision output"), len(tiles), False

    if len(sections) == 1:
        return sections[0], len(tiles), vision_ok

    merged = f"### {path.stem.replace('_', ' ')} (multi-tile)\n\n" + "\n\n---\n\n".join(sections)
    return merged, len(tiles), vision_ok


async def _build_customer_summary(
    llm: Any,
    journey_body: str,
    *,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
) -> str:
    if not journey_body.strip():
        return ""
    v_provider, v_model = _resolve_vision_config(provider=vision_provider, model=vision_model)
    try:
        response = await llm.chat_completion(
            [
                {"role": "system", "content": _CUSTOMER_SUMMARY_SYSTEM},
                {
                    "role": "user",
                    "content": f"Summarise these purchase journeys for QA and business users:\n\n{journey_body[:8000]}",
                },
            ],
            provider=v_provider,
            model=v_model,
            max_tokens=1024,
        )
        return _parse_response_text(response)
    except Exception as exc:
        logger.warning("Customer journey summary failed: %s", exc)
        return ""


def assemble_journeys_markdown(sections: list[str], customer_summary: str = "") -> str:
    body = "\n\n".join(s.strip() for s in sections if s.strip())
    if not body:
        return ""
    out = f"{PURCHASE_JOURNEYS_HEADING}\n\n{body}"
    if customer_summary.strip():
        out += f"\n\n{CUSTOMER_JOURNEYS_HEADING}\n\n{customer_summary.strip()}\n"
    return out


async def extract_journeys_for_product(
    product_id: str,
    *,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
    progress: Optional[ProgressCallback] = None,
    progress_base: int = 0,
    progress_span: int = 0,
) -> JourneyExtractionResult:
    """Run vision extraction on all cached ux_ui images for a product."""
    from app.services.universal_llm import UniversalLLMService

    result = JourneyExtractionResult()
    paths = list_ux_ui_image_paths(product_id)
    if not paths:
        return result

    offer_context = _offer_context_from_mvp_files(product_id)
    llm = UniversalLLMService()
    sections: list[str] = []
    total = len(paths)

    for idx, path in enumerate(paths):
        img_base = progress_base + int(progress_span * idx / total) if total and progress_span else progress_base
        img_span = int(progress_span / total) if total and progress_span else progress_span
        label = f"Flow {idx + 1}/{total}: {path.name}"
        await _report_progress(progress, "Analysing UX/UI flows", img_base, label)
        try:
            section, tiles, used_vision = await _extract_single_image(
                llm,
                path,
                offer_context=offer_context,
                vision_provider=vision_provider,
                vision_model=vision_model,
                progress=progress,
                progress_label=label,
                progress_base=img_base,
                progress_span=img_span,
            )
            sections.append(section)
            result.images_processed += 1
            result.tiles_processed += tiles
            if used_vision:
                result.vision_used = True
            name = _journey_name_from_markdown(section) or path.stem
            if name:
                result.journey_names.append(name)
        except Exception as exc:
            result.errors.append(f"{path.name}: {exc}")
            sections.append(_placeholder_section(path, str(exc)))

    customer_summary = ""
    if sections and result.vision_used:
        await _report_progress(
            progress,
            "Analysing UX/UI flows",
            progress_base + progress_span - 2 if progress_span else progress_base,
            "Writing customer journey summary…",
        )
        customer_summary = await _build_customer_summary(
            llm,
            "\n\n".join(sections),
            vision_provider=vision_provider,
            vision_model=vision_model,
        )

    result.journeys_markdown = assemble_journeys_markdown(sections, customer_summary)
    return result


def build_compile_feature_supplement(journeys_markdown: str) -> str:
    """Short compile hint only — full journey markdown must not go in the compile URL."""
    if not journeys_markdown.strip():
        return ""
    return (
        "Purchase journeys were pre-extracted from UX/UI images in a separate vision step. "
        "Focus this compile on ## Base offer, ## Active promotions, and related offer sections. "
        "Purchase journeys will be merged after compile.\n\n"
    )
