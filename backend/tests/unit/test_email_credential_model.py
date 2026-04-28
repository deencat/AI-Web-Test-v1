"""
Unit tests for EmailCredential ORM model — Sprint 10.10.

TDD RED phase: validates AES encryption at rest and model field constraints.
"""
import os
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# EncryptionService round-trip (infrastructure)
# ---------------------------------------------------------------------------

class TestEncryptionServiceRoundTrip:
    """EncryptionService is already implemented; verify it works for passwords."""

    def test_encrypt_decrypt_round_trip(self):
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": test_key}):
            from app.services.encryption_service import EncryptionService
            svc = EncryptionService()
            ciphertext = svc.encrypt_password("my-app-password-123")
            assert ciphertext != "my-app-password-123"
            assert svc.decrypt_password(ciphertext) == "my-app-password-123"

    def test_empty_password_raises(self):
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": test_key}):
            from app.services.encryption_service import EncryptionService
            svc = EncryptionService()
            with pytest.raises(ValueError):
                svc.encrypt_password("")


# ---------------------------------------------------------------------------
# EmailCredential model field validation
# ---------------------------------------------------------------------------

class TestEmailCredentialModelFields:
    """Verify the SQLAlchemy model has the expected columns."""

    def test_model_has_expected_columns(self):
        from app.models.email_credential import EmailCredential
        columns = {col.key for col in EmailCredential.__table__.columns}
        assert "id" in columns
        assert "user_id" in columns
        assert "label" in columns
        assert "imap_host" in columns
        assert "imap_port" in columns
        assert "email_address" in columns
        assert "imap_password_encrypted" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_default_imap_port(self):
        from app.models.email_credential import EmailCredential
        port_col = EmailCredential.__table__.columns["imap_port"]
        assert port_col.default is not None
        assert port_col.default.arg == 993

    def test_tablename(self):
        from app.models.email_credential import EmailCredential
        assert EmailCredential.__tablename__ == "email_credentials"

    def test_user_id_is_foreign_key(self):
        from app.models.email_credential import EmailCredential
        fks = {fk.target_fullname for fk in EmailCredential.__table__.foreign_keys}
        assert "users.id" in fks

    def test_label_not_nullable(self):
        from app.models.email_credential import EmailCredential
        col = EmailCredential.__table__.columns["label"]
        assert not col.nullable

    def test_email_address_not_nullable(self):
        from app.models.email_credential import EmailCredential
        col = EmailCredential.__table__.columns["email_address"]
        assert not col.nullable

    def test_imap_host_not_nullable(self):
        from app.models.email_credential import EmailCredential
        col = EmailCredential.__table__.columns["imap_host"]
        assert not col.nullable

    def test_imap_password_encrypted_not_nullable(self):
        from app.models.email_credential import EmailCredential
        col = EmailCredential.__table__.columns["imap_password_encrypted"]
        assert not col.nullable


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TestEmailCredentialSchemas:
    """Verify Pydantic request/response schemas."""

    def test_create_schema_requires_all_fields(self):
        from app.schemas.email_credential import EmailCredentialCreate
        import pydantic

        with pytest.raises((pydantic.ValidationError, TypeError)):
            EmailCredentialCreate()  # missing required fields

    def test_create_schema_accepts_valid_data(self):
        from app.schemas.email_credential import EmailCredentialCreate
        cred = EmailCredentialCreate(
            label="Gmail QA",
            imap_host="imap.gmail.com",
            imap_port=993,
            email_address="qa@gmail.com",
            app_password="secret",
        )
        assert cred.label == "Gmail QA"
        assert cred.app_password == "secret"

    def test_create_schema_default_imap_port(self):
        from app.schemas.email_credential import EmailCredentialCreate
        cred = EmailCredentialCreate(
            label="Gmail QA",
            imap_host="imap.gmail.com",
            email_address="qa@gmail.com",
            app_password="secret",
        )
        assert cred.imap_port == 993

    def test_response_schema_excludes_password(self):
        """EmailCredentialResponse must NOT expose imap_password_encrypted."""
        from app.schemas.email_credential import EmailCredentialResponse
        fields = EmailCredentialResponse.model_fields
        assert "imap_password_encrypted" not in fields
        assert "app_password" not in fields

    def test_response_schema_has_id(self):
        from app.schemas.email_credential import EmailCredentialResponse
        assert "id" in EmailCredentialResponse.model_fields


# ---------------------------------------------------------------------------
# IMAP provider defaults
# ---------------------------------------------------------------------------

class TestKnownImapHosts:
    """Verify constant KNOWN_IMAP_HOSTS covers major providers."""

    def test_gmail_present(self):
        from app.services.email_otp_service import KNOWN_IMAP_HOSTS
        assert "imap.gmail.com" in KNOWN_IMAP_HOSTS

    def test_outlook_present(self):
        from app.services.email_otp_service import KNOWN_IMAP_HOSTS
        assert "outlook.office365.com" in KNOWN_IMAP_HOSTS

    def test_yahoo_present(self):
        from app.services.email_otp_service import KNOWN_IMAP_HOSTS
        assert "imap.mail.yahoo.com" in KNOWN_IMAP_HOSTS
