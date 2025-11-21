"""Pagination helper schemas."""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database query."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Get limit value for database query."""
        return self.per_page
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 1,
                "per_page": 20
            }
        }
    }


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")
    
    @classmethod
    def create(cls, total: int, page: int, per_page: int):
        """Create pagination metadata from parameters."""
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        return cls(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams):
        """Create paginated response from items and parameters."""
        return cls(
            items=items,
            pagination=PaginationMeta.create(
                total=total,
                page=params.page,
                per_page=params.per_page
            )
        )

