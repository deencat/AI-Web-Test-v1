"""
Factory for creating Stagehand adapters based on user preferences.

This factory selects between Python and TypeScript Stagehand providers
by reading the user's stagehand_provider setting from the database.
"""
import os
from typing import Optional
from sqlalchemy.orm import Session

from app.services.stagehand_adapter import StagehandAdapter
from app.services.python_stagehand_adapter import PythonStagehandAdapter
from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter
from app.services.user_settings_service import user_settings_service


class StagehandFactory:
    """
    Factory for creating the appropriate Stagehand adapter.
    
    Usage:
        factory = StagehandFactory()
        adapter = factory.create_adapter(db, user_id)
        await adapter.initialize()
        await adapter.execute_test(...)
    """
    
    @staticmethod
    def create_adapter(
        db: Session,
        user_id: int,
        browser: str = "chromium",
        headless: bool = True,
        screenshot_dir: str = "./screenshots",
        video_dir: str = "./videos"
    ) -> StagehandAdapter:
        """
        Create Stagehand adapter based on user's provider preference.
        
        Args:
            db: Database session
            user_id: User ID to fetch settings for
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            screenshot_dir: Directory to save screenshots
            video_dir: Directory to save videos
            
        Returns:
            StagehandAdapter instance (Python or TypeScript)
            
        Raises:
            ValueError: If provider setting is invalid
        """
        # Get user's stagehand provider preference
        settings = user_settings_service.get_user_settings(db, user_id)
        
        provider = "python"  # Default fallback
        if settings and hasattr(settings, 'stagehand_provider'):
            provider = settings.stagehand_provider
        
        # Allow environment variable override for testing
        provider_override = os.getenv("STAGEHAND_PROVIDER_OVERRIDE")
        if provider_override:
            provider = provider_override
            print(f"[Factory] Using provider override from env: {provider}")
        
        print(f"[Factory] Creating adapter for provider: {provider}")
        
        # Create appropriate adapter
        if provider == "python":
            return PythonStagehandAdapter(
                browser=browser,
                headless=headless,
                screenshot_dir=screenshot_dir,
                video_dir=video_dir
            )
        elif provider == "typescript":
            # TypeScript adapter gets service URL from environment
            return TypeScriptStagehandAdapter()
        else:
            raise ValueError(
                f"Invalid stagehand provider: {provider}. "
                f"Must be 'python' or 'typescript'"
            )
    
    @staticmethod
    def create_adapter_explicit(
        provider: str,
        browser: str = "chromium",
        headless: bool = True,
        screenshot_dir: str = "./screenshots",
        video_dir: str = "./videos"
    ) -> StagehandAdapter:
        """
        Create Stagehand adapter with explicit provider selection.
        
        This method bypasses database lookup and directly creates
        the specified adapter. Useful for testing or direct control.
        
        Args:
            provider: Provider name ('python' or 'typescript')
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            screenshot_dir: Directory to save screenshots
            video_dir: Directory to save videos
            
        Returns:
            StagehandAdapter instance (Python or TypeScript)
            
        Raises:
            ValueError: If provider is invalid
        """
        print(f"[Factory] Creating adapter explicitly for provider: {provider}")
        
        if provider == "python":
            return PythonStagehandAdapter(
                browser=browser,
                headless=headless,
                screenshot_dir=screenshot_dir,
                video_dir=video_dir
            )
        elif provider == "typescript":
            return TypeScriptStagehandAdapter()
        else:
            raise ValueError(
                f"Invalid stagehand provider: {provider}. "
                f"Must be 'python' or 'typescript'"
            )


# Convenience function for quick adapter creation
def get_stagehand_adapter(
    db: Session,
    user_id: int,
    browser: str = "chromium",
    headless: bool = True,
    screenshot_dir: str = "./screenshots",
    video_dir: str = "./videos"
) -> StagehandAdapter:
    """
    Convenience function to create Stagehand adapter.
    
    Args:
        db: Database session
        user_id: User ID to fetch settings for
        browser: Browser type (chromium, firefox, webkit)
        headless: Whether to run browser in headless mode
        screenshot_dir: Directory to save screenshots
        video_dir: Directory to save videos
        
    Returns:
        StagehandAdapter instance based on user preference
    """
    factory = StagehandFactory()
    return factory.create_adapter(
        db=db,
        user_id=user_id,
        browser=browser,
        headless=headless,
        screenshot_dir=screenshot_dir,
        video_dir=video_dir
    )
