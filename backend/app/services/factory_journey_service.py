"""Journey generation via crawl-and-save for factory worker (HF-3)."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import journey_factory as crud_journey
from app.crud import test_schedule as crud_schedules
from app.models.factory_job import FactoryJob
from app.models.journey_factory import JourneyBacklogItem, JourneyRegistryEntry
from app.schemas.test_schedule import TestScheduleCreate
from app.services.factory_job_service import append_job_event
from app.services.scheduler_service import scheduler_service
from app.services.workflow_store import get_state

logger = logging.getLogger(__name__)


def _v2_base() -> str:
    return settings.AWT_BASE_URL.rstrip("/").replace("/api/v1", "/api/v2")


def _build_user_instruction(entry: JourneyRegistryEntry) -> str:
    parts = [
        f"Journey: {entry.name}.",
        f"Start from the feature URL and exercise the main user flow.",
    ]
    if entry.requires_login:
        parts.append("Login first using provided credentials or login module.")
    if entry.stop_at_page_hint:
        parts.append(
            f"STOP as soon as the page title or URL contains '{entry.stop_at_page_hint}'. "
            "Do NOT proceed past that page."
        )
    else:
        parts.append("STOP at a stable page before complex forms or payment.")
    return " ".join(parts)


def _build_crawl_body(
    entry: JourneyRegistryEntry,
    project_meta: Any,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    defaults = (project_meta.default_env_config if project_meta else None) or {}
    extra = extra_params or {}

    tags = list(entry.tags or [])
    if "factory-generated" not in tags:
        tags.append("factory-generated")
    if "regression" not in tags:
        tags.append("regression")

    body: Dict[str, Any] = {
        "url": entry.feature_url,
        "user_instruction": extra.get("user_instruction") or _build_user_instruction(entry),
        "test_title": extra.get("test_title") or f"{entry.name} (factory)",
        "test_description": extra.get("test_description")
        or f"Auto-generated from journey registry slug={entry.slug}",
        "tags": extra.get("tags") or tags,
        "priority": extra.get("priority") or "medium",
        "test_type": "e2e",
    }

    if entry.stop_at_page_hint:
        body["stop_at_page_hint"] = entry.stop_at_page_hint
    if entry.reference_test_id:
        body["reference_test_id"] = entry.reference_test_id

    for key in (
        "login_module",
        "existing_subscriber_module",
        "new_subscriber_module",
        "subscriber_type_hint",
        "max_browser_steps",
        "max_flow_timeout_seconds",
        "login_credentials",
        "http_credentials",
    ):
        if key in extra and extra[key] is not None:
            body[key] = extra[key]
        elif key in defaults and defaults[key] is not None:
            body[key] = defaults[key]

    return body


def _start_crawl(body: Dict[str, Any]) -> str:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{_v2_base()}/crawl-and-save-test", json=body)
        response.raise_for_status()
        data = response.json()
        workflow_id = data.get("workflow_id")
        if not workflow_id:
            raise RuntimeError("crawl-and-save did not return workflow_id")
        return workflow_id


def _poll_workflow(
    workflow_id: str,
    *,
    poll_interval: int = 15,
    timeout_seconds: int = 1200,
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = get_state(workflow_id)
        if not state:
            time.sleep(poll_interval)
            continue
        status = state.get("status", "pending")
        if status == "completed":
            result = state.get("result") or {}
            if not result.get("test_case_ids"):
                raise RuntimeError("crawl completed but no test_case_ids in result")
            return result
        if status == "failed":
            raise RuntimeError(state.get("error") or "crawl-and-save workflow failed")
        time.sleep(poll_interval)
    raise TimeoutError(f"crawl-and-save workflow {workflow_id} timed out after {timeout_seconds}s")


def auto_schedule_test(
    db: Session,
    test_case_id: int,
    user_id: int,
    *,
    cron: Optional[str] = None,
) -> Optional[int]:
    """Create nightly regression schedule for a new test (HF-3.4)."""
    if not settings.FACTORY_AUTO_SCHEDULE_ENABLED:
        return None

    existing = crud_schedules.list_schedules_for_test(db, test_case_id, user_id)
    if existing:
        return existing[0].id

    cron_expr = cron or settings.FACTORY_AUTO_SCHEDULE_CRON
    schedule = crud_schedules.create_schedule(
        db,
        TestScheduleCreate(
            test_case_id=test_case_id,
            name="Factory nightly regression",
            schedule_type="cron",
            cron_expression=cron_expr,
            browser="chromium",
            environment="staging",
            enabled=True,
        ),
        user_id,
    )
    scheduler_service.add_schedule(schedule)
    return schedule.id


def generate_journey_for_entry(
    db: Session,
    job: FactoryJob,
    entry: JourneyRegistryEntry,
    *,
    extra_params: Optional[Dict[str, Any]] = None,
) -> int:
    """Run crawl-and-save for a registry entry; return test_case_id."""
    project_meta = crud_journey.get_project_meta(db, entry.project)
    body = _build_crawl_body(entry, project_meta, extra_params)

    append_job_event(
        db,
        job.id,
        event_type="crawl_started",
        profile="qa-test-gen",
        message=f"Starting crawl for journey {entry.slug}",
        payload_summary={"journey_slug": entry.slug, "url": entry.feature_url},
    )

    workflow_id = _start_crawl(body)
    timeout = int(body.get("max_flow_timeout_seconds") or 1200) + 120

    append_job_event(
        db,
        job.id,
        event_type="crawl_polling",
        profile="qa-test-gen",
        message=f"Polling workflow {workflow_id}",
        payload_summary={"workflow_id": workflow_id},
    )

    result = _poll_workflow(workflow_id, timeout_seconds=timeout)
    test_case_id = int(result["test_case_ids"][0])

    user_id = job.created_by_user_id or settings.FACTORY_SERVICE_USER_ID
    schedule_id = auto_schedule_test(db, test_case_id, user_id)

    append_job_event(
        db,
        job.id,
        event_type="test_generated",
        profile="qa-test-gen",
        message=f"Saved test_case_id={test_case_id}",
        payload_summary={
            "test_case_id": test_case_id,
            "workflow_id": workflow_id,
            "schedule_id": schedule_id,
        },
    )

    if entry.reference_test_id is None:
        from app.schemas.journey_factory import JourneyRegistryEntryUpdate

        crud_journey.update_registry_entry(
            db,
            entry,
            JourneyRegistryEntryUpdate(reference_test_id=test_case_id),
        )

    return test_case_id


def generate_journey_for_backlog_item(
    db: Session,
    job: FactoryJob,
    item: JourneyBacklogItem,
) -> int:
    entry = crud_journey.get_registry_by_slug(db, item.project, item.journey_slug)
    if not entry:
        raise ValueError(f"Registry entry missing: {item.journey_slug}")
    return generate_journey_for_entry(db, job, entry, extra_params=item.params)
