"""Background worker for Hermes QA Factory jobs (HF-1)."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud import test_execution as crud_executions
from app.db.session import SessionLocal
from app.models.factory_job import FactoryJob, FactoryJobStatus
from app.models.test_case import TestCase
from app.services.execution_queue import get_execution_queue
from app.services.factory_job_service import append_job_event, get_factory_job, set_job_status
from app.services.scheduler_service import _infer_target_url

logger = logging.getLogger(__name__)

SUPPORTED_JOB_TYPES = {"run_regression"}


def _parse_tags(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(t) for t in parsed]
        except json.JSONDecodeError:
            pass
        if "," in raw:
            return [t.strip() for t in raw.split(",") if t.strip()]
        return [raw] if raw else []
    return []


def _test_cases_matching_tags(db: Session, tags: List[str]) -> List[TestCase]:
    if not tags:
        return []
    tag_set = {t.lower() for t in tags}
    cases = db.query(TestCase).all()
    matched: List[TestCase] = []
    for case in cases:
        case_tags = {t.lower() for t in _parse_tags(case.tags)}
        if tag_set.intersection(case_tags):
            matched.append(case)
    return matched


def run_factory_job(job_id: str) -> None:
    """Execute a factory job in a background thread."""
    db = SessionLocal()
    try:
        job = get_factory_job(db, job_id)
        if not job:
            logger.error("[FactoryWorker] Job %s not found", job_id)
            return
        if job.status != FactoryJobStatus.QUEUED.value:
            logger.info("[FactoryWorker] Job %s skipped (status=%s)", job_id, job.status)
            return

        set_job_status(db, job, FactoryJobStatus.RUNNING)
        append_job_event(
            db,
            job_id,
            event_type="job_started",
            profile="factory_worker",
            message=f"Started {job.job_type}",
        )

        if job.job_type == "run_regression":
            _run_regression(db, job)
        else:
            set_job_status(
                db,
                job,
                FactoryJobStatus.FAILED,
                error_message=f"Unsupported job_type: {job.job_type}",
            )
            append_job_event(
                db,
                job_id,
                event_type="error",
                profile="factory_worker",
                message=f"Unsupported job_type: {job.job_type}",
            )
            return

        job = get_factory_job(db, job_id)
        if job and job.status == FactoryJobStatus.RUNNING.value:
            set_job_status(db, job, FactoryJobStatus.COMPLETED)
            append_job_event(
                db,
                job_id,
                event_type="job_complete",
                profile="factory_worker",
                message="Job completed successfully",
            )
    except Exception as exc:
        logger.exception("[FactoryWorker] Job %s failed", job_id)
        job = get_factory_job(db, job_id)
        if job:
            set_job_status(db, job, FactoryJobStatus.FAILED, error_message=str(exc))
            append_job_event(
                db,
                job_id,
                event_type="error",
                profile="factory_worker",
                message=str(exc),
            )
    finally:
        db.close()


def _run_regression(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    tags = params.get("tags") or ["regression"]
    if isinstance(tags, str):
        tags = [tags]

    user_id = job.created_by_user_id or 1
    cases = _test_cases_matching_tags(db, tags)

    append_job_event(
        db,
        job.id,
        event_type="regression_plan",
        profile="qa-dispatcher",
        message=f"Found {len(cases)} test(s) matching tags {tags}",
        payload_summary={"tags": tags, "test_count": len(cases)},
    )

    if not cases:
        append_job_event(
            db,
            job.id,
            event_type="warning",
            profile="qa-dispatcher",
            message="No active test cases matched the requested tags",
        )
        return

    queue = get_execution_queue()
    execution_ids: List[int] = []

    for case in cases:
        base_url = _infer_target_url(case) or ""
        execution = crud_executions.create_execution(
            db=db,
            test_case_id=case.id,
            user_id=user_id,
            browser=params.get("browser", "chromium"),
            environment=params.get("environment", "dev"),
            base_url=base_url,
        )
        execution.triggered_by = "factory_regression"
        execution.queued_at = datetime.utcnow()
        execution.priority = int(params.get("priority", 5))
        db.commit()

        queue.add_to_queue(
            execution_id=execution.id,
            test_case_id=case.id,
            user_id=user_id,
            priority=execution.priority,
        )
        execution_ids.append(execution.id)

        append_job_event(
            db,
            job.id,
            event_type="execute_test",
            profile="qa-dispatcher",
            message=f"Queued execution {execution.id} for test_case {case.id}",
            payload_summary={
                "test_case_id": case.id,
                "execution_id": execution.id,
                "title": case.title,
            },
        )

    append_job_event(
        db,
        job.id,
        event_type="regression_dispatched",
        profile="qa-reporter",
        message=f"Queued {len(execution_ids)} execution(s)",
        payload_summary={"execution_ids": execution_ids},
    )
