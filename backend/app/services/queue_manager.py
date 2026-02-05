"""
Queue Manager - Manages test execution queue and worker pool.

Handles concurrent execution, resource management, and automatic queue processing.
"""
import threading
import time
import logging
import json
from typing import Optional
from datetime import datetime

from app.services.execution_queue import get_execution_queue, QueuedExecution
from app.services.stagehand_factory import get_stagehand_adapter
from app.services.stagehand_adapter import StagehandAdapter
from app.db.session import SessionLocal
from app.crud import test_execution as crud_execution
from app.crud import test_case as crud_test
from app.crud import browser_profile as crud_profile
from app.models.test_execution import ExecutionStatus

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages the execution queue and worker pool.
    
    Handles:
    - Queue processing loop
    - Starting executions when slots available
    - Tracking active executions
    - Cleaning up completed executions
    """
    
    def __init__(self, max_concurrent: int = 5, check_interval: int = 2):
        """
        Initialize the queue manager.
        
        Args:
            max_concurrent: Maximum concurrent executions
            check_interval: How often to check queue (seconds)
        """
        self.max_concurrent = max_concurrent
        self.check_interval = check_interval
        self.queue = get_execution_queue(max_concurrent=max_concurrent)
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        logger.info(
            f"QueueManager initialized: max_concurrent={max_concurrent}, "
            f"check_interval={check_interval}s"
        )
    
    def start(self):
        """Start the queue processing worker."""
        if self._running:
            logger.warning("QueueManager already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self._worker_thread.start()
        
        logger.info("QueueManager worker started")
    
    def stop(self):
        """Stop the queue processing worker."""
        if not self._running:
            logger.warning("QueueManager not running")
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        
        logger.info("QueueManager worker stopped")
    
    def _process_queue_loop(self):
        """Main queue processing loop (runs in background thread)."""
        logger.info("Queue processing loop started")
        
        while self._running and not self._stop_event.is_set():
            try:
                self._check_and_start_next()
            except Exception as e:
                logger.error(f"Error in queue processing loop: {e}", exc_info=True)
            
            # Wait before next check
            self._stop_event.wait(self.check_interval)
        
        logger.info("Queue processing loop stopped")
    
    def _check_and_start_next(self):
        """Check if we can start next execution and do so if possible."""
        # Check if we're under the concurrent limit
        if not self.queue.is_under_limit():
            logger.debug(
                f"At concurrent limit ({self.queue.get_active_count()}/{self.max_concurrent}), "
                "waiting for executions to complete"
            )
            return
        
        # Get next execution from queue
        queued_execution = self.queue.get_next_execution()
        if not queued_execution:
            logger.debug("Queue is empty, nothing to start")
            return
        
        # Mark as active before starting
        if not self.queue.mark_as_active(queued_execution):
            logger.error(
                f"Failed to mark execution {queued_execution.execution_id} as active, "
                "re-queueing"
            )
            # Re-queue it
            self.queue.add_to_queue(
                queued_execution.execution_id,
                queued_execution.test_case_id,
                queued_execution.user_id,
                queued_execution.priority,
                http_credentials=queued_execution.http_credentials
            )
            return
        
        # Start execution in background
        self._start_execution_async(queued_execution)
    
    def _start_execution_async(self, queued_execution: QueuedExecution):
        """
        Start an execution in a background thread.
        
        Args:
            queued_execution: The execution to start
        """
        def run_execution():
            """Inner function to run in thread."""
            import asyncio
            import sys
            import signal
            from app.db.session import SessionLocal, engine
            from sqlalchemy.orm import scoped_session, sessionmaker
            
            logger.info(f"Starting execution {queued_execution.execution_id} from queue")
            
            # Patch signal.signal to be a no-op in threads
            original_signal = signal.signal
            signal.signal = lambda signalnum, handler: None
            
            try:
                # Set Windows event loop policy
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Create thread-local database session
                    ThreadSession = scoped_session(sessionmaker(bind=engine))
                    bg_db = ThreadSession()
                    
                    try:
                        # Get test case
                        test_case = crud_test.get_test_case(bg_db, queued_execution.test_case_id)
                        if not test_case:
                            logger.error(
                                f"Test case {queued_execution.test_case_id} not found "
                                f"for execution {queued_execution.execution_id}"
                            )
                            return
                        
                        # Get execution record
                        execution = crud_execution.get_execution(bg_db, queued_execution.execution_id)
                        if not execution:
                            logger.error(f"Execution {queued_execution.execution_id} not found")
                            return
                        
                        # Get base URL from test case or execution
                        base_url = execution.base_url or test_case.test_data.get("base_url", "https://example.com")

                        # Extract browser profile data (if provided)
                        browser_profile_data = None
                        browser_profile_id = None
                        if execution.trigger_details:
                            try:
                                trigger_details = json.loads(execution.trigger_details)
                                browser_profile_data = trigger_details.get("browser_profile_data")
                                browser_profile_id = trigger_details.get("browser_profile_id")
                            except Exception as e:
                                logger.warning(f"Failed to parse trigger_details JSON: {e}")

                        if browser_profile_id and not browser_profile_data:
                            try:
                                browser_profile_data = crud_profile.load_profile_session(
                                    db=bg_db,
                                    profile_id=browser_profile_id,
                                    user_id=queued_execution.user_id
                                )
                            except Exception as e:
                                logger.warning(f"Failed to load profile session data: {e}")

                        http_credentials = queued_execution.http_credentials
                        
                        # Load user's execution provider settings (Sprint 3 - Settings Page Dynamic Configuration)
                        from app.services.user_settings_service import user_settings_service
                        user_config = user_settings_service.get_provider_config(
                            db=bg_db,
                            user_id=queued_execution.user_id,
                            config_type="execution"
                        )
                        print(f"[DEBUG] 🎯 Loaded user execution config: provider={user_config['provider']}, model={user_config['model']}")
                        
                        # ========================================
                        # Sprint 5.5: Use NEW ExecutionService with 3-Tier System
                        # ========================================
                        from app.services.execution_service import ExecutionService, ExecutionConfig
                        
                        # TEMPORARY: Force headless=False to see browser during testing
                        headless = False  # TODO: Change back to env var after testing
                        
                        print(f"[DEBUG] Creating ExecutionService with 3-Tier system, headless={headless}")
                        
                        # Create ExecutionConfig
                        exec_config = ExecutionConfig(
                            browser=execution.browser or "chromium",
                            headless=headless,
                            timeout=30000  # 30 seconds
                        )
                        
                        # Create ExecutionService with config
                        service = ExecutionService(config=exec_config)
                        
                        # No separate initialize() call needed - ExecutionService handles it internally
                        
                        try:
                            loop.run_until_complete(
                                service.execute_test(
                                    db=bg_db,
                                    test_case=test_case,
                                    execution_id=queued_execution.execution_id,
                                    user_id=queued_execution.user_id,
                                    base_url=base_url,
                                    environment=execution.environment or "dev",
                                    browser_profile_data=browser_profile_data,
                                    http_credentials=http_credentials
                                )
                            )

                            if browser_profile_id:
                                profile = crud_profile.get_profile_by_user(
                                    db=bg_db,
                                    profile_id=browser_profile_id,
                                    user_id=queued_execution.user_id
                                )
                                if profile and profile.auto_sync:
                                    try:
                                        session_snapshot = loop.run_until_complete(
                                            service.export_profile_session()
                                        )
                                        if session_snapshot:
                                            crud_profile.sync_profile_session(
                                                db=bg_db,
                                                profile_id=browser_profile_id,
                                                user_id=queued_execution.user_id,
                                                session_data=session_snapshot
                                            )
                                    except Exception as e:
                                        logger.warning(f"Failed to auto-sync profile: {e}")
                            
                            # Commit final state
                            bg_db.commit()
                            logger.info(f"Execution {queued_execution.execution_id} completed successfully")
                        finally:
                            # Always clean up Stagehand/Playwright resources
                            try:
                                loop.run_until_complete(service.cleanup())
                            except Exception as e:
                                logger.warning(f"Error cleaning up Stagehand: {e}")
                        
                    except Exception as e:
                        logger.error(
                            f"Error executing test {queued_execution.execution_id}: {e}",
                            exc_info=True
                        )
                        bg_db.rollback()
                    finally:
                        bg_db.close()
                        ThreadSession.remove()
                finally:
                    loop.close()
            finally:
                # Restore original signal handler
                signal.signal = original_signal
                
                # Mark execution as complete in queue
                self.queue.mark_as_complete(queued_execution.execution_id)
                logger.info(
                    f"Execution {queued_execution.execution_id} finished, "
                    f"queue slot freed ({self.queue.get_active_count()}/{self.max_concurrent} active)"
                )
        
        # Start execution in new thread
        thread = threading.Thread(target=run_execution, daemon=True)
        thread.start()
    
    def get_statistics(self) -> dict:
        """
        Get queue manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "is_running": self._running,
            "max_concurrent": self.max_concurrent,
            "check_interval": self.check_interval,
            "queue_status": self.queue.get_queue_status()
        }


# Global queue manager instance
_manager_instance: Optional[QueueManager] = None
_manager_lock = threading.Lock()


def get_queue_manager(max_concurrent: int = 5, check_interval: int = 2) -> QueueManager:
    """
    Get or create the global queue manager instance.
    
    Args:
        max_concurrent: Maximum concurrent executions (only used on first call)
        check_interval: Queue check interval in seconds (only used on first call)
        
    Returns:
        QueueManager singleton instance
    """
    global _manager_instance
    
    with _manager_lock:
        if _manager_instance is None:
            _manager_instance = QueueManager(
                max_concurrent=max_concurrent,
                check_interval=check_interval
            )
            # Auto-start the queue manager
            _manager_instance.start()
            logger.info("Created and started global QueueManager instance")
        
        return _manager_instance


def start_queue_manager(max_concurrent: int = 5, check_interval: int = 2):
    """
    Start the global queue manager.
    
    Args:
        max_concurrent: Maximum concurrent executions
        check_interval: Queue check interval in seconds
    """
    manager = get_queue_manager(max_concurrent, check_interval)
    if not manager._running:
        manager.start()
        logger.info("Started QueueManager")


def stop_queue_manager():
    """Stop the global queue manager."""
    global _manager_instance
    
    if _manager_instance:
        _manager_instance.stop()
        logger.info("Stopped QueueManager")

