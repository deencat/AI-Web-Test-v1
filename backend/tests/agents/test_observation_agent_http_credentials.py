"""HTTP Basic credential support for ObservationAgent workflow."""

import base64
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))


def _make_agent():
    with patch.dict(
        "sys.modules",
        {"playwright": MagicMock(), "playwright.async_api": MagicMock()},
    ):
        from agents.observation_agent import ObservationAgent

        agent = ObservationAgent.__new__(ObservationAgent)
        agent.config = {"enable_flow_crawling": True}
        agent.max_depth = 1
        agent.max_browser_steps = 50
        agent.llm_client = None
        return agent


class TestWorkflowSchemas:
    def test_observation_request_accepts_http_credentials(self):
        from app.schemas.workflow import ObservationRequest

        request = ObservationRequest(
            url="https://wwwuat.three.com.hk/",
            http_credentials={"username": "uat_user", "password": "secret"},
        )

        assert request.http_credentials == {
            "username": "uat_user",
            "password": "secret",
        }

    def test_generate_tests_request_accepts_http_credentials(self):
        from app.schemas.workflow import GenerateTestsRequest

        request = GenerateTestsRequest(
            url="https://wwwuat.three.com.hk/",
            http_credentials={"username": "uat_user", "password": "secret"},
        )

        assert request.http_credentials == {
            "username": "uat_user",
            "password": "secret",
        }

    def test_observation_request_accepts_browser_profile_data(self):
        from app.schemas.workflow import ObservationRequest

        request = ObservationRequest(
            url="https://wwwuat.three.com.hk/",
            browser_profile_data={
                "cookies": [],
                "localStorage": {"journey": "active"},
                "sessionStorage": {"selectedPlan": "world"},
            },
        )

        assert request.browser_profile_data is not None
        assert request.browser_profile_data["localStorage"]["journey"] == "active"


class TestObservationAgentHelpers:
    def test_build_browser_profile_includes_basic_auth_header(self):
        agent = _make_agent()
        expected = base64.b64encode(b"uat_user:secret").decode()

        with patch("browser_use.BrowserProfile") as mock_profile:
            mock_profile.return_value = MagicMock()
            agent._build_browser_profile(
                {"username": "uat_user", "password": "secret"}
            )

        kwargs = mock_profile.call_args.kwargs
        assert kwargs["headers"]["Authorization"] == f"Basic {expected}"
        assert kwargs["headless"] is False

    def test_build_browser_profile_omits_header_without_credentials(self):
        agent = _make_agent()

        with patch("browser_use.BrowserProfile") as mock_profile:
            mock_profile.return_value = MagicMock()
            agent._build_browser_profile(None)

        headers = mock_profile.call_args.kwargs.get("headers")
        assert not headers or "Authorization" not in headers

    def test_build_authenticated_url_encodes_special_characters(self):
        agent = _make_agent()

        result = agent._build_authenticated_url(
            "https://example.com/path",
            {"username": "user+1", "password": "p@ss:word"},
        )

        assert result == "https://user%2B1:p%40ss%3Aword@example.com/path"

    def test_build_browser_profile_includes_storage_state_from_browser_profile_data(self):
        agent = _make_agent()

        with patch("browser_use.BrowserProfile") as mock_profile:
            mock_profile.return_value = MagicMock()
            agent._build_browser_profile(
                http_credentials=None,
                url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
                browser_profile_data={
                    "cookies": [{"name": "sid", "value": "123", "domain": ".three.com.hk", "path": "/"}],
                    "localStorage": {"journey": "active"},
                    "sessionStorage": {"selectedPlan": "world"},
                },
            )

        storage_state = mock_profile.call_args.kwargs["storage_state"]
        assert storage_state["cookies"][0]["name"] == "sid"
        assert storage_state["origins"][0]["origin"] == "https://wwwuat.three.com.hk"
        assert storage_state["origins"][0]["localStorage"][0] == {"name": "journey", "value": "active"}
        assert storage_state["origins"][0]["sessionStorage"][0] == {"name": "selectedPlan", "value": "world"}


class TestExecuteTaskPassThrough:
    @pytest.mark.asyncio
    async def test_execute_task_forwards_http_credentials_to_flow_crawling(self):
        from agents.base_agent import TaskContext

        agent = _make_agent()
        result = MagicMock(success=True)

        with patch.object(
            agent,
            "_execute_multi_page_flow_crawling",
            new_callable=AsyncMock,
            return_value=result,
        ) as mock_flow:
            task = TaskContext(
                conversation_id="wf-1",
                task_id="obs-1",
                task_type="ui_element_extraction",
                payload={
                    "url": "https://wwwuat.three.com.hk/",
                    "user_instruction": "Observe the purchase flow",
                    "http_credentials": {
                        "username": "uat_user",
                        "password": "secret",
                    },
                },
                priority=8,
            )

            await agent.execute_task(task)

        assert mock_flow.call_args.kwargs["http_credentials"] == {
            "username": "uat_user",
            "password": "secret",
        }

    @pytest.mark.asyncio
    async def test_execute_task_forwards_browser_profile_data_to_flow_crawling(self):
        from agents.base_agent import TaskContext

        agent = _make_agent()
        result = MagicMock(success=True)

        browser_profile_data = {
            "cookies": [],
            "localStorage": {"journey": "active"},
            "sessionStorage": {"selectedPlan": "world"},
        }

        with patch.object(
            agent,
            "_execute_multi_page_flow_crawling",
            new_callable=AsyncMock,
            return_value=result,
        ) as mock_flow:
            task = TaskContext(
                conversation_id="wf-1b",
                task_id="obs-1b",
                task_type="ui_element_extraction",
                payload={
                    "url": "https://wwwuat.three.com.hk/",
                    "user_instruction": "Observe the purchase flow",
                    "browser_profile_data": browser_profile_data,
                },
                priority=8,
            )

            await agent.execute_task(task)

        assert mock_flow.call_args.kwargs["browser_profile_data"] == browser_profile_data

    @pytest.mark.asyncio
    async def test_flow_crawling_builds_profile_and_uses_authenticated_url(self):
        from agents.base_agent import TaskContext

        agent = _make_agent()
        fake_history = MagicMock(final_result=lambda: '{"ui_elements": []}')
        fake_browser_agent = MagicMock()
        fake_browser_agent.run = AsyncMock(return_value=fake_history)

        with (
            patch.object(agent, "_build_browser_profile", return_value=MagicMock()) as mock_profile,
            patch.object(agent, "_create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Browser", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=fake_browser_agent) as mock_browser_agent_ctor,
        ):
            task = TaskContext(
                conversation_id="wf-2",
                task_id="obs-2",
                task_type="ui_element_extraction",
                payload={},
                priority=8,
            )

            try:
                await agent._execute_multi_page_flow_crawling(
                    task=task,
                    url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
                    user_instruction="Observe the purchase flow",
                    login_credentials={},
                    gmail_credentials={},
                    auth=None,
                    http_credentials={"username": "uat_user", "password": "secret"},
                )
            except Exception:
                pass

        mock_profile.assert_called_once_with(
            http_credentials={"username": "uat_user", "password": "secret"},
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            browser_profile_data=None,
        )
        browser_task = mock_browser_agent_ctor.call_args.kwargs["task"]
        assert "https://uat_user:secret@wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/" in browser_task


class TestOrchestrationPassThrough:
    @pytest.mark.asyncio
    async def test_run_observation_only_passes_http_credentials(self):
        from app.services.orchestration_service import OrchestrationService

        service = OrchestrationService.__new__(OrchestrationService)
        service.progress_tracker = None
        mock_observation_agent = MagicMock()
        mock_task_result = MagicMock(
            success=True,
            result={"ui_elements": [], "page_context": {"url": "https://example.com"}},
            execution_time_seconds=1.0,
        )
        mock_observation_agent.execute_task = AsyncMock(return_value=mock_task_result)
        service._create_agents = MagicMock(return_value=(mock_observation_agent, None, None, None))

        with (
            patch("app.services.workflow_store.update_state"),
            patch("app.services.workflow_store.set_state"),
        ):
            await service.run_observation_only(
                workflow_id="wf-obs",
                request={
                    "url": "https://wwwuat.three.com.hk/",
                    "user_instruction": "Observe the purchase flow",
                    "http_credentials": {
                        "username": "uat_user",
                        "password": "secret",
                    },
                },
            )

        task_context = mock_observation_agent.execute_task.call_args.args[0]
        assert task_context.payload["http_credentials"] == {
            "username": "uat_user",
            "password": "secret",
        }

    @pytest.mark.asyncio
    async def test_run_observation_only_passes_browser_profile_data(self):
        from app.services.orchestration_service import OrchestrationService

        service = OrchestrationService.__new__(OrchestrationService)
        service.progress_tracker = None
        mock_observation_agent = MagicMock()
        mock_task_result = MagicMock(
            success=True,
            result={"ui_elements": [], "page_context": {"url": "https://example.com"}},
            execution_time_seconds=1.0,
        )
        mock_observation_agent.execute_task = AsyncMock(return_value=mock_task_result)
        service._create_agents = MagicMock(return_value=(mock_observation_agent, None, None, None))

        browser_profile_data = {
            "cookies": [],
            "localStorage": {"journey": "active"},
            "sessionStorage": {"selectedPlan": "world"},
        }

        with (
            patch("app.services.workflow_store.update_state"),
            patch("app.services.workflow_store.set_state"),
        ):
            await service.run_observation_only(
                workflow_id="wf-obs-profile",
                request={
                    "url": "https://wwwuat.three.com.hk/",
                    "user_instruction": "Observe the purchase flow",
                    "browser_profile_data": browser_profile_data,
                },
            )

        task_context = mock_observation_agent.execute_task.call_args.args[0]
        assert task_context.payload["browser_profile_data"] == browser_profile_data

    @pytest.mark.asyncio
    async def test_observation_endpoint_forwards_http_credentials(self):
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from app.api.v2.api import api_router
        from app.services.orchestration_service import get_orchestration_service

        app = FastAPI()
        app.include_router(api_router, prefix="/api/v2")

        captured = {}

        async def fake_run_observation(workflow_id: str, request: dict):
            captured["request"] = request

        mock_service = MagicMock()
        mock_service.run_observation_only = AsyncMock(side_effect=fake_run_observation)
        mock_service.progress_tracker = None
        app.dependency_overrides[get_orchestration_service] = lambda: mock_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v2/observation",
                    json={
                        "url": "https://wwwuat.three.com.hk/",
                        "user_instruction": "Observe the purchase flow",
                        "http_credentials": {
                            "username": "uat_user",
                            "password": "secret",
                        },
                    },
                )
        finally:
            app.dependency_overrides.pop(get_orchestration_service, None)

        assert response.status_code == 202
        if captured.get("request"):
            assert captured["request"]["http_credentials"] == {
                "username": "uat_user",
                "password": "secret",
            }
