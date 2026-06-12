"""CRUD for URL snapshots (HF-4)."""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.url_snapshot import UrlSnapshot


def create_snapshot(db: Session, row: UrlSnapshot) -> UrlSnapshot:
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_snapshot(db: Session, snapshot_id: int) -> Optional[UrlSnapshot]:
    return db.query(UrlSnapshot).filter(UrlSnapshot.id == snapshot_id).first()


def get_latest_by_url_hash(db: Session, url_hash: str) -> Optional[UrlSnapshot]:
    return (
        db.query(UrlSnapshot)
        .filter(UrlSnapshot.url_hash == url_hash)
        .order_by(desc(UrlSnapshot.captured_at))
        .first()
    )


def get_previous_snapshot(
    db: Session,
    url_hash: str,
    exclude_id: int,
) -> Optional[UrlSnapshot]:
    return (
        db.query(UrlSnapshot)
        .filter(UrlSnapshot.url_hash == url_hash, UrlSnapshot.id != exclude_id)
        .order_by(desc(UrlSnapshot.captured_at))
        .first()
    )


def list_snapshots_for_url(
    db: Session,
    url_hash: str,
    limit: int = 10,
) -> List[UrlSnapshot]:
    return (
        db.query(UrlSnapshot)
        .filter(UrlSnapshot.url_hash == url_hash)
        .order_by(desc(UrlSnapshot.captured_at))
        .limit(limit)
        .all()
    )
