
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_lever_passenger_technology-share_new.py"

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
DM_tra["ots"]["passenger_technology-share_new"]

# get new registration data
filepath = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_new-vehicles.pickle')
with open(filepath, 'rb') as handle:
    dm_new = pickle.load(handle)

# normalise
dm_new.normalise("Categories2")
dm_new.rename_col("tra_passenger_new-vehicles","tra_passenger_technology-share_new","Variables")

# split between ots and fts
DM_new = {"ots": {"passenger_technology-share_new" : []}, "fts": {"passenger_technology-share_new" : dict()}}
DM_new["ots"]["passenger_technology-share_new"] = dm_new.filter({"Years" : years_ots})
for i in range(1,4+1):
    DM_new["fts"]["passenger_technology-share_new"][i] = dm_new.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_passenger_technology-share_new.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_new, handle, protocol=pickle.HIGHEST_PROTOCOL)









