"""REST endpoints for user-defined test categories."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import test_category as crud
from app.models.user import User
from app.schemas.test_category import (
    TestCategoryCreate,
    TestCategoryListItem,
    TestCategoryListResponse,
    TestCategoryResponse,
    TestCategoryUpdate,
)

router = APIRouter()


def _get_category_or_404(category_id: int, user_id: int, db: Session):
    category = crud.get_test_category(db=db, category_id=category_id, user_id=user_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test category not found",
        )
    return category


@router.get("", response_model=TestCategoryListResponse)
def list_test_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List the current user's test categories with test counts.

    **Authentication Required**
    """
    categories = crud.get_test_categories(db=db, user_id=current_user.id)
    items = []
    for category in categories:
        item = TestCategoryListItem.model_validate(category)
        item.test_count = crud.get_test_count_for_category(db=db, category_id=category.id)
        items.append(item)
    return TestCategoryListResponse(items=items)


@router.post("", response_model=TestCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_test_category(
    body: TestCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new test category for the current user.

    **Authentication Required**

    **Errors:**
    - 409: Duplicate category name for this user
    """
    existing = crud.get_test_category_by_name(
        db=db,
        name=body.name,
        user_id=current_user.id,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category named '{body.name}' already exists",
        )

    try:
        return crud.create_test_category(
            db=db,
            category=body,
            user_id=current_user.id,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category named '{body.name}' already exists",
        )


@router.get("/{category_id}", response_model=TestCategoryResponse)
def get_test_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a single test category by ID.

    **Authentication Required**

    **Errors:**
    - 404: Category not found or not owned by current user
    """
    return _get_category_or_404(category_id, current_user.id, db)


@router.put("/{category_id}", response_model=TestCategoryResponse)
def update_test_category(
    category_id: int,
    body: TestCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a test category.

    **Authentication Required**

    **Errors:**
    - 404: Category not found or not owned by current user
    - 409: Duplicate category name for this user
    """
    _get_category_or_404(category_id, current_user.id, db)

    if body.name:
        existing = crud.get_test_category_by_name(
            db=db,
            name=body.name,
            user_id=current_user.id,
        )
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A category named '{body.name}' already exists",
            )

    try:
        updated = crud.update_test_category(
            db=db,
            category_id=category_id,
            user_id=current_user.id,
            updates=body,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test category not found",
        )
    return updated


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a test category and uncategorize affected tests.

    Sets `test_category_id = NULL` on all tests that referenced this category.

    **Authentication Required**

    **Errors:**
    - 404: Category not found or not owned by current user
    """
    deleted = crud.delete_test_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test category not found",
        )
    return None
