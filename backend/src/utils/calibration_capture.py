"""Calibration rates of a model run.

Each model module calibrates its raw outputs with calibration_rates
(reference / raw) and then drops the rates, so they never reach the output.
To show them, the run is done with calibration_rates wrapped: every call is
recorded with the module and variable it calibrates. The model is not changed.
"""

import sys
import warnings
from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np

from src.utils.model_package import MODEL_PACKAGE

_MODULE_PREFIX = f"{MODEL_PACKAGE}.model."


def _caller(depth: int = 2) -> tuple[str, str]:
    """Model module and function that called calibration_rates.

    A module can call it through a local helper (tcaf_module's _calib): skip
    those frames up to the module's own function.
    """
    frame = sys._getframe(depth)
    while frame.f_code.co_name.startswith("_") and frame.f_back is not None:
        frame = frame.f_back
    module = frame.f_globals.get("__name__", "").removeprefix(_MODULE_PREFIX)
    return module.removesuffix("_module"), frame.f_code.co_name


@contextmanager
def capture_calibration_rates() -> Iterator[list[dict[str, Any]]]:
    """Record every calibration_rates call made inside the block.

    Each record keeps the returned datamatrix itself: some modules change it
    after the call (crop sets rice to 1, land use sets extensive to 1), so it
    is read once the run is over. The model runs synchronously inside one
    request, so patching the module globals does not leak into another run.
    """
    records: list[dict[str, Any]] = []
    patched = []

    for name, module in list(sys.modules.items()):
        if not name.startswith(_MODULE_PREFIX):
            continue
        original = getattr(module, "calibration_rates", None)
        if original is None or getattr(original, "__wrapped__", None):
            continue

        def wrapper(dm, dm_cal, years_setting, *args, _original=original, **kwargs):
            rates = _original(dm, dm_cal, years_setting, *args, **kwargs)
            module_name, function = _caller()
            records.append(
                {
                    "module": module_name,
                    "function": function,
                    "variable": dm.col_labels["Variables"][0],
                    "start_year": kwargs.get("calibration_start_year", 1990),
                    "end_year": kwargs.get("calibration_end_year", 2023),
                    "dm": rates,
                }
            )
            return rates

        wrapper.__wrapped__ = original
        setattr(module, "calibration_rates", wrapper)
        patched.append((module, original))

    try:
        yield records
    finally:
        for module, original in patched:
            module.calibration_rates = original


def _clean(values: np.ndarray) -> list[float | None]:
    return [float(v) if np.isfinite(v) else None for v in values]


def serialize_calibration_record(record: dict[str, Any], country: str) -> dict:
    """One record as {years, series: [{name, values}]} for the region.

    A rate over several countries is the imports split per exporting country:
    the region's own row is empty there, so it is summarised by the median over
    the exporting countries.
    """
    dm = record["dm"]
    countries = list(dm.col_labels["Country"])
    years = [int(y) for y in dm.col_labels["Years"]]
    # Country x Years x Variables(cal_rate) x Categories...
    array = np.asarray(dm.array, dtype=float)[:, :, 0, ...]

    if len(countries) == 1:
        array = array[0]
        scope = countries[0]
    else:
        exporters = [i for i, c in enumerate(countries) if c != country]
        finite = np.where(np.isfinite(array[exporters]), array[exporters], np.nan)
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN slices
            array = np.nanmedian(finite, axis=0)
        scope = f"median over {len(exporters)} exporting countries"

    category_dims = [d for d in dm.dim_labels if d.startswith("Categories")]
    labels = [list(dm.col_labels[d]) for d in category_dims]
    series = []
    if not labels:
        series.append({"name": record["variable"], "values": _clean(array)})
    else:
        flat = array.reshape(len(years), -1)
        names = [" / ".join(combo) for combo in _combinations(labels)]
        for i, name in enumerate(names):
            series.append({"name": name, "values": _clean(flat[:, i])})

    per_exporter = len(countries) > 1
    return {
        # A module can calibrate one variable twice, for the region and per
        # exporting country (crop's domestic production)
        "id": record["variable"] + ("@exporters" if per_exporter else ""),
        "module": record["module"],
        "function": record["function"],
        "variable": record["variable"],
        "calibration_window": [record["start_year"], record["end_year"]],
        "scope": scope,
        "years": years,
        "series": series,
    }


def _combinations(labels: list[list[str]]) -> list[tuple[str, ...]]:
    """Category label tuples in C order, matching reshape(len(years), -1)."""
    combos: list[tuple[str, ...]] = [()]
    for level in labels:
        combos = [c + (label,) for c in combos for label in level]
    return combos
