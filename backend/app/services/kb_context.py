"""Knowledge Base Context Service for Test Generation Integration."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.kb_document import KBDocument, KBCategory
from app.crud.kb_document import get_documents


class KBContextService:
    """Service for retrieving and formatting KB documents for LLM context."""
    
    def __init__(self):
        """Initialize KB Context Service."""
        pass
    
    async def get_category_context(
        self,
        db: Session,
        category_id: Optional[int] = None,
        max_docs: int = 10,
        max_chars_per_doc: int = 3000
    ) -> str:
        """
        Retrieve KB documents from a specific category and format for LLM context.
        
        Args:
            db: Database session
            category_id: KB category ID to filter by (e.g., 1=System Guide, 2=Product Info)
            max_docs: Maximum number of documents to include (default: 10)
            max_chars_per_doc: Maximum characters per document (default: 3000)
            
        Returns:
            Formatted string containing KB document content for LLM context
            
        Example Output:
            ```
            === Knowledge Base Documents (Category: CRM) ===
            
            [Document 1: CRM User Guide.pdf]
            Category: System Guide
            Content:
            The CRM system login process requires...
            
            [Document 2: CRM Field Definitions.pdf]
            Category: Reference
            Content:
            Customer ID field: Unique identifier...
            ```
        """
        # Get documents from the specified category (or all categories if None)
        documents = get_documents(
            db=db,
            category_id=category_id,  # None = all categories
            limit=max_docs
        )
        
        if not documents:
            return ""
        
        # Get category name for header
        if category_id:
            category = db.query(KBCategory).filter(KBCategory.id == category_id).first()
            category_name = category.name if category else f"Category {category_id}"
        else:
            category_name = "All Categories"
        
        # Format KB context
        context_parts = [
            f"=== Knowledge Base Documents (Category: {category_name}) ===",
            "",
            f"The following {len(documents)} document(s) contain relevant information:",
            ""
        ]
        
        for idx, doc in enumerate(documents, 1):
            # Extract content (truncate if too long)
            content = doc.content or "No content extracted"
            if len(content) > max_chars_per_doc:
                content = content[:max_chars_per_doc] + "... [truncated]"
            
            # Format document section
            doc_section = [
                f"[Document {idx}: {doc.title}]",
                f"Category: {doc.category.name if doc.category else 'Unknown'}",
                f"Type: {doc.file_type.value}",
                f"Content:",
                content,
                ""  # Empty line between documents
            ]
            
            context_parts.extend(doc_section)
        
        # Add instructions for using KB context
        context_parts.extend([
            "=== Instructions for Using KB Documents ===",
            "- Reference specific document names when generating test steps",
            "- Use exact field names and UI paths mentioned in the documents",
            "- Include realistic test data from the documents",
            "- Cite sources in format: '(per [Document Name] Section X)' or '(ref: [Document Name])'",
            "- Validate test assertions against documented procedures",
            ""
        ])
        
        return "\n".join(context_parts)
    
    async def get_relevant_documents(
        self,
        db: Session,
        requirement: str,
        category_id: Optional[int] = None,
        max_docs: int = 5
    ) -> List[KBDocument]:
        """
        Retrieve KB documents relevant to a requirement.
        
        This is a basic implementation. In future, this could use:
        - Vector similarity search
        - Full-text search ranking
        - Semantic search with embeddings
        
        Args:
            db: Database session
            requirement: The test requirement text
            category_id: Optional category filter
            max_docs: Maximum documents to return
            
        Returns:
            List of relevant KBDocument objects
        """
        # For now, just return documents from category (if specified)
        # Future enhancement: Add semantic search, keyword matching, etc.
        
        documents = get_documents(
            db=db,
            category_id=category_id,
            limit=max_docs
        )
        
        return documents
    
    async def increment_reference_count(
        self,
        db: Session,
        document_id: int
    ) -> bool:
        """
        Increment the reference count for a KB document.
        
        Args:
            db: Database session
            document_id: ID of the document that was referenced
            
        Returns:
            True if successful, False otherwise
        """
        try:
            document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
            if document:
                document.referenced_count += 1
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
    
    async def get_kb_statistics(
        self,
        db: Session,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about KB usage.
        
        Args:
            db: Database session
            category_id: Optional category filter
            
        Returns:
            Dictionary with KB statistics
        """
        query = db.query(KBDocument)
        
        if category_id:
            query = query.filter(KBDocument.category_id == category_id)
        
        total_docs = query.count()
        total_references = db.query(func.sum(KBDocument.referenced_count)).scalar() or 0
        
        stats = {
            "total_documents": total_docs,
            "total_references": int(total_references),
            "average_references_per_doc": round(total_references / total_docs, 2) if total_docs > 0 else 0
        }
        
        if category_id:
            category = db.query(KBCategory).filter(KBCategory.id == category_id).first()
            stats["category_name"] = category.name if category else "Unknown"
        
        return stats
    
    def format_kb_citation(
        self,
        document_title: str,
        section: Optional[str] = None
    ) -> str:
        """
        Format a KB citation for inclusion in test steps.
        
        Args:
            document_title: Title of the KB document
            section: Optional section reference
            
        Returns:
            Formatted citation string
            
        Example:
            "(per CRM_User_Guide.pdf Section 2.1)"
            "(ref: Payment_Gateway_API.pdf)"
        """
        if section:
            return f"(per {document_title} Section {section})"
        else:
            return f"(ref: {document_title})"
