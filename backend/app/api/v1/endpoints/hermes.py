"""
Hermes Agent trigger endpoint — H2 ("Generate via Hermes" button in UI).

Sends a structured Telegram message to the qa-manager bot so Hermes starts
the full QA pipeline (requirements check → test generation → dispatch →
report).  Fire-and-forget: returns immediately; results arrive via Telegram
from qa-reporter (typically 8–15 min).

Required .env keys:
    TELEGRAM_BOT_TOKEN            — BotFather token for the qa-manager bot
    QA_MANAGER_TELEGRAM_CHAT_ID   — DM chat ID between your user and the bot

See docs/Hermes_QA_MultiAgent_Profiles_v4.md §"AI Web Test Webapp Integration"
for the full integration context.
"""
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


class HermesTriggerRequest(BaseModel):
    project: str
    feature: str
    feature_url: str
    env_config: dict = {}


class HermesTriggerResponse(BaseModel):
    status: str
    message: str


@router.post(
    "/hermes/trigger",
    response_model=HermesTriggerResponse,
    summary="Trigger Hermes QA pipeline via Telegram (H2)",
)
async def trigger_hermes(
    body: HermesTriggerRequest,
    _: User = Depends(get_current_user),
) -> HermesTriggerResponse:
    """Send a message to the qa-manager Telegram bot to start the Hermes pipeline.

    The backend calls the Telegram HTTP API server-side — the bot token is
    never exposed to the browser.

    Returns 503 when Telegram credentials are not configured in .env.
    Returns 502 when the Telegram API call fails.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.QA_MANAGER_TELEGRAM_CHAT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Hermes Telegram trigger is not configured. "
                "Set TELEGRAM_BOT_TOKEN and QA_MANAGER_TELEGRAM_CHAT_ID in backend/.env."
            ),
        )

    lines = [
        f"Generate and run tests for {body.feature} in {body.project}.",
        f"feature_url: {body.feature_url}",
    ]
    if body.env_config:
        lines.append(f"env_config: {body.env_config}")
    message = "\n".join(lines)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": settings.QA_MANAGER_TELEGRAM_CHAT_ID,
                    "text": message,
                },
            )
    except httpx.RequestError as exc:
        logger.error("Telegram API request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Telegram API: {exc}",
        )

    if resp.status_code != 200:
        logger.error("Telegram API returned %s: %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram API error {resp.status_code}: {resp.text}",
        )

    logger.info(
        "Hermes pipeline triggered for project=%s feature=%s", body.project, body.feature
    )
    return HermesTriggerResponse(
        status="accepted",
        message="Hermes pipeline started. Watch Telegram for results (8–15 min).",
    )
