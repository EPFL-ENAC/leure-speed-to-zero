
# packages
import pickle
import os
import numpy as np
import warnings

# from _database.pre_processing.api_routine_Eurostat import get_data_api_eurostat
warnings.simplefilter("ignore")
import plotly.express as px
import plotly.io as pio
import re
pio.renderers.default='browser'

from _database.pre_processing.api_routine_Eurostat import get_data_api_eurostat
from _database.pre_processing.routine_JRC import get_jrc_data
from model.common.auxiliary_functions import eurostat_iso2_dict, jrc_iso2_dict

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_lever_pkm.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# load current transport pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/transport.pickle')
with open(filepath, 'rb') as handle:
    DM_tra = pickle.load(handle)
    
# load pkm pickle
filepath = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_pkm.pickle')
with open(filepath, 'rb') as handle:
    DM_pkm = pickle.load(handle)

# load population pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/lifestyles.pickle')
with open(filepath, 'rb') as handle:
    DM_lfs = pickle.load(handle)

# Set years range
years_setting = [1990, 2023, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(range(startyear, baseyear+1, 1))
years_fts = list(range(baseyear+2, lastyear+1, step_fts))
years_all = years_ots + years_fts

# get total pkm
dm_pkmtot = DM_pkm["ots"]["passenger_pkm"].copy()
dm_pkmtot.append(DM_pkm["fts"]["passenger_pkm"][1],"Years")
dm_pkmtot.group_all("Categories1")

# get pkm/cap
dm_pkmtot.sort("Country")
dm_pkmtot.sort("Years")
dm_pop = DM_lfs["ots"]["pop"]["lfs_population_"].copy()
dm_pop.append(DM_lfs["fts"]["pop"]["lfs_population_"][1],"Years")
dm_pop.drop("Country",["Vaud","Switzerland","United Kingdom"])
dm_pop.sort("Country")
dm_pop.sort("Years")
dm_pkmtot.array = dm_pkmtot.array / dm_pop.array
dm_pkmtot.units["tra_passenger_pkm"] = "pkm/cap"
dm_pkmtot.rename_col("tra_passenger_pkm","tra_pkm-cap","Variables")

# check
# dm_pkmtot.filter({"Country" : ["EU27"]}).datamatrix_plot()

# split between ots and fts
DM_pkmtot = {"ots": {"pkm" : []}, "fts": {"pkm" : dict()}}
DM_pkmtot ["ots"]["pkm"] = dm_pkmtot.filter({"Years" : years_ots})
for i in range(1,4+1):
    DM_pkmtot["fts"]["pkm"][i] = dm_pkmtot.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_pkm.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_pkmtot, handle, protocol=pickle.HIGHEST_PROTOCOL)








