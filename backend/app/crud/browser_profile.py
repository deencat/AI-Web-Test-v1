"""
CRUD operations for browser profiles.
Created: February 3, 2026
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.browser_profile import BrowserProfile
from app.schemas.browser_profile import BrowserProfileCreate, BrowserProfileUpdate


def create_profile(
    db: Session,
    user_id: int,
    profile_data: BrowserProfileCreate
) -> BrowserProfile:
    """Create a new browser profile registry entry."""
    profile = BrowserProfile(
        user_id=user_id,
        profile_name=profile_data.profile_name,
        os_type=profile_data.os_type,
        browser_type=profile_data.browser_type,
        description=profile_data.description,
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
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    return profile


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
