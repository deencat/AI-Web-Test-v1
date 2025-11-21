"""Standard response wrapper schemas."""
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


T = TypeVar('T')


class ResponseMetadata(BaseModel):
    """Metadata for API responses."""
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(default="1.0", description="API version")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    @classmethod
    def create(cls, request_id: Optional[str] = None):
        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0",
            request_id=request_id
        )


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    success: bool = Field(True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    meta: ResponseMetadata = Field(..., description="Response metadata")
    
    @classmethod
    def create(cls, data: T, request_id: Optional[str] = None):
        return cls(
            success=True,
            data=data,
            meta=ResponseMetadata.create(request_id)
        )


class ErrorDetail(BaseModel):
    """Error details in response."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    success: bool = Field(False, description="Indicates failed operation")
    error: ErrorDetail = Field(..., description="Error information")
    
    @classmethod
    def create(cls, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        return cls(
            success=False,
            error=ErrorDetail(
                code=code,
                message=message,
                details=details,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
        )


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool = Field(True, description="Indicates successful operation")
    message: str = Field(..., description="Response message")
    meta: ResponseMetadata = Field(..., description="Response metadata")
    
    @classmethod
    def create(cls, message: str, request_id: Optional[str] = None):
        return cls(
            success=True,
            message=message,
            meta=ResponseMetadata.create(request_id)
        )

