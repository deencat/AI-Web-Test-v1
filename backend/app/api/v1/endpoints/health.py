from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.api.deps import get_db
from app.models.user import User
from app.models.test_case import TestCase
from app.models.kb_document import KBDocument

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "Agentic QA API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Health check with database connection test."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with system statistics.
    
    Returns comprehensive health information including:
    - Service status
    - Database connectivity
    - System statistics
    - API version
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "build": "sprint-2-day-5"
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_data["services"] = {
            "database": {
                "status": "connected",
                "type": "SQLite"
            }
        }
        
        # Get statistics
        try:
            stats = {
                "total_users": db.query(User).count(),
                "total_test_cases": db.query(TestCase).count(),
                "total_kb_documents": db.query(KBDocument).count()
            }
            health_data["statistics"] = stats
        except Exception as e:
            health_data["statistics"] = {
                "error": f"Failed to fetch statistics: {str(e)}"
            }
            
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["services"] = {
            "database": {
                "status": "disconnected",
                "error": str(e)
            }
        }
    
    # API endpoints info
    health_data["endpoints"] = {
        "auth": 4,
        "users": 3,
        "test_generation": 3,
        "test_management": 6,
        "knowledge_base": 9,
        "total": 25
    }
    
    # Features
    health_data["features"] = [
        "authentication",
        "test_generation",
        "test_management",
        "kb_upload",
        "text_extraction",
        "multi_format_support"
    ]
    
    return health_data

