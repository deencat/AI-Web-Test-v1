"""
Encryption Service
Created: February 5, 2026
Purpose: Encrypt/decrypt sensitive data like HTTP Basic Auth passwords.
"""
import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive values.

    Uses Fernet symmetric encryption (AES-128 + HMAC). The key is loaded
    from the CREDENTIAL_ENCRYPTION_KEY environment variable.
    """

    def __init__(self) -> None:
        key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY environment variable not set. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self.cipher = Fernet(key.encode())

    def encrypt_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")

        encrypted_bytes = self.cipher.encrypt(password.encode())
        encrypted_str = encrypted_bytes.decode()
        logger.debug("Encrypted password successfully")
        return encrypted_str

    def decrypt_password(self, encrypted: str) -> str:
        if not encrypted:
            raise ValueError("Encrypted password cannot be empty")

        try:
            decrypted_bytes = self.cipher.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except Exception as exc:
            logger.error("Failed to decrypt password: %s", exc)
            raise ValueError(f"Failed to decrypt password: {exc}")
