"""RBAC tests for Observatory endpoints (HF-6)."""
import pytest
from fastapi import HTTPException

from app.api.deps import require_superadmin
from app.models.user import User


def _user(role: str) -> User:
    u = User()
    u.id = 1
    u.role = role
    u.is_active = True
    u.email = f"{role}@test.com"
    u.username = role
    return u


class TestObservatoryRBAC:
    def test_admin_gets_403_on_superadmin_route(self):
        dep = require_superadmin
        with pytest.raises(HTTPException) as exc:
            dep(current_user=_user("admin"))
        assert exc.value.status_code == 403

    def test_superadmin_allowed(self):
        dep = require_superadmin
        user = dep(current_user=_user("superadmin"))
        assert user.role == "superadmin"
