"""Factory job completion notifications (HF-6)."""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import notification as crud_notifications
from app.models.factory_job import FactoryJob, FactoryJobStatus

logger = logging.getLogger(__name__)


def _digest_for_job(job: FactoryJob) -> tuple[str, str]:
    status = job.status
    jt = job.job_type
    if status == FactoryJobStatus.COMPLETED.value:
        title = f"Factory job completed: {jt}"
        body = f"Job {job.id[:8]}… finished successfully."
    elif status == FactoryJobStatus.FAILED.value:
        title = f"Factory job failed: {jt}"
        body = job.error_message or f"Job {job.id[:8]}… failed."
    else:
        title = f"Factory job update: {jt}"
        body = f"Job {job.id[:8]}… status is {status}."

    return title, body


def notify_factory_job_complete(db: Session, job: FactoryJob) -> Optional[int]:
    """Create in-app notification for job creator (or factory service user)."""
    user_id = job.created_by_user_id or settings.FACTORY_SERVICE_USER_ID
    if not user_id:
        return None

    title, body = _digest_for_job(job)
    try:
        row = crud_notifications.create_notification(
            db,
            user_id=user_id,
            title=title,
            body=body,
            notification_type="factory_job",
            link=f"/agent-console?job={job.id}",
            metadata={
                "job_id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "project": job.project,
            },
        )
        logger.info("[FactoryNotify] Created notification %s for user %s", row.id, user_id)
        return row.id
    except Exception as exc:
        logger.warning("[FactoryNotify] Failed to notify: %s", exc)
        return None
