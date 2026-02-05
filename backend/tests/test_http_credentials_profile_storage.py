"""
Tests for HTTP Basic Auth profile-level storage (Enhancement 5 Add-On).
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


def test_encrypt_decrypt_password(encryption_service):
    password = "super-secret"

    encrypted = encryption_service.encrypt_password(password)

    assert encrypted != password
    assert encryption_service.decrypt_password(encrypted) == password


def test_create_profile_with_http_credentials(db: Session, test_user, crud_profile):
    from app.schemas.browser_profile import BrowserProfileCreate

    profile_data = BrowserProfileCreate(
        profile_name="UAT Profile",
        os_type="windows",
        browser_type="chromium",
        description="UAT with Basic Auth",
        http_username="uat_user",
        http_password="uat_password"
    )

    profile = crud_profile.create_profile(db, test_user.id, profile_data)

    assert profile.http_username == "uat_user"
    assert profile.http_password_encrypted is not None
    assert profile.http_password_encrypted != "uat_password"

    credentials = crud_profile.get_http_credentials(db, profile.id, test_user.id)

    assert credentials == {
        "username": "uat_user",
        "password": "uat_password"
    }


def test_update_profile_clears_http_credentials(db: Session, test_user, crud_profile):
    from app.schemas.browser_profile import BrowserProfileCreate, BrowserProfileUpdate

    profile_data = BrowserProfileCreate(
        profile_name="UAT Profile",
        os_type="windows",
        browser_type="chromium",
        http_username="uat_user",
        http_password="uat_password"
    )
    profile = crud_profile.create_profile(db, test_user.id, profile_data)

    update_data = BrowserProfileUpdate(clear_http_credentials=True)
    updated = crud_profile.update_profile(db, profile, update_data)

    assert updated.http_username is None
    assert updated.http_password_encrypted is None


def test_get_http_credentials_missing_returns_none(db: Session, test_user, crud_profile):
    from app.schemas.browser_profile import BrowserProfileCreate

    profile_data = BrowserProfileCreate(
        profile_name="No Auth Profile",
        os_type="linux",
        browser_type="chromium"
    )
    profile = crud_profile.create_profile(db, test_user.id, profile_data)

    assert crud_profile.get_http_credentials(db, profile.id, test_user.id) is None
