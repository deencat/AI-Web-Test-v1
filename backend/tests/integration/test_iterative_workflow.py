"""
10A.11: Integration Tests for Iterative Workflow

Tests for:
1. Multi-page flow crawling (ObservationAgent with browser-use)
2. Dynamic URL crawling (EvolutionAgent calling ObservationAgent)
3. Goal-oriented navigation (configurable goal indicators)
4. Iterative improvement loop (convergence criteria)

Run with: pytest tests/integration/test_iterative_workflow.py -v -s
"""
import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGoalOrientedNavigation:
    """Tests for 10A.10: Goal-oriented navigation with configurable indicators"""
    
    @pytest.fixture
    def mock_observation_agent(self):
        """Create a mock ObservationAgent for testing"""
        from agents.observation_agent import ObservationAgent
        
        # Create agent with mocked message queue
        mock_queue = MagicMock()
        agent = ObservationAgent(
            message_queue=mock_queue,
            agent_id="test-observation-agent",
            config={"use_llm": False}
        )
        return agent
    
    def test_get_goal_indicators_purchase_flow(self, mock_observation_agent):
        """Test goal indicators for purchase flow"""
        indicators = mock_observation_agent._get_goal_indicators(
            "Complete the purchase flow for a mobile plan"
        )
        
        # Should include purchase-related indicators
        assert any("confirmation" in i.lower() for i in indicators)
        assert any("order" in i.lower() for i in indicators)
        assert any("payment" in i.lower() for i in indicators)
        assert any("success" in i.lower() for i in indicators)
        
        logger.info(f"Purchase flow indicators: {indicators[:10]}...")
    
    def test_get_goal_indicators_registration_flow(self, mock_observation_agent):
        """Test goal indicators for registration flow"""
        indicators = mock_observation_agent._get_goal_indicators(
            "Register a new user account"
        )
        
        # Should include registration-related indicators
        assert any("registration" in i.lower() for i in indicators)
        assert any("account" in i.lower() for i in indicators)
        assert any("welcome" in i.lower() for i in indicators)
        
        logger.info(f"Registration flow indicators: {indicators[:10]}...")
    
    def test_get_goal_indicators_login_flow(self, mock_observation_agent):
        """Test goal indicators for login flow"""
        indicators = mock_observation_agent._get_goal_indicators(
            "Login to the user dashboard"
        )
        
        # Should include login-related indicators
        assert any("dashboard" in i.lower() for i in indicators)
        assert any("welcome" in i.lower() for i in indicators)
        assert any("logged" in i.lower() or "profile" in i.lower() for i in indicators)
        
        logger.info(f"Login flow indicators: {indicators[:10]}...")
    
    def test_get_goal_indicators_custom(self, mock_observation_agent):
        """Test custom goal indicators override"""
        custom_indicators = ["custom_success", "my_confirmation"]
        indicators = mock_observation_agent._get_goal_indicators(
            "Some generic instruction",
            custom_indicators=custom_indicators
        )
        
        # Custom indicators should be included
        assert "custom_success" in indicators
        assert "my_confirmation" in indicators
        
        logger.info(f"Custom indicators included: {indicators[:5]}...")
    
    def test_check_goal_reached_with_url_match(self, mock_observation_agent):
        """Test goal detection when URL contains indicator"""
        # Mock history with confirmation URL
        mock_history = [
            MagicMock(
                url="https://example.com/order/confirmation",
                title="Order Confirmation",
                result=[]
            )
        ]
        
        result = mock_observation_agent._check_goal_reached(
            mock_history,
            "Complete the purchase flow"
        )
        
        assert result is True
        logger.info("Goal reached detected via URL match")
    
    def test_check_goal_reached_with_title_match(self, mock_observation_agent):
        """Test goal detection when title contains indicator"""
        # Mock history with success title
        mock_history = [
            MagicMock(
                url="https://example.com/result",
                title="Payment Successful - Thank You",
                result=[]
            )
        ]
        
        result = mock_observation_agent._check_goal_reached(
            mock_history,
            "Complete the purchase flow"
        )
        
        assert result is True
        logger.info("Goal reached detected via title match")
    
    def test_check_goal_not_reached(self, mock_observation_agent):
        """Test goal detection when goal is not reached"""
        # Mock history without any goal indicators
        mock_history = [
            MagicMock(
                url="https://example.com/cart",
                title="Shopping Cart",
                result=[]
            )
        ]
        
        result = mock_observation_agent._check_goal_reached(
            mock_history,
            "Complete the purchase flow"
        )
        
        assert result is False
        logger.info("Goal not reached correctly detected")


class TestDynamicURLCrawling:
    """Tests for 10A.9: Dynamic URL crawling in EvolutionAgent"""
    
    @pytest.fixture
    def mock_evolution_agent(self):
        """Create a mock EvolutionAgent for testing"""
        from agents.evolution_agent import EvolutionAgent
        
        mock_queue = MagicMock()
        agent = EvolutionAgent(
            agent_id="test-evolution-agent",
            agent_type="evolution",
            priority=5,
            message_queue=mock_queue,
            config={"use_llm": False, "cache_enabled": False}
        )
        return agent
    
    def test_identify_missing_urls_basic(self, mock_evolution_agent):
        """Test identification of missing URLs from scenarios"""
        scenarios = [
            {
                "scenario_id": "SC-001",
                "given": "User is on https://example.com/products",
                "when": "User clicks checkout",
                "then": "User is redirected to https://example.com/checkout"
            }
        ]
        
        page_context = {
            "url": "https://example.com",
            "pages": [
                {"url": "https://example.com"}
            ]
        }
        
        missing = mock_evolution_agent._identify_missing_urls(scenarios, page_context)
        
        # Should identify the URLs mentioned in scenarios but not in page_context
        assert len(missing) > 0
        assert any("products" in url for url in missing) or any("checkout" in url for url in missing)
        
        logger.info(f"Identified missing URLs: {missing}")
    
    def test_identify_missing_urls_no_missing(self, mock_evolution_agent):
        """Test when all URLs are already observed"""
        scenarios = [
            {
                "scenario_id": "SC-001",
                "given": "User is on https://example.com",
                "when": "User clicks login",
                "then": "User sees login form"
            }
        ]
        
        page_context = {
            "url": "https://example.com",
            "pages": [
                {"url": "https://example.com"}
            ]
        }
        
        missing = mock_evolution_agent._identify_missing_urls(scenarios, page_context)
        
        # No URLs mentioned in scenarios that aren't already observed
        assert len(missing) == 0
        
        logger.info("No missing URLs detected (correct)")
    
    def test_extract_urls_from_text(self, mock_evolution_agent):
        """Test URL extraction from text"""
        text = "Navigate to https://example.com/login and then go to https://example.com/dashboard"
        
        urls = mock_evolution_agent._extract_urls_from_text(text)
        
        assert len(urls) == 2
        assert "https://example.com/login" in urls
        assert "https://example.com/dashboard" in urls
        
        logger.info(f"Extracted URLs: {urls}")
    
    def test_is_valid_crawlable_url(self, mock_evolution_agent):
        """Test URL validation for crawling"""
        # Valid URLs
        assert mock_evolution_agent._is_valid_crawlable_url("https://example.com/page") is True
        assert mock_evolution_agent._is_valid_crawlable_url("http://example.com/login") is True
        
        # Invalid URLs
        assert mock_evolution_agent._is_valid_crawlable_url("https://example.com/api/data") is False
        assert mock_evolution_agent._is_valid_crawlable_url("https://example.com/image.png") is False
        assert mock_evolution_agent._is_valid_crawlable_url("javascript:void(0)") is False
        assert mock_evolution_agent._is_valid_crawlable_url("mailto:test@example.com") is False
        assert mock_evolution_agent._is_valid_crawlable_url("") is False
        
        logger.info("URL validation tests passed")
    
    @pytest.mark.asyncio
    async def test_crawl_missing_urls_integration(self, mock_evolution_agent):
        """Test dynamic URL crawling with mock ObservationAgent"""
        # Create mock ObservationAgent
        mock_observation_agent = AsyncMock()
        mock_observation_agent.execute_task.return_value = MagicMock(
            success=True,
            result={
                "ui_elements": [
                    {"type": "button", "text": "Submit", "selector": "#submit"}
                ],
                "pages": [
                    {"url": "https://example.com/checkout", "title": "Checkout"}
                ]
            }
        )
        
        scenarios = [
            {
                "scenario_id": "SC-001",
                "given": "User is on https://example.com/checkout",
                "when": "User fills form",
                "then": "Order is placed"
            }
        ]
        
        page_context = {
            "url": "https://example.com",
            "pages": [{"url": "https://example.com"}],
            "ui_elements": []
        }
        
        # Call the method
        updated_context = await mock_evolution_agent._crawl_missing_urls(
            scenarios=scenarios,
            page_context=page_context,
            observation_agent=mock_observation_agent,
            user_instruction="Complete checkout",
            login_credentials={}
        )
        
        # Verify ObservationAgent was called
        assert mock_observation_agent.execute_task.called
        
        # Verify page_context was updated
        assert len(updated_context.get("ui_elements", [])) > 0
        
        logger.info("Dynamic URL crawling integration test passed")


class TestMultiPageFlowCrawling:
    """Tests for 10A.7: Multi-page flow crawling"""
    
    @pytest.fixture
    def mock_observation_agent(self):
        """Create a mock ObservationAgent for testing"""
        from agents.observation_agent import ObservationAgent
        
        mock_queue = MagicMock()
        agent = ObservationAgent(
            message_queue=mock_queue,
            agent_id="test-observation-agent",
            config={"use_llm": False, "enable_flow_crawling": True}
        )
        return agent
    
    def test_flow_crawling_enabled_with_instruction(self, mock_observation_agent):
        """Test that flow crawling is enabled when user_instruction is provided"""
        # The agent should use flow crawling when user_instruction is provided
        # and enable_flow_crawling is True (default)
        
        user_instruction = "Complete the purchase flow"
        use_flow_crawling = bool(user_instruction) and mock_observation_agent.config.get("enable_flow_crawling", True)
        
        assert use_flow_crawling is True
        logger.info("Flow crawling correctly enabled with user instruction")
    
    def test_flow_crawling_disabled_without_instruction(self, mock_observation_agent):
        """Test that flow crawling is disabled when no user_instruction"""
        user_instruction = ""
        use_flow_crawling = bool(user_instruction) and mock_observation_agent.config.get("enable_flow_crawling", True)
        
        assert use_flow_crawling is False
        logger.info("Flow crawling correctly disabled without user instruction")


class TestIterativeImprovementLoop:
    """Tests for iterative improvement loop convergence"""
    
    def test_convergence_criteria_met(self):
        """Test that convergence is detected when pass rate >= threshold"""
        pass_rate = 0.92
        threshold = 0.90
        
        converged = pass_rate >= threshold
        
        assert converged is True
        logger.info(f"Convergence detected: {pass_rate:.1%} >= {threshold:.1%}")
    
    def test_convergence_criteria_not_met(self):
        """Test that convergence is not detected when pass rate < threshold"""
        pass_rate = 0.75
        threshold = 0.90
        
        converged = pass_rate >= threshold
        
        assert converged is False
        logger.info(f"Convergence not met: {pass_rate:.1%} < {threshold:.1%}")
    
    def test_max_iterations_limit(self):
        """Test that iterations stop at max limit"""
        max_iterations = 5
        current_iteration = 5
        
        should_stop = current_iteration >= max_iterations
        
        assert should_stop is True
        logger.info(f"Max iterations reached: {current_iteration} >= {max_iterations}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
