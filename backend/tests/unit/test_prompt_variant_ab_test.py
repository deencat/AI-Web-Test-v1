"""
Unit tests for Prompt Variant A/B Testing Framework
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from agents.prompt_variant_ab_test import (
    PromptVariantABTest,
    VariantMetrics,
    ABTestResult
)


@pytest.fixture
def sample_scenarios():
    """Sample BDD scenarios for testing"""
    return [
        {
            "scenario_id": "REQ-F-001",
            "title": "User Login",
            "given": "User is on login page",
            "when": "User enters credentials and clicks Login",
            "then": "User is redirected to dashboard",
            "priority": "critical",
            "page_context": {"url": "https://example.com/login"}
        },
        {
            "scenario_id": "REQ-F-002",
            "title": "Search Product",
            "given": "User is on homepage",
            "when": "User searches for product",
            "then": "Search results are displayed",
            "priority": "high",
            "page_context": {"url": "https://example.com"}
        }
    ]


@pytest.fixture
def mock_evolution_agent():
    """Mock EvolutionAgent for testing"""
    agent = MagicMock()
    agent.current_variant = "variant_1"
    agent.prompt_variants = {
        "variant_1": MagicMock(),
        "variant_2": MagicMock(),
        "variant_3": MagicMock()
    }
    return agent


class TestVariantMetrics:
    """Test VariantMetrics class"""
    
    def test_variant_metrics_initialization(self):
        """Test VariantMetrics initialization"""
        metrics = VariantMetrics(variant_name="variant_1")
        assert metrics.variant_name == "variant_1"
        assert metrics.sample_count == 0
        assert metrics.total_tokens == 0
        assert len(metrics.confidence_scores) == 0
    
    def test_calculate_averages(self):
        """Test average calculation"""
        metrics = VariantMetrics(variant_name="variant_1")
        metrics.confidence_scores = [0.8, 0.9, 0.85]
        metrics.token_usages = [500, 600, 550]
        metrics.generation_times = [2.0, 2.5, 2.2]
        metrics.execution_results = [
            {"status": "passed"},
            {"status": "passed"},
            {"status": "failed"}
        ]
        
        metrics.calculate_averages()
        
        assert metrics.avg_confidence == pytest.approx(0.85, 0.01)
        assert metrics.avg_tokens_per_scenario == pytest.approx(550.0, 0.01)
        assert metrics.avg_generation_time == pytest.approx(2.23, 0.01)
        assert metrics.execution_success_rate == pytest.approx(2/3, 0.01)
    
    def test_get_composite_score(self):
        """Test composite score calculation"""
        metrics = VariantMetrics(variant_name="variant_1")
        metrics.avg_confidence = 0.9
        metrics.execution_success_rate = 0.85
        metrics.steps_quality_score = 0.95
        metrics.avg_tokens_per_scenario = 1000
        metrics.avg_generation_time = 3.0
        
        score = metrics.get_composite_score()
        
        assert score > 0.0
        assert score <= 1.0
        # Should be high with good metrics
        assert score > 0.7


class TestPromptVariantABTest:
    """Test PromptVariantABTest class"""
    
    def test_ab_test_initialization(self):
        """Test A/B test initialization"""
        ab_test = PromptVariantABTest("test_001", ["variant_1", "variant_2"])
        assert ab_test.test_id == "test_001"
        assert len(ab_test.variant_names) == 2
        assert len(ab_test.variant_metrics) == 2
    
    @pytest.mark.asyncio
    async def test_run_test_basic(self, mock_evolution_agent, sample_scenarios):
        """Test basic A/B test execution"""
        ab_test = PromptVariantABTest("test_001", ["variant_1", "variant_2"], min_samples=1)
        
        # Mock execute_task to return success
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.confidence = 0.9
        mock_result.execution_time_seconds = 2.0
        mock_result.metadata = {"token_usage": 500}
        mock_result.result = {
            "test_cases": [{
                "steps": ["Navigate to page", "Click button", "Verify result"]
            }],
            "cache_hits": 0,
            "cache_misses": 1
        }
        
        mock_evolution_agent.execute_task = AsyncMock(return_value=mock_result)
        
        result = await ab_test.run_test(mock_evolution_agent, sample_scenarios)
        
        assert result.test_id == "test_001"
        assert len(result.variants_tested) == 2
        assert result.total_scenarios == 2
        assert len(result.variant_metrics) == 2
    
    @pytest.mark.asyncio
    async def test_determine_winner(self, mock_evolution_agent, sample_scenarios):
        """Test winner determination"""
        ab_test = PromptVariantABTest("test_001", ["variant_1", "variant_2"], min_samples=1)
        
        # Set up metrics
        metrics1 = VariantMetrics(variant_name="variant_1")
        metrics1.sample_count = 10
        metrics1.avg_confidence = 0.9
        metrics1.execution_success_rate = 0.95
        metrics1.steps_quality_score = 0.9
        metrics1.avg_tokens_per_scenario = 1000
        metrics1.avg_generation_time = 2.0
        
        metrics2 = VariantMetrics(variant_name="variant_2")
        metrics2.sample_count = 10
        metrics2.avg_confidence = 0.8
        metrics2.execution_success_rate = 0.85
        metrics2.steps_quality_score = 0.8
        metrics2.avg_tokens_per_scenario = 1200
        metrics2.avg_generation_time = 2.5
        
        ab_test.variant_metrics = {
            "variant_1": metrics1,
            "variant_2": metrics2
        }
        
        winner, score = ab_test._determine_winner()
        
        assert winner == "variant_1"  # Should win with better metrics
        assert score > 0.0
    
    def test_check_statistical_significance(self):
        """Test statistical significance check"""
        ab_test = PromptVariantABTest("test_001", ["variant_1", "variant_2"], min_samples=10)
        
        # Insufficient samples
        ab_test.variant_metrics["variant_1"].sample_count = 5
        ab_test.variant_metrics["variant_2"].sample_count = 5
        assert ab_test._check_statistical_significance() is False
        
        # Sufficient samples
        ab_test.variant_metrics["variant_1"].sample_count = 10
        ab_test.variant_metrics["variant_2"].sample_count = 10
        assert ab_test._check_statistical_significance() is True
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        ab_test = PromptVariantABTest("test_001", ["variant_1", "variant_2"], min_samples=10)
        
        # Set up metrics
        metrics1 = VariantMetrics(variant_name="variant_1")
        metrics1.sample_count = 10
        metrics1.avg_confidence = 0.9
        metrics1.execution_success_rate = 0.95
        metrics1.avg_tokens_per_scenario = 1000
        
        metrics2 = VariantMetrics(variant_name="variant_2")
        metrics2.sample_count = 5  # Insufficient
        metrics2.avg_confidence = 0.8
        metrics2.execution_success_rate = 0.6  # Low success rate
        metrics2.avg_tokens_per_scenario = 2500  # High tokens
        
        ab_test.variant_metrics = {
            "variant_1": metrics1,
            "variant_2": metrics2
        }
        
        recommendations = ab_test._generate_recommendations("variant_1", 0.85)
        
        assert len(recommendations) > 0
        assert any("variant_1" in r for r in recommendations)  # Should recommend winner
        assert any("variant_2" in r for r in recommendations)  # Should mention issues


class TestABTestResult:
    """Test ABTestResult class"""
    
    def test_ab_test_result_to_dict(self):
        """Test conversion to dictionary"""
        metrics = VariantMetrics(variant_name="variant_1")
        metrics.sample_count = 10
        metrics.avg_confidence = 0.9
        metrics.execution_success_rate = 0.85
        
        result = ABTestResult(
            test_id="test_001",
            test_name="Test",
            variants_tested=["variant_1"],
            start_time=datetime.now(timezone.utc),
            variant_metrics={"variant_1": metrics},
            winner="variant_1",
            winner_score=0.85
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["test_id"] == "test_001"
        assert result_dict["winner"] == "variant_1"
        assert "variant_metrics" in result_dict
        assert "variant_1" in result_dict["variant_metrics"]


class TestEvolutionAgentABTestIntegration:
    """Test EvolutionAgent A/B test integration"""
    
    @pytest.mark.asyncio
    async def test_evolution_agent_run_ab_test(self, mock_evolution_agent, sample_scenarios):
        """Test EvolutionAgent.run_ab_test method"""
        from agents.evolution_agent import EvolutionAgent
        from unittest.mock import MagicMock
        
        # Create real EvolutionAgent instance
        message_queue = MagicMock()
        agent = EvolutionAgent(
            agent_id="test_agent",
            agent_type="evolution",
            priority=5,
            message_queue=message_queue,
            config={"use_llm": False, "cache_enabled": False}
        )
        
        # Mock execute_task to avoid actual LLM calls
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.confidence = 0.9
        mock_result.execution_time_seconds = 2.0
        mock_result.metadata = {"token_usage": 500}
        mock_result.result = {
            "test_cases": [{
                "steps": ["Navigate to page", "Click button"]
            }],
            "cache_hits": 0,
            "cache_misses": 1
        }
        
        agent.execute_task = AsyncMock(return_value=mock_result)
        
        # Run A/B test
        result = await agent.run_ab_test(
            scenarios=sample_scenarios,
            variant_names=["variant_1", "variant_2"],
            min_samples=1
        )
        
        assert "test_id" in result
        assert "winner" in result
        assert "variant_metrics" in result
        assert len(result["variants_tested"]) == 2

