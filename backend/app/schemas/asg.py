"""Pydantic schemas for ASG API endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ASGPolicyLimits(BaseModel):
    max_nodes: int = Field(default=150, ge=1, le=500)
    max_depth: int = Field(default=20, ge=1, le=100)
    max_branching: int = Field(default=8, ge=1, le=50)
    domain_allowlist: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)


class ASGBuildRequest(BaseModel):
    target_url: HttpUrl
    seed_intents: List[str] = Field(default_factory=list)
    flow_steps: List[Dict[str, Any]] = Field(default_factory=list)
    policy: ASGPolicyLimits = Field(default_factory=ASGPolicyLimits)
    project_id: Optional[int] = None
    seed_hash: Optional[str] = None
    page_context: Dict[str, Any] = Field(default_factory=dict)
    readiness_snapshots: List[Dict[str, Any]] = Field(default_factory=list)


class ASGConfidenceSummary(BaseModel):
    mean: float
    min: float
    max: float
    below_threshold_count: int
    threshold: float


class ASGBuildStats(BaseModel):
    node_count: int
    edge_count: int
    terminal_nodes: int
    policy_hits: List[str] = Field(default_factory=list)
    build_duration_ms: int


class ASGBuildResponse(BaseModel):
    graph_id: int
    status: str
    seed_hash: str
    stats: ASGBuildStats
    confidence: ASGConfidenceSummary


class ASGGraphDetailResponse(BaseModel):
    graph_id: int
    project_id: Optional[int]
    status: str
    seed_hash: str
    confidence_score: float
    node_count: int
    edge_count: int
    confidence_distribution: Dict[str, float]
    created_at: str
    updated_at: str


class ASGPlanGoal(BaseModel):
    mode: Literal["shortest_path", "requirement_coverage", "risk_first"] = "shortest_path"
    requirement_ids: List[str] = Field(default_factory=list)
    risk_profile: str = "balanced"
    max_paths: int = Field(default=5, ge=1, le=50)
    target_node_fingerprint: Optional[str] = None


class ASGPlannedPath(BaseModel):
    path_id: int
    goal_type: str
    node_fingerprints: List[str]
    edge_keys: List[str]
    score: float
    risk_score: float
    confidence: float
    rationale: str


class ASGPlanResponse(BaseModel):
    graph_id: int
    plan_id: str
    paths: List[ASGPlannedPath]


class ASGSynthesizeRequest(BaseModel):
    path_ids: List[int] = Field(..., min_length=1)
    synthesis_profile: str = "default"
    save_test_cases: bool = False
    test_title_prefix: str = "ASG Generated"
    login_credentials: Optional[Dict[str, str]] = None
    plan_id: Optional[str] = None


class ASGSynthesizedDraftTest(BaseModel):
    synthesis_id: int
    path_id: int
    steps: List[str]
    provenance: Dict[str, Any]
    validation_score: Optional[float] = None
    test_case_id: Optional[int] = None


class ASGSynthesizeResponse(BaseModel):
    graph_id: int
    synthesis_id: Optional[str] = None
    tests: List[ASGSynthesizedDraftTest] = Field(default_factory=list)
    fallback_reason_code: Optional[str] = None
    confidence_gate_passed: bool = True


class ASGValidateResponse(BaseModel):
    graph_id: int
    replay_confidence: float
    node_confidence_mean: float
    edge_confidence_mean: float
    fallback_recommended: bool
    fallback_reason_code: Optional[str] = None
    threshold: float
