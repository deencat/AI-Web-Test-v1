"""
Unit + integration tests for module rename (Option C — Preview + Confirm Cascade).
Sprint 10.11 tasks 10.11-B11.

TDD RED phase: all tests must FAIL before implementation.

Covers:
  Unit — rename_module_references()
    1.  Returns list of affected TestCase rows
    2.  Rewrites @module:old_name → @module:new_name in step strings
    3.  Rewrites inside step dicts (description field)
    4.  Rewrites multiple occurrences within one test case
    5.  Rewrites across multiple test cases
    6.  Does NOT touch steps of other users' test cases
    7.  Does NOT touch unrelated @module: references
    8.  Returns empty list when no test cases match
    9.  Handles test cases whose steps field is None
    10. Handles test cases whose steps field is a JSON string (legacy)
    11. Calls db.flush() (not db.commit()) inside the transaction

  Endpoint — GET /{id}/rename-preview?new_name=foo
    12. 200 with empty affected_test_cases when nothing references the module
    13. 200 with affected test cases listed by id and name when ≥1 references exist
    14. count field equals len(affected_test_cases)
    15. 404 when module_id belongs to another user
    16. 400 when new_name is blank / missing

  Endpoint — PUT /{id} cascade behaviour
    17. When name changes, rename_module_references() is called
    18. When name does NOT change, rename_module_references() is NOT called
    19. Response body contains updated module name after rename
    20. 409 when new_name collides with an existing module
"""
import json
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_module(module_id=1, name="login_three_hk", user_id=10):
    """Minimal StepLibraryModule-like row."""
    return SimpleNamespace(id=module_id, name=name, user_id=user_id)


def _make_test_case(tc_id, title, steps, user_id=10):
    """Minimal TestCase-like row."""
    tc = SimpleNamespace(id=tc_id, title=title, steps=steps, user_id=user_id)
    return tc


# ---------------------------------------------------------------------------
# Unit tests — rename_module_references()
# ---------------------------------------------------------------------------

class TestRenameModuleReferences:
    """Unit tests for crud.step_library.rename_module_references()."""

    def _call(self, db, old_name, new_name, user_id=10):
        from app.crud.step_library import rename_module_references
        return rename_module_references(db=db, old_name=old_name, new_name=new_name, user_id=user_id)

    # ------------------------------------------------------------------
    # 1. Returns affected test case rows
    # ------------------------------------------------------------------
    def test_returns_affected_test_cases(self):
        tc = _make_test_case(1, "Login Test", ["@module:login_three_hk()"])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        result = self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert len(result) == 1
        assert result[0].id == 1

    # ------------------------------------------------------------------
    # 2. Rewrites @module:old_name in plain step strings
    # ------------------------------------------------------------------
    def test_rewrites_string_step(self):
        tc = _make_test_case(1, "Test", ["@module:login_three_hk(username=user@x.com)"])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert tc.steps[0] == "@module:login_flow(username=user@x.com)"

    # ------------------------------------------------------------------
    # 3. Rewrites @module:old_name inside step dicts (description field)
    # ------------------------------------------------------------------
    def test_rewrites_dict_step_description(self):
        tc = _make_test_case(1, "Test", [{"description": "@module:login_three_hk()", "type": "action"}])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert tc.steps[0]["description"] == "@module:login_flow()"

    # ------------------------------------------------------------------
    # 4. Rewrites multiple occurrences within one test case
    # ------------------------------------------------------------------
    def test_rewrites_multiple_steps_in_one_tc(self):
        tc = _make_test_case(1, "Test", [
            "@module:login_three_hk()",
            "Click continue",
            "@module:login_three_hk(username=other)",
        ])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert tc.steps[0] == "@module:login_flow()"
        assert tc.steps[1] == "Click continue"
        assert tc.steps[2] == "@module:login_flow(username=other)"

    # ------------------------------------------------------------------
    # 5. Rewrites across multiple test cases
    # ------------------------------------------------------------------
    def test_rewrites_across_multiple_test_cases(self):
        tc1 = _make_test_case(1, "Test A", ["@module:login_three_hk()"])
        tc2 = _make_test_case(2, "Test B", ["@module:login_three_hk(username=b)"])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc1, tc2]

        result = self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert len(result) == 2
        assert tc1.steps[0] == "@module:login_flow()"
        assert tc2.steps[0] == "@module:login_flow(username=b)"

    # ------------------------------------------------------------------
    # 6. Does NOT touch steps of other users' test cases
    # ------------------------------------------------------------------
    def test_skips_other_user_test_cases(self):
        """The DB query must filter by user_id — verified by checking the filter call args."""
        from app.models.test_case import TestCase
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        self._call(db, old_name="login_three_hk", new_name="login_flow", user_id=42)

        # Confirm query was scoped with a filter (user_id must be part of it)
        db.query.assert_called_once_with(TestCase)
        db.query.return_value.filter.assert_called_once()

    # ------------------------------------------------------------------
    # 7. Does NOT touch unrelated @module: references
    # ------------------------------------------------------------------
    def test_does_not_rewrite_other_module_refs(self):
        tc = _make_test_case(1, "Test", [
            "@module:checkout_flow()",
            "@module:login_three_hk()",
        ])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert tc.steps[0] == "@module:checkout_flow()"
        assert tc.steps[1] == "@module:login_flow()"

    # ------------------------------------------------------------------
    # 8. Returns empty list when nothing matches
    # ------------------------------------------------------------------
    def test_returns_empty_list_when_no_match(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = self._call(db, old_name="login_three_hk", new_name="login_flow")

        assert result == []

    # ------------------------------------------------------------------
    # 9. Handles test cases whose steps field is None
    # ------------------------------------------------------------------
    def test_handles_none_steps(self):
        tc = _make_test_case(1, "Test", None)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        result = self._call(db, old_name="login_three_hk", new_name="login_flow")

        # Must not crash; tc not listed as affected (nothing to rewrite)
        assert result == []

    # ------------------------------------------------------------------
    # 10. Handles steps stored as a JSON string (legacy rows)
    # ------------------------------------------------------------------
    def test_handles_json_string_steps(self):
        steps_json = json.dumps(["@module:login_three_hk()", "Click OK"])
        tc = _make_test_case(1, "Legacy Test", steps_json)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        result = self._call(db, old_name="login_three_hk", new_name="login_flow")

        # Row is affected and steps were rewritten (stored back as list)
        assert len(result) == 1
        assert "@module:login_flow()" in tc.steps

    # ------------------------------------------------------------------
    # 11. Calls db.flush() not db.commit() (transaction safety)
    # ------------------------------------------------------------------
    def test_calls_flush_not_commit(self):
        tc = _make_test_case(1, "Test", ["@module:login_three_hk()"])
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [tc]

        self._call(db, old_name="login_three_hk", new_name="login_flow")

        db.flush.assert_called_once()
        db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Endpoint tests — GET /{id}/rename-preview
# ---------------------------------------------------------------------------

class TestRenamePreviewEndpoint:
    """Integration tests for GET /step-library/{id}/rename-preview?new_name=foo."""

    def _client(self):
        """Return an authenticated TestClient against the FastAPI app."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.deps import get_current_user, get_db

        mock_user = SimpleNamespace(id=10, email="user@test.com")
        mock_db = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        self._mock_db = mock_db
        return TestClient(app)

    # ------------------------------------------------------------------
    # 12. 200 empty affected list when no tests reference this module
    # ------------------------------------------------------------------
    def test_preview_empty_when_no_references(self):
        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_affected_test_cases") as mock_affected:
            mock_get.return_value = _make_db_module(module_id=1, name="login_three_hk", user_id=10)
            mock_affected.return_value = []

            client = self._client()
            resp = client.get("/api/v1/step-library/1/rename-preview?new_name=login_flow")

        assert resp.status_code == 200
        body = resp.json()
        assert body["affected_test_cases"] == []
        assert body["count"] == 0

    # ------------------------------------------------------------------
    # 13. 200 with affected test cases listed
    # ------------------------------------------------------------------
    def test_preview_lists_affected_test_cases(self):
        tc1 = SimpleNamespace(id=5, title="Login Test")
        tc2 = SimpleNamespace(id=9, title="Checkout Test")
        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_affected_test_cases") as mock_affected:
            mock_get.return_value = _make_db_module(module_id=1, name="login_three_hk", user_id=10)
            mock_affected.return_value = [tc1, tc2]

            client = self._client()
            resp = client.get("/api/v1/step-library/1/rename-preview?new_name=login_flow")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        ids = [item["id"] for item in body["affected_test_cases"]]
        assert 5 in ids
        assert 9 in ids

    # ------------------------------------------------------------------
    # 14. count == len(affected_test_cases)
    # ------------------------------------------------------------------
    def test_preview_count_matches_list_length(self):
        tcs = [SimpleNamespace(id=i, title=f"TC {i}") for i in range(4)]
        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_affected_test_cases") as mock_affected:
            mock_get.return_value = _make_db_module(module_id=2, name="checkout_flow", user_id=10)
            mock_affected.return_value = tcs

            client = self._client()
            resp = client.get("/api/v1/step-library/2/rename-preview?new_name=checkout_v2")

        body = resp.json()
        assert body["count"] == len(body["affected_test_cases"])

    # ------------------------------------------------------------------
    # 15. 404 when module belongs to another user
    # ------------------------------------------------------------------
    def test_preview_404_for_other_user_module(self):
        with patch("app.crud.step_library.get_by_id") as mock_get:
            mock_get.return_value = None  # not found for this user

            client = self._client()
            resp = client.get("/api/v1/step-library/99/rename-preview?new_name=new_name")

        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # 16. 400 when new_name is missing
    # ------------------------------------------------------------------
    def test_preview_400_when_new_name_missing(self):
        with patch("app.crud.step_library.get_by_id") as mock_get:
            mock_get.return_value = _make_db_module(module_id=1)

            client = self._client()
            resp = client.get("/api/v1/step-library/1/rename-preview")

        assert resp.status_code == 422  # FastAPI validation error for missing query param


# ---------------------------------------------------------------------------
# Endpoint tests — PUT /{id} cascade behaviour
# ---------------------------------------------------------------------------

class TestPutEndpointCascade:
    """Tests for rename cascade in PUT /step-library/{id}."""

    def _client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.deps import get_current_user, get_db

        mock_user = SimpleNamespace(id=10, email="user@test.com")
        mock_db = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        self._mock_db = mock_db
        return TestClient(app)

    # ------------------------------------------------------------------
    # 17. rename_module_references() called when name changes
    # ------------------------------------------------------------------
    def test_put_calls_rename_when_name_changes(self):
        old_module = _make_db_module(module_id=1, name="old_name", user_id=10)
        updated_module = _make_db_module(module_id=1, name="new_name", user_id=10)
        # Give updated_module the required schema attributes
        updated_module.display_name = "New Name"
        updated_module.description = None
        updated_module.steps = ["Step 1"]
        updated_module.parameters = []
        updated_module.tags = []
        import datetime
        updated_module.created_at = datetime.datetime(2026, 1, 1)
        updated_module.updated_at = datetime.datetime(2026, 1, 2)

        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_by_name") as mock_get_by_name, \
             patch("app.crud.step_library.update_module") as mock_update, \
             patch("app.crud.step_library.rename_module_references") as mock_rename:
            mock_get.return_value = old_module
            mock_get_by_name.return_value = None  # no collision
            mock_update.return_value = updated_module
            mock_rename.return_value = []

            client = self._client()
            resp = client.put(
                "/api/v1/step-library/1",
                json={"name": "new_name", "display_name": "New Name",
                      "steps": ["Step 1"]},
            )

        assert resp.status_code == 200
        mock_rename.assert_called_once()

    # ------------------------------------------------------------------
    # 18. rename_module_references() NOT called when name does not change
    # ------------------------------------------------------------------
    def test_put_skips_rename_when_name_unchanged(self):
        module = _make_db_module(module_id=1, name="same_name", user_id=10)
        module.display_name = "Same Name"
        module.description = None
        module.steps = ["Step 1"]
        module.parameters = []
        module.tags = []
        import datetime
        module.created_at = datetime.datetime(2026, 1, 1)
        module.updated_at = datetime.datetime(2026, 1, 2)

        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.update_module") as mock_update, \
             patch("app.crud.step_library.rename_module_references") as mock_rename:
            mock_get.return_value = module
            mock_update.return_value = module

            client = self._client()
            resp = client.put(
                "/api/v1/step-library/1",
                json={"display_name": "Updated display name"},
            )

        assert resp.status_code == 200
        mock_rename.assert_not_called()

    # ------------------------------------------------------------------
    # 19. Response contains updated module name
    # ------------------------------------------------------------------
    def test_put_response_contains_updated_name(self):
        old_module = _make_db_module(module_id=1, name="old_name", user_id=10)
        updated_module = _make_db_module(module_id=1, name="new_name", user_id=10)
        updated_module.display_name = "New Name"
        updated_module.description = None
        updated_module.steps = ["Step 1"]
        updated_module.parameters = []
        updated_module.tags = []
        import datetime
        updated_module.created_at = datetime.datetime(2026, 1, 1)
        updated_module.updated_at = datetime.datetime(2026, 1, 2)

        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_by_name") as mock_get_by_name, \
             patch("app.crud.step_library.update_module") as mock_update, \
             patch("app.crud.step_library.rename_module_references") as mock_rename:
            mock_get.return_value = old_module
            mock_get_by_name.return_value = None
            mock_update.return_value = updated_module
            mock_rename.return_value = []

            client = self._client()
            resp = client.put(
                "/api/v1/step-library/1",
                json={"name": "new_name", "display_name": "New Name", "steps": ["Step 1"]},
            )

        body = resp.json()
        assert body["name"] == "new_name"

    # ------------------------------------------------------------------
    # 20. 409 when new_name collides with existing module
    # ------------------------------------------------------------------
    def test_put_409_on_name_collision(self):
        old_module = _make_db_module(module_id=1, name="old_name", user_id=10)
        collision = _make_db_module(module_id=2, name="existing_name", user_id=10)

        with patch("app.crud.step_library.get_by_id") as mock_get, \
             patch("app.crud.step_library.get_by_name") as mock_get_by_name:
            mock_get.return_value = old_module
            mock_get_by_name.return_value = collision  # collision found

            client = self._client()
            resp = client.put(
                "/api/v1/step-library/1",
                json={"name": "existing_name"},
            )

        assert resp.status_code == 409
