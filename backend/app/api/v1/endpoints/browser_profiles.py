"""
Browser Profile API endpoints for Browser Profile Session Persistence.
Created: February 3, 2026
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api import deps
from app.models.user import User
from app.schemas.browser_profile import (
    BrowserProfileCreate,
    BrowserProfileUpdate,
    BrowserProfileResponse,
    BrowserProfileListResponse,
    BrowserProfileSyncRequest
)
from app.crud import browser_profile as crud_profile
from app.services.debug_session_service import get_debug_session_service

router = APIRouter()


@router.post("/browser-profiles", response_model=BrowserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_browser_profile(
    profile_data: BrowserProfileCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Create a new browser profile registry entry.
    
    **Authentication required**
    
    Creates profile registry entry. Session data is synced separately after manual login.
    
    **Request Body:**
    - `profile_name`: Human-readable name (e.g., "Windows 11 - Logged In")
    - `os_type`: Operating system (windows, linux, or macos)
    - `browser_type`: Browser type (chromium, firefox, or webkit) - default: chromium
    - `description`: Optional description
    
    **Example:**
    ```json
    {
        "profile_name": "Windows 11 - Admin Session",
        "os_type": "windows",
        "browser_type": "chromium",
        "description": "Windows 11 with admin account logged in"
    }
    ```
    """
    try:
        profile = crud_profile.create_profile(
            db=db,
            user_id=current_user.id,
            profile_data=profile_data
        )
        return profile
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile name already exists for this user."
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(exc)}"
        )


@router.get("/browser-profiles", response_model=BrowserProfileListResponse)
async def list_browser_profiles(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    List all browser profiles for the current user.
    
    **Authentication required**
    
    Returns all profile metadata sorted by creation date (newest first).
    """
    profiles = crud_profile.get_all_profiles_by_user(db=db, user_id=current_user.id)
    total = crud_profile.get_profiles_count(db=db, user_id=current_user.id)
    
    return BrowserProfileListResponse(profiles=profiles, total=total)


@router.get("/browser-profiles/{profile_id}", response_model=BrowserProfileResponse)
async def get_browser_profile(
    profile_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get a specific browser profile by ID.
    
    **Authentication required**
    
    Returns profile metadata if it belongs to current user.
    """
    profile = crud_profile.get_profile_by_user(db=db, profile_id=profile_id, user_id=current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    
    return profile


@router.patch("/browser-profiles/{profile_id}", response_model=BrowserProfileResponse)
async def update_browser_profile(
    profile_id: int,
    profile_data: BrowserProfileUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Update a browser profile's metadata.
    
    **Authentication required**
    
    Updates profile_name, os_type, browser_type, or description.
    """
    profile = crud_profile.get_profile_by_user(db=db, profile_id=profile_id, user_id=current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    
    try:
        updated_profile = crud_profile.update_profile(db=db, profile=profile, profile_data=profile_data)
        return updated_profile
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile name already exists for this user."
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(exc)}"
        )


@router.delete("/browser-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_browser_profile(
    profile_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Delete a browser profile.
    
    **Authentication required**
    
    Permanently removes profile registry entry. No session data to delete (never stored).
    """
    profile = crud_profile.get_profile_by_user(db=db, profile_id=profile_id, user_id=current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    
    try:
        crud_profile.delete_profile(db=db, profile=profile)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.post("/browser-profiles/{profile_id}/sync", response_model=BrowserProfileResponse)
async def sync_browser_profile(
    profile_id: int,
    request: BrowserProfileSyncRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Sync browser session data from a debug session (after manual login).
    
    **Authentication required**
    
    **Workflow:**
    1. User starts debug session with `/debug/start` (manual mode recommended)
    2. User manually logs in to website in debug browser
    3. User calls this endpoint with session_id
    4. System exports cookies, localStorage, sessionStorage
    5. System encrypts and stores data in database
    6. Updates profile's last_sync_at
    
    **Security:** Session data is encrypted at rest using CREDENTIAL_ENCRYPTION_KEY.
    
    **Request Body:**
    - `session_id`: Active debug session ID from /debug/start
    
    **Example:**
    ```json
    {
        "session_id": "debug_abc123def456"
    }
    ```
    """
    # Verify profile ownership
    profile = crud_profile.get_profile_by_user(db=db, profile_id=profile_id, user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    
    # Get debug session service
    debug_service = get_debug_session_service()
    
    try:
        # Get stagehand service from debug session
        stagehand_service = debug_service.get_stagehand_for_session(request.session_id)
        if not stagehand_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Debug session {request.session_id} not found or not active"
            )
        
        # Export profile data from browser
        profile_data = await stagehand_service.export_browser_profile()
        synced_profile = crud_profile.sync_profile_session(
            db=db,
            profile_id=profile_id,
            user_id=current_user.id,
            session_data=profile_data
        )

        return synced_profile
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to export profile: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export profile: {str(e)}"
        )


@router.get("/browser-profiles/{profile_id}/session", response_model=dict)
async def get_browser_profile_session(
    profile_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Load decrypted session data for a browser profile.
    
    **Authentication required**
    
    Returns cookies, localStorage, and sessionStorage for injection.
    """
    session_data = crud_profile.load_profile_session(
        db=db,
        profile_id=profile_id,
        user_id=current_user.id
    )

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile has no synced session data"
        )

    return session_data
