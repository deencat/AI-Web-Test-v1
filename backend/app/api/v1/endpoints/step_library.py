"""
CRUD endpoints for StepLibraryModule — Sprint 10.11.

GET    /api/v1/step-library              List user's modules
POST   /api/v1/step-library              Create a new module
PUT    /api/v1/step-library/{id}         Update an existing module
DELETE /api/v1/step-library/{id}         Delete a module
GET    /api/v1/step-library/{id}/usage   Get usage count for a module
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.crud import step_library as crud
from app.models.user import User
from app.schemas.step_library_module import (
    StepLibraryModuleCreate,
    StepLibraryModuleResponse,
    StepLibraryModuleUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_module_or_404(module_id: int, user_id: int, db: Session):
    module = crud.get_by_id(db=db, module_id=module_id, user_id=user_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step library module {module_id} not found.",
        )
    return module


@router.get(
    "/step-library",
    response_model=List[StepLibraryModuleResponse],
    summary="List step library modules for the current user",
)
def list_step_library_modules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    modules = crud.list_modules(db=db, user_id=current_user.id)
    # Annotate with usage counts
    result = []
    for m in modules:
        response = StepLibraryModuleResponse.model_validate(m)
        response.usage_count = crud.get_usage_count(db=db, module_name=m.name)
        result.append(response)
    return result


@router.post(
    "/step-library",
    response_model=StepLibraryModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new step library module",
)
def create_step_library_module(
    body: StepLibraryModuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Enforce name uniqueness per user
    existing = crud.get_by_name(db=db, name=body.name, user_id=current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A module named '{body.name}' already exists.",
        )
    module = crud.create_module(db=db, schema=body, user_id=current_user.id)
    logger.info("Created step library module '%s' for user %s", module.name, current_user.id)
    return module


@router.put(
    "/step-library/{module_id}",
    response_model=StepLibraryModuleResponse,
    summary="Update an existing step library module",
)
def update_step_library_module(
    module_id: int,
    body: StepLibraryModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _get_module_or_404(module_id, current_user.id, db)

    # If renaming, enforce uniqueness
    if body.name and body.name != module.name:
        existing = crud.get_by_name(db=db, name=body.name, user_id=current_user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A module named '{body.name}' already exists.",
            )

    updated = crud.update_module(db=db, module=module, schema=body)
    logger.info("Updated step library module %s for user %s", module_id, current_user.id)
    return updated


@router.delete(
    "/step-library/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a step library module",
)
def delete_step_library_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = crud.delete_module(db=db, module_id=module_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step library module {module_id} not found.",
        )
    logger.info("Deleted step library module %s for user %s", module_id, current_user.id)


@router.get(
    "/step-library/{module_id}/usage",
    summary="Get usage count (number of test cases referencing this module)",
)
def get_module_usage(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _get_module_or_404(module_id, current_user.id, db)
    count = crud.get_usage_count(db=db, module_name=module.name)
    return {"module_id": module_id, "usage_count": count}
