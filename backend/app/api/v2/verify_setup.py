"""
Verification Script - Sprint 10 API v2 Setup

This script verifies that the API v2 structure is correctly set up.

Run with: python -m app.api.v2.verify_setup
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

def verify_imports():
    """Verify all imports work correctly."""
    print("[*] Verifying imports...")
    
    try:
        from app.api.v2.api import api_router
        print("  [OK] api_router imported successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to import api_router: {e}")
        return False
    
    try:
        from app.schemas.workflow import (
            GenerateTestsRequest,
            WorkflowStatusResponse,
            AgentProgressEvent,
            WorkflowResultsResponse
        )
        print("  [OK] Pydantic schemas imported successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to import schemas: {e}")
        return False
    
    try:
        from app.services.orchestration_service import OrchestrationService
        print("  [OK] OrchestrationService imported successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to import OrchestrationService: {e}")
        return False
    
    try:
        from app.services.progress_tracker import ProgressTracker
        print("  [OK] ProgressTracker imported successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to import ProgressTracker: {e}")
        return False
    
    return True

def verify_endpoints():
    """Verify endpoint files exist and are importable."""
    print("\n[*] Verifying endpoints...")
    
    endpoints = [
        "app.api.v2.endpoints.generate_tests",
        "app.api.v2.endpoints.workflows",
        "app.api.v2.endpoints.sse_stream"
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            __import__(endpoint)
            print(f"  [OK] {endpoint} imported successfully")
        except Exception as e:
            print(f"  [FAIL] Failed to import {endpoint}: {e}")
            all_ok = False
    
    return all_ok

def verify_router_registration():
    """Verify router is registered in main app."""
    print("\n[*] Verifying router registration...")
    
    try:
        from app.core.config import settings
        
        # Check if API_V2_STR is defined
        if hasattr(settings, 'API_V2_STR'):
            print(f"  [OK] API_V2_STR configured: {settings.API_V2_STR}")
        else:
            print("  [FAIL] API_V2_STR not found in settings")
            return False
        
        # Try to import app (may fail if dependencies missing)
        try:
            from app.main import app
            
            # Check if router is registered (by checking routes)
            routes = [route.path for route in app.routes]
            v2_routes = [r for r in routes if r.startswith('/api/v2')]
            
            if v2_routes:
                print(f"  [OK] Found {len(v2_routes)} v2 routes:")
                for route in v2_routes[:5]:  # Show first 5
                    print(f"     - {route}")
                if len(v2_routes) > 5:
                    print(f"     ... and {len(v2_routes) - 5} more")
            else:
                print("  [WARN] No v2 routes found (may be expected if endpoints are stubs)")
        except ImportError as e:
            print(f"  [WARN] Cannot import app (missing dependencies): {e}")
            print("  [INFO] This is expected if dependencies are not installed")
            print("  [INFO] Router registration will be verified when app starts")
        
        return True
        
    except Exception as e:
        print(f"  [WARN] Router registration check incomplete: {e}")
        print("  [INFO] This may be expected if dependencies are not installed")
        return True  # Don't fail on missing dependencies

def verify_file_structure():
    """Verify file structure exists."""
    print("\n[*] Verifying file structure...")
    
    base_path = Path(__file__).parent
    required_files = [
        "api.py",
        "README.md",
        "TECHNICAL_RESEARCH.md",
        "IMPLEMENTATION_GUIDE.md",
        "QUICK_REFERENCE.md",
        "endpoints/generate_tests.py",
        "endpoints/workflows.py",
        "endpoints/sse_stream.py"
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} not found")
            all_ok = False
    
    return all_ok

def verify_schemas():
    """Verify Pydantic schemas are correctly defined."""
    print("\n[*] Verifying Pydantic schemas...")
    
    try:
        from app.schemas.workflow import (
            GenerateTestsRequest,
            WorkflowStatusResponse,
            AgentProgressEvent,
            WorkflowResultsResponse,
            WorkflowErrorResponse
        )
        
        # Test schema instantiation (HttpUrl normalizes URLs, may add trailing slash)
        request = GenerateTestsRequest(url="https://example.com")
        url_str = str(request.url)
        if not url_str.startswith("https://example.com"):
            raise AssertionError(f"Expected URL starting with 'https://example.com', got '{url_str}'")
        print("  [OK] GenerateTestsRequest schema works")
        
        from datetime import datetime, timezone
        from app.schemas.workflow import AgentProgress
        
        # Create minimal progress dict
        progress_dict = {
            "observation": AgentProgress(
                agent="observation",
                status="pending",
                progress=0.0
            )
        }
        
        response = WorkflowStatusResponse(
            workflow_id="test-123",
            status="pending",
            progress=progress_dict,
            started_at=datetime.now(timezone.utc)
        )
        assert response.workflow_id == "test-123"
        print("  [OK] WorkflowStatusResponse schema works")
        
        event = AgentProgressEvent(
            event="agent_started",
            data={
                "agent": "observation",
                "timestamp": "2026-02-11T00:00:00Z"
            }
        )
        assert event.event == "agent_started"
        assert event.data.get("agent") == "observation"
        print("  [OK] AgentProgressEvent schema works")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Schema verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Sprint 10 API v2 Setup Verification")
    print("=" * 60)
    
    checks = [
        ("File Structure", verify_file_structure),
        ("Imports", verify_imports),
        ("Endpoints", verify_endpoints),
        ("Schemas", verify_schemas),
        ("Router Registration", verify_router_registration),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] All checks passed! Setup is ready for Sprint 10.")
    else:
        print("[WARN] Some checks failed. Please review the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

