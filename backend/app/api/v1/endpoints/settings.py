"""API endpoints for user settings."""
from typing import Dict, Any, List
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
from app.schemas.execution_settings import (
    ExecutionSettings as ExecutionSettingsSchema,
    ExecutionSettingsUpdate,
    ExecutionStrategyInfo,
    TierDistributionStats,
    StrategyEffectivenessStats
)
from app.services.user_settings_service import user_settings_service
from app.crud import execution_settings as crud_execution_settings

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


# ============================================================================
# Sprint 5.5: 3-Tier Execution Engine Settings Endpoints
# ============================================================================

@router.get("/execution", response_model=ExecutionSettingsSchema)
async def get_execution_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's 3-Tier execution settings.
    Creates default settings if none exist.
    
    Default Strategy: Option C (Tier 1 → Tier 2 → Tier 3)
    - Maximum reliability: 97-99% success rate
    - Balanced cost
    """
    try:
        settings = crud_execution_settings.get_or_create_execution_settings(db, current_user.id)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution settings: {str(e)}"
        )


@router.put("/execution", response_model=ExecutionSettingsSchema)
async def update_execution_settings(
    settings_update: ExecutionSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's 3-Tier execution settings.
    
    Fallback Strategies:
    - option_a: Tier 1 → Tier 2 (90-95% success, cost-conscious)
    - option_b: Tier 1 → Tier 3 (92-94% success, AI-first)
    - option_c: Tier 1 → Tier 2 → Tier 3 (97-99% success, recommended)
    """
    try:
        settings = crud_execution_settings.update_execution_settings(
            db, 
            current_user.id, 
            settings_update
        )
        
        if not settings:
            # Create if doesn't exist
            from app.schemas.execution_settings import ExecutionSettingsCreate
            
            update_dict = settings_update.model_dump(exclude_unset=True)
            
            create_data = ExecutionSettingsCreate(
                user_id=current_user.id,
                fallback_strategy=update_dict.get("fallback_strategy", "option_c"),
                max_retry_per_tier=update_dict.get("max_retry_per_tier", 1),
                timeout_per_tier_seconds=update_dict.get("timeout_per_tier_seconds", 30),
                track_fallback_reasons=update_dict.get("track_fallback_reasons", True),
                track_strategy_effectiveness=update_dict.get("track_strategy_effectiveness", True)
            )
            
            settings = crud_execution_settings.create_execution_settings(db, create_data)
        
        return settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update execution settings: {str(e)}"
        )


@router.get("/execution/strategies", response_model=List[ExecutionStrategyInfo])
async def get_available_strategies(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about available fallback strategies.
    
    Returns details about Options A, B, and C including:
    - Success rates
    - Cost levels
    - Use cases
    - Tier flows
    """
    strategies = [
        {
            "name": "option_a",
            "display_name": "Option A: Cost-Conscious",
            "description": "Tier 1 → Tier 2. Balances reliability with cost efficiency.",
            "success_rate_min": 90,
            "success_rate_max": 95,
            "cost_level": "medium",
            "speed_level": "fast",
            "performance_level": "high",
            "recommended": False,
            "tier_flow": [1, 2],
            "fallback_chain": ["Tier 1: Playwright", "Tier 2: Hybrid"],
            "recommended_for": "Stable pages with occasional selector changes, cost-conscious environments",
            "use_cases": [
                "Stable pages with occasional selector changes",
                "Cost-conscious environments",
                "Tests with predictable selectors"
            ],
            "pros": [
                "Fast execution (most tests succeed at Tier 1)",
                "XPath caching benefits (Tier 2)",
                "Cost-effective (no Tier 3 usage)",
                "90-95% combined success rate"
            ],
            "cons": [
                "Lower success rate than Option C",
                "No AI reasoning fallback",
                "May fail on complex interactions"
            ]
        },
        {
            "name": "option_b",
            "display_name": "Option B: AI-First",
            "description": "Tier 1 → Tier 3. Uses full AI reasoning when Tier 1 fails.",
            "success_rate_min": 92,
            "success_rate_max": 94,
            "cost_level": "high",
            "speed_level": "medium",
            "performance_level": "medium",
            "recommended": False,
            "tier_flow": [1, 3],
            "fallback_chain": ["Tier 1: Playwright", "Tier 3: Stagehand AI"],
            "recommended_for": "Complex interactions requiring AI reasoning, dynamic pages with unpredictable structure",
            "use_cases": [
                "Complex interactions requiring AI reasoning",
                "Dynamic pages with unpredictable structure",
                "When cost is less of a concern"
            ],
            "pros": [
                "Full AI reasoning for complex cases",
                "Handles unpredictable page structures",
                "92-94% combined success rate",
                "Skips Tier 2 (faster than Option C)"
            ],
            "cons": [
                "Higher cost (Tier 3 uses full LLM)",
                "Slower execution on failures",
                "No XPath caching benefits"
            ]
        },
        {
            "name": "option_c",
            "display_name": "Option C: Maximum Reliability",
            "description": "Tier 1 → Tier 2 → Tier 3. Full cascade for highest success rate.",
            "success_rate_min": 97,
            "success_rate_max": 99,
            "cost_level": "medium",
            "speed_level": "fast",
            "performance_level": "high",
            "recommended": True,
            "tier_flow": [1, 2, 3],
            "fallback_chain": ["Tier 1: Playwright", "Tier 2: Hybrid", "Tier 3: Stagehand AI"],
            "recommended_for": "Production environments, critical test suites, maximum reliability requirements",
            "use_cases": [
                "Production environments",
                "Critical test suites",
                "Maximum reliability requirements",
                "Most tests succeed at Tier 1/2 (low cost)"
            ],
            "pros": [
                "Highest success rate (97-99%)",
                "Comprehensive fallback strategy",
                "Balanced cost (most succeed at Tier 1/2)",
                "Self-healing with XPath caching"
            ],
            "cons": [
                "Slightly slower on complex failures",
                "Higher cost than Option A",
                "More complex execution flow"
            ]
        }
    ]
    
    return strategies


@router.get("/analytics/tier-distribution", response_model=TierDistributionStats)
async def get_tier_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tier distribution statistics for the current user.
    
    Shows how often each tier is used and success rates per tier.
    Useful for optimizing strategy selection and cost analysis.
    """
    try:
        stats = crud_execution_settings.get_tier_distribution_stats(db, user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tier distribution: {str(e)}"
        )


@router.get("/analytics/strategy-effectiveness", response_model=List[StrategyEffectivenessStats])
async def get_strategy_effectiveness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get effectiveness statistics for each fallback strategy used.
    
    Returns metrics like:
    - Success rates per strategy
    - Average execution times
    - Tier distribution percentages
    - Cost estimates
    
    Helps users understand which strategy works best for their tests.
    """
    try:
        stats = crud_execution_settings.get_strategy_effectiveness_stats(db, user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy effectiveness: {str(e)}"
        )

