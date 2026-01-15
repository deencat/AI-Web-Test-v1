"""API endpoints for test case version control."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.version_service import VersionService
from app.models.test_case import TestCase


router = APIRouter()


# Pydantic models for request/response
class VersionResponse(BaseModel):
    """Response model for version data."""
    id: int
    test_case_id: int
    version_number: int
    steps: list
    expected_result: str | None = None
    test_data: dict | None = None
    created_at: str
    created_by: str
    change_reason: str | None = None
    parent_version_id: int | None = None
    
    class Config:
        from_attributes = True


class UpdateTestStepsRequest(BaseModel):
    """Request model for updating test steps."""
    steps: List[str] = Field(..., description="Updated test steps")
    expected_result: str | None = Field(None, description="Updated expected result")
    test_data: dict | None = Field(None, description="Updated test data")
    created_by: str = Field(default="user", description="Who made the change")
    change_reason: str = Field(default="manual_edit", description="Reason for the change")


class RollbackRequest(BaseModel):
    """Request model for rollback."""
    version_id: int = Field(..., description="Version ID to rollback to")
    created_by: str = Field(default="user", description="Who initiated rollback")


@router.put("/{test_case_id}/steps", response_model=VersionResponse, status_code=status.HTTP_200_OK)
def update_test_steps(
    test_case_id: int,
    request: UpdateTestStepsRequest,
    db: Session = Depends(get_db)
):
    """
    Update test case steps and create a new version.
    
    - **test_case_id**: ID of the test case to update
    - **steps**: New test steps (complete list)
    - **expected_result**: Optional updated expected result
    - **test_data**: Optional updated test data
    - **created_by**: Who made the change (default: "user")
    - **change_reason**: Reason for the change (default: "manual_edit")
    
    Returns the newly created version.
    """
    # Verify test case exists
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {test_case_id} not found"
        )
    
    try:
        # Save new version
        new_version = VersionService.save_version(
            db=db,
            test_case_id=test_case_id,
            steps=request.steps,
            expected_result=request.expected_result,
            test_data=request.test_data,
            created_by=request.created_by,
            change_reason=request.change_reason
        )
        
        # Update the actual test case
        test_case.steps = request.steps
        if request.expected_result is not None:
            test_case.expected_result = request.expected_result
        if request.test_data is not None:
            test_case.test_data = request.test_data
        
        db.commit()
        db.refresh(test_case)
        
        # Return version data
        return VersionResponse(
            id=new_version.id,
            test_case_id=new_version.test_case_id,
            version_number=new_version.version_number,
            steps=new_version.steps,
            expected_result=new_version.expected_result,
            test_data=new_version.test_data,
            created_at=new_version.created_at.isoformat(),
            created_by=new_version.created_by,
            change_reason=new_version.change_reason,
            parent_version_id=new_version.parent_version_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test steps: {str(e)}"
        )


@router.get("/{test_case_id}/versions", response_model=List[VersionResponse])
def get_version_history(
    test_case_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get version history for a test case.
    
    - **test_case_id**: ID of the test case
    - **limit**: Maximum number of versions to return (default: 50)
    
    Returns list of versions, newest first.
    """
    # Verify test case exists
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {test_case_id} not found"
        )
    
    versions = VersionService.get_version_history(db, test_case_id, limit)
    
    return [
        VersionResponse(
            id=v.id,
            test_case_id=v.test_case_id,
            version_number=v.version_number,
            steps=v.steps,
            expected_result=v.expected_result,
            test_data=v.test_data,
            created_at=v.created_at.isoformat(),
            created_by=v.created_by,
            change_reason=v.change_reason,
            parent_version_id=v.parent_version_id
        )
        for v in versions
    ]


@router.get("/{test_case_id}/versions/{version_id}", response_model=VersionResponse)
def get_version(
    test_case_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific version by ID.
    
    - **test_case_id**: ID of the test case
    - **version_id**: ID of the version to retrieve
    
    Returns the version data.
    """
    version = VersionService.get_version(db, version_id)
    
    if not version or version.test_case_id != test_case_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found for test case {test_case_id}"
        )
    
    return VersionResponse(
        id=version.id,
        test_case_id=version.test_case_id,
        version_number=version.version_number,
        steps=version.steps,
        expected_result=version.expected_result,
        test_data=version.test_data,
        created_at=version.created_at.isoformat(),
        created_by=version.created_by,
        change_reason=version.change_reason,
        parent_version_id=version.parent_version_id
    )


@router.post("/{test_case_id}/versions/rollback", response_model=VersionResponse)
def rollback_to_version(
    test_case_id: int,
    request: RollbackRequest,
    db: Session = Depends(get_db)
):
    """
    Rollback test case to a previous version.
    
    Creates a new version with content from the specified version.
    
    - **test_case_id**: ID of the test case
    - **version_id**: ID of the version to rollback to
    - **created_by**: Who initiated the rollback (default: "user")
    
    Returns the new version created from rollback.
    """
    # Verify test case exists
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {test_case_id} not found"
        )
    
    try:
        new_version = VersionService.rollback_to_version(
            db=db,
            test_case_id=test_case_id,
            version_id=request.version_id,
            created_by=request.created_by
        )
        
        return VersionResponse(
            id=new_version.id,
            test_case_id=new_version.test_case_id,
            version_number=new_version.version_number,
            steps=new_version.steps,
            expected_result=new_version.expected_result,
            test_data=new_version.test_data,
            created_at=new_version.created_at.isoformat(),
            created_by=new_version.created_by,
            change_reason=new_version.change_reason,
            parent_version_id=new_version.parent_version_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback: {str(e)}"
        )


@router.get("/{test_case_id}/versions/compare/{version_id_1}/{version_id_2}")
def compare_versions(
    test_case_id: int,
    version_id_1: int,
    version_id_2: int,
    db: Session = Depends(get_db)
):
    """
    Compare two versions.
    
    - **test_case_id**: ID of the test case
    - **version_id_1**: ID of first version
    - **version_id_2**: ID of second version
    
    Returns comparison results.
    """
    try:
        comparison = VersionService.compare_versions(db, version_id_1, version_id_2)
        return comparison
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare versions: {str(e)}"
        )
