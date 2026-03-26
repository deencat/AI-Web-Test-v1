"""
Unit tests for ObservationAgent browser-use integration.

Tests cover the Three HK $368/month World Plan purchase flow and
the underlying browser-use configuration bugs:

  Bug 1 – max_steps never forwarded to agent.run()
  Bug 2 – ChatAzureOpenAI using outdated api_version
  Bug 3 – Browser() created without BrowserProfile (headless, allowed_domains)

TDD cycle: write failing tests first (RED), then fix implementation (GREEN).
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.observation_agent import ObservationAgent
from agents.base_agent import TaskContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_queue():
    """Minimal mock message queue."""
    class _MockQueue:
        async def publish(self, *a, **kw):
            pass
        async def subscribe(self, *a, **kw):
            pass
    return _MockQueue()


@pytest.fixture
def agent(mock_queue) -> ObservationAgent:
    """ObservationAgent with LLM enabled (needed for browser-use path)."""
    config = {
        "use_llm": True,
        "max_browser_steps": 50,
        "max_flow_timeout_seconds": 30,
        "enable_flow_crawling": True,
    }
    return ObservationAgent(
        message_queue=mock_queue,
        agent_id="test-obs-agent",
        priority=8,
        config=config,
    )


def make_task(url: str, instruction: str, credentials: dict | None = None) -> TaskContext:
    """Build a minimal TaskContext for testing."""
    return TaskContext(
        task_id="task-test-001",
        task_type="web_crawling",
        payload={
            "url": url,
            "user_instruction": instruction,
            "login_credentials": credentials or {},
            "gmail_credentials": {},
            "auth": None,
        },
        conversation_id="conv-test-001",
    )


# ---------------------------------------------------------------------------
# Helper: make a fake browser-use history list
# ---------------------------------------------------------------------------

def _make_fake_history(pages: list[dict]):
    """Return a fake AgentHistoryList-like object with minimal state."""
    items = []
    for p in pages:
        state = MagicMock()
        state.url = p["url"]
        state.title = p.get("title", "")
        state.interacted_element = []
        item = MagicMock()
        item.state = state
        item.result = []
        items.append(item)
    hist = MagicMock()
    hist.history = items
    return hist


# ===========================================================================
# Bug 1: max_steps must be forwarded to agent.run()
# ===========================================================================

class TestMaxStepsForwardedToRun:
    """
    agent.run() in browser-use 0.11.x accepts max_steps as a required keyword
    argument.  The ObservationAgent configures self.max_browser_steps = 50 but
    previously called agent.run() with NO arguments, silently using the library
    default of 500 steps.  This test verifies the fix.
    """

    @pytest.mark.asyncio
    async def test_agent_run_receives_max_steps(self, agent):
        """agent.run() must be called with max_steps=self.max_browser_steps."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to the $368/month World Plan",
        )

        fake_history = _make_fake_history([
            {"url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/", "title": "Three HK"}
        ])

        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(return_value=fake_history)
        mock_browser_agent.history = fake_history

        mock_browser_session = MagicMock()
        mock_browser_session.__aenter__ = AsyncMock(return_value=mock_browser_session)
        mock_browser_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", return_value=mock_browser_session),
        ):
            await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        # Bug 1 assertion: run() must receive max_steps=50 (configured value)
        mock_browser_agent.run.assert_called_once_with(max_steps=agent.max_browser_steps)

    @pytest.mark.asyncio
    async def test_max_steps_matches_config(self, mock_queue):
        """max_browser_steps from config flows through to agent.run()."""
        custom_steps = 30
        obs = ObservationAgent(
            message_queue=mock_queue,
            config={"use_llm": True, "max_browser_steps": custom_steps},
        )
        assert obs.max_browser_steps == custom_steps

        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Buy World Plan $368",
        )
        fake_history = _make_fake_history([
            {"url": "https://wwwuat.three.com.hk/", "title": "Three HK"}
        ])
        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(return_value=fake_history)
        mock_browser_agent.history = fake_history

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", return_value=MagicMock()),
        ):
            await obs._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        mock_browser_agent.run.assert_called_once_with(max_steps=custom_steps)


# ===========================================================================
# Bug 2: ChatAzureOpenAI api_version must be "2024-12-01-preview"
# ===========================================================================

class TestChatAzureOpenAIApiVersion:
    """
    browser-use 0.11.x defaults to api_version="2024-12-01-preview" which
    supports json_schema structured output needed for AgentOutput parsing.
    The old code hardcoded "2024-08-01-preview", causing schema-format errors.
    """

    def test_llm_adapter_uses_correct_api_version(self, agent):
        """ChatAzureOpenAI must be created with api_version='2024-12-01-preview'."""
        captured_kwargs = {}

        class FakeChatAzureOpenAI:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)
            # Provide .model so the post-init logger line doesn't raise
            model = "gpt-4o-fake"

        with (
            patch("browser_use.llm.azure.chat.ChatAzureOpenAI", FakeChatAzureOpenAI),
            patch.dict("os.environ", {
                "AZURE_OPENAI_API_KEY": "fake-key",
                "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com",
                "AZURE_OPENAI_MODEL": "gpt-4o",
            }),
        ):
            # Force the method to use the env-var path
            agent.llm_client = None
            agent._create_browser_use_llm_adapter()

        assert captured_kwargs.get("api_version") == "2024-12-01-preview", (
            f"Expected api_version='2024-12-01-preview', got '{captured_kwargs.get('api_version')}'"
        )

    def test_llm_adapter_does_not_use_old_api_version(self, agent):
        """The deprecated 2024-08-01-preview version must NOT be used."""
        captured_kwargs = {}

        class FakeChatAzureOpenAI:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)
            model = "gpt-4o-fake"

        with (
            patch("browser_use.llm.azure.chat.ChatAzureOpenAI", FakeChatAzureOpenAI),
            patch.dict("os.environ", {
                "AZURE_OPENAI_API_KEY": "fake-key",
                "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com",
                "AZURE_OPENAI_MODEL": "gpt-4o",
            }),
        ):
            agent.llm_client = None
            agent._create_browser_use_llm_adapter()

        assert captured_kwargs.get("api_version") != "2024-08-01-preview", (
            "api_version '2024-08-01-preview' is outdated and must not be used"
        )


# ===========================================================================
# Bug 3: Browser() must be configured with BrowserProfile
# ===========================================================================

class TestBrowserProfileConfiguration:
    """
    Browser() (BrowserSession in 0.11.x) must receive a BrowserProfile so
    that headless mode, allowed_domains, and other settings are respected
    for the purchase flow.
    """

    @pytest.mark.asyncio
    async def test_browser_created_with_browser_profile(self, agent):
        """Browser() must be called with a browser_profile keyword argument."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368/month World Plan",
        )
        fake_history = _make_fake_history([
            {"url": "https://wwwuat.three.com.hk/", "title": "Three HK"}
        ])
        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(return_value=fake_history)
        mock_browser_agent.history = fake_history

        browser_init_kwargs = {}

        class CaptureBrowser:
            def __init__(self, **kwargs):
                browser_init_kwargs.update(kwargs)

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", CaptureBrowser),
        ):
            await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        assert "browser_profile" in browser_init_kwargs, (
            "Browser() must receive a browser_profile= argument for proper configuration"
        )

    @pytest.mark.asyncio
    async def test_browser_profile_sets_headless_false_for_purchase_flow(self, agent):
        """Browser profile must set headless=False so the purchase flow is visible."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Complete the $368/month World Plan subscription purchase",
        )
        fake_history = _make_fake_history([
            {"url": "https://wwwuat.three.com.hk/", "title": "Three HK"}
        ])
        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(return_value=fake_history)
        mock_browser_agent.history = fake_history

        captured_profile = {}

        class CaptureBrowser:
            def __init__(self, **kwargs):
                captured_profile.update(kwargs)

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", CaptureBrowser),
        ):
            await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        profile = captured_profile.get("browser_profile")
        assert profile is not None, "browser_profile must not be None"
        # BrowserProfile in browser-use 0.11.x stores headless as an attribute
        headless_val = getattr(profile, "headless", None)
        assert headless_val is False, (
            f"BrowserProfile.headless must be False for purchase flows, got {headless_val!r}"
        )

    def test_build_browser_profile_sets_reliable_defaults_without_saved_profile(self, agent):
        """Fresh observation sessions should still use stable browser settings for purchase flows."""
        with patch("browser_use.BrowserProfile") as mock_profile:
            mock_profile.return_value = MagicMock()

            agent._build_browser_profile(
                http_credentials=None,
                url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
                browser_profile_data=None,
            )

        kwargs = mock_profile.call_args.kwargs
        assert kwargs["headless"] is False
        assert kwargs["viewport"] == {"width": 1280, "height": 720}
        assert kwargs["window_size"] == {"width": 1280, "height": 720}
        assert "Chrome/" in kwargs["user_agent"]
        assert "--disable-blink-features=AutomationControlled" in kwargs["args"]
        assert kwargs["wait_for_network_idle_page_load_time"] >= 1.0
        assert kwargs["minimum_wait_page_load_time"] >= 0.5


# ===========================================================================
# Three HK $368 World Plan – task description content
# ===========================================================================

class TestThreeHKWorldPlanTaskDescription:
    """
    Verify the task description built for the Three HK $368/month World Plan
    purchase flow contains all required navigation cues.
    """

    def _capture_task_description(self, agent, task) -> str:
        """Run the flow method up to where the BrowserUseAgent is constructed
        and capture the task string passed to it."""
        captured = {}

        class CaptureAgent:
            def __init__(self, task, **kwargs):
                captured["task"] = task

            async def run(self, *a, **kw):
                return _make_fake_history([
                    {"url": "https://wwwuat.three.com.hk/success", "title": "Order Confirmed"}
                ])

            @property
            def history(self):
                return _make_fake_history([
                    {"url": "https://wwwuat.three.com.hk/success", "title": "Order Confirmed"}
                ])

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", CaptureAgent),
            patch("browser_use.Browser", MagicMock()),
        ):
            asyncio.get_event_loop().run_until_complete(
                agent._execute_multi_page_flow_crawling(
                    task=task,
                    url=task.payload["url"],
                    user_instruction=task.payload["user_instruction"],
                    login_credentials=task.payload.get("login_credentials", {}),
                    gmail_credentials=task.payload.get("gmail_credentials", {}),
                    auth=None,
                )
            )
        return captured.get("task", "")

    def test_task_description_contains_target_url(self, agent):
        """Task description must reference the Three HK UAT URL."""
        url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/"
        task = make_task(url=url, instruction="Subscribe to $368/month World Plan")
        desc = self._capture_task_description(agent, task)
        assert url in desc, "Task description must contain the target URL"

    def test_task_description_contains_user_instruction(self, agent):
        """Task description must embed the user's purchase instruction verbatim."""
        instruction = "Subscribe to the $368 per month World Plan"
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction=instruction,
        )
        desc = self._capture_task_description(agent, task)
        assert instruction in desc, "Task description must contain the full user instruction"

    def test_task_description_contains_login_credentials_when_provided(self, agent):
        """If credentials are given, they must appear in the task description."""
        creds = {"email": "test@example.com", "password": "secret123"}
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
            credentials=creds,
        )
        desc = self._capture_task_description(agent, task)
        assert "test@example.com" in desc
        assert "secret123" in desc

    def test_task_description_excludes_credentials_when_not_provided(self, agent):
        """No credential references when no credentials are provided."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
            credentials={},
        )
        desc = self._capture_task_description(agent, task)
        # Should NOT contain credential-injection text
        assert "Target website email:" not in desc
        assert "Target website password:" not in desc

    def test_task_description_requires_modal_recovery_without_restart(self, agent):
        """Three HK purchase guidance must tell the agent to close reminders and continue from the same step."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )

        desc = self._capture_task_description(agent, task)

        assert "If a reminder, confirmation, or informational modal appears" in desc
        assert "click the close, confirm, or I understand button" in desc
        assert "continue from the current step without restarting the purchase flow" in desc

    def test_task_description_requires_reselecting_previous_choice_after_redirect(self, agent):
        """Fresh sessions must recover by reselecting the same plan if the site redirects backward."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )

        desc = self._capture_task_description(agent, task)

        assert "If the site unexpectedly returns to an earlier plan-selection step" in desc
        assert "reselect the same plan or add-on choices you already made" in desc
        assert "resume progressing forward instead of starting over with a different plan" in desc

    def test_task_description_warns_against_my3_and_requires_upload_link(self, agent):
        """Three HK UAT task must steer away from My3 promo and toward Identity Document Upload link."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )
        desc = self._capture_task_description(agent, task)
        assert "Download My3 App" in desc
        assert "Never click" in desc or "off-limits" in desc
        assert "Identity Document" in desc


# ===========================================================================
# Edge cases
# ===========================================================================

class TestBrowserUseEdgeCases:
    """Edge cases for the browser-use flow crawling."""

    @pytest.mark.asyncio
    async def test_cancellation_during_run_returns_empty_result(self, agent):
        """Cancellation mid-run must return a successful result with empty data."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )
        cancelled_flag = {"value": False}

        async def slow_run(*a, **kw):
            await asyncio.sleep(5)

        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(side_effect=slow_run)
        mock_browser_agent.history = MagicMock(history=[])

        def cancel_after_start():
            cancelled_flag["value"] = True
            return True

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", return_value=MagicMock()),
        ):
            result = await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
                cancel_check=cancel_after_start,
            )

        assert result.success is True
        assert result.metadata.get("cancelled") is True

    @pytest.mark.asyncio
    async def test_wall_clock_timeout_cancels_browser_use_run(self, agent):
        """After max_flow_timeout_seconds, observation must cancel agent.run before returning."""
        pytest.importorskip("browser_use")

        cancel_seen = {"v": False}

        async def hang_until_cancel(*a, **kw):
            try:
                while True:
                    await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                cancel_seen["v"] = True
                raise

        mock_browser_agent = MagicMock()
        mock_browser_agent.run = hang_until_cancel
        mock_browser_agent.history = _make_fake_history(
            [{"url": "https://wwwuat.three.com.hk/done", "title": "Done"}]
        )

        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )
        task.payload["max_flow_timeout_seconds"] = 1

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch(
                "agents.observation_agent.ObservationAgent._prime_browser_session_http_auth",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", return_value=MagicMock()),
        ):
            result = await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        assert cancel_seen["v"] is True
        assert result.success is True

    @pytest.mark.asyncio
    async def test_browser_use_not_available_falls_back_to_traditional(self, agent):
        """ImportError on browser_use must fall back to traditional crawling."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Subscribe to $368 World Plan",
        )

        fallback_called = {"value": False}

        async def fake_traditional(*a, **kw):
            fallback_called["value"] = True
            from agents.base_agent import TaskResult
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result={"pages_crawled": 0, "ui_elements": []},
                confidence=0.5,
            )

        with (
            patch.dict("sys.modules", {"browser_use": None}),
            patch(
                "agents.observation_agent.ObservationAgent._execute_traditional_crawling",
                side_effect=fake_traditional,
            ),
        ):
            result = await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials={},
                gmail_credentials={},
                auth=None,
            )

        assert fallback_called["value"] is True
        assert result.success is True

    @pytest.mark.asyncio
    async def test_null_login_credentials_does_not_crash(self, agent):
        """None login_credentials must be handled without crashing."""
        task = make_task(
            url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            instruction="Browse $368 World Plan",
            credentials=None,
        )
        # Force credentials to None in payload
        task.payload["login_credentials"] = None

        fake_history = _make_fake_history([
            {"url": "https://wwwuat.three.com.hk/", "title": "Three HK"}
        ])
        mock_browser_agent = MagicMock()
        mock_browser_agent.run = AsyncMock(return_value=fake_history)
        mock_browser_agent.history = fake_history

        with (
            patch("agents.observation_agent.ObservationAgent._create_browser_use_llm_adapter", return_value=MagicMock()),
            patch("browser_use.Agent", return_value=mock_browser_agent),
            patch("browser_use.Browser", return_value=MagicMock()),
        ):
            result = await agent._execute_multi_page_flow_crawling(
                task=task,
                url=task.payload["url"],
                user_instruction=task.payload["user_instruction"],
                login_credentials=None,
                gmail_credentials=None,
                auth=None,
            )

        assert result is not None
