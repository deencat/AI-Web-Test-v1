"""Factory job completion notifications (HF-6) — superadmin only."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud import notification as crud_notifications
from app.models.factory_job import FactoryJob, FactoryJobStatus
from app.models.user import User

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


def _superadmin_user_ids(db: Session) -> List[int]:
    rows = db.query(User.id).filter(User.role == "superadmin").all()
    return [r[0] for r in rows]


def notify_factory_job_complete(db: Session, job: FactoryJob) -> Optional[int]:
    """Create in-app notifications for all superadmin users (Agent Console is superadmin-only)."""
    user_ids = _superadmin_user_ids(db)
    if not user_ids:
        logger.warning("[FactoryNotify] No superadmin users — skipping notification")
        return None

    title, body = _digest_for_job(job)
    last_id: Optional[int] = None

    try:
        for user_id in user_ids:
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
            last_id = row.id
        logger.info(
            "[FactoryNotify] Notified %s superadmin user(s) for job %s",
            len(user_ids),
            job.id,
        )
        return last_id
    except Exception as exc:
        logger.warning("[FactoryNotify] Failed to notify: %s", exc)
        return None
