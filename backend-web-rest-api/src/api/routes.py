from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
import logging
import json
from model.interactions import runner
from model.common.auxiliary_functions import filter_geoscale
import numpy as np
import time
import re
from pathlib import Path
from src.api.lever_keys import LEVER_KEYS

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
# The file path to lever_position.json assumes the current working directory is the project root. You may need to adjust this path.

years_setting = [1990, 2023, 2025, 2050, 5]
geo_pattern = 'Switzerland|Vaud|EU27'
filter_geoscale(geo_pattern)


@router.get("/v1/run-model")
async def run_model(levers: str = None):
    try:
        # Parse levers string or use default (all 1s)
        if levers is None:
            lever_values = [1] * len(LEVER_KEYS)
        else:
            lever_values = [int(c) for c in levers]
            if len(lever_values) != len(LEVER_KEYS):
                return ORJSONResponse(content={
                    "status": "error",
                    "message": f"levers string must be {len(LEVER_KEYS)} digits"
                }, status_code=400)
        lever_setting = dict(zip(LEVER_KEYS, lever_values))

        start = time.perf_counter()
        output = runner(lever_setting, years_setting, logger)
        duration = (time.perf_counter() - start) * 1000  # ms

        def serialize(obj):
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif hasattr(obj, "__dict__"):
                return {str(k): serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize(i) for i in obj]
            elif isinstance(obj, dict):
                return {str(k): serialize(v) for k, v in obj.items()}
            else:
                return obj

        serializable_output = {k: serialize(v) for k, v in output.items()}

        response = ORJSONResponse(content={
            "status": "success",
            "sectors": list(serializable_output.keys()),
            "data": serializable_output
        })
        response.headers["Server-Timing"] = f"runmodel;dur={duration:.2f}"
        return response
    except Exception as e:
        logger.error(f"Model execution failed: {str(e)}")
        response = ORJSONResponse(content={
            "status": "error",
            "message": f"Failed to run model: {str(e)}"
        }, status_code=500)
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
