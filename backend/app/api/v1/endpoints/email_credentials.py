"""
CRUD endpoints for EmailCredential — Sprint 10.10.

GET    /api/v1/email-credentials         List user's credentials
POST   /api/v1/email-credentials         Create a new credential
PUT    /api/v1/email-credentials/{id}    Update an existing credential
DELETE /api/v1/email-credentials/{id}    Delete a credential

The app password is encrypted before persisting and never returned in responses.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.email_credential import EmailCredential
from app.models.user import User
from app.schemas.email_credential import (
    EmailCredentialCreate,
    EmailCredentialResponse,
    EmailCredentialUpdate,
)
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)
router = APIRouter()

_encryption: EncryptionService | None = None


def _get_encryption() -> EncryptionService:
    """Lazy singleton — avoids ImportError when CREDENTIAL_ENCRYPTION_KEY is unset at test time."""
    global _encryption
    if _encryption is None:
        _encryption = EncryptionService()
    return _encryption


def _get_credential_or_404(credential_id: int, user_id: int, db: Session) -> EmailCredential:
    cred = (
        db.query(EmailCredential)
        .filter(
            EmailCredential.id == credential_id,
            EmailCredential.user_id == user_id,
        )
        .first()
    )
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email credential {credential_id} not found.",
        )
    return cred


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/email-credentials",
    response_model=List[EmailCredentialResponse],
    summary="List email credentials for the current user",
)
def list_email_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(EmailCredential)
        .filter(EmailCredential.user_id == current_user.id)
        .order_by(EmailCredential.created_at)
        .all()
    )


@router.post(
    "/email-credentials",
    response_model=EmailCredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new email credential",
)
def create_email_credential(
    body: EmailCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    encrypted = _get_encryption().encrypt_password(body.app_password)
    cred = EmailCredential(
        user_id=current_user.id,
        label=body.label,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        email_address=body.email_address,
        imap_password_encrypted=encrypted,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    logger.info("EmailCredential created: id=%s user=%s", cred.id, current_user.id)
    return cred


@router.put(
    "/email-credentials/{credential_id}",
    response_model=EmailCredentialResponse,
    summary="Update an existing email credential",
)
def update_email_credential(
    credential_id: int,
    body: EmailCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cred = _get_credential_or_404(credential_id, current_user.id, db)

    if body.label is not None:
        cred.label = body.label
    if body.imap_host is not None:
        cred.imap_host = body.imap_host
    if body.imap_port is not None:
        cred.imap_port = body.imap_port
    if body.email_address is not None:
        cred.email_address = body.email_address
    if body.app_password is not None:
        cred.imap_password_encrypted = _get_encryption().encrypt_password(body.app_password)

    db.commit()
    db.refresh(cred)
    return cred


@router.delete(
    "/email-credentials/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an email credential",
)
def delete_email_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cred = _get_credential_or_404(credential_id, current_user.id, db)
    db.delete(cred)
    db.commit()
    logger.info("EmailCredential deleted: id=%s user=%s", credential_id, current_user.id)
