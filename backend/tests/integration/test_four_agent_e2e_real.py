"""
REAL 4-Agent E2E Test: ObservationAgent → RequirementsAgent → AnalysisAgent → EvolutionAgent

This is a TRUE end-to-end test that:
1. Actually crawls a real web page (ObservationAgent with Playwright)
2. Uses real LLM calls (RequirementsAgent, AnalysisAgent, EvolutionAgent with Azure OpenAI)
3. Executes real test scenarios (AnalysisAgent with real-time execution enabled)
4. Generates test steps and stores in database (EvolutionAgent with LLM)

Expected execution time: 45-155 seconds (depending on LLM response times and execution)

NOTE: For real-time logging output, you MUST run with the -s flag:
    python -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
    
The -s flag disables pytest's output capturing, allowing logs to appear in real-time.
The -u flag forces unbuffered Python output so logs appear immediately.
Without -s, pytest captures all output and only shows it at the end!
"""
import pytest
import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output for real-time logging
# Set PYTHONUNBUFFERED environment variable
os.environ['PYTHONUNBUFFERED'] = '1'

# Try to reconfigure stdout/stderr for line buffering
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except AttributeError:
    # Python < 3.7 or reconfigure not available
    pass

# Custom print function that flushes immediately and writes to log file
_log_file_handle = None  # Will be set after log_file is created

def print_flush(*args, **kwargs):
    """Print with immediate flush and also write to log file"""
    # Print to stdout (will be captured by pytest if -s is not used)
    print(*args, **kwargs)
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Also write to log file directly (so print statements are saved even if pytest captures stdout)
    global _log_file_handle
    if _log_file_handle is None and 'log_file' in globals():
        try:
            _log_file_handle = open(log_file, 'a', encoding='utf-8')
        except:
            pass  # If file can't be opened, just skip file logging
    
    if _log_file_handle:
        try:
            # Format the message (remove newlines from args, add them back)
            message = ' '.join(str(arg) for arg in args)
            if kwargs.get('end', '\n') == '\n':
                message += '\n'
            _log_file_handle.write(message)
            _log_file_handle.flush()
        except:
            pass  # If write fails, continue without file logging

# Configure logging - DEBUG level for agents to show detailed progress
# Use StreamHandler with immediate flush
class FlushingStreamHandler(logging.StreamHandler):
    """StreamHandler that flushes after each emit"""
    def emit(self, record):
        super().emit(record)
        self.flush()

class FlushingFileHandler(logging.FileHandler):
    """FileHandler that flushes after each emit"""
    def emit(self, record):
        super().emit(record)
        self.flush()

# Get backend path for log directory (before using it)
backend_path = Path(__file__).parent.parent.parent

# Create log file with timestamp
from datetime import datetime
log_dir = backend_path / "logs"
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"test_four_agent_e2e_{timestamp}.log"

# Console handler (stdout)
console_handler = FlushingStreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                               datefmt='%Y-%m-%d %H:%M:%S'))

# File handler (write to file)
file_handler = FlushingFileHandler(str(log_file), mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                            datefmt='%Y-%m-%d %H:%M:%S'))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[console_handler, file_handler],
    force=True  # Override any existing configuration
)

# Log file location info
print(f"Logs are being saved to: {log_file}", file=sys.stderr)
sys.stderr.flush()

# Initialize log file handle for print_flush
try:
    _log_file_handle = open(log_file, 'a', encoding='utf-8')
except:
    _log_file_handle = None

# Set specific loggers to DEBUG (agents, services) for detailed output
logging.getLogger('agents').setLevel(logging.DEBUG)
logging.getLogger('agents.observation_agent').setLevel(logging.DEBUG)
logging.getLogger('agents.requirements_agent').setLevel(logging.DEBUG)
logging.getLogger('agents.analysis_agent').setLevel(logging.DEBUG)
logging.getLogger('agents.evolution_agent').setLevel(logging.DEBUG)
logging.getLogger('llm').setLevel(logging.INFO)
logging.getLogger('app.services').setLevel(logging.INFO)
logging.getLogger('app.crud').setLevel(logging.INFO)

# Reduce noise from HTTP libraries (set to WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Load environment variables from .env file
# This must be done BEFORE importing agents that use Azure OpenAI
# (backend_path already defined above for log file)
env_path = backend_path / '.env'
load_dotenv(dotenv_path=env_path)

# Add backend to path
sys.path.insert(0, str(backend_path))

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext

# Get logger for this test
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_message_queue():
    """Mock message queue for all agents"""
    class MockMessageQueue:
        async def publish(self, *args, **kwargs):
            pass
        async def subscribe(self, *args, **kwargs):
            pass
    
    return MockMessageQueue()


@pytest.fixture
def observation_agent_real(mock_message_queue):
    """Create ObservationAgent instance with REAL web crawling enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real observation
        "max_depth": 1,
        "max_pages": 1
    }
    return ObservationAgent(
        message_queue=mock_message_queue,
        agent_id="e2e_test_observation_agent",
        priority=8,
        config=config
    )


@pytest.fixture
def requirements_agent_real(mock_message_queue):
    """Create RequirementsAgent instance with REAL LLM enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real scenario generation
        "cache_enabled": False  # DISABLE caching for real E2E test
    }
    return RequirementsAgent(
        agent_id="e2e_test_requirements_agent",
        agent_type="requirements",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def db_session():
    """Create a test database session for real execution"""
    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        yield db
        db.close()
    except Exception as e:
        # If database is not available, return None (will use stub mode)
        print_flush(f"Warning: Database not available: {e}. Using stub mode.")
        yield None


@pytest.fixture
def analysis_agent_real(mock_message_queue, db_session):
    """Create AnalysisAgent instance with REAL LLM and real-time execution enabled"""
    config = {
        "use_llm": True,  # ENABLE LLM for real risk analysis
        "db": db_session,  # Use database session if available
        "enable_realtime_execution": True,  # ENABLE real-time execution
        "execution_rpn_threshold": 0,  # Lower threshold for testing (execute top scenarios)
        "headless_browser": False,  # Show browser during execution (set to True to hide)
        "cache_enabled": False  # DISABLE caching for real E2E test
    }
    return AnalysisAgent(
        agent_id="e2e_test_analysis_agent",
        agent_type="analysis",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


@pytest.fixture
def evolution_agent_real(mock_message_queue, db_session):
    """Create EvolutionAgent instance with REAL LLM enabled and database session"""
    config = {
        "use_llm": True,  # ENABLE LLM for real test steps generation
        "cache_enabled": False,  # DISABLE caching for real E2E test
        "db": db_session  # Use database session if available
    }
    return EvolutionAgent(
        agent_id="e2e_test_evolution_agent",
        agent_type="evolution",
        priority=5,
        message_queue=mock_message_queue,
        config=config
    )


class TestFourAgentE2EReal:
    """REAL 4-Agent E2E Test with actual web crawling, LLM calls, and execution"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test (requires real web crawling, LLM calls, and execution)
    async def test_complete_4_agent_workflow_real(
        self,
        observation_agent_real,
        requirements_agent_real,
        analysis_agent_real,
        evolution_agent_real,
        db_session
    ):
        """
        REAL 4-Agent E2E Test: Complete workflow with actual execution
        
        This test:
        1. Actually crawls the Three HK 5G Broadband page (ObservationAgent)
        2. Uses real LLM to generate BDD scenarios (RequirementsAgent)
        3. Uses real LLM to analyze risk and executes real test scenarios (AnalysisAgent)
        4. Uses real LLM to generate test steps and stores in database (EvolutionAgent)
        
        Expected duration: 45-155 seconds
        
        User Instruction Support:
        - Set USER_INSTRUCTION environment variable to provide specific test requirement
        - Example: USER_INSTRUCTION="Test purchase flow for '5G寬頻數據無限任用' plan" pytest ...
        - If not set, RequirementsAgent will generate generic scenarios
        """
        target_url = "https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc"
        conversation_id = "e2e-4agent-real-001"
        
        # Get user instruction from environment variable (optional)
        user_instruction = os.getenv("USER_INSTRUCTION", "")
        if user_instruction:
            print_flush(f"\n[INFO] User instruction provided: '{user_instruction}'")
            print_flush(f"        RequirementsAgent will prioritize scenarios matching this requirement")
        
        # Get login credentials from environment variables (optional)
        login_email = os.getenv("LOGIN_EMAIL", "")
        login_password = os.getenv("LOGIN_PASSWORD", "")
        login_credentials = {}
        if login_email and login_password:
            login_credentials = {
                "email": login_email,
                "password": login_password
            }
            print_flush(f"\n[INFO] Login credentials provided: email='{login_email[:10]}...'")
            print_flush(f"        Test steps will include login before purchase flow")
        
        # Force immediate output - flush everything
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Print to both stdout and stderr to maximize visibility
        # (pytest might capture one but not the other)
        print_flush(f"\n{'='*80}")
        print_flush(f"REAL 4-Agent E2E Test: Complete Workflow")
        print_flush(f"URL: {target_url}")
        print_flush(f"{'='*80}\n")
        print_flush("=" * 80)
        print_flush("IMPORTANT: To see logs in REAL-TIME, you MUST run with -s flag:")
        print_flush("  python -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s")
        print_flush("=" * 80)
        print_flush("Without -s, pytest captures all output and only shows it at the end!")
        print_flush("=" * 80)
        print_flush(f"\nAll logs are being saved to: {log_file}")
        print_flush("You can view the log file in real-time with: tail -f " + str(log_file))
        print_flush("=" * 80 + "\n")
        
        # Also log it
        logger.info("="*80)
        logger.info("REAL 4-Agent E2E Test: Complete Workflow")
        logger.info(f"URL: {target_url}")
        logger.info("="*80)
        logger.warning("If you don't see logs in real-time, run with: pytest -v -s")
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Step 1: ObservationAgent - Observe the page
        logger.info("="*80)
        logger.info("Step 1: Starting ObservationAgent - Observing page...")
        logger.info("="*80)
        print_flush("\n" + "="*80)
        print_flush("Step 1: Observing page with ObservationAgent...")
        print_flush("="*80)
        observation_task = TaskContext(
            conversation_id=conversation_id,
            task_id="obs-task-real-001",
            task_type="ui_element_extraction",
            payload={"url": target_url, "max_depth": 1}
        )
        
        logger.info(f"ObservationAgent: Starting page observation for {target_url}")
        logger.debug(f"ObservationAgent task payload keys: {list(observation_task.payload.keys())}")
        print_flush(f"[INFO] ObservationAgent: Crawling {target_url}...")
        print_flush(f"        Observation stages:")
        print_flush(f"        1. Launching browser (Playwright)")
        print_flush(f"        2. Loading page and extracting UI elements")
        print_flush(f"        3. LLM enhancement (if enabled) for semantic understanding")
        print_flush(f"        4. Merging Playwright + LLM results\n")
        
        observation_result = await observation_agent_real.execute_task(observation_task)
        
        logger.info(f"ObservationAgent: COMPLETED - success={observation_result.success}, "
                   f"confidence={observation_result.confidence:.2f}, "
                   f"execution_time={observation_result.execution_time_seconds:.2f}s, "
                   f"ui_elements={len(observation_result.result.get('ui_elements', []))}")
        
        # Verify observation succeeded
        assert observation_result.success is True, f"Observation failed: {observation_result.error}"
        ui_elements = observation_result.result.get('ui_elements', [])
        ui_elements_count = len(ui_elements)
        logger.info(f"ObservationAgent found {ui_elements_count} UI elements")
        print_flush(f"[OK] Observation complete: {ui_elements_count} UI elements found")
        assert ui_elements_count > 0, "No UI elements found - observation failed"
        
        # Show element breakdown
        element_types = {}
        for element in ui_elements:
            elem_type = element.get('type', 'unknown')
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print_flush(f"\n  Element Breakdown:")
        for elem_type, count in sorted(element_types.items(), key=lambda x: x[1], reverse=True):
            print_flush(f"    - {elem_type}: {count} elements")
        
        # Show page structure
        page_structure = observation_result.result.get('page_structure', {})
        page_context = observation_result.result.get('page_context', {})
        if page_structure:
            print_flush(f"\n  Page Structure:")
            print_flush(f"    - URL: {page_structure.get('url', 'N/A')}")
            print_flush(f"    - Title: {page_structure.get('title', 'N/A')[:60]}")
            forms_count = len(page_structure.get('forms', []))
            if forms_count > 0:
                print_flush(f"    - Forms: {forms_count} forms found")
        
        if page_context:
            print_flush(f"\n  Page Context:")
            print_flush(f"    - Page Type: {page_context.get('page_type', 'unknown')}")
            print_flush(f"    - Framework: {page_context.get('framework', 'unknown')}")
            print_flush(f"    - Complexity: {page_context.get('complexity', 'unknown')}")
        
        # Show LLM analysis if available
        llm_analysis = observation_result.result.get('llm_analysis', {})
        if llm_analysis:
            enhanced_count = len(llm_analysis.get('enhanced_elements', []))
            if enhanced_count > 0:
                print_flush(f"\n  LLM Enhancement:")
                print_flush(f"    - Enhanced elements: {enhanced_count} additional elements found by LLM")
                missed_elements = llm_analysis.get('missed_by_playwright', [])
                if missed_elements:
                    print_flush(f"    - Missed by Playwright: {len(missed_elements)} elements")
        
        # Extract observation data
        observation_data = {
            "ui_elements": observation_result.result.get("ui_elements", []),
            "page_structure": observation_result.result.get("page_structure", {}),
            "page_context": observation_result.result.get("page_context", {})
        }
        
        # Ensure URL is in page_context for EvolutionAgent
        if "url" not in observation_data["page_context"]:
            observation_data["page_context"]["url"] = target_url
        
        # Step 2: RequirementsAgent - Generate test scenarios
        logger.info("="*80)
        logger.info("Step 2: Starting RequirementsAgent - Generating test scenarios...")
        logger.info("="*80)
        print_flush("\n" + "="*80)
        print_flush("Step 2: Generating test scenarios with RequirementsAgent...")
        print_flush("="*80)
        # Build payload with optional user instruction
        requirements_payload = {**observation_data}
        if user_instruction:
            requirements_payload["user_instruction"] = user_instruction
            logger.info(f"RequirementsAgent: User instruction provided: '{user_instruction}'")
        
        requirements_task = TaskContext(
            conversation_id=conversation_id,
            task_id="req-task-real-001",
            task_type="requirement_extraction",
            payload=requirements_payload
        )
        
        logger.info(f"RequirementsAgent: Starting scenario generation from {len(observation_data.get('ui_elements', []))} UI elements")
        logger.debug(f"RequirementsAgent task payload keys: {list(requirements_task.payload.keys())}")
        print_flush(f"[INFO] RequirementsAgent: Generating BDD scenarios from {len(observation_data.get('ui_elements', []))} UI elements...")
        if user_instruction:
            print_flush(f"        User instruction: '{user_instruction}'")
            print_flush(f"        Will prioritize scenarios matching this requirement")
        print_flush(f"        Scenario generation stages:")
        print_flush(f"        1. Grouping elements by page/component (Page Object Model)")
        print_flush(f"        2. Mapping user journeys (multi-step flows)")
        print_flush(f"        3. Generating functional scenarios (LLM + patterns)")
        if user_instruction:
            print_flush(f"           • Prioritizing scenarios matching: '{user_instruction}'")
        print_flush(f"        4. Generating accessibility scenarios (WCAG 2.1)")
        print_flush(f"        5. Generating security scenarios (OWASP Top 10)")
        print_flush(f"        6. Generating edge case scenarios (boundary tests)")
        print_flush(f"        7. Extracting test data and calculating coverage\n")
        
        requirements_result = await requirements_agent_real.execute_task(requirements_task)
        
        scenarios_count = len(requirements_result.result.get("scenarios", []))
        logger.info(f"RequirementsAgent: COMPLETED - success={requirements_result.success}, "
                   f"confidence={requirements_result.confidence:.2f}, "
                   f"execution_time={requirements_result.execution_time_seconds:.2f}s, "
                   f"scenarios_generated={scenarios_count}")
        
        # Verify requirements generation succeeded
        assert requirements_result.success is True, f"Requirements generation failed: {requirements_result.error}"
        scenarios = requirements_result.result.get("scenarios", [])
        logger.info(f"RequirementsAgent generated {len(scenarios)} BDD scenarios")
        print_flush(f"[OK] Requirements complete: {len(scenarios)} BDD scenarios generated")
        assert len(scenarios) > 0, "No scenarios generated"
        
        # Check for scenarios matching user instruction (if provided)
        matching_scenarios = []
        if user_instruction:
            instruction_keywords = user_instruction.lower().split()
            for scenario in scenarios:
                title_lower = scenario.get("title", "").lower()
                when_lower = scenario.get("when", "").lower()
                matches = sum(1 for keyword in instruction_keywords 
                             if keyword in title_lower or keyword in when_lower)
                # Also check for specific plan name (Chinese characters)
                if "5g寬頻數據無限任用" in title_lower or "5g寬頻數據無限任用" in when_lower:
                    matches += 3  # Strong match
                if matches >= 2:  # At least 2 keywords match
                    matching_scenarios.append(scenario)
            
            if matching_scenarios:
                print_flush(f"\n  [USER INSTRUCTION MATCH] Found {len(matching_scenarios)} scenario(s) matching: '{user_instruction}'")
                for idx, match_scenario in enumerate(matching_scenarios[:3], 1):
                    print_flush(f"    [{idx}] {match_scenario.get('title')} (Priority: {match_scenario.get('priority')})")
                    if match_scenario.get('tags') and 'user-requirement' in match_scenario.get('tags', []):
                        print_flush(f"        Tagged with: user-requirement")
            else:
                print_flush(f"\n  [WARNING] No scenarios found matching user instruction: '{user_instruction}'")
                print_flush(f"           This may indicate the instruction doesn't match available UI elements")
        
        # Show scenarios by type
        scenarios_by_type = {}
        for scenario in scenarios:
            scenario_type = scenario.get('scenario_type', 'unknown')
            scenarios_by_type[scenario_type] = scenarios_by_type.get(scenario_type, 0) + 1
        
        print_flush(f"\n  Scenarios by Type:")
        for scenario_type, count in sorted(scenarios_by_type.items(), key=lambda x: x[1], reverse=True):
            print_flush(f"    - {scenario_type}: {count} scenarios")
        
        # Show scenarios by priority
        scenarios_by_priority = {}
        for scenario in scenarios:
            priority = scenario.get('priority', 'unknown')
            scenarios_by_priority[priority] = scenarios_by_priority.get(priority, 0) + 1
        
        print_flush(f"\n  Scenarios by Priority:")
        for priority in ['critical', 'high', 'medium', 'low']:
            count = scenarios_by_priority.get(priority, 0)
            if count > 0:
                print_flush(f"    - {priority}: {count} scenarios")
        
        # Show first few scenarios with BDD structure
        print_flush(f"\n  Sample Scenarios (First 3):")
        for idx, scenario in enumerate(scenarios[:3], 1):
            scenario_id = scenario.get('scenario_id', 'UNKNOWN')
            scenario_title = scenario.get('title', 'Unknown')[:60]
            scenario_type = scenario.get('scenario_type', 'unknown')
            priority = scenario.get('priority', 'unknown')
            
            assert "given" in scenario, f"Scenario {scenario_id} missing 'given'"
            assert "when" in scenario, f"Scenario {scenario_id} missing 'when'"
            assert "then" in scenario, f"Scenario {scenario_id} missing 'then'"
            
            print_flush(f"    [{idx}] {scenario_id} ({scenario_type}, {priority}): {scenario_title}")
            print_flush(f"         Given: {scenario.get('given', '')[:70]}{'...' if len(scenario.get('given', '')) > 70 else ''}")
            print_flush(f"         When: {scenario.get('when', '')[:70]}{'...' if len(scenario.get('when', '')) > 70 else ''}")
            print_flush(f"         Then: {scenario.get('then', '')[:70]}{'...' if len(scenario.get('then', '')) > 70 else ''}")
        
        if len(scenarios) > 3:
            print_flush(f"    ... and {len(scenarios) - 3} more scenarios")
        
        # Show coverage metrics
        coverage_metrics = requirements_result.result.get('coverage_metrics', {})
        if coverage_metrics:
            print_flush(f"\n  Coverage Metrics:")
            ui_coverage = coverage_metrics.get('ui_coverage_percent', 0)
            print_flush(f"    - UI Coverage: {ui_coverage:.1f}%")
            total_elements = coverage_metrics.get('total_elements', 0)
            covered_elements = coverage_metrics.get('covered_elements', 0)
            if total_elements > 0:
                print_flush(f"    - Elements: {covered_elements}/{total_elements} covered")
        
        # Show quality indicators
        quality_indicators = requirements_result.result.get('quality_indicators', {})
        if quality_indicators:
            print_flush(f"\n  Quality Indicators:")
            confidence = quality_indicators.get('confidence', 0)
            completeness = quality_indicators.get('completeness', 0)
            print_flush(f"    - Confidence: {confidence:.2f}")
            print_flush(f"    - Completeness: {completeness:.2f}")
        
        # Step 3: AnalysisAgent - Analyze scenarios (with real-time execution enabled)
        logger.info("="*80)
        logger.info("Step 3: Starting AnalysisAgent - Analyzing scenarios with real-time execution...")
        logger.info("="*80)
        print_flush("\n" + "="*80)
        print_flush("Step 3: Analyzing scenarios with AnalysisAgent...")
        print_flush("        Real-time execution is ENABLED - critical scenarios will be executed automatically")
        print_flush("="*80)
        analysis_task = TaskContext(
            conversation_id=conversation_id,
            task_id="analysis-task-real-001",
            task_type="risk_analysis",
            payload={
                "scenarios": scenarios,
                "test_data": requirements_result.result.get("test_data", []),
                "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                "page_context": observation_data["page_context"]
            }
        )
        
        logger.info(f"AnalysisAgent: Starting risk analysis for {len(scenarios)} scenarios (real-time execution enabled)")
        logger.debug(f"AnalysisAgent task: {len(scenarios)} scenarios to analyze")
        print_flush(f"[INFO] AnalysisAgent: Analyzing {len(scenarios)} scenarios (calculating risk scores, prioritizing, executing critical ones)...")
        print_flush(f"        Analysis stages:")
        print_flush(f"        1. Historical data integration")
        print_flush(f"        2. FMEA risk scoring (RPN = Severity × Occurrence × Detection)")
        print_flush(f"        3. Real-time execution for critical scenarios (RPN ≥ 80)")
        print_flush(f"        4. Business value scoring")
        print_flush(f"        5. ROI calculation")
        print_flush(f"        6. Dependency analysis")
        print_flush(f"        7. Final prioritization\n")
        
        analysis_result = await analysis_agent_real.execute_task(analysis_task)
        
        risk_scores_count = len(analysis_result.result.get('risk_scores', []))
        execution_success = analysis_result.result.get("execution_success", [])
        real_execution_count = len([es for es in execution_success if es.get("source") in ["real_time_execution", "execution_results"]])
        
        logger.info(f"AnalysisAgent: COMPLETED - success={analysis_result.success}, "
                   f"confidence={analysis_result.confidence:.2f}, "
                   f"execution_time={analysis_result.execution_time_seconds:.2f}s, "
                   f"risk_scores={risk_scores_count}, "
                   f"real_executions={real_execution_count}")
        
        # Verify analysis succeeded
        assert analysis_result.success is True, f"Analysis failed: {analysis_result.error}"
        risk_scores_count = len(analysis_result.result.get('risk_scores', []))
        logger.info(f"AnalysisAgent calculated {risk_scores_count} risk scores")
        print_flush(f"[OK] Analysis complete: {risk_scores_count} risk scores calculated")
        assert risk_scores_count > 0, "No risk scores calculated"
        
        # Check if any scenarios were executed automatically (if RPN >= 80)
        execution_success = analysis_result.result.get("execution_success", [])
        real_execution_count = len([
            es for es in execution_success 
            if es.get("source") in ["real_time_execution", "execution_results"]
        ])
        
        if real_execution_count > 0:
            print_flush(f"[INFO] {real_execution_count} scenarios were automatically executed during analysis")
            print_flush("\n  Execution Results:")
            for idx, es in enumerate(execution_success[:5], 1):  # Show first 5
                if es.get("source") in ["real_time_execution", "execution_results"]:
                    scenario_id = es.get("scenario_id", "UNKNOWN")
                    success_rate = es.get("success_rate", 0.0)
                    passed_steps = es.get("passed_steps", 0)
                    total_steps = es.get("total_steps", 0)
                    tier_used = es.get("tier_used", "unknown")
                    reliability = es.get("reliability", "unknown")
                    print_flush(f"    [{idx}] Scenario {scenario_id}:")
                    print_flush(f"         Success Rate: {success_rate:.2%} ({passed_steps}/{total_steps} steps)")
                    print_flush(f"         Reliability: {reliability}, Tier: {tier_used}")
        
        # Verify analysis output structure
        print_flush("\n  Analysis Output Structure:")
        assert "risk_scores" in analysis_result.result
        print_flush(f"    [OK] Risk scores: {len(analysis_result.result['risk_scores'])} scenarios")
        assert "business_values" in analysis_result.result
        print_flush(f"    [OK] Business values: {len(analysis_result.result['business_values'])} scenarios")
        assert "roi_scores" in analysis_result.result
        print_flush(f"    [OK] ROI scores: {len(analysis_result.result['roi_scores'])} scenarios")
        assert "final_prioritization" in analysis_result.result
        print_flush(f"    [OK] Final prioritization: {len(analysis_result.result['final_prioritization'])} scenarios")
        assert "execution_strategy" in analysis_result.result
        print_flush(f"    [OK] Execution strategy: {len(analysis_result.result['execution_strategy'].get('smoke_tests', []))} smoke tests")
        
        # Step 4: EvolutionAgent - Generate test steps and store in database
        logger.info("="*80)
        logger.info("Step 4: Starting EvolutionAgent - Generating test steps and storing in database...")
        logger.info("="*80)
        print_flush("\n" + "="*80)
        print_flush("Step 4: Generating test steps with EvolutionAgent...")
        print_flush("="*80)
        # Build evolution task payload with optional user instruction and login credentials
        evolution_payload = {
            "scenarios": scenarios,  # BDD scenarios from RequirementsAgent
            "risk_scores": analysis_result.result["risk_scores"],
            "final_prioritization": analysis_result.result["final_prioritization"],
            "page_context": observation_data["page_context"],
            "test_data": requirements_result.result.get("test_data", []),
            "db": db_session  # Pass database session if available
        }
        if user_instruction:
            evolution_payload["user_instruction"] = user_instruction
            logger.info(f"EvolutionAgent: User instruction provided: '{user_instruction}'")
        if login_credentials:
            evolution_payload["login_credentials"] = login_credentials
            logger.info(f"EvolutionAgent: Login credentials provided (email: {login_credentials['email'][:10]}...)")
        
        evolution_task = TaskContext(
            conversation_id=conversation_id,
            task_id="evolution-task-real-001",
            task_type="test_generation",
            payload=evolution_payload
        )
        
        logger.info(f"EvolutionAgent: Starting test steps generation for {len(scenarios)} scenarios")
        logger.info(f"EvolutionAgent: Database session available: {db_session is not None}")
        logger.debug(f"EvolutionAgent task: {len(scenarios)} scenarios to convert to test steps")
        print_flush(f"[INFO] EvolutionAgent: Generating test steps for {len(scenarios)} scenarios "
              f"(database: {'enabled' if db_session else 'disabled'})...")
        print_flush(f"        This will convert BDD scenarios (Given/When/Then) to executable test steps")
        print_flush(f"        and store them in the database as TestCase objects\n")
        
        # Show which scenarios will be processed
        print_flush("  Scenarios to process:")
        for idx, scenario in enumerate(scenarios[:5], 1):  # Show first 5
            scenario_id = scenario.get("scenario_id", "UNKNOWN")
            scenario_title = scenario.get("title", "Unknown")[:60]
            print_flush(f"    [{idx}/{len(scenarios)}] {scenario_id}: {scenario_title}")
        if len(scenarios) > 5:
            print_flush(f"    ... and {len(scenarios) - 5} more scenarios\n")
        else:
            print_flush()
        
        evolution_result = await evolution_agent_real.execute_task(evolution_task)
        
        test_case_ids = evolution_result.result.get("test_case_ids", [])
        stored_in_db = evolution_result.result.get("stored_in_database", False)
        
        logger.info(f"EvolutionAgent: COMPLETED - success={evolution_result.success}, "
                   f"confidence={evolution_result.confidence:.2f}, "
                   f"execution_time={evolution_result.execution_time_seconds:.2f}s, "
                   f"test_cases_generated={evolution_result.result.get('test_count', 0)}, "
                   f"stored_in_db={stored_in_db}, "
                   f"db_ids_count={len(test_case_ids)}")
        
        # Verify EvolutionAgent succeeded
        assert evolution_result.success is True, f"EvolutionAgent failed: {evolution_result.error}"
        assert "generation_id" in evolution_result.result
        assert "test_count" in evolution_result.result
        assert "test_cases" in evolution_result.result
        assert evolution_result.result["test_count"] == len(scenarios)
        
        generation_id = evolution_result.result["generation_id"]
        test_case_ids = evolution_result.result.get("test_case_ids", [])
        stored_in_db = evolution_result.result.get("stored_in_database", False)
        
        print_flush(f"[OK] Evolution complete: {evolution_result.result['test_count']} test cases generated")
        print_flush(f"        Generation ID: {generation_id}")
        print_flush(f"        Stored in database: {stored_in_db}")
        if test_case_ids:
            print_flush(f"        Database IDs: {test_case_ids[:5]}{'...' if len(test_case_ids) > 5 else ''}")
        
        # Step 4.6: Feedback Loop - Learn from execution results (if available)
        print_flush("\nStep 4.6: Feedback Loop - Learning from execution results...")
        execution_feedback = None
        if stored_in_db and test_case_ids and evolution_agent_real.db:
            try:
                # Collect execution results from database
                from app.models.test_execution import TestExecution, ExecutionResult
                from app.models.test_case import TestCase
                
                # Query for completed executions
                executions = evolution_agent_real.db.query(TestExecution).filter(
                    TestExecution.test_case_id.in_(test_case_ids),
                    TestExecution.status == "completed"
                ).all()
                
                if executions:
                    # Prepare execution results for feedback
                    execution_summary = {
                        "total": len(executions),
                        "passed": sum(1 for e in executions if e.result == ExecutionResult.PASS),
                        "failed": sum(1 for e in executions if e.result == ExecutionResult.FAIL),
                        "errors": sum(1 for e in executions if e.result == ExecutionResult.ERROR)
                    }
                    
                    # Get scenario IDs from test cases
                    test_cases = evolution_agent_real.db.query(TestCase).filter(
                        TestCase.id.in_(test_case_ids)
                    ).all()
                    
                    failed_scenarios = []
                    successful_scenarios = []
                    for tc in test_cases:
                        scenario_id = None
                        if isinstance(tc.test_metadata, dict):
                            scenario_id = tc.test_metadata.get("scenario_id")
                        elif tc.test_metadata:
                            import json
                            try:
                                metadata = json.loads(tc.test_metadata)
                                scenario_id = metadata.get("scenario_id")
                            except:
                                pass
                        
                        # Check if this test case failed
                        exec_result = next((e for e in executions if e.test_case_id == tc.id), None)
                        if exec_result:
                            if exec_result.result == ExecutionResult.FAIL or exec_result.result == ExecutionResult.ERROR:
                                if scenario_id:
                                    failed_scenarios.append(scenario_id)
                            elif exec_result.result == ExecutionResult.PASS:
                                if scenario_id:
                                    successful_scenarios.append(scenario_id)
                    
                    execution_results = {
                        "test_case_ids": test_case_ids,
                        "execution_summary": execution_summary,
                        "failed_scenarios": failed_scenarios,
                        "successful_scenarios": successful_scenarios
                    }
                    
                    # Call learn_from_feedback
                    feedback_result = await evolution_agent_real.learn_from_feedback(
                        generation_id=generation_id,
                        execution_results=execution_results
                    )
                    
                    if feedback_result.get("status") == "success":
                        execution_feedback = feedback_result
                        insights = feedback_result.get("insights", [])
                        recommendations = feedback_result.get("recommendations", [])
                        metrics = feedback_result.get("metrics", {})
                        
                        print_flush(f"[OK] Feedback analysis complete:")
                        print_flush(f"        Pass Rate: {metrics.get('pass_rate', 0):.1f}%")
                        print_flush(f"        Insights: {len(insights)}")
                        print_flush(f"        Recommendations: {len(recommendations)}")
                        if insights:
                            print_flush(f"        Top Insight: {insights[0]}")
                        if recommendations:
                            print_flush(f"        Top Recommendation: {recommendations[0]}")
                    else:
                        print_flush(f"[INFO] Feedback analysis: {feedback_result.get('status', 'unknown')}")
                        if feedback_result.get("status") == "no_data":
                            print_flush(f"        No execution data available yet (tests may not have been executed)")
                else:
                    print_flush(f"[INFO] No completed executions found yet (feedback will be available after test execution)")
            except Exception as e:
                logger.warning(f"Feedback loop error: {e}", exc_info=True)
                print_flush(f"[WARN] Feedback loop error: {e}")
        else:
            print_flush(f"[INFO] Feedback loop skipped (database not available or test cases not stored)")
        
        # Store execution_feedback for potential use in next iteration
        # (In a real continuous improvement scenario, this would be passed to RequirementsAgent)
        if execution_feedback:
            logger.info(f"Feedback loop complete: {len(execution_feedback.get('insights', []))} insights generated")
        
        # Verify each scenario has corresponding test steps
        test_cases = evolution_result.result["test_cases"]
        assert len(test_cases) == len(scenarios)
        
        print_flush("\n  Generated Test Cases:")
        for idx, test_case_data in enumerate(test_cases[:5], 1):  # Show first 5
            scenario_id = test_case_data.get('scenario_id', 'UNKNOWN')
            steps = test_case_data.get('steps', [])
            confidence = test_case_data.get('confidence', 0.0)
            from_cache = test_case_data.get('from_cache', False)
            
            assert "steps" in test_case_data, \
                f"Test case {scenario_id} missing steps"
            assert isinstance(steps, list), \
                f"Test case {scenario_id} steps should be a list"
            assert len(steps) > 0, \
                f"Test case {scenario_id} has empty steps"
            
            cache_indicator = " [CACHED]" if from_cache else ""
            print_flush(f"    [{idx}] Scenario {scenario_id}:")
            print_flush(f"         Steps: {len(steps)} steps, Confidence: {confidence:.2f}{cache_indicator}")
            print_flush(f"         First step: {steps[0][:80]}{'...' if len(steps[0]) > 80 else ''}")
            if len(steps) > 1:
                print_flush(f"         Last step: {steps[-1][:80]}{'...' if len(steps[-1]) > 80 else ''}")
        
        if len(test_cases) > 5:
            print_flush(f"    ... and {len(test_cases) - 5} more test cases")
        
        # Verify confidence score
        assert evolution_result.confidence > 0.0
        assert evolution_result.result["confidence"] > 0.0
        print_flush(f"\n        Overall Confidence: {evolution_result.result['confidence']:.2f}")
        
        # Step 4.5: Verify test cases are stored in database (if database available)
        if db_session and stored_in_db and test_case_ids:
            logger.info(f"Step 4.5: Verifying {len(test_case_ids)} test cases in database...")
            print_flush("\nStep 4.5: Verifying test cases in database...")
            from app.models.test_case import TestCase
            import json
            
            # Query database for test cases by IDs (more reliable than JSON query)
            logger.debug(f"Querying database for test case IDs: {test_case_ids[:5]}{'...' if len(test_case_ids) > 5 else ''}")
            db_test_cases = db_session.query(TestCase).filter(
                TestCase.id.in_(test_case_ids)
            ).all()
            
            logger.info(f"Retrieved {len(db_test_cases)} test cases from database")
            assert len(db_test_cases) == len(test_case_ids), \
                f"Expected {len(test_case_ids)} test cases in database, got {len(db_test_cases)}"
            
            print_flush(f"[OK] Verified {len(db_test_cases)} test cases in database")
            
            # Verify test case structure
            print_flush("\n  Database Test Cases:")
            for idx, db_tc in enumerate(db_test_cases[:5], 1):  # Show first 5
                logger.debug(f"Verifying test case {idx}: ID={db_tc.id}, Title={db_tc.title}")
                assert db_tc.title is not None and len(db_tc.title) > 0, "Test case title should not be empty"
                assert db_tc.steps is not None and isinstance(db_tc.steps, list), "Test case steps should be a list"
                assert len(db_tc.steps) > 0, "Test case should have at least one step"
                assert db_tc.expected_result is not None, "Test case should have expected result"
                
                logger.debug(f"Test case {idx} steps: {db_tc.steps}")
                
                # Verify metadata contains generation_id
                if db_tc.test_metadata:
                    metadata = db_tc.test_metadata if isinstance(db_tc.test_metadata, dict) else json.loads(db_tc.test_metadata)
                    logger.debug(f"Test case {idx} metadata: {metadata}")
                    assert metadata.get("generation_id") == generation_id, \
                        f"Test case metadata should contain generation_id: {generation_id}"
                
                print_flush(f"    [{idx}] ID={db_tc.id}: {db_tc.title[:60]}{'...' if len(db_tc.title) > 60 else ''}")
                print_flush(f"         Steps: {len(db_tc.steps)} steps")
                print_flush(f"         First step: {db_tc.steps[0][:70]}{'...' if len(db_tc.steps[0]) > 70 else ''}")
                if len(db_tc.steps) > 1:
                    print_flush(f"         Last step: {db_tc.steps[-1][:70]}{'...' if len(db_tc.steps[-1]) > 70 else ''}")
            
            if len(db_test_cases) > 5:
                print_flush(f"    ... and {len(db_test_cases) - 5} more test cases in database")
        else:
            logger.warning(f"Step 4.5: Skipping database verification - db_session={db_session is not None}, "
                         f"stored_in_db={stored_in_db}, test_case_ids={len(test_case_ids) if test_case_ids else 0}")
            print_flush("\nStep 4.5: Skipping database verification (database not available or not stored)")
        
        # Step 5: Print summary
        print_flush(f"\n{'='*80}")
        print_flush("TEST SUMMARY")
        print_flush(f"{'='*80}")
        print_flush(f"Page URL: {target_url}")
        print_flush(f"UI Elements Observed: {len(observation_data['ui_elements'])}")
        print_flush(f"Scenarios Generated: {len(scenarios)}")
        print_flush(f"Risk Scores Calculated: {len(analysis_result.result['risk_scores'])}")
        print_flush(f"Scenarios Prioritized: {len(analysis_result.result['final_prioritization'])}")
        print_flush(f"Scenarios Executed (REAL): {real_execution_count}")
        print_flush(f"Test Cases Generated: {evolution_result.result['test_count']}")
        if evolution_result.result.get("stored_in_database"):
            print_flush(f"Test Cases Stored in DB: {len(evolution_result.result.get('test_case_ids', []))}")
        
        # Show top 3 prioritized scenarios
        print_flush(f"\nTop 3 Prioritized Scenarios:")
        final_prioritization = analysis_result.result["final_prioritization"]
        for idx, item in enumerate(final_prioritization[:3], 1):
            scenario = next((s for s in scenarios if s["scenario_id"] == item["scenario_id"]), None)
            if scenario:
                print_flush(f"  {idx}. {scenario.get('title', 'N/A')}")
                print_flush(f"     Priority: {item['priority']}, Score: {item['composite_score']:.2f}")
                print_flush(f"     Type: {scenario.get('scenario_type', 'N/A')}")
        
        print_flush(f"{'='*80}\n")
        
        # Final assertions
        assert len(scenarios) >= 5, f"Expected at least 5 scenarios, got {len(scenarios)}"
        # Some scenarios might be filtered out (circular dependencies, etc.), so allow some variance
        risk_scores_count = len(analysis_result.result["risk_scores"])
        assert risk_scores_count >= len(scenarios) * 0.7, \
            f"Expected at least 70% of scenarios to have risk scores, got {risk_scores_count}/{len(scenarios)}"
        assert len(final_prioritization) >= len(scenarios) * 0.7, \
            f"Expected at least 70% of scenarios to be prioritized, got {len(final_prioritization)}/{len(scenarios)}"
        
        print_flush("[OK] All assertions passed!")
        print_flush(f"\n{'='*80}")
        print_flush("TEST COMPLETE - All logs saved to:")
        print_flush(f"  {log_file}")
        print_flush(f"{'='*80}\n")


if __name__ == "__main__":
    # Use -s for no capture, -u for unbuffered output
    # Note: For real-time logging, run with: pytest -v -s --tb=short
    pytest.main([__file__, "-v", "-s", "--tb=short"])
