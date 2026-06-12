"""API v2: URL snapshot capture and diff (HF-4 Loop C)."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import url_snapshot as crud_snapshots
from app.schemas.url_snapshot import (
    ObserveSnapshotRequest,
    SnapshotDiffRequest,
    SnapshotDiffResponse,
    UrlSnapshotResponse,
)
from app.services.url_snapshot_service import (
    capture_snapshot,
    diff_snapshot_records,
    url_hash as compute_url_hash,
)

router = APIRouter()


@router.post(
    "/observe-snapshot",
    response_model=UrlSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Capture a URL snapshot for change detection",
)
def observe_snapshot(
    body: ObserveSnapshotRequest,
    db: Session = Depends(get_db),
) -> UrlSnapshotResponse:
    try:
        row = capture_snapshot(
            db,
            str(body.url),
            http_credentials=body.http_credentials,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Snapshot capture failed: {exc}",
        ) from exc
    return UrlSnapshotResponse.model_validate(row)


@router.get(
    "/snapshots/{url_hash}",
    response_model=UrlSnapshotResponse,
    summary="Get latest snapshot for a URL hash",
)
def get_latest_snapshot(
    url_hash: str,
    db: Session = Depends(get_db),
) -> UrlSnapshotResponse:
    row = crud_snapshots.get_latest_by_url_hash(db, url_hash)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return UrlSnapshotResponse.model_validate(row)


@router.post(
    "/snapshots/diff",
    response_model=SnapshotDiffResponse,
    summary="Diff URL snapshots (optionally capture a new baseline first)",
)
def diff_snapshots(
    body: SnapshotDiffRequest,
    db: Session = Depends(get_db),
) -> SnapshotDiffResponse:
    resolved_hash = body.url_hash
    resolved_url = str(body.url) if body.url else None

    if body.capture_new:
        if not resolved_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="url is required when capture_new=true",
            )
        current = capture_snapshot(db, resolved_url)
        resolved_hash = current.url_hash
    else:
        if not resolved_hash and resolved_url:
            resolved_hash = compute_url_hash(resolved_url)
        current = crud_snapshots.get_latest_by_url_hash(db, resolved_hash or "")
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current snapshot")

    if body.baseline_snapshot_id:
        baseline = crud_snapshots.get_snapshot(db, body.baseline_snapshot_id)
    else:
        baseline = crud_snapshots.get_previous_snapshot(db, current.url_hash, current.id)

    if not baseline:
        return SnapshotDiffResponse(
            material_change=False,
            summary="No baseline snapshot — first capture stored.",
            url=current.url,
            url_hash=current.url_hash,
            current_snapshot_id=current.id,
            current_fingerprint=current.element_fingerprint,
        )

    result: dict[str, Any] = diff_snapshot_records(baseline, current)
    return SnapshotDiffResponse(**result)
