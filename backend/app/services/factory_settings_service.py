"""QA Factory system settings — UI overrides for server .env."""
from __future__ import annotations

import time
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.constants.factory_profiles import FACTORY_PROFILE_DISPLAY_NAMES
from app.core.config import settings
from app.models.system_settings import SystemSettings

_SINGLETON_ID = 1


def get_system_settings_row(db: Session) -> SystemSettings:
    row = db.query(SystemSettings).filter(SystemSettings.id == _SINGLETON_ID).first()
    if row is None:
        row = SystemSettings(id=_SINGLETON_ID)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_env_bridge_url() -> Optional[str]:
    raw = settings.HERMES_BRIDGE_URL
    if raw and raw.strip():
        return raw.strip().rstrip("/")
    return None


def get_effective_bridge_url(db: Session) -> Optional[str]:
    row = get_system_settings_row(db)
    override = row.factory_orchestrator_bridge_url
    if override and override.strip():
        return override.strip().rstrip("/")
    return get_env_bridge_url()


def build_qa_factory_settings_response(db: Session) -> dict:
    row = get_system_settings_row(db)
    env_url = get_env_bridge_url()
    override = (
        row.factory_orchestrator_bridge_url.strip().rstrip("/")
        if row.factory_orchestrator_bridge_url and row.factory_orchestrator_bridge_url.strip()
        else None
    )
    effective = override or env_url
    return {
        "orchestrator_bridge_url_override": override,
        "env_bridge_url": env_url,
        "effective_bridge_url": effective,
        "routing_enabled": bool(effective),
        "profile_display_names": dict(FACTORY_PROFILE_DISPLAY_NAMES),
    }


def update_orchestrator_bridge_override(db: Session, url: Optional[str]) -> dict:
    row = get_system_settings_row(db)
    row.factory_orchestrator_bridge_url = url
    db.commit()
    db.refresh(row)
    return build_qa_factory_settings_response(db)


def check_orchestrator_bridge_health(db: Session) -> dict:
    effective = get_effective_bridge_url(db)
    if not effective:
        return {
            "status": "unconfigured",
            "effective_bridge_url": None,
            "message": "No orchestrator node URL configured. Set one in Settings or HERMES_BRIDGE_URL in .env.",
        }

    health_url = f"{effective}/health"
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(health_url)
            latency_ms = int((time.perf_counter() - started) * 1000)
            if resp.is_success:
                return {
                    "status": "healthy",
                    "effective_bridge_url": effective,
                    "message": "QA Orchestrator node responded OK",
                    "latency_ms": latency_ms,
                }
            return {
                "status": "unhealthy",
                "effective_bridge_url": effective,
                "message": f"HTTP {resp.status_code} from {health_url}",
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "status": "unreachable",
            "effective_bridge_url": effective,
            "message": str(exc),
            "latency_ms": latency_ms,
        }
