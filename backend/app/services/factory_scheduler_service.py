"""Cron scheduler for Hermes QA Factory loops (HF-1: regression only)."""
import logging
from concurrent.futures import ThreadPoolExecutor

from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.factory_job import FactoryJobCreate
from app.services.factory_job_service import create_factory_job
from app.services.factory_worker import run_factory_job
from app.services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="factory-worker")


def _enqueue_factory_job(job_type: str, params: dict) -> None:
    db = SessionLocal()
    try:
        body = FactoryJobCreate(
            job_type=job_type,
            project=params.get("project"),
            params=params,
        )
        job = create_factory_job(
            db,
            body,
            created_by_user_id=settings.FACTORY_SERVICE_USER_ID,
        )
        _executor.submit(run_factory_job, job.id)
        logger.info("[FactoryScheduler] Enqueued %s job %s", job_type, job.id)
    except Exception:
        logger.exception("[FactoryScheduler] Failed to enqueue %s", job_type)
    finally:
        db.close()


def _run_scheduled_regression() -> None:
    tags = [t.strip() for t in settings.FACTORY_REGRESSION_TAGS.split(",") if t.strip()]
    _enqueue_factory_job(
        "run_regression",
        {"tags": tags or ["regression"], "source": "factory_cron"},
    )


def register_factory_cron_jobs() -> None:
    """Register factory cron jobs on the shared APScheduler instance."""
    if not settings.FACTORY_SCHEDULER_ENABLED:
        logger.info("[FactoryScheduler] Disabled (FACTORY_SCHEDULER_ENABLED=false)")
        return

    scheduler = scheduler_service._scheduler
    if not scheduler_service._started:
        logger.warning("[FactoryScheduler] APScheduler not started — skipping factory cron registration")
        return

    job_id = "factory_regression_cron"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    try:
        trigger = CronTrigger.from_crontab(settings.FACTORY_REGRESSION_CRON, timezone="UTC")
    except ValueError as exc:
        logger.error("[FactoryScheduler] Invalid FACTORY_REGRESSION_CRON: %s", exc)
        return

    scheduler.add_job(
        _run_scheduled_regression,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "[FactoryScheduler] Registered regression cron: %s",
        settings.FACTORY_REGRESSION_CRON,
    )


def submit_factory_job_async(job_id: str) -> None:
    """Submit an already-created job to the worker pool."""
    _executor.submit(run_factory_job, job_id)
