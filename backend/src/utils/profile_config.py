"""Deployment profile.

One image serves several sites. A profile says which region, which sectors and
which model modules a site runs. It is picked with the MODEL_PROFILE
environment variable and defined in model_config.json under PROFILES.

Without MODEL_PROFILE the app behaves exactly as before: the top level keys of
model_config.json are used.
"""

import os
from typing import Any, Dict

from src.utils.region_config import load_shared_config

DEFAULT_PROFILE = "default"


def get_active_profile() -> str:
    """Name of the profile this instance runs, 'default' if none is set."""
    return os.getenv("MODEL_PROFILE") or DEFAULT_PROFILE


def get_profile_config() -> Dict[str, Any]:
    """Settings of the active profile, empty for the default profile."""
    name = get_active_profile()
    if name == DEFAULT_PROFILE:
        return {}
    profiles = load_shared_config().get("PROFILES", {})
    return profiles.get(name, {})


def profile_value(key: str, default: Any = None) -> Any:
    """Read a key from the profile, fall back to the top level config."""
    profile = get_profile_config()
    if key in profile:
        return profile[key]
    return load_shared_config().get(key, default)
