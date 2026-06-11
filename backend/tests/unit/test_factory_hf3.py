"""Unit tests for Hermes QA Factory HF-3 worker and chat."""
import pytest
from unittest.mock import MagicMock, patch

from app.services.agent_chat_service import parse_chat_to_job
from app.services.factory_journey_service import _build_crawl_body, _build_user_instruction
from app.models.journey_factory import JourneyRegistryEntry


class TestAgentChatHF3:
    def test_parse_drain_backlog(self):
        job, reply = parse_chat_to_job("Drain backlog for Three-HK", {"project": "Three-HK"})
        assert job.job_type == "drain_backlog"
        assert "drain_backlog" in reply

    def test_parse_full_cycle(self):
        job, reply = parse_chat_to_job("Run full cycle", {})
        assert job.job_type == "full_cycle"
        assert "full_cycle" in reply

    def test_parse_generate_journey_with_slug(self):
        job, _ = parse_chat_to_job(
            "Generate journey diy-dashboard",
            {"project": "Three-HK"},
        )
        assert job.job_type == "generate_journey"
        assert job.params["journey_slug"] == "diy-dashboard"


class TestJourneyCrawlBody:
    def test_build_instruction_with_stop_hint(self):
        entry = JourneyRegistryEntry(
            slug="test",
            project="Three-HK",
            name="Test Journey",
            feature_url="https://example.com",
            requires_login=True,
            stop_at_page_hint="SIM Card Setting",
        )
        text = _build_user_instruction(entry)
        assert "SIM Card Setting" in text
        assert "Login" in text

    def test_build_crawl_body_merges_defaults(self):
        entry = JourneyRegistryEntry(
            slug="test",
            project="Three-HK",
            name="Test Journey",
            feature_url="https://example.com",
            tags=["diy"],
            capability_keys=["X"],
        )
        meta = MagicMock()
        meta.default_env_config = {"login_module": "login_my3_andrew", "max_browser_steps": 50}
        body = _build_crawl_body(entry, meta)
        assert body["login_module"] == "login_my3_andrew"
        assert "factory-generated" in body["tags"]
        assert "regression" in body["tags"]


class TestDrainBacklogWorker:
    @patch("app.services.factory_worker.generate_journey_for_backlog_item")
    @patch("app.services.factory_worker.crud_journey.list_backlog_items")
    @patch("app.services.factory_worker.append_job_event")
    def test_drain_processes_pending_items(self, mock_event, mock_list, mock_gen):
        from app.services.factory_worker import _drain_backlog
        from app.models.factory_job import FactoryJob

        item = MagicMock()
        item.id = 1
        item.journey_slug = "diy-dashboard"
        mock_list.return_value = [item]
        mock_gen.return_value = 42

        job = FactoryJob(id="j1", job_type="drain_backlog", params={"max_items": 1})
        db = MagicMock()
        _drain_backlog(db, job)
        mock_gen.assert_called_once()
