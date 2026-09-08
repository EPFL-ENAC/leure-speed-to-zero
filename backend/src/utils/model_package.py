"""The model package this site runs.

Several models can be installed at the same time. They are separate python
packages, so a site picks one with MODEL_PACKAGE in its profile. Without a
profile the app uses the main model, transition_compass_model, and nothing
changes.

Everything the API needs from the model goes through here, so there is only one
place that knows the package name.
"""

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType

from src.utils.profile_config import profile_value

logger = logging.getLogger("uvicorn")

DEFAULT_MODEL_PACKAGE = "transition_compass_model"


def get_model_package_name() -> str:
    """Import name of the model package for the active profile."""
    return profile_value("MODEL_PACKAGE", DEFAULT_MODEL_PACKAGE)


def _import(name: str) -> ModuleType:
    return importlib.import_module(name)


MODEL_PACKAGE = get_model_package_name()

try:
    model_package = _import(MODEL_PACKAGE)
except ImportError as exc:
    raise ImportError(
        f"The profile asks for the model package '{MODEL_PACKAGE}' but it is not "
        f"installed. Add it to backend/pyproject.toml and run 'uv lock'."
    ) from exc

model = _import(f"{MODEL_PACKAGE}.model")

# The pickles were written before the model became a package, they name their
# classes under 'model.common.*'. Point that name at the package we just picked.
sys.modules["model"] = model

runner = _import(f"{MODEL_PACKAGE}.model.interactions").runner
filter_country_and_load_data_from_pickles = _import(
    f"{MODEL_PACKAGE}.model.common.auxiliary_functions"
).filter_country_and_load_data_from_pickles
get_lever_data_to_plot = _import(
    f"{MODEL_PACKAGE}.model.common.lever_plotting"
).get_lever_data_to_plot

DATAMATRIX_DIR = (
    Path(model_package.__file__).parent / "_database" / "data" / "datamatrix"
)

logger.info(f"Model package: {MODEL_PACKAGE} ({model_package.__file__})")


def load_lever_keys() -> list[str]:
    """Lever names, in the order the model expects them in the lever string."""
    config_loader = _import(f"{MODEL_PACKAGE}.model.common.config_loader")
    return list(config_loader.load_lever_config().keys())
