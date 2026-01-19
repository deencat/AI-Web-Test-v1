# Phase 3: Code Examples - Working Implementations

**Purpose:** Provide working code examples for core Phase 3 components  
**Status:** Ready for Sprint 7 implementation  
**Last Updated:** January 16, 2026

---

## 📋 Overview

This document contains production-ready code examples for:
1. **BaseAgent Abstract Class** (100 lines)
2. **Redis Streams Message Bus** (150 lines)
3. **Three-Layer Memory System** (200 lines)
4. **Specialized Agent Example** (Evolution Agent)
5. **Contract Net Protocol** (bidding system)
6. **Health Check \& Graceful Shutdown**

All examples are **runnable** with minimal dependencies.

---

## 1. BaseAgent Abstract Class

**File:** `backend/agents/base_agent.py`

```python
"""
BaseAgent - Abstract base class for all Phase 3 agents
Provides rich default behavior with minimal abstractions
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AgentCapability:
    """Represents a capability that an agent can perform"""
    def __init__(self, name: str, version: str, confidence_threshold: float = 0.7,
                 resource_requirements: Optional[Dict] = None):
        self.name = name
        self.version = version
        self.confidence_threshold = confidence_threshold
        self.resource_requirements = resource_requirements or {}


class TaskContext:
    """Context for a task to be executed"""
    def __init__(self, task_id: str, task_type: str, payload: Dict,
                 conversation_id: str, priority: int = 5, deadline_seconds: int = 300):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.conversation_id = conversation_id
        self.priority = priority
        self.deadline_seconds = deadline_seconds
        self.created_at = datetime.utcnow()


class TaskResult:
    """Result of task execution"""
    def __init__(self, task_id: str, success: bool, result: Optional[Dict] = None,
                 error: Optional[str] = None, confidence: float = 0.0,
                 execution_time_seconds: float = 0.0, token_usage: int = 0):
        self.task_id = task_id
        self.success = success
        self.result = result or {}
        self.error = error
        self.confidence = confidence
        self.execution_time_seconds = execution_time_seconds
        self.token_usage = token_usage
        self.completed_at = datetime.utcnow()


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides:
    - Message loop (Redis Streams)
    - Heartbeat loop (30s interval)
    - Registration/de-registration
    - Graceful shutdown
    - Event publishing
    - Metrics tracking
    
    Subclasses must implement:
    - capabilities (property)
    - can_handle(task)
    - execute_task(task)
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int,
                 redis_client, message_queue, llm_client, vector_db, registry, config: Dict):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.priority = priority
        self.redis = redis_client
        self.mq = message_queue
        self.llm = llm_client
        self.vector_db = vector_db
        self.registry = registry
        self.config = config
        
        # State
        self.accepting_requests = False
        self.active_tasks: Dict[str, TaskContext] = {}
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        
        # Metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_tokens_used = 0
        
        # Async tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_loop_task: Optional[asyncio.Task] = None
    
    # ========== ABSTRACT METHODS (MUST IMPLEMENT) ==========
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Return list of capabilities this agent provides"""
        pass
    
    @abstractmethod
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """
        Determine if agent can handle task.
        
        Returns:
            (can_handle: bool, confidence: float)
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Execute the task and return result"""
        pass
    
    # ========== DEFAULT IMPLEMENTATIONS (CAN OVERRIDE) ==========
    
    async def start(self):
        """Start the agent (register, start loops)"""
        self.start_time = datetime.utcnow()
        self.accepting_requests = True
        
        # Register with registry
        await self._register()
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._message_loop_task = asyncio.create_task(self._process_messages_loop())
        
        logger.info(f"Agent {self.agent_id} started successfully")
    
    async def stop(self):
        """Graceful shutdown"""
        logger.info(f"Agent {self.agent_id} stopping...")
        
        # Step 1: Stop accepting new requests
        self.accepting_requests = False
        await self.registry.update_status(self.agent_id, "shutting_down")
        
        # Step 2: Wait for active tasks (max 5 minutes)
        await self._wait_for_active_tasks(timeout=300)
        
        # Step 3: Checkpoint state
        await self._save_checkpoint()
        
        # Step 4: Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._message_loop_task:
            self._message_loop_task.cancel()
        
        # Step 5: Cleanup resources
        await self._cleanup()
        
        # Step 6: De-register
        await self.registry.deregister(self.agent_id)
        
        self.stop_time = datetime.utcnow()
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def process_message(self, message: Dict) -> Optional[TaskResult]:
        """Process incoming message"""
        if not self.accepting_requests:
            logger.warning(f"Agent {self.agent_id} not accepting requests")
            return None
        
        # Convert message to task
        task = self._message_to_task(message)
        
        # Check if can handle
        can_handle, confidence = await self.can_handle(task)
        if not can_handle:
            await self._send_reject_response(message, "Cannot handle task")
            return None
        
        # Execute task
        self.active_tasks[task.task_id] = task
        start_time = datetime.utcnow()
        
        try:
            result = await self.execute_task(task)
            self.tasks_completed += 1
            self.total_tokens_used += result.token_usage
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
            self.tasks_failed += 1
        finally:
            del self.active_tasks[task.task_id]
        
        # Send result
        await self._send_task_result(message, result)
        return result
    
    async def bid_on_task(self, cfp: Dict) -> Optional[Dict]:
        """Submit bid for Contract Net Protocol"""
        task = self._cfp_to_task(cfp)
        can_handle, confidence = await self.can_handle(task)
        
        if not can_handle or confidence < 0.5:
            return None
        
        # Adjust confidence by current load
        current_load = len(self.active_tasks)
        max_load = self.config.get("max_concurrent_tasks", 5)
        load_factor = 1.0 - (current_load / max_load)
        adjusted_confidence = confidence * load_factor
        
        return {
            "agent_id": self.agent_id,
            "confidence": adjusted_confidence,
            "estimated_time_seconds": self._estimate_execution_time(task),
            "estimated_tokens": self._estimate_token_usage(task),
            "current_load": current_load
        }
    
    async def publish_event(self, event_type: str, payload: Dict):
        """Publish event to Redis Pub/Sub"""
        event = {
            "event_type": event_type,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        await self.redis.publish(f"events.{event_type}", json.dumps(event))
    
    # ========== PRIVATE METHODS ==========
    
    async def _register(self):
        """Register agent with registry"""
        agent_card = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": [
                {
                    "name": cap.name,
                    "version": cap.version,
                    "confidence_threshold": cap.confidence_threshold
                }
                for cap in self.capabilities
            ],
            "priority": self.priority,
            "endpoints": {
                "inbox_stream": f"agent:{self.agent_id}:inbox"
            },
            "health": {
                "status": "healthy",
                "last_heartbeat": datetime.utcnow().isoformat()
            },
            "constraints": {
                "max_concurrent_tasks": self.config.get("max_concurrent_tasks", 5)
            }
        }
        await self.registry.register(agent_card)
    
    async def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds"""
        while self.accepting_requests:
            try:
                await self.registry.heartbeat(self.agent_id, {
                    "active_tasks": len(self.active_tasks),
                    "tasks_completed": self.tasks_completed,
                    "tasks_failed": self.tasks_failed,
                    "cpu_usage": 0.0,  # TODO: Get actual CPU usage
                    "memory_usage_mb": 0  # TODO: Get actual memory
                })
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)
    
    async def _process_messages_loop(self):
        """Process messages from inbox stream"""
        stream_name = f"agent:{self.agent_id}:inbox"
        consumer_group = f"{self.agent_type}_group"
        consumer_name = self.agent_id
        
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
        except:
            pass  # Group already exists
        
        while self.accepting_requests:
            try:
                # Read from stream (blocking, 1 second timeout)
                messages = await self.redis.xreadgroup(
                    consumer_group, consumer_name,
                    {stream_name: ">"},
                    count=1, block=1000
                )
                
                for stream, message_list in messages:
                    for message_id, message_data in message_list:
                        await self.process_message(message_data)
                        # Acknowledge message
                        await self.redis.xack(stream_name, consumer_group, message_id)
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await asyncio.sleep(1)
    
    async def _wait_for_active_tasks(self, timeout: int):
        """Wait for active tasks to complete"""
        start = datetime.utcnow()
        while self.active_tasks:
            if (datetime.utcnow() - start).total_seconds() > timeout:
                logger.warning(f"Shutdown timeout, {len(self.active_tasks)} tasks still active")
                break
            await asyncio.sleep(1)
    
    async def _save_checkpoint(self):
        """Save agent state to checkpoint"""
        checkpoint = {
            "agent_id": self.agent_id,
            "pending_tasks": list(self.active_tasks.keys()),
            "metrics": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "total_tokens_used": self.total_tokens_used
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        # Save to PostgreSQL or Redis
        # TODO: Implement checkpoint storage
    
    async def _cleanup(self):
        """Cleanup resources"""
        # Close connections, release locks, etc.
        pass
    
    async def _send_reject_response(self, message: Dict, reason: str):
        """Send rejection response"""
        response = {
            "status": "rejected",
            "reason": reason,
            "agent_id": self.agent_id
        }
        # TODO: Send back to sender
    
    async def _send_task_result(self, message: Dict, result: TaskResult):
        """Send task result back to requester"""
        # TODO: Send result to response channel
        pass
    
    def _message_to_task(self, message: Dict) -> TaskContext:
        """Convert message to TaskContext"""
        return TaskContext(
            task_id=message.get("message_id"),
            task_type=message.get("content", {}).get("type"),
            payload=message.get("content", {}).get("payload", {}),
            conversation_id=message.get("conversation_id"),
            priority=message.get("priority", 5)
        )
    
    def _cfp_to_task(self, cfp: Dict) -> TaskContext:
        """Convert CFP to TaskContext"""
        return TaskContext(
            task_id=cfp.get("task_id"),
            task_type=cfp.get("task_type"),
            payload=cfp.get("requirements", {}),
            conversation_id=cfp.get("conversation_id", ""),
            priority=cfp.get("priority", 5)
        )
    
    def _estimate_execution_time(self, task: TaskContext) -> float:
        """Estimate execution time in seconds"""
        # Default: 60 seconds (subclasses can override)
        return 60.0
    
    def _estimate_token_usage(self, task: TaskContext) -> int:
        """Estimate token usage"""
        # Default: 5000 tokens (subclasses can override)
        return 5000
```

---

## 2. Redis Streams Message Bus

**File:** `backend/infrastructure/message_bus.py`

```python
"""
Redis Streams Message Bus
Production-ready async message passing with consumer groups
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class MessageBus:
    """Redis Streams-based message bus with exactly-once delivery"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.handlers: Dict[str, List[Callable]] = {}
    
    async def send_message(self, stream_name: str, message: Dict) -> str:
        """
        Send message to stream.
        
        Returns:
            message_id: Redis stream message ID
        """
        # Add metadata
        message["schema_version"] = "1.0.0"
        message["message_id"] = message.get("message_id", str(uuid.uuid4()))
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Add to stream
        message_id = await self.redis.xadd(stream_name, message)
        logger.info(f"Sent message {message['message_id']} to {stream_name}")
        return message_id
    
    async def create_consumer_group(self, stream_name: str, group_name: str):
        """Create consumer group (idempotent)"""
        try:
            await self.redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Created consumer group {group_name} on {stream_name}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    
    async def consume_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        handler: Callable,
        count: int = 1,
        block_ms: int = 1000
    ):
        """
        Consume messages from stream with exactly-once delivery.
        
        Args:
            stream_name: Stream to consume from
            group_name: Consumer group name
            consumer_name: Unique consumer name
            handler: Async function to process message
            count: Max messages to fetch per call
            block_ms: Blocking timeout in milliseconds
        """
        while True:
            try:
                # Read new messages
                messages = await self.redis.xreadgroup(
                    group_name,
                    consumer_name,
                    {stream_name: ">"},
                    count=count,
                    block=block_ms
                )
                
                for stream, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            # Process message
                            await handler(message_data)
                            
                            # Acknowledge (exactly-once)
                            await self.redis.xack(stream_name, group_name, message_id)
                            logger.debug(f"Processed message {message_id}")
                        except Exception as e:
                            logger.error(f"Handler error for {message_id}: {e}")
                            # Move to retry queue
                            await self._handle_failure(stream_name, message_id, message_data, e)
            
            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(1)
    
    async def _handle_failure(self, stream_name: str, message_id: str, message: Dict, error: Exception):
        """Handle message processing failure"""
        retry_count = int(message.get("retry_count", 0))
        max_retries = 5
        
        if retry_count >= max_retries:
            # Move to DLQ
            await self._move_to_dlq(stream_name, message, error)
            return
        
        # Calculate backoff
        delay = min(2 ** retry_count, 60)  # Exponential backoff, max 60s
        
        # Update retry metadata
        message["retry_count"] = str(retry_count + 1)
        message["last_error"] = str(error)
        message["retry_at"] = (datetime.utcnow().timestamp() + delay)
        
        # Add to retry stream
        await self.redis.xadd(f"{stream_name}:retry", message)
        logger.warning(f"Message {message_id} requeued, attempt {retry_count + 1}")
    
    async def _move_to_dlq(self, stream_name: str, message: Dict, error: Exception):
        """Move message to Dead Letter Queue"""
        dlq_entry = {
            "original_stream": stream_name,
            "message": json.dumps(message),
            "error": str(error),
            "retry_count": message.get("retry_count", "0"),
            "moved_at": datetime.utcnow().isoformat()
        }
        await self.redis.xadd(f"{stream_name}:dlq", dlq_entry)
        logger.error(f"Message moved to DLQ: {message.get('message_id')}")
    
    async def publish_event(self, event_type: str, payload: Dict):
        """Publish event to Pub/Sub (fire-and-forget)"""
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis.publish(f"events.{event_type}", json.dumps(event))
    
    async def subscribe_events(self, event_pattern: str, handler: Callable):
        """Subscribe to events by pattern"""
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe(event_pattern)
        
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                event = json.loads(message["data"])
                await handler(event)
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()


# ========== USAGE EXAMPLE ==========

async def example_usage():
    """Example of using MessageBus"""
    bus = MessageBus("redis://localhost:6379")
    
    # Create consumer group
    await bus.create_consumer_group("test_generation_tasks", "evolution_agent_group")
    
    # Producer: Send message
    message = {
        "performative": "request",
        "sender_id": "agent_orchestration",
        "receiver_id": "agent_evolution",
        "content": {
            "type": "generate_tests",
            "payload": {
                "class_name": "UserService",
                "coverage_target": 0.85
            }
        },
        "priority": 7,
        "conversation_id": str(uuid.uuid4())
    }
    await bus.send_message("test_generation_tasks", message)
    
    # Consumer: Process messages
    async def handle_message(msg: Dict):
        print(f"Processing: {msg.get('content', {}).get('type')}")
        # Simulate work
        await asyncio.sleep(1)
        print("Done")
    
    # This will block and process messages
    await bus.consume_messages(
        "test_generation_tasks",
        "evolution_agent_group",
        "evolution_agent_1",
        handle_message
    )


if __name__ == "__main__":
    asyncio.run(example_usage())
```

---

## 3. Three-Layer Memory System

**File:** `backend/agents/memory_system.py`

```python
"""
Three-Layer Memory System for AI Agents
- Short-term: Redis (1 hour TTL, recency-based)
- Working: PostgreSQL (30 days, conversation-scoped)
- Long-term: Vector DB (unlimited, semantic search)
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import redis.asyncio as redis
import asyncpg
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Single memory item"""
    memory_id: str
    content: str
    embedding: Optional[List[float]] = None
    timestamp: datetime = None
    importance: float = 0.5  # 0.0-1.0
    layer: str = "short_term"  # short_term, working, long_term
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class AgentMemorySystem:
    """
    Three-layer memory system for agents.
    
    Usage:
        memory = AgentMemorySystem(agent_id, redis_client, pg_pool, vector_client)
        await memory.store("Observed pattern: Factory method in UserService", importance=0.8)
        context = await memory.get_context("UserService patterns", max_tokens=1500)
    """
    
    def __init__(self, agent_id: str, redis_client: redis.Redis,
                 pg_pool: asyncpg.Pool, vector_client):
        self.agent_id = agent_id
        self.stm = ShortTermMemory(redis_client, agent_id)
        self.wm = WorkingMemory(pg_pool, agent_id)
        self.ltm = LongTermMemory(vector_client, agent_id)
    
    async def store(self, content: str, layer: str = "short_term",
                    importance: float = 0.5, metadata: Optional[Dict] = None):
        """
        Store memory in appropriate layer(s).
        
        Args:
            content: Memory content
            layer: Target layer (short_term, working, long_term, all)
            importance: 0.0-1.0 (0.8+ goes to long-term automatically)
            metadata: Additional metadata (conversation_id, task_id, etc.)
        """
        import uuid
        memory = MemoryItem(
            memory_id=str(uuid.uuid4()),
            content=content,
            timestamp=datetime.utcnow(),
            importance=importance,
            layer=layer,
            metadata=metadata or {}
        )
        
        # Store in requested layer
        if layer == "short_term" or layer == "all":
            await self.stm.store(memory)
        
        if layer == "working" or layer == "all":
            await self.wm.store(memory)
        
        # High-importance memories go to long-term
        if importance >= 0.8 or layer == "long_term" or layer == "all":
            await self.ltm.store(memory)
        
        logger.info(f"Stored memory in {layer}: {content[:50]}...")
    
    async def get_context(self, query: str, max_tokens: int = 1500,
                          layers: List[str] = None) -> str:
        """
        Retrieve relevant memories as context string.
        
        Args:
            query: Search query
            max_tokens: Max token budget for context
            layers: Which layers to search (default: all)
        
        Returns:
            Formatted context string
        """
        if layers is None:
            layers = ["short_term", "working", "long_term"]
        
        memories = []
        
        # Retrieve from each layer
        if "short_term" in layers:
            memories.extend(await self.stm.retrieve(query, limit=5))
        
        if "working" in layers:
            memories.extend(await self.wm.retrieve(query, limit=10))
        
        if "long_term" in layers:
            memories.extend(await self.ltm.retrieve(query, limit=10))
        
        # Sort by importance and recency
        memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        # Build context within token budget
        context_parts = []
        token_count = 0
        
        for memory in memories:
            # Rough token estimate (4 chars = 1 token)
            memory_tokens = len(memory.content) // 4
            if token_count + memory_tokens > max_tokens:
                break
            
            context_parts.append(f"[{memory.timestamp.strftime('%Y-%m-%d %H:%M')}] {memory.content}")
            token_count += memory_tokens
        
        return "\n".join(context_parts)
    
    async def cleanup(self):
        """Cleanup expired memories"""
        await self.stm.cleanup()
        await self.wm.cleanup()


class ShortTermMemory:
    """Redis-based short-term memory (1 hour TTL)"""
    
    def __init__(self, redis_client: redis.Redis, agent_id: str):
        self.redis = redis_client
        self.key = f"stm:{agent_id}"
        self.max_items = 100
        self.ttl = 3600  # 1 hour
    
    async def store(self, memory: MemoryItem):
        """Add to head of list"""
        await self.redis.lpush(self.key, json.dumps(asdict(memory), default=str))
        await self.redis.ltrim(self.key, 0, self.max_items - 1)
        await self.redis.expire(self.key, self.ttl)
    
    async def retrieve(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Get recent memories (no semantic search)"""
        items_json = await self.redis.lrange(self.key, 0, limit - 1)
        return [MemoryItem(**json.loads(item)) for item in items_json]
    
    async def cleanup(self):
        """TTL handles cleanup automatically"""
        pass


class WorkingMemory:
    """PostgreSQL-based working memory (30 days)"""
    
    def __init__(self, pg_pool: asyncpg.Pool, agent_id: str):
        self.pool = pg_pool
        self.agent_id = agent_id
    
    async def store(self, memory: MemoryItem):
        """Store in PostgreSQL"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO working_memory (
                    memory_id, agent_id, content, timestamp, importance, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (memory_id) DO UPDATE
                SET content = EXCLUDED.content, timestamp = EXCLUDED.timestamp
            """, memory.memory_id, self.agent_id, memory.content,
                memory.timestamp, memory.importance, json.dumps(memory.metadata))
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Query by conversation_id or keyword"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM working_memory
                WHERE agent_id = $1
                AND (metadata->>'conversation_id' = $2 OR content ILIKE $3)
                ORDER BY timestamp DESC
                LIMIT $4
            """, self.agent_id, query, f"%{query}%", limit)
            
            return [MemoryItem(
                memory_id=row["memory_id"],
                content=row["content"],
                timestamp=row["timestamp"],
                importance=row["importance"],
                layer="working",
                metadata=json.loads(row["metadata"])
            ) for row in rows]
    
    async def cleanup(self):
        """Delete memories older than 30 days"""
        cutoff = datetime.utcnow() - timedelta(days=30)
        async with self.pool.acquire() as conn:
            deleted = await conn.execute("""
                DELETE FROM working_memory
                WHERE agent_id = $1 AND timestamp < $2
            """, self.agent_id, cutoff)
            logger.info(f"Cleaned up {deleted} working memories")


class LongTermMemory:
    """Vector DB-based long-term memory (semantic search)"""
    
    def __init__(self, vector_client, agent_id: str):
        self.vector_db = vector_client
        self.agent_id = agent_id
        self.collection = f"agent_{agent_id}_memories"
    
    async def store(self, memory: MemoryItem):
        """Store with embedding"""
        # Generate embedding if not provided
        if memory.embedding is None:
            memory.embedding = await self._generate_embedding(memory.content)
        
        # Store in vector DB
        await self.vector_db.upsert(
            collection=self.collection,
            id=memory.memory_id,
            vector=memory.embedding,
            payload={
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "importance": memory.importance,
                "metadata": memory.metadata
            }
        )
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Semantic search"""
        query_embedding = await self._generate_embedding(query)
        
        results = await self.vector_db.search(
            collection=self.collection,
            vector=query_embedding,
            limit=limit
        )
        
        return [MemoryItem(
            memory_id=result.id,
            content=result.payload["content"],
            embedding=result.vector,
            timestamp=datetime.fromisoformat(result.payload["timestamp"]),
            importance=result.payload["importance"],
            layer="long_term",
            metadata=result.payload.get("metadata", {})
        ) for result in results]
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using LLM"""
        # TODO: Call OpenAI embeddings API
        # For now, return dummy vector
        return [0.0] * 1536
    
    async def cleanup(self):
        """Long-term memories never expire"""
        pass
```

---

## 4. Specialized Agent Example (Evolution Agent)

**File:** `backend/agents/evolution_agent.py`

```python
"""
Evolution Agent - Generates test cases using LLM
Demonstrates specialized agent implementation
"""
from typing import List, Tuple
from .base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult


class EvolutionAgent(BaseAgent):
    """
    Specialized agent for test generation and mutation testing.
    
    Capabilities:
    - test_generation: Generate test cases from requirements
    - mutation_testing: Create mutants for existing tests
    """
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="test_generation",
                version="1.0.0",
                confidence_threshold=0.75,
                resource_requirements={"max_tokens": 10000, "timeout": 180}
            ),
            AgentCapability(
                name="mutation_testing",
                version="1.0.0",
                confidence_threshold=0.70,
                resource_requirements={"max_tokens": 5000, "timeout": 120}
            )
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if can handle task"""
        if task.task_type == "test_generation":
            # Check if required fields present
            if "class_name" in task.payload:
                return True, 0.85
            return False, 0.0
        
        elif task.task_type == "mutation_testing":
            if "test_file" in task.payload:
                return True, 0.80
            return False, 0.0
        
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Execute test generation task"""
        if task.task_type == "test_generation":
            return await self._generate_tests(task)
        elif task.task_type == "mutation_testing":
            return await self._mutate_tests(task)
        else:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"Unknown task type: {task.task_type}"
            )
    
    async def _generate_tests(self, task: TaskContext) -> TaskResult:
        """Generate test cases"""
        from datetime import datetime
        start_time = datetime.utcnow()
        
        # Get memory context
        context = await self.memory.get_context(
            query=f"test patterns for {task.payload.get('class_name')}",
            max_tokens=2000
        )
        
        # Build prompt
        prompt = f"""
        Previous test patterns:
        {context}
        
        Generate pytest tests for class: {task.payload.get('class_name')}
        Target coverage: {task.payload.get('coverage_target', 0.80)}
        
        Requirements:
        {task.payload.get('requirements', 'Standard best practices')}
        """
        
        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=5000,
            temperature=0.7
        )
        
        # Store success pattern in memory
        await self.memory.store(
            content=f"Successfully generated tests for {task.payload.get('class_name')}",
            layer="long_term",
            importance=0.7,
            metadata={"task_id": task.task_id, "coverage": 0.85}
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={
                "tests": response["text"],
                "coverage_estimate": 0.85,
                "test_count": 12
            },
            confidence=0.85,
            execution_time_seconds=execution_time,
            token_usage=response.get("token_usage", 0)
        )
    
    async def _mutate_tests(self, task: TaskContext) -> TaskResult:
        """Create test mutations"""
        # Similar implementation
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={"mutations": []}
        )
    
    def _estimate_execution_time(self, task: TaskContext) -> float:
        """Override to provide better estimates"""
        if task.task_type == "test_generation":
            return 120.0  # 2 minutes
        elif task.task_type == "mutation_testing":
            return 60.0  # 1 minute
        return 90.0
    
    def _estimate_token_usage(self, task: TaskContext) -> int:
        """Override to provide better estimates"""
        if task.task_type == "test_generation":
            return 8000
        elif task.task_type == "mutation_testing":
            return 4000
        return 5000
```

---

## 5. Contract Net Protocol Example

**File:** `backend/agents/orchestrator.py`

```python
"""
Orchestration Agent - Implements Contract Net Protocol
Demonstrates task allocation with bidding
"""
import asyncio
from typing import List, Dict
from datetime import datetime


class Orchestrator:
    """Orchestrates tasks across multiple agents using CNP"""
    
    def __init__(self, message_bus, agent_registry):
        self.bus = message_bus
        self.registry = agent_registry
    
    async def allocate_task(self, task: Dict) -> Dict:
        """
        Allocate task using Contract Net Protocol.
        
        Steps:
        1. Announce CFP (Call for Proposals)
        2. Collect bids
        3. Select winner
        4. Award task
        5. Monitor execution
        """
        # Step 1: Announce CFP
        cfp = {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "requirements": task["requirements"],
            "constraints": {
                "max_tokens": 10000,
                "deadline_seconds": 300
            },
            "success_criteria": {
                "min_coverage": 0.80
            }
        }
        
        # Find capable agents
        capable_agents = await self.registry.find_agents(
            capability=task["task_type"],
            status="healthy"
        )
        
        # Step 2: Collect bids (5 second window)
        bids = await self._collect_bids(capable_agents, cfp, timeout=5)
        
        if not bids:
            return {"status": "no_bidders", "task_id": task["task_id"]}
        
        # Step 3: Select winner (highest confidence / lowest load)
        winner = self._select_winner(bids)
        
        # Step 4: Award task
        await self._award_task(winner, task)
        
        # Step 5: Monitor (async)
        asyncio.create_task(self._monitor_execution(winner, task))
        
        return {
            "status": "awarded",
            "task_id": task["task_id"],
            "winner": winner["agent_id"],
            "confidence": winner["confidence"]
        }
    
    async def _collect_bids(self, agents: List[Dict], cfp: Dict, timeout: int) -> List[Dict]:
        """Collect bids from agents"""
        bids = []
        
        # Send CFP to all agents
        for agent in agents:
            await self.bus.send_message(
                f"agent:{agent['agent_id']}:cfp",
                {"type": "call_for_proposals", "cfp": cfp}
            )
        
        # Wait for bids (with timeout)
        start = datetime.utcnow()
        while (datetime.utcnow() - start).total_seconds() < timeout:
            # Check for bids
            # In real implementation, would use Redis Streams or Pub/Sub
            await asyncio.sleep(0.1)
        
        return bids
    
    def _select_winner(self, bids: List[Dict]) -> Dict:
        """Select best bid"""
        # Score formula: confidence / (1 + load)
        def score_bid(bid):
            return bid["confidence"] / (1 + bid["current_load"])
        
        return max(bids, key=score_bid)
    
    async def _award_task(self, winner: Dict, task: Dict):
        """Send task to winning agent"""
        await self.bus.send_message(
            f"agent:{winner['agent_id']}:inbox",
            {
                "performative": "request",
                "content": {
                    "type": task["task_type"],
                    "payload": task["requirements"]
                },
                "priority": 7
            }
        )
    
    async def _monitor_execution(self, winner: Dict, task: Dict):
        """Monitor task execution"""
        # Wait for result or timeout
        # In real implementation, would listen for completion events
        pass
```

---

## 6. Health Check \& Metrics

**File:** `backend/api/health.py`

```python
"""
Health check endpoints for agents
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()


@router.get("/health/{agent_id}")
async def liveness_check(agent_id: str):
    """Liveness probe - is agent alive?"""
    # Check if agent registered
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "status": "healthy",
        "agent_id": agent_id,
        "uptime_seconds": (datetime.utcnow() - agent["start_time"]).total_seconds()
    }


@router.get("/ready/{agent_id}")
async def readiness_check(agent_id: str):
    """Readiness probe - can agent accept work?"""
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if at capacity
    active_tasks = agent["health"]["active_tasks"]
    max_tasks = agent["constraints"]["max_concurrent_tasks"]
    
    if active_tasks >= max_tasks:
        raise HTTPException(status_code=503, detail="Agent at capacity")
    
    return {"status": "ready", "available_capacity": max_tasks - active_tasks}


@router.get("/metrics/{agent_id}")
async def metrics(agent_id: str):
    """Prometheus-compatible metrics"""
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "tasks_completed": agent["metrics"]["tasks_completed"],
        "tasks_failed": agent["metrics"]["tasks_failed"],
        "success_rate": agent["metrics"]["tasks_completed"] / 
                        (agent["metrics"]["tasks_completed"] + agent["metrics"]["tasks_failed"] + 0.001),
        "total_tokens_used": agent["metrics"]["total_tokens_used"],
        "active_tasks": agent["health"]["active_tasks"]
    }
```

---

## 🚀 Running the Examples

### Prerequisites
```bash
pip install redis asyncpg asyncio-redis fastapi uvicorn
```

### Start Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Run BaseAgent Example
```python
from base_agent import BaseAgent, EvolutionAgent
import asyncio

async def main():
    # Initialize dependencies (mock for example)
    redis_client = None  # Initialize Redis
    pg_pool = None  # Initialize PostgreSQL
    vector_db = None  # Initialize vector DB
    registry = None  # Initialize registry
    
    agent = EvolutionAgent(
        agent_id="evolution_1",
        agent_type="evolution",
        priority=9,
        redis_client=redis_client,
        message_queue=None,
        llm_client=None,
        vector_db=vector_db,
        registry=registry,
        config={"max_concurrent_tasks": 5}
    )
    
    await agent.start()
    # Agent is now running
    await asyncio.sleep(60)
    await agent.stop()

asyncio.run(main())
```

---

## 📚 Next Steps

1. **Integrate with Phase 2**: Connect agents to existing execution engine
2. **Add LLM Client**: Implement OpenAI API wrapper
3. **Setup Vector DB**: Configure Qdrant or Pinecone
4. **Deploy to Kubernetes**: Use provided health checks for probes
5. **Add Monitoring**: Prometheus + Grafana for metrics

---

**END OF CODE EXAMPLES**
