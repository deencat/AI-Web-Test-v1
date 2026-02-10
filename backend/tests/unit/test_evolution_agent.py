"""
Unit tests for EvolutionAgent
Tests code generation, LLM integration, caching, and performance scoring
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext, TaskResult


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
    # Patch the get_azure_client function and keep it active
    patcher = patch('llm.azure_client.get_azure_client', return_value=mock_llm_client)
    patcher.start()
    try:
        agent = EvolutionAgent(
            agent_id="evolution_1",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config={"use_llm": True, "cache_enabled": True}
        )
        # Ensure the mock client is set
        agent.llm_client = mock_llm_client
        yield agent
    finally:
        patcher.stop()


@pytest.fixture
def evolution_agent_no_llm(mock_message_queue):
    """EvolutionAgent without LLM (template mode)"""
    return EvolutionAgent(
        agent_id="evolution_1",
        agent_type="evolution",
        priority=5,
        message_queue=mock_message_queue,
        config={"use_llm": False, "cache_enabled": False}
    )


@pytest.fixture
def sample_bdd_scenario():
    """Sample BDD scenario for testing"""
    return {
        "scenario_id": "REQ-F-001",
        "title": "User Login - Happy Path",
        "given": "User is on login page",
        "when": "User enters valid email and password, clicks Login button",
        "then": "User is redirected to dashboard and session is created",
        "priority": "critical",
        "scenario_type": "functional",
        "confidence": 0.92
    }


@pytest.fixture
def sample_task_context(sample_bdd_scenario):
    """Sample task context for testing"""
    return TaskContext(
        task_id="task-123",
        task_type="test_generation",
        payload={
            "scenarios": [sample_bdd_scenario],
            "risk_scores": [{"scenario_id": "REQ-F-001", "rpn": 100}],
            "final_prioritization": [{"scenario_id": "REQ-F-001", "composite_score": 0.95}],
            "page_context": {
                "url": "https://example.com/login",
                "page_type": "login"
            },
            "test_data": []
        },
        conversation_id="conv-456"
    )


class TestEvolutionAgentCapabilities:
    """Test EvolutionAgent capabilities"""
    
    def test_capabilities(self, evolution_agent_with_llm):
        """Test that EvolutionAgent declares correct capabilities"""
        capabilities = evolution_agent_with_llm.capabilities
        assert len(capabilities) == 2
        assert capabilities[0].name == "test_generation"
        assert capabilities[1].name == "code_generation"
    
    @pytest.mark.asyncio
    async def test_can_handle_test_generation(self, evolution_agent_with_llm, sample_task_context):
        """Test that agent can handle test_generation tasks"""
        can_handle, confidence = await evolution_agent_with_llm.can_handle(sample_task_context)
        assert can_handle is True
        assert confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_can_handle_unknown_task(self, evolution_agent_with_llm):
        """Test that agent rejects unknown task types"""
        task = TaskContext(
            task_id="task-999",
            task_type="unknown_task",
            payload={},
            conversation_id="conv-999"
        )
        can_handle, confidence = await evolution_agent_with_llm.can_handle(task)
        assert can_handle is False
        assert confidence == 0.0


class TestEvolutionAgentCodeGeneration:
    """Test code generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_code_with_llm(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test code generation using LLM"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
```typescript
import { test, expect } from '@playwright/test';

test('User Login - Happy Path', async ({ page }) => {
  await page.goto('https://example.com/login');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
```
"""
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm._generate_test_code_with_llm(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            []
        )
        
        assert result is not None
        assert "test(" in result["code"]
        assert "@playwright/test" in result["code"]
        assert result["confidence"] > 0.0
        assert result["tokens_used"] == 500
    
    @pytest.mark.asyncio
    async def test_generate_code_from_template(self, evolution_agent_no_llm, sample_bdd_scenario):
        """Test template-based code generation (fallback)"""
        result = evolution_agent_no_llm._generate_test_code_from_template(
            sample_bdd_scenario,
            {"url": "https://example.com/login"}
        )
        
        assert result is not None
        assert "test(" in result["code"]
        assert "@playwright/test" in result["code"]
        assert result["confidence"] == 0.6  # Lower confidence for template
    
    def test_extract_code_from_response(self, evolution_agent_with_llm):
        """Test code extraction from LLM response"""
        response_with_code_block = """
Here's the test code:

```typescript
import { test, expect } from '@playwright/test';
test('example', async ({ page }) => {});
```
"""
        code = evolution_agent_with_llm._extract_code_from_response(response_with_code_block)
        assert "import" in code
        assert "test(" in code
        assert "```" not in code  # Code blocks should be removed
    
    def test_calculate_code_confidence(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test code confidence calculation"""
        good_code = """
import { test, expect } from '@playwright/test';
test('example', async ({ page }) => {
  await page.goto('https://example.com');
  expect(page).toHaveURL(/example/);
});
"""
        confidence = evolution_agent_with_llm._calculate_code_confidence(good_code, sample_bdd_scenario)
        assert confidence >= 0.7


class TestEvolutionAgentCaching:
    """Test caching functionality"""
    
    def test_cache_key_generation(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test cache key generation"""
        page_context = {"url": "https://example.com/login"}
        key1 = evolution_agent_with_llm._generate_cache_key(sample_bdd_scenario, page_context)
        key2 = evolution_agent_with_llm._generate_cache_key(sample_bdd_scenario, page_context)
        
        # Same scenario should generate same key
        assert key1 == key2
        
        # Different scenario should generate different key
        different_scenario = sample_bdd_scenario.copy()
        different_scenario["given"] = "Different precondition"
        key3 = evolution_agent_with_llm._generate_cache_key(different_scenario, page_context)
        assert key1 != key3
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, evolution_agent_with_llm, sample_task_context):
        """Test that cached results are reused"""
        # First generation (cache miss)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test code here"
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result1 = await evolution_agent_with_llm.execute_task(sample_task_context)
        assert result1.success is True
        assert result1.result["cache_hits"] == 0
        assert result1.result["cache_misses"] == 1
        
        # Second generation (cache hit)
        result2 = await evolution_agent_with_llm.execute_task(sample_task_context)
        assert result2.success is True
        assert result2.result["cache_hits"] == 1
        assert result2.result["cache_misses"] == 0
        
        # LLM should not be called on second run
        assert evolution_agent_with_llm.llm_client.client.chat.completions.create.call_count == 1


class TestEvolutionAgentExecuteTask:
    """Test execute_task method"""
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, evolution_agent_with_llm, sample_task_context):
        """Test successful task execution"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
```typescript
import { test, expect } from '@playwright/test';
test('User Login - Happy Path', async ({ page }) => {});
```
"""
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm.execute_task(sample_task_context)
        
        assert result.success is True
        assert "generation_id" in result.result
        assert "test_file" in result.result
        assert "code" in result.result
        assert result.result["test_count"] == 1
        assert result.confidence > 0.0
        assert "generation_id" in result.metadata
    
    @pytest.mark.asyncio
    async def test_execute_task_no_scenarios(self, evolution_agent_with_llm):
        """Test task execution with no scenarios"""
        task = TaskContext(
            task_id="task-empty",
            task_type="test_generation",
            payload={"scenarios": []},
            conversation_id="conv-empty"
        )
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        assert result.success is False
        assert "No scenarios" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_task_llm_failure_fallback(self, evolution_agent_with_llm, sample_task_context):
        """Test fallback to template when LLM fails"""
        evolution_agent_with_llm.llm_client.client.chat.completions.create = AsyncMock(side_effect=Exception("LLM error"))
        
        result = await evolution_agent_with_llm.execute_task(sample_task_context)
        
        # Should still succeed with template fallback
        assert result.success is True
        assert "code" in result.result


class TestEvolutionAgentPerformanceScoring:
    """Test performance scoring functionality"""
    
    @pytest.mark.asyncio
    async def test_calculate_performance_score(self, evolution_agent_with_llm):
        """Test performance score calculation"""
        task_result = TaskResult(
            task_id="task-123",
            success=True,
            result={
                "code": """
import { test, expect } from '@playwright/test';
test('example', async ({ page }) => {
  await page.goto('https://example.com');
  expect(page).toHaveURL(/example/);
});
""",
                "test_count": 1
            },
            confidence=0.85,
            execution_time_seconds=2.5,
            metadata={"token_usage": 1000}
        )
        
        execution_results = {
            "REQ-F-001": {"status": "passed"}
        }
        
        score = await evolution_agent_with_llm.calculate_performance_score(
            task_result,
            execution_results
        )
        
        assert "overall_score" in score
        assert "component_scores" in score
        assert "grade" in score
        assert "recommendations" in score
        assert score["overall_score"] > 0.0
        assert score["grade"] in ["A", "B", "C", "D", "F"]
    
    @pytest.mark.asyncio
    async def test_calculate_performance_score_failed_task(self, evolution_agent_with_llm):
        """Test performance score for failed task"""
        task_result = TaskResult(
            task_id="task-123",
            success=False,
            error="Generation failed",
            confidence=0.0
        )
        
        score = await evolution_agent_with_llm.calculate_performance_score(task_result)
        
        assert score["overall_score"] == 0.0
        assert score["grade"] == "F"
    
    def test_validate_code_syntax(self, evolution_agent_with_llm):
        """Test code syntax validation"""
        good_code = """
import { test, expect } from '@playwright/test';
test('example', async ({ page }) => {
  await page.goto('https://example.com');
  expect(page).toHaveURL(/example/);
});
"""
        score = evolution_agent_with_llm._validate_code_syntax(good_code)
        assert score >= 0.8
        
        bad_code = "invalid code"
        score = evolution_agent_with_llm._validate_code_syntax(bad_code)
        assert score < 0.5
    
    def test_calculate_execution_success_rate(self, evolution_agent_with_llm):
        """Test execution success rate calculation"""
        results = {
            "test1": {"status": "passed"},
            "test2": {"status": "passed"},
            "test3": {"status": "failed"}
        }
        
        rate = evolution_agent_with_llm._calculate_execution_success_rate(results)
        assert rate == pytest.approx(2/3, 0.01)


class TestEvolutionAgentPromptVariants:
    """Test prompt variant functionality"""
    
    def test_prompt_variant_1(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 1 (detailed, explicit)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_1(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            []
        )
        
        assert "Given:" in prompt
        assert "When:" in prompt
        assert "Then:" in prompt
        assert "Playwright" in prompt
    
    def test_prompt_variant_2(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 2 (concise, focused)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_2(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            []
        )
        
        assert "Given:" in prompt
        assert len(prompt) < 500  # Should be concise
    
    def test_prompt_variant_3(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 3 (pattern-based)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_3(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            []
        )
        
        assert "pattern" in prompt.lower() or "Pattern" in prompt


class TestEvolutionAgentFileGeneration:
    """Test test file generation"""
    
    def test_combine_tests_to_file(self, evolution_agent_with_llm):
        """Test combining multiple tests into a file"""
        generated_tests = [
            {
                "scenario_id": "REQ-F-001",
                "test_code": "test('test1', async ({ page }) => {});",
                "from_cache": False
            },
            {
                "scenario_id": "REQ-F-002",
                "test_code": "test('test2', async ({ page }) => {});",
                "from_cache": True
            }
        ]
        
        file_content = evolution_agent_with_llm._combine_tests_to_file(
            generated_tests,
            {"url": "https://example.com"}
        )
        
        assert "import" in file_content
        assert "REQ-F-001" in file_content
        assert "REQ-F-002" in file_content
        assert "(from cache)" in file_content
    
    def test_generate_test_filename(self, evolution_agent_with_llm):
        """Test test filename generation"""
        filename = evolution_agent_with_llm._generate_test_filename(
            {"url": "https://example.com/login"}
        )
        
        assert filename.endswith(".spec.ts")
        assert "example" in filename.lower() or "test" in filename.lower()

