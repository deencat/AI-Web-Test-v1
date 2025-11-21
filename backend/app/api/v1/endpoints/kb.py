"""Knowledge Base API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.kb_document import FileType
from app.schemas.kb_document import (
    KBCategoryCreate,
    KBCategoryResponse,
    KBDocumentCreate,
    KBDocumentUpdate,
    KBDocumentResponse,
    KBDocumentListItem,
    KBDocumentListResponse,
    KBUploadResponse,
    KBStatistics
)
from app.crud import kb_document as crud
from app.services.file_upload import FileUploadService

router = APIRouter()
file_service = FileUploadService()


# ============================================================================
# Category Endpoints
# ============================================================================

@router.get("/categories", response_model=List[KBCategoryResponse])
def list_categories(
    db: Session = Depends(deps.get_db)
):
    """
    List all KB categories.
    
    **No authentication required** (read-only)
    
    Returns all predefined and custom categories.
    """
    categories = crud.get_categories(db)
    return categories


@router.post("/categories", response_model=KBCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: KBCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Create a new KB category.
    
    **Admin only**
    
    Creates a custom category for organizing documents.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    # Check if category already exists
    existing = crud.get_category_by_name(db, category.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category.name}' already exists"
        )
    
    return crud.create_category(db, category)


# ============================================================================
# Document Upload
# ============================================================================

@router.post("/upload", response_model=KBUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload (PDF, DOCX, TXT, MD)"),
    title: str = Form(..., description="Document title"),
    category_id: int = Form(..., description="Category ID"),
    description: Optional[str] = Form(None, description="Document description"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Upload a document to the Knowledge Base.
    
    **Authentication required**
    
    Accepts PDF, DOCX, TXT, or MD files up to 10MB.
    Automatically extracts text content for search.
    
    **Form Data:**
    - `file`: The file to upload
    - `title`: Title for the document
    - `category_id`: ID of the category
    - `description`: Optional description
    """
    # Verify category exists
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Save file
    try:
        file_path, file_type, file_size = await file_service.save_file(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Extract text content
    content = await file_service.extract_text(file_path, file_type)
    
    # Create document record
    document_create = KBDocumentCreate(
        title=title,
        description=description,
        category_id=category_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        content=content
    )
    
    document = crud.create_document(db, document_create, current_user.id)
    
    return KBUploadResponse(
        id=document.id,
        title=document.title,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        category_id=document.category_id,
        message="File uploaded successfully"
    )


# ============================================================================
# Document Management
# ============================================================================

@router.get("", response_model=KBDocumentListResponse)
def list_documents(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    search: Optional[str] = Query(None, description="Search in title, description, content"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    List KB documents with optional filtering.
    
    **Authentication required**
    
    Non-admin users see only their own documents.
    Admins see all documents.
    
    **Query Parameters:**
    - `category_id`: Filter by category
    - `file_type`: Filter by file type (pdf, docx, txt, md)
    - `search`: Search query
    - `skip`: Pagination offset
    - `limit`: Max results per page
    """
    # Non-admin users can only see their own documents
    user_filter = None if current_user.role == "admin" else current_user.id
    
    documents = crud.get_documents(
        db=db,
        user_id=user_filter,
        category_id=category_id,
        file_type=file_type,
        search_query=search,
        skip=skip,
        limit=limit
    )
    
    total = crud.get_document_count(
        db=db,
        user_id=user_filter,
        category_id=category_id,
        file_type=file_type,
        search_query=search
    )
    
    # Convert to list items (without full content)
    items = [KBDocumentListItem.model_validate(doc) for doc in documents]
    
    return KBDocumentListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=KBStatistics)
def get_statistics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get KB statistics.
    
    **Authentication required**
    
    Returns statistics for current user's documents.
    Admins see statistics for all documents.
    """
    user_filter = None if current_user.role == "admin" else current_user.id
    stats = crud.get_kb_statistics(db, user_filter)
    return KBStatistics(**stats)


@router.get("/{document_id}", response_model=KBDocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get document details by ID.
    
    **Authentication required**
    
    Returns full document metadata including extracted content.
    Non-admin users can only access their own documents.
    """
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership (unless admin)
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )
    
    # Increment reference count
    crud.increment_reference_count(db, document_id)
    
    return document


@router.put("/{document_id}", response_model=KBDocumentResponse)
def update_document(
    document_id: int,
    updates: KBDocumentUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Update document metadata.
    
    **Authentication required**
    
    Allows updating title, description, and category.
    Non-admin users can only update their own documents.
    """
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership (unless admin)
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this document"
        )
    
    # If updating category, verify it exists
    if updates.category_id is not None:
        category = crud.get_category(db, updates.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {updates.category_id} not found"
            )
    
    updated_document = crud.update_document(db, document_id, updates)
    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Delete a document.
    
    **Authentication required**
    
    Deletes both the database record and the physical file.
    Non-admin users can only delete their own documents.
    """
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership (unless admin)
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )
    
    # Delete file from disk
    await file_service.delete_file(document.file_path)
    
    # Delete database record
    crud.delete_document(db, document_id)
    
    return None


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Download document file.
    
    **Authentication required**
    
    Returns the original file for download.
    Non-admin users can only download their own documents.
    """
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership (unless admin)
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this document"
        )
    
    # Check if file exists
    import os
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Increment reference count
    crud.increment_reference_count(db, document_id)
    
    return FileResponse(
        path=document.file_path,
        filename=document.filename,
        media_type="application/octet-stream"
    )

