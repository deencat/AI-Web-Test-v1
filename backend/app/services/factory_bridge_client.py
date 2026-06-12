"""Forward factory jobs to Hermes Bridge on Node 1 (HF-3.7)."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.factory_job_service import append_job_event, get_factory_job, set_job_status
from app.models.factory_job import FactoryJobStatus

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="hermes-bridge")


def bridge_routing_enabled() -> bool:
    return bool(settings.HERMES_BRIDGE_URL and settings.HERMES_BRIDGE_URL.strip())


def _bridge_run_url() -> str:
    base = settings.HERMES_BRIDGE_URL.rstrip("/")
    return f"{base}/run"


def _forward_sync(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = get_factory_job(db, job_id)
        if not job:
            logger.warning("[HermesBridge] job %s not found", job_id)
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
                resp = client.post(_bridge_run_url(), json=payload, headers=headers)
                resp.raise_for_status()
            append_job_event(
                db,
                job.id,
                event_type="bridge_accepted",
                profile="hermes_bridge",
                message="Job accepted by Hermes Bridge",
                payload_summary={"bridge_url": settings.HERMES_BRIDGE_URL},
            )
            logger.info("[HermesBridge] Forwarded job %s to bridge", job_id)
        except Exception as exc:
            logger.exception("[HermesBridge] Forward failed for job %s", job_id)
            set_job_status(db, job, FactoryJobStatus.FAILED, error_message=str(exc))
            append_job_event(
                db,
                job.id,
                event_type="error",
                profile="hermes_bridge",
                message=f"Bridge forward failed: {exc}",
            )
    finally:
        db.close()


def submit_job_to_bridge_async(job_id: str) -> bool:
    """Queue HTTP forward to Hermes Bridge. Returns False if bridge URL not configured."""
    if not bridge_routing_enabled():
        return False
    _executor.submit(_forward_sync, job_id)
    return True
