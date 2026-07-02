"""Forward factory jobs to the QA Orchestrator node (HF-3.7)."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.factory_job_service import append_job_event, get_factory_job, set_job_status
from app.models.factory_job import FactoryJobStatus
from app.services.factory_settings_service import get_effective_bridge_url

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="factory-bridge")

_BRIDGE_PROGRESS_EVENTS = {
    "job_started",
    "delegate_start",
    "delegate_complete",
    "job_complete",
    "error",
}
_BRIDGE_WATCHDOG_SECONDS = 45


def bridge_routing_enabled() -> bool:
    db = SessionLocal()
    try:
        return bool(get_effective_bridge_url(db))
    finally:
        db.close()


def _bridge_run_url(bridge_base: str) -> str:
    return f"{bridge_base.rstrip('/')}/run"


def _bridge_received_progress(job) -> bool:
    for event in job.events or []:
        if event.event_type in _BRIDGE_PROGRESS_EVENTS:
            return True
    return False


def _watch_bridge_job(job_id: str) -> None:
    """Fail jobs that were accepted by the bridge but never reported progress."""
    time.sleep(_BRIDGE_WATCHDOG_SECONDS)
    db = SessionLocal()
    try:
        job = get_factory_job(db, job_id)
        if not job:
            return
        if job.status in (
            FactoryJobStatus.COMPLETED.value,
            FactoryJobStatus.FAILED.value,
            FactoryJobStatus.CANCELLED.value,
        ):
            return
        if _bridge_received_progress(job):
            return

        hint = (
            "The orchestrator node accepted the job but sent no events back to Agentic QA. "
            "On the factory node, set AWT_AGENT_EVENTS_URL to this machine's LAN URL, e.g. "
            "http://<WINDOWS-IP>:8000/api/v1/agent/hermes/events "
            "(not localhost unless the bridge runs on the same PC)."
        )
        set_job_status(db, job, FactoryJobStatus.FAILED, error_message=hint)
        append_job_event(
            db,
            job.id,
            event_type="error",
            profile="factory_bridge",
            message=hint,
        )
        logger.warning("[FactoryBridge] Watchdog timed out job %s — no bridge events ingested", job_id)
    finally:
        db.close()


def _forward_sync(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = get_factory_job(db, job_id)
        if not job:
            logger.warning("[FactoryBridge] job %s not found", job_id)
            return

        bridge_url = get_effective_bridge_url(db)
        if not bridge_url:
            logger.warning("[FactoryBridge] no orchestrator URL configured for job %s", job_id)
            set_job_status(db, job, FactoryJobStatus.FAILED, error_message="Orchestrator node URL not configured")
            return

        secret = settings.HERMES_BRIDGE_SECRET or ""
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"

        payload = {
            "job_id": job.id,
            "job_type": job.job_type,
            "project": job.project,
            "params": job.params or {},
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(_bridge_run_url(bridge_url), json=payload, headers=headers)
                resp.raise_for_status()
            set_job_status(db, job, FactoryJobStatus.RUNNING)
            append_job_event(
                db,
                job.id,
                event_type="bridge_accepted",
                profile="factory_bridge",
                message="Job accepted by QA Orchestrator node",
                payload_summary={"bridge_url": bridge_url},
            )
            _executor.submit(_watch_bridge_job, job_id)
            logger.info("[FactoryBridge] Forwarded job %s to %s", job_id, bridge_url)
        except Exception as exc:
            logger.exception("[FactoryBridge] Forward failed for job %s", job_id)
            set_job_status(db, job, FactoryJobStatus.FAILED, error_message=str(exc))
            append_job_event(
                db,
                job.id,
                event_type="error",
                profile="factory_bridge",
                message=f"Orchestrator forward failed: {exc}",
            )
    finally:
        db.close()


def submit_job_to_bridge_async(job_id: str) -> bool:
    """Queue HTTP forward to QA Orchestrator node. Returns False if URL not configured."""
    if not bridge_routing_enabled():
        return False
    _executor.submit(_forward_sync, job_id)
    return True
