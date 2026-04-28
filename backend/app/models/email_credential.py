"""
EmailCredential ORM model — Sprint 10.10 IMAP Email OTP.

Stores IMAP credentials for email-based OTP retrieval during test execution.
The IMAP app password is encrypted at rest using CREDENTIAL_ENCRYPTION_KEY.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, utc_now


class EmailCredential(Base):
    """
    Per-user IMAP credential for email OTP retrieval.

    imap_password_encrypted is stored as a Fernet-encrypted ciphertext.
    Use EncryptionService to encrypt before saving and decrypt before using.
    """

    __tablename__ = "email_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable label, e.g. "Gmail QA Account"
    label = Column(String(100), nullable=False)

    # IMAP server details
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)

    # Account credentials (password encrypted at rest)
    email_address = Column(String(255), nullable=False, index=True)
    imap_password_encrypted = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_credentials")
