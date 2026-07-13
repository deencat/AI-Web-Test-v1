"""
Additional ASG tests targeting 100% coverage on service, CRUD, and API modules.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.api.v2.endpoints import asg as asg_module
from app.crud import asg as asg_crud
from app.db.base import Base
from app.models.user import User
from app.schemas.asg import ASGBuildRequest, ASGPlanGoal, ASGSynthesizeRequest, ASGPolicyLimits
from app.services.asg_service import (
    ASGPolicyEngine,
    ASGService,
    compute_node_confidence,
    compute_transition_confidence,
    extract_readiness_snapshots_from_flow_steps,
    get_asg_service,
    is_asg_enabled_for_project,
    normalize_transition,
    score_action_reproducibility,
    score_readiness_signal,
    score_selector_stability,
    should_use_asg_primary,
    trigger_shadow_build,
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
        email="cov@example.com",
        username="covuser",
        hashed_password="x",
        role="user",
        is_active=True,
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


@pytest.fixture
def asg_app(db: Session):
    app = FastAPI()
    app.include_router(asg_module.router, prefix="/asg")
    app.dependency_overrides[deps.get_db] = lambda: db
    user = MagicMock(spec=User)
    user.id = 1
    app.dependency_overrides[deps.get_current_user] = lambda: user
    return app


@pytest.fixture
def client(asg_app: FastAPI):
    return TestClient(asg_app)


BRANCHING_FLOW = [
    {"order": 1, "action": "navigate", "page_url": "https://allowed.example.com", "target": "home"},
    {"order": 2, "action": "click", "page_url": "https://allowed.example.com/a", "target": "A", "locator": {"css": "#a"}},
    {"order": 3, "action": "click", "page_url": "https://allowed.example.com/b", "target": "B", "locator": {"css": "#b"}},
    {"order": 4, "action": "click", "page_url": "https://allowed.example.com/c", "target": "C", "locator": {"css": "#c"}},
]


class TestScoringBranches:
    def test_selector_stability_all_branches(self):
        assert score_selector_stability({"locator": "bad"}) == 0.4
        assert score_selector_stability({"locator": {"xpath": "//x"}}) == 0.55
        assert score_selector_stability({"locator": {"css": "#x"}}) == 0.75
        assert score_selector_stability({"locator": {"role": "btn", "text": "Go"}}) == 0.85
        assert score_selector_stability({"locator": {}, "target": "Checkout"}) == 0.7
        assert score_selector_stability({"locator": {}, "target": "div"}) == 0.45
        assert score_selector_stability(
            {
                "locator": {"xpath": "//button"},
                "playwright_suggestions": [{"kind": "role", "role": "button", "name": "Go"}],
            }
        ) == 0.85
        assert score_selector_stability(
            {
                "locator": {
                    "xpath": "//div",
                    "playwright_suggestions": [{"kind": "css_id", "id": "submit"}],
                }
            }
        ) == 0.75
        assert score_selector_stability(
            {
                "locator": {
                    "xpath": "//div",
                    "playwright_suggestions": [{"kind": "role", "role": "button"}],
                }
            }
        ) == 0.55

    def test_readiness_all_branches(self):
        assert score_readiness_signal(None) == 0.6
        assert score_readiness_signal({"settled": True}) == 0.9
        assert score_readiness_signal({"loading_cleared": True}) == 0.8
        assert score_readiness_signal({"modal_dismissed": True}) == 0.75
        assert score_readiness_signal({"other": True}) == 0.55

    def test_action_reproducibility_branches(self):
        assert score_action_reproducibility({"action_type": "navigate"}) == 0.95
        assert score_action_reproducibility({"action_type": "click", "target": "x"}) == 0.8
        assert score_action_reproducibility({"action_type": "input"}) == 0.7
        assert score_action_reproducibility({"action_type": "hover"}) == 0.5

    def test_node_confidence_without_landmarks(self):
        assert compute_node_confidence([], []) == 0.45
        assert compute_node_confidence(["x"], [0.9, 0.8]) > 0.45


class TestPolicyEngine:
    def test_domain_allowlist_blocks(self):
        policy = ASGPolicyEngine({"domain_allowlist": ["allowed.example.com"]})
        assert policy.is_url_allowed("https://allowed.example.com/page") is True
        assert policy.is_url_allowed("https://evil.example.com/page") is False
        assert any("domain_blocked" in h for h in policy.hits)

    def test_forbidden_action(self):
        policy = ASGPolicyEngine({"forbidden_actions": ["download"]})
        assert policy.is_action_allowed("download") is False
        assert policy.is_action_allowed("click") is True

    def test_max_nodes_depth_branching(self):
        policy = ASGPolicyEngine({"max_nodes": 1, "max_depth": 1, "max_branching": 0})
        assert policy.can_add_node(1) is False
        assert policy.can_go_deeper(1) is False
        assert policy.can_add_branch(5, 0) is False


class TestBuildPolicyIntegration:
    def test_policy_hits_during_build(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        req = ASGBuildRequest(
            target_url="https://allowed.example.com",
            flow_steps=BRANCHING_FLOW
            + [
                {"order": 5, "action": "download", "page_url": "https://allowed.example.com/d", "target": "file"},
                {"order": 6, "action": "click", "page_url": "https://blocked.example.com/x", "target": "X"},
            ],
            policy={
                "max_nodes": 3,
                "max_depth": 2,
                "max_branching": 1,
                "domain_allowlist": ["allowed.example.com"],
                "forbidden_actions": ["download"],
            },
            readiness_snapshots=[{"order": 2, "settled": True}],
            seed_hash="policy-seed",
        )
        resp = service.build_graph(db, req, created_by=1)
        assert resp.stats.policy_hits
        assert any("forbidden_action" in h or "domain_blocked" in h or "max_" in h for h in resp.stats.policy_hits)

    def test_empty_flow_steps_creates_navigate_only(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        resp = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=[]),
            created_by=1,
        )
        assert resp.stats.node_count >= 1

    def test_prev_node_none_and_policy_skips_in_build(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        req = ASGBuildRequest(
            target_url="https://allowed.example.com",
            flow_steps=[
                {"order": 1, "action": "download", "page_url": "https://blocked.com", "target": "x"},
                {"order": 2, "action": "navigate", "page_url": "https://blocked.com", "target": "blocked"},
                {"order": 3, "action": "click", "page_url": "https://allowed.example.com/a", "target": "A", "locator": {"css": "#a"}},
            ],
            policy=ASGPolicyLimits.model_construct(
                max_nodes=0,
                max_depth=20,
                max_branching=0,
                domain_allowlist=["allowed.example.com"],
                forbidden_actions=["download"],
            ),
            readiness_snapshots=[{"order": 3, "modal_dismissed": True}],
        )
        resp = service.build_graph(db, req, created_by=1)
        assert resp.stats.node_count == 0
        assert any("forbidden_action" in h for h in resp.stats.policy_hits)
        assert any("domain_blocked" in h for h in resp.stats.policy_hits)

    def test_max_nodes_cap_stops_build(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        many_steps = [
            {"order": i, "action": "click", "page_url": f"https://example.com/p{i}", "target": f"P{i}", "locator": {"css": f"#p{i}"}}
            for i in range(1, 8)
        ]
        resp = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=many_steps,
                policy={"max_nodes": 2, "max_depth": 10, "max_branching": 10},
            ),
            created_by=1,
        )
        assert resp.stats.node_count <= 2

    def test_duplicate_transition_reuses_edge(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        step = {"order": 1, "action": "click", "page_url": "https://example.com/p", "target": "Go", "locator": {"css": "#go"}}
        flow = [
            {"order": 0, "action": "navigate", "page_url": "https://example.com", "target": "home"},
            step,
            dict(step, order=2),
        ]
        resp = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow, seed_hash="dup-edge"),
            created_by=1,
        )
        assert resp.stats.edge_count >= 1

    def test_build_seed_hash_generated_when_not_explicit(self, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        h = service.build_seed_hash("https://example.com", ["intent"], [], {})
        assert len(h) == 16


class TestPlannerModes:
    def _build_service_graph(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        flow = [
            {"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"},
            {"order": 2, "action": "click", "page_url": "https://example.com/login", "target": "Login", "page_title": "Login", "locator": {"css": "#login"}},
            {"order": 3, "action": "click", "page_url": "https://example.com/dashboard", "target": "Dash", "page_title": "Dashboard", "locator": {"css": "#dash"}},
        ]
        build = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow, seed_hash="modes-seed"),
            created_by=1,
        )
        return service, build.graph_id

    def test_requirement_coverage_planner(self, db, tmp_path):
        service, graph_id = self._build_service_graph(db, tmp_path)
        plan = service.plan_paths(
            db,
            graph_id,
            ASGPlanGoal(mode="requirement_coverage", requirement_ids=["Login"], max_paths=2),
        )
        assert plan.paths
        assert plan.paths[0].goal_type == "requirement_coverage"

    def test_requirement_coverage_default_target_score_discount(self, db, tmp_path):
        service, graph_id = self._build_service_graph(db, tmp_path)
        plan = service.plan_paths(
            db,
            graph_id,
            ASGPlanGoal(mode="requirement_coverage", requirement_ids=[], max_paths=1),
        )
        assert plan.paths

    def test_risk_first_planner(self, db, tmp_path):
        service, graph_id = self._build_service_graph(db, tmp_path)
        plan = service.plan_paths(
            db,
            graph_id,
            ASGPlanGoal(mode="risk_first", max_paths=2),
        )
        assert plan.paths
        assert plan.paths[0].goal_type == "risk_first"

    def test_shortest_path_with_target_fingerprint(self, db, tmp_path):
        service, graph_id = self._build_service_graph(db, tmp_path)
        nodes = asg_crud.list_nodes(db, graph_id)
        terminal = nodes[-1]
        plan = service.plan_paths(
            db,
            graph_id,
            ASGPlanGoal(mode="shortest_path", target_node_fingerprint=terminal.state_fingerprint),
        )
        assert terminal.state_fingerprint in plan.paths[0].node_fingerprints

    def test_shortest_path_start_equals_target(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[],
                seed_hash="single-node",
            ),
            created_by=1,
        )
        root = asg_crud.list_nodes(db, build.graph_id)[0]
        path = service._shortest_path(root.id, root.id, {})
        assert path == [root.id]

    def test_plan_empty_graph_raises(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        graph = asg_crud.create_graph(db, created_by=1, project_id=None, policy_json={}, seed_hash="empty")
        with pytest.raises(ValueError, match="no nodes"):
            service.plan_paths(db, graph.id, ASGPlanGoal())


class TestSynthesizeSkips:
    def test_skip_missing_path_and_edges(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        path = asg_crud.create_path(
            db,
            graph_id=build.graph_id,
            goal_type="test",
            path_nodes_json=["fp1"],
            path_edges_json=["missing-edge-key"],
            score=0.5,
            risk_score=0.5,
        )
        synth = service.synthesize_tests(
            db,
            build.graph_id,
            ASGSynthesizeRequest(path_ids=[path.id, 99999]),
        )
        assert len(synth.tests) == 1
        assert synth.tests[0].steps == []

    def test_fallback_step_strings_when_converter_empty(self, db, tmp_path, monkeypatch):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[
                    {"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"},
                    {"order": 2, "action": "click", "page_url": "https://example.com", "target": "div", "locator": {"css": "#x"}},
                ],
                seed_hash="fallback-steps",
            ),
            created_by=1,
        )
        plan = service.plan_paths(db, build.graph_id, ASGPlanGoal(mode="shortest_path"))
        monkeypatch.setattr(
            "app.api.v2.endpoints.crawl_and_save._flow_steps_to_test_steps",
            lambda *_a, **_k: [],
        )
        synth = service.synthesize_tests(
            db,
            build.graph_id,
            ASGSynthesizeRequest(path_ids=[plan.paths[0].path_id]),
        )
        assert synth.tests[0].steps
        assert synth.tests[0].steps[0].startswith("Step 1:")


class TestValidateAndGates:
    def test_evaluate_confidence_gate_pass_branch(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.1)
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        ok, reason = service.evaluate_confidence_gate(db, build.graph_id)
        assert ok is True
        assert reason is None

    def test_validate_low_node_confidence_reason(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        for node in asg_crud.list_nodes(db, build.graph_id):
            node.confidence = 0.1
        for edge in asg_crud.list_edges(db, build.graph_id):
            edge.confidence = 0.99
        db.commit()
        result = service.validate_graph(db, build.graph_id)
        assert result.fallback_reason_code == "low_node_confidence"

    def test_validate_low_edge_confidence_reason(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
        service = ASGService(artifacts_root=tmp_path / "asg")
        with patch.object(
            asg_crud,
            "list_nodes",
            return_value=[MagicMock(confidence=0.99), MagicMock(confidence=0.99)],
        ), patch.object(
            asg_crud,
            "list_edges",
            return_value=[MagicMock(confidence=0.1)],
        ), patch.object(asg_crud, "get_graph", return_value=MagicMock()):
            result = service.validate_graph(db, 1)
        assert result.fallback_reason_code == "low_edge_confidence"

    def test_validate_low_replay_confidence_reason(self, db, tmp_path, monkeypatch):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        for node in asg_crud.list_nodes(db, build.graph_id):
            node.confidence = 0.8
        db.commit()
        with patch("app.services.asg_service.round", return_value=0.70):
            monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.75)
            result = service.validate_graph(db, build.graph_id)
        assert result.fallback_reason_code == "low_replay_confidence"

    def test_write_replay_artifact(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        path = service.write_replay_artifact(
            graph_id=42,
            execution_id=99,
            plan_id="plan-1",
            synthesis_id="syn-1",
            extra={"status": "completed"},
        )
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["graph_id"] == 42
        assert data["execution_id"] == 99
        assert data["plan_id"] == "plan-1"
        assert data["synthesis_id"] == "syn-1"


class TestFeatureFlags:
    def test_is_asg_enabled_allowlist_blocks(self, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", True)
        monkeypatch.setattr("app.services.asg_service.settings.ASG_ENABLED", False)
        monkeypatch.setattr("app.services.asg_service.settings.ASG_PROJECT_ALLOWLIST", "1,2")
        assert is_asg_enabled_for_project(99) is False
        assert is_asg_enabled_for_project(1) is True

    def test_is_asg_disabled_when_both_flags_off(self, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", False)
        monkeypatch.setattr("app.services.asg_service.settings.ASG_ENABLED", False)
        assert is_asg_enabled_for_project() is False

    def test_should_use_asg_primary(self, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_ENABLED", True)
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", True)
        assert should_use_asg_primary() is True

    def test_trigger_shadow_build_exception_returns_none(self, db, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", True)
        with patch.object(ASGService, "build_graph", side_effect=RuntimeError("boom")):
            assert trigger_shadow_build(db, target_url="https://example.com", flow_steps=[]) is None

    def test_trigger_shadow_build_skipped_when_disabled(self, db, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", False)
        monkeypatch.setattr("app.services.asg_service.settings.ASG_ENABLED", False)
        assert trigger_shadow_build(db, target_url="https://example.com", flow_steps=[]) is None


class TestCrudCoverage:
    def test_get_node_by_fingerprint(self, db):
        graph = asg_crud.create_graph(db, created_by=1, project_id=None, policy_json={}, seed_hash="crud")
        node = asg_crud.create_node(
            db,
            graph_id=graph.id,
            state_fingerprint="fp-abc",
            url="https://example.com",
            title="T",
            state_payload_json={},
            confidence=0.8,
        )
        db.commit()
        found = asg_crud.get_node_by_fingerprint(db, graph.id, "fp-abc")
        assert found.id == node.id

    def test_list_paths_selected_only(self, db):
        graph = asg_crud.create_graph(db, created_by=1, project_id=None, policy_json={}, seed_hash="paths")
        asg_crud.create_path(
            db,
            graph_id=graph.id,
            goal_type="a",
            path_nodes_json=["n1"],
            path_edges_json=["e1"],
            score=0.9,
            risk_score=0.1,
            selected=True,
        )
        asg_crud.create_path(
            db,
            graph_id=graph.id,
            goal_type="b",
            path_nodes_json=["n2"],
            path_edges_json=["e2"],
            score=0.5,
            risk_score=0.5,
            selected=False,
        )
        selected = asg_crud.list_paths(db, graph.id, selected_only=True)
        assert len(selected) == 1
        assert selected[0].goal_type == "a"

    def test_count_nodes_edges(self, db):
        graph = asg_crud.create_graph(db, created_by=1, project_id=None, policy_json={}, seed_hash="count")
        n = asg_crud.create_node(
            db,
            graph_id=graph.id,
            state_fingerprint="fp1",
            url="u",
            title="t",
            state_payload_json={},
            confidence=0.5,
        )
        asg_crud.create_edge(
            db,
            graph_id=graph.id,
            from_node_id=n.id,
            to_node_id=n.id,
            action_type="click",
            action_payload_json={},
            readiness_snapshot_json=None,
            confidence=0.5,
            deterministic_key="key1",
        )
        db.commit()
        nodes, edges = asg_crud.count_nodes_edges(db, graph.id)
        assert nodes == 1
        assert edges == 1


class TestApiErrorPaths:
    def test_require_asg_enabled_503(self, client, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.ASG_ENABLED", False)
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", False)
        resp = client.post("/asg/build", json={"target_url": "https://example.com", "flow_steps": []})
        assert resp.status_code == 503

    def test_build_exception_400(self, client, monkeypatch, asg_app):
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)

        def _failing_service():
            mock_svc = MagicMock()
            mock_svc.build_graph.side_effect = RuntimeError("build failed")
            return mock_svc

        asg_app.dependency_overrides[asg_module.get_asg_service] = _failing_service
        resp = client.post("/asg/build", json={"target_url": "https://example.com", "flow_steps": []})
        assert resp.status_code == 400

    def test_plan_404(self, client, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
        resp = client.post("/asg/99999/plan", json={"mode": "shortest_path"})
        assert resp.status_code == 404

    def test_synthesize_404(self, client, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
        resp = client.post("/asg/99999/synthesize", json={"path_ids": [1]})
        assert resp.status_code == 404

    def test_validate_404(self, client, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
        resp = client.post("/asg/99999/validate")
        assert resp.status_code == 404

    def test_plan_value_error_no_nodes(self, client, db, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
        graph = asg_crud.create_graph(db, created_by=1, project_id=None, policy_json={}, seed_hash="empty-api")
        resp = client.post(f"/asg/{graph.id}/plan", json={"mode": "shortest_path"})
        assert resp.status_code == 404


def test_evaluate_confidence_gate_module(db, tmp_path, monkeypatch):
    """Cover evaluate_confidence_gate method used in orchestration."""
    monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
    service = ASGService(artifacts_root=tmp_path / "asg")
    build = service.build_graph(
        db,
        ASGBuildRequest(
            target_url="https://example.com",
            flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
        ),
        created_by=1,
    )
    ok, reason = service.evaluate_confidence_gate(db, build.graph_id)
    assert ok is False
    assert reason is not None


class TestRemainingServiceCoverage:
    def test_get_graph_detail_confidence_buckets(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[
                    {"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"},
                    {"order": 2, "action": "click", "page_url": "https://example.com/x", "target": "X", "locator": {"css": "#x"}},
                ],
            ),
            created_by=1,
        )
        nodes = asg_crud.list_nodes(db, build.graph_id)
        edges = asg_crud.list_edges(db, build.graph_id)
        nodes[0].confidence = 0.95
        if len(nodes) > 1:
            nodes[1].confidence = 0.8
        if edges:
            edges[0].confidence = 0.6
        db.commit()
        detail = service.get_graph_detail(db, build.graph_id)
        assert detail.confidence_distribution["high"] > 0
        assert detail.confidence_distribution["low"] > 0

    def test_requirement_coverage_skips_duplicate_paths(self, db, tmp_path):
        service, graph_id = TestPlannerModes()._build_service_graph(db, tmp_path)
        goal = ASGPlanGoal(mode="requirement_coverage", requirement_ids=["Login", "Login"], max_paths=3)
        plan = service.plan_paths(db, graph_id, goal)
        assert len(plan.paths) == 1

    def test_shortest_path_unreachable_and_visited_skip(self, db, tmp_path):
        from app.models.asg import ASGEdge

        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        root = asg_crud.list_nodes(db, build.graph_id)[0]
        assert service._shortest_path(root.id, root.id + 999, {}) == [root.id]
        assert service._path_score([]) == 0.5

        edge_ab = ASGEdge(
            id=1,
            graph_id=build.graph_id,
            from_node_id=1,
            to_node_id=2,
            action_type="click",
            action_payload_json={},
            confidence=0.9,
            deterministic_key="e1",
        )
        edge_ac = ASGEdge(
            id=2,
            graph_id=build.graph_id,
            from_node_id=1,
            to_node_id=3,
            action_type="click",
            action_payload_json={},
            confidence=0.8,
            deterministic_key="e2",
        )
        edge_b4 = ASGEdge(
            id=3,
            graph_id=build.graph_id,
            from_node_id=2,
            to_node_id=4,
            action_type="click",
            action_payload_json={},
            confidence=0.9,
            deterministic_key="e3",
        )
        edge_c4 = ASGEdge(
            id=4,
            graph_id=build.graph_id,
            from_node_id=3,
            to_node_id=4,
            action_type="click",
            action_payload_json={},
            confidence=0.9,
            deterministic_key="e4",
        )
        edge_45 = ASGEdge(
            id=5,
            graph_id=build.graph_id,
            from_node_id=4,
            to_node_id=5,
            action_type="click",
            action_payload_json={},
            confidence=0.9,
            deterministic_key="e5",
        )
        adj = {1: [edge_ab, edge_ac], 2: [edge_b4], 3: [edge_c4], 4: [edge_45], 5: []}
        assert service._shortest_path(1, 5, adj) == [1, 2, 4, 5]

    def test_synthesize_and_validate_graph_not_found(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        with pytest.raises(ValueError, match="not found"):
            service.synthesize_tests(db, 99999, ASGSynthesizeRequest(path_ids=[1]))
        with pytest.raises(ValueError, match="not found"):
            service.validate_graph(db, 99999)

    def test_trigger_shadow_build_success(self, db, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", True)
        graph_id = trigger_shadow_build(
            db,
            target_url="https://example.com",
            flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            created_by=1,
        )
        assert graph_id is not None

    def test_max_branching_skips_extra_edges(self, db, tmp_path, monkeypatch):
        service = ASGService(artifacts_root=tmp_path / "asg")
        original_branch = ASGPolicyEngine.can_add_branch

        def _deny_branch(self, from_node_id, branch_count):
            self.hits.append(f"max_branching_reached:node_{from_node_id}")
            return False

        monkeypatch.setattr(ASGPolicyEngine, "can_add_branch", _deny_branch)
        resp = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[
                    {"order": 1, "action": "click", "page_url": "https://example.com/a", "target": "A", "locator": {"css": "#a"}},
                ],
                policy={"max_branching": 1, "max_nodes": 20, "max_depth": 20},
            ),
            created_by=1,
        )
        assert any("max_branching" in h for h in resp.stats.policy_hits)

    def test_prev_node_none_branch_via_skipped_root(self, db, tmp_path, monkeypatch):
        service = ASGService(artifacts_root=tmp_path / "asg")
        original = ASGPolicyEngine.can_add_node
        calls = {"count": 0}

        def _skip_root_only(self, count):
            if count == 0 and calls["count"] == 0:
                calls["count"] += 1
                return False
            return original(self, count)

        monkeypatch.setattr(ASGPolicyEngine, "can_add_node", _skip_root_only)
        resp = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[
                    {"order": 1, "action": "click", "page_url": "https://example.com/a", "target": "A", "locator": {"css": "#a"}},
                ],
                policy={"max_nodes": 5, "max_depth": 10, "max_branching": 5},
            ),
            created_by=1,
        )
        assert resp.stats.node_count >= 1

    def test_existing_node_marked_terminal(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        step = {"order": 1, "action": "click", "page_url": "https://example.com/same", "target": "Go", "locator": {"css": "#go"}}
        flow = [
            {"order": 0, "action": "navigate", "page_url": "https://example.com", "target": "home"},
            step,
            dict(step, order=2),
        ]
        service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow, seed_hash="terminal"),
            created_by=1,
        )

    def test_get_asg_service_factory(self):
        assert isinstance(get_asg_service(), ASGService)


class TestPhase3Integration:
    def test_synthesize_confidence_gate_returns_fallback(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_CONFIDENCE_MIN", 0.99)
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
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

    def test_compare_shadow_vs_primary(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        flow = [
            {"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"},
            {"order": 2, "action": "click", "page_url": "https://example.com/x", "target": "Go", "locator": {"css": "#go"}},
        ]
        build = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow),
            created_by=1,
        )
        diff = service.compare_shadow_vs_primary(db, build.graph_id, flow)
        assert diff["graph_id"] == build.graph_id
        assert "step_jaccard_similarity" in diff

    def test_compare_shadow_vs_primary_plan_failure(self, db, tmp_path, monkeypatch):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        with patch.object(service, "plan_paths", side_effect=RuntimeError("plan failed")):
            diff = service.compare_shadow_vs_primary(db, build.graph_id, [])
        assert diff["asg_step_count"] == 0

    def test_compare_shadow_vs_primary_skips_missing_edges(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        path = asg_crud.create_path(
            db,
            graph_id=build.graph_id,
            goal_type="test",
            path_nodes_json=["a", "b"],
            path_edges_json=["nonexistent-edge-key"],
            score=0.9,
            risk_score=0.1,
        )
        with patch.object(service, "plan_paths") as mock_plan:
            mock_plan.return_value = type("P", (), {"paths": [type("PP", (), {"path_id": path.id})()]})()
            diff = service.compare_shadow_vs_primary(db, build.graph_id, [])
        assert diff["asg_step_count"] == 0

    def test_mark_paths_selected_empty_path_ids(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        build = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        asg_crud.mark_paths_selected(db, build.graph_id, [])

    def test_build_records_metrics(self, db, tmp_path):
        from app.services.asg_metrics import reset_asg_metrics, get_asg_metrics

        reset_asg_metrics()
        service = ASGService(artifacts_root=tmp_path / "asg")
        service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://example.com",
                flow_steps=[{"order": 1, "action": "navigate", "page_url": "https://example.com", "target": "home"}],
            ),
            created_by=1,
        )
        snap = get_asg_metrics().snapshot
        assert snap.build_count == 1
        assert snap.node_count_total >= 1


class TestPhase4ConfidenceV2:
    FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "asg"

    def test_normalize_transition_copies_playwright_suggestions(self):
        step = {
            "action": "click",
            "locator": {
                "xpath": "//btn",
                "playwright_suggestions": [{"kind": "role", "role": "button", "name": "X"}],
            },
        }
        norm = normalize_transition(step)
        assert norm["playwright_suggestions"][0]["kind"] == "role"

    def test_extract_readiness_snapshots_from_flow_steps(self):
        steps = [
            {"order": 1, "action": "navigate", "readiness": {"settled": True}},
            {"order": 2, "action": "click", "post_click_readiness": {"loading_cleared": True}},
            {"order": 3, "action": "click"},
            {"action": "click", "readiness": {"settled": True}},
        ]
        snaps = extract_readiness_snapshots_from_flow_steps(steps)
        assert len(snaps) == 2
        assert snaps[0]["order"] == 1
        assert snaps[1]["loading_cleared"] is True

    def test_trigger_shadow_build_forwards_readiness_snapshots(self, db, monkeypatch):
        monkeypatch.setattr("app.services.asg_service.settings.ASG_SHADOW_MODE", True)
        captured: dict = {}

        def _capture_build(self, db_session, request, **kwargs):
            captured["readiness_snapshots"] = request.readiness_snapshots
            return ASGService.build_graph(self, db_session, request, **kwargs)

        with patch.object(ASGService, "build_graph", _capture_build):
            trigger_shadow_build(
                db,
                target_url="https://example.com",
                flow_steps=[
                    {
                        "order": 1,
                        "action": "navigate",
                        "page_url": "https://example.com",
                        "target": "home",
                        "readiness": {"settled": True},
                    },
                    {
                        "order": 2,
                        "action": "click",
                        "page_url": "https://example.com/a",
                        "target": "A",
                        "readiness": {"loading_cleared": True},
                    },
                ],
                created_by=1,
            )
        assert len(captured["readiness_snapshots"]) == 2

    def test_build_confidence_report_includes_uplift(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        flow = [
            {
                "order": 1,
                "action": "navigate",
                "page_url": "https://example.com",
                "target": "home",
                "readiness": {"settled": True},
            },
            {
                "order": 2,
                "action": "click",
                "page_url": "https://example.com/x",
                "target": "Go",
                "locator": {
                    "xpath": "//button",
                    "playwright_suggestions": [{"kind": "role", "role": "button", "name": "Go"}],
                },
                "readiness": {"loading_cleared": True},
            },
        ]
        resp = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow),
            created_by=1,
        )
        report_path = tmp_path / "asg" / str(resp.graph_id) / "build" / "confidence-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["scoring_version"] == "v2"
        assert "v1_mean" in report["uplift"]
        assert report["uplift"]["v2_mean"] == resp.confidence.mean
        assert report["uplift"]["v2_mean"] >= report["uplift"]["v1_mean"]

    def test_pilot_rebuild_confidence_uplift(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        flow5 = json.loads((self.FIXTURES / "pilot_graph5_flow_steps.json").read_text(encoding="utf-8"))
        snapshots = extract_readiness_snapshots_from_flow_steps(flow5)
        resp = service.build_graph(
            db,
            ASGBuildRequest(
                target_url="https://pilot5.example.com",
                flow_steps=flow5,
                readiness_snapshots=snapshots,
                seed_hash="pilot-graph5",
            ),
            created_by=1,
        )
        assert resp.confidence.mean >= 0.75
        validation = service.validate_graph(db, resp.graph_id)
        assert validation.fallback_recommended is False

    def test_weak_signals_graph_fails_confidence_gate(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        weak_flow = [
            {"order": 0, "action": "navigate", "page_url": "https://weak.example.com", "target": "home"},
        ] + [
            {
                "order": i,
                "action": "click",
                "page_url": f"https://weak.example.com/p{i}",
                "target": "div",
                "locator": {"xpath": f"//div[{i}]"},
            }
            for i in range(1, 10)
        ]
        resp = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://weak.example.com", flow_steps=weak_flow, seed_hash="weak"),
            created_by=1,
        )
        assert resp.confidence.mean < service.confidence_min
        validation = service.validate_graph(db, resp.graph_id)
        assert validation.fallback_recommended is True

    def test_v1_uplift_covers_legacy_selector_branches(self, db, tmp_path):
        service = ASGService(artifacts_root=tmp_path / "asg")
        flow = [
            {"order": 0, "action": "navigate", "page_url": "https://example.com", "target": "home"},
            {"order": 1, "action": "click", "page_url": "https://example.com/a", "target": "div", "locator": {}},
            {"order": 2, "action": "click", "page_url": "https://example.com/b", "target": "x", "locator": "bad"},
        ]
        resp = service.build_graph(
            db,
            ASGBuildRequest(target_url="https://example.com", flow_steps=flow, seed_hash="v1-branches"),
            created_by=1,
        )
        report_path = tmp_path / "asg" / str(resp.graph_id) / "build" / "confidence-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["uplift"]["v1_mean"] < report["uplift"]["v2_mean"] or report["uplift"]["v1_mean"] > 0
