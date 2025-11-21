"""Performance timing middleware."""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add timing information to responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add timing headers."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id
        
        # Log slow requests (> 1 second)
        if process_time > 1.0:
            print(
                f"[SLOW REQUEST] {request.method} {request.url.path} "
                f"took {process_time:.2f}s (Request ID: {request_id})"
            )
        
        return response


def add_timing_middleware(app):
    """Add timing middleware to FastAPI app."""
    app.add_middleware(TimingMiddleware)

