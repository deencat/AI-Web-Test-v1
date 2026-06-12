"""Loop C: scan journey registry URLs for material changes (HF-4)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud import journey_factory as crud_journey
from app.crud import url_snapshot as crud_snapshots
from app.models.factory_job import FactoryJob
from app.schemas.journey_factory import JourneyBacklogEnqueue
from app.services.factory_job_service import append_job_event
from app.services.url_snapshot_service import (
    capture_snapshot,
    diff_snapshot_records,
    url_hash,
)

logger = logging.getLogger(__name__)


def snapshot_status_for_url(db: Session, feature_url: str) -> Dict[str, Any]:
    """Latest change-detection status for a registry URL."""
    h = url_hash(feature_url)
    latest = crud_snapshots.get_latest_by_url_hash(db, h)
    if not latest:
        return {
            "has_baseline": False,
            "material_change": False,
            "summary": "No snapshot yet",
            "last_captured_at": None,
        }
    previous = crud_snapshots.get_previous_snapshot(db, h, latest.id)
    if not previous:
        return {
            "has_baseline": False,
            "material_change": False,
            "summary": "First snapshot captured",
            "last_captured_at": latest.captured_at.isoformat(),
        }
    diff = diff_snapshot_records(previous, latest)
    return {
        "has_baseline": True,
        "material_change": diff["material_change"],
        "summary": diff["summary"],
        "last_captured_at": latest.captured_at.isoformat(),
    }


def scan_registry_changes(
    db: Session,
    job: FactoryJob,
    *,
    project: Optional[str] = None,
    http_credentials: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    """Capture snapshots for all registry journeys; enqueue backlog on material change."""
    entries = crud_journey.list_registry_entries(db, project=project)
    results: List[Dict[str, Any]] = []

    append_job_event(
        db,
        job.id,
        event_type="scan_changes_start",
        profile="qa-change-detector",
        message=f"Scanning {len(entries)} journey URL(s)",
        payload_summary={"project": project, "count": len(entries)},
    )

    for entry in entries:
        creds = http_credentials
        meta = crud_journey.get_project_meta(db, entry.project)
        if not creds and meta and meta.default_env_config:
            creds = meta.default_env_config.get("http_credentials")

        try:
            current = capture_snapshot(db, entry.feature_url, http_credentials=creds)
            baseline = crud_snapshots.get_previous_snapshot(db, current.url_hash, current.id)
            status: Dict[str, Any] = {
                "journey_slug": entry.slug,
                "url": entry.feature_url,
                "snapshot_id": current.id,
                "material_change": False,
            }
            if baseline:
                diff = diff_snapshot_records(baseline, current)
                status.update(diff)
                if diff["material_change"]:
                    item = crud_journey.enqueue_backlog_item(
                        db,
                        JourneyBacklogEnqueue(
                            journey_slug=entry.slug,
                            project=entry.project,
                            priority=1,
                            params={
                                "diff_summary": diff["summary"],
                                "reference_test_id": entry.reference_test_id,
                                "source": "scan_changes",
                            },
                        ),
                    )
                    status["backlog_id"] = item.id
                    append_job_event(
                        db,
                        job.id,
                        event_type="material_change_detected",
                        profile="qa-change-detector",
                        message=f"{entry.slug}: {diff['summary']}",
                        payload_summary={
                            "journey_slug": entry.slug,
                            "backlog_id": item.id,
                            "similarity_score": diff.get("similarity_score"),
                        },
                    )
            else:
                status["summary"] = "First snapshot — baseline stored"
                append_job_event(
                    db,
                    job.id,
                    event_type="snapshot_baseline",
                    profile="qa-change-detector",
                    message=f"{entry.slug}: first snapshot captured",
                    payload_summary={"journey_slug": entry.slug, "snapshot_id": current.id},
                )
            results.append(status)
        except Exception as exc:
            logger.exception("[FactoryChangeScan] Failed for %s", entry.slug)
            append_job_event(
                db,
                job.id,
                event_type="scan_error",
                profile="qa-change-detector",
                message=f"{entry.slug}: {exc}",
                payload_summary={"journey_slug": entry.slug, "error": str(exc)},
            )
            results.append(
                {"journey_slug": entry.slug, "error": str(exc), "material_change": False}
            )

    append_job_event(
        db,
        job.id,
        event_type="scan_changes_complete",
        profile="qa-change-detector",
        message=f"Scan complete — {sum(1 for r in results if r.get('material_change'))} material change(s)",
        payload_summary={"results_count": len(results)},
    )
    return results
