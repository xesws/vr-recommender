"""System Configuration Manager.

Acts as the source of truth for system settings, prioritizing
database-stored configurations over environment variables.
"""

import os
from typing import Optional, Dict, Any
from .db.repositories.config_repo import ConfigRepository

class ConfigManager:
    """Manages system configuration with DB persistence and Env fallback."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.repo = ConfigRepository()
        self._cache = {}
        self.refresh_config()
        self._initialized = True

    def refresh_config(self):
        """Reload configuration from database."""
        self._cache = self.repo.get_config()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Priority:
        1. Database stored value
        2. Environment variable (key is uppercase)
        3. Default value
        """
        # Check DB cache first
        val = self._cache.get(key.lower()) or self._cache.get(key.upper())
        if val:
            return val
        
        # Check Environment Variable
        env_val = os.getenv(key.upper())
        if env_val:
            return env_val
            
        return default

    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value in the database.
        """
        success = self.repo.update_config(key.lower(), value)
        if success:
            self.refresh_config()
        return success
        
    def set_bulk(self, config_dict: Dict[str, Any]) -> bool:
        """
        Set multiple configuration values in the database.
        """
        # Store keys in lowercase for consistency in DB
        normalized_dict = {k.lower(): v for k, v in config_dict.items()}
        success = self.repo.update_bulk(normalized_dict)
        if success:
            self.refresh_config()
        return success

    # -- Specific Getters for Type Safety --

    @property
    def openrouter_api_key(self) -> Optional[str]:
        return self.get("OPENROUTER_API_KEY")

    @property
    def openrouter_model(self) -> str:
        return self.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

    @property
    def firecrawl_api_key(self) -> Optional[str]:
        return self.get("FIRECRAWL_API_KEY")

    @property
    def tavily_api_key(self) -> Optional[str]:
        return self.get("TAVILY_API_KEY")
        
    @property
    def mongodb_uri(self) -> Optional[str]:
        return self.get("MONGODB_URI")
        
    @property
    def neo4j_uri(self) -> Optional[str]:
        return self.get("NEO4J_URI")
