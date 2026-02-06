"""
Integration test for A/B Testing Framework

This test demonstrates how to use the A/B testing framework to compare
the 3 prompt variants (variant_1, variant_2, variant_3) in EvolutionAgent.

What this tests:
1. A/B testing framework can run tests on multiple variants
2. Metrics are collected correctly (tokens, confidence, quality)
3. Winner is determined based on composite scores
4. Results are meaningful and actionable

This is DIFFERENT from test_four_agent_e2e_real.py:
- test_four_agent_e2e_real.py: Tests the complete 4-agent workflow (uses 1 variant)
- This test: Tests A/B comparison of 3 variants on the same scenarios
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Load environment variables
env_path = backend_path / '.env'
load_dotenv(dotenv_path=env_path)

from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext


@pytest.fixture
def mock_message_queue():
    """Mock message queue"""
    class MockMessageQueue:
        async def publish(self, *args, **kwargs):
            pass
        async def subscribe(self, *args, **kwargs):
            pass
    return MockMessageQueue()


@pytest.fixture
def evolution_agent_with_llm(mock_message_queue):
    """EvolutionAgent with LLM enabled for A/B testing"""
    mock_llm_client = MagicMock()
    mock_llm_client.enabled = True
    mock_llm_client.deployment = "ChatGPT-UAT"
    mock_llm_client.client = MagicMock()
    mock_llm_client.client.chat = MagicMock()
    mock_llm_client.client.chat.completions = MagicMock()
    
    config = {
        "use_llm": True,
        "cache_enabled": False  # Disable cache for fair A/B comparison
    }
    
    with patch('llm.azure_client.get_azure_client', return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="ab_test_evolution_agent",
            agent_type="evolution",
            priority=5,
            message_queue=mock_message_queue,
            config=config
        )
        agent.llm_client = mock_llm_client
        yield agent


@pytest.fixture
def sample_scenarios_for_ab_test():
    """Sample BDD scenarios for A/B testing"""
    return [
        {
            "scenario_id": "REQ-F-001",
            "title": "User Login - Happy Path",
            "given": "User is on login page",
            "when": "User enters valid email and password, clicks Login button",
            "then": "User is redirected to dashboard and session is created",
            "priority": "critical",
            "scenario_type": "functional",
            "page_context": {"url": "https://example.com/login"}
        },
        {
            "scenario_id": "REQ-F-002",
            "title": "Search Product",
            "given": "User is on homepage",
            "when": "User enters search term in search box, clicks Search button",
            "then": "Search results are displayed with matching products",
            "priority": "high",
            "scenario_type": "functional",
            "page_context": {"url": "https://example.com"}
        },
        {
            "scenario_id": "REQ-F-003",
            "title": "Add to Cart",
            "given": "User is viewing a product page",
            "when": "User clicks Add to Cart button",
            "then": "Product is added to cart and cart count increases",
            "priority": "high",
            "scenario_type": "functional",
            "page_context": {"url": "https://example.com/product/123"}
        }
    ]


class TestPromptVariantABTestIntegration:
    """Integration tests for A/B testing framework"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_ab_test_compares_variants(
        self,
        evolution_agent_with_llm,
        sample_scenarios_for_ab_test
    ):
        """
        Test that A/B testing framework can compare all 3 variants.
        
        This test:
        1. Runs the same scenarios through all 3 prompt variants
        2. Collects metrics for each variant
        3. Determines a winner based on composite scores
        4. Verifies results are meaningful
        """
        import json
        
        # Mock LLM responses for each variant
        # Variant 1: Detailed response
        variant_1_response = json.dumps({
            "steps": [
                "Navigate to https://example.com/login",
                "Enter email: test@example.com",
                "Enter password: password123",
                "Click Login button",
                "Verify URL contains /dashboard",
                "Verify session cookie is set"
            ]
        })
        
        # Variant 2: Concise response
        variant_2_response = json.dumps({
            "steps": [
                "Navigate to https://example.com/login",
                "Enter credentials and click Login",
                "Verify redirect to dashboard"
            ]
        })
        
        # Variant 3: Pattern-based response
        variant_3_response = json.dumps({
            "steps": [
                "Navigate to login page",
                "Fill login form (email, password)",
                "Submit form",
                "Verify successful login"
            ]
        })
        
        # Create mock responses that return different results per variant
        def mock_llm_create(*args, **kwargs):
            # Get the prompt from messages
            messages = kwargs.get('messages', [])
            user_message = next((m for m in messages if m.get('role') == 'user'), {})
            prompt = user_message.get('content', '')
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            
            # Return different responses based on prompt characteristics
            if "Detailed" in prompt or "Variant 1" in prompt or len(prompt) > 1000:
                mock_response.choices[0].message.content = variant_1_response
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 800  # More tokens for detailed
            elif "Concise" in prompt or "Variant 2" in prompt:
                mock_response.choices[0].message.content = variant_2_response
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 400  # Fewer tokens for concise
            else:  # Variant 3
                mock_response.choices[0].message.content = variant_3_response
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 600  # Medium tokens
            
            return mock_response
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(side_effect=mock_llm_create)
        
        # Run A/B test
        result = await evolution_agent_with_llm.run_ab_test(
            scenarios=sample_scenarios_for_ab_test,
            variant_names=["variant_1", "variant_2", "variant_3"],
            min_samples=1  # Lower for testing
        )
        
        # Verify A/B test completed
        assert "test_id" in result
        assert "variants_tested" in result
        assert len(result["variants_tested"]) == 3
        assert "variant_metrics" in result
        
        # Verify metrics were collected for each variant
        for variant_name in ["variant_1", "variant_2", "variant_3"]:
            assert variant_name in result["variant_metrics"]
            metrics = result["variant_metrics"][variant_name]
            assert "sample_count" in metrics
            assert metrics["sample_count"] > 0
            assert "avg_confidence" in metrics
            assert "avg_tokens_per_scenario" in metrics
        
        # Verify winner was determined
        if result.get("winner"):
            assert result["winner"] in ["variant_1", "variant_2", "variant_3"]
            assert result["winner_score"] > 0.0
        
        # Verify recommendations were generated
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        
        print(f"\n{'='*80}")
        print("A/B Test Results:")
        print(f"{'='*80}")
        print(f"Test ID: {result['test_id']}")
        print(f"Variants Tested: {', '.join(result['variants_tested'])}")
        print(f"Total Scenarios: {result['total_scenarios']}")
        print(f"\nVariant Metrics:")
        for variant_name, metrics in result["variant_metrics"].items():
            print(f"  {variant_name}:")
            print(f"    Samples: {metrics['sample_count']}")
            print(f"    Avg Tokens: {metrics['avg_tokens_per_scenario']:.0f}")
            print(f"    Avg Confidence: {metrics['avg_confidence']:.2f}")
            print(f"    Composite Score: {metrics.get('composite_score', 'N/A')}")
        if result.get("winner"):
            print(f"\nWinner: {result['winner']} (score: {result['winner_score']:.4f})")
        print(f"\nRecommendations:")
        for rec in result["recommendations"]:
            print(f"  - {rec}")
        print(f"{'='*80}\n")
    
    @pytest.mark.asyncio
    async def test_ab_test_with_execution_results(
        self,
        evolution_agent_with_llm,
        sample_scenarios_for_ab_test
    ):
        """
        Test A/B testing with execution results to compare real-world performance.
        
        This simulates having execution results from actual test runs,
        which allows the A/B test to factor in execution success rates.
        """
        import json
        
        # Mock LLM responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "steps": ["Navigate to page", "Click button", "Verify result"]
        })
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 500
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        # Simulate execution results (some variants perform better)
        execution_results = {
            "REQ-F-001": {"status": "passed", "execution_time": 2.5},
            "REQ-F-002": {"status": "passed", "execution_time": 1.8},
            "REQ-F-003": {"status": "failed", "execution_time": 3.0, "error": "Timeout"}
        }
        
        # Run A/B test with execution results
        result = await evolution_agent_with_llm.run_ab_test(
            scenarios=sample_scenarios_for_ab_test,
            variant_names=["variant_1", "variant_2"],
            min_samples=1,
            execution_results=execution_results
        )
        
        # Verify execution results were factored in
        assert "variant_metrics" in result
        # Note: Execution results distribution is simplified in current implementation
        # In a real scenario, we'd track which variant generated which test
    
    @pytest.mark.asyncio
    async def test_ab_test_winner_selection(
        self,
        evolution_agent_with_llm,
        sample_scenarios_for_ab_test
    ):
        """
        Test that A/B test correctly selects winner based on metrics.
        
        This verifies the composite scoring and winner selection logic.
        """
        import json
        
        # Create responses that will result in different scores
        def create_mock_response(variant_num):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            
            # Variant 1: High quality, high tokens
            if variant_num == 1:
                mock_response.choices[0].message.content = json.dumps({
                    "steps": [
                        "Navigate to https://example.com/login",
                        "Enter email: test@example.com",
                        "Enter password: password123",
                        "Click Login button",
                        "Verify URL contains /dashboard",
                        "Verify session cookie is set",
                        "Verify user menu is visible"
                    ]
                })
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 1000
            # Variant 2: Medium quality, medium tokens
            elif variant_num == 2:
                mock_response.choices[0].message.content = json.dumps({
                    "steps": [
                        "Navigate to https://example.com/login",
                        "Enter credentials and click Login",
                        "Verify redirect to dashboard"
                    ]
                })
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 500
            # Variant 3: Low quality, low tokens
            else:
                mock_response.choices[0].message.content = json.dumps({
                    "steps": ["Navigate to page", "Click button"]
                })
                mock_response.usage = MagicMock()
                mock_response.usage.total_tokens = 300
            
            return mock_response
        
        call_count = [0]
        def mock_llm_create(*args, **kwargs):
            call_count[0] += 1
            variant_num = ((call_count[0] - 1) // len(sample_scenarios_for_ab_test)) % 3 + 1
            return create_mock_response(variant_num)
        
        evolution_agent_with_llm.llm_client.client.chat.completions.create = MagicMock(side_effect=mock_llm_create)
        
        # Run A/B test
        result = await evolution_agent_with_llm.run_ab_test(
            scenarios=sample_scenarios_for_ab_test,
            variant_names=["variant_1", "variant_2", "variant_3"],
            min_samples=1
        )
        
        # Verify winner was selected
        assert result.get("winner") is not None
        assert result["winner"] in ["variant_1", "variant_2", "variant_3"]
        assert result["winner_score"] > 0.0
        
        # Verify winner has best composite score
        winner_metrics = result["variant_metrics"][result["winner"]]
        winner_score = winner_metrics.get("composite_score", 0)
        
        for variant_name, metrics in result["variant_metrics"].items():
            if variant_name != result["winner"]:
                other_score = metrics.get("composite_score", 0)
                # Winner should have equal or better score
                assert winner_score >= other_score - 0.01, \
                    f"Winner {result['winner']} should have best score, but {variant_name} has {other_score} vs {winner_score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

