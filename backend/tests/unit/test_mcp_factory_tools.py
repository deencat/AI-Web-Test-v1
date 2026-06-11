"""Unit tests for HF-2 MCP factory tool wrappers."""
import pytest
from unittest.mock import AsyncMock, patch

import mcp_server


@pytest.mark.asyncio
async def test_get_execution_feedback_calls_api():
    with patch.object(mcp_server, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = [{"id": 1, "failure_type": "timeout"}]
        result = await mcp_server.get_execution_feedback(42)
        mock_call.assert_awaited_once_with("GET", "/executions/42/feedback")
        assert result[0]["failure_type"] == "timeout"


@pytest.mark.asyncio
async def test_list_failed_executions_passes_filters():
    with patch.object(mcp_server, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"items": [], "total": 0}
        await mcp_server.list_failed_executions(since="2026-01-01T00:00:00Z", limit=10, test_case_id=5)
        mock_call.assert_awaited_once_with(
            "GET",
            "/executions/",
            params={"result": "fail", "limit": 10, "since": "2026-01-01T00:00:00Z", "test_case_id": 5},
        )


@pytest.mark.asyncio
async def test_create_test_schedule_cron():
    with patch.object(mcp_server, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 1, "cron_expression": "0 2 * * *"}
        await mcp_server.create_test_schedule(
            test_case_id=99,
            cron_expression="0 2 * * *",
        )
        args, kwargs = mock_call.await_args
        assert args[0] == "POST" and args[1] == "/schedules/"
        assert kwargs["json"]["test_case_id"] == 99
        assert kwargs["json"]["cron_expression"] == "0 2 * * *"


@pytest.mark.asyncio
async def test_get_coverage_matrix():
    with patch.object(mcp_server, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"capabilities": []}
        await mcp_server.get_coverage_matrix("proj-123")
        mock_call.assert_awaited_once_with("GET", "/requirements/proj-123/coverage-matrix")


@pytest.mark.asyncio
async def test_enqueue_journey():
    with patch.object(mcp_server, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 7, "status": "pending"}
        result = await mcp_server.enqueue_journey("diy-dashboard", project="Three-HK")
        mock_call.assert_awaited_once()
        assert result["status"] == "pending"
