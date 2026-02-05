"""
Tests for server-side browser profile session storage (Enhancement 5 update).
"""
import importlib
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))


@pytest.fixture
def db(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", key)

    from app.db.base import Base
    from app.models.user import User

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def encryption_service(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", key)

    from app.services import encryption_service as encryption_service_module
    importlib.reload(encryption_service_module)

    return encryption_service_module.EncryptionService()


@pytest.fixture
def crud_profile(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", key)

    from app.crud import browser_profile as crud_profile_module
    importlib.reload(crud_profile_module)

    return crud_profile_module


@pytest.fixture
def test_user(db: Session):
    from app.models.user import User

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password_here",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def profile_payload():
    from app.schemas.browser_profile import BrowserProfileCreate

    return BrowserProfileCreate(
        profile_name="Server Sync Profile",
        os_type="windows",
        browser_type="chromium",
        description="Synced profile"
    )


@pytest.fixture
def session_payload():
    return {
        "cookies": [
            {
                "name": "session_id",
                "value": "abc123",
                "domain": ".example.com",
                "path": "/",
                "secure": True,
                "httpOnly": True
            }
        ],
        "localStorage": {"token": "local-token"},
        "sessionStorage": {"session": "session-token"}
    }


def test_encrypt_decrypt_json_roundtrip(encryption_service, session_payload):
    encrypted = encryption_service.encrypt_json(session_payload)
    assert isinstance(encrypted, str)

    decrypted = encryption_service.decrypt_json(encrypted)
    assert decrypted == session_payload


def test_sync_and_load_profile_session(db: Session, test_user, crud_profile, profile_payload, session_payload):
    profile = crud_profile.create_profile(db, test_user.id, profile_payload)

    synced = crud_profile.sync_profile_session(
        db=db,
        profile_id=profile.id,
        user_id=test_user.id,
        session_data=session_payload
    )

    assert synced.has_session_data is True
    assert synced.last_sync_at is not None
    assert synced.cookies_encrypted is not None

    loaded = crud_profile.load_profile_session(db, profile.id, test_user.id)

    assert loaded["cookies"] == session_payload["cookies"]
    assert loaded["localStorage"] == session_payload["localStorage"]
    assert loaded["sessionStorage"] == session_payload["sessionStorage"]


def test_load_profile_session_missing_returns_none(db: Session, test_user, crud_profile, profile_payload):
    profile = crud_profile.create_profile(db, test_user.id, profile_payload)

    assert crud_profile.load_profile_session(db, profile.id, test_user.id) is None


def test_update_profile_enables_auto_sync(db: Session, test_user, crud_profile, profile_payload):
    from app.schemas.browser_profile import BrowserProfileUpdate

    profile = crud_profile.create_profile(db, test_user.id, profile_payload)

    update_data = BrowserProfileUpdate(auto_sync=True)
    updated = crud_profile.update_profile(db, profile, update_data)

    assert updated.auto_sync is True
