"""
CRUD helpers for StepLibraryModule — Sprint 10.11.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.step_library_module import StepLibraryModule
from app.schemas.step_library_module import StepLibraryModuleCreate, StepLibraryModuleUpdate


def list_modules(db: Session, user_id: int) -> List[StepLibraryModule]:
    """Return all step library modules owned by the user, ordered by name."""
    return (
        db.query(StepLibraryModule)
        .filter(StepLibraryModule.user_id == user_id)
        .order_by(StepLibraryModule.name)
        .all()
    )


def get_by_id(db: Session, module_id: int, user_id: int) -> Optional[StepLibraryModule]:
    """Return a single module by ID, scoped to the user."""
    return (
        db.query(StepLibraryModule)
        .filter(
            StepLibraryModule.id == module_id,
            StepLibraryModule.user_id == user_id,
        )
        .first()
    )


def get_by_name(db: Session, name: str, user_id: int) -> Optional[StepLibraryModule]:
    """Return a module by slug name, scoped to the user."""
    return (
        db.query(StepLibraryModule)
        .filter(
            StepLibraryModule.name == name,
            StepLibraryModule.user_id == user_id,
        )
        .first()
    )


def create_module(
    db: Session,
    schema: StepLibraryModuleCreate,
    user_id: int,
) -> StepLibraryModule:
    """Create a new step library module."""
    module = StepLibraryModule(
        user_id=user_id,
        name=schema.name,
        display_name=schema.display_name,
        description=schema.description,
        steps=schema.steps,
        parameters=schema.parameters,
        tags=schema.tags,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def update_module(
    db: Session,
    module: StepLibraryModule,
    schema: StepLibraryModuleUpdate,
) -> StepLibraryModule:
    """Apply a partial update to a module."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(module, field, value)
    db.commit()
    db.refresh(module)
    return module


def delete_module(db: Session, module_id: int, user_id: int) -> bool:
    """Delete a module by ID scoped to user. Returns True if deleted, False if not found."""
    module = get_by_id(db=db, module_id=module_id, user_id=user_id)
    if not module:
        return False
    db.delete(module)
    db.commit()
    return True


def get_usage_count(db: Session, module_name: str) -> int:
    """
    Count how many test cases reference @module:name in their steps.
    This is a best-effort scan — returns 0 if scan cannot be performed.
    """
    from app.models.test_case import TestCase
    import json

    try:
        pattern = f"@module:{module_name}"
        test_cases = db.query(TestCase).all()
        count = 0
        for tc in test_cases:
            steps = tc.steps or []
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except (json.JSONDecodeError, TypeError):
                    steps = []
            for step in steps:
                step_text = step if isinstance(step, str) else step.get("description", "")
                if pattern in step_text:
                    count += 1
                    break  # Count test case once even if it ref the module multiple times
        return count
    except Exception:
        return 0
