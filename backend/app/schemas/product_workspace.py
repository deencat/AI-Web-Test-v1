"""Pydantic schemas for Product workspace (UF)."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    id: str
    title: str
    title_zh: Optional[str] = None
    locale: Optional[str] = None
    pilot: bool = False
    program_slug: Optional[str] = None
    wiki_profile: Optional[str] = None


class ProductListResponse(BaseModel):
    items: list[ProductSummary]
    total: int


class ProductDetailResponse(BaseModel):
    id: str
    title: str
    title_zh: Optional[str] = None
    locale: Optional[str] = None
    pilot: bool = False
    program_slug: Optional[str] = None
    wiki_profile: Optional[str] = None
    default_urls: dict[str, str] = Field(default_factory=dict)
    reqiq_project_id: str


class ProductWorkspaceStatus(BaseModel):
    source_count: int = 0
    wiki_ready: bool = False
    wiki_stale: bool = False
    wiki_compiled_at: Optional[str] = None
    requirement_count: int = 0
    draft_requirement_count: int = 0
    readiness_score: Optional[float] = None


class ProductStatusResponse(BaseModel):
    product: ProductDetailResponse
    status: ProductWorkspaceStatus


class ProductSyncResponse(BaseModel):
    product_id: str
    program_slug: str
    initiatives_synced: int
    journeys_upserted: int
    journeys_retired: int
    tests_retired: int
    message: str = "Program synced from wiki"


class ProductGenerateTestsResponse(BaseModel):
    created: int = 0
    dedupe_dropped: int = 0
    batch_id: Optional[str] = None
    message: str = "Test scenarios generated from wiki"
    journey_guided: bool = False


class ProductCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    title_zh: Optional[str] = Field(None, max_length=200)
    webapp_url: Optional[str] = Field(None, max_length=500)
    id: Optional[str] = Field(None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProductUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    title_zh: Optional[str] = Field(None, max_length=200)
    webapp_url: Optional[str] = Field(None, max_length=500)


class ProductCreateResponse(BaseModel):
    product: ProductDetailResponse
    message: str = "Product ready — upload your documents to get started"


class ProductCompileWikiResponse(BaseModel):
    wiki: dict[str, Any] = Field(default_factory=dict)
    sync: Optional[ProductSyncResponse] = None
    message: str = "Summary updated from your documents"
    journeys_extracted: int = 0
    ux_sources_processed: int = 0
    vision_used: bool = False


class AllowedFormatsResponse(BaseModel):
    extensions: list[str]
    source_type_hints: dict[str, str]
