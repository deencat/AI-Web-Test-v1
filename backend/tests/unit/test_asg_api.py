"""
Contract tests for /api/v2/asg endpoints.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.api import deps
from app.api.v2.endpoints import asg as asg_module
from app.db.base import Base
from app.models.user import User


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
        email="api@example.com",
        username="apiuser",
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


FLOW = [
    {
        "order": 1,
        "action": "navigate",
        "target": "https://example.com",
        "page_url": "https://example.com",
        "page_title": "Home",
    },
    {
        "order": 2,
        "action": "click",
        "target": "Login",
        "page_url": "https://example.com/login",
        "page_title": "Login",
        "element_type": "button",
        "locator": {"role": "button", "text": "Login"},
    },
]


def test_build_graph_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    resp = client.post(
        "/asg/build",
        json={
            "target_url": "https://example.com",
            "flow_steps": FLOW,
            "seed_hash": "api-test-seed",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "graph_id" in data
    assert data["stats"]["node_count"] >= 1
    assert "confidence" in data


def test_get_graph_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    build = client.post(
        "/asg/build",
        json={"target_url": "https://example.com", "flow_steps": FLOW},
    ).json()
    graph_id = build["graph_id"]

    resp = client.get(f"/asg/{graph_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["graph_id"] == graph_id
    assert detail["node_count"] >= 1


def test_plan_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    graph_id = client.post(
        "/asg/build",
        json={"target_url": "https://example.com", "flow_steps": FLOW},
    ).json()["graph_id"]

    resp = client.post(
        f"/asg/{graph_id}/plan",
        json={"mode": "shortest_path", "max_paths": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["graph_id"] == graph_id
    assert len(data["paths"]) >= 1


def test_synthesize_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    graph_id = client.post(
        "/asg/build",
        json={"target_url": "https://example.com", "flow_steps": FLOW},
    ).json()["graph_id"]
    path_id = client.post(
        f"/asg/{graph_id}/plan",
        json={"mode": "shortest_path", "max_paths": 1},
    ).json()["paths"][0]["path_id"]

    resp = client.post(
        f"/asg/{graph_id}/synthesize",
        json={"path_ids": [path_id]},
    )
    assert resp.status_code == 200
    tests = resp.json()["tests"]
    assert tests
    assert all(isinstance(s, str) for s in tests[0]["steps"])


def test_validate_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    graph_id = client.post(
        "/asg/build",
        json={"target_url": "https://example.com", "flow_steps": FLOW},
    ).json()["graph_id"]

    resp = client.post(f"/asg/{graph_id}/validate")
    assert resp.status_code == 200
    data = resp.json()
    assert "replay_confidence" in data
    assert "fallback_recommended" in data


def test_get_graph_404(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ASG_SHADOW_MODE", True)
    resp = client.get("/asg/99999")
    assert resp.status_code == 404
