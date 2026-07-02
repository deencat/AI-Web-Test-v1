"""Unit tests for QA Factory system settings override."""
from unittest.mock import MagicMock, patch

from app.services import factory_settings_service as svc


class TestEffectiveBridgeUrl:
    def test_override_wins_over_env(self):
        db = MagicMock()
        row = MagicMock()
        row.factory_orchestrator_bridge_url = "http://192.168.1.50:8790"
        db.query.return_value.filter.return_value.first.return_value = row

        with patch.object(svc, "get_env_bridge_url", return_value="http://localhost:8790"):
            assert svc.get_effective_bridge_url(db) == "http://192.168.1.50:8790"

    def test_falls_back_to_env_when_override_empty(self):
        db = MagicMock()
        row = MagicMock()
        row.factory_orchestrator_bridge_url = "   "
        db.query.return_value.filter.return_value.first.return_value = row

        with patch.object(svc, "get_env_bridge_url", return_value="http://10.0.0.2:8790"):
            assert svc.get_effective_bridge_url(db) == "http://10.0.0.2:8790"

    def test_build_response_includes_profile_names(self):
        db = MagicMock()
        row = MagicMock()
        row.factory_orchestrator_bridge_url = None
        db.query.return_value.filter.return_value.first.return_value = row

        with patch.object(svc, "get_env_bridge_url", return_value=None):
            data = svc.build_qa_factory_settings_response(db)
            assert data["routing_enabled"] is False
            assert data["profile_display_names"]["qa-orchestrator"] == "QA Orchestrator"
