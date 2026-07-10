"""
Integration tests: flow_steps -> build -> plan -> synthesize -> save test case.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
        "page_title": "Dashboard",
    },
    {
        "order": 2,
        "action": "input",
        "target": "email address",
        "page_url": "https://app.example.com/login",
        "input_type": "email",
        "element_type": "input",
    },
    {
        "order": 3,
        "action": "click",
        "target": "Sign in",
        "page_url": "https://app.example.com/home",
        "element_type": "button",
        "locator": {"role": "button", "text": "Sign in"},
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
        email="int@example.com",
        username="intuser",
        hashed_password="x",
        role="user",
        is_active=True,
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


def test_end_to_end_pipeline_saves_test_case(db, tmp_path):
    service = ASGService(artifacts_root=tmp_path / "asg")

    build = service.build_graph(
        db,
        ASGBuildRequest(
            target_url="https://app.example.com",
            flow_steps=FLOW,
            seed_hash="e2e-seed",
        ),
        created_by=1,
    )
    plan = service.plan_paths(
        db,
        build.graph_id,
        ASGPlanGoal(mode="shortest_path", max_paths=1),
    )
    assert plan.paths

    synth = service.synthesize_tests(
        db,
        build.graph_id,
        ASGSynthesizeRequest(
            path_ids=[plan.paths[0].path_id],
            save_test_cases=True,
            login_credentials={"email": "u@example.com", "password": "secret"},
        ),
        user_id=1,
    )

    assert synth.tests[0].test_case_id is not None
    tc = db.query(TestCase).filter(TestCase.id == synth.tests[0].test_case_id).one()
    assert isinstance(tc.steps, list)
    assert all(isinstance(s, str) for s in tc.steps)
    assert tc.test_metadata.get("strategy") == "asg"


def test_legacy_path_unchanged_when_asg_disabled(monkeypatch):
    """Regression: should_use_asg_primary is False when ASG_ENABLED=false."""
    monkeypatch.setattr("app.core.config.settings.ASG_ENABLED", False)
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", False)

    from app.services.asg_service import should_use_asg_primary, trigger_shadow_build

    assert should_use_asg_primary() is False

    class _FakeDB:
        pass

    assert trigger_shadow_build(_FakeDB(), target_url="https://x.com", flow_steps=FLOW) is None
