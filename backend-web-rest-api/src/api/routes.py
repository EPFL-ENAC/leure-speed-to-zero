from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
import logging
import json
from model.interactions import runner
from model.common.auxiliary_functions import filter_geoscale
import numpy as np

router = APIRouter()
logger = logging.getLogger("uvicorn")

@router.get("/health")
async def health_check() -> dict:
    """Check if the API and its dependencies are healthy"""
    return {
        "status": "healthy",
    }

lever_setting = {"lever_pkm":1,
  "lever_passenger_modal-share":1,
  "lever_passenger_occupancy":1,
  "lever_passenger_utilization-rate":1,
  "lever_floor-intensity":1,
  "lever_floor-area-fraction":1,
  "lever_heatcool-behaviour":1,
  "lever_appliance-own":1,
  "lever_appliance-use":1,
  "lever_kcal-req":1,
  "lever_diet":1,
  "lever_paperpack":1,
  "lever_product-substitution-rate":1,
  "lever_fwaste":1,
  "lever_freight_tkm":1,
  "lever_passenger_veh-efficiency_new":1,
  "lever_passenger_technology-share_new":1,
  "lever_freight_vehicle-efficiency_new":1,
  "lever_freight_technology-share_new":1,
  "lever_freight_modal-share":1,
  "lever_freight_utilization-rate":1,
  "lever_fuel-mix":1,
  "lever_building-renovation-rate":1,
  "lever_district-heating-share":1,
  "lever_heating-technology-fuel":1,
  "lever_heating-efficiency":1,
  "lever_appliance-efficiency":1,
  "lever_material-efficiency":1,
  "lever_material-switch":1,
  "lever_technology-share":1,
  "lever_technology-development":1,
  "lever_energy-carrier-mix":1,
  "lever_cc":1,
  "lever_ccus":1,
  "lever_decom_fossil":1,
  "lever_ccs":1,
  "lever_capacity_nuclear":1,
  "lever_capacity_RES_wind":1,
  "lever_capacity_RES_solar":1,
  "lever_capacity_RES_other":1,
  "lever_bal-strat":1,
  "lever_str_charging":1,
  "lever_climate-smart-crop":1,
  "lever_climate-smart-livestock":1,
  "lever_bioenergy-capacity":1,
  "lever_alt-protein":1,
  "lever_climate-smart-forestry":1,
  "lever_land-man":1,
  "lever_biomass-hierarchy":1,
  "lever_biodiversity":1,
  "lever_land-prioritisation":1,
  "lever_pop":1,
  "lever_urbpop":1,
  "lever_ems-after-2050":1,
  "lever_food-net-import":1,
  "lever_product-net-import":1,
  "lever_material-net-import":1,
  "lever_temp":1,
  "lever_passenger_aviation-pkm":1,
  "lever_pv-capacity":1,
  "lever_csp-capacity":1,
  "lever_onshore-wind-capacity":1,
  "lever_offshore-wind-capacity":1,
  "lever_biogas-capacity":1,
  "lever_biomass-capacity":1,
  "lever_hydroelectric-capacity":1,
  "lever_geothermal-capacity":1,
  "lever_marine-capacity":1,
  "lever_gas-capacity":1,
  "lever_oil-capacity":1,
  "lever_coal-capacity":1,
  "lever_nuclear-capacity":1,
  "lever_carbon-storage-capacity":1,
  "lever_ev-charging-profile": 1,
  "lever_non-residential-heat-profile": 1,
  "lever_residential-heat-profile": 1,
  "lever_non-residential-cooling-profile": 1,
  "lever_residential-cooling-profile": 1,
  "lever_eol-waste-management": 1,
  "lever_eol-material-recovery": 1
}

# For a production implementation, you might want to:

# Add support for customizing parameters via query params or request body
# Make the endpoint asynchronous if the model takes a long time to run
# Add proper error handling and validation
# Implement caching for frequent requests with the same parameters
# The file path to lever_position.json assumes the current working directory is the project root. You may need to adjust this path.

@router.get("/run-model")
async def run_model():
    try:
        years_setting = [1990, 2023, 2025, 2050, 5]
        geo_pattern = 'Switzerland|Vaud|EU27'
        filter_geoscale(geo_pattern)
        output = runner(lever_setting, years_setting, logger)

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

        return ORJSONResponse(content={
            "status": "success",
            "sectors": list(serializable_output.keys()),
            "data": serializable_output
        })
    except Exception as e:
        logger.error(f"Model execution failed: {str(e)}")
        return ORJSONResponse(content={
            "status": "error",
            "message": f"Failed to run model: {str(e)}"
        }, status_code=500)
