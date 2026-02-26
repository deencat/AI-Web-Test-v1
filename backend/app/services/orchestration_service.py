"""
Orchestration Service - Coordinates 4-Agent Workflow

This service coordinates the execution of the 4-agent workflow:
1. ObservationAgent - Crawls URL and extracts UI elements
2. RequirementsAgent - Generates BDD test scenarios
3. AnalysisAgent - Analyzes risks, ROI, and dependencies
4. EvolutionAgent - Generates executable test code

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


class _MockMessageQueue:
    """Minimal message queue for agents when run via API (no pub/sub)."""
    async def publish(self, *args, **kwargs):
        pass
    async def subscribe(self, *args, **kwargs):
        pass


class OrchestrationService:
    """
    Coordinates the 4-agent workflow with progress tracking.
    Creates agents on demand and runs Observation -> Requirements -> Analysis -> Evolution.
    """

    def __init__(self, progress_tracker=None):
        """
        Initialize OrchestrationService.

        Args:
            progress_tracker: ProgressTracker instance for emitting progress events
        """
        self.progress_tracker = progress_tracker

    def _create_agents(self, db=None):
        """Create agent instances with shared message queue and config. db used for Analysis + Evolution."""
        from agents.base_agent import TaskContext, TaskResult
        from agents.observation_agent import ObservationAgent
        from agents.requirements_agent import RequirementsAgent
        from agents.analysis_agent import AnalysisAgent
        from agents.evolution_agent import EvolutionAgent
        from app.core.config import settings

        mq = _MockMessageQueue()
        obs_config = {"use_llm": True, "max_depth": 1, "max_pages": 1}
        req_config = {"use_llm": True}
        ana_config = {
            "use_llm": True,
            "db": db,
            "enable_realtime_execution": getattr(settings, "ENABLE_ANALYSIS_REALTIME_EXECUTION", True),
        }
        evo_config = {"use_llm": True, "db": db}

        observation_agent = ObservationAgent(
            message_queue=mq, agent_id="api_observation", priority=8, config=obs_config
        )
        requirements_agent = RequirementsAgent(
            agent_id="api_requirements", agent_type="requirements", priority=5,
            message_queue=mq, config=req_config
        )
        analysis_agent = AnalysisAgent(
            agent_id="api_analysis", agent_type="analysis", priority=5,
            message_queue=mq, config=ana_config
        )
        evolution_agent = EvolutionAgent(
            agent_id="api_evolution", agent_type="evolution", priority=5,
            message_queue=mq, config=evo_config
        )
        return observation_agent, requirements_agent, analysis_agent, evolution_agent

    async def run_workflow(
        self,
        workflow_id: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the 4-agent workflow: Observation -> Requirements -> Analysis -> Evolution.
        Updates workflow store and emits progress events after each stage.
        """
        from agents.base_agent import TaskContext
        from app.services.workflow_store import update_state, set_state, get_state, is_cancel_requested

        url = str(request.get("url", ""))
        user_instruction = request.get("user_instruction") or ""
        depth = request.get("depth", 1)
        login_credentials = request.get("login_credentials") or {}
        gmail_credentials = request.get("gmail_credentials") or {}

        db = None
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
        except Exception as e:
            logger.warning(f"DB session not available: {e}. Evolution storage will be skipped.")

        observation_agent, requirements_agent, analysis_agent, evolution_agent = self._create_agents(db=db)

        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker

        # Total progress milestones per (event, agent) pair
        _STAGE_PROGRESS: Dict[tuple, float] = {
            ("agent_started",   "observation"):  0.05,
            ("agent_completed", "observation"):  0.25,
            ("agent_started",   "requirements"): 0.30,
            ("agent_completed", "requirements"): 0.50,
            ("agent_started",   "analysis"):     0.55,
            ("agent_completed", "analysis"):     0.75,
            ("agent_started",   "evolution"):    0.80,
            ("agent_completed", "evolution"):    0.95,
        }

        _STAGE_BOUNDS: Dict[str, tuple] = {
            "observation": (0.05, 0.25),
            "requirements": (0.30, 0.50),
            "analysis": (0.55, 0.75),
            "evolution": (0.80, 0.95),
        }

        def _emit(evt: str, data: dict):
            agent = data.get("agent")
            prog = _STAGE_PROGRESS.get((evt, agent))
            # Include total_progress in SSE payload so frontend can use it directly
            payload = {**data}
            if prog is not None:
                payload["total_progress"] = prog
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, payload))
            store_updates: Dict[str, Any] = {"current_agent": agent, "status": "running"}
            if prog is not None:
                store_updates["total_progress"] = prog
            update_state(workflow_id, **store_updates)

        def _emit_progress(agent: str, progress: float, message: Optional[str] = None, **extra: Any):
            progress = max(0.0, min(1.0, float(progress)))
            start, end = _STAGE_BOUNDS.get(agent, (0.0, 1.0))
            total_progress = start + ((end - start) * progress)

            payload: Dict[str, Any] = {
                "agent": agent,
                "progress": progress,
                "total_progress": total_progress,
            }
            if message:
                payload["message"] = message
            payload.update(extra)

            if pt:
                asyncio.create_task(pt.emit(workflow_id, "agent_progress", payload))

            update_state(
                workflow_id,
                current_agent=agent,
                status="running",
                total_progress=total_progress,
            )

        def _check_cancelled() -> bool:
            if not is_cancel_requested(workflow_id):
                return False
            if pt:
                asyncio.create_task(pt.emit(workflow_id, "workflow_failed", {"error": "Cancelled by user"}))
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "current_agent": None,
                "error": "Cancelled by user",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            if db:
                try:
                    db.close()
                except Exception:
                    pass
            return True

        try:
            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            # Stage 1: Observation
            _emit("agent_started", {"agent": "observation", "timestamp": started_at.isoformat()})
            obs_payload = {"url": url, "max_depth": depth}

            def _observation_progress(progress_data: Dict[str, Any]):
                data = dict(progress_data or {})
                stage_progress = data.pop("progress", 0.0)
                stage_message = data.pop("message", None)
                _emit_progress("observation", stage_progress, stage_message, **data)

            obs_payload["progress_callback"] = _observation_progress
            obs_payload["cancel_check"] = lambda: is_cancel_requested(workflow_id)

            if user_instruction:
                obs_payload["user_instruction"] = user_instruction
            if login_credentials:
                obs_payload["login_credentials"] = login_credentials
            if gmail_credentials:
                obs_payload["gmail_credentials"] = gmail_credentials
            obs_task = TaskContext(
                conversation_id=workflow_id,
                task_id=f"{workflow_id}-obs",
                task_type="ui_element_extraction",
                payload=obs_payload,
                priority=8,
            )
            observation_result = await observation_agent.execute_task(obs_task)

            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            if not observation_result.success:
                raise RuntimeError(observation_result.error or "Observation failed")
            obs_data = observation_result.result
            ui_elements = obs_data.get("ui_elements", [])
            _emit("agent_completed", {
                "agent": "observation",
                "elements_found": len(ui_elements),
                "duration_seconds": getattr(observation_result, "execution_time_seconds", None),
            })
            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            # Stage 2: Requirements
            _emit("agent_started", {"agent": "requirements"})
            _emit_progress("requirements", 0.1, "Preparing requirement extraction...")
            observation_data = {
                "ui_elements": ui_elements,
                "page_structure": obs_data.get("page_structure", {}),
                "page_context": obs_data.get("page_context", {}),
            }
            if "url" not in observation_data["page_context"]:
                observation_data["page_context"]["url"] = url
            req_payload = {**observation_data}

            def _requirements_progress(progress_data: Dict[str, Any]):
                data = dict(progress_data or {})
                stage_progress = data.pop("progress", 0.0)
                stage_message = data.pop("message", None)
                _emit_progress("requirements", stage_progress, stage_message, **data)

            req_payload["progress_callback"] = _requirements_progress
            req_payload["cancel_check"] = lambda: is_cancel_requested(workflow_id)

            if user_instruction:
                req_payload["user_instruction"] = user_instruction
            req_task = TaskContext(
                conversation_id=workflow_id,
                task_id=f"{workflow_id}-req",
                task_type="requirement_extraction",
                payload=req_payload,
                priority=5,
            )
            requirements_result = await requirements_agent.execute_task(req_task)

            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            if not requirements_result.success:
                raise RuntimeError(requirements_result.error or "Requirements failed")
            scenarios = requirements_result.result.get("scenarios", [])
            _emit("agent_completed", {
                "agent": "requirements",
                "scenarios_generated": len(scenarios),
                "duration_seconds": getattr(requirements_result, "execution_time_seconds", None),
            })
            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            # Stage 3: Analysis
            _emit("agent_started", {"agent": "analysis"})
            _emit_progress("analysis", 0.1, "Preparing risk analysis...")
            def _analysis_progress(progress_data: Dict[str, Any]):
                data = dict(progress_data or {})
                stage_progress = data.pop("progress", 0.0)
                stage_message = data.pop("message", None)
                _emit_progress("analysis", stage_progress, stage_message, **data)

            analysis_task = TaskContext(
                conversation_id=workflow_id,
                task_id=f"{workflow_id}-ana",
                task_type="risk_analysis",
                payload={
                    "scenarios": scenarios,
                    "test_data": requirements_result.result.get("test_data", []),
                    "coverage_metrics": requirements_result.result.get("coverage_metrics", {}),
                    "page_context": observation_data["page_context"],
                    "progress_callback": _analysis_progress,
                    "cancel_check": lambda: is_cancel_requested(workflow_id),
                },
                priority=5,
            )
            analysis_result = await analysis_agent.execute_task(analysis_task)

            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            if not analysis_result.success:
                raise RuntimeError(analysis_result.error or "Analysis failed")
            _emit("agent_completed", {
                "agent": "analysis",
                "duration_seconds": getattr(analysis_result, "execution_time_seconds", None),
            })
            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            # Stage 4: Evolution
            _emit("agent_started", {"agent": "evolution"})
            _emit_progress("evolution", 0.1, "Preparing test generation...")
            evolution_payload = {
                "scenarios": scenarios,
                "risk_scores": analysis_result.result.get("risk_scores", []),
                "final_prioritization": analysis_result.result.get("final_prioritization", []),
                "page_context": observation_data["page_context"],
                "test_data": requirements_result.result.get("test_data", []),
                "db": db,
            }

            def _evolution_progress(progress_data: Dict[str, Any]):
                data = dict(progress_data or {})
                stage_progress = data.pop("progress", 0.0)
                stage_message = data.pop("message", None)
                _emit_progress("evolution", stage_progress, stage_message, **data)

            evolution_payload["progress_callback"] = _evolution_progress
            evolution_payload["cancel_check"] = lambda: is_cancel_requested(workflow_id)

            if user_instruction:
                evolution_payload["user_instruction"] = user_instruction
            if login_credentials:
                evolution_payload["login_credentials"] = login_credentials
            if gmail_credentials:
                evolution_payload["gmail_credentials"] = gmail_credentials
            evolution_task = TaskContext(
                conversation_id=workflow_id,
                task_id=f"{workflow_id}-evo",
                task_type="test_generation",
                payload=evolution_payload,
                priority=5,
            )
            evolution_result = await evolution_agent.execute_task(evolution_task)

            if _check_cancelled():
                return {"workflow_id": workflow_id, "status": "cancelled"}

            if not evolution_result.success:
                raise RuntimeError(evolution_result.error or "Evolution failed")
            test_case_ids = evolution_result.result.get("test_case_ids", [])
            test_count = evolution_result.result.get("test_count", 0)
            _emit("agent_completed", {
                "agent": "evolution",
                "tests_generated": test_count,
                "duration_seconds": getattr(evolution_result, "execution_time_seconds", None),
            })

            completed_at = datetime.now(timezone.utc)
            total_duration = (completed_at - started_at).total_seconds()
            if pt:
                await pt.emit(workflow_id, "workflow_completed", {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "test_case_ids": test_case_ids,
                    "test_count": test_count,
                    "total_duration_seconds": total_duration,
                })

            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "completed",
                "current_agent": None,
                "progress": {},
                "total_progress": 1.0,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "error": None,
                "result": {
                    "test_case_ids": test_case_ids,
                    "test_count": test_count,
                    "observation_result": obs_data,
                    "requirements_result": requirements_result.result,
                    "analysis_result": analysis_result.result,
                    "evolution_result": evolution_result.result,
                    "total_duration_seconds": total_duration,
                },
            })

            if db:
                try:
                    db.close()
                except Exception:
                    pass

            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": {
                    "test_case_ids": test_case_ids,
                    "test_count": test_count,
                    "total_duration_seconds": total_duration,
                },
            }
        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed: {e}")
            if pt:
                await pt.emit(workflow_id, "workflow_failed", {"error": str(e)})
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            if db:
                try:
                    db.close()
                except Exception:
                    pass
            raise

    async def run_observation_only(
        self,
        workflow_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run only ObservationAgent; persist observation_result in workflow store.
        Use workflow_id to chain into requirements/analysis/evolution later.
        """
        from agents.base_agent import TaskContext

        url = str(request.get("url", ""))
        user_instruction = request.get("user_instruction") or ""
        depth = request.get("depth", 1)
        login_credentials = request.get("login_credentials") or {}
        gmail_credentials = request.get("gmail_credentials") or {}
        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker

        def _emit(evt: str, data: dict):
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, data))
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

        observation_agent, _, _, _ = self._create_agents(db=None)
        _emit("agent_started", {"agent": "observation", "timestamp": started_at.isoformat()})
        obs_payload = {"url": url, "max_depth": depth}
        if user_instruction:
            obs_payload["user_instruction"] = user_instruction
        if login_credentials:
            obs_payload["login_credentials"] = login_credentials
        if gmail_credentials:
            obs_payload["gmail_credentials"] = gmail_credentials
        obs_task = TaskContext(
            conversation_id=workflow_id,
            task_id=f"{workflow_id}-obs",
            task_type="ui_element_extraction",
            payload=obs_payload,
            priority=8,
        )
        observation_result = await observation_agent.execute_task(obs_task)
        if not observation_result.success:
            _emit("agent_completed", {"agent": "observation", "error": observation_result.error})
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": observation_result.error or "Observation failed",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "workflow_type": "observation",
            })
            raise RuntimeError(observation_result.error or "Observation failed")
        obs_data = observation_result.result
        ui_elements = obs_data.get("ui_elements", [])
        _emit("agent_completed", {
            "agent": "observation",
            "elements_found": len(ui_elements),
            "duration_seconds": getattr(observation_result, "execution_time_seconds", None),
        })
        completed_at = datetime.now(timezone.utc)
        total_duration = (completed_at - started_at).total_seconds()
        if pt:
            await pt.emit(workflow_id, "workflow_completed", {
                "workflow_id": workflow_id,
                "status": "completed",
                "workflow_type": "observation",
                "total_duration_seconds": total_duration,
            })
        set_state(workflow_id, {
            "workflow_id": workflow_id,
            "status": "completed",
            "current_agent": None,
            "progress": {},
            "total_progress": 1.0,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "error": None,
            "workflow_type": "observation",
            "result": {
                "observation_result": obs_data,
                "test_case_ids": [],
                "test_count": 0,
                "total_duration_seconds": total_duration,
            },
        })
        return {"workflow_id": workflow_id, "status": "completed", "observation_result": obs_data}

    async def run_requirements_after_observation(
        self,
        workflow_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run RequirementsAgent. Input: workflow_id (with observation_result in store) or inline observation_result.
        Persists requirements_result in workflow store.
        """
        from agents.base_agent import TaskContext

        user_instruction = request.get("user_instruction") or ""
        obs_from_store = None
        source_wid = request.get("workflow_id") or workflow_id
        state = get_state(source_wid)
        if state:
            obs_from_store = (state.get("result") or {}).get("observation_result")
        observation_result = request.get("observation_result") or obs_from_store
        if not observation_result:
            raise ValueError("Missing observation data: provide workflow_id (with prior observation) or observation_result")
        ui_elements = observation_result.get("ui_elements", [])
        page_context = observation_result.get("page_context", {})
        url = str(request.get("url") or page_context.get("url") or "")
        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker

        def _emit(evt: str, data: dict):
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, data))
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

        _, requirements_agent, _, _ = self._create_agents(db=None)
        _emit("agent_started", {"agent": "requirements"})
        observation_data = {
            "ui_elements": ui_elements,
            "page_structure": observation_result.get("page_structure", {}),
            "page_context": {**page_context, "url": url or page_context.get("url")},
        }
        if user_instruction:
            observation_data["user_instruction"] = user_instruction
        req_task = TaskContext(
            conversation_id=workflow_id,
            task_id=f"{workflow_id}-req",
            task_type="requirement_extraction",
            payload=observation_data,
            priority=5,
        )
        requirements_result = await requirements_agent.execute_task(req_task)
        if not requirements_result.success:
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": requirements_result.error or "Requirements failed",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "workflow_type": "requirements",
            })
            raise RuntimeError(requirements_result.error or "Requirements failed")
        scenarios = requirements_result.result.get("scenarios", [])
        _emit("agent_completed", {
            "agent": "requirements",
            "scenarios_generated": len(scenarios),
            "duration_seconds": getattr(requirements_result, "execution_time_seconds", None),
        })
        completed_at = datetime.now(timezone.utc)
        total_duration = (completed_at - started_at).total_seconds()
        if pt:
            await pt.emit(workflow_id, "workflow_completed", {
                "workflow_id": workflow_id,
                "status": "completed",
                "workflow_type": "requirements",
                "total_duration_seconds": total_duration,
            })
        state = get_state(workflow_id) or {}
        existing_result = state.get("result") or {}
        set_state(workflow_id, {
            **state,
            "workflow_id": workflow_id,
            "status": "completed",
            "current_agent": None,
            "total_progress": 1.0,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "error": None,
            "workflow_type": "requirements",
            "result": {
                **existing_result,
                "observation_result": observation_result,
                "requirements_result": requirements_result.result,
                "test_case_ids": [],
                "test_count": 0,
                "total_duration_seconds": total_duration,
            },
        })
        return {"workflow_id": workflow_id, "status": "completed", "requirements_result": requirements_result.result}

    async def run_analysis_after_requirements(
        self,
        workflow_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run AnalysisAgent. Input: workflow_id (with requirements + observation in store) or inline requirements_result + observation_result.
        Persists analysis_result in workflow store.
        """
        from agents.base_agent import TaskContext

        state = get_state(workflow_id) or {}
        existing_result = state.get("result") or {}
        requirements_result = request.get("requirements_result") or existing_result.get("requirements_result")
        observation_result = request.get("observation_result") or existing_result.get("observation_result")
        if request.get("workflow_id") and not requirements_result:
            other = get_state(request["workflow_id"])
            if other:
                existing_result = other.get("result") or {}
                requirements_result = existing_result.get("requirements_result")
                observation_result = observation_result or existing_result.get("observation_result")
        if not requirements_result or not observation_result:
            raise ValueError("Missing requirements/observation: provide workflow_id or inline requirements_result and observation_result")
        scenarios = requirements_result.get("scenarios", [])
        page_context = observation_result.get("page_context", {})
        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker

        def _emit(evt: str, data: dict):
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, data))
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

        db = None
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
        except Exception as e:
            logger.warning(f"DB session not available for analysis: {e}")
        _, _, analysis_agent, _ = self._create_agents(db=db)
        _emit("agent_started", {"agent": "analysis"})
        try:
            analysis_task = TaskContext(
                conversation_id=workflow_id,
                task_id=f"{workflow_id}-ana",
                task_type="risk_analysis",
                payload={
                    "scenarios": scenarios,
                    "test_data": requirements_result.get("test_data", []),
                    "coverage_metrics": requirements_result.get("coverage_metrics", {}),
                    "page_context": page_context,
                },
                priority=5,
            )
            analysis_result = await analysis_agent.execute_task(analysis_task)
            if not analysis_result.success:
                set_state(workflow_id, {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "error": analysis_result.error or "Analysis failed",
                    "started_at": started_at.isoformat(),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "workflow_type": "analysis",
                })
                raise RuntimeError(analysis_result.error or "Analysis failed")
            _emit("agent_completed", {
                "agent": "analysis",
                "duration_seconds": getattr(analysis_result, "execution_time_seconds", None),
            })
            completed_at = datetime.now(timezone.utc)
            total_duration = (completed_at - started_at).total_seconds()
            if pt:
                await pt.emit(workflow_id, "workflow_completed", {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "workflow_type": "analysis",
                    "total_duration_seconds": total_duration,
                })
            set_state(workflow_id, {
                **state,
                "workflow_id": workflow_id,
                "status": "completed",
                "current_agent": None,
                "total_progress": 1.0,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "error": None,
                "workflow_type": "analysis",
                "result": {
                    **existing_result,
                    "observation_result": observation_result,
                    "requirements_result": requirements_result,
                    "analysis_result": analysis_result.result,
                    "test_case_ids": [],
                    "test_count": 0,
                    "total_duration_seconds": total_duration,
                },
            })
            return {"workflow_id": workflow_id, "status": "completed", "analysis_result": analysis_result.result}
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass

    async def run_evolution_after_analysis(
        self,
        workflow_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run EvolutionAgent (test generation). Input: workflow_id (with analysis + requirements + observation in store) or inline payload.
        Persists evolution_result and test_case_ids in workflow store.
        """
        from agents.base_agent import TaskContext

        db = None
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
        except Exception as e:
            logger.warning(f"DB session not available: {e}")
        state = get_state(workflow_id) or {}
        existing_result = state.get("result") or {}
        analysis_result = request.get("analysis_result") or existing_result.get("analysis_result")
        requirements_result = request.get("requirements_result") or existing_result.get("requirements_result")
        observation_result = request.get("observation_result") or existing_result.get("observation_result")
        if request.get("workflow_id") and not analysis_result:
            other = get_state(request["workflow_id"])
            if other:
                existing_result = other.get("result") or {}
                analysis_result = existing_result.get("analysis_result")
                requirements_result = requirements_result or existing_result.get("requirements_result")
                observation_result = observation_result or existing_result.get("observation_result")
        if not analysis_result or not requirements_result or not observation_result:
            raise ValueError("Missing analysis/requirements/observation: provide workflow_id or inline payloads")
        scenarios = requirements_result.get("scenarios", [])
        page_context = observation_result.get("page_context", {})
        user_instruction = request.get("user_instruction") or ""
        login_credentials = request.get("login_credentials") or {}
        gmail_credentials = request.get("gmail_credentials") or {}
        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker

        def _emit(evt: str, data: dict):
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, data))
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

        _, _, _, evolution_agent = self._create_agents(db=db)
        _emit("agent_started", {"agent": "evolution"})
        evolution_payload = {
            "scenarios": scenarios,
            "risk_scores": analysis_result.get("risk_scores", []),
            "final_prioritization": analysis_result.get("final_prioritization", []),
            "page_context": page_context,
            "test_data": requirements_result.get("test_data", []),
            "db": db,
        }
        if user_instruction:
            evolution_payload["user_instruction"] = user_instruction
        if login_credentials:
            evolution_payload["login_credentials"] = login_credentials
        if gmail_credentials:
            evolution_payload["gmail_credentials"] = gmail_credentials
        evolution_task = TaskContext(
            conversation_id=workflow_id,
            task_id=f"{workflow_id}-evo",
            task_type="test_generation",
            payload=evolution_payload,
            priority=5,
        )
        try:
            evolution_result = await evolution_agent.execute_task(evolution_task)
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass
        if not evolution_result.success:
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": evolution_result.error or "Evolution failed",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "workflow_type": "evolution",
            })
            raise RuntimeError(evolution_result.error or "Evolution failed")
        test_case_ids = evolution_result.result.get("test_case_ids", [])
        test_count = evolution_result.result.get("test_count", 0)
        _emit("agent_completed", {
            "agent": "evolution",
            "tests_generated": test_count,
            "duration_seconds": getattr(evolution_result, "execution_time_seconds", None),
        })
        completed_at = datetime.now(timezone.utc)
        total_duration = (completed_at - started_at).total_seconds()
        if pt:
            await pt.emit(workflow_id, "workflow_completed", {
                "workflow_id": workflow_id,
                "status": "completed",
                "test_case_ids": test_case_ids,
                "test_count": test_count,
                "total_duration_seconds": total_duration,
            })
        set_state(workflow_id, {
            **state,
            "workflow_id": workflow_id,
            "status": "completed",
            "current_agent": None,
            "total_progress": 1.0,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "error": None,
            "workflow_type": "evolution",
            "result": {
                **existing_result,
                "observation_result": observation_result,
                "requirements_result": requirements_result,
                "analysis_result": analysis_result,
                "evolution_result": evolution_result.result,
                "test_case_ids": test_case_ids,
                "test_count": test_count,
                "total_duration_seconds": total_duration,
            },
        })
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "test_case_ids": test_case_ids,
            "test_count": test_count,
            "evolution_result": evolution_result.result,
        }

    async def run_iterative_workflow(
        self,
        workflow_id: str,
        request: Dict[str, Any],
        max_iterations: int = 5,
        goal_indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run iterative improvement workflow (Sprint 10 Task 10A.8).
        
        Enhanced workflow:
        1. ObservationAgent crawls multi-page flow using browser-use
        2. RequirementsAgent generates test cases from all pages
        3. AnalysisAgent runs tests and scores
        4. EvolutionAgent generates improved test cases based on scoring
        5. Loop: EvolutionAgent → AnalysisAgent (up to max_iterations) until goal reached
        
        Args:
            workflow_id: Unique workflow identifier
            request: GenerateTestsRequest data (url, user_instruction, login_credentials, etc.)
            max_iterations: Maximum number of improvement iterations (default: 5)
            goal_indicators: List of strings indicating goal achievement (e.g., ["confirmation", "order ID"])
        
        Returns:
            Dict containing final workflow results with iteration history
        
        Implementation: Sprint 10 Task 10A.8 (improve-tests path: test_case_ids → evolution→analysis loop).
        """
        from agents.base_agent import TaskContext
        from app.services.workflow_store import update_state, set_state, get_state, is_cancel_requested

        test_case_ids = request.get("test_case_ids") or []
        user_instruction = (request.get("user_instruction") or "").strip()
        if not test_case_ids:
            raise ValueError("run_iterative_workflow requires test_case_ids (improve-tests path)")

        db = None
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
        except Exception as e:
            logger.warning(f"DB session not available: {e}")
            raise ValueError("Database required for iterative improvement workflow") from e

        from app.crud.test_case import get_test_case

        def _test_cases_to_scenarios(tcs: List[Any]) -> List[Dict[str, Any]]:
            """Build scenario-like dicts for analysis/evolution from TestCase list."""
            scenarios = []
            for tc in tcs:
                steps = tc.steps if isinstance(tc.steps, list) else []
                when = " | ".join(steps) if steps else (tc.description or "")
                scenarios.append({
                    "scenario_id": str(tc.id),
                    "title": tc.title or "",
                    "given": tc.description or "",
                    "when": when,
                    "then": tc.expected_result or "",
                })
            return scenarios

        # Load initial test cases
        test_cases = []
        for tid in test_case_ids:
            tc = get_test_case(db, int(tid))
            if not tc:
                raise ValueError(f"Test case not found: {tid}")
            test_cases.append(tc)

        current_scenarios = _test_cases_to_scenarios(test_cases)
        page_context: Dict[str, Any] = {}
        requirements_result = {
            "scenarios": current_scenarios,
            "test_data": [],
            "coverage_metrics": {},
        }
        observation_result = {"page_context": page_context}

        started_at = datetime.now(timezone.utc)
        pt = self.progress_tracker
        iteration_history: List[Dict[str, Any]] = []
        best_score = 0.0
        final_test_case_ids = list(test_case_ids)
        previous_analysis: Dict[str, Any] = {}

        def _emit(evt: str, data: dict):
            if pt:
                asyncio.create_task(pt.emit(workflow_id, evt, data))
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

        def _check_cancelled() -> bool:
            if not is_cancel_requested(workflow_id):
                return False
            if pt:
                asyncio.create_task(pt.emit(workflow_id, "workflow_failed", {"error": "Cancelled by user"}))
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "current_agent": None,
                "error": "Cancelled by user",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "workflow_type": "improve",
                "result": {
                    "test_case_ids": final_test_case_ids,
                    "iteration_history": iteration_history,
                    "iterations_completed": len(iteration_history),
                },
            })
            return True

        update_state(workflow_id, status="running", workflow_type="improve")
        _, _, analysis_agent, evolution_agent = self._create_agents(db=db)
        try:
            for iteration in range(1, max_iterations + 1):
                logger.info(f"[Iterative] Iteration {iteration}/{max_iterations}")

                if _check_cancelled():
                    return {"workflow_id": workflow_id, "status": "cancelled", "iteration_history": iteration_history}

                # Evolution: improve tests from current scenarios + prior analysis + user_instruction
                _emit("agent_started", {"agent": "evolution", "iteration": iteration})
                evolution_payload = {
                    "scenarios": current_scenarios,
                    "risk_scores": previous_analysis.get("risk_scores", []),
                    "final_prioritization": previous_analysis.get("final_prioritization", []),
                    "page_context": page_context,
                    "test_data": requirements_result.get("test_data", []),
                }
                if user_instruction:
                    evolution_payload["user_instruction"] = user_instruction
                evolution_task = TaskContext(
                    conversation_id=workflow_id,
                    task_id=f"{workflow_id}-evo-{iteration}",
                    task_type="test_generation",
                    payload=evolution_payload,
                    priority=5,
                )
                evolution_result = await evolution_agent.execute_task(evolution_task)
                if not evolution_result.success:
                    set_state(workflow_id, {
                        "workflow_id": workflow_id,
                        "status": "failed",
                        "error": evolution_result.error or "Evolution failed",
                        "started_at": started_at.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "workflow_type": "improve",
                        "result": {"iteration_history": iteration_history},
                    })
                    raise RuntimeError(evolution_result.error or "Evolution failed")

                new_test_case_ids = evolution_result.result.get("test_case_ids", [])
                _emit("agent_completed", {"agent": "evolution", "iteration": iteration, "test_count": len(new_test_case_ids)})

                if _check_cancelled():
                    return {"workflow_id": workflow_id, "status": "cancelled", "iteration_history": iteration_history}

                # Load new test cases for analysis (and next evolution round)
                next_test_cases = []
                for tid in new_test_case_ids:
                    tc = get_test_case(db, int(tid))
                    if tc:
                        next_test_cases.append(tc)
                if next_test_cases:
                    current_scenarios = _test_cases_to_scenarios(next_test_cases)
                    final_test_case_ids = list(new_test_case_ids)
                requirements_result["scenarios"] = current_scenarios

                # Analysis: score current scenarios
                _emit("agent_started", {"agent": "analysis", "iteration": iteration})
                analysis_task = TaskContext(
                    conversation_id=workflow_id,
                    task_id=f"{workflow_id}-ana-{iteration}",
                    task_type="risk_analysis",
                    payload={
                        "scenarios": current_scenarios,
                        "test_data": requirements_result.get("test_data", []),
                        "coverage_metrics": requirements_result.get("coverage_metrics", {}),
                        "page_context": page_context,
                    },
                    priority=5,
                )
                analysis_result = await analysis_agent.execute_task(analysis_task)
                if not analysis_result.success:
                    set_state(workflow_id, {
                        "workflow_id": workflow_id,
                        "status": "failed",
                        "error": analysis_result.error or "Analysis failed",
                        "started_at": started_at.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "workflow_type": "improve",
                        "result": {"iteration_history": iteration_history},
                    })
                    raise RuntimeError(analysis_result.error or "Analysis failed")

                previous_analysis = analysis_result.result or {}
                risk_list = previous_analysis.get("risk_scores", [])
                # Simple score: lower average RPN is better; normalize to 0-1 (e.g. 1 - min(1, avg_rpn/100))
                rpns = [r.get("rpn", 0) for r in risk_list if isinstance(r, dict)]
                avg_rpn = (sum(rpns) / len(rpns)) if rpns else 0
                score = max(0.0, 1.0 - (avg_rpn / 100.0))
                if score > best_score:
                    best_score = score
                iteration_history.append({
                    "iteration": iteration,
                    "test_case_ids": list(final_test_case_ids),
                    "test_count": len(final_test_case_ids),
                    "score": score,
                    "avg_rpn": avg_rpn,
                })
                _emit("agent_completed", {"agent": "analysis", "iteration": iteration, "score": score})

                # Convergence: stop at max_iterations or if score is high enough
                if iteration >= max_iterations or score >= 0.95:
                    logger.info(f"[Iterative] Stopping at iteration {iteration} (score={score}, max_iterations={max_iterations})")
                    break

            completed_at = datetime.now(timezone.utc)
            total_duration = (completed_at - started_at).total_seconds()
            result = {
                "test_case_ids": final_test_case_ids,
                "test_count": len(final_test_case_ids),
                "iteration_history": iteration_history,
                "iterations_completed": len(iteration_history),
                "best_score": best_score,
                "total_duration_seconds": total_duration,
            }
            if pt:
                await pt.emit(workflow_id, "workflow_completed", {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    **result,
                })
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "completed",
                "current_agent": None,
                "total_progress": 1.0,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "error": None,
                "workflow_type": "improve",
                "result": result,
            })
            return {"workflow_id": workflow_id, "status": "completed", **result}
        except Exception as e:
            logger.exception("Iterative workflow %s failed: %s", workflow_id, e)
            if pt:
                asyncio.create_task(pt.emit(workflow_id, "workflow_failed", {"error": str(e)}))
            set_state(workflow_id, {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "workflow_type": "improve",
                "result": {"iteration_history": iteration_history},
            })
            raise
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Workflow identifier
        
        Returns:
            True if cancelled successfully
        
        Status: STUB - Not yet implemented
        Implementation: Sprint 10 Day 8
        """
        logger.info(f"[STUB] OrchestrationService.cancel_workflow called for workflow {workflow_id}")
        
        # TODO: Sprint 10 Day 8 Implementation
        # - Mark workflow as cancelled in database
        # - Stop agent execution if possible
        # - Emit workflow_cancelled event
        
        return False  # STUB: Always returns False


def get_orchestration_service() -> OrchestrationService:
    """
    Dependency injection function for OrchestrationService.
    
    Returns:
        OrchestrationService instance
    """
    # TODO: Sprint 10 Days 6-7 - Initialize with ProgressTracker
    # from app.services.progress_tracker import get_progress_tracker
    # progress_tracker = get_progress_tracker()
    # return OrchestrationService(progress_tracker=progress_tracker)
    
    # STUB: Return service without dependencies
    return OrchestrationService()

