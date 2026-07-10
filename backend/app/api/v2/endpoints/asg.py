"""API v2: App State Graph (ASG) endpoints — Feature 3."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.asg import (
    ASGBuildRequest,
    ASGBuildResponse,
    ASGGraphDetailResponse,
    ASGPlanGoal,
    ASGPlanResponse,
    ASGSynthesizeRequest,
    ASGSynthesizeResponse,
    ASGValidateResponse,
)
from app.services.asg_service import ASGService, get_asg_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_asg_enabled() -> None:
    from app.core.config import settings

    if not getattr(settings, "ASG_ENABLED", False) and not getattr(settings, "ASG_SHADOW_MODE", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ASG feature is disabled (ASG_ENABLED and ASG_SHADOW_MODE are both off)",
        )


@router.post(
    "/build",
    response_model=ASGBuildResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Build ASG graph from crawl artifacts",
)
def build_graph(
    request: ASGBuildRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    asg_service: ASGService = Depends(get_asg_service),
) -> ASGBuildResponse:
    _require_asg_enabled()
    try:
        return asg_service.build_graph(db, request, created_by=current_user.id)
    except Exception as exc:
        logger.exception("ASG build failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{graph_id}",
    response_model=ASGGraphDetailResponse,
    summary="Get ASG graph metadata and confidence distribution",
)
def get_graph(
    graph_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    asg_service: ASGService = Depends(get_asg_service),
) -> ASGGraphDetailResponse:
    _require_asg_enabled()
    try:
        return asg_service.get_graph_detail(db, graph_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{graph_id}/plan",
    response_model=ASGPlanResponse,
    summary="Plan deterministic paths through the graph",
)
def plan_paths(
    graph_id: int,
    goal: ASGPlanGoal,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    asg_service: ASGService = Depends(get_asg_service),
) -> ASGPlanResponse:
    _require_asg_enabled()
    try:
        return asg_service.plan_paths(db, graph_id, goal)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{graph_id}/synthesize",
    response_model=ASGSynthesizeResponse,
    summary="Synthesize draft tests from planned paths",
)
def synthesize_tests(
    graph_id: int,
    request: ASGSynthesizeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    asg_service: ASGService = Depends(get_asg_service),
) -> ASGSynthesizeResponse:
    _require_asg_enabled()
    try:
        return asg_service.synthesize_tests(
            db, graph_id, request, user_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{graph_id}/validate",
    response_model=ASGValidateResponse,
    summary="Validate replay confidence and fallback recommendation",
)
def validate_graph(
    graph_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    asg_service: ASGService = Depends(get_asg_service),
) -> ASGValidateResponse:
    _require_asg_enabled()
    try:
        return asg_service.validate_graph(db, graph_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
