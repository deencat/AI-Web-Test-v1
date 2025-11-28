"""Password Reset Schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password endpoint."""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password endpoint."""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123xyz789",
                "new_password": "NewSecurePass123"
            }
        }


class PasswordResetTokenResponse(BaseModel):
    """Response schema for password reset token."""
    id: int
    user_id: int
    expires_at: datetime
    is_used: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password endpoint."""
    message: str
    token_expires_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "If the email exists, a password reset link has been sent",
                "token_expires_at": "2025-11-29T12:00:00Z"
            }
        }


class ResetPasswordResponse(BaseModel):
    """Response schema for reset password endpoint."""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Password has been reset successfully"
            }
        }
