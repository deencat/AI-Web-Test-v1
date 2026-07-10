"""
Execution contract test: ASG synthesize -> save TestCase -> ExecutionService consumes string[] steps.
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
from app.services.asg_service import ASGService


FLOW = [
    {
        "order": 1,
        "action": "navigate",
        "target": "https://app.example.com",
        "page_url": "https://app.example.com",
        "page_title": "Home",
    },
    {
        "order": 2,
        "action": "click",
        "target": "Submit",
        "page_url": "https://app.example.com/form",
        "element_type": "button",
        "locator": {"role": "button", "text": "Submit"},
        "extracted_content": "Clicked button 'Submit'",
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
        email="exec@example.com",
        username="execuser",
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


@pytest.mark.asyncio
async def test_asg_synthesize_then_execution_service_accepts_string_steps(db, owner, tmp_path):
    service = ASGService(artifacts_root=tmp_path / "asg")

    build = service.build_graph(
        db,
        ASGBuildRequest(target_url="https://app.example.com", flow_steps=FLOW, seed_hash="exec-contract"),
        created_by=owner.id,
    )
    plan = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path", max_paths=1))
    synth = service.synthesize_tests(
        db,
        build.graph_id,
        ASGSynthesizeRequest(path_ids=[plan.paths[0].path_id], save_test_cases=True),
        user_id=owner.id,
    )

    test_case = db.query(TestCase).filter(TestCase.id == synth.tests[0].test_case_id).one()
    assert isinstance(test_case.steps, list)
    assert all(isinstance(step, str) for step in test_case.steps)

    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case.id,
        user_id=owner.id,
        browser="chromium",
        environment="dev",
        base_url="https://app.example.com",
    )

    from app.services.execution_service import ExecutionService, ExecutionConfig

    exec_service = ExecutionService(config=ExecutionConfig(browser="chromium", headless=True))
    captured_steps: list = []

    async def capture_execute_step(page, step_description, *args, **kwargs):
        captured_steps.append(step_description)
        return {"success": True, "expected": "ok", "actual": "ok"}

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
         patch.object(exec_service, "_resolve_initial_navigation_url", return_value="https://app.example.com"), \
         patch.object(exec_service, "_resolve_http_credentials_from_steps", return_value=None), \
         patch.object(exec_service, "_capture_screenshot", new=AsyncMock(return_value=None)), \
         patch("app.services.execution_service.crud_execution.create_execution_step"), \
         patch("app.services.execution_service.get_step_session_snapshot", return_value=None), \
         patch.object(exec_service, "_execute_step", side_effect=capture_execute_step):

        mock_tier_cls.return_value = MagicMock()
        normalized = exec_service._normalize_test_steps(test_case.steps)
        assert all(isinstance(s, str) for s in normalized)

        await exec_service.execute_test(
            db=db,
            test_case=test_case,
            user_id=owner.id,
            base_url="https://app.example.com",
            execution_id=execution.id,
        )

    assert captured_steps
    assert all(isinstance(s, str) for s in captured_steps)

    artifact_path = service.write_replay_artifact(
        graph_id=build.graph_id,
        execution_id=execution.id,
        plan_id=plan.plan_id,
        synthesis_id=synth.synthesis_id,
    )
    replay = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert replay["graph_id"] == build.graph_id
    assert replay["execution_id"] == execution.id
    assert replay["plan_id"] == plan.plan_id
    assert replay["synthesis_id"] == synth.synthesis_id
