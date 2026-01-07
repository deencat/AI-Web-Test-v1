"""API endpoints for user settings."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user_settings import (
    UserSettingInDB, 
    UserSettingUpdate, 
    UserSettingCreate,
    AvailableProvidersResponse,
    StagehandProviderResponse,
    StagehandProviderUpdate
)
from app.services.user_settings_service import user_settings_service

router = APIRouter()


@router.get("/provider", response_model=UserSettingInDB)
async def get_user_provider_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's provider settings.
    Creates default settings if none exist.
    """
    try:
        settings = user_settings_service.get_or_create_user_settings(db, current_user.id)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )


@router.put("/provider", response_model=UserSettingInDB)
async def update_user_provider_settings(
    settings_update: UserSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's provider settings.
    Creates settings if none exist.
    """
    try:
        # Get or create settings
        existing_settings = user_settings_service.get_user_settings(db, current_user.id)
        
        if not existing_settings:
            # Create new settings - need full data
            # Build complete settings from update + defaults
            default_gen = user_settings_service.get_default_provider_config("generation")
            default_exec = user_settings_service.get_default_provider_config("execution")
            
            update_dict = settings_update.model_dump(exclude_unset=True)
            
            create_data = UserSettingCreate(
                generation_provider=update_dict.get("generation_provider", default_gen["provider"]),
                generation_model=update_dict.get("generation_model", default_gen["model"]),
                generation_temperature=update_dict.get("generation_temperature", 0.7),
                generation_max_tokens=update_dict.get("generation_max_tokens", 4096),
                execution_provider=update_dict.get("execution_provider", default_exec["provider"]),
                execution_model=update_dict.get("execution_model", default_exec["model"]),
                execution_temperature=update_dict.get("execution_temperature", 0.7),
                execution_max_tokens=update_dict.get("execution_max_tokens", 4096)
            )
            
            settings = user_settings_service.create_user_settings(db, current_user.id, create_data)
        else:
            # Update existing settings
            settings = user_settings_service.update_user_settings(db, current_user.id, settings_update)
        
        return settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )


@router.get("/available-providers", response_model=AvailableProvidersResponse)
async def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available providers and their models.
    Shows which providers are configured (have API keys).
    """
    try:
        providers = user_settings_service.get_available_providers()
        
        # Get default configurations
        default_gen = user_settings_service.get_default_provider_config("generation")
        default_exec = user_settings_service.get_default_provider_config("execution")
        
        return AvailableProvidersResponse(
            providers=providers,
            default_generation_provider=default_gen["provider"],
            default_generation_model=default_gen["model"],
            default_execution_provider=default_exec["provider"],
            default_execution_model=default_exec["model"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available providers: {str(e)}"
        )


@router.delete("/provider", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_provider_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's provider settings.
    User will fall back to environment defaults.
    """
    try:
        deleted = user_settings_service.delete_user_settings(db, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user settings: {str(e)}"
        )


@router.get("/provider/generation", response_model=Dict[str, Any])
async def get_generation_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's generation provider configuration.
    Used internally by test generation services.
    """
    try:
        config = user_settings_service.get_provider_config(db, current_user.id, "generation")
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation config: {str(e)}"
        )


@router.get("/provider/execution", response_model=Dict[str, Any])
async def get_execution_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's execution provider configuration.
    Used internally by test execution services.
    """
    try:
        config = user_settings_service.get_provider_config(db, current_user.id, "execution")
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution config: {str(e)}"
        )


# Sprint 5: Dual Stagehand Provider System Endpoints

@router.get("/stagehand-provider", response_model=StagehandProviderResponse)
async def get_stagehand_provider(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's stagehand provider preference.
    Returns current provider and list of available providers.
    
    Sprint 5: Dual Stagehand Provider System
    """
    try:
        settings = user_settings_service.get_or_create_user_settings(db, current_user.id)
        
        return StagehandProviderResponse(
            provider=settings.stagehand_provider,
            available_providers=["python", "typescript"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stagehand provider: {str(e)}"
        )


@router.put("/stagehand-provider", response_model=StagehandProviderResponse)
async def update_stagehand_provider(
    provider_update: StagehandProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's stagehand provider preference.
    Switches between Python and TypeScript Stagehand implementations.
    
    Sprint 5: Dual Stagehand Provider System
    
    Args:
        provider_update: New provider selection ('python' or 'typescript')
    
    Returns:
        Updated provider configuration
    """
    try:
        # Get or create settings
        settings = user_settings_service.get_or_create_user_settings(db, current_user.id)
        
        # Update the stagehand_provider field
        update_data = UserSettingUpdate(stagehand_provider=provider_update.provider)
        updated_settings = user_settings_service.update_user_settings(db, current_user.id, update_data)
        
        return StagehandProviderResponse(
            provider=updated_settings.stagehand_provider,
            available_providers=["python", "typescript"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stagehand provider: {str(e)}"
        )
