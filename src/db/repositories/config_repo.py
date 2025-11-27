"""Repository for system configuration settings."""
from typing import Dict, Any, Optional
from ..mongo_connection import MongoConnection

class ConfigRepository:
    """Handles CRUD operations for system configuration in MongoDB."""

    def __init__(self):
        """Initialize repository with MongoDB connection."""
        self.connection = MongoConnection()
        self.collection = self.connection.get_collection("system_config")

    def get_config(self) -> Dict[str, Any]:
        """
        Retrieve all system configuration settings.
        
        Returns:
            Dictionary containing configuration key-value pairs.
        """
        # We use a singleton document with _id='global_settings'
        config = self.collection.find_one({"_id": "global_settings"})
        if config:
            return config
        return {}

    def update_config(self, key: str, value: Any) -> bool:
        """
        Update a single configuration setting.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.collection.update_one(
                {"_id": "global_settings"},
                {"$set": {key: value}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating config {key}: {e}")
            return False

    def update_bulk(self, config_dict: Dict[str, Any]) -> bool:
        """
        Update multiple configuration settings at once.
        
        Args:
            config_dict: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.collection.update_one(
                {"_id": "global_settings"},
                {"$set": config_dict},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating bulk config: {e}")
            return False
