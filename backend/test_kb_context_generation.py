"""
Integration tests for KB-aware test generation (Sprint 2 Day 11).

Tests verify that:
1. KB context service retrieves and formats documents correctly
2. Test generation service integrates KB context into prompts
3. Generated tests reference KB documents appropriately
4. KB statistics tracking works correctly
"""

import pytest
import asyncio
from sqlalchemy.orm import Session

from app.services.kb_context import KBContextService
from app.services.test_generation import TestGenerationService
from app.crud import kb_document as kb_crud
from app.schemas.kb_document import KBDocumentCreate, KBCategoryCreate


class TestKBContextService:
    """Test KB context retrieval and formatting."""
    
    def test_get_category_context_with_documents(self, db_session: Session, sample_kb_category):
        """Test retrieving KB context for a category with documents."""
        # Create test category and documents
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="CRM",
            description="Customer Relationship Management"
        ))
        
        doc1 = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="CRM_User_Guide.pdf",
            category_id=category.id,
            extracted_text="""
            Section 2.1: Creating Service Requests
            
            To create a new service request:
            1. Navigate to Service Requests > New Request
            2. Select request type from dropdown (Technical, Billing, General)
            3. Fill in required fields:
               - Customer ID (numeric, 10 digits)
               - Priority (High, Medium, Low)
               - Subject (max 100 characters)
               - Description (max 2000 characters)
            4. Click "Submit Request"
            
            Expected result: Request ID generated in format SR-YYYYMMDD-XXXX
            """
        ))
        
        doc2 = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="CRM_API_Reference.pdf",
            category_id=category.id,
            extracted_text="""
            API Endpoint: POST /api/v1/service-requests
            
            Request Body:
            {
                "customer_id": "1234567890",
                "type": "Technical",
                "priority": "High",
                "subject": "System login issues",
                "description": "User cannot access portal after password reset"
            }
            
            Response: 201 Created
            {
                "request_id": "SR-20250110-0042",
                "status": "Open",
                "created_at": "2025-01-10T14:30:00Z"
            }
            """
        ))
        
        # Test context retrieval
        service = KBContextService()
        context = asyncio.run(service.get_category_context(
            db=db_session,
            category_id=category.id,
            max_docs=10
        ))
        
        # Verify context contains documents
        assert context is not None
        assert len(context) > 0
        assert "CRM_User_Guide.pdf" in context
        assert "CRM_API_Reference.pdf" in context
        assert "Section 2.1: Creating Service Requests" in context
        assert "POST /api/v1/service-requests" in context
        
        # Verify formatting includes document headers
        assert "[Document " in context
        assert "[End Document]" in context
        
    def test_get_category_context_empty(self, db_session: Session):
        """Test retrieving KB context for category with no documents."""
        # Create category with no documents
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="EmptyCategory",
            description="Category with no documents"
        ))
        
        service = KBContextService()
        context = asyncio.run(service.get_category_context(
            db=db_session,
            category_id=category.id,
            max_docs=10
        ))
        
        # Should return empty string
        assert context == ""
        
    def test_max_docs_limit(self, db_session: Session):
        """Test that max_docs parameter limits document count."""
        # Create category with multiple documents
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="TestCategory",
            description="Category for max docs test"
        ))
        
        # Create 5 documents
        for i in range(5):
            kb_crud.create_document(db_session, KBDocumentCreate(
                filename=f"Document_{i}.pdf",
                category_id=category.id,
                extracted_text=f"Content of document {i}"
            ))
        
        service = KBContextService()
        
        # Request only 2 documents
        context = asyncio.run(service.get_category_context(
            db=db_session,
            category_id=category.id,
            max_docs=2
        ))
        
        # Count document markers
        doc_count = context.count("[Document ")
        assert doc_count == 2


class TestKBIntegratedGeneration:
    """Test test generation with KB context integration."""
    
    @pytest.mark.asyncio
    async def test_generate_with_kb_context(self, db_session: Session):
        """Test generating tests with KB context."""
        # Create KB category and document
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="Billing",
            description="Billing system documentation"
        ))
        
        kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Billing_Portal_Guide.pdf",
            category_id=category.id,
            extracted_text="""
            Section 3: Invoice Management
            
            Users can view and download invoices from the Billing Portal.
            
            Navigation: Dashboard > Billing > Invoices
            
            Invoice List displays:
            - Invoice Number (format: INV-YYYY-NNNNN)
            - Date (MM/DD/YYYY)
            - Amount (USD)
            - Status (Paid, Pending, Overdue)
            - Download button (PDF format)
            
            Search filters:
            - Date range (from/to)
            - Status dropdown
            - Invoice number search
            """
        ))
        
        # Generate tests WITH KB context
        service = TestGenerationService()
        result = await service.generate_tests(
            requirement="User can view and download invoices from billing portal",
            test_type="e2e",
            num_tests=2,
            category_id=category.id,
            db=db_session,
            use_kb_context=True,
            max_kb_docs=5
        )
        
        # Verify result structure
        assert "test_cases" in result
        assert "metadata" in result
        assert len(result["test_cases"]) > 0
        
        # Verify metadata includes KB context info
        metadata = result["metadata"]
        assert metadata["kb_context_used"] is True
        assert metadata["kb_category_id"] == category.id
        assert metadata["kb_documents_used"] > 0
        
        # Check if test cases reference KB content
        test_cases_str = str(result["test_cases"])
        
        # Should contain KB-specific terminology
        kb_terms_found = any(term in test_cases_str for term in [
            "Billing Portal",
            "Invoice",
            "INV-",
            "Download",
            "PDF"
        ])
        
        assert kb_terms_found, "Generated tests should reference KB content"
        
    @pytest.mark.asyncio
    async def test_generate_without_kb_context(self, db_session: Session):
        """Test generating tests WITHOUT KB context (baseline)."""
        service = TestGenerationService()
        
        # Generate tests without KB context
        result = await service.generate_tests(
            requirement="User can view and download invoices",
            test_type="e2e",
            num_tests=2,
            category_id=None,  # No category
            db=db_session,
            use_kb_context=True,
            max_kb_docs=5
        )
        
        # Verify result structure
        assert "test_cases" in result
        assert "metadata" in result
        
        # Verify metadata shows NO KB context used
        metadata = result["metadata"]
        assert metadata["kb_context_used"] is False
        assert metadata["kb_category_id"] is None
        assert metadata["kb_documents_used"] == 0
        
    @pytest.mark.asyncio
    async def test_kb_context_disabled(self, db_session: Session):
        """Test that use_kb_context=False disables KB context."""
        # Create KB category and document
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="TestCategory",
            description="Test category"
        ))
        
        kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Test_Doc.pdf",
            category_id=category.id,
            extracted_text="Test content"
        ))
        
        service = TestGenerationService()
        
        # Generate tests with category_id but use_kb_context=False
        result = await service.generate_tests(
            requirement="Test requirement",
            test_type="e2e",
            num_tests=1,
            category_id=category.id,
            db=db_session,
            use_kb_context=False,  # Explicitly disabled
            max_kb_docs=5
        )
        
        # Verify KB context was NOT used despite category_id being provided
        metadata = result["metadata"]
        assert metadata["kb_context_used"] is False
        

class TestKBStatistics:
    """Test KB usage statistics tracking."""
    
    def test_increment_reference_count(self, db_session: Session):
        """Test that KB document reference counts are incremented."""
        # Create KB document
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="TestCategory",
            description="Test"
        ))
        
        doc = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Test.pdf",
            category_id=category.id,
            extracted_text="Test content"
        ))
        
        initial_count = doc.reference_count or 0
        
        # Increment reference count
        service = KBContextService()
        service.increment_reference_count(db=db_session, document_id=doc.id)
        
        # Verify count increased
        db_session.refresh(doc)
        assert doc.reference_count == initial_count + 1
        
    def test_get_kb_statistics(self, db_session: Session):
        """Test retrieving KB usage statistics."""
        # Create category with multiple documents
        category = kb_crud.create_category(db_session, KBCategoryCreate(
            name="StatsCategory",
            description="Category for stats test"
        ))
        
        # Create 3 documents with different reference counts
        doc1 = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Doc1.pdf",
            category_id=category.id,
            extracted_text="Content 1"
        ))
        doc1.reference_count = 5
        
        doc2 = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Doc2.pdf",
            category_id=category.id,
            extracted_text="Content 2"
        ))
        doc2.reference_count = 10
        
        doc3 = kb_crud.create_document(db_session, KBDocumentCreate(
            filename="Doc3.pdf",
            category_id=category.id,
            extracted_text="Content 3"
        ))
        doc3.reference_count = 3
        
        db_session.commit()
        
        # Get statistics
        service = KBContextService()
        stats = service.get_kb_statistics(db=db_session, category_id=category.id)
        
        # Verify statistics
        assert stats["total_documents"] == 3
        assert stats["total_references"] == 18  # 5 + 10 + 3
        assert "most_referenced" in stats
        assert stats["most_referenced"]["filename"] == "Doc2.pdf"
        assert stats["most_referenced"]["count"] == 10


# Pytest fixtures
@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use the same database session setup as the application
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_kb_category(db_session):
    """Create a sample KB category for testing."""
    category = kb_crud.create_category(db_session, KBCategoryCreate(
        name="Sample CRM",
        description="Sample CRM documentation"
    ))
    yield category
    # Cleanup after test
    db_session.delete(category)
    db_session.commit()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
