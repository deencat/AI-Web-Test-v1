"""Security utilities for input validation and sanitization."""
import re
from typing import Optional
from html import escape
from fastapi import HTTPException, status


class SecurityValidator:
    """Security validation utilities."""
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(--|\#|\/\*)",  # SQL comments
        r"(\bexec\b|\bexecute\b)",
        r"(\bor\b.*=.*)",
        r"(1\s*=\s*1)",
        r"('\s*or\s*'1'\s*=\s*'1)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
        r"<iframe",
        r"<embed",
        r"<object",
    ]
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Sanitize HTML to prevent XSS attacks."""
        if not text:
            return text
        return escape(text)
    
    @classmethod
    def validate_no_sql_injection(cls, text: str, field_name: str = "input") -> None:
        """
        Check for SQL injection patterns.
        Raises HTTPException if suspicious patterns found.
        """
        if not text:
            return
        
        text_lower = text.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name}: Suspicious pattern detected"
                )
    
    @classmethod
    def validate_no_xss(cls, text: str, field_name: str = "input") -> None:
        """
        Check for XSS patterns.
        Raises HTTPException if suspicious patterns found.
        """
        if not text:
            return
        
        text_lower = text.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name}: Potentially unsafe content detected"
                )
    
    @classmethod
    def validate_safe_filename(cls, filename: str) -> None:
        """
        Validate filename to prevent path traversal attacks.
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: Path traversal detected"
            )
        
        # Check for null bytes
        if "\x00" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: Null byte detected"
            )
    
    @classmethod
    def validate_email_format(cls, email: str) -> None:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
    
    @classmethod
    def sanitize_search_query(cls, query: str, max_length: int = 200) -> str:
        """
        Sanitize search query.
        
        Removes dangerous characters while preserving searchability.
        """
        if not query:
            return ""
        
        # Truncate to max length
        query = query[:max_length]
        
        # Remove SQL injection patterns
        query = re.sub(r"[';\"\\]", "", query)
        
        # Remove excessive whitespace
        query = " ".join(query.split())
        
        return query.strip()


def validate_content_security(
    text: Optional[str],
    field_name: str = "input",
    check_sql: bool = True,
    check_xss: bool = True
) -> None:
    """
    Comprehensive content security validation.
    
    Args:
        text: Text to validate
        field_name: Name of field being validated (for error messages)
        check_sql: Whether to check for SQL injection
        check_xss: Whether to check for XSS
    
    Raises:
        HTTPException: If validation fails
    """
    if not text:
        return
    
    if check_sql:
        SecurityValidator.validate_no_sql_injection(text, field_name)
    
    if check_xss:
        SecurityValidator.validate_no_xss(text, field_name)
