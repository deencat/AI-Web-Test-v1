from sqlalchemy.orm import Session
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate
from app.db.init_kb_categories import init_kb_categories


def init_db(db: Session) -> None:
    """Initialize database with test user and predefined categories."""
    # Check if admin user exists
    user = get_user_by_username(db, username="admin")
    if not user:
        user_in = UserCreate(
            email="admin@aiwebtest.com",
            username="admin",
            password="admin123",  # Change in production!
            role="admin",
        )
        user = create_user(db, user_in)
        print(f"Created admin user: {user.username}")
    
    # Initialize KB categories
    init_kb_categories(db)

