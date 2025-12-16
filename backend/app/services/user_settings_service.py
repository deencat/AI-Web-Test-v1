"""Service for managing user settings."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user_settings import UserSetting
from app.schemas.user_settings import UserSettingCreate, UserSettingUpdate, AvailableProvider
from app.core.config import settings


class UserSettingsService:
    """Service for user settings operations."""
    
    # Provider configurations with available models
    PROVIDER_CONFIGS = {
        "google": {
            "display_name": "Google Gemini",
            "models": [
                "gemini-2.0-flash-exp",
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-2.0-flash-thinking-exp-01-21",
            ],
            "recommended": "gemini-2.0-flash-exp",
            "api_key_env": "GOOGLE_API_KEY"
        },
        "cerebras": {
            "display_name": "Cerebras",
            "models": [
                "llama3.1-8b",
                "llama3.1-70b",
                "llama3.3-70b"
            ],
            "recommended": "llama3.3-70b",
            "api_key_env": "CEREBRAS_API_KEY"
        },
        "openrouter": {
            "display_name": "OpenRouter",
            "models": [
                "google/gemini-2.0-flash-exp:free",
                "google/gemini-flash-1.5:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "meta-llama/llama-3.2-1b-instruct:free",
                "microsoft/phi-3-mini-128k-instruct:free",
                "qwen/qwen-2-7b-instruct:free",
                "mistralai/mistral-7b-instruct:free",
                "nousresearch/hermes-3-llama-3.1-405b:free",
                "gpt-4o",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229"
            ],
            "recommended": "google/gemini-2.0-flash-exp:free",
            "api_key_env": "OPENROUTER_API_KEY"
        }
    }
    
    def get_available_providers(self) -> List[AvailableProvider]:
        """
        Get list of available providers with their configuration status.
        
        Returns:
            List of AvailableProvider objects
        """
        providers = []
        
        for name, config in self.PROVIDER_CONFIGS.items():
            # Check if API key is configured
            api_key_env = config["api_key_env"]
            is_configured = bool(getattr(settings, api_key_env, None))
            
            providers.append(AvailableProvider(
                name=name,
                display_name=config["display_name"],
                is_configured=is_configured,
                models=config["models"],
                recommended_model=config["recommended"]
            ))
        
        return providers
    
    def get_default_provider_config(self, config_type: str = "generation") -> Dict[str, Any]:
        """
        Get default provider configuration from environment settings.
        
        Args:
            config_type: "generation" or "execution"
            
        Returns:
            Dict with provider and model
        """
        provider = settings.MODEL_PROVIDER
        
        # Map provider to default model
        model_map = {
            "google": settings.GOOGLE_MODEL,
            "cerebras": settings.CEREBRAS_MODEL,
            "openrouter": settings.OPENROUTER_MODEL
        }
        
        return {
            "provider": provider,
            "model": model_map.get(provider, self.PROVIDER_CONFIGS[provider]["recommended"])
        }
    
    def get_user_settings(self, db: Session, user_id: int) -> Optional[UserSetting]:
        """
        Get user settings by user ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            UserSetting object or None
        """
        return db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    def create_user_settings(
        self, 
        db: Session, 
        user_id: int, 
        settings_data: UserSettingCreate
    ) -> UserSetting:
        """
        Create user settings.
        
        Args:
            db: Database session
            user_id: User ID
            settings_data: Settings data
            
        Returns:
            Created UserSetting object
            
        Raises:
            IntegrityError: If settings already exist for user
        """
        db_settings = UserSetting(
            user_id=user_id,
            **settings_data.model_dump()
        )
        
        try:
            db.add(db_settings)
            db.commit()
            db.refresh(db_settings)
            return db_settings
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Settings already exist for user {user_id}")
    
    def update_user_settings(
        self,
        db: Session,
        user_id: int,
        settings_data: UserSettingUpdate
    ) -> UserSetting:
        """
        Update user settings.
        
        Args:
            db: Database session
            user_id: User ID
            settings_data: Settings data to update
            
        Returns:
            Updated UserSetting object
            
        Raises:
            ValueError: If settings don't exist
        """
        db_settings = self.get_user_settings(db, user_id)
        if not db_settings:
            raise ValueError(f"Settings not found for user {user_id}")
        
        # Update only provided fields
        update_data = settings_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_settings, key, value)
        
        db.commit()
        db.refresh(db_settings)
        return db_settings
    
    def get_or_create_user_settings(
        self,
        db: Session,
        user_id: int
    ) -> UserSetting:
        """
        Get existing settings or create default settings for user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            UserSetting object
        """
        db_settings = self.get_user_settings(db, user_id)
        
        if not db_settings:
            # Create default settings from environment
            default_gen = self.get_default_provider_config("generation")
            default_exec = self.get_default_provider_config("execution")
            
            default_settings = UserSettingCreate(
                generation_provider=default_gen["provider"],
                generation_model=default_gen["model"],
                generation_temperature=0.7,
                generation_max_tokens=4096,
                execution_provider=default_exec["provider"],
                execution_model=default_exec["model"],
                execution_temperature=0.7,
                execution_max_tokens=4096
            )
            
            db_settings = self.create_user_settings(db, user_id, default_settings)
        
        return db_settings
    
    def delete_user_settings(self, db: Session, user_id: int) -> bool:
        """
        Delete user settings.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        db_settings = self.get_user_settings(db, user_id)
        if db_settings:
            db.delete(db_settings)
            db.commit()
            return True
        return False
    
    def get_provider_config(
        self,
        db: Session,
        user_id: int,
        config_type: str = "generation"
    ) -> Dict[str, Any]:
        """
        Get provider configuration for user (generation or execution).
        Falls back to environment settings if user settings don't exist.
        
        Args:
            db: Database session
            user_id: User ID
            config_type: "generation" or "execution"
            
        Returns:
            Dict with provider, model, temperature, and max_tokens
        """
        user_settings = self.get_user_settings(db, user_id)
        
        if user_settings:
            if config_type == "generation":
                return {
                    "provider": user_settings.generation_provider,
                    "model": user_settings.generation_model,
                    "temperature": user_settings.generation_temperature,
                    "max_tokens": user_settings.generation_max_tokens
                }
            else:  # execution
                return {
                    "provider": user_settings.execution_provider,
                    "model": user_settings.execution_model,
                    "temperature": user_settings.execution_temperature,
                    "max_tokens": user_settings.execution_max_tokens
                }
        
        # Fallback to environment settings
        default_config = self.get_default_provider_config(config_type)
        return {
            "provider": default_config["provider"],
            "model": default_config["model"],
            "temperature": 0.7,
            "max_tokens": 4096
        }


# Singleton instance
user_settings_service = UserSettingsService()
