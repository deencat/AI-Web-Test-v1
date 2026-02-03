"""
Browser Profile API endpoints for Browser Profile Session Persistence.
Created: February 3, 2026
"""
import json
import zipfile
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.browser_profile import (
    BrowserProfileCreate,
    BrowserProfileUpdate,
    BrowserProfileResponse,
    BrowserProfileListResponse,
    BrowserProfileExportRequest,
    BrowserProfileExportResponse
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
    
    Creates metadata-only registry entry. No session data stored on server.
    User must manually log in and export profile to capture session data.
    
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
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


@router.post("/browser-profiles/{profile_id}/export", response_model=BrowserProfileExportResponse)
async def export_browser_profile(
    profile_id: int,
    request: BrowserProfileExportRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Export browser session data from a debug session (after manual login).
    
    **Authentication required**
    
    **Workflow:**
    1. User starts debug session with `/debug/start` (manual mode recommended)
    2. User manually logs in to website in debug browser
    3. User calls this endpoint with session_id
    4. System exports cookies, localStorage, sessionStorage
    5. System packages data as ZIP file (profile.json inside)
    6. Returns download link and updates profile's last_sync_at
    
    **Security:** All data handled in-memory only, no disk writes.
    
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
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add profile data as JSON
            profile_json = json.dumps(profile_data, indent=2)
            zip_file.writestr("profile.json", profile_json)
            
            # Add metadata
            metadata = {
                "profile_id": profile_id,
                "profile_name": profile.profile_name,
                "os_type": profile.os_type,
                "browser_type": profile.browser_type,
                "exported_at": profile_data["exported_at"]
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        # Get file size
        file_size_bytes = zip_buffer.tell()
        
        # Update profile's last_sync_at timestamp
        crud_profile.update_last_sync(db=db, profile=profile)
        
        # Return response with file download
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=profile_{profile_id}_{profile.profile_name}.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export profile: {str(e)}"
        )


@router.post("/browser-profiles/upload", response_model=dict)
async def upload_browser_profile(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Upload and parse a browser profile ZIP file for use in test execution.
    
    **Authentication required**
    
    **Security:** File processed entirely in RAM, no disk writes, auto-cleaned by garbage collection.
    
    **Workflow:**
    1. User uploads profile ZIP file
    2. System extracts profile.json in-memory
    3. Returns profile_data dict for use in execution request
    4. User includes profile_data in POST /executions request
    
    **Returns:**
    - `profile_data`: Dict with cookies, localStorage, sessionStorage
    - `metadata`: Profile metadata from ZIP
    - `file_size_bytes`: Size of uploaded file
    """
    try:
        # Read ZIP file into memory
        contents = await file.read()
        file_size_bytes = len(contents)
        
        # Extract profile data from ZIP (in-memory only)
        with zipfile.ZipFile(io.BytesIO(contents), 'r') as zip_file:
            # Read profile.json
            if "profile.json" not in zip_file.namelist():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid profile file: missing profile.json"
                )
            
            profile_json = zip_file.read("profile.json").decode('utf-8')
            profile_data = json.loads(profile_json)
            
            # Read metadata.json (optional)
            metadata = None
            if "metadata.json" in zip_file.namelist():
                metadata_json = zip_file.read("metadata.json").decode('utf-8')
                metadata = json.loads(metadata_json)
        
        return {
            "success": True,
            "message": "Profile uploaded and parsed successfully",
            "profile_data": profile_data,
            "metadata": metadata,
            "file_size_bytes": file_size_bytes
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in profile file: {str(e)}"
        )
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process profile file: {str(e)}"
        )
