"""
Pydantic schemas for EmailCredential — Sprint 10.10.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailCredentialCreate(BaseModel):
    """Request body for creating a new email credential."""

    label: str = Field(..., min_length=1, max_length=100, description="Human-readable label")
    imap_host: str = Field(..., min_length=1, max_length=255, description="IMAP server hostname")
    imap_port: int = Field(993, ge=1, le=65535, description="IMAP port (default: 993 for TLS)")
    email_address: str = Field(..., min_length=1, max_length=255, description="Email address / username")
    app_password: str = Field(..., min_length=1, description="App password (never stored in plaintext)")


class EmailCredentialUpdate(BaseModel):
    """Request body for updating an existing email credential (all fields optional)."""

    label: Optional[str] = Field(None, min_length=1, max_length=100)
    imap_host: Optional[str] = Field(None, min_length=1, max_length=255)
    imap_port: Optional[int] = Field(None, ge=1, le=65535)
    email_address: Optional[str] = Field(None, min_length=1, max_length=255)
    app_password: Optional[str] = Field(None, min_length=1, description="Leave unset to keep existing password")


class EmailCredentialResponse(BaseModel):
    """Response body — never exposes the encrypted password."""

    id: int
    label: str
    imap_host: str
    imap_port: int
    email_address: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
