"""Background worker for Hermes QA Factory jobs (HF-1, HF-3)."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import journey_factory as crud_journey
from app.crud import test_execution as crud_executions
from app.db.session import SessionLocal
from app.models.factory_job import FactoryJob, FactoryJobStatus
from app.models.journey_factory import BacklogStatus, JourneyBacklogItem
from app.models.test_case import TestCase
from app.services.execution_queue import get_execution_queue
from app.services.factory_job_service import append_job_event, get_factory_job, set_job_status
from app.services.factory_journey_service import (
    generate_journey_for_backlog_item,
    generate_journey_for_entry,
)
from app.services.factory_change_scan_service import scan_registry_changes
from app.services.factory_heal_service import scan_and_heal_failures
from app.services.factory_notification_service import notify_factory_job_complete
from app.services.scheduler_service import _infer_target_url

logger = logging.getLogger(__name__)

SUPPORTED_JOB_TYPES = {
    "run_regression",
    "drain_backlog",
    "generate_journey",
    "full_cycle",
    "scan_changes",
    "heal_failures",
}


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

        handlers = {
            "run_regression": _run_regression,
            "drain_backlog": _drain_backlog,
            "generate_journey": _generate_journey,
            "full_cycle": _full_cycle,
            "scan_changes": _scan_changes,
            "heal_failures": _heal_failures,
        }
        handler = handlers.get(job.job_type)
        if not handler:
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

        handler(db, job)

        job = get_factory_job(db, job_id)
        if job and job.status == FactoryJobStatus.RUNNING.value:
            set_job_status(db, job, FactoryJobStatus.COMPLETED)
            append_job_event(
                db,
                job_id,
                event_type="job_complete",
                profile="qa-reporter",
                message="Job completed successfully",
            )
            job = get_factory_job(db, job_id)
            if job:
                notify_factory_job_complete(db, job)
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
            job = get_factory_job(db, job_id)
            if job:
                notify_factory_job_complete(db, job)
    finally:
        db.close()


def _run_regression(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    tags = params.get("tags") or ["regression"]
    if isinstance(tags, str):
        tags = [tags]

    user_id = job.created_by_user_id or settings.FACTORY_SERVICE_USER_ID
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
        execution.triggered_by = params.get("triggered_by", "factory_regression")
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


def _drain_backlog(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    max_items = int(params.get("max_items", settings.FACTORY_LOOP_A_MAX_ITEMS))
    project = job.project or params.get("project")

    items = crud_journey.list_backlog_items(
        db,
        status=BacklogStatus.PENDING.value,
        project=project,
        limit=max_items,
    )

    append_job_event(
        db,
        job.id,
        event_type="backlog_drain_start",
        profile="qa-journey-planner",
        message=f"Processing {len(items)} pending backlog item(s)",
        payload_summary={"max_items": max_items, "count": len(items), "project": project},
    )

    if not items:
        append_job_event(
            db,
            job.id,
            event_type="backlog_empty",
            profile="qa-journey-planner",
            message="No pending backlog items",
        )
        return

    failed = 0
    for item in items:
        crud_journey.update_backlog_status(
            db,
            item.id,
            BacklogStatus.IN_PROGRESS.value,
            factory_job_id=job.id,
        )
        try:
            test_case_id = generate_journey_for_backlog_item(db, job, item)
            crud_journey.update_backlog_status(db, item.id, BacklogStatus.DONE.value)
            append_job_event(
                db,
                job.id,
                event_type="backlog_item_done",
                profile="qa-test-gen",
                message=f"Backlog #{item.id} → test_case_id={test_case_id}",
                payload_summary={
                    "backlog_id": item.id,
                    "journey_slug": item.journey_slug,
                    "test_case_id": test_case_id,
                },
            )
        except Exception as exc:
            failed += 1
            crud_journey.update_backlog_status(
                db,
                item.id,
                BacklogStatus.FAILED.value,
                error_message=str(exc),
            )
            append_job_event(
                db,
                job.id,
                event_type="backlog_item_failed",
                profile="qa-test-gen",
                message=f"Backlog #{item.id} failed: {exc}",
                payload_summary={"backlog_id": item.id, "error": str(exc)},
            )
            logger.exception("[FactoryWorker] Backlog item %s failed", item.id)

    if failed and failed == len(items):
        raise RuntimeError(f"All {failed} backlog item(s) failed")


def _generate_journey(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    project = job.project or params.get("project") or "Three-HK"

    if params.get("backlog_item_id"):
        item = db.query(JourneyBacklogItem).filter_by(id=int(params["backlog_item_id"])).first()
        if not item:
            raise ValueError(f"Backlog item {params['backlog_item_id']} not found")
        crud_journey.update_backlog_status(
            db, item.id, BacklogStatus.IN_PROGRESS.value, factory_job_id=job.id
        )
        try:
            test_case_id = generate_journey_for_backlog_item(db, job, item)
            crud_journey.update_backlog_status(db, item.id, BacklogStatus.DONE.value)
        except Exception as exc:
            crud_journey.update_backlog_status(
                db, item.id, BacklogStatus.FAILED.value, error_message=str(exc)
            )
            raise
        append_job_event(
            db,
            job.id,
            event_type="journey_generated",
            profile="qa-test-gen",
            message=f"Generated test_case_id={test_case_id}",
            payload_summary={"test_case_id": test_case_id, "backlog_id": item.id},
        )
        return

    slug = params.get("journey_slug")
    if not slug:
        raise ValueError("generate_journey requires journey_slug or backlog_item_id")

    entry = crud_journey.get_registry_by_slug(db, project, slug)
    if not entry:
        raise ValueError(f"Unknown journey slug '{slug}' for project '{project}'")

    test_case_id = generate_journey_for_entry(
        db, job, entry, extra_params=params.get("overrides")
    )
    append_job_event(
        db,
        job.id,
        event_type="journey_generated",
        profile="qa-test-gen",
        message=f"Generated test_case_id={test_case_id}",
        payload_summary={"test_case_id": test_case_id, "journey_slug": slug},
    )


def _heal_failures(db: Session, job: FactoryJob) -> None:
    from datetime import datetime

    params: Dict[str, Any] = job.params or {}
    since_raw = params.get("since")
    since = None
    if since_raw:
        since = datetime.fromisoformat(str(since_raw).replace("Z", "+00:00"))
        if since.tzinfo:
            since = since.replace(tzinfo=None)

    scan_and_heal_failures(db, job, since=since)


def _scan_changes(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    project = job.project or params.get("project")
    scan_registry_changes(
        db,
        job,
        project=project,
        http_credentials=params.get("http_credentials"),
    )


def _full_cycle(db: Session, job: FactoryJob) -> None:
    params: Dict[str, Any] = job.params or {}
    append_job_event(
        db,
        job.id,
        event_type="full_cycle_start",
        profile="qa-orchestrator",
        message="full_cycle: drain backlog then run regression",
    )
    try:
        _drain_backlog(db, job)
    except Exception:
        # drain may partial-fail; continue to regression if any tests exist
        logger.warning("[FactoryWorker] drain_backlog step had failures in full_cycle %s", job.id)

    reg_params = {**params, "tags": params.get("tags") or ["regression"]}
    regression_job = FactoryJob(
        id=job.id,
        job_type="run_regression",
        project=job.project,
        params=reg_params,
        status=job.status,
        created_by_user_id=job.created_by_user_id,
    )
    _run_regression(db, regression_job)
