"""
CRUD operations for browser profiles.
Created: February 3, 2026
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.browser_profile import BrowserProfile
from app.schemas.browser_profile import BrowserProfileCreate, BrowserProfileUpdate
from app.services.encryption_service import EncryptionService


def _get_encryption_service() -> EncryptionService:
    return EncryptionService()


def create_profile(
    db: Session,
    user_id: int,
    profile_data: BrowserProfileCreate
) -> BrowserProfile:
    """Create a new browser profile registry entry."""
    encrypted_password = None
    if profile_data.http_password:
        encrypted_password = _get_encryption_service().encrypt_password(profile_data.http_password)

    profile = BrowserProfile(
        user_id=user_id,
        profile_name=profile_data.profile_name,
        os_type=profile_data.os_type,
        browser_type=profile_data.browser_type,
        description=profile_data.description,
        http_username=profile_data.http_username,
        http_password_encrypted=encrypted_password,
        auto_sync=bool(profile_data.auto_sync),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, profile_id: int) -> Optional[BrowserProfile]:
    """Get browser profile by ID."""
    return db.query(BrowserProfile).filter(BrowserProfile.id == profile_id).first()


def get_profile_by_user(db: Session, profile_id: int, user_id: int) -> Optional[BrowserProfile]:
    """Get browser profile by ID and user ID (ensures ownership)."""
    return db.query(BrowserProfile).filter(
        BrowserProfile.id == profile_id,
        BrowserProfile.user_id == user_id
    ).first()


def get_all_profiles_by_user(db: Session, user_id: int) -> List[BrowserProfile]:
    """Get all browser profiles for a specific user."""
    return db.query(BrowserProfile).filter(
        BrowserProfile.user_id == user_id
    ).order_by(BrowserProfile.created_at.desc()).all()


def update_profile(
    db: Session,
    profile: BrowserProfile,
    profile_data: BrowserProfileUpdate
) -> BrowserProfile:
    """Update an existing browser profile."""
    update_data = profile_data.dict(exclude_unset=True)

    if update_data.pop("clear_http_credentials", False):
        profile.http_username = None
        profile.http_password_encrypted = None
        update_data.pop("http_username", None)
        update_data.pop("http_password", None)

    if "http_password" in update_data:
        http_password = update_data.pop("http_password")
        if http_password:
            profile.http_password_encrypted = _get_encryption_service().encrypt_password(http_password)
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    return profile


def sync_profile_session(
    db: Session,
    profile_id: int,
    user_id: int,
    session_data: dict
) -> BrowserProfile:
    """Encrypt and store session data for a browser profile."""
    profile = get_profile_by_user(db=db, profile_id=profile_id, user_id=user_id)
    if not profile:
        raise ValueError("Profile not found")

    encryption_service = _get_encryption_service()
    profile.cookies_encrypted = encryption_service.encrypt_json(session_data.get("cookies", []))
    profile.local_storage_encrypted = encryption_service.encrypt_json(
        session_data.get("localStorage", {})
    )
    profile.session_storage_encrypted = encryption_service.encrypt_json(
        session_data.get("sessionStorage", {})
    )
    profile.last_sync_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def load_profile_session(
    db: Session,
    profile_id: int,
    user_id: int
) -> Optional[dict]:
    """Decrypt and return session data for execution."""
    profile = get_profile_by_user(db=db, profile_id=profile_id, user_id=user_id)
    if not profile or not profile.has_session_data:
        return None

    encryption_service = _get_encryption_service()

    session_storage = (
        encryption_service.decrypt_json(profile.session_storage_encrypted)
        if profile.session_storage_encrypted
        else {}
    )

    return {
        "cookies": encryption_service.decrypt_json(profile.cookies_encrypted) if profile.cookies_encrypted else [],
        "localStorage": encryption_service.decrypt_json(profile.local_storage_encrypted) if profile.local_storage_encrypted else {},
        "sessionStorage": session_storage,
        "http_credentials": get_http_credentials(db=db, profile_id=profile_id, user_id=user_id)
    }


def get_http_credentials(
    db: Session,
    profile_id: int,
    user_id: int
) -> Optional[dict]:
    """Return decrypted HTTP credentials for a profile if available."""
    profile = get_profile_by_user(db=db, profile_id=profile_id, user_id=user_id)
    if not profile or not profile.has_http_credentials:
        return None

    password = _get_encryption_service().decrypt_password(profile.http_password_encrypted)
    return {
        "username": profile.http_username,
        "password": password
    }


def delete_profile(db: Session, profile: BrowserProfile) -> bool:
    """Delete a browser profile."""
    db.delete(profile)
    db.commit()
    return True


def update_last_sync(db: Session, profile: BrowserProfile) -> BrowserProfile:
    """Update the last_sync_at timestamp (called after profile export)."""
    profile.last_sync_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    return profile


def get_profiles_count(db: Session, user_id: int) -> int:
    """Get total count of profiles for a user."""
    return db.query(BrowserProfile).filter(BrowserProfile.user_id == user_id).count()
