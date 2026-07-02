"""Schemas for QA Factory connection settings (Agent Console → orchestrator node)."""
from typing import Optional

from pydantic import BaseModel, Field, validator


class QaFactorySettingsResponse(BaseModel):
    """Effective factory orchestrator connection for the Agent Console."""

    orchestrator_bridge_url_override: Optional[str] = Field(
        None,
        description="URL set in Settings UI; empty means use server .env default",
    )
    env_bridge_url: Optional[str] = Field(
        None,
        description="HERMES_BRIDGE_URL from server .env (read-only)",
    )
    effective_bridge_url: Optional[str] = Field(
        None,
        description="URL used for routing (override wins when set)",
    )
    routing_enabled: bool = Field(
        ...,
        description="True when Agent Console forwards jobs to the orchestrator node",
    )
    profile_display_names: dict[str, str] = Field(
        default_factory=dict,
        description="Human-readable names for factory specialist profiles",
    )


class QaFactorySettingsUpdate(BaseModel):
    """Update orchestrator node URL override from Settings page."""

    orchestrator_bridge_url: Optional[str] = Field(
        None,
        description="Full bridge URL e.g. http://192.168.1.50:8790; null or empty clears override",
    )

    @validator("orchestrator_bridge_url")
    def validate_bridge_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not trimmed.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(trimmed) > 500:
            raise ValueError("URL must be at most 500 characters")
        return trimmed.rstrip("/")


class QaFactoryHealthResponse(BaseModel):
    status: str
    effective_bridge_url: Optional[str] = None
    message: Optional[str] = None
    latency_ms: Optional[int] = None
