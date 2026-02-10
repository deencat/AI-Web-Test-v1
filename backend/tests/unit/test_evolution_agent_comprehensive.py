"""
Comprehensive Unit Tests for EvolutionAgent (Sprint 9 Task 9A.5)
Tests test step generation, LLM integration, caching, database storage, and feedback loop
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
from datetime import datetime, timezone
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
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.commit = MagicMock()
    return session


@pytest.fixture
def evolution_agent_with_llm(mock_message_queue, mock_llm_client):
    """EvolutionAgent with LLM enabled"""
    with patch('llm.azure_client.get_azure_client', return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="evolution_1",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config={"use_llm": True, "cache_enabled": True}
        )
        agent.llm_client = mock_llm_client
        yield agent


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
def evolution_agent_with_db(mock_message_queue, mock_llm_client, mock_db_session):
    """EvolutionAgent with LLM and database"""
    with patch('llm.azure_client.get_azure_client', return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="evolution_1",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config={"use_llm": True, "cache_enabled": True, "db": mock_db_session}
        )
        agent.llm_client = mock_llm_client
        agent.db = mock_db_session
        yield agent


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
    """Test EvolutionAgent capabilities and can_handle"""
    
    def test_capabilities(self, evolution_agent_with_llm):
        """Test that EvolutionAgent declares correct capabilities"""
        capabilities = evolution_agent_with_llm.capabilities
        assert len(capabilities) == 2
        assert capabilities[0].name == "test_generation"
        assert capabilities[1].name == "code_generation"
        assert capabilities[0].confidence_threshold == 0.7
        assert capabilities[1].confidence_threshold == 0.75
    
    @pytest.mark.asyncio
    async def test_can_handle_test_generation(self, evolution_agent_with_llm, sample_task_context):
        """Test that agent can handle test_generation tasks"""
        can_handle, confidence = await evolution_agent_with_llm.can_handle(sample_task_context)
        assert can_handle is True
        assert confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_can_handle_high_confidence_with_many_scenarios(self, evolution_agent_with_llm):
        """Test that confidence increases with more scenarios"""
        task = TaskContext(
            task_id="task-many",
            task_type="test_generation",
            payload={"scenarios": [{}] * 50},  # 50 scenarios
            conversation_id="conv-many"
        )
        can_handle, confidence = await evolution_agent_with_llm.can_handle(task)
        assert can_handle is True
        assert confidence >= 0.95  # Should be capped at 0.95
    
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


class TestEvolutionAgentStepGeneration:
    """Test test step generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_steps_with_llm(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test step generation using LLM"""
        # Mock LLM response with JSON format
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": [
                "Navigate to https://example.com/login",
                "Enter email: test@example.com",
                "Enter password: password123",
                "Click Login button",
                "Verify URL contains /dashboard"
            ]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm._generate_test_steps_with_llm(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        assert result is not None
        assert "steps" in result
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) == 5
        assert "Navigate" in result["steps"][0]
        assert result["confidence"] > 0.0
        assert result["tokens_used"] == 500
    
    @pytest.mark.asyncio
    async def test_generate_steps_with_login_credentials(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test step generation with login credentials"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": [
                "Navigate to https://example.com/login",
                "Enter email: user@example.com",
                "Enter password: secret123",
                "Click Login button"
            ]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 400
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm._generate_test_steps_with_llm(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {"email": "user@example.com", "password": "secret123"}
        )
        
        assert result is not None
        assert len(result["steps"]) > 0
        # Verify login credentials are used in prompt (indirectly via steps)
        assert any("user@example.com" in step or "email" in step.lower() for step in result["steps"])
    
    @pytest.mark.asyncio
    async def test_generate_steps_llm_fallback_to_template(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test fallback to template when LLM fails"""
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(side_effect=Exception("LLM error"))
        
        result = await evolution_agent_with_llm._generate_test_steps_with_llm(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        # Should fallback to template
        assert result is not None
        assert "steps" in result
        assert result["confidence"] == 0.7  # Template confidence
        assert result["tokens_used"] == 0
    
    @pytest.mark.asyncio
    async def test_generate_steps_invalid_json_fallback(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test fallback when LLM returns invalid JSON"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm._generate_test_steps_with_llm(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        # Should fallback to template
        assert result is not None
        assert "steps" in result
    
    def test_generate_steps_from_template(self, evolution_agent_no_llm, sample_bdd_scenario):
        """Test template-based step generation"""
        result = evolution_agent_no_llm._generate_test_steps_from_template(
            sample_bdd_scenario,
            {"url": "https://example.com/login"}
        )
        
        assert result is not None
        assert "steps" in result
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) > 0
        assert result["confidence"] == 0.7
        assert result["tokens_used"] == 0
    
    def test_convert_scenario_to_steps(self, evolution_agent_no_llm, sample_bdd_scenario):
        """Test BDD scenario to steps conversion"""
        steps = evolution_agent_no_llm._convert_scenario_to_steps(
            sample_bdd_scenario,
            {"url": "https://example.com/login"}
        )
        
        assert isinstance(steps, list)
        assert len(steps) > 0
        # Should include navigation
        assert any("navigate" in step.lower() or "https://example.com" in step.lower() for step in steps)
        # Should include actions from "when"
        assert any("enter" in step.lower() or "click" in step.lower() for step in steps)
        # Should include verification from "then"
        assert any("verify" in step.lower() or "redirected" in step.lower() for step in steps)
    
    def test_extract_steps_from_text(self, evolution_agent_with_llm):
        """Test extracting steps from text response"""
        text_with_json = 'Here are the steps: ["Step 1", "Step 2", "Step 3"]'
        steps = evolution_agent_with_llm._extract_steps_from_text(text_with_json)
        assert isinstance(steps, list)
        assert len(steps) == 3
        
        text_with_list = """
        1. Navigate to page
        2. Click button
        3. Verify result
        """
        steps = evolution_agent_with_llm._extract_steps_from_text(text_with_list)
        assert len(steps) >= 3
    
    def test_calculate_steps_confidence(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test steps confidence calculation"""
        good_steps = [
            "Navigate to https://example.com/login",
            "Enter email: test@example.com",
            "Click Login button",
            "Verify URL contains /dashboard"
        ]
        confidence = evolution_agent_with_llm._calculate_steps_confidence(good_steps, sample_bdd_scenario)
        assert confidence >= 0.7
        assert confidence <= 0.95
        
        # Fewer steps should have lower confidence
        minimal_steps = ["Navigate to page"]
        confidence_minimal = evolution_agent_with_llm._calculate_steps_confidence(minimal_steps, sample_bdd_scenario)
        assert confidence_minimal < confidence


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
        
        # Different URL should generate different key
        different_context = {"url": "https://example.com/different"}
        key4 = evolution_agent_with_llm._generate_cache_key(sample_bdd_scenario, different_context)
        assert key1 != key4
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, evolution_agent_with_llm, sample_task_context):
        """Test that cached results are reused"""
        # Mock LLM response for first generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2", "Step 3"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        # First generation (cache miss)
        result1 = await evolution_agent_with_llm.execute_task(sample_task_context)
        assert result1.success is True
        assert result1.result["cache_hits"] == 0
        assert result1.result["cache_misses"] == 1
        
        # Second generation (cache hit)
        result2 = await evolution_agent_with_llm.execute_task(sample_task_context)
        assert result2.success is True
        assert result2.result["cache_hits"] == 1
        assert result2.result["cache_misses"] == 0
        
        # LLM should only be called once
        assert evolution_agent_with_llm.llm_client.client.chat.completions.create.call_count == 1
    
    def test_cache_disabled(self, evolution_agent_no_llm, sample_bdd_scenario):
        """Test that cache is not used when disabled"""
        assert evolution_agent_no_llm.cache_enabled is False
        # Cache should be empty
        assert len(evolution_agent_no_llm.steps_cache) == 0


class TestEvolutionAgentDatabaseStorage:
    """Test database storage functionality"""
    
    @pytest.mark.asyncio
    async def test_store_test_cases_in_database(self, evolution_agent_with_db, mock_db_session, sample_bdd_scenario):
        """Test storing test cases in database"""
        generated_test_cases = [{
            "scenario_id": "REQ-F-001",
            "steps": ["Step 1", "Step 2", "Step 3"],
            "confidence": 0.9
        }]
        
        scenarios = [sample_bdd_scenario]
        risk_scores = [{"scenario_id": "REQ-F-001", "rpn": 100}]
        prioritization = [{"scenario_id": "REQ-F-001", "composite_score": 0.95}]
        page_context = {"url": "https://example.com/login"}
        
        # Mock the TestCase model (imported inside the method)
        with patch('app.models.test_case.TestCase') as MockTestCase:
            mock_test_case = MagicMock()
            mock_test_case.id = 123
            MockTestCase.return_value = mock_test_case
            
            db_ids = await evolution_agent_with_db._store_test_cases_in_database(
                mock_db_session,
                generated_test_cases,
                scenarios,
                risk_scores,
                prioritization,
                page_context,
                "gen-123"
            )
            
            assert len(db_ids) == 1
            assert db_ids[0] == 123
            mock_db_session.add.assert_called_once()
            mock_db_session.flush.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_with_database(self, evolution_agent_with_db, sample_task_context, mock_db_session):
        """Test execute_task stores test cases in database"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 300
        
        evolution_agent_with_db.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        # Mock TestCase model (imported inside the method)
        with patch('app.models.test_case.TestCase') as MockTestCase:
            mock_test_case = MagicMock()
            mock_test_case.id = 456
            MockTestCase.return_value = mock_test_case
            
            result = await evolution_agent_with_db.execute_task(sample_task_context)
            
            assert result.success is True
            assert result.result["stored_in_database"] is True
            assert len(result.result["test_case_ids"]) == 1
            assert result.result["test_case_ids"][0] == 456


class TestEvolutionAgentPromptVariants:
    """Test prompt variant functionality"""
    
    def test_prompt_variant_1(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 1 (detailed, explicit)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_1(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        assert "Given:" in prompt or "given" in prompt.lower()
        assert "When:" in prompt or "when" in prompt.lower()
        assert "Then:" in prompt or "then" in prompt.lower()
        assert "steps" in prompt.lower() or "test" in prompt.lower()
    
    def test_prompt_variant_2(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 2 (concise, focused)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_2(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        assert len(prompt) > 0
        assert "Given" in prompt or "given" in prompt.lower()
    
    def test_prompt_variant_3(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test variant 3 (pattern-based)"""
        prompt = evolution_agent_with_llm._build_prompt_variant_3(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {}
        )
        
        assert len(prompt) > 0
        assert "pattern" in prompt.lower() or "Pattern" in prompt or "reusable" in prompt.lower()
    
    def test_prompt_variant_with_login_credentials(self, evolution_agent_with_llm, sample_bdd_scenario):
        """Test prompt includes login credentials when provided"""
        prompt = evolution_agent_with_llm._build_prompt_variant_1(
            sample_bdd_scenario,
            [],
            [],
            {"url": "https://example.com/login"},
            [],
            "",
            {"email": "user@example.com", "password": "secret123"}
        )
        
        assert "user@example.com" in prompt or "email" in prompt.lower()
        assert "login" in prompt.lower() or "credential" in prompt.lower()


class TestEvolutionAgentExecuteTask:
    """Test execute_task method"""
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, evolution_agent_with_llm, sample_task_context):
        """Test successful task execution"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Navigate to page", "Click button", "Verify result"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 400
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm.execute_task(sample_task_context)
        
        assert result.success is True
        assert "generation_id" in result.result
        assert result.result["test_count"] == 1
        assert len(result.result["test_cases"]) == 1
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
        assert "No scenarios" in result.error or "scenarios" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_task_multiple_scenarios(self, evolution_agent_with_llm):
        """Test task execution with multiple scenarios"""
        scenarios = [
            {
                "scenario_id": "REQ-F-001",
                "title": "Test 1",
                "given": "User on page",
                "when": "User clicks button",
                "then": "Page loads"
            },
            {
                "scenario_id": "REQ-F-002",
                "title": "Test 2",
                "given": "User on page",
                "when": "User enters text",
                "then": "Text appears"
            }
        ]
        
        task = TaskContext(
            task_id="task-multi",
            task_type="test_generation",
            payload={
                "scenarios": scenarios,
                "risk_scores": [],
                "final_prioritization": [],
                "page_context": {"url": "https://example.com"},
                "test_data": []
            },
            conversation_id="conv-multi"
        )
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1", "Step 2"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 300
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = await evolution_agent_with_llm.execute_task(task)
        
        assert result.success is True
        assert result.result["test_count"] == 2
        assert len(result.result["test_cases"]) == 2


class TestEvolutionAgentFeedbackLearning:
    """Test feedback learning functionality"""
    
    @pytest.mark.asyncio
    async def test_learn_from_feedback(self, evolution_agent_with_llm):
        """Test feedback learning (currently returns not_implemented)"""
        execution_results = {
            "REQ-F-001": {"status": "passed", "execution_time": 2.5},
            "REQ-F-002": {"status": "failed", "error": "Timeout"}
        }
        
        result = await evolution_agent_with_llm.learn_from_feedback(
            "gen-123",
            execution_results
        )
        
        # Currently returns not_implemented status
        assert "status" in result
        # Note: This will change when feedback learning is fully implemented


class TestEvolutionAgentErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_execute_task_exception_handling(self, evolution_agent_with_llm, sample_task_context):
        """Test that exceptions are caught and returned as error"""
        # Force an exception
        evolution_agent_with_llm._generate_test_steps_with_llm = AsyncMock(side_effect=Exception("Test error"))
        
        result = await evolution_agent_with_llm.execute_task(sample_task_context)
        
        assert result.success is False
        assert "error" in result.error.lower() or "Test error" in result.error
        assert result.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_database_storage_failure_continues(self, evolution_agent_with_db, sample_task_context, mock_db_session):
        """Test that database storage failure doesn't fail entire task"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Step 1"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200
        
        evolution_agent_with_db.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        # Make database commit fail
        mock_db_session.commit.side_effect = Exception("Database error")
        
        # Mock TestCase model (imported inside the method)
        with patch('app.models.test_case.TestCase'):
            result = await evolution_agent_with_db.execute_task(sample_task_context)
            
            # Task should still succeed, but database storage should fail gracefully
            assert result.success is True
            # Database IDs might be empty due to error
            assert result.result["stored_in_database"] is False or len(result.result["test_case_ids"]) == 0

