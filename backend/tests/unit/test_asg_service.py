"""
Unit tests for ASGService — fingerprinting, confidence, planner, synthesizer.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.user import User
from app.schemas.asg import ASGBuildRequest, ASGPlanGoal, ASGSynthesizeRequest
from app.services.asg_service import (
    ASGService,
    compute_edge_deterministic_key,
    compute_state_fingerprint,
    compute_transition_confidence,
    normalize_transition,
)


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
        email="asg@example.com",
        username="asguser",
        hashed_password="x",
        role="user",
        is_active=True,
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


SAMPLE_FLOW = [
    {
        "order": 1,
        "action": "navigate",
        "target": "https://shop.example.com",
        "page_url": "https://shop.example.com",
        "page_title": "Shop Home",
        "locator": {"css": "#home"},
    },
    {
        "order": 2,
        "action": "click",
        "target": "Plans",
        "page_url": "https://shop.example.com/plans",
        "page_title": "Plans",
        "element_type": "button",
        "locator": {"role": "button", "text": "Plans"},
        "extracted_content": "Clicked button 'Plans'",
    },
    {
        "order": 3,
        "action": "click",
        "target": "Select",
        "page_url": "https://shop.example.com/checkout",
        "page_title": "Checkout",
        "element_type": "button",
        "locator": {"css": "button.select-plan"},
    },
]


class TestFingerprinting:
    def test_fingerprint_is_stable_for_same_input(self):
        fp1 = compute_state_fingerprint(
            url="https://example.com/plans",
            title="Plans",
            landmarks=["Plans", "button.select-plan"],
            ui_traits={"element_type": "button"},
        )
        fp2 = compute_state_fingerprint(
            url="https://example.com/plans",
            title="Plans",
            landmarks=["button.select-plan", "Plans"],
            ui_traits={"element_type": "button"},
        )
        assert fp1 == fp2
        assert len(fp1) == 64

    def test_fingerprint_differs_for_different_urls(self):
        a = compute_state_fingerprint(url="https://a.com", title="", landmarks=[], ui_traits={})
        b = compute_state_fingerprint(url="https://b.com", title="", landmarks=[], ui_traits={})
        assert a != b


class TestTransitionNormalization:
    def test_normalize_transition_fields(self):
        raw = SAMPLE_FLOW[1]
        norm = normalize_transition(raw)
        assert norm["action_type"] == "click"
        assert norm["target"] == "Plans"
        assert norm["locator"]["role"] == "button"


class TestConfidenceScoring:
    def test_confidence_within_bounds(self):
        transition = normalize_transition(SAMPLE_FLOW[1])
        score = compute_transition_confidence(transition, {"settled": True})
        assert 0.0 <= score <= 1.0

    def test_readiness_improves_score(self):
        transition = normalize_transition(SAMPLE_FLOW[1])
        low = compute_transition_confidence(transition, None)
        high = compute_transition_confidence(transition, {"settled": True})
        assert high >= low


class TestDeterministicKeys:
    def test_edge_key_stable(self):
        t = normalize_transition(SAMPLE_FLOW[1])
        k1 = compute_edge_deterministic_key("fp_a", "fp_b", t, "seed123")
        k2 = compute_edge_deterministic_key("fp_a", "fp_b", t, "seed123")
        assert k1 == k2


class TestASGServiceBuild:
    def test_build_graph_persists_nodes_and_edges(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        req = ASGBuildRequest(
            target_url="https://shop.example.com",
            flow_steps=SAMPLE_FLOW,
            seed_hash="fixed-seed-001",
        )
        resp = service.build_graph(db, req, created_by=1)
        assert resp.graph_id > 0
        assert resp.stats.node_count >= 2
        assert resp.stats.edge_count >= 1
        assert resp.confidence.mean > 0

    def test_build_deterministic_on_fixed_seed(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        req = ASGBuildRequest(
            target_url="https://shop.example.com",
            flow_steps=SAMPLE_FLOW,
            seed_hash="deterministic-seed",
        )
        r1 = service.build_graph(db, req, created_by=1)
        r2 = service.build_graph(db, req, created_by=1)
        assert r1.seed_hash == r2.seed_hash == "deterministic-seed"

        from app.crud import asg as asg_crud

        nodes1 = asg_crud.list_nodes(db, r1.graph_id)
        nodes2 = asg_crud.list_nodes(db, r2.graph_id)
        fps1 = [n.state_fingerprint for n in nodes1]
        fps2 = [n.state_fingerprint for n in nodes2]
        assert fps1 == fps2


class TestPlannerAndSynthesizer:
    def test_plan_and_synthesize_output_string_steps(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://shop.example.com",
                flow_steps=SAMPLE_FLOW,
                seed_hash="plan-seed",
            ),
            created_by=1,
        )
        plan = service.plan_paths(
            db,
            build.graph_id,
            ASGPlanGoal(mode="shortest_path", max_paths=1),
        )
        assert plan.paths
        path_id = plan.paths[0].path_id

        synth = service.synthesize_tests(
            db,
            build.graph_id,
            ASGSynthesizeRequest(path_ids=[path_id]),
            user_id=1,
        )
        assert synth.tests
        steps = synth.tests[0].steps
        assert isinstance(steps, list)
        assert all(isinstance(s, str) for s in steps)
        assert len(steps) >= 1

    def test_planner_deterministic_for_fixture(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://shop.example.com",
                flow_steps=SAMPLE_FLOW,
                seed_hash="planner-seed",
            ),
            created_by=1,
        )
        p1 = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path"))
        p2 = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path"))
        assert p1.paths[0].node_fingerprints == p2.paths[0].node_fingerprints


class TestValidate:
    def test_validate_recommends_fallback_when_low_confidence(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://shop.example.com",
                flow_steps=SAMPLE_FLOW,
                seed_hash="validate-seed",
            ),
            created_by=1,
        )
        result = service.validate_graph(db, build.graph_id)
        assert result.fallback_recommended is True
        assert result.fallback_reason_code is not None
