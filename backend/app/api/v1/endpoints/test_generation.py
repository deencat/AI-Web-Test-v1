"""Test generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.test_case import TestGenerationRequest, TestGenerationResponse
from app.services.test_generation import TestGenerationService

router = APIRouter()


@router.post("/generate", response_model=TestGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_test_cases(
    request: TestGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate test cases using LLM based on requirements.
    
    **Authentication Required**
    
    **Request Body:**
    - `requirement`: Feature or requirement description (10-2000 chars)
    - `test_type`: Optional test type filter (e2e, unit, integration, api)
    - `num_tests`: Number of tests to generate (1-10, default: 3)
    - `model`: Optional specific model to use
    - `category_id`: Optional KB category ID for context (NEW - Sprint 2 Day 11)
    - `use_kb_context`: Whether to include KB context if available (default: true)
    - `max_kb_docs`: Maximum KB documents to include (1-20, default: 10)
    
    **Response:**
    - `test_cases`: Array of generated test cases
    - `metadata`: Generation metadata (model used, tokens, KB context used, etc.)
    
    **Example (with KB context):**
    ```json
    {
        "requirement": "User can submit CRM service request through billing portal",
        "test_type": "e2e",
        "num_tests": 3,
        "category_id": 1,
        "use_kb_context": true,
        "max_kb_docs": 5
    }
    ```
    
    **Example (without KB context):**
    ```json
    {
        "requirement": "User can login with username and password",
        "test_type": "e2e",
        "num_tests": 3
    }
    ```
    
    **Note**: When category_id is provided, the generator will use Knowledge Base documents
    from that category to generate more accurate, domain-specific test cases with proper
    field names, workflows, and test data.
    """
    try:
        # Initialize test generation service
        service = TestGenerationService()
        
        # Generate tests (with optional KB context)
        result = await service.generate_tests(
            requirement=request.requirement,
            test_type=request.test_type.value if request.test_type else None,
            num_tests=request.num_tests,
            model=request.model,
            category_id=request.category_id,
            db=db,
            use_kb_context=request.use_kb_context,
            max_kb_docs=request.max_kb_docs
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post("/generate/page", response_model=TestGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_page_tests(
    page_name: str,
    page_description: str,
    num_tests: int = 5,
    model: str = None,
    category_id: int = None,
    use_kb_context: bool = True,
    max_kb_docs: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate E2E test cases for a specific page.
    
    **Authentication Required**
    
    **Query Parameters:**
    - `page_name`: Name of the page (e.g., "Login Page")
    - `page_description`: Description of page functionality
    - `num_tests`: Number of tests to generate (default: 5)
    - `model`: Optional specific model to use
    - `category_id`: Optional KB category ID for context (NEW - Sprint 2 Day 11)
    - `use_kb_context`: Whether to include KB context (default: true)
    - `max_kb_docs`: Maximum KB documents to include (1-20, default: 10)
    
    **Response:**
    - `test_cases`: Array of generated E2E test cases
    - `metadata`: Generation metadata (includes KB context info)
    """
    try:
        service = TestGenerationService()
        
        result = await service.generate_tests_for_page(
            page_name=page_name,
            page_description=page_description,
            num_tests=num_tests,
            model=model,
            category_id=category_id,
            db=db,
            use_kb_context=use_kb_context,
            max_kb_docs=max_kb_docs
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post("/generate/api", response_model=TestGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_api_tests(
    endpoint: str,
    method: str,
    description: str,
    num_tests: int = 4,
    model: str = None,
    category_id: int = None,
    use_kb_context: bool = True,
    max_kb_docs: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate API test cases for an endpoint.
    
    **Authentication Required**
    
    **Query Parameters:**
    - `endpoint`: API endpoint path (e.g., "/api/v1/users")
    - `method`: HTTP method (GET, POST, PUT, DELETE)
    - `description`: What the endpoint does
    - `num_tests`: Number of tests to generate (default: 4)
    - `model`: Optional specific model to use
    - `category_id`: Optional KB category ID for context (NEW - Sprint 2 Day 11)
    - `use_kb_context`: Whether to include KB context (default: true)
    - `max_kb_docs`: Maximum KB documents to include (1-20, default: 10)
    
    **Response:**
    - `test_cases`: Array of generated API test cases
    - `metadata`: Generation metadata (includes KB context info)
    """
    try:
        service = TestGenerationService()
        
        result = await service.generate_api_tests(
            endpoint=endpoint,
            method=method.upper(),
            description=description,
            num_tests=num_tests,
            model=model,
            category_id=category_id,
            db=db,
            use_kb_context=use_kb_context,
            max_kb_docs=max_kb_docs
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )

