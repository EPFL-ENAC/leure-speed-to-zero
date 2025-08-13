"""Region configuration for the application."""
import json
import os
from pathlib import Path

def load_shared_config():
    """Load shared configuration from JSON file."""
    config_file = Path(__file__).parent.parent.parent /  "model_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

shared_config = load_shared_config()

class RegionConfig:
    """Configuration for regional data filtering."""
    
    # Primary region - try shared config first, then env var, then default
    PRIMARY_REGION = (
        shared_config.get("MODEL_PRIMARY_REGION") or 
        "Vaud"
    )
    
    # Available regions
    AVAILABLE_REGIONS = shared_config.get("AVAILABLE_REGIONS", ["Vaud", "Switzerland", "EU27"])
    
    @classmethod
    def get_current_region(cls) -> str:
        """Get the current primary region."""
        return cls.PRIMARY_REGION
    
