"""Lever checks.

The frontend sends one digit per lever, in the order of the model. A lever the
frontend does not know is sent at its model default, and a wrong level is a
400 instead of a crash inside the model. The last test catches a model bump
that adds levers the frontend has no text for.
"""

import importlib
import json
import re
from pathlib import Path

import pytest

from src.api.lever_keys import LEVER_KEYS, MAX_LEVEL, MIN_LEVEL, parse_lever_string

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_LEVERS = ROOT / "frontend" / "src" / "config" / "levers.ts"
MODEL_CONFIG = ROOT / "backend" / "model_config.json"


def _model_packages() -> list[str]:
    profiles = json.loads(MODEL_CONFIG.read_text()).get("PROFILES", {})
    packages = {"transition_compass_model"}
    packages |= {p["MODEL_PACKAGE"] for p in profiles.values() if "MODEL_PACKAGE" in p}
    return sorted(packages)


def _model_lever_keys(package: str) -> list[str]:
    config_loader = importlib.import_module(f"{package}.model.common.config_loader")
    return list(config_loader.load_lever_config())


def _frontend_lever_codes() -> set[str]:
    return set(re.findall(r"code: '([^']+)'", FRONTEND_LEVERS.read_text()))


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


@pytest.mark.parametrize("package", _model_packages())
def test_frontend_knows_every_model_lever(package):
    missing = [
        k for k in _model_lever_keys(package) if k not in _frontend_lever_codes()
    ]
    assert not missing, (
        f"{package} has levers with no entry in {FRONTEND_LEVERS.relative_to(ROOT)}: "
        f"{missing}"
    )
