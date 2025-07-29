import logging
import json
from model.interactions import runner
from model.common.auxiliary_functions import filter_country_and_load_data_from_pickles

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Configures initial input for model run
f = open('config/lever_position.json')
lever_setting = json.load(f)[0]
years_setting = [1990, 2023, 2025, 2050, 5]
country_list = ['Vaud']
#sectors = ['climate', 'lifestyles', 'buildings', 'transport', 'agriculture', 'industry', 'forestry']

sectors = ['climate', 'lifestyles', 'buildings', 'transport', 'agriculture', 'forestry']
# Filter geoscale
# from database/data/datamatrix/.* reads the pickles, filters the geoscale, and loads them
DM_input = filter_country_and_load_data_from_pickles(country_list= country_list, modules_list = sectors)

# Main model run
output, KPI = runner(lever_setting, years_setting, DM_input, sectors, logger, )
logger.info('Run over')

