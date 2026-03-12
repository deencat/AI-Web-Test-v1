"""
Unit tests for DELETE /api/v1/tests/batch — Sprint 10.5 Feature 2: Batch Delete Tests.

TDD RED phase: written before implementation.
All tests mock CRUD and auth to focus solely on endpoint logic.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.api.v1.endpoints import tests as tests_module
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(tests_module.router, prefix="/tests")
    return app


def _mock_user(user_id: int = 1, role: str = "user") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    return user


def _mock_test_case(test_id: int, owner_id: int = 1):
    tc = MagicMock()
    tc.id = test_id
    tc.user_id = owner_id
    return tc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    return _make_app()


@pytest.fixture
def client(app: FastAPI):
    return TestClient(app)


@pytest.fixture
def auth_override(app: FastAPI):
    """Override get_current_user to return a standard user."""
    from app.api import deps
    user = _mock_user(user_id=1, role="user")
    app.dependency_overrides[deps.get_current_user] = lambda: user
    yield user
    app.dependency_overrides.clear()


@pytest.fixture
def admin_override(app: FastAPI):
    """Override get_current_user to return an admin user."""
    from app.api import deps
    user = _mock_user(user_id=99, role="admin")
    app.dependency_overrides[deps.get_current_user] = lambda: user
    yield user
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestBatchDeleteHappyPath:
    def test_deletes_multiple_ids_returns_deleted_count(self, client, auth_override):
        """Deleting 3 owned tests returns { deleted: 3, failed: [] }."""
        tc1 = _mock_test_case(1, owner_id=1)
        tc2 = _mock_test_case(2, owner_id=1)
        tc3 = _mock_test_case(3, owner_id=1)

        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", side_effect=[tc1, tc2, tc3]),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=True),
        ):
            resp = client.request(
                "DELETE",
                "/tests/batch",
                json={"ids": [1, 2, 3]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 3
        assert data["failed"] == []

    def test_deletes_single_id(self, client, auth_override):
        tc = _mock_test_case(10, owner_id=1)
        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", return_value=tc),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=True),
        ):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [10]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1

    def test_admin_can_delete_other_users_tests(self, client, admin_override):
        tc = _mock_test_case(5, owner_id=42)  # owned by user 42, not admin 99
        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", return_value=tc),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=True),
        ):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [5]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1


# ---------------------------------------------------------------------------
# Validation / guard tests
# ---------------------------------------------------------------------------

class TestBatchDeleteValidation:
    def test_empty_ids_returns_400(self, client, auth_override):
        resp = client.request("DELETE", "/tests/batch", json={"ids": []})
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_more_than_100_ids_returns_400(self, client, auth_override):
        ids = list(range(1, 102))  # 101 ids
        resp = client.request("DELETE", "/tests/batch", json={"ids": ids})
        assert resp.status_code == 400
        assert "100" in resp.json()["detail"]

    def test_unauthenticated_returns_401(self, client):
        """Without auth override no user is injected → should 401 or 422 (dependency error)."""
        resp = client.request("DELETE", "/tests/batch", json={"ids": [1]})
        assert resp.status_code in (401, 422)

    def test_missing_ids_field_returns_422(self, client, auth_override):
        resp = client.request("DELETE", "/tests/batch", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Ownership guard tests
# ---------------------------------------------------------------------------

class TestBatchDeleteOwnership:
    def test_non_owner_test_is_not_deleted(self, client, auth_override):
        """User 1 cannot delete a test owned by user 2."""
        tc = _mock_test_case(7, owner_id=2)  # owned by user 2
        with patch("app.api.v1.endpoints.tests.crud.get_test_case", return_value=tc):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [7]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert 7 in data["failed"]

    def test_mixed_ownership_deletes_only_owned(self, client, auth_override):
        """User 1 owns tc1 (id=1) but not tc2 (id=2). Only id=1 is deleted."""
        tc1 = _mock_test_case(1, owner_id=1)
        tc2 = _mock_test_case(2, owner_id=2)
        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", side_effect=[tc1, tc2]),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=True),
        ):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [1, 2]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 1
        assert data["failed"] == [2]

    def test_not_found_test_goes_to_failed(self, client, auth_override):
        with patch("app.api.v1.endpoints.tests.crud.get_test_case", return_value=None):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [999]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert 999 in data["failed"]


# ---------------------------------------------------------------------------
# Partial-failure / edge-case tests
# ---------------------------------------------------------------------------

class TestBatchDeletePartialFailure:
    def test_crud_delete_failure_goes_to_failed(self, client, auth_override):
        tc = _mock_test_case(4, owner_id=1)
        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", return_value=tc),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=False),
        ):
            resp = client.request("DELETE", "/tests/batch", json={"ids": [4]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert 4 in data["failed"]

    def test_exactly_100_ids_is_accepted(self, client, auth_override):
        """100 IDs is within the cap and must not be rejected."""
        ids = list(range(1, 101))  # exactly 100

        def mock_get(db, test_case_id):
            return _mock_test_case(test_case_id, owner_id=1)

        with (
            patch("app.api.v1.endpoints.tests.crud.get_test_case", side_effect=mock_get),
            patch("app.api.v1.endpoints.tests.crud.delete_test_case", return_value=True),
        ):
            resp = client.request("DELETE", "/tests/batch", json={"ids": ids})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 100
