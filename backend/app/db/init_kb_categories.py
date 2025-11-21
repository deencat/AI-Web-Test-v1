"""Initialize predefined KB categories."""
from sqlalchemy.orm import Session
from app.models.kb_document import KBCategory
from app.schemas.kb_document import KBCategoryCreate
from app.crud import kb_document as crud


# Predefined categories for Three HK / AI Web Test
PREDEFINED_CATEGORIES = [
    {
        "name": "System Guide",
        "description": "System guides and documentation for CRM, billing, and other internal systems",
        "color": "#3B82F6",  # Blue
        "icon": "system"
    },
    {
        "name": "Product Info",
        "description": "Product information for 5G plans, services, and offerings",
        "color": "#10B981",  # Green
        "icon": "package"
    },
    {
        "name": "Process",
        "description": "Business processes, workflows, and procedures",
        "color": "#8B5CF6",  # Purple
        "icon": "workflow"
    },
    {
        "name": "Login Flows",
        "description": "Login flows, authentication guides, and access procedures",
        "color": "#F59E0B",  # Amber
        "icon": "lock"
    },
    {
        "name": "API Documentation",
        "description": "API documentation, endpoints, and integration guides",
        "color": "#EF4444",  # Red
        "icon": "code"
    },
    {
        "name": "User Guides",
        "description": "End-user guides and help documentation",
        "color": "#06B6D4",  # Cyan
        "icon": "book-open"
    },
    {
        "name": "Test Cases",
        "description": "Test case documentation and QA resources",
        "color": "#EC4899",  # Pink
        "icon": "check-circle"
    },
    {
        "name": "Bug Reports",
        "description": "Bug reports and issue documentation",
        "color": "#DC2626",  # Dark red
        "icon": "alert-circle"
    }
]


def init_kb_categories(db: Session) -> None:
    """
    Initialize predefined KB categories if they don't exist.
    
    Args:
        db: Database session
    """
    print("\n[KB] Initializing predefined categories...")
    
    created_count = 0
    existing_count = 0
    
    for category_data in PREDEFINED_CATEGORIES:
        # Check if category already exists
        existing = crud.get_category_by_name(db, category_data["name"])
        
        if not existing:
            # Create new category
            category = KBCategoryCreate(**category_data)
            crud.create_category(db, category)
            created_count += 1
            print(f"  [+] Created category: {category_data['name']}")
        else:
            existing_count += 1
            print(f"  [=] Category exists: {category_data['name']}")
    
    print(f"\n[KB] Categories initialized: {created_count} created, {existing_count} existing")

