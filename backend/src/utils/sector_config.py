"""
Sector configuration management for the Transition Compass model.

This module provides utilities to manage sector dependencies and execution order
based on the model_config.json configuration file.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class SectorConfig:
    """Manages sector configuration and dependencies."""

    _config_cache: Dict[str, List[str]] = {}
    _config_loaded = False

    @classmethod
    def _load_config(cls) -> None:
        """Load sector configuration from model_config.json."""
        if cls._config_loaded:
            return

        config_path = Path(__file__).parent.parent.parent / "model_config.json"

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                cls._config_cache = config.get("SECTORS_TO_RUN", {})
                cls._config_loaded = True
                logger.info(
                    f"Loaded sector configuration with {len(cls._config_cache)} sectors"
                )
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}")
            cls._config_cache = {}
            cls._config_loaded = True
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {e}")
            cls._config_cache = {}
            cls._config_loaded = True

    @classmethod
    def get_sectors_for(cls, sector: str) -> List[str]:
        """
        Get the list of sectors required to run a specific sector.

        Args:
            sector: The target sector name

        Returns:
            List of sectors to run (in execution order) including dependencies
        """
        cls._load_config()

        if sector not in cls._config_cache:
            logger.warning(
                f"Sector '{sector}' not found in configuration, returning single sector"
            )
            return [sector]

        return cls._config_cache[sector]

    @classmethod
    def get_all_available_sectors(cls) -> List[str]:
        """
        Get all unique sectors from all dependency chains.

        Returns:
            List of all unique sectors across all dependency chains
        """
        cls._load_config()

        if not cls._config_cache:
            logger.warning("No sector configuration found, using default sectors")
            return [
                "climate",
                "lifestyles",
                "buildings",
                "energy",
                "forestry",
                "transport",
            ]

        # Collect all unique sectors from all dependency chains
        all_sectors = set()
        for sectors_list in cls._config_cache.values():
            all_sectors.update(sectors_list)

        # Return as list to maintain consistency with return type
        return list(all_sectors)

    @classmethod
    def get_available_sector_names(cls) -> List[str]:
        """
        Get list of all sector names defined in configuration.

        Returns:
            List of sector names
        """
        cls._load_config()
        return list(cls._config_cache.keys())

    @classmethod
    def force_reload(cls) -> Dict:
        """
        Force reload the sector configuration from disk.

        Returns:
            Dictionary with reloaded configuration info
        """
        cls._config_loaded = False
        cls._config_cache = {}
        cls._load_config()

        return {
            "sectors_configured": len(cls._config_cache),
            "available_sectors": cls.get_available_sector_names(),
            "execution_order": cls.get_all_available_sectors(),
        }
