"""Service for managing user settings."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user_settings import UserSetting
from app.schemas.user_settings import UserSettingCreate, UserSettingUpdate, AvailableProvider, ModelOption
from app.core.config import settings


class UserSettingsService:
    """Service for user settings operations."""
    
    # Provider configurations with available models
    PROVIDER_CONFIGS = {
        "google": {
            "display_name": "Google Gemini",
            "models": [
                "gemini-2.0-flash",
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-2.0-flash-thinking-exp-01-21",
                "gemini-3-flash-preview",
            ],
            "recommended": "gemini-2.0-flash-exp",
            "api_key_env": "GOOGLE_API_KEY"
        },
        "cerebras": {
            "display_name": "Cerebras",
            "models": [
                "llama3.1-8b",
                "llama3.1-70b",
                "llama3.3-70b",
                "gpt-oss-120b",
                "qwen-3-32b"
            ],
            "recommended": "llama3.3-70b",
            "api_key_env": "CEREBRAS_API_KEY"
        },
        "openrouter": {
            "display_name": "OpenRouter",
            # Sprint 10.5: verified $0/$0 free models from openrouter.ai/models
            # ordered recommended-first; all paid/stale models removed.
            "models": [
                "qwen/qwen3-coder-480b-a35b:free",          # ⭐ recommended coder model
                "meta-llama/llama-3.3-70b-instruct:free",   # 1.69B weekly tokens
                "openai/gpt-oss-120b:free",
                "openai/gpt-oss-20b:free",
                "qwen/qwen3-next-80b-a3b-instruct:free",    # 262K ctx
                "nvidia/nemotron-3-nano-30b-a3b:free",      # 256K ctx MoE
                "google/gemma-3-27b:free",
                "mistralai/mistral-small-3.1-24b-instruct:free",
                "z-ai/glm-4.5-air:free",
                "arcee-ai/trinity-mini:free",
                "nvidia/nemotron-nano-9b-v2:free",          # lightweight 128K
                "google/gemma-3-12b:free",
                "google/gemma-3-4b:free",
                "qwen/qwen3-4b:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "nousresearch/hermes-3-llama-3.1-405b:free", # largest free model
                "google/gemini-2.0-flash-exp:free",         # retain: existing recommended
                "google/gemini-flash-1.5:free",             # retain: stable fallback
            ],
            "recommended": "qwen/qwen3-coder-480b-a35b:free",
            "api_key_env": "OPENROUTER_API_KEY"
        },
        "azure": {
            "display_name": "Azure OpenAI",
            "models": [
                "ChatGPT-UAT"
            ],
            "recommended": "ChatGPT-UAT",
            "api_key_env": "AZURE_OPENAI_API_KEY"
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

            # Build rich model_options list; free models detected by :free suffix
            model_options = [
                ModelOption(
                    id=model_id,
                    display_name=model_id,
                    is_free=model_id.endswith(":free"),
                )
                for model_id in config["models"]
            ]

            providers.append(AvailableProvider(
                name=name,
                display_name=config["display_name"],
                is_configured=is_configured,
                models=config["models"],
                recommended_model=config["recommended"],
                model_options=model_options,
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
            "openrouter": settings.OPENROUTER_MODEL,
            "azure": getattr(settings, "AZURE_OPENAI_MODEL", "ChatGPT-UAT")
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
    
    # Per-agent Azure fallbacks (Sprint 10.6)
    _AGENT_AZURE_DEFAULT = {"provider": "azure", "model": "ChatGPT-UAT"}
    _VALID_AGENT_NAMES = frozenset({"observation", "requirements", "analysis", "evolution"})

    def get_agent_config(
        self,
        db: Optional[Session],
        user_id: int,
        agent_name: str,
    ) -> Dict[str, Any]:
        """
        Return the effective {provider, model} for the given agent.

        Resolution order:
          1. If db is None or no user-settings row exists → Azure default.
          2. If the per-agent provider column is set → use override.
             If provider is set but model is None → use the provider's recommended model.
          3. Otherwise → Azure default.

        Args:
            db:         SQLAlchemy Session (may be None in background tasks).
            user_id:    ID of the authenticated user.
            agent_name: One of "observation", "requirements", "analysis", "evolution".

        Returns:
            Dict with "provider" (str) and "model" (str).

        Raises:
            ValueError: If agent_name is not recognised.
        """
        if agent_name not in self._VALID_AGENT_NAMES:
            raise ValueError(
                f"Unknown agent: {agent_name!r}. "
                f"Must be one of: {sorted(self._VALID_AGENT_NAMES)}"
            )

        # Resolve provider fallback: use PROVIDER_CONFIGS recommended when available
        def _default_model_for_provider(provider: str) -> str:
            cfg = self.PROVIDER_CONFIGS.get(provider)
            if cfg:
                return cfg["recommended"]
            return self._AGENT_AZURE_DEFAULT["model"]

        if db is None:
            return dict(self._AGENT_AZURE_DEFAULT)

        user_settings = self.get_user_settings(db, user_id)
        if user_settings is None:
            return dict(self._AGENT_AZURE_DEFAULT)

        provider_val = getattr(user_settings, f"{agent_name}_provider", None)
        model_val = getattr(user_settings, f"{agent_name}_model", None)

        if provider_val is None:
            return dict(self._AGENT_AZURE_DEFAULT)

        # Provider is set; resolve model
        resolved_model = model_val if model_val else _default_model_for_provider(provider_val)
        return {"provider": provider_val, "model": resolved_model}

    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """
        Get the appropriate API key from environment variables based on provider.
        
        Args:
            provider: Provider name ("openrouter", "google", "gemini", "cerebras")
            
        Returns:
            API key from environment or None
        """
        import os
        
        if provider == "cerebras":
            return os.getenv("CEREBRAS_API_KEY")
        elif provider in ["google", "gemini"]:
            return os.getenv("GOOGLE_API_KEY")
        elif provider == "azure":
            return os.getenv("AZURE_OPENAI_API_KEY")
        elif provider == "openrouter":
            return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        else:
            # Default fallback
            return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    
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
            # Get API key from environment based on provider (not stored in database for security)
            import os
            
            if config_type == "generation":
                provider = user_settings.generation_provider
                api_key = self._get_api_key_for_provider(provider)
                return {
                    "provider": provider,
                    "model": user_settings.generation_model,
                    "api_key": api_key,  # From environment variables
                    "temperature": user_settings.generation_temperature,
                    "max_tokens": user_settings.generation_max_tokens
                }
            else:  # execution
                provider = user_settings.execution_provider
                api_key = self._get_api_key_for_provider(provider)
                return {
                    "provider": provider,
                    "model": user_settings.execution_model,
                    "api_key": api_key,  # From environment variables
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
