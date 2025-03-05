
# packages
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting, fix_jumps_in_dm, my_pickle_dump
import pandas as pd
import pickle
import os
import numpy as np
import warnings
import eurostat
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_lever_passenger_utilization-rate.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# load current transport pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/transport.pickle')
with open(filepath, 'rb') as handle:
    DM_tra = pickle.load(handle)
    
# Set years range
years_setting = [1990, 2023, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(range(startyear, baseyear+1, 1))
years_fts = list(range(baseyear+2, lastyear+1, step_fts))
years_all = years_ots + years_fts

# check
list(DM_tra["ots"])
DM_tra["ots"]["passenger_utilization-rate"].units

# get fleet data
filepath = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_fleet.pickle')
with open(filepath, 'rb') as handle:
    dm_fleet = pickle.load(handle)
dm_fleet.group_all("Categories2")
    
# get vkm data
filepath = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_vkm.pickle')
with open(filepath, 'rb') as handle:
    DM_vkm = pickle.load(handle)
dm_vkm = DM_vkm["ots"]["passenger_vkm"].copy()
dm_vkm.append(DM_vkm["fts"]["passenger_vkm"][1].copy(),"Years")
dm_vkm.sort("Years")

# obtain vkm/veh
dm_uti = dm_vkm.copy()
dm_uti.array = dm_uti.array / dm_fleet.array
dm_uti.units["tra_passenger_vkm"] = "vkm/veh"
dm_uti.rename_col("tra_passenger_vkm","tra_passenger_utilisation-rate","Variables")

# check
# dm_uti.filter({"Country" : ["EU27"]}).datamatrix_plot()

# split between ots and fts
DM_uti = {"ots": {"passenger_utilization-rate" : []}, "fts": {"passenger_utilization-rate" : dict()}}
DM_uti["ots"]["passenger_utilization-rate"] = dm_uti.filter({"Years" : years_ots})
for i in range(1,4+1):
    DM_uti["fts"]["passenger_utilization-rate"][i] = dm_uti.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_passenger_utilization-rate.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_uti, handle, protocol=pickle.HIGHEST_PROTOCOL)






