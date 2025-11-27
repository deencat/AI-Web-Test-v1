"""
Test Template API Endpoints
Manage test templates for scenario generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.user import User
from app.schemas.test_template import (
    TestTemplateCreate,
    TestTemplateUpdate,
    TestTemplateResponse,
    TestTemplateListResponse,
    TestTemplateCloneRequest,
    TestTemplateStatsResponse
)
from app.services.test_template_service import TestTemplateService

router = APIRouter()


@router.post("/", response_model=TestTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: TestTemplateCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new test template
    
    Requires authentication.
    """
    # Validate template structure
    is_valid, errors = TestTemplateService.validate_template_structure(template_in.model_dump())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid template structure", "errors": errors}
        )
    
    # Create template
    try:
        template = TestTemplateService.create_template(
            db=db,
            name=template_in.name,
            description=template_in.description,
            template_type=template_in.template_type,
            category_id=template_in.category_id,
            steps_template=template_in.steps_template,
            assertion_template=template_in.assertion_template,
            data_requirements=template_in.data_requirements,
            created_by=current_user.id
        )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=TestTemplateListResponse)
def get_templates(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    template_type: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all templates with optional filters
    
    Requires authentication.
    """
    templates = TestTemplateService.get_templates(
        db=db,
        skip=skip,
        limit=limit,
        template_type=template_type,
        category_id=category_id,
        is_active=is_active
    )
    
    # Get total count (simplified - in production would use count query)
    total = len(templates)
    
    return {
        "total": total,
        "templates": templates
    }


@router.get("/type/{template_type}", response_model=List[TestTemplateResponse])
def get_templates_by_type(
    template_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all active templates of a specific type
    
    Valid types: api, mobile, e2e, performance
    """
    valid_types = ['api', 'mobile', 'e2e', 'performance']
    if template_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template type. Must be one of: {', '.join(valid_types)}"
        )
    
    templates = TestTemplateService.get_templates_by_type(db, template_type)
    return templates


@router.get("/popular", response_model=List[TestTemplateResponse])
def get_popular_templates(
    db: Session = Depends(deps.get_db),
    limit: int = 10,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get most used templates
    
    Useful for showing recommended templates to users.
    """
    templates = TestTemplateService.get_popular_templates(db, limit)
    return templates


@router.get("/best", response_model=List[TestTemplateResponse])
def get_best_templates(
    db: Session = Depends(deps.get_db),
    limit: int = 10,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get templates with highest success rate
    
    Only includes templates used at least 5 times.
    """
    templates = TestTemplateService.get_best_templates(db, limit)
    return templates


@router.get("/{template_id}", response_model=TestTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get template by ID
    """
    template = TestTemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.put("/{template_id}", response_model=TestTemplateResponse)
def update_template(
    template_id: int,
    template_update: TestTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update template
    
    System templates cannot be updated.
    """
    template = TestTemplateService.update_template(
        db,
        template_id,
        **template_update.model_dump(exclude_unset=True)
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be updated (system template)"
        )
    
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete template
    
    System templates cannot be deleted.
    This will also delete all scenarios generated from this template.
    """
    success = TestTemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be deleted (system template)"
        )


@router.post("/{template_id}/clone", response_model=TestTemplateResponse, status_code=status.HTTP_201_CREATED)
def clone_template(
    template_id: int,
    clone_request: TestTemplateCloneRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Clone an existing template with a new name
    
    Useful for creating variations of templates.
    """
    cloned = TestTemplateService.clone_template(
        db,
        template_id,
        clone_request.new_name,
        current_user.id
    )
    
    if not cloned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return cloned


@router.get("/{template_id}/stats", response_model=TestTemplateStatsResponse)
def get_template_stats(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get template usage statistics
    """
    template = TestTemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Count scenarios
    from app.models.test_scenario import TestScenario
    total_scenarios = db.query(TestScenario).filter(TestScenario.template_id == template_id).count()
    active_scenarios = db.query(TestScenario)\
        .filter(TestScenario.template_id == template_id)\
        .filter(TestScenario.status.in_(['ready', 'validated']))\
        .count()
    
    return {
        "id": template.id,
        "name": template.name,
        "template_type": template.template_type,
        "usage_count": template.usage_count,
        "success_rate": template.success_rate,
        "total_scenarios": total_scenarios,
        "active_scenarios": active_scenarios
    }
