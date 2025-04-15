from fastapi import APIRouter
import logging
import json
from model.interactions import runner
from model.common.auxiliary_functions import filter_geoscale

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

@router.get("/run-model")
async def run_model() -> dict:
    """Run the PathwayCalc model and return results"""
    try:
        # Configure inputs for model run
        with open('config/lever_position.json') as f:
            lever_setting = json.load(f)[0]
        years_setting = [1990, 2023, 2025, 2050, 5]
        geo_pattern = 'Switzerland|Vaud|EU27'

        # Filter geoscale
        filter_geoscale(geo_pattern)
        
        # Run the model
        output = runner(lever_setting, years_setting, logger)
        
        # Return results
        return {
            "status": "success",
            "sectors": list(output.keys()),
            "data": output  # Note: this may need serialization handling depending on output types
        }
    except Exception as e:
        logger.error(f"Model execution failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to run model: {str(e)}"
        }
