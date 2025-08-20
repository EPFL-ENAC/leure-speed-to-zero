import hashlib
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
import logging

import orjson
from model.interactions import runner
from model.common.auxiliary_functions import filter_country_and_load_data_from_pickles
import numpy as np
import time
import re
from pathlib import Path
from src.api.lever_keys import LEVER_KEYS
import pickle

from src.utils.serialize_model import serialize_model_output
from src.utils.transform_model import (
    transform_datamatrix_to_clean_structure,
)

from src.utils.region_config import RegionConfig


from fastapi_cache.decorator import cache


router = APIRouter()
logger = logging.getLogger("uvicorn")


@router.get("/health")
async def health_check() -> dict:
    """Check if the API and its dependencies are healthy"""
    return {
        "status": "healthy",
    }


# For a production implementation, you might want to:

# Add support for customizing parameters via query params or request body
# Make the endpoint asynchronous if the model takes a long time to run
# Add proper error handling and validation
# Implement caching for frequent requests with the same parameters
# The file path to lever_position.json assumes the current working directory
# is the project root. You may need to adjust this path.

years_setting = [
    1990,
    2023,
    2025,
    2050,
    5,
]  # [start_year, current_year, future_year, end_year, step]
country_list = [RegionConfig.get_current_region()]
sectors = ['climate', 'lifestyles', 'buildings', 'transport']

# Filter country
# from database/data/datamatrix/.* reads the pickles, filters the countries, and loads them
DM_input = filter_country_and_load_data_from_pickles(country_list= country_list, modules_list = sectors)


@router.get("/v1/run-model")
async def run_model(levers: str = None):
    try:
        # Parse levers string or use default (all 1s)
        if levers is None:
            lever_values = [1] * len(LEVER_KEYS)
        else:
            lever_values = [int(c) for c in levers]
            if len(lever_values) != len(LEVER_KEYS):
                return ORJSONResponse(
                    content={
                        "status": "error",
                        "message": f"levers string must be {len(LEVER_KEYS)} digits",
                    },
                    status_code=400,
                )
        lever_setting = dict(zip(LEVER_KEYS, lever_values))
        logger.info(f"Levers input: {str(lever_setting)}")

        start = time.perf_counter()
        output, KPI = runner(lever_setting, years_setting, DM_input, sectors, logger, )
        duration = (time.perf_counter() - start) * 1000  # ms

        serializable_output = {k: serialize_model_output(v) for k, v in output.items()}
        output_str = orjson.dumps(serializable_output)
        fingerprint_result = hashlib.md5(output_str).hexdigest()[:12]
        fingerprint_input = hashlib.md5(orjson.dumps(lever_setting)).hexdigest()[:12]
        response = ORJSONResponse(
            content={
                "fingerprint_result": fingerprint_result,
                "fingerprint_input": fingerprint_input,
                "status": "success",
                "kpis": KPI,
                "sectors": list(serializable_output.keys()),
                "data": serializable_output,
            }
        )
        response.headers["Server-Timing"] = f"runmodel;dur={duration:.2f}"
        return response
    except Exception as e:
        logger.error(f"Model execution failed: {str(e)}")
        response = ORJSONResponse(
            content={"status": "error", "message": f"Failed to run model: {str(e)}"},
            status_code=500,
        )
        response.headers["Server-Timing"] = "runmodel;dur=0"
        return response


@router.get("/v1/run-model-clean-structure")
@cache(expire=600)
async def run_model_clean_structure(levers: str = None):
    try:
        # Parse levers string or use default (all 1s)
        if levers is None:
            lever_values = [1] * len(LEVER_KEYS)
        else:
            lever_values = [int(c) for c in levers]
            if len(lever_values) != len(LEVER_KEYS):
                return ORJSONResponse(
                    content={
                        "status": "error",
                        "message": f"levers string must be {len(LEVER_KEYS)} digits",
                    },
                    status_code=400,
                )

        lever_setting = dict(zip(LEVER_KEYS, lever_values))

        start = time.perf_counter()
        logger.info("Starting model run...")
        output, KPI = runner(lever_setting, years_setting, DM_input, sectors, logger, )
        logger.info(
            f"Model run completed in {(time.perf_counter() - start) * 1000:.2f}ms"
        )
        logger.info(f"KPI: {KPI}")

        duration = (time.perf_counter() - start) * 1000  # ms

        # Use the transformer utility
        logger.info("Starting data transformation...")
        transform_start = time.perf_counter()
        cleaned_output = transform_datamatrix_to_clean_structure(output)
        transform_duration = (time.perf_counter() - transform_start) * 1000
        logger.info(f"Data transformation completed in {transform_duration:.2f}ms")

        # Log information about the transformed output
        logger.info(f"Transformed output contains {len(cleaned_output)} sectors")

        json_parse_start = time.perf_counter()
        # Generate fingerprints
        output_str = orjson.dumps(cleaned_output)
        fingerprint_result = hashlib.md5(output_str).hexdigest()[:12]
        fingerprint_input = hashlib.md5(orjson.dumps(lever_setting)).hexdigest()[:12]

        response = ORJSONResponse(
            content={
                "fingerprint_result": fingerprint_result,
                "fingerprint_input": fingerprint_input,
                "status": "success",
                "sectors": list(cleaned_output.keys()),
                "kpis": KPI,
                "data": cleaned_output,
            }
        )
        response.headers["Server-Timing"] = f"runmodel;dur={duration:.2f}"
        logger.info("Returning transformed data response")
        logger.info(
            f"JSON serialization completed in {(time.perf_counter() - json_parse_start) * 1000:.2f}ms"
        )
        return response
    except Exception as e:
        logger.error(
            f"Model execution failed: {str(e)}", exc_info=True
        )  # Include full traceback
        response = ORJSONResponse(
            content={"status": "error", "message": f"Failed to run model: {str(e)}"},
            status_code=500,
        )
        response.headers["Server-Timing"] = "runmodel;dur=0"
        return response


@router.get("/v1/version")
async def get_version():
    """Return the current API version from the CHANGELOG.md file."""
    changelog_path = Path(__file__).parent.parent.parent.parent / "CHANGELOG.md"
    version = "Unknown"
    if changelog_path.exists():
        with open(changelog_path, "r") as f:
            for line in f:
                match = re.match(r"## \[([0-9]+\.[0-9]+\.[0-9]+)\]", line)
                if match:
                    version = match.group(1)
                    break
    return {"version": version}


@router.get("/v1/datamatrix/{name}")
async def get_datamatrix(name: str):
    """Return the content of a single datamatrix pickle file as a JSON-serializable object."""

    try:
        allowed = [
            "agriculture",
            "ammonia",
            "buildings",
            "climate",
            "district-heating",
            "emissions",
            "industry",
            "landuse",
            "lifestyles",
            "minerals_new",
            "minerals",
            "oil-refinery",
            "transport",
        ]
        if name not in allowed:
            return ORJSONResponse(
                content={"status": "error", "message": f"Unknown datamatrix: {name}"},
                status_code=404,
            )
        file = f"_database/data/datamatrix/{name}.pickle"

        with open(file, "rb") as f:
            data = pickle.load(f)
        result = serialize_model_output(data)
        return ORJSONResponse(content={"status": "success", "data": result})
    except Exception as e:
        return ORJSONResponse(
            content={"status": "error", "message": str(e)}, status_code=500
        )


@router.get("/debug-region")
async def debug_region():
    """Debug endpoint to check current region configuration."""
    from src.utils.region_config import RegionConfig

    return {
        "status": "success",
        "current_region": RegionConfig.get_current_region(),
        "available_regions": RegionConfig.AVAILABLE_REGIONS,
    }
