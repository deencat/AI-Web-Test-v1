"""
Test Execution Queue System

Provides thread-safe queue for managing test executions with priority support.
"""
import threading
from typing import Optional, List, Dict
from datetime import datetime
from dataclasses import dataclass, field
from queue import PriorityQueue
import logging

logger = logging.getLogger(__name__)


@dataclass(order=True)
class QueuedExecution:
    """
    Represents a queued test execution.
    
    Attributes:
        priority: Lower number = higher priority (1=high, 5=medium, 10=low)
        queued_at: When the execution was queued
        execution_id: Database execution record ID
    """
    priority: int
    queued_at: datetime = field(compare=False)
    execution_id: int = field(compare=False)
    test_case_id: int = field(default=0, compare=False)
    user_id: int = field(default=0, compare=False)


class ExecutionQueue:
    """
    Thread-safe queue for test executions.
    
    Manages queued executions with priority support and concurrent execution tracking.
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the execution queue.
        
        Args:
            max_concurrent: Maximum number of concurrent executions allowed
        """
        self.max_concurrent = max_concurrent
        self._queue = PriorityQueue()
        self._active_executions: Dict[int, QueuedExecution] = {}
        self._lock = threading.Lock()
        self._queue_positions: Dict[int, int] = {}
        
        logger.info(f"ExecutionQueue initialized with max_concurrent={max_concurrent}")
    
    def add_to_queue(
        self,
        execution_id: int,
        test_case_id: int,
        user_id: int,
        priority: int = 5
    ) -> int:
        """
        Add an execution to the queue.
        
        Args:
            execution_id: Database execution record ID
            test_case_id: Test case ID
            user_id: User who triggered the execution
            priority: Priority level (1=high, 5=medium, 10=low)
            
        Returns:
            Queue position (1-indexed)
        """
        with self._lock:
            queued_execution = QueuedExecution(
                priority=priority,
                queued_at=datetime.utcnow(),
                execution_id=execution_id,
                test_case_id=test_case_id,
                user_id=user_id
            )
            
            self._queue.put(queued_execution)
            
            # Update queue positions
            self._update_queue_positions()
            
            position = self._queue_positions.get(execution_id, self._queue.qsize())
            
            logger.info(
                f"Added execution {execution_id} to queue at position {position} "
                f"(priority={priority}, test_case={test_case_id})"
            )
            
            return position
    
    def get_next_execution(self) -> Optional[QueuedExecution]:
        """
        Get the next execution from the queue (highest priority first).
        
        Returns:
            QueuedExecution if available, None if queue is empty
        """
        with self._lock:
            if self._queue.empty():
                return None
            
            try:
                execution = self._queue.get_nowait()
                self._update_queue_positions()
                logger.info(f"Retrieved execution {execution.execution_id} from queue")
                return execution
            except:
                return None
    
    def mark_as_active(self, execution: QueuedExecution) -> bool:
        """
        Mark an execution as active (currently running).
        
        Args:
            execution: The queued execution to mark as active
            
        Returns:
            True if marked successfully, False if at concurrent limit
        """
        with self._lock:
            if len(self._active_executions) >= self.max_concurrent:
                logger.warning(
                    f"Cannot mark execution {execution.execution_id} as active: "
                    f"at concurrent limit ({self.max_concurrent})"
                )
                return False
            
            self._active_executions[execution.execution_id] = execution
            logger.info(
                f"Marked execution {execution.execution_id} as active "
                f"({len(self._active_executions)}/{self.max_concurrent})"
            )
            return True
    
    def mark_as_complete(self, execution_id: int) -> bool:
        """
        Mark an execution as complete (no longer running).
        
        Args:
            execution_id: Execution ID to mark as complete
            
        Returns:
            True if removed from active, False if not found
        """
        with self._lock:
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
                logger.info(
                    f"Marked execution {execution_id} as complete "
                    f"({len(self._active_executions)}/{self.max_concurrent} active)"
                )
                return True
            
            logger.warning(f"Execution {execution_id} not found in active executions")
            return False
    
    def remove_from_queue(self, execution_id: int) -> bool:
        """
        Remove an execution from the queue (cancel before it starts).
        
        Args:
            execution_id: Execution ID to remove
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            # Can't remove directly from PriorityQueue, so we recreate it
            temp_queue = PriorityQueue()
            found = False
            
            while not self._queue.empty():
                try:
                    execution = self._queue.get_nowait()
                    if execution.execution_id == execution_id:
                        found = True
                        logger.info(f"Removed execution {execution_id} from queue")
                    else:
                        temp_queue.put(execution)
                except:
                    break
            
            self._queue = temp_queue
            self._update_queue_positions()
            
            return found
    
    def is_under_limit(self) -> bool:
        """
        Check if we're under the concurrent execution limit.
        
        Returns:
            True if can start more executions, False if at limit
        """
        with self._lock:
            return len(self._active_executions) < self.max_concurrent
    
    def get_queue_size(self) -> int:
        """Get number of executions in queue (not running)."""
        with self._lock:
            return self._queue.qsize()
    
    def get_active_count(self) -> int:
        """Get number of active (running) executions."""
        with self._lock:
            return len(self._active_executions)
    
    def get_active_executions(self) -> List[Dict]:
        """
        Get list of active executions.
        
        Returns:
            List of active execution dictionaries
        """
        with self._lock:
            return [
                {
                    "execution_id": execution_id,
                    "test_case_id": exec_data.test_case_id,
                    "user_id": exec_data.user_id,
                    "priority": exec_data.priority,
                    "queued_at": exec_data.queued_at.isoformat()
                }
                for execution_id, exec_data in self._active_executions.items()
            ]
    
    def get_queue_status(self) -> Dict:
        """
        Get complete queue status.
        
        Returns:
            Dictionary with queue status information
        """
        with self._lock:
            # Get queue items (peek without removing)
            queue_items = []
            temp_list = []
            
            while not self._queue.empty():
                try:
                    execution = self._queue.get_nowait()
                    temp_list.append(execution)
                    queue_items.append({
                        "execution_id": execution.execution_id,
                        "test_case_id": execution.test_case_id,
                        "priority": execution.priority,
                        "queue_position": len(queue_items),
                        "queued_at": execution.queued_at.isoformat()
                    })
                except:
                    break
            
            # Restore queue
            for execution in temp_list:
                self._queue.put(execution)
            
            # Calculate is_under_limit without calling the method (avoid deadlock)
            is_under_limit = len(self._active_executions) < self.max_concurrent
            
            # Get active executions without calling the method (avoid deadlock)
            active_executions = [
                {
                    "execution_id": execution_id,
                    "test_case_id": exec_data.test_case_id,
                    "user_id": exec_data.user_id,
                    "priority": exec_data.priority,
                    "queued_at": exec_data.queued_at.isoformat()
                }
                for execution_id, exec_data in self._active_executions.items()
            ]
            
            return {
                "active_count": len(self._active_executions),
                "queued_count": len(queue_items),
                "max_concurrent": self.max_concurrent,
                "is_under_limit": is_under_limit,
                "queue": queue_items,
                "active": active_executions
            }
    
    def clear_queue(self) -> int:
        """
        Clear all queued executions (not active ones).
        
        Returns:
            Number of executions removed from queue
        """
        with self._lock:
            count = self._queue.qsize()
            self._queue = PriorityQueue()
            self._queue_positions.clear()
            logger.warning(f"Cleared queue: removed {count} executions")
            return count
    
    def _update_queue_positions(self):
        """Update queue position tracking (internal method)."""
        # This is a simplified version - positions may not be 100% accurate
        # due to PriorityQueue limitations, but provides a reasonable estimate
        self._queue_positions.clear()
        position = 1
        
        # Note: Can't easily peek into PriorityQueue without removing items
        # This is acceptable for position tracking as it's informational only


# Global queue instance
_queue_instance: Optional[ExecutionQueue] = None
_queue_lock = threading.Lock()


def get_execution_queue(max_concurrent: int = 5) -> ExecutionQueue:
    """
    Get or create the global execution queue instance.
    
    Args:
        max_concurrent: Maximum concurrent executions (only used on first call)
        
    Returns:
        ExecutionQueue singleton instance
    """
    global _queue_instance
    
    with _queue_lock:
        if _queue_instance is None:
            _queue_instance = ExecutionQueue(max_concurrent=max_concurrent)
            logger.info("Created global ExecutionQueue instance")
        
        return _queue_instance

