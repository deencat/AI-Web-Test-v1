"""CRUD operations for Knowledge Base documents."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.kb_document import KBDocument, KBCategory, FileType
from app.schemas.kb_document import (
    KBCategoryCreate,
    KBCategoryUpdate,
    KBDocumentCreate,
    KBDocumentUpdate
)


# ============================================================================
# Category CRUD
# ============================================================================

def create_category(db: Session, category: KBCategoryCreate) -> KBCategory:
    """Create a new KB category."""
    db_category = KBCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category(db: Session, category_id: int) -> Optional[KBCategory]:
    """Get category by ID."""
    return db.query(KBCategory).filter(KBCategory.id == category_id).first()


def get_category_by_name(db: Session, name: str) -> Optional[KBCategory]:
    """Get category by name."""
    return db.query(KBCategory).filter(KBCategory.name == name).first()


def get_categories(db: Session) -> List[KBCategory]:
    """Get all categories."""
    return db.query(KBCategory).order_by(KBCategory.name).all()


def update_category(db: Session, category_id: int, updates: KBCategoryUpdate) -> Optional[KBCategory]:
    """Update a KB category."""
    category = get_category(db, category_id)
    if not category:
        return None
    
    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    """Delete a category (if no documents reference it)."""
    category = db.query(KBCategory).filter(KBCategory.id == category_id).first()
    if category:
        # Check if any documents reference this category
        doc_count = db.query(KBDocument).filter(KBDocument.category_id == category_id).count()
        if doc_count > 0:
            return False  # Cannot delete category with documents
        
        db.delete(category)
        db.commit()
        return True
    return False


# ============================================================================
# Document CRUD
# ============================================================================

def create_document(db: Session, document: KBDocumentCreate, user_id: int) -> KBDocument:
    """Create a new KB document."""
    db_document = KBDocument(
        **document.model_dump(),
        user_id=user_id,
        referenced_count=0
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_document(db: Session, document_id: int) -> Optional[KBDocument]:
    """Get document by ID."""
    return db.query(KBDocument).filter(KBDocument.id == document_id).first()


def get_documents(
    db: Session,
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    file_type: Optional[FileType] = None,
    search_query: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[KBDocument]:
    """
    Get documents with optional filters.
    
    Args:
        db: Database session
        user_id: Filter by user (None for all users)
        category_id: Filter by category
        file_type: Filter by file type
        search_query: Search in title, description, and content
        skip: Number of records to skip
        limit: Maximum records to return
    """
    query = db.query(KBDocument)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(KBDocument.user_id == user_id)
    
    if category_id is not None:
        query = query.filter(KBDocument.category_id == category_id)
    
    if file_type is not None:
        query = query.filter(KBDocument.file_type == file_type)
    
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                KBDocument.title.ilike(search_pattern),
                KBDocument.description.ilike(search_pattern),
                KBDocument.content.ilike(search_pattern)
            )
        )
    
    # Order by most recent first
    query = query.order_by(KBDocument.created_at.desc())
    
    return query.offset(skip).limit(limit).all()


def get_document_count(
    db: Session,
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    file_type: Optional[FileType] = None,
    search_query: Optional[str] = None
) -> int:
    """Get count of documents matching filters."""
    query = db.query(KBDocument)
    
    if user_id is not None:
        query = query.filter(KBDocument.user_id == user_id)
    
    if category_id is not None:
        query = query.filter(KBDocument.category_id == category_id)
    
    if file_type is not None:
        query = query.filter(KBDocument.file_type == file_type)
    
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                KBDocument.title.ilike(search_pattern),
                KBDocument.description.ilike(search_pattern),
                KBDocument.content.ilike(search_pattern)
            )
        )
    
    return query.count()


def update_document(
    db: Session,
    document_id: int,
    updates: KBDocumentUpdate
) -> Optional[KBDocument]:
    """Update document metadata."""
    db_document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
    
    if db_document:
        update_data = updates.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_document, key, value)
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
    
    return db_document


def delete_document(db: Session, document_id: int) -> bool:
    """Delete a document."""
    db_document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
    
    if db_document:
        db.delete(db_document)
        db.commit()
        return True
    
    return False


def increment_reference_count(db: Session, document_id: int) -> Optional[KBDocument]:
    """Increment the reference count for a document."""
    db_document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
    
    if db_document:
        db_document.referenced_count += 1
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
    
    return db_document


# ============================================================================
# Statistics
# ============================================================================

def get_kb_statistics(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get KB statistics.
    
    Args:
        db: Database session
        user_id: Filter by user (None for all users)
    """
    query = db.query(KBDocument)
    
    if user_id is not None:
        query = query.filter(KBDocument.user_id == user_id)
    
    # Total documents
    total_documents = query.count()
    
    # Total size
    total_size = db.query(func.sum(KBDocument.file_size)).filter(
        KBDocument.user_id == user_id if user_id else True
    ).scalar() or 0
    
    # By category
    by_category = {}
    category_stats = query.join(KBCategory).with_entities(
        KBCategory.name,
        func.count(KBDocument.id)
    ).group_by(KBCategory.name).all()
    
    for category_name, count in category_stats:
        by_category[category_name] = count
    
    # By file type
    by_file_type = {}
    type_stats = query.with_entities(
        KBDocument.file_type,
        func.count(KBDocument.id)
    ).group_by(KBDocument.file_type).all()
    
    for file_type, count in type_stats:
        by_file_type[file_type.value] = count
    
    # Most referenced documents
    most_referenced = query.order_by(
        KBDocument.referenced_count.desc()
    ).limit(5).all()
    
    most_referenced_list = [
        {
            "id": doc.id,
            "title": doc.title,
            "referenced_count": doc.referenced_count,
            "category": doc.category.name
        }
        for doc in most_referenced
    ] if most_referenced else []
    
    return {
        "total_documents": total_documents,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "by_category": by_category,
        "by_file_type": by_file_type,
        "most_referenced": most_referenced_list
    }

