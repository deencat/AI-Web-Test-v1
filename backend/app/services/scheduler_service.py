"""
In-process test scheduler using APScheduler.

Cross-platform (Windows / Linux / macOS) — no OS cron or Task Scheduler required.
Schedules are persisted in the `test_schedules` SQLite table and reloaded on every
server start, so they survive restarts automatically.

Usage:
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()   # called once from main.py startup
    scheduler_service.stop()    # called once from main.py shutdown (optional)
    scheduler_service.add_schedule(schedule)
    scheduler_service.remove_schedule(schedule_id)
"""
import json
import logging
import re
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


# ---------------------------------------------------------------------------
# Internal job function — runs in APScheduler's background thread
# ---------------------------------------------------------------------------

def _infer_target_url(test_case) -> Optional[str]:
    """Replicate the URL-inference logic from run_test_101_scheduled.sh."""
    test_data = test_case.test_data or {}
    if isinstance(test_data, str):
        try:
            test_data = json.loads(test_data)
        except Exception:
            test_data = {}

    if isinstance(test_data, dict):
        for key in ("base_url", "url", "target_url"):
            value = str(test_data.get(key) or "").strip()
            if value:
                return value

        detailed_steps = test_data.get("detailed_steps") or []
        if isinstance(detailed_steps, list):
            for step in detailed_steps:
                if not isinstance(step, dict):
                    continue
                if str(step.get("action") or "").lower() == "navigate":
                    for key in ("value", "url"):
                        value = str(step.get(key) or "").strip()
                        if value:
                            return value

    raw_steps = test_case.steps or []
    if isinstance(raw_steps, str):
        try:
            raw_steps = json.loads(raw_steps)
        except Exception:
            raw_steps = [raw_steps]

    for step in (raw_steps if isinstance(raw_steps, list) else []):
        match = _URL_PATTERN.search(str(step))
        if match:
            return match.group(0).rstrip(".,)")

    return None


def _run_scheduled_test(schedule_id: int) -> None:
    """
    APScheduler job — fires a queued test execution for the given schedule_id.
    This runs in a background thread; must create its own DB session.
    """
    from app.db.session import SessionLocal
    from app.models.test_schedule import TestSchedule
    from app.models.test_case import TestCase
    from app.crud import test_execution as crud_executions
    from app.services.execution_queue import get_execution_queue

    db = SessionLocal()
    try:
        schedule = db.query(TestSchedule).filter(TestSchedule.id == schedule_id).first()
        if not schedule or not schedule.enabled:
            logger.info(f"[Scheduler] Schedule {schedule_id} is disabled or missing — skipping")
            return

        # Resolve base_url
        base_url = schedule.base_url
        if not base_url:
            test_case = db.query(TestCase).filter(TestCase.id == schedule.test_case_id).first()
            if test_case:
                base_url = _infer_target_url(test_case) or ""

        # Create execution record
        execution = crud_executions.create_execution(
            db=db,
            test_case_id=schedule.test_case_id,
            user_id=schedule.user_id,
            browser=schedule.browser,
            environment=schedule.environment,
            base_url=base_url,
        )
        execution.triggered_by = "scheduled"
        execution.queued_at = datetime.utcnow()
        execution.priority = 5
        db.commit()

        # Hand off to the queue (same path as the HTTP endpoint)
        queue = get_execution_queue()
        queue.add_to_queue(
            execution_id=execution.id,
            test_case_id=schedule.test_case_id,
            user_id=schedule.user_id,
            priority=5,
        )

        # Record last trigger time
        schedule.last_triggered_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"[Scheduler] Triggered execution {execution.id} for schedule {schedule_id} "
            f"(test_case {schedule.test_case_id})"
        )
    except Exception:
        logger.exception(f"[Scheduler] Failed to trigger execution for schedule {schedule_id}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler service singleton
# ---------------------------------------------------------------------------

class _SchedulerService:
    """Singleton wrapper around APScheduler BackgroundScheduler."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return

        self._scheduler.start()
        self._started = True
        logger.info("[Scheduler] APScheduler started")

        # Reload all enabled schedules from DB
        self._load_from_db()

    def stop(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("[Scheduler] APScheduler stopped")

    # ------------------------------------------------------------------
    # DB reload on startup
    # ------------------------------------------------------------------

    def _load_from_db(self) -> None:
        from app.db.session import SessionLocal
        from app.crud.test_schedule import list_all_enabled_schedules

        db = SessionLocal()
        try:
            schedules = list_all_enabled_schedules(db)
            for s in schedules:
                self._add_job(s.id, s.schedule_type, s.interval_minutes, s.cron_expression)
            logger.info(f"[Scheduler] Loaded {len(schedules)} active schedule(s) from DB")
        except Exception:
            logger.exception("[Scheduler] Failed to load schedules from DB on startup")
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    def _job_id(self, schedule_id: int) -> str:
        return f"test_schedule_{schedule_id}"

    def _add_job(
        self,
        schedule_id: int,
        schedule_type: str,
        interval_minutes: Optional[int],
        cron_expression: Optional[str],
    ) -> None:
        job_id = self._job_id(schedule_id)

        # Remove stale job if it exists
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

        if schedule_type == "interval" and interval_minutes:
            trigger = IntervalTrigger(minutes=interval_minutes)
        elif schedule_type == "cron" and cron_expression:
            try:
                trigger = CronTrigger.from_crontab(cron_expression)
            except Exception as exc:
                logger.error(
                    f"[Scheduler] Invalid cron expression {cron_expression!r} "
                    f"for schedule {schedule_id}: {exc}"
                )
                return
        else:
            logger.error(f"[Scheduler] Schedule {schedule_id} has no valid trigger params — skipping")
            return

        self._scheduler.add_job(
            _run_scheduled_test,
            trigger=trigger,
            id=job_id,
            args=[schedule_id],
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f"[Scheduler] Added job for schedule {schedule_id} ({schedule_type})")

    def add_schedule(self, schedule) -> None:
        """Register a new (or updated) schedule with APScheduler."""
        if not self._started:
            return
        if schedule.enabled:
            self._add_job(
                schedule.id,
                schedule.schedule_type,
                schedule.interval_minutes,
                schedule.cron_expression,
            )

    def remove_schedule(self, schedule_id: int) -> None:
        """Remove the APScheduler job for a deleted/disabled schedule."""
        if not self._started:
            return
        job_id = self._job_id(schedule_id)
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(f"[Scheduler] Removed job for schedule {schedule_id}")

    def next_run_time(self, schedule_id: int) -> Optional[datetime]:
        """Return the next scheduled fire time (UTC) or None."""
        if not self._started:
            return None
        job = self._scheduler.get_job(self._job_id(schedule_id))
        return job.next_run_time if job else None

    def describe(self, schedule_type: str, interval_minutes: Optional[int], cron_expression: Optional[str]) -> str:
        """Human-readable description of a schedule trigger."""
        if schedule_type == "interval" and interval_minutes:
            if interval_minutes < 60:
                return f"Every {interval_minutes} minute{'s' if interval_minutes != 1 else ''}"
            hours = interval_minutes / 60
            if hours == int(hours):
                h = int(hours)
                return f"Every {h} hour{'s' if h != 1 else ''}"
            return f"Every {interval_minutes} minutes"
        if schedule_type == "cron" and cron_expression:
            return f"Cron: {cron_expression}"
        return "Unknown schedule"


scheduler_service = _SchedulerService()
