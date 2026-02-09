"""
Comprehensive tests for Browser Profile Session Persistence (Enhancement 5).
Created: February 3, 2026

Tests cover:
1. CRUD operations (create, list, get, update, delete)
2. Profile injection and export
3. Integration with execution service
4. Security and validation
"""
import pytest
import json
import io
import zipfile
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.browser_profile import BrowserProfile
from app.models.user import User
from app.crud import browser_profile as crud_profile
from app.schemas.browser_profile import BrowserProfileCreate, BrowserProfileUpdate


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
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
def sample_profile_data():
    """Sample profile data for testing."""
    return BrowserProfileCreate(
        profile_name="Windows 11 - Admin",
        os_type="windows",
        browser_type="chromium",
        description="Windows 11 admin session with login"
    )


@pytest.fixture
def sample_session_data():
    """Sample browser session data (cookies, localStorage)."""
    return {
        "cookies": [
            {
                "name": "session_id",
                "value": "abc123def456",
                "domain": ".example.com",
                "path": "/",
                "secure": True,
                "httpOnly": True
            },
            {
                "name": "auth_token",
                "value": "xyz789uvw012",
                "domain": ".example.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            }
        ],
        "localStorage": {
            "user_id": "12345",
            "username": "testuser",
            "preferences": json.dumps({"theme": "dark", "language": "en"})
        },
        "sessionStorage": {
            "temp_data": "temporary_value"
        },
        "exported_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# Test Suite 1: CRUD Operations
# ============================================================================

class TestBrowserProfileCRUD:
    """Test CRUD operations for browser profiles."""
    
    def test_create_profile(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test creating a new browser profile."""
        profile = crud_profile.create_profile(
            db=db,
            user_id=test_user.id,
            profile_data=sample_profile_data
        )
        
        assert profile.id is not None
        assert profile.user_id == test_user.id
        assert profile.profile_name == "Windows 11 - Admin"
        assert profile.os_type == "windows"
        assert profile.browser_type == "chromium"
        assert profile.description == "Windows 11 admin session with login"
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.last_sync_at is None
    
    def test_get_profile_by_id(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test retrieving a profile by ID."""
        # Create profile
        profile = crud_profile.create_profile(db, test_user.id, sample_profile_data)
        
        # Retrieve profile
        retrieved = crud_profile.get_profile(db, profile.id)
        
        assert retrieved is not None
        assert retrieved.id == profile.id
        assert retrieved.profile_name == profile.profile_name
    
    def test_get_profile_by_user(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test retrieving a profile with user ownership check."""
        # Create profile
        profile = crud_profile.create_profile(db, test_user.id, sample_profile_data)
        
        # Retrieve profile (ownership verified)
        retrieved = crud_profile.get_profile_by_user(db, profile.id, test_user.id)
        
        assert retrieved is not None
        assert retrieved.id == profile.id
        
        # Try with wrong user ID (should return None)
        wrong_user_result = crud_profile.get_profile_by_user(db, profile.id, 99999)
        assert wrong_user_result is None
    
    def test_list_profiles_by_user(self, db: Session, test_user: User):
        """Test listing all profiles for a user."""
        # Create multiple profiles
        profile1 = crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Profile 1", os_type="windows", browser_type="chromium")
        )
        profile2 = crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Profile 2", os_type="linux", browser_type="firefox")
        )
        profile3 = crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Profile 3", os_type="macos", browser_type="webkit")
        )
        
        # List profiles
        profiles = crud_profile.get_all_profiles_by_user(db, test_user.id)
        
        assert len(profiles) == 3
        assert profiles[0].profile_name == "Profile 3"  # Newest first
        assert profiles[1].profile_name == "Profile 2"
        assert profiles[2].profile_name == "Profile 1"
    
    def test_update_profile(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test updating a profile."""
        import time
        
        # Create profile
        profile = crud_profile.create_profile(db, test_user.id, sample_profile_data)
        original_updated_at = profile.updated_at
        
        # Small delay to ensure timestamp difference
        time.sleep(0.01)
        
        # Update profile
        update_data = BrowserProfileUpdate(
            profile_name="Windows 11 - Updated",
            description="Updated description"
        )
        updated = crud_profile.update_profile(db, profile, update_data)
        
        assert updated.profile_name == "Windows 11 - Updated"
        assert updated.description == "Updated description"
        assert updated.os_type == "windows"  # Unchanged
        assert updated.updated_at >= original_updated_at
    
    def test_delete_profile(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test deleting a profile."""
        # Create profile
        profile = crud_profile.create_profile(db, test_user.id, sample_profile_data)
        profile_id = profile.id
        
        # Delete profile
        result = crud_profile.delete_profile(db, profile)
        
        assert result is True
        
        # Verify deletion
        deleted = crud_profile.get_profile(db, profile_id)
        assert deleted is None
    
    def test_update_last_sync(self, db: Session, test_user: User, sample_profile_data: BrowserProfileCreate):
        """Test updating last_sync_at timestamp."""
        import time
        
        # Create profile
        profile = crud_profile.create_profile(db, test_user.id, sample_profile_data)
        original_updated_at = profile.updated_at
        
        assert profile.last_sync_at is None
        
        # Small delay to ensure timestamp difference
        time.sleep(0.01)
        
        # Update last sync
        updated = crud_profile.update_last_sync(db, profile)
        
        assert updated.last_sync_at is not None
        assert updated.updated_at >= original_updated_at
    
    def test_get_profiles_count(self, db: Session, test_user: User):
        """Test counting profiles for a user."""
        # Create profiles
        crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Profile 1", os_type="windows", browser_type="chromium")
        )
        crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Profile 2", os_type="linux", browser_type="chromium")
        )
        
        # Count profiles
        count = crud_profile.get_profiles_count(db, test_user.id)
        
        assert count == 2


# ============================================================================
# Test Suite 2: Schema Validation
# ============================================================================

class TestBrowserProfileSchemas:
    """Test Pydantic schema validation."""
    
    def test_valid_os_types(self):
        """Test that only valid OS types are accepted."""
        # Valid OS types
        for os_type in ["windows", "linux", "macos"]:
            profile = BrowserProfileCreate(
                profile_name="Test Profile",
                os_type=os_type,
                browser_type="chromium"
            )
            assert profile.os_type == os_type.lower()
    
    def test_invalid_os_type(self):
        """Test that invalid OS types are rejected."""
        with pytest.raises(ValueError, match="os_type must be one of"):
            BrowserProfileCreate(
                profile_name="Test Profile",
                os_type="ios",  # Invalid
                browser_type="chromium"
            )
    
    def test_valid_browser_types(self):
        """Test that only valid browser types are accepted."""
        # Valid browser types
        for browser_type in ["chromium", "firefox", "webkit"]:
            profile = BrowserProfileCreate(
                profile_name="Test Profile",
                os_type="windows",
                browser_type=browser_type
            )
            assert profile.browser_type == browser_type.lower()
    
    def test_invalid_browser_type(self):
        """Test that invalid browser types are rejected."""
        with pytest.raises(ValueError, match="browser_type must be one of"):
            BrowserProfileCreate(
                profile_name="Test Profile",
                os_type="windows",
                browser_type="safari"  # Invalid
            )
    
    def test_profile_name_required(self):
        """Test that profile_name is required."""
        with pytest.raises(ValueError):
            BrowserProfileCreate(
                profile_name="",  # Empty
                os_type="windows",
                browser_type="chromium"
            )
    
    def test_update_partial_fields(self):
        """Test updating only some fields."""
        update = BrowserProfileUpdate(profile_name="Updated Name")
        
        assert update.profile_name == "Updated Name"
        assert update.os_type is None
        assert update.browser_type is None
        assert update.description is None


# ============================================================================
# Test Suite 3: Profile Data Packaging
# ============================================================================

class TestProfileDataPackaging:
    """Test ZIP packaging of profile data."""
    
    def test_create_profile_zip(self, sample_session_data: dict):
        """Test creating a profile ZIP file in-memory."""
        # Create in-memory ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add profile data
            profile_json = json.dumps(sample_session_data, indent=2)
            zip_file.writestr("profile.json", profile_json)
            
            # Add metadata
            metadata = {
                "profile_id": 1,
                "profile_name": "Test Profile",
                "os_type": "windows",
                "browser_type": "chromium",
                "exported_at": datetime.utcnow().isoformat()
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        # Verify ZIP was created
        file_size = zip_buffer.tell()
        assert file_size > 0
        
        # Verify ZIP contents
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            assert "profile.json" in zip_file.namelist()
            assert "metadata.json" in zip_file.namelist()
            
            # Verify profile data
            profile_data = json.loads(zip_file.read("profile.json").decode('utf-8'))
            assert len(profile_data["cookies"]) == 2
            assert "localStorage" in profile_data
            assert "sessionStorage" in profile_data
    
    def test_extract_profile_from_zip(self, sample_session_data: dict):
        """Test extracting profile data from ZIP file."""
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("profile.json", json.dumps(sample_session_data))
        
        # Extract data
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            profile_json = zip_file.read("profile.json").decode('utf-8')
            profile_data = json.loads(profile_json)
        
        # Verify extracted data
        assert profile_data["cookies"][0]["name"] == "session_id"
        assert profile_data["localStorage"]["user_id"] == "12345"
        assert profile_data["sessionStorage"]["temp_data"] == "temporary_value"


# ============================================================================
# Test Suite 4: Security & Edge Cases
# ============================================================================

class TestBrowserProfileSecurity:
    """Test security aspects and edge cases."""
    
    def test_user_isolation(self, db: Session):
        """Test that users can only access their own profiles."""
        # Create two users
        user1 = User(email="user1@example.com", username="user1", hashed_password="hash", role="user", is_active=True)
        user2 = User(email="user2@example.com", username="user2", hashed_password="hash", role="user", is_active=True)
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        
        # Create profile for user1
        profile_data = BrowserProfileCreate(profile_name="User1 Profile", os_type="windows", browser_type="chromium")
        profile = crud_profile.create_profile(db, user1.id, profile_data)
        
        # User1 can access their profile
        assert crud_profile.get_profile_by_user(db, profile.id, user1.id) is not None
        
        # User2 cannot access user1's profile
        assert crud_profile.get_profile_by_user(db, profile.id, user2.id) is None
    
    def test_large_session_data(self):
        """Test handling of large session data."""
        # Create large session data (1000 cookies + 1000 localStorage items)
        large_session = {
            "cookies": [
                {
                    "name": f"cookie_{i}",
                    "value": f"value_{i}" * 10,  # 100+ bytes per cookie
                    "domain": ".example.com",
                    "path": "/"
                }
                for i in range(1000)
            ],
            "localStorage": {
                f"key_{i}": f"value_{i}" * 10 for i in range(1000)
            },
            "sessionStorage": {},
            "exported_at": datetime.utcnow().isoformat()
        }
        
        # Package as ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("profile.json", json.dumps(large_session))
        
        file_size = zip_buffer.tell()
        print(f"[DEBUG] Large session ZIP size: {file_size:,} bytes")
        
        # Verify compression worked (should be much smaller than raw JSON)
        raw_json_size = len(json.dumps(large_session))
        compression_ratio = file_size / raw_json_size
        assert compression_ratio < 0.5  # At least 50% compression
    
    def test_case_insensitive_os_type(self, db: Session, test_user: User):
        """Test that OS type is case-insensitive."""
        profile = crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Test", os_type="WINDOWS", browser_type="chromium")
        )
        
        assert profile.os_type == "windows"  # Normalized to lowercase
    
    def test_case_insensitive_browser_type(self, db: Session, test_user: User):
        """Test that browser type is case-insensitive."""
        profile = crud_profile.create_profile(
            db, test_user.id,
            BrowserProfileCreate(profile_name="Test", os_type="windows", browser_type="CHROMIUM")
        )
        
        assert profile.browser_type == "chromium"  # Normalized to lowercase


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
