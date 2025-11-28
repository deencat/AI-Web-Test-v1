"""Rate limiting configuration using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    
    Uses IP address by default, but can be extended to use
    user ID for authenticated requests.
    """
    # Try to get user from request state (if authenticated)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["200/hour", "50/minute"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down.",
                "details": {
                    "retry_after": exc.detail if hasattr(exc, "detail") else "60 seconds"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        headers={"Retry-After": "60"}
    )


# Endpoint-specific rate limits (can be imported and used as decorators)
STRICT_LIMITS = "10/minute"  # For sensitive operations (login, register, password reset)
NORMAL_LIMITS = "50/minute"  # For regular API operations
GENEROUS_LIMITS = "100/minute"  # For read-only operations
