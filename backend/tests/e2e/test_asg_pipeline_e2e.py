"""
E2E-style ASG pipeline test: build → plan → synthesize → execute → replay artifact.

Uses in-memory SQLite and mocked browser execution (no live Playwright).
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.crud import test_execution as crud_executions
from app.db.base import Base
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.asg import ASGBuildRequest, ASGPlanGoal, ASGSynthesizeRequest
from app.services.asg_metrics import (
    evaluate_canary_rollback,
    get_asg_metrics,
    reset_asg_metrics,
)
from app.services.asg_service import ASGService


FLOW = [
    {
        "order": 1,
        "action": "navigate",
        "target": "https://pipeline.example.com",
        "page_url": "https://pipeline.example.com",
        "page_title": "Home",
    },
    {
        "order": 2,
        "action": "click",
        "target": "Start",
        "page_url": "https://pipeline.example.com/start",
        "element_type": "button",
        "locator": {"role": "button", "text": "Start"},
        "extracted_content": "Clicked button 'Start'",
    },
]


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _rec):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(
        email="e2e@example.com",
        username="e2euser",
        hashed_password="x",
        role="user",
        is_active=True,
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


@pytest.fixture
def owner(db):
    return db.query(User).first()


@pytest.fixture(autouse=True)
def _reset_metrics():
    reset_asg_metrics()
    yield
    reset_asg_metrics()


@pytest.mark.asyncio
async def test_asg_full_pipeline_build_plan_synthesize_execute_replay(db, owner, tmp_path):
    service = ASGService(artifacts_root=tmp_path / "asg")

    build = service.build_graph(
        db,
        ASGBuildRequest(
            target_url="https://pipeline.example.com",
            flow_steps=FLOW,
            seed_hash="pipeline-e2e",
        ),
        created_by=owner.id,
    )
    assert build.stats.node_count >= 1

    plan = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path", max_paths=1))
    assert plan.paths

    synth = service.synthesize_tests(
        db,
        build.graph_id,
        ASGSynthesizeRequest(
            path_ids=[plan.paths[0].path_id],
            plan_id=plan.plan_id,
            save_test_cases=True,
        ),
        user_id=owner.id,
    )
    assert synth.confidence_gate_passed is True
    assert synth.tests
    test_case = db.query(TestCase).filter(TestCase.id == synth.tests[0].test_case_id).one()
    assert test_case.test_metadata.get("strategy") == "asg"
    assert test_case.test_metadata.get("graph_id") == build.graph_id

    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case.id,
        user_id=owner.id,
        browser="chromium",
        environment="dev",
        base_url="https://pipeline.example.com",
    )

    from app.services.execution_service import ExecutionConfig, ExecutionService

    exec_service = ExecutionService(config=ExecutionConfig(browser="chromium", headless=True))
    page_mock = MagicMock()
    page_mock.goto = AsyncMock()

    with patch.object(exec_service, "initialize", new=AsyncMock()), \
         patch.object(exec_service, "create_context", new=AsyncMock()), \
         patch.object(exec_service, "create_page", new=AsyncMock(return_value=page_mock)), \
         patch.object(exec_service, "cleanup", new=AsyncMock()), \
         patch("app.services.execution_service.auto_dismiss_blocking_modals", new=AsyncMock()), \
         patch.object(exec_service, "_get_user_execution_settings", return_value=MagicMock(timeout_per_tier_seconds=30, fallback_strategy="option_a")), \
         patch("app.services.execution_service.user_settings_service.get_provider_config", return_value={"provider": "openai", "model": "gpt-4"}), \
         patch("app.services.execution_service.ThreeTierExecutionService") as mock_tier_cls, \
         patch("app.services.execution_service.resolve_steps", side_effect=lambda steps, **kwargs: steps), \
         patch.object(exec_service, "_resolve_initial_navigation_url", return_value="https://pipeline.example.com"), \
         patch.object(exec_service, "_resolve_http_credentials_from_steps", return_value=None), \
         patch.object(exec_service, "_capture_screenshot", new=AsyncMock(return_value=None)), \
         patch("app.services.execution_service.crud_execution.create_execution_step"), \
         patch("app.services.execution_service.get_step_session_snapshot", return_value=None), \
         patch.object(exec_service, "_execute_step", new=AsyncMock(return_value={"success": True, "expected": "ok", "actual": "ok"})), \
         patch("app.services.asg_service.ASGService", lambda *a, **kw: service):

        mock_tier_cls.return_value = MagicMock()
        completed = await exec_service.execute_test(
            db=db,
            test_case=test_case,
            user_id=owner.id,
            base_url="https://pipeline.example.com",
            execution_id=execution.id,
        )

    replay_path = tmp_path / "asg" / str(build.graph_id) / "replay" / f"{completed.id}.json"
    assert replay_path.exists()
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    assert replay["graph_id"] == build.graph_id
    assert replay["execution_id"] == completed.id
    assert replay["plan_id"] == plan.plan_id
    assert replay["synthesis_id"] == synth.synthesis_id

    metrics = get_asg_metrics().snapshot
    assert metrics.build_count >= 1
    assert metrics.replay_attempts >= 1


def test_shadow_vs_primary_diff(db, owner, tmp_path):
    service = ASGService(artifacts_root=tmp_path / "asg")
    build = service.build_graph(
        db,
        ASGBuildRequest(target_url="https://pipeline.example.com", flow_steps=FLOW),
        created_by=owner.id,
    )
    diff = service.compare_shadow_vs_primary(db, build.graph_id, FLOW)
    assert "legacy_step_count" in diff
    assert "asg_step_count" in diff
    assert "step_jaccard_similarity" in diff
    assert diff["graph_id"] == build.graph_id


def test_canary_rollback_assertions():
    ok = evaluate_canary_rollback(replay_pass_rate=0.85, fallback_rate=0.10)
    assert ok["rollback_recommended"] is False

    bad_replay = evaluate_canary_rollback(replay_pass_rate=0.75, fallback_rate=0.10)
    assert bad_replay["rollback_recommended"] is True
    assert "replay_pass_below_threshold" in bad_replay["rollback_triggers"]

    bad_fallback = evaluate_canary_rollback(replay_pass_rate=0.90, fallback_rate=0.50)
    assert bad_fallback["rollback_recommended"] is True
    assert "fallback_rate_above_threshold" in bad_fallback["rollback_triggers"]


def test_synthesize_confidence_gate_blocks_low_confidence(db, owner, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
    service = ASGService(artifacts_root=tmp_path / "asg")
    build = service.build_graph(
        db,
        ASGBuildRequest(target_url="https://pipeline.example.com", flow_steps=FLOW),
        created_by=owner.id,
    )
    plan = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path", max_paths=1))
    synth = service.synthesize_tests(
        db,
        build.graph_id,
        ASGSynthesizeRequest(path_ids=[plan.paths[0].path_id]),
    )
    assert synth.confidence_gate_passed is False
    assert synth.fallback_reason_code is not None
    assert synth.tests == []

    metrics = get_asg_metrics().snapshot
    assert metrics.fallback_total >= 1
