import logging
import json
from model.interactions import runner
from model.common.auxiliary_functions import filter_geoscale

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Configures initial input for model run
f = open('config/lever_position.json')
lever_setting = json.load(f)[0]
years_setting = [1990, 2023, 2025, 2050, 5]
geo_pattern = 'Switzerland|Vaud|EU27'

# Filter geoscale
# from _database/data/datamatrix/.* reads the pickles, filters the geoscale, and saves new filtered pickles to geoscale/
filter_geoscale(geo_pattern)
# Main model run
output = runner(lever_setting, years_setting, logger)

logger.info('Run over')
