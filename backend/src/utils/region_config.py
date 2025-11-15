"""Region configuration for the application."""
import json
from pathlib import Path
from functools import lru_cache
import time

_config_cache = {"data": None, "mtime": 0}

def load_shared_config():
    """Load shared configuration from JSON file with caching and hot-reload support."""
    config_file = Path(__file__).parent.parent.parent / "model_config.json"
    
    if not config_file.exists():
        return {}
    
    # Check if file has been modified
    current_mtime = config_file.stat().st_mtime
    
    # Reload if file changed or not yet loaded
    if _config_cache["data"] is None or current_mtime > _config_cache["mtime"]:
        with open(config_file, 'r') as f:
            _config_cache["data"] = json.load(f)
            _config_cache["mtime"] = current_mtime
    
    return _config_cache["data"]

class RegionConfig:
    """Configuration for regional data filtering with hot-reload support."""
    
    @classmethod
    def get_current_region(cls) -> str:
        """Get the current primary region (reloads config if file changed)."""
        config = load_shared_config()
        return config.get("MODEL_PRIMARY_REGION", "Vaud")
    
    @classmethod
    def get_available_regions(cls) -> list[str]:
        """Get available regions (reloads config if file changed)."""
        config = load_shared_config()
        return config.get("AVAILABLE_REGIONS", ["Vaud", "Switzerland", "EU27"])
    
    @classmethod
    def force_reload(cls) -> dict:
        """Force reload the configuration from file."""
        global _config_cache
        _config_cache["data"] = None
        _config_cache["mtime"] = 0
        config = load_shared_config()
        return {
            "reloaded": True,
            "current_region": cls.get_current_region(),
            "available_regions": cls.get_available_regions()
        }

