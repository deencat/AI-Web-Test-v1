"""Pydantic schemas for product program manifests (PG)."""
from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class InitiativeAmendment(BaseModel):
    type: str
    amended_at: Optional[str] = None
    previous_effective_to: Optional[str] = None
    new_effective_to: Optional[str] = None
    note: Optional[str] = None


class InitiativeSummary(BaseModel):
    id: str
    kind: str
    title: str
    effective_from: str
    effective_to: Optional[str] = None
    resolved_effective_to: Optional[str] = None
    relationship: Optional[Literal["replace", "stack"]] = None
    relates_to: list[str] = Field(default_factory=list)
    audience: Optional[Literal["new_signups", "all", "existing_only"]] = None
    capability_keys: list[str] = Field(default_factory=list)
    platform_components: list[str] = Field(default_factory=list)
    regression_tags: list[str] = Field(default_factory=list)
    amendments: list[InitiativeAmendment] = Field(default_factory=list)


class ReferenceLayerSummary(BaseModel):
    id: str
    title: str
    capability_key: Optional[str] = None
    automate: bool = False
    parity_note: Optional[str] = None


class PlatformComponentSummary(BaseModel):
    id: str
    title: str
    modules: list[str] = Field(default_factory=list)
    test_surfaces: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ProgramSummary(BaseModel):
    slug: str
    title: str
    kind: Optional[str] = None
    test_scope: Optional[str] = None
    initiative_count: int = 0
    active_initiative_count: int = 0


class ProgramListResponse(BaseModel):
    items: list[ProgramSummary]
    total: int


class ProgramDetailResponse(BaseModel):
    slug: str
    program: dict[str, Any]
    platform_components: list[PlatformComponentSummary]
    reference_layers: list[ReferenceLayerSummary]
    initiatives: list[InitiativeSummary]
    hub_gaps: list[dict[str, Any]] = Field(default_factory=list)
    factory: Optional[dict[str, Any]] = None
    orchestration_suites: list[dict[str, Any]] = Field(default_factory=list)


class ProgramManifestRawResponse(BaseModel):
    slug: str
    yaml_content: str


class ProgramManifestSaveRequest(BaseModel):
    yaml_content: str


class ProgramManifestSaveResponse(BaseModel):
    slug: str
    message: str


class ProgramSeedJourneysResponse(BaseModel):
    slug: str
    journeys_upserted: int
    journeys_retired: int


class ReqIQOnboardingItem(BaseModel):
    initiative_id: str
    initiative_title: str
    source_files: list[str]
    capability_keys: list[str]


class ReqIQOnboardingResponse(BaseModel):
    program_slug: str
    reqiq_project_id: Optional[str] = None
    items: list[ReqIQOnboardingItem]
    steps: list[str]
