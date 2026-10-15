"""Lever checks.

The frontend sends one digit per lever, in the order of the model. A lever the
frontend does not know is sent at its model default, and a wrong level is a
400 instead of a crash inside the model. The last test catches a model bump
that adds levers the frontend has no text for: each profile has its lever
texts in frontend/src/config/levers/<profile>.json.
"""

import importlib
import json
import re
from pathlib import Path

import pytest

from src.api.lever_keys import LEVER_KEYS, MAX_LEVEL, MIN_LEVEL, parse_lever_string

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_LEVERS = ROOT / "frontend" / "src" / "config" / "levers"
MODEL_CONFIG = ROOT / "backend" / "model_config.json"
DEFAULT_PACKAGE = "transition_compass_model"


def _profile_packages() -> list[tuple[str, str]]:
    """(profile, model package) for every profile, the default one included."""
    profiles = json.loads(MODEL_CONFIG.read_text()).get("PROFILES", {})
    pairs = [("default", DEFAULT_PACKAGE)]
    pairs += [
        (name, conf.get("MODEL_PACKAGE", DEFAULT_PACKAGE))
        for name, conf in profiles.items()
    ]
    return pairs


def _model_lever_keys(package: str) -> list[str]:
    config_loader = importlib.import_module(f"{package}.model.common.config_loader")
    return list(config_loader.load_lever_config())


def _frontend_lever_codes(profile: str) -> set[str]:
    # Same fallback as the frontend: a profile with no file uses default.json.
    path = FRONTEND_LEVERS / f"{profile}.json"
    if not path.exists():
        path = FRONTEND_LEVERS / "default.json"
    return {lever["code"] for lever in json.loads(path.read_text())}


def test_no_string_means_level_1():
    assert parse_lever_string(None) == {key: MIN_LEVEL for key in LEVER_KEYS}


def test_valid_string():
    levers = str(MAX_LEVEL) * len(LEVER_KEYS)
    assert set(parse_lever_string(levers).values()) == {MAX_LEVEL}


def test_wrong_length():
    with pytest.raises(ValueError, match="digits"):
        parse_lever_string("1")


@pytest.mark.parametrize("bad", ["0", str(MAX_LEVEL + 1), "a"])
def test_bad_level_names_the_lever(bad):
    levers = bad + "1" * (len(LEVER_KEYS) - 1)
    with pytest.raises(ValueError, match=re.escape(LEVER_KEYS[0])):
        parse_lever_string(levers)


@pytest.mark.parametrize("profile, package", _profile_packages())
def test_frontend_knows_every_model_lever(profile, package):
    codes = _frontend_lever_codes(profile)
    missing = [key for key in _model_lever_keys(package) if key not in codes]
    assert not missing, (
        f"{package} has levers with no entry in "
        f"frontend/src/config/levers/{profile}.json: {missing}"
    )
