"""Custom exception classes for the API."""
from typing import Optional, Dict, Any


class APIException(Exception):
    """Base exception for all API errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIException):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(APIException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with ID '{id}' not found",
            code="NOT_FOUND",
            status_code=404
        )


class UnauthorizedError(APIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401
        )


class ForbiddenError(APIException):
    """Raised when user doesn't have permission."""
    
    def __init__(self, message: str = "You don't have permission to access this resource"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )


class ConflictError(APIException):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class BadRequestError(APIException):
    """Raised for general bad requests."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details
        )


class InternalServerError(APIException):
    """Raised for internal server errors."""
    
    def __init__(self, message: str = "An internal server error occurred"):
        super().__init__(
            message=message,
            code="INTERNAL_SERVER_ERROR",
            status_code=500
        )


class ServiceUnavailableError(APIException):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(self, service: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"{service} is temporarily unavailable",
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service}
        )


class RateLimitError(APIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )

