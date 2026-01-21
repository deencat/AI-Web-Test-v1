"""
MessageBusStub - In-memory message bus for development/testing

This is a STUB implementation that allows agents to be developed and tested
without Redis/Kafka/RabbitMQ dependencies.

Key Features:
- In-memory message storage (Python dict)
- Async API matching real implementation
- No external dependencies
- Fast for testing (no network calls)

When to use:
- Local development (no Redis installed)
- Unit testing (mock dependencies)
- Early Phase 3 development (before infrastructure ready)

Migration path:
When Developer B builds real infrastructure (Sprint 7), simply replace:
```python
# Before (stub)
from messaging.message_bus_stub import MessageBusStub
message_bus = MessageBusStub()

# After (real Redis)
from messaging.message_bus import MessageBus
message_bus = MessageBus(redis_client)
```

Agent code doesn't change - dependency injection pattern!
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from datetime import datetime
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class MessageBusStub:
    """
    In-memory message bus stub (no Redis required).
    
    Implements same interface as real MessageBus, but stores
    messages in memory instead of Redis Streams.
    
    Data structures:
    - streams: Dict[stream_name, deque(messages)]
    - consumer_groups: Dict[stream_name, Dict[group_name, consumers]]
    - pending_messages: Dict[consumer_id, List[messages]]
    """
    
    def __init__(self, max_messages_per_stream: int = 1000):
        """
        Initialize in-memory message bus.
        
        Args:
            max_messages_per_stream: Max messages per stream (prevents memory leak)
        """
        self.streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_messages_per_stream))
        self.consumer_groups: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
        self.pending_messages: Dict[str, List[Dict]] = defaultdict(list)
        self._message_counter = 0
        self._lock = asyncio.Lock()
        
        logger.info("MessageBusStub initialized (in-memory mode)")
    
    async def send_message(
        self, 
        stream_name: str, 
        message: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> str:
        """
        Send a message to a stream.
        
        Args:
            stream_name: Stream name (e.g., "agent_tasks", "agent_results")
            message: Message payload (must be JSON-serializable)
            message_id: Optional message ID (auto-generated if not provided)
        
        Returns:
            Message ID (e.g., "msg-123")
        
        Example:
            msg_id = await bus.send_message("agent_tasks", {
                "task_id": "task_123",
                "task_type": "code_analysis",
                "payload": {"code": "def hello(): pass"}
            })
        """
        async with self._lock:
            # Generate message ID
            if message_id is None:
                self._message_counter += 1
                message_id = f"msg-{self._message_counter}"
            
            # Store message in stream
            message_envelope = {
                "id": message_id,
                "data": message,
                "timestamp": datetime.utcnow().isoformat(),
                "stream": stream_name,
            }
            self.streams[stream_name].append(message_envelope)
            
            logger.debug(f"Sent message {message_id} to stream {stream_name}")
            return message_id
    
    async def receive_batch(
        self,
        stream_name: str,
        count: int = 10,
        timeout_ms: int = 5000,
        consumer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from a stream (blocking with timeout).
        
        Args:
            stream_name: Stream name to read from
            count: Max number of messages to receive
            timeout_ms: Timeout in milliseconds (blocks until messages or timeout)
            consumer_id: Optional consumer ID for tracking
        
        Returns:
            List of message envelopes (each has 'id', 'data', 'timestamp')
        
        Example:
            messages = await bus.receive_batch("agent_tasks", count=5, timeout_ms=1000)
            for msg in messages:
                print(f"Received: {msg['id']} -> {msg['data']}")
        """
        start_time = datetime.utcnow()
        timeout_seconds = timeout_ms / 1000.0
        
        while True:
            async with self._lock:
                # Get messages from stream
                messages = []
                stream = self.streams.get(stream_name, deque())
                
                # Pop messages from left (FIFO)
                while len(messages) < count and stream:
                    messages.append(stream.popleft())
                
                if messages:
                    # Track pending messages for this consumer
                    if consumer_id:
                        self.pending_messages[consumer_id].extend(messages)
                    
                    logger.debug(f"Consumer {consumer_id} received {len(messages)} messages from {stream_name}")
                    return messages
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                return []
            
            # Wait a bit before checking again
            await asyncio.sleep(0.1)
    
    async def create_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create a consumer group for a stream.
        
        Consumer groups allow multiple consumers to work together on the same stream.
        Each message is delivered to only one consumer in the group.
        
        Args:
            stream_name: Stream name
            group_name: Consumer group name
            start_id: Where to start reading ("0" = from beginning, "$" = new messages only)
        
        Returns:
            True if created, False if already exists
        
        Example:
            await bus.create_consumer_group("agent_tasks", "observation_agents")
        """
        async with self._lock:
            if group_name in self.consumer_groups[stream_name]:
                logger.debug(f"Consumer group {group_name} already exists for stream {stream_name}")
                return False
            
            self.consumer_groups[stream_name][group_name] = []
            logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            return True
    
    async def acknowledge_message(
        self,
        stream_name: str,
        consumer_id: str,
        message_id: str
    ) -> bool:
        """
        Acknowledge that a message has been processed.
        
        This removes the message from the pending list for this consumer.
        If not acknowledged, message will be redelivered on consumer failure.
        
        Args:
            stream_name: Stream name
            consumer_id: Consumer ID
            message_id: Message ID to acknowledge
        
        Returns:
            True if acknowledged, False if not found
        
        Example:
            result = await agent.execute_task(task)
            await bus.acknowledge_message("agent_tasks", "obs_1", task.task_id)
        """
        async with self._lock:
            pending = self.pending_messages.get(consumer_id, [])
            for i, msg in enumerate(pending):
                if msg["id"] == message_id:
                    pending.pop(i)
                    logger.debug(f"Acknowledged message {message_id} for consumer {consumer_id}")
                    return True
            
            logger.warning(f"Message {message_id} not found in pending for consumer {consumer_id}")
            return False
    
    async def get_stream_length(self, stream_name: str) -> int:
        """
        Get number of messages in a stream.
        
        Useful for monitoring queue depth.
        
        Args:
            stream_name: Stream name
        
        Returns:
            Number of messages in stream
        """
        async with self._lock:
            return len(self.streams.get(stream_name, []))
    
    async def get_pending_count(self, consumer_id: str) -> int:
        """
        Get number of pending (unacknowledged) messages for a consumer.
        
        High pending count may indicate:
        - Consumer is slow/stuck
        - Messages are failing to process
        - Consumer crashed without acknowledgment
        
        Args:
            consumer_id: Consumer ID
        
        Returns:
            Number of pending messages
        """
        async with self._lock:
            return len(self.pending_messages.get(consumer_id, []))
    
    async def clear_stream(self, stream_name: str) -> int:
        """
        Clear all messages from a stream.
        
        Useful for testing/cleanup.
        
        Args:
            stream_name: Stream name to clear
        
        Returns:
            Number of messages cleared
        """
        async with self._lock:
            stream = self.streams.get(stream_name, deque())
            count = len(stream)
            stream.clear()
            logger.info(f"Cleared {count} messages from stream {stream_name}")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.
        
        Returns:
            Dictionary with:
            - total_streams: Number of streams
            - total_messages: Total messages across all streams
            - streams: List of stream names with message counts
            - consumer_groups: List of consumer groups
            - pending_consumers: Number of consumers with pending messages
        """
        total_messages = sum(len(stream) for stream in self.streams.values())
        
        return {
            "type": "MessageBusStub (in-memory)",
            "total_streams": len(self.streams),
            "total_messages": total_messages,
            "streams": {
                name: len(stream) 
                for name, stream in self.streams.items()
            },
            "consumer_groups": {
                stream: list(groups.keys())
                for stream, groups in self.consumer_groups.items()
            },
            "pending_consumers": len([c for c, msgs in self.pending_messages.items() if msgs]),
        }
    
    def __repr__(self) -> str:
        return f"MessageBusStub(streams={len(self.streams)}, messages={sum(len(s) for s in self.streams.values())})"
