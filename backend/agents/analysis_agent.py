"""
AnalysisAgent - Risk analysis, prioritization, and dependency management
Follows ISTQB, IEEE 29119, FMEA standards for risk-based testing
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, deque
import time
import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RiskPriority(Enum):
    """Priority levels based on RPN (Risk Priority Number)"""
    CRITICAL = "critical"  # RPN ≥ 80
    HIGH = "high"          # RPN ≥ 50
    MEDIUM = "medium"      # RPN ≥ 20
    LOW = "low"            # RPN < 20


class RiskScore:
    """FMEA-based risk scoring (ISTQB, IEEE 29119)"""
    
    def __init__(self, severity: int, occurrence: int, detection: int):
        """
        Severity (1-5): Impact if bug reaches production
        Occurrence (1-5): Probability of bug occurring
        Detection (1-5): Difficulty of detecting bug (1=easy, 5=hard)
        """
        self.severity = severity  # 1=cosmetic, 5=system failure
        self.occurrence = occurrence  # 1=rare, 5=frequent
        self.detection = detection  # 1=always caught, 5=never caught
        self.rpn = severity * occurrence * detection  # Risk Priority Number (1-125)
    
    def to_priority(self) -> RiskPriority:
        """Convert RPN to priority level"""
        if self.rpn >= 80:
            return RiskPriority.CRITICAL
        elif self.rpn >= 50:
            return RiskPriority.HIGH
        elif self.rpn >= 20:
            return RiskPriority.MEDIUM
        else:
            return RiskPriority.LOW


class AnalysisAgent(BaseAgent):
    """
    Analyzes test scenarios for risk, prioritization, and dependencies.
    
    Industry Standards:
    - ISTQB: Risk-based testing approach
    - IEEE 29119: Test prioritization framework
    - FMEA: Failure Mode and Effects Analysis
    - Risk Priority Number (RPN) calculation
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int, 
                 message_queue, config: Optional[Dict] = None):
        """Initialize AnalysisAgent with optional LLM and database support"""
        super().__init__(agent_id, agent_type, priority, message_queue, config)
        
        # Initialize LLM client if enabled
        self.use_llm = config.get("use_llm", True) if config else True
        self.llm_client = None
        if self.use_llm:
            from llm.azure_client import get_azure_client
            self.llm_client = get_azure_client()
            if self.llm_client and self.llm_client.enabled:
                logger.info("AnalysisAgent initialized with LLM enhancement (Azure OpenAI)")
            else:
                logger.warning("LLM requested but not available, using heuristic-based scoring")
                self.use_llm = False
        
        # Initialize database connection if provided
        self.db = config.get("db") if config else None
        if self.db:
            logger.info("AnalysisAgent initialized with database access for historical data")
        else:
            logger.info("AnalysisAgent using stub mode for historical data (no database)")
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability("risk_analysis", "1.0.0", confidence_threshold=0.7),
            AgentCapability("dependency_analysis", "1.0.0", confidence_threshold=0.8),
            AgentCapability("roi_calculation", "1.0.0", confidence_threshold=0.75),
            AgentCapability("test_prioritization", "1.0.0", confidence_threshold=0.85)
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if agent can handle task"""
        if task.task_type in ["risk_analysis", "dependency_analysis", "test_prioritization"]:
            scenarios = task.payload.get("scenarios", [])
            if len(scenarios) > 0:
                confidence = min(0.95, 0.7 + (len(scenarios) / 50) * 0.25)
                return True, confidence
            return True, 0.7
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Analyze scenarios for risk, ROI, dependencies, and prioritization"""
        start_time = time.time()
        
        try:
            # Extract input data
            scenarios = task.payload.get("scenarios", [])
            test_data = task.payload.get("test_data", [])
            coverage_metrics = task.payload.get("coverage_metrics", {})
            page_context = task.payload.get("page_context", {})
            
            logger.info(f"AnalysisAgent: Processing {len(scenarios)} scenarios...")
            
            # Stage 1: Historical data integration
            logger.debug("AnalysisAgent: Stage 1 - Loading historical data...")
            historical_data = await self._load_historical_data(scenarios)
            logger.debug(f"AnalysisAgent: Loaded historical data for {len(historical_data)} scenarios")
            
            # Stage 2: Risk scoring (FMEA framework) - Initial scoring
            logger.debug("AnalysisAgent: Stage 2 - Calculating risk scores (FMEA framework)...")
            risk_scores = await self._calculate_risk_scores(
                scenarios, historical_data, page_context
            )
            logger.info(f"AnalysisAgent: Calculated risk scores for {len(risk_scores)} scenarios")
            
            # Stage 3: Business value scoring
            logger.debug("AnalysisAgent: Stage 3 - Calculating business values...")
            business_values = self._calculate_business_values(scenarios, page_context)
            
            # Stage 4: ROI calculation
            logger.debug("AnalysisAgent: Stage 4 - Calculating ROI scores...")
            roi_scores = self._calculate_roi_scores(
                scenarios, risk_scores, business_values, historical_data, page_context
            )
            
            # Stage 5: Execution time estimation
            logger.debug("AnalysisAgent: Stage 5 - Estimating execution times...")
            execution_times = self._estimate_execution_times(scenarios)
            
            # Stage 6: Dependency analysis
            logger.debug("AnalysisAgent: Stage 6 - Analyzing dependencies...")
            dependencies = self._analyze_dependencies(scenarios)
            
            # Stage 7: Coverage impact analysis
            logger.debug("AnalysisAgent: Stage 7 - Analyzing coverage impact...")
            coverage_impact = self._analyze_coverage_impact(
                scenarios, coverage_metrics
            )
            
            # Stage 8: Regression risk assessment
            logger.debug("AnalysisAgent: Stage 8 - Assessing regression risk...")
            regression_risk = await self._assess_regression_risk(scenarios, page_context)
            
            # Stage 9: Real-time test execution for critical scenarios (NEW - Phase 2 integration)
            execution_results = task.payload.get("execution_results")  # Optional: from post-execution feedback
            enable_realtime_execution = self.config.get("enable_realtime_execution", False) if self.config else False
            
            # Execute critical scenarios in real-time if enabled
            if enable_realtime_execution:
                # Get RPN threshold from config (default: 80 for production, lower for testing)
                rpn_threshold = self.config.get("execution_rpn_threshold", 80) if self.config else 80
                
                critical_scenarios = [
                    s for s in scenarios 
                    if risk_scores.get(s.get("scenario_id")) and 
                    risk_scores[s.get("scenario_id")].rpn >= rpn_threshold
                ]
                
                # If no scenarios meet threshold, execute top 2 prioritized scenarios instead
                if not critical_scenarios and len(scenarios) > 0:
                    logger.info(f"No scenarios with RPN >= {rpn_threshold}, executing top 2 prioritized scenarios instead")
                    # Sort scenarios by RPN (highest first) and take top 2
                    scenarios_with_scores = [
                        (s, risk_scores.get(s.get("scenario_id"))) 
                        for s in scenarios 
                        if risk_scores.get(s.get("scenario_id"))
                    ]
                    scenarios_with_scores.sort(key=lambda x: x[1].rpn if x[1] else 0, reverse=True)
                    critical_scenarios = [s for s, _ in scenarios_with_scores[:2]]
                
                if critical_scenarios:
                    # Get parallel execution batch size from config (default: 3)
                    batch_size = self.config.get("parallel_execution_batch_size", 3) if self.config else 3
                    scenarios_to_execute = critical_scenarios[:17]  # Execute all scenarios (or limit if needed)
                    
                    logger.info(f"AnalysisAgent: Executing {len(scenarios_to_execute)} scenarios in real-time "
                               f"(RPN threshold: {rpn_threshold}, parallel batch size: {batch_size})")
                    
                    # Execute scenarios in parallel batches
                    for batch_idx in range(0, len(scenarios_to_execute), batch_size):
                        batch = scenarios_to_execute[batch_idx:batch_idx + batch_size]
                        batch_num = (batch_idx // batch_size) + 1
                        total_batches = (len(scenarios_to_execute) + batch_size - 1) // batch_size
                        
                        logger.info(f"AnalysisAgent: Executing batch {batch_num}/{total_batches} "
                                   f"({len(batch)} scenarios in parallel)")
                        
                        # Create tasks for parallel execution
                        tasks = [
                            self._execute_scenario_real_time(scenario, page_context)
                            for scenario in batch
                        ]
                        
                        # Execute batch in parallel
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Process results
                        for idx, (scenario, result) in enumerate(zip(batch, batch_results)):
                            scenario_id = scenario.get("scenario_id", "UNKNOWN")
                            scenario_title = scenario.get("title", "Unknown")[:50]
                            
                            if isinstance(result, Exception):
                                logger.warning(f"AnalysisAgent: Real-time execution failed for {scenario_id}: {result}", exc_info=True)
                                continue
                            
                            if result and "scenario_id" in result:
                                if not execution_results:
                                    execution_results = []
                                execution_results.append(result)
                                passed_steps = result.get("passed_steps", 0)
                                total_steps = result.get("total_steps", 0)
                                success_rate = result.get("success_rate", 0.0)
                                logger.info(f"AnalysisAgent: Successfully executed scenario {scenario_id} "
                                           f"({passed_steps}/{total_steps} passed, success_rate={success_rate:.2f}, tier={result.get('tier_used', 'unknown')})")
                            else:
                                logger.warning(f"AnalysisAgent: Execution returned no result for scenario {scenario_id}")
                else:
                    logger.info("AnalysisAgent: No critical scenarios found for real-time execution")
            
            # Stage 10: Execution success rate analysis (incorporates real-time results)
            execution_success = await self._analyze_execution_success(
                scenarios, execution_results, page_context
            )
            
            # Adjust risk scores based on execution success
            for success_data in execution_success:
                scenario_id = success_data["scenario_id"]
                if scenario_id in risk_scores:
                    original_detection = risk_scores[scenario_id].detection
                    adjusted_detection = self._adjust_detection_score(
                        original_detection, success_data["success_rate"]
                    )
                    # Recalculate RPN with adjusted detection
                    risk_scores[scenario_id] = RiskScore(
                        severity=risk_scores[scenario_id].severity,
                        occurrence=risk_scores[scenario_id].occurrence,
                        detection=adjusted_detection
                    )
            
            # Stage 10: Final prioritization
            final_prioritization = self._finalize_prioritization(
                scenarios, risk_scores, business_values, roi_scores,
                coverage_impact, regression_risk, execution_times, execution_success
            )
            
            # Build execution strategy
            execution_strategy = self._build_execution_strategy(
                final_prioritization, dependencies, execution_times
            )
            
            # Prepare output
            # Convert risk_scores dict to list - one entry per scenario
            # (Some scenarios may share the same scenario_id due to RequirementsAgent
            #  generating template scenarios with overlapping IDs)
            risk_scores_list = []
            seen_in_list = set()
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                if scenario_id and scenario_id in risk_scores:
                    rs = risk_scores[scenario_id]
                    risk_dict = self._risk_score_to_dict(rs)
                    risk_dict["scenario_id"] = scenario_id
                    risk_scores_list.append(risk_dict)
                    seen_in_list.add(scenario_id)
            # Also add any risk_scores for IDs not in scenarios list (shouldn't happen, but be safe)
            for scenario_id, rs in risk_scores.items():
                if scenario_id not in seen_in_list:
                    risk_dict = self._risk_score_to_dict(rs)
                    risk_dict["scenario_id"] = scenario_id
                    risk_scores_list.append(risk_dict)
            logger.info(f"AnalysisAgent: risk_scores_list has {len(risk_scores_list)} entries for {len(scenarios)} scenarios (from {len(risk_scores)} unique IDs)")
            
            result = {
                "risk_scores": risk_scores_list,
                "business_values": business_values,
                "roi_scores": roi_scores,
                "execution_times": execution_times,
                "dependencies": dependencies,
                "coverage_impact": coverage_impact,
                "regression_risk": regression_risk,
                "execution_success": execution_success,
                "final_prioritization": final_prioritization,
                "execution_strategy": execution_strategy
            }
            
            execution_time = time.time() - start_time
            self.tasks_completed += 1
            self.total_execution_time += execution_time
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=0.87,
                execution_time_seconds=execution_time,
                metadata={"token_usage": self._estimate_token_usage(scenarios)}
            )
            
        except Exception as e:
            logger.error(f"AnalysisAgent error: {e}", exc_info=True)
            self.tasks_failed += 1
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time
            )
    
    async def _load_historical_data(self, scenarios: List[Dict]) -> Dict:
        """Load historical execution data from Phase 2 database"""
        historical = {
            "failure_rates": {},
            "bug_frequency": {},
            "time_to_fix": {},
            "change_frequency": {}
        }
        
        # If no database, return default values
        if not self.db:
            scenario_types = set(s.get("scenario_type", "functional") for s in scenarios)
            for scenario_type in scenario_types:
                historical["failure_rates"][scenario_type] = 0.3  # 30% default
                historical["bug_frequency"][scenario_type] = 0
                historical["time_to_fix"][scenario_type] = 24.0
            return historical
        
        # Query Phase 2 executions table (using existing test_executions table)
        scenario_types = [s.get("scenario_type", "functional") for s in scenarios]
        
        try:
            # Use SQLAlchemy query (SQLite-compatible syntax)
            from sqlalchemy import text
            query = text("""
                SELECT 
                    'functional' as scenario_type,
                    SUM(CASE WHEN result = 'failed' THEN 1 ELSE 0 END) as failure_count,
                    COUNT(*) as total_count,
                    AVG((julianday(updated_at) - julianday(created_at)) * 24) as avg_fix_time
                FROM test_executions
                WHERE created_at > datetime('now', '-90 days')
                GROUP BY scenario_type
            """)
            
            result = self.db.execute(query)
            rows = result.fetchall()
            
            for row in rows:
                scenario_type = row[0] if len(row) > 0 else "functional"
                failure_count = row[1] if len(row) > 1 else 0
                total_count = row[2] if len(row) > 2 else 1
                avg_fix_time = float(row[3]) if len(row) > 3 and row[3] else 24.0
                
                historical["failure_rates"][scenario_type] = (
                    failure_count / total_count if total_count > 0 else 0.0
                )
                historical["bug_frequency"][scenario_type] = failure_count
                historical["time_to_fix"][scenario_type] = avg_fix_time
                
        except Exception as e:
            logger.warning(f"Could not load historical data: {e}, using defaults")
            # Use default values
            scenario_types = set(s.get("scenario_type", "functional") for s in scenarios)
            for scenario_type in scenario_types:
                historical["failure_rates"][scenario_type] = 0.3  # 30% default
                historical["bug_frequency"][scenario_type] = 0
                historical["time_to_fix"][scenario_type] = 24.0
        
        return historical
    
    async def _calculate_risk_scores(
        self, scenarios: List[Dict], historical_data: Dict, page_context: Dict
    ) -> Dict[str, RiskScore]:
        """Calculate FMEA-based risk scores using LLM + historical data"""
        risk_scores = {}
        
        # Build LLM prompt for risk analysis
        prompt = self._build_risk_analysis_prompt(scenarios, historical_data, page_context)
        
        if self.use_llm and self.llm_client and self.llm_client.enabled:
            try:
                # Call LLM for risk assessment using Azure OpenAI
                response = await asyncio.to_thread(
                    self.llm_client.client.chat.completions.create,
                    model=self.llm_client.deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert risk analyst for software testing. Analyze test scenarios and provide FMEA-based risk assessments. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,  # Lower temperature for more consistent scoring
                    max_tokens=3000,
                    response_format={"type": "json_object"}
                )
                
                # Parse LLM response (structured JSON)
                llm_output = json.loads(response.choices[0].message.content)
                
                for scenario_data in llm_output.get("risk_assessments", []):
                    scenario_id = scenario_data.get("scenario_id")
                    severity = scenario_data.get("severity")
                    occurrence = scenario_data.get("occurrence")
                    detection = scenario_data.get("detection")
                    
                    if not all([scenario_id, severity, occurrence, detection]):
                        continue
                    
                    # Get original scenario to check for user-requirement tag
                    original_scenario = next(
                        (s for s in scenarios if s.get("scenario_id") == scenario_id),
                        {}
                    )
                    has_user_requirement = "user-requirement" in original_scenario.get("tags", [])
                    original_priority = original_scenario.get("priority", "medium")
                    
                    # Adjust occurrence based on historical data
                    scenario_type = next(
                        (s.get("scenario_type", "functional") for s in scenarios 
                         if s.get("scenario_id") == scenario_id), 
                        "functional"
                    )
                    historical_failure_rate = historical_data["failure_rates"].get(
                        scenario_type, 0.3
                    )
                    
                    # Adjust occurrence: if historical failure rate is high, boost occurrence
                    occurrence_adjusted = occurrence
                    if historical_failure_rate > 0.5:
                        occurrence_adjusted = min(5, occurrence + 1)
                    elif historical_failure_rate > 0.3:
                        occurrence_adjusted = min(5, occurrence + 0.5)
                    
                    # BOOST risk scores for user-requirement scenarios
                    # This ensures they get higher priority in final prioritization
                    severity_adjusted = severity
                    if has_user_requirement:
                        # Boost severity for user-requirement scenarios (they're important to the user)
                        severity_adjusted = min(5, severity + 1)
                        logger.debug(f"AnalysisAgent: Boosting severity for user-requirement scenario {scenario_id}: {severity} -> {severity_adjusted}")
                    
                    # Also boost if original priority was high/critical
                    if original_priority in ["critical", "high"] and not has_user_requirement:
                        severity_adjusted = min(5, severity + 1)
                        logger.debug(f"AnalysisAgent: Boosting severity for high-priority scenario {scenario_id}: {severity} -> {severity_adjusted}")
                    
                    risk_scores[scenario_id] = RiskScore(
                        severity=int(severity_adjusted),
                        occurrence=int(occurrence_adjusted),
                        detection=int(detection)
                    )
                
            except Exception as e:
                logger.warning(f"LLM risk analysis failed: {e}, using heuristics")
                # Fall through to heuristic-based scoring
        
        # Fallback to heuristic-based scoring for scenarios without risk scores
        # This ensures ALL scenarios get risk scores, even if LLM didn't return them all
        all_scenario_ids = [s.get("scenario_id") for s in scenarios]
        unique_scenario_ids = set(all_scenario_ids)
        logger.info(f"AnalysisAgent: Risk scores before fallback: {len(risk_scores)} unique IDs scored, "
                     f"{len(scenarios)} scenarios ({len(unique_scenario_ids)} unique IDs)")
        if len(unique_scenario_ids) < len(scenarios):
            duplicate_ids = [sid for sid in unique_scenario_ids if all_scenario_ids.count(sid) > 1]
            logger.warning(f"AnalysisAgent: {len(scenarios) - len(unique_scenario_ids)} duplicate scenario_ids detected: {duplicate_ids[:5]}")
        missing_scenarios = [s for s in scenarios if s.get("scenario_id") not in risk_scores]
        logger.info(f"AnalysisAgent: Missing scenarios (no risk score): {len(missing_scenarios)}")
        if missing_scenarios:
            logger.info(f"AnalysisAgent: Using heuristic scoring for {len(missing_scenarios)} scenarios not returned by LLM")
            for scenario in missing_scenarios:
                scenario_id = scenario.get("scenario_id")
                if scenario_id:
                    priority = scenario.get("priority", "medium")
                    
                    # Heuristic mapping
                    if priority == "critical":
                        risk_scores[scenario_id] = RiskScore(5, 4, 5)  # RPN = 100
                    elif priority == "high":
                        risk_scores[scenario_id] = RiskScore(4, 3, 4)  # RPN = 48
                    elif priority == "medium":
                        risk_scores[scenario_id] = RiskScore(3, 2, 3)  # RPN = 18
                    else:
                        risk_scores[scenario_id] = RiskScore(2, 1, 2)  # RPN = 4
            logger.info(f"AnalysisAgent: Added heuristic risk scores for {len(missing_scenarios)} scenarios. Total risk scores: {len(risk_scores)}/{len(scenarios)}")
        
        # If no risk scores at all (LLM failed completely and no scenarios), use heuristics for all
        if not risk_scores:
            logger.debug("AnalysisAgent: No risk scores from LLM, using heuristics for all scenarios")
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                if scenario_id and scenario_id not in risk_scores:
                    priority = scenario.get("priority", "medium")
                    
                    # Heuristic mapping
                    if priority == "critical":
                        risk_scores[scenario_id] = RiskScore(5, 4, 5)  # RPN = 100
                    elif priority == "high":
                        risk_scores[scenario_id] = RiskScore(4, 3, 4)  # RPN = 48
                    elif priority == "medium":
                        risk_scores[scenario_id] = RiskScore(3, 2, 3)  # RPN = 18
                    else:
                        risk_scores[scenario_id] = RiskScore(2, 1, 2)  # RPN = 4
        
        return risk_scores
    
    def _build_risk_analysis_prompt(
        self, scenarios: List[Dict], historical_data: Dict, page_context: Dict
    ) -> str:
        """Build LLM prompt for structured risk analysis"""
        # Check for user-requirement scenarios
        user_requirement_scenarios = [s for s in scenarios if "user-requirement" in s.get("tags", [])]
        user_requirement_section = ""
        if user_requirement_scenarios:
            user_requirement_section = f"""
**IMPORTANT - USER REQUIREMENT SCENARIOS:**
The following scenarios are tagged with "user-requirement" - they match specific user instructions:
{chr(10).join(f"- {s.get('scenario_id')}: {s.get('title')} (Priority: {s.get('priority', 'medium')})" for s in user_requirement_scenarios[:5])}

**CRITICAL INSTRUCTION:** These user-requirement scenarios MUST be assigned HIGH severity (4-5) and HIGH priority in your risk assessment.
They represent specific user needs and should be prioritized accordingly. If a scenario has "user-requirement" tag, assign severity >= 4.
"""
        
        return f"""Analyze the following test scenarios and provide FMEA-based risk assessment.
{user_requirement_section}
Page Context:
- Type: {page_context.get("page_type", "unknown")}
- Framework: {page_context.get("framework", "unknown")}
- Complexity: {page_context.get("complexity", "medium")}

Historical Data:
- Failure Rates: {json.dumps(historical_data.get("failure_rates", {}), indent=2)}
- Bug Frequency: {json.dumps(historical_data.get("bug_frequency", {}), indent=2)}

Test Scenarios:
{json.dumps(scenarios, indent=2)}

For each scenario, provide:
{{
  "risk_assessments": [
    {{
      "scenario_id": "REQ-F-001",
      "severity": 1-5,  // 1=cosmetic, 5=system failure
      "occurrence": 1-5,  // 1=rare, 5=frequent (consider historical data)
      "detection": 1-5,  // 1=always caught, 5=never caught
      "reasoning": "Explanation of scores"
    }}
  ]
}}

Scoring Guidelines:
- Severity: Consider business impact if bug reaches production
- Occurrence: Use historical failure rates to inform probability
- Detection: Consider test complexity and coverage

Respond with valid JSON only."""
    
    def _calculate_business_values(
        self, scenarios: List[Dict], page_context: Dict
    ) -> List[Dict]:
        """Calculate business value scores (revenue, users, compliance)"""
        business_values = []
        
        page_type = page_context.get("page_type", "unknown")
        
        # Revenue impact weights
        revenue_weights = {
            "checkout": 1.0,
            "payment": 1.0,
            "pricing": 0.9,
            "login": 0.8,
            "dashboard": 0.6,
            "footer": 0.1
        }
        revenue_impact = revenue_weights.get(page_type, 0.5)
        
        # User impact (normalize to 10K users)
        estimated_users = page_context.get("estimated_users", 1000)
        user_impact = min(1.0, estimated_users / 10000)
        
        # Compliance check
        compliance_score = 0.0
        if "gdpr" in page_type.lower() or "data" in page_type.lower():
            compliance_score = 1.0
        elif "payment" in page_type.lower() or "pci" in page_type.lower():
            compliance_score = 1.0
        
        # Reputation (public-facing vs internal)
        reputation_score = 1.0 if page_context.get("public", True) else 0.5
        
        # Weighted sum
        total_value = (
            revenue_impact * 0.4 +
            user_impact * 0.3 +
            compliance_score * 0.2 +
            reputation_score * 0.1
        )
        
        for scenario in scenarios:
            business_values.append({
                "scenario_id": scenario.get("scenario_id"),
                "revenue_impact": revenue_impact,
                "user_impact": user_impact,
                "compliance": compliance_score,
                "reputation": reputation_score,
                "total_value": round(total_value, 2)
            })
        
        return business_values
    
    def _calculate_roi_scores(
        self, scenarios: List[Dict], risk_scores: Dict[str, RiskScore],
        business_values: List[Dict], historical_data: Dict, page_context: Dict
    ) -> List[Dict]:
        """Calculate ROI for each scenario"""
        roi_scores = []
        
        # Cost of production bugs by page type
        bug_costs = {
            "checkout": 50000.0,  # $50K/hour revenue loss
            "payment": 50000.0,
            "login": 10000.0,     # $10K/hour downtime
            "dashboard": 5000.0,
            "default": 1000.0
        }
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            risk_score = risk_scores.get(scenario_id)
            business_value = next(
                (bv for bv in business_values if bv["scenario_id"] == scenario_id),
                {}
            )
            
            if not risk_score:
                continue
            
            # Probability of bug (from occurrence score)
            p_bug = risk_score.occurrence / 5.0  # Normalize 1-5 to 0.0-1.0
            
            # Cost of production bug
            page_type = scenario.get("page_type") or page_context.get("page_type", "default")
            cost_production = bug_costs.get(page_type, bug_costs["default"])
            
            # Detection rate (from detection score, inverted)
            detection_rate = 1.0 - ((risk_score.detection - 1) / 4.0)  # 1=0.0, 5=1.0
            detection_rate = max(0.5, detection_rate)  # Minimum 50%
            
            # Bug detection value
            bug_value = p_bug * cost_production * detection_rate
            
            # Test cost
            dev_time_cost = 50.0  # $50 for development
            exec_time_cost = 5.0  # $5 for execution (estimated)
            maintenance_cost = 10.0  # $10/month maintenance
            test_cost = dev_time_cost + exec_time_cost + maintenance_cost
            
            # ROI
            roi = (bug_value - test_cost) / test_cost if test_cost > 0 else 0.0
            
            roi_scores.append({
                "scenario_id": scenario_id,
                "roi": round(roi, 2),
                "bug_detection_value": round(bug_value, 2),
                "test_cost": round(test_cost, 2),
                "break_even_days": round(test_cost / (bug_value / 30), 2) if bug_value > 0 else 999
            })
        
        return roi_scores
    
    def _estimate_execution_times(self, scenarios: List[Dict]) -> List[Dict]:
        """Estimate execution time for each scenario"""
        execution_times = []
        
        # Action time heuristics
        action_times = {
            "navigation": 1.0,
            "click": 0.5,
            "type": 0.3,
            "wait": 2.0,
            "assertion": 0.2
        }
        
        base_time = 2.0  # Page load, setup
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            when_clause = scenario.get("when", "").lower()
            
            # Count actions (simple heuristic)
            action_count = {
                "navigation": when_clause.count("navigate") + when_clause.count("goto"),
                "click": when_clause.count("click"),
                "type": when_clause.count("type") + when_clause.count("enter"),
                "wait": when_clause.count("wait"),
                "assertion": scenario.get("then", "").lower().count("expect") + 
                            scenario.get("then", "").lower().count("verify")
            }
            
            # Calculate total time
            total_time = base_time + sum(
                action_times[action] * count 
                for action, count in action_count.items()
            )
            
            # Add flakiness buffer (20%)
            estimated_seconds = total_time * 1.2
            
            # Categorize
            if estimated_seconds < 30:
                category = "fast"
            elif estimated_seconds < 120:
                category = "medium"
            else:
                category = "slow"
            
            execution_times.append({
                "scenario_id": scenario_id,
                "estimated_seconds": round(estimated_seconds, 1),
                "category": category
            })
        
        return execution_times
    
    def _analyze_dependencies(self, scenarios: List[Dict]) -> List[Dict]:
        """Analyze dependencies using topological sort"""
        dependencies = []
        
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        scenario_ids = [s.get("scenario_id") for s in scenarios]
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            depends_on = scenario.get("depends_on", [])
            
            in_degree[scenario_id] = len(depends_on)
            
            for dep in depends_on:
                if dep in scenario_ids:
                    graph[dep].append(scenario_id)
        
        # Topological sort (Kahn's algorithm)
        queue = deque([sid for sid, degree in in_degree.items() if degree == 0])
        execution_order = []
        order_map = {}
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            order_map[current] = len(execution_order)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Detect cycles
        if len(execution_order) < len(scenarios):
            logger.warning("Circular dependency detected in scenarios!")
        
        # Build dependencies output
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            depends_on = scenario.get("depends_on", [])
            can_run_parallel = in_degree.get(scenario_id, 0) == 0
            
            dependencies.append({
                "scenario_id": scenario_id,
                "depends_on": depends_on,
                "execution_order": order_map.get(scenario_id, 999),
                "can_run_parallel": can_run_parallel
            })
        
        return dependencies
    
    def _analyze_coverage_impact(
        self, scenarios: List[Dict], coverage_metrics: Dict
    ) -> List[Dict]:
        """Analyze coverage impact of each test"""
        coverage_impact = []
        
        current_coverage = coverage_metrics.get("ui_coverage_percent", 0.0) / 100.0
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            scenario_type = scenario.get("scenario_type", "functional")
            
            # Estimate coverage delta (heuristic)
            # Critical/security scenarios typically cover more
            if scenario_type == "security" or scenario.get("priority") == "critical":
                coverage_delta = 0.15
            elif scenario_type == "functional":
                coverage_delta = 0.10
            else:
                coverage_delta = 0.05
            
            # Check if covers new code
            covers_new_code = current_coverage < 0.8  # If coverage is low, likely new
            
            # Gap priority
            if current_coverage < 0.5:
                gap_priority = "high"
            elif current_coverage < 0.8:
                gap_priority = "medium"
            else:
                gap_priority = "low"
            
            coverage_impact.append({
                "scenario_id": scenario_id,
                "coverage_delta": round(coverage_delta, 2),
                "covers_new_code": covers_new_code,
                "gap_priority": gap_priority
            })
        
        return coverage_impact
    
    async def _assess_regression_risk(
        self, scenarios: List[Dict], page_context: Dict
    ) -> List[Dict]:
        """Assess regression risk based on code churn"""
        regression_risk = []
        
        # Git history analysis (simplified - would need actual git integration)
        # For now, use heuristics based on page type and scenario type
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            scenario_type = scenario.get("scenario_type", "functional")
            
            # Heuristic: Security and critical scenarios have higher regression risk
            if scenario_type == "security" or scenario.get("priority") == "critical":
                churn_score = 0.8
                recent_changes = 5
                days_since_last_change = 2
            elif scenario_type == "functional":
                churn_score = 0.5
                recent_changes = 2
                days_since_last_change = 7
            else:
                churn_score = 0.3
                recent_changes = 1
                days_since_last_change = 14
            
            regression_risk.append({
                "scenario_id": scenario_id,
                "churn_score": churn_score,
                "recent_changes": recent_changes,
                "days_since_last_change": days_since_last_change
            })
        
        return regression_risk
    
    async def _analyze_execution_success(
        self, scenarios: List[Dict], execution_results: Optional[Dict] = None,
        page_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Analyze test execution success rates.
        
        Three modes:
        1. Real-time execution: Execute critical scenarios using Phase 2 engine (Sprint 8)
        2. Historical data: Use past execution results from database
        3. Post-execution: Use actual execution results from EvolutionAgent
        """
        execution_success = []
        
        # Convert execution_results to dict if it's a list
        execution_results_dict = {}
        if execution_results:
            if isinstance(execution_results, list):
                for er in execution_results:
                    if isinstance(er, dict) and "scenario_id" in er:
                        execution_results_dict[er["scenario_id"]] = er
            elif isinstance(execution_results, dict):
                execution_results_dict = execution_results
        
        # Mode 2: Post-execution results (from EvolutionAgent or real-time execution)
        if execution_results_dict:
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                result = execution_results_dict.get(scenario_id, {})
                
                passed_steps = result.get("passed_steps", 0)
                total_steps = result.get("total_steps", 0)
                
                if total_steps > 0:
                    success_rate = passed_steps / total_steps
                else:
                    success_rate = 0.0
                
                reliability = self._categorize_reliability(success_rate)
                
                execution_success.append({
                    "scenario_id": scenario_id,
                    "success_rate": round(success_rate, 2),
                    "passed_steps": passed_steps,
                    "total_steps": total_steps,
                    "reliability": reliability,
                    "source": "execution_results"
                })
        
        # Mode 3: Historical data (for non-critical scenarios)
        else:
            for scenario in scenarios:
                historical = await self._get_historical_success_rate(scenario)
                execution_success.append(historical)
        
        return execution_success
    
    async def _get_historical_success_rate(self, scenario: Dict) -> Dict:
        """Get historical success rate from Phase 2 executions"""
        scenario_id = scenario.get("scenario_id")
        scenario_type = scenario.get("scenario_type", "functional")
        
        if not self.db:
            # Stub mode: return default values
            return {
                "scenario_id": scenario_id,
                "success_rate": 0.85,
                "passed_steps": 17,
                "total_steps": 20,
                "reliability": "high",
                "source": "historical_data_stub"
            }
        
        try:
            from sqlalchemy import text
            query = text("""
                SELECT 
                    AVG(CAST(passed_steps AS FLOAT) / NULLIF(total_steps, 0)) as avg_success_rate,
                    AVG(passed_steps) as avg_passed,
                    AVG(total_steps) as avg_total
                FROM test_executions
                WHERE created_at > datetime('now', '-90 days')
                  AND total_steps > 0
            """)
            result = self.db.execute(query)
            row = result.fetchone()
            
            if row and row[0]:
                success_rate = float(row[0])
                avg_passed = int(row[1] or 0)
                avg_total = int(row[2] or 0)
            else:
                success_rate = 0.85
                avg_passed = 17
                avg_total = 20
        
        except Exception as e:
            logger.warning(f"Could not load historical success rate: {e}, using defaults")
            success_rate = 0.85
            avg_passed = 17
            avg_total = 20
        
        return {
            "scenario_id": scenario_id,
            "success_rate": round(success_rate, 2),
            "passed_steps": avg_passed,
            "total_steps": avg_total,
            "reliability": self._categorize_reliability(success_rate),
            "source": "historical_data"
        }
    
    def _categorize_reliability(self, success_rate: float) -> str:
        """Categorize reliability based on success rate"""
        if success_rate >= 0.9:
            return "high"
        elif success_rate >= 0.7:
            return "medium"
        elif success_rate >= 0.5:
            return "low"
        else:
            return "flaky"
    
    def _adjust_detection_score(
        self, original_detection: int, success_rate: float
    ) -> int:
        """
        Adjust Detection score in RPN based on execution success rate.
        
        High success rate = Lower detection score (test is reliable)
        Low success rate = Higher detection score (test is unreliable)
        """
        if success_rate >= 0.9:
            # Test is very reliable, detection is easy
            return max(1, original_detection - 2)
        elif success_rate >= 0.7:
            # Test is usually reliable
            return max(1, original_detection - 1)
        elif success_rate >= 0.5:
            # Test is sometimes reliable
            return original_detection
        else:
            # Test is unreliable/flaky, detection is hard
            return min(5, original_detection + 1)
    
    def _finalize_prioritization(
        self, scenarios: List[Dict], risk_scores: Dict[str, RiskScore],
        business_values: List[Dict], roi_scores: List[Dict],
        coverage_impact: List[Dict], regression_risk: List[Dict],
        execution_times: List[Dict], execution_success: List[Dict]
    ) -> List[Dict]:
        """Final prioritization using composite scoring"""
        final_prioritization = []
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            
            # Get all scores
            risk_score = risk_scores.get(scenario_id)
            business_value = next(
                (bv for bv in business_values if bv["scenario_id"] == scenario_id),
                {}
            )
            roi_score = next(
                (roi for roi in roi_scores if roi["scenario_id"] == scenario_id),
                {}
            )
            coverage = next(
                (cov for cov in coverage_impact if cov["scenario_id"] == scenario_id),
                {}
            )
            regression = next(
                (reg for reg in regression_risk if reg["scenario_id"] == scenario_id),
                {}
            )
            exec_time = next(
                (et for et in execution_times if et["scenario_id"] == scenario_id),
                {}
            )
            exec_success = next(
                (es for es in execution_success if es["scenario_id"] == scenario_id),
                {}
            )
            
            if not risk_score:
                continue
            
            # Normalize scores to 0.0-1.0
            risk_normalized = risk_score.rpn / 125.0  # RPN max = 125
            business_normalized = business_value.get("total_value", 0.0)
            roi_normalized = min(1.0, roi_score.get("roi", 0.0) / 50.0)  # ROI max ~50x
            coverage_normalized = coverage.get("coverage_delta", 0.0) / 0.2  # Max delta ~0.2
            regression_normalized = regression.get("churn_score", 0.0)
            success_normalized = exec_success.get("success_rate", 0.85)  # Default 85% if unknown
            
            # Composite score (weighted, enhanced with execution success)
            composite_score = (
                risk_normalized * 0.25 +
                business_normalized * 0.25 +
                roi_normalized * 0.2 +
                coverage_normalized * 0.15 +
                regression_normalized * 0.1 +
                success_normalized * 0.05  # Execution success component
            )
            
            # Business rules: Compliance always critical
            if business_value.get("compliance", 0.0) >= 0.8:
                priority = RiskPriority.CRITICAL
            else:
                priority = risk_score.to_priority()
            
            # Execution group (enhanced with success rate)
            is_fast = exec_time.get("category") == "fast"
            is_reliable = exec_success.get("reliability") in ["high", "medium"]
            is_flaky = exec_success.get("reliability") == "flaky"
            
            if priority == RiskPriority.CRITICAL and is_fast and is_reliable:
                execution_group = "critical_smoke"
            elif priority == RiskPriority.CRITICAL:
                execution_group = "critical_full"
            elif is_flaky:
                execution_group = "flaky"  # Mark flaky tests separately
            else:
                execution_group = priority.value
            
            final_prioritization.append({
                "scenario_id": scenario_id,
                "composite_score": round(composite_score, 2),
                "priority": priority.value,
                "execution_group": execution_group,
                "recommended_execution_time": "immediate" if priority == RiskPriority.CRITICAL else "normal"
            })
        
        # Sort by composite score (descending)
        final_prioritization.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Add rank
        for idx, item in enumerate(final_prioritization, 1):
            item["rank"] = idx
        
        return final_prioritization
    
    def _build_execution_strategy(
        self, final_prioritization: List[Dict],
        dependencies: List[Dict], execution_times: List[Dict]
    ) -> Dict:
        """Build execution strategy (smoke tests, parallel groups)"""
        # Smoke tests: Critical + Fast
        smoke_tests = [
            item["scenario_id"] for item in final_prioritization
            if item["execution_group"] == "critical_smoke"
        ]
        
        # Parallel groups: Independent scenarios
        parallel_groups = []
        independent_scenarios = [
            dep["scenario_id"] for dep in dependencies
            if dep["can_run_parallel"]
        ]
        
        if independent_scenarios:
            # Group by execution group for parallel execution
            groups = defaultdict(list)
            for item in final_prioritization:
                if item["scenario_id"] in independent_scenarios:
                    groups[item["execution_group"]].append(item["scenario_id"])
            parallel_groups = list(groups.values())
        
        # Calculate estimated times
        total_time = sum(
            et["estimated_seconds"] for et in execution_times
        )
        
        # Parallel time (assume 3 parallel workers)
        parallel_time = total_time / 3.0 if parallel_groups else total_time
        
        return {
            "smoke_tests": smoke_tests,
            "parallel_groups": parallel_groups,
            "estimated_total_time": round(total_time, 1),
            "estimated_parallel_time": round(parallel_time, 1)
        }
    
    async def _execute_scenario_real_time(
        self, scenario: Dict, page_context: Optional[Dict]
    ) -> Optional[Dict]:
        """
        Execute a scenario in real-time using Phase 2 execution engine.
        
        Converts BDD scenario (Given/When/Then) to executable test steps
        and executes using 3-tier strategy (Playwright → Hybrid → Stagehand AI).
        
        Returns execution result with success rate for scoring.
        """
        try:
            from app.services.stagehand_service import StagehandExecutionService
            from app.models.test_case import TestCase, TestType, Priority
            from app.models.test_execution import ExecutionStatus, ExecutionResult
            from app.crud import test_execution as crud_execution
            
            # Convert BDD scenario to test steps
            test_steps = self._convert_scenario_to_steps(scenario, page_context)
            
            if not test_steps:
                logger.warning(f"No executable steps for scenario {scenario.get('scenario_id')}")
                return None
            
            base_url = page_context.get("url", "https://example.com") if page_context else "https://example.com"
            
            # Create temporary test case for execution
            temp_test_case = TestCase(
                title=f"[AnalysisAgent] {scenario.get('title', 'Scenario')}",
                description=scenario.get("given", ""),
                test_type=TestType.E2E,
                priority=Priority.HIGH,
                steps=test_steps,
                expected_result=scenario.get("then", ""),
                user_id=1  # Default user for agent executions
            )
            
            # Initialize execution service
            # Read headless mode from config first, then env (default: True for CI/CD compatibility)
            # Support both HEADLESS_BROWSER (existing) and BROWSER_HEADLESS (for consistency)
            # Note: headless=True means browser is hidden, headless=False means browser is shown
            import os
            if self.config and "headless_browser" in self.config:
                # Config takes precedence: False = show browser, True = hide browser
                headless_mode = bool(self.config["headless_browser"])
            else:
                # Fall back to environment variable
                headless_str = os.getenv("HEADLESS_BROWSER") or os.getenv("BROWSER_HEADLESS", "true")
                headless_str = headless_str.lower()
                headless_mode = headless_str in ("true", "1", "yes")
            execution_service = StagehandExecutionService(headless=headless_mode)
            
            # Create execution record in database if available
            execution_id = None
            if self.db:
                try:
                    execution = crud_execution.create_execution(
                        db=self.db,
                        test_case_id=0,  # Temporary test case
                        user_id=1,
                        browser="chromium",
                        environment="dev",
                        base_url=base_url
                    )
                    execution_id = execution.id
                except Exception as e:
                    logger.warning(f"Could not create execution record: {e}")
            
            try:
                # Initialize execution service (browser + Stagehand)
                # Navigation will be handled by the first \"navigate\" step in test_steps,
                # which is interpreted by StagehandExecutionService._execute_step_simple
                await execution_service.initialize()

                # Execute using Phase 2 engine (3-tier strategy)
                # Note: StagehandExecutionService uses hybrid execution (Tier 1 → Tier 3)
                if execution_id and self.db:
                    # Full execution with database tracking
                    execution_result = await execution_service.execute_test(
                        db=self.db,
                        test_case=temp_test_case,
                        execution_id=execution_id,
                        user_id=1,
                        base_url=base_url,
                        environment="dev"
                    )
                    # Calculate success rate from database execution result
                    total_steps = execution_result.total_steps or len(test_steps)
                    passed_steps = execution_result.passed_steps or 0
                    success_rate = (passed_steps / total_steps) if total_steps > 0 else 0.0
                    final_result = execution_result.result.value if execution_result.result else "unknown"
                else:
                    # Real execution without database (still executes, just doesn't save records)
                    logger.info(f"Real execution for scenario {scenario.get('scenario_id')} (no database tracking)")
                    logger.info(f"Executing {len(test_steps)} steps: {test_steps}")
                    
                    # Execute steps manually without database
                    total_steps = len(test_steps)
                    passed_steps = 0
                    failed_steps = 0
                    
                    # Track which tier was used
                    tier_used = "tier1"  # Default to Tier 1 (Playwright)
                    
                    for idx, step_desc in enumerate(test_steps, start=1):
                        try:
                            logger.info(f"Executing step {idx}/{total_steps}: {step_desc}")
                            # Use hybrid execution (Tier 1 → Tier 3)
                            result = await execution_service._execute_step_hybrid(step_desc, idx)
                            if result.get("success", False):
                                passed_steps += 1
                                # Track tier used (from action_method if available)
                                action_method = result.get("action_method", "")
                                if "tier3" in action_method or "stagehand_ai" in action_method:
                                    tier_used = "tier3"  # Tier 3: Full AI was used
                                elif "tier2" in action_method or "observe" in action_method.lower():
                                    tier_used = "tier2"  # Tier 2: Observe + Playwright was used
                                elif "tier1" in action_method or "playwright" in action_method.lower() or not action_method:
                                    if tier_used not in ["tier2", "tier3"]:
                                        tier_used = "tier1"  # Tier 1: Direct Playwright was used
                                logger.info(f"Step {idx} PASSED (tier: {action_method or 'tier1'})")
                            else:
                                failed_steps += 1
                                error_msg = result.get("error", "Unknown error")
                                actual = result.get("actual", "No details")
                                logger.warning(f"Step {idx} FAILED: {error_msg} | Actual: {actual}")
                        except Exception as step_error:
                            logger.warning(f"Step {idx} EXCEPTION: {step_error}", exc_info=True)
                            failed_steps += 1
                    
                    # Calculate success rate for real execution without database
                    success_rate = (passed_steps / total_steps) if total_steps > 0 else 0.0
                    final_result = "pass" if success_rate >= 0.8 else "fail"
                    execution_result = None  # No database record, but execution happened
                
                # Determine tier used (for database execution, default to hybrid)
                if execution_id and self.db:
                    tier_used = "hybrid"  # StagehandExecutionService uses hybrid (Tier 1 → Tier 3)
                # tier_used is already set from the loop above for non-database execution
                
                logger.info(f"Scenario {scenario.get('scenario_id')} executed: "
                          f"{passed_steps}/{total_steps} passed, success_rate={success_rate:.2f}, tier={tier_used}")
                
                return {
                    "scenario_id": scenario.get("scenario_id"),
                    "success_rate": success_rate,
                    "passed_steps": passed_steps,
                    "total_steps": total_steps,
                    "result": final_result,
                    "execution_id": execution_id,
                    "tier_used": tier_used
                }
                
            except Exception as e:
                logger.error(f"Execution failed for scenario {scenario.get('scenario_id')}: {e}", exc_info=True)
                return {
                    "scenario_id": scenario.get("scenario_id"),
                    "success_rate": 0.0,
                    "passed_steps": 0,
                    "total_steps": len(test_steps),
                    "result": "fail",
                    "error": str(e),
                    "tier_used": "error"  # Mark as error tier
                }
            finally:
                # Cleanup
                try:
                    await execution_service.cleanup()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Real-time execution setup failed: {e}")
            return None
    
    def _convert_scenario_to_steps(self, scenario: Dict, page_context: Optional[Dict] = None) -> List[str]:
        """
        Convert BDD scenario (Given/When/Then) to executable test steps.
        
        Example:
        Given: "User is on login page"
        When: "User enters email and password, clicks Login"
        Then: "User is redirected to dashboard"
        
        Converts to:
        - Navigate to login page
        - Enter email: test@example.com
        - Enter password: password123
        - Click Login button
        - Verify URL contains /dashboard
        """
        steps = []
        
        # Debug: Log what we received
        logger.debug(f"_convert_scenario_to_steps: page_context={page_context}")
        
        # Priority: Always add navigation from page_context URL if available (most reliable)
        if page_context and page_context.get("url"):
            url = page_context["url"]
            logger.debug(f"Found URL in page_context: {url}")
            # Only add navigation if URL is valid
            if url.startswith("http://") or url.startswith("https://"):
                nav_step = f"Navigate to {url}"
                steps.append(nav_step)  # Add at beginning
                logger.debug(f"Added navigation step: {nav_step}")
            else:
                logger.warning(f"URL in page_context is not valid HTTP(S) URL: {url}")
        else:
            logger.warning(f"No URL found in page_context. page_context keys: {list(page_context.keys()) if page_context else 'None'}")
        
        # Given: Preconditions → Navigate/setup (only if no URL was added above)
        given = scenario.get("given", "")
        url_was_added = bool(page_context and page_context.get("url") and page_context["url"].startswith(("http://", "https://")))
        if given and not url_was_added:
            given_lower = given.lower()
            if "on" in given_lower and "page" in given_lower:
                # Extract page name from "User is on {page} page"
                page_match = re.search(r'on\s+([^,\s]+)\s+page', given_lower)
                if page_match:
                    page_name = page_match.group(1)
                    steps.append(f"Navigate to {page_name} page")
                else:
                    steps.append(f"Navigate to page: {given}")
            elif "navigate" in given_lower or "go to" in given_lower:
                steps.append(given)
        
        # When: Actions → Click, type, navigate
        when = scenario.get("when", "")
        if when:
            # Parse actions from "when" clause
            # Simple heuristic: split by commas, detect action verbs
            when_parts = [p.strip() for p in when.split(",")]
            
            # If only one part, try to break it down into multiple steps
            if len(when_parts) == 1:
                single_action = when_parts[0]
                part_lower = single_action.lower()
                
                # Try to extract multiple actions from a single sentence
                # Pattern: "User does X, then Y, then Z" or "User does X and Y and Z"
                # Check for "and" or "then" connectors
                if " and " in single_action or " then " in single_action:
                    # Split by "and" or "then"
                    sub_actions = re.split(r'\s+(?:and|then)\s+', single_action, flags=re.IGNORECASE)
                    for sub_action in sub_actions:
                        sub_action = sub_action.strip()
                        if sub_action:
                            # Remove "User" prefix if present
                            sub_action = re.sub(r'^User\s+', '', sub_action, flags=re.IGNORECASE)
                            steps.append(sub_action)
                # Check for multiple verbs in sequence
                elif any(word in part_lower for word in ["click", "select", "press", "enter", "type"]):
                    # Single action - add as is
                    # Remove "User" prefix if present for cleaner steps
                    clean_action = re.sub(r'^User\s+', '', single_action, flags=re.IGNORECASE)
                    steps.append(clean_action)
                else:
                    # Generic action
                    clean_action = re.sub(r'^User\s+', '', single_action, flags=re.IGNORECASE)
                    steps.append(clean_action)
            else:
                # Multiple comma-separated actions
                for part in when_parts:
                    part_lower = part.lower()
                    # Remove "User" prefix if present
                    clean_part = re.sub(r'^User\s+', '', part, flags=re.IGNORECASE)
                    if any(word in part_lower for word in ["enter", "type", "fill", "input"]):
                        steps.append(clean_part)  # e.g., "Enter email: test@example.com"
                    elif any(word in part_lower for word in ["click", "select", "press"]):
                        steps.append(clean_part)  # e.g., "Click Login button"
                    elif any(word in part_lower for word in ["navigate", "go to", "open"]):
                        steps.append(clean_part)  # e.g., "Navigate to dashboard"
                    elif part.strip():
                        steps.append(clean_part)  # Include other actions
        
        # Then: Assertions → Verify, check, wait
        then = scenario.get("then", "")
        if then:
            if not then.lower().startswith("verify"):
                steps.append(f"Verify: {then}")
            else:
                steps.append(then)
        
        # If no steps generated, create a basic step from title
        if not steps:
            title = scenario.get("title", "")
            if title:
                steps.append(f"Execute: {title}")
            else:
                steps.append("Execute scenario")
        
        logger.debug(f"_convert_scenario_to_steps: Generated {len(steps)} steps: {steps}")
        return steps
    
    def _risk_score_to_dict(self, risk_score: RiskScore) -> Dict:
        """Convert RiskScore to dictionary"""
        return {
            "rpn": risk_score.rpn,
            "severity": risk_score.severity,
            "occurrence": risk_score.occurrence,
            "detection": risk_score.detection,
            "priority": risk_score.to_priority().value
        }
    
    def _estimate_token_usage(self, scenarios: List[Dict]) -> int:
        """Estimate token usage for LLM calls"""
        # Rough estimation: 1 token ≈ 4 characters
        input_chars = len(json.dumps(scenarios))
        # Output: risk assessments for each scenario
        output_chars = len(scenarios) * 200  # ~200 chars per assessment
        return int((input_chars + output_chars) / 4)

