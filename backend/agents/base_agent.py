"""
BaseAgent - Abstract base class for all Phase 3 agents

Design Philosophy:
- Rich defaults (90% functionality in base class)
- Minimal abstractions (3 abstract methods)
- Dependency injection (stubs can be swapped for real implementations)
- Type hints for all methods
- Async-first design
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from enum import Enum
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentCapability:
    """
    Represents a capability that an agent can perform.
    
    Capabilities are used for:
    1. Agent discovery (find agents that can handle a task)
    2. Task routing (Contract Net Protocol bidding)
    3. Confidence scoring (how well can this agent handle this task)
    """
    
    def __init__(
        self, 
        name: str, 
        version: str, 
        confidence_threshold: float = 0.7,
        description: str = ""
    ):
        self.name = name
        self.version = version
        self.confidence_threshold = confidence_threshold
        self.description = description
    
    def __repr__(self) -> str:
        return f"AgentCapability(name={self.name}, version={self.version}, threshold={self.confidence_threshold})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "confidence_threshold": self.confidence_threshold,
            "description": self.description,
        }


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskContext:
    """
    Context for a task to be executed by an agent.
    
    Contains all information needed for task execution:
    - task_id: Unique identifier for tracking
    - task_type: Type of task (e.g., "code_analysis", "requirement_extraction")
    - payload: Task-specific data (e.g., code to analyze, requirements to extract)
    - conversation_id: Links task to a conversation/workflow
    - priority: Task priority (1-10, higher = more important)
    - metadata: Additional context (user_id, timestamp, etc.)
    """
    
    def __init__(
        self, 
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        conversation_id: str,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.conversation_id = conversation_id
        self.priority = priority
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
        self.status = TaskStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "conversation_id": self.conversation_id,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
        }
    
    def __repr__(self) -> str:
        return f"TaskContext(task_id={self.task_id}, type={self.task_type}, priority={self.priority})"


class TaskResult:
    """
    Result of task execution by an agent.
    
    Contains:
    - task_id: Links back to original task
    - success: Whether task completed successfully
    - result: Task output (agent-specific format)
    - error: Error message if failed
    - confidence: Agent's confidence in result (0.0-1.0)
    - execution_time_seconds: How long task took
    - metadata: Additional info (token usage, cache hits, etc.)
    """
    
    def __init__(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        confidence: float = 0.0,
        execution_time_seconds: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.success = success
        self.result = result or {}
        self.error = error
        self.confidence = confidence
        self.execution_time_seconds = execution_time_seconds
        self.metadata = metadata or {}
        self.completed_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "confidence": self.confidence,
            "execution_time_seconds": self.execution_time_seconds,
            "metadata": self.metadata,
            "completed_at": self.completed_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"TaskResult(task_id={self.task_id}, status={status}, confidence={self.confidence:.2f})"


class BaseAgent(ABC):
    """
    Abstract base class for all Phase 3 agents.
    
    Provides rich defaults:
    - Message loop for receiving tasks
    - Heartbeat for health monitoring
    - Agent registration
    - Metrics tracking (tasks completed, failed, etc.)
    - Graceful shutdown
    
    Subclasses must implement:
    1. capabilities() - Declare what this agent can do
    2. can_handle() - Determine if agent can handle a specific task
    3. execute_task() - Execute the task and return result
    
    Example Usage:
    ```python
    class ObservationAgent(BaseAgent):
        @property
        def capabilities(self) -> List[AgentCapability]:
            return [AgentCapability("code_analysis", "1.0.0")]
        
        async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
            if task.task_type == "code_analysis":
                return True, 0.9
            return False, 0.0
        
        async def execute_task(self, task: TaskContext) -> TaskResult:
            # Analyze code using AST
            ...
            return TaskResult(task.task_id, success=True, result={...})
    ```
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        priority: int,
        message_queue,  # MessageBus instance (stub or real)
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique agent identifier (e.g., "obs_1", "req_2")
            agent_type: Agent type (e.g., "observation", "requirements")
            priority: Agent priority (1-10, higher = more important)
            message_queue: MessageBus for pub/sub communication
            config: Agent-specific configuration
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.priority = priority
        self.message_queue = message_queue
        self.config = config or {}
        
        # State management
        self.accepting_requests = False
        self.active_tasks: Dict[str, TaskContext] = {}
        self._shutdown_event = asyncio.Event()
        
        # Metrics tracking
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time = 0.0
        self.started_at: Optional[datetime] = None
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_loop_task: Optional[asyncio.Task] = None
    
    # ========== ABSTRACT METHODS (MUST IMPLEMENT) ==========
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """
        Declare agent capabilities.
        
        Returns:
            List of capabilities this agent can perform
        
        Example:
            return [
                AgentCapability("code_analysis", "1.0.0", confidence_threshold=0.8),
                AgentCapability("complexity_scoring", "1.0.0", confidence_threshold=0.7)
            ]
        """
        pass
    
    @abstractmethod
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """
        Determine if agent can handle a task.
        
        Used for:
        1. Task routing (which agent should handle this task?)
        2. Contract Net Protocol bidding (confidence = bid amount)
        
        Args:
            task: Task context to evaluate
        
        Returns:
            Tuple of (can_handle: bool, confidence: float)
            - can_handle: True if agent can handle this task
            - confidence: 0.0-1.0, how confident agent is (used for bidding)
        
        Example:
            if task.task_type == "code_analysis":
                language = task.payload.get("language", "python")
                confidence = 0.9 if language == "python" else 0.6
                return True, confidence
            return False, 0.0
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        Execute a task and return result.
        
        This is where the agent's core logic lives.
        
        Args:
            task: Task context with all necessary data
        
        Returns:
            TaskResult with success status, result data, confidence, etc.
        
        Example:
            start_time = time.time()
            try:
                # Do the work
                result_data = await self._analyze_code(task.payload["code"])
                execution_time = time.time() - start_time
                
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=result_data,
                    confidence=0.85,
                    execution_time_seconds=execution_time
                )
            except Exception as e:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e)
                )
        """
        pass
    
    # ========== DEFAULT IMPLEMENTATIONS (RICH FUNCTIONALITY) ==========
    
    async def start(self) -> None:
        """
        Start the agent.
        
        - Registers agent with registry
        - Starts accepting requests
        - Starts heartbeat loop
        - Starts message loop
        """
        logger.info(f"Starting agent {self.agent_id} (type: {self.agent_type})")
        
        self.accepting_requests = True
        self.started_at = datetime.now(timezone.utc)
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._message_loop_task = asyncio.create_task(self._message_loop())
        
        logger.info(f"Agent {self.agent_id} started successfully")
    
    async def stop(self) -> None:
        """
        Graceful shutdown of agent.
        
        - Stop accepting new requests
        - Wait for active tasks to complete (with timeout)
        - Cancel background tasks
        - Deregister from registry
        """
        logger.info(f"Stopping agent {self.agent_id}...")
        
        self.accepting_requests = False
        self._shutdown_event.set()
        
        # Wait for active tasks (max 30 seconds)
        timeout = 30
        start_wait = datetime.now(timezone.utc)
        while self.active_tasks and (datetime.now(timezone.utc) - start_wait).total_seconds() < timeout:
            await asyncio.sleep(0.5)
        
        if self.active_tasks:
            logger.warning(f"Agent {self.agent_id} had {len(self.active_tasks)} active tasks at shutdown")
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._message_loop_task:
            self._message_loop_task.cancel()
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def _heartbeat_loop(self) -> None:
        """
        Send periodic heartbeats to registry.
        
        Heartbeats let the orchestrator know:
        - Agent is still alive
        - How many active tasks
        - Metrics (tasks completed, failed, etc.)
        """
        heartbeat_interval = self.config.get("heartbeat_interval_seconds", 30)
        
        while not self._shutdown_event.is_set():
            try:
                # In stub implementation, this does nothing
                # In real implementation, sends heartbeat to Redis
                logger.debug(f"Agent {self.agent_id} heartbeat: {len(self.active_tasks)} active tasks")
                await asyncio.sleep(heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for agent {self.agent_id}: {e}")
                await asyncio.sleep(heartbeat_interval)
    
    async def _message_loop(self) -> None:
        """
        Receive and process messages from message bus.
        
        Message types:
        - TASK: Execute a task
        - PING: Health check
        - SHUTDOWN: Graceful shutdown
        """
        while not self._shutdown_event.is_set():
            try:
                # In stub implementation, this waits for tasks manually added
                # In real implementation, receives from Redis Streams
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message loop error for agent {self.agent_id}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent metrics for monitoring.
        
        Returns:
            Dictionary with:
            - agent_id, agent_type, priority
            - tasks_completed, tasks_failed
            - active_tasks_count
            - uptime_seconds
            - average_execution_time
            - success_rate
        """
        uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds() if self.started_at else 0
        total_tasks = self.tasks_completed + self.tasks_failed
        success_rate = self.tasks_completed / total_tasks if total_tasks > 0 else 0.0
        avg_exec_time = self.total_execution_time / self.tasks_completed if self.tasks_completed > 0 else 0.0
        
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "priority": self.priority,
            "accepting_requests": self.accepting_requests,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "active_tasks_count": len(self.active_tasks),
            "uptime_seconds": uptime,
            "average_execution_time_seconds": avg_exec_time,
            "success_rate": success_rate,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
        }
    
    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id}, type={self.agent_type}, active_tasks={len(self.active_tasks)})"
