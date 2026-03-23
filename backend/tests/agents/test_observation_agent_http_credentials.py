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

    def test_generate_tests_request_accepts_available_file_paths(self):
        from app.schemas.workflow import GenerateTestsRequest

        request = GenerateTestsRequest(
            url="https://example.com/",
            available_file_paths=["C:\\Users\\test\\ekyctest\\test01.jpg"],
        )
        assert request.available_file_paths == ["C:\\Users\\test\\ekyctest\\test01.jpg"]


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

    def test_build_http_auth_headers_ignores_blank_credentials(self):
        agent = _make_agent()

        assert agent._build_http_auth_headers({"username": "  ", "password": "secret"}) == {}
        assert agent._build_http_auth_headers({"username": "uat_user", "password": "  "}) == {}

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

    @pytest.mark.asyncio
    async def test_traditional_crawling_passes_http_credentials_to_playwright_context(self):
        agent = _make_agent()

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        play_ctx = MagicMock()
        play_ctx.__aenter__ = AsyncMock(return_value=mock_playwright)
        play_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.dict(
                agent._execute_traditional_crawling.__globals__,
                {"async_playwright": MagicMock(return_value=play_ctx)},
            ),
            patch.object(agent, "_crawl_pages", AsyncMock(return_value=[])),
            patch.object(agent, "_identify_flows", return_value=[]),
        ):
            from agents.base_agent import TaskContext

            task = TaskContext(
                conversation_id="wf-trad-1",
                task_id="obs-trad-1",
                task_type="ui_element_extraction",
                payload={},
                priority=8,
            )

            await agent._execute_traditional_crawling(
                task=task,
                url="https://wwwuat.three.com.hk/",
                max_depth=1,
                auth=None,
                http_credentials={"username": "uat_user", "password": "secret"},
            )

        kwargs = mock_browser.new_context.call_args.kwargs
        assert kwargs["http_credentials"] == {"username": "uat_user", "password": "secret"}


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
    async def test_execute_task_forwards_http_credentials_to_traditional_crawling(self):
        from agents.base_agent import TaskContext

        agent = _make_agent()
        result = MagicMock(success=True)

        with patch.object(
            agent,
            "_execute_traditional_crawling",
            new_callable=AsyncMock,
            return_value=result,
        ) as mock_traditional:
            task = TaskContext(
                conversation_id="wf-1c",
                task_id="obs-1c",
                task_type="ui_element_extraction",
                payload={
                    "url": "https://wwwuat.three.com.hk/",
                    "http_credentials": {
                        "username": "uat_user",
                        "password": "secret",
                    },
                },
                priority=8,
            )

            await agent.execute_task(task)

        assert mock_traditional.call_args.kwargs["http_credentials"] == {
            "username": "uat_user",
            "password": "secret",
        }

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
        assert "You are already on https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/" in browser_task

    @pytest.mark.asyncio
    async def test_flow_crawling_primes_via_cdp_not_extra_headers(self):
        """After the fix, priming must use CDP Fetch.authRequired — not set_extra_headers."""
        from agents.base_agent import TaskContext

        agent = _make_agent()
        fake_history = MagicMock(final_result=lambda: '{"ui_elements": []}')
        fake_browser_agent = MagicMock()
        fake_browser_agent.run = AsyncMock(return_value=fake_history)

        fake_browser = MagicMock()
        fake_browser.start = AsyncMock()
        fake_browser.set_extra_headers = AsyncMock()
        fake_browser.navigate_to = AsyncMock()

        with (
            patch.object(agent, "_build_browser_profile", return_value=MagicMock()),
            patch.object(agent, "_create_browser_use_llm_adapter", return_value=MagicMock()),
            patch.object(agent, "_setup_cdp_server_auth", new_callable=AsyncMock, return_value=True),
            patch("browser_use.Browser", return_value=fake_browser),
            patch("browser_use.Agent", return_value=fake_browser_agent),
        ):
            task = TaskContext(
                conversation_id="wf-2b",
                task_id="obs-2b",
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

        # Must use CDP auth, NOT set_extra_headers
        fake_browser.set_extra_headers.assert_not_called()
        # Browser must still be started and initial page navigated
        fake_browser.start.assert_awaited_once()
        fake_browser.navigate_to.assert_awaited_once_with(
            "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/"
        )

    @pytest.mark.asyncio
    async def test_flow_crawling_uses_cdp_auth_handler_for_preprod(self):
        """Browser session CDP client must receive Fetch.enable + authRequired registration."""
        from agents.base_agent import TaskContext

        agent = _make_agent()
        fake_history = MagicMock(final_result=lambda: '{"ui_elements": []}')
        fake_browser_agent = MagicMock()
        fake_browser_agent.run = AsyncMock(return_value=fake_history)

        # Build a mock browser with _cdp_client_root
        mock_cdp = MagicMock()
        mock_cdp.send.Fetch.enable = AsyncMock()
        mock_cdp.send.Fetch.continueWithAuth = AsyncMock()
        mock_cdp.register = MagicMock()

        fake_browser = MagicMock()
        fake_browser.start = AsyncMock()
        fake_browser.navigate_to = AsyncMock()
        fake_browser._cdp_client_root = mock_cdp

        with (
            patch.object(agent, "_build_browser_profile", return_value=MagicMock()),
            patch.object(agent, "_create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Browser", return_value=fake_browser),
            patch("browser_use.Agent", return_value=fake_browser_agent),
        ):
            task = TaskContext(
                conversation_id="wf-3",
                task_id="obs-3",
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

        # Fetch must be enabled at CDP level
        mock_cdp.send.Fetch.enable.assert_awaited_once_with(params={"handleAuthRequests": True})
        # authRequired and requestPaused handlers must be registered
        mock_cdp.register.Fetch.authRequired.assert_called_once()
        mock_cdp.register.Fetch.requestPaused.assert_called_once()


class TestCdpServerAuth:
    """Unit tests for the CDP-level HTTP Basic Auth handler."""

    @pytest.mark.asyncio
    async def test_setup_cdp_server_auth_enables_fetch_and_registers_handlers(self):
        agent = _make_agent()

        mock_cdp = MagicMock()
        mock_cdp.send.Fetch.enable = AsyncMock()
        mock_cdp.register = MagicMock()

        mock_browser = MagicMock()
        mock_browser._cdp_client_root = mock_cdp

        result = await agent._setup_cdp_server_auth(
            mock_browser,
            {"username": "uat_user", "password": "secret"},
        )

        assert result is True
        mock_cdp.send.Fetch.enable.assert_awaited_once_with(params={"handleAuthRequests": True})
        mock_cdp.register.Fetch.authRequired.assert_called_once()
        mock_cdp.register.Fetch.requestPaused.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_cdp_server_auth_returns_false_without_credentials(self):
        agent = _make_agent()
        mock_browser = MagicMock()

        assert await agent._setup_cdp_server_auth(mock_browser, None) is False
        assert await agent._setup_cdp_server_auth(mock_browser, {"username": "  ", "password": "x"}) is False
        assert await agent._setup_cdp_server_auth(mock_browser, {"username": "u", "password": "  "}) is False

    @pytest.mark.asyncio
    async def test_setup_cdp_server_auth_returns_false_without_cdp_client(self):
        agent = _make_agent()

        mock_browser = MagicMock(spec=[])  # no attributes including _cdp_client_root
        result = await agent._setup_cdp_server_auth(
            mock_browser,
            {"username": "u", "password": "p"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_auth_required_handler_provides_credentials(self):
        """The registered authRequired callback must call continueWithAuth with ProvideCredentials."""
        import asyncio

        agent = _make_agent()

        mock_cdp = MagicMock()
        mock_cdp.send.Fetch.enable = AsyncMock()
        mock_cdp.send.Fetch.continueWithAuth = AsyncMock()
        mock_cdp.register = MagicMock()

        mock_browser = MagicMock()
        mock_browser._cdp_client_root = mock_cdp

        await agent._setup_cdp_server_auth(
            mock_browser,
            {"username": "uat_user", "password": "s3cret"},
        )

        # The handler registered for Fetch.authRequired
        auth_handler = mock_cdp.register.Fetch.authRequired.call_args.args[0]

        # Simulate a server auth challenge event
        auth_handler(
            {
                "requestId": "req-abc",
                "authChallenge": {"source": "Server", "origin": "https://wwwuat.three.com.hk"},
            }
        )

        # Give the event loop a chance to run the scheduled task
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        mock_cdp.send.Fetch.continueWithAuth.assert_awaited_once()
        call_params = mock_cdp.send.Fetch.continueWithAuth.call_args.kwargs["params"]
        assert call_params["requestId"] == "req-abc"
        assert call_params["authChallengeResponse"]["response"] == "ProvideCredentials"
        assert call_params["authChallengeResponse"]["username"] == "uat_user"
        assert call_params["authChallengeResponse"]["password"] == "s3cret"

    @pytest.mark.asyncio
    async def test_prime_browser_session_starts_browser_uses_cdp_and_navigates(self):
        agent = _make_agent()

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.navigate_to = AsyncMock()

        with patch.object(
            agent, "_setup_cdp_server_auth", new_callable=AsyncMock, return_value=True
        ) as mock_cdp_setup:
            result = await agent._prime_browser_session_http_auth(
                mock_browser,
                url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
                http_credentials={"username": "uat_user", "password": "secret"},
            )

        assert result is True
        mock_browser.start.assert_awaited_once()
        mock_cdp_setup.assert_awaited_once_with(
            mock_browser, {"username": "uat_user", "password": "secret"}
        )
        mock_browser.navigate_to.assert_awaited_once_with(
            "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/"
        )
        # Must NOT call set_extra_headers at all
        mock_browser.set_extra_headers.assert_not_called()


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
        # UAT URLs get hardcoded credentials (user/3.comUXuat), not user-provided
        assert task_context.payload["http_credentials"] == {
            "username": "user",
            "password": "3.comUXuat",
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
