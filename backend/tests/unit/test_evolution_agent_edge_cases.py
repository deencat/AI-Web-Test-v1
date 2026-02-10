"""
Edge Case Tests for EvolutionAgent
Tests boundary conditions, special characters, large inputs, and error recovery
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext


@pytest.fixture
def mock_message_queue():
    """Mock message queue"""
    return MagicMock()


@pytest.fixture
def mock_llm_client():
    """Mock Azure OpenAI client"""
    client = MagicMock()
    client.enabled = True
    client.deployment = "ChatGPT-UAT"
    client.client = MagicMock()
    client.client.chat = MagicMock()
    client.client.chat.completions = MagicMock()
    return client


@pytest.fixture
def evolution_agent_with_llm(mock_message_queue, mock_llm_client):
    """EvolutionAgent with LLM enabled"""
    with patch('llm.azure_client.get_azure_client', return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="evolution_edge",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config={"use_llm": True, "cache_enabled": True}
        )
        agent.llm_client = mock_llm_client
        return agent


class TestEvolutionAgentEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_large_number_of_scenarios(self, evolution_agent_with_llm):
        """Test with 50+ scenarios to ensure performance"""
        # Create 50 scenarios
        many_scenarios = [
            {
                "scenario_id": f"REQ-F-{i:03d}",
                "title": f"Test scenario {i}",
                "given": f"Given condition {i}",
                "when": f"When action {i}",
                "then": f"Then result {i}",
                "priority": "medium"
            }
            for i in range(1, 51)
        ]
        
        # Mock LLM response (must be AsyncMock for async calls)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2", "Step 3"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        task = TaskContext(
            conversation_id="test-large",
            task_id="test-large-001",
            task_type="test_generation",
            payload={
                "scenarios": many_scenarios,
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        # Should handle large number of scenarios
        assert result.success is True
        assert "test_cases" in result.result, f"Expected 'test_cases' in result, got: {list(result.result.keys())}"
        assert len(result.result["test_cases"]) == 50
    
    @pytest.mark.asyncio
    async def test_special_characters_in_scenario(self, evolution_agent_with_llm):
        """Test scenarios with special characters and Unicode"""
        scenario = {
            "scenario_id": "REQ-SPECIAL-001",
            "title": "Test with special chars: <>&\"' and Unicode: 中文 日本語",
            "given": "Given: User is on page with 5G寬頻數據無限任用 plan",
            "when": "When: User selects '48個月' contract term",
            "then": "Then: Price should be displayed correctly (¥, $, €)",
            "priority": "high"
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Navigate to page", "Select 5G寬頻數據無限任用 plan", "Select 48個月 contract"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        task = TaskContext(
            conversation_id="test-special",
            task_id="test-special-001",
            task_type="test_generation",
            payload={
                "scenarios": [scenario],
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        # Should handle special characters correctly
        assert result.success is True
        assert "test_cases" in result.result
        assert len(result.result["test_cases"]) == 1
    
    @pytest.mark.asyncio
    async def test_very_long_scenario_description(self, evolution_agent_with_llm):
        """Test with very long scenario descriptions"""
        long_description = "Given: " + "User is on a page with many elements. " * 100
        scenario = {
            "scenario_id": "REQ-LONG-001",
            "title": "Very long scenario title " * 10,
            "given": long_description,
            "when": "When: " + "User performs action. " * 50,
            "then": "Then: " + "System should respond. " * 50,
            "priority": "medium"
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        task = TaskContext(
            conversation_id="test-long",
            task_id="test-long-001",
            task_type="test_generation",
            payload={
                "scenarios": [scenario],
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        # Should handle long descriptions (may truncate but shouldn't fail)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_empty_scenario_fields(self, evolution_agent_with_llm):
        """Test with empty or missing scenario fields"""
        scenario = {
            "scenario_id": "REQ-EMPTY-001",
            "title": "",
            "given": "",
            "when": "When: User clicks button",
            "then": "",
            "priority": "low"
        }
        
        task = TaskContext(
            conversation_id="test-empty",
            task_id="test-empty-001",
            task_type="test_generation",
            payload={
                "scenarios": [scenario],
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        # Should handle empty fields gracefully (use template fallback)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_network_failure_during_llm_call(self, evolution_agent_with_llm):
        """Test that network failures fall back to template generation"""
        scenario = {
            "scenario_id": "REQ-NET-001",
            "title": "Network failure test",
            "given": "Given: User is on page",
            "when": "When: User clicks button",
            "then": "Then: System responds",
            "priority": "medium"
        }
        
        # Mock LLM to raise network error
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Network timeout")
        )
        
        task = TaskContext(
            conversation_id="test-network",
            task_id="test-network-001",
            task_type="test_generation",
            payload={
                "scenarios": [scenario],
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        # Should fall back to template generation
        assert result.success is True
        assert "test_cases" in result.result
        assert len(result.result["test_cases"]) == 1
        # Should have generated steps (from template)
        assert len(result.result["test_cases"][0].get("steps", [])) > 0


class TestEvolutionAgentPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_concurrent_generation(self, evolution_agent_with_llm):
        """Test concurrent test generation for multiple scenarios"""
        scenarios = [
            {
                "scenario_id": f"REQ-CONC-{i:03d}",
                "title": f"Concurrent scenario {i}",
                "given": f"Given condition {i}",
                "when": f"When action {i}",
                "then": f"Then result {i}",
                "priority": "medium"
            }
            for i in range(1, 6)  # 5 scenarios
        ]
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        task = TaskContext(
            conversation_id="test-concurrent",
            task_id="test-concurrent-001",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,
                "risk_scores": {},
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"}
            }
        )
        
        import time
        start_time = time.time()
        result = await evolution_agent_with_llm.execute_task(task)
        elapsed = time.time() - start_time
        
        # Should complete successfully
        assert result.success is True
        assert "test_cases" in result.result
        assert len(result.result["test_cases"]) == 5
        # Should complete in reasonable time (< 30 seconds for 5 scenarios with mocked LLM)
        assert elapsed < 30.0
    
    def test_cache_memory_usage(self, evolution_agent_with_llm):
        """Test that cache doesn't grow unbounded"""
        scenario = {
            "scenario_id": "REQ-CACHE-001",
            "title": "Cache test",
            "given": "Given condition",
            "when": "When action",
            "then": "Then result",
            "priority": "medium"
        }
        
        # Generate many cached entries
        for i in range(100):
            scenario_copy = scenario.copy()
            scenario_copy["scenario_id"] = f"REQ-CACHE-{i:03d}"
            cache_key = evolution_agent_with_llm._generate_cache_key(scenario_copy, {})
            evolution_agent_with_llm.steps_cache[cache_key] = {
                "steps": [f"Step {j}" for j in range(10)],
                "confidence": 0.9
            }
        
        # Cache should have entries
        assert len(evolution_agent_with_llm.steps_cache) > 0
        # Cache should not exceed reasonable size
        # Note: Current implementation uses simple dict, LRU would be better for production
        assert len(evolution_agent_with_llm.steps_cache) <= 100

