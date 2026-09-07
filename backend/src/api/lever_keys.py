# The lever keys, in the order the frontend sends them.
#
# They come from the installed model (config/lever_position.json), so a model
# with other levers, like the TCAF build, works without touching the app. The
# list below is only the fallback, for a model too old to have config_loader.

import logging

logger = logging.getLogger("uvicorn")

_FALLBACK_LEVER_KEYS = [
    "lever_pkm",
    "lever_passenger_modal-share",
    "lever_passenger_occupancy",
    "lever_passenger_utilization-rate",
    "lever_floor-intensity",
    "lever_floor-area-fraction",
    "lever_heatcool-behaviour",
    "lever_appliance-own",
    "lever_appliance-use",
    "lever_kcal-req",
    "lever_diet",
    "lever_paperpack",
    "lever_product-substitution-rate",
    "lever_fwaste",
    "lever_freight_tkm",
    "lever_passenger_veh-efficiency_new",
    "lever_passenger_technology-share_new",
    "lever_freight_vehicle-efficiency_new",
    "lever_freight_technology-share_new",
    "lever_freight_modal-share",
    "lever_freight_utilization-rate",
    "lever_fuel-mix",
    "lever_building-renovation-rate",
    "lever_district-heating-share",
    "lever_heating-technology-fuel",
    "lever_heating-efficiency",
    "lever_appliance-efficiency",
    "lever_material-efficiency",
    "lever_material-switch",
    "lever_technology-share",
    "lever_technology-development",
    "lever_energy-carrier-mix",
    "lever_cc",
    "lever_ccus",
    "lever_decom_fossil",
    "lever_ccs",
    "lever_capacity_nuclear",
    "lever_capacity_RES_wind",
    "lever_capacity_RES_solar",
    "lever_capacity_RES_other",
    "lever_bal-strat",
    "lever_str_charging",
    "lever_climate-smart-crop",
    "lever_climate-smart-livestock",
    "lever_bioenergy-capacity",
    "lever_alt-protein",
    "lever_climate-smart-forestry",
    "lever_land-man",
    "lever_biomass-hierarchy",
    "lever_biodiversity",
    "lever_land-prioritisation",
    "lever_pop",
    "lever_ruminant-feed",
    "lever_ems-after-2050",
    "lever_food-net-import",
    "lever_product-net-import",
    "lever_material-net-import",
    "lever_temp",
    "lever_passenger_aviation-pkm",
    "lever_pv-capacity",
    "lever_csp-capacity",
    "lever_onshore-wind-capacity",
    "lever_offshore-wind-capacity",
    "lever_biogas-capacity",
    "lever_biomass-capacity",
    "lever_hydroelectric-capacity",
    "lever_geothermal-capacity",
    "lever_marine-capacity",
    "lever_gas-capacity",
    "lever_oil-capacity",
    "lever_coal-capacity",
    "lever_nuclear-capacity",
    "lever_carbon-storage-capacity",
    "lever_ev-charging-profile",
    "lever_non-residential-heat-profile",
    "lever_residential-heat-profile",
    "lever_non-residential-cooling-profile",
    "lever_residential-cooling-profile",
    "lever_eol-waste-management",
    "lever_eol-material-recovery",
    "lever_harvest-rate",
]


def _load_lever_keys() -> list[str]:
    try:
        from transition_compass_model.model.common.config_loader import (
            load_lever_config,
        )

        keys = list(load_lever_config().keys())
        if keys:
            return keys
        logger.warning("Model lever config is empty, using the built-in list")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not read the lever config from the model: {exc}")
    return _FALLBACK_LEVER_KEYS


LEVER_KEYS = _load_lever_keys()
