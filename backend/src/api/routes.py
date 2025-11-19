import hashlib
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
import logging

import orjson
from model.interactions import runner
from model.common.auxiliary_functions import filter_country_and_load_data_from_pickles
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
from src.utils.sector_config import SectorConfig


from src.utils.cache_decorator import conditional_cache


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

# Get all possible sectors for data loading (use the most complete sector's dependencies)
all_sectors = SectorConfig.get_all_available_sectors()

# Filter country
# from database/data/datamatrix/.* reads the pickles, filters the countries, and loads them
DM_input = filter_country_and_load_data_from_pickles(
    country_list=country_list, modules_list=all_sectors
)


@router.get("/v1/run-model")
async def run_model(levers: str | None = None, sector: str | None = None):
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

        # Get sectors to run based on requested sector or all if not specified
        if sector:
            sectors_to_run = SectorConfig.get_sectors_for(sector)
            logger.info(f"Running sectors for '{sector}': {sectors_to_run}")
        else:
            sectors_to_run = SectorConfig.get_all_available_sectors()
            logger.info(f"Running all sectors: {sectors_to_run}")

        start = time.perf_counter()
        output, KPI = runner(
            lever_setting,
            years_setting,
            DM_input,
            sectors_to_run,
            logger,
        )
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
@conditional_cache(expire=600)
async def run_model_clean_structure(
    levers: str | None = None, sector: str | None = None
):
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

        # Get sectors to run based on requested sector or all if not specified
        if sector:
            sectors_to_run = SectorConfig.get_sectors_for(sector)
            logger.info(f"Running sectors for '{sector}': {sectors_to_run}")
        else:
            sectors_to_run = SectorConfig.get_all_available_sectors()
            logger.info(f"Running all sectors: {sectors_to_run}")

        start = time.perf_counter()
        logger.info("Starting model run...")
        logger.info(f"Sectors: {sectors_to_run}")
        output, KPI = runner(
            lever_setting,
            years_setting,
            DM_input,
            sectors_to_run,
            logger,
        )
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
        if isinstance(cleaned_output, dict):
            logger.info(f"Transformed output contains {len(cleaned_output)} sectors")
        else:
            logger.warning("Transformed output is not a dictionary")

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
                "sectors": (
                    list(cleaned_output.keys())
                    if isinstance(cleaned_output, dict)
                    else []
                ),
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
        "available_regions": RegionConfig.get_available_regions(),
    }


@router.get("/debug-sectors")
async def debug_sectors():
    """Debug endpoint to check current sector configuration."""
    return {
        "status": "success",
        "available_sectors": SectorConfig.get_available_sector_names(),
        "all_sectors_execution_order": SectorConfig.get_all_available_sectors(),
        "sector_dependencies": {
            sector: SectorConfig.get_sectors_for(sector)
            for sector in SectorConfig.get_available_sector_names()
        },
    }


@router.post("/reload-config")
async def reload_config():
    """Force reload the region and sector configuration from model_config.json."""
    from src.utils.region_config import RegionConfig
    import logging

    logger = logging.getLogger(__name__)
    logger.info("🔄 Manual configuration reload requested")

    region_result = RegionConfig.force_reload()
    sector_result = SectorConfig.force_reload()

    logger.info(
        f"✅ Configuration reloaded - New region: {region_result['current_region']}"
    )
    logger.info(f"✅ Sectors configured: {sector_result['sectors_configured']}")

    return {
        "status": "success",
        "message": "Configuration reloaded successfully",
        "region": region_result,
        "sectors": sector_result,
    }
