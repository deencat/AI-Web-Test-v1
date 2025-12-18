"""Pydantic schemas for Knowledge Base documents."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from app.models.kb_document import FileType


# ============================================================================
# Category Schemas
# ============================================================================

class KBCategoryBase(BaseModel):
    """Base KB category schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")


class KBCategoryCreate(KBCategoryBase):
    """Schema for creating a KB category."""
    pass


class KBCategoryUpdate(BaseModel):
    """Schema for updating a KB category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")


class KBCategoryResponse(KBCategoryBase):
    """Schema for KB category response."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Document Schemas
# ============================================================================

class KBDocumentBase(BaseModel):
    """Base KB document schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    category_id: int = Field(..., description="Category ID")


class KBDocumentCreate(KBDocumentBase):
    """Schema for creating a KB document (used internally after upload)."""
    filename: str
    file_path: str
    file_type: FileType
    file_size: int
    content: Optional[str] = None


class KBDocumentUpdate(BaseModel):
    """Schema for updating a KB document."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None


class KBDocumentResponse(KBDocumentBase):
    """Schema for KB document response."""
    id: int
    filename: str
    file_path: str
    file_type: FileType
    file_size: int
    content: Optional[str] = None
    referenced_count: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    category: KBCategoryResponse
    
    model_config = ConfigDict(from_attributes=True)


class KBDocumentListItem(BaseModel):
    """Schema for KB document in list view (without content)."""
    id: int
    title: str
    description: Optional[str]
    filename: str
    file_type: FileType
    file_size: int
    referenced_count: int
    created_at: datetime
    updated_at: datetime
    category: KBCategoryResponse
    
    model_config = ConfigDict(from_attributes=True)


class KBDocumentListResponse(BaseModel):
    """Schema for paginated KB document list."""
    items: List[KBDocumentListItem]
    total: int
    skip: int
    limit: int


# ============================================================================
# Upload Schemas
# ============================================================================

class KBUploadResponse(BaseModel):
    """Schema for file upload response."""
    id: int
    title: str
    filename: str
    file_type: FileType
    file_size: int
    category_id: int
    message: str = "File uploaded successfully"
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Statistics Schemas
# ============================================================================

class KBStatistics(BaseModel):
    """Schema for KB statistics."""
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    by_category: Dict[str, int]  # category_name: count
    by_file_type: Dict[str, int]  # file_type: count
    most_referenced: Optional[List[Dict[str, Any]]] = None  # top 5 referenced docs


# ============================================================================
# Search/Filter Schemas
# ============================================================================

class KBSearchRequest(BaseModel):
    """Schema for KB search request."""
    query: Optional[str] = Field(None, min_length=1, max_length=255, description="Search query")
    category_id: Optional[int] = Field(None, description="Filter by category")
    file_type: Optional[FileType] = Field(None, description="Filter by file type")
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum records to return")

