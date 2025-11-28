"""
Test Scenario API Endpoints
Generate and manage test scenarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.user import User
from app.schemas.test_scenario import (
    TestScenarioCreate,
    TestScenarioUpdate,
    TestScenarioResponse,
    TestScenarioListResponse,
    ScenarioGenerationRequest,
    BatchGenerationRequest,
    BatchGenerationResponse,
    ScenarioValidationRequest,
    ScenarioValidationResponse,
    FakerDataRequest,
    FakerDataResponse,
    FakerFieldsResponse
)
from app.services.scenario_generator_service import ScenarioGeneratorService
from app.services.test_validation_service import TestValidationService
from app.services.scenario_converter import ScenarioConverter
from app.schemas.test_case import TestCaseResponse

router = APIRouter()


@router.post("/generate", response_model=TestScenarioResponse, status_code=status.HTTP_201_CREATED)
def generate_scenario(
    *,
    db: Session = Depends(deps.get_db),
    generation_request: ScenarioGenerationRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate a test scenario from a template
    
    This endpoint:
    1. Takes a template ID and context variables
    2. Generates realistic test data using Faker (if enabled)
    3. Expands template steps with actual values
    4. Creates and returns a new scenario
    """
    generator = ScenarioGeneratorService()
    
    try:
        scenario = generator.generate_from_template(
            db=db,
            template_id=generation_request.template_id,
            context=generation_request.context,
            created_by=current_user.id,
            use_ai=generation_request.use_ai,
            generate_data=generation_request.generate_data
        )
        return scenario
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate scenario: {str(e)}"
        )


@router.post("/batch-generate", response_model=BatchGenerationResponse)
def batch_generate_scenarios(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchGenerationRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate multiple scenarios in batch
    
    Useful for creating test suites with variations.
    """
    generator = ScenarioGeneratorService()
    scenarios = []
    errors = []
    
    total_requested = len(batch_request.template_ids) * len(batch_request.variations)
    
    for template_id in batch_request.template_ids:
        for i, variation in enumerate(batch_request.variations):
            # Merge base context with variation
            context = {**batch_request.base_context, **variation}
            
            try:
                scenario = generator.generate_from_template(
                    db=db,
                    template_id=template_id,
                    context=context,
                    created_by=current_user.id
                )
                scenarios.append(scenario)
            except Exception as e:
                errors.append({
                    "template_id": template_id,
                    "variation_index": i,
                    "error": str(e)
                })
    
    return {
        "total_requested": total_requested,
        "generated": len(scenarios),
        "failed": len(errors),
        "scenarios": scenarios,
        "errors": errors
    }


@router.post("/", response_model=TestScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    *,
    db: Session = Depends(deps.get_db),
    scenario_in: TestScenarioCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a test scenario manually (not from template)
    """
    generator = ScenarioGeneratorService()
    
    try:
        scenario = generator.create_scenario(
            db=db,
            name=scenario_in.name,
            description=scenario_in.description,
            template_id=scenario_in.template_id,
            steps=scenario_in.steps,
            dependencies=scenario_in.dependencies,
            test_data=scenario_in.test_data,
            expected_results=scenario_in.expected_results,
            created_by=current_user.id
        )
        return scenario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=TestScenarioListResponse)
def get_scenarios(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    template_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all scenarios with optional filters
    """
    generator = ScenarioGeneratorService()
    scenarios = generator.get_scenarios(
        db=db,
        skip=skip,
        limit=limit,
        status=status_filter,
        template_id=template_id
    )
    
    total = len(scenarios)
    
    return {
        "total": total,
        "scenarios": scenarios
    }


@router.get("/faker-fields", response_model=FakerFieldsResponse)
def get_faker_fields(current_user: User = Depends(deps.get_current_user)):
    """
    Get list of available Faker fields by category
    
    Useful for frontend to show available options when configuring templates.
    """
    generator = ScenarioGeneratorService()
    fields = generator.get_available_faker_fields()
    
    return {
        "fields": fields,
        "description": "Available faker fields organized by category"
    }


@router.get("/{scenario_id}", response_model=TestScenarioResponse)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get scenario by ID
    """
    generator = ScenarioGeneratorService()
    scenario = generator.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    return scenario


@router.put("/{scenario_id}", response_model=TestScenarioResponse)
def update_scenario(
    scenario_id: int,
    scenario_update: TestScenarioUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update scenario
    """
    generator = ScenarioGeneratorService()
    scenario = generator.update_scenario(
        db,
        scenario_id,
        **scenario_update.model_dump(exclude_unset=True)
    )
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete scenario
    """
    generator = ScenarioGeneratorService()
    success = generator.delete_scenario(db, scenario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )


@router.post("/{scenario_id}/validate", response_model=ScenarioValidationResponse)
def validate_scenario(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Validate a scenario
    
    Checks for:
    - Missing required fields
    - Invalid step structure
    - Circular dependencies
    - Missing test data
    
    Also provides suggestions for improvement.
    """
    generator = ScenarioGeneratorService()
    scenario = generator.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    is_valid, errors, warnings = TestValidationService.validate_scenario(scenario)
    suggestions = TestValidationService.suggest_improvements(scenario)
    
    # Update scenario status
    if is_valid:
        scenario.mark_validated(True)
    else:
        scenario.mark_validated(False, errors)
    db.commit()
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions
    }


@router.post("/validate", response_model=ScenarioValidationResponse)
def validate_scenario_json(
    validation_request: ScenarioValidationRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Validate scenario JSON before creating
    
    Useful for frontend validation.
    """
    is_valid, errors = TestValidationService.validate_scenario_json(
        validation_request.model_dump()
    )
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": [],
        "suggestions": []
    }


@router.post("/generate-data", response_model=FakerDataResponse)
def generate_faker_data(
    data_request: FakerDataRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate test data using Faker
    
    Useful for testing data generation or manual scenario creation.
    """
    generator = ScenarioGeneratorService()
    data = generator.generate_faker_data(data_request.data_requirements)
    
    return {
        "data": data
    }


@router.post("/{scenario_id}/convert-to-test", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def convert_scenario_to_test(
    scenario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Convert a validated scenario to an executable test case
    
    **This is the BRIDGE between Day 7 template/scenario system and Sprint 3 execution system.**
    
    Process:
    1. Retrieves validated scenario
    2. Maps scenario steps to Playwright actions
    3. Creates TestCase ready for execution
    4. Links test to original scenario/template
    
    The created test can then be:
    - Executed via POST /api/v1/tests/{id}/execute (Sprint 3)
    - Queued via POST /api/v1/tests/{id}/run (Sprint 3 queue)
    - Managed via standard test endpoints
    
    Requirements:
    - Scenario must have status "validated"
    - User must own the scenario
    
    Returns:
        TestCase ready for execution with Stagehand/Playwright
    """
    from app.crud import test_scenario as crud_scenarios
    
    # Get scenario
    scenario = crud_scenarios.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Verify status
    if scenario.status != "validated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scenario must be validated before conversion. Current status: {scenario.status}"
        )
    
    # Convert to test case
    try:
        test_case = ScenarioConverter.convert_scenario_to_test(
            scenario=scenario,
            user_id=current_user.id,
            db=db
        )
        
        # Update scenario execution count
        scenario.execution_count = (scenario.execution_count or 0) + 1
        db.commit()
        
        return test_case
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert scenario to test: {str(e)}"
        )


@router.post("/batch-convert", response_model=List[TestCaseResponse], status_code=status.HTTP_201_CREATED)
def batch_convert_scenarios(
    scenario_ids: List[int],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Convert multiple validated scenarios to test cases
    
    Useful for batch test generation workflows.
    Only converts scenarios with status "validated".
    """
    test_cases = ScenarioConverter.batch_convert_scenarios(
        scenario_ids=scenario_ids,
        user_id=current_user.id,
        db=db
    )
    
    return test_cases
