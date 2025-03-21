
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
for v in dm_new.col_labels["Variables"]:
    dm_new.rename_col(v,"tra_passenger_technology-share_new_" + v,"Variables")
dm_new.deepen_twice()
dm_new.add(np.nan, col_label="FCEV", dummy=True, dim="Categories2")
dm_new.sort("Categories2")
dm_new.normalise("Categories2")

# check
# dm_new.filter({"Country" : ["EU27"]}).flatten().flatten().datamatrix_plot(stacked=True)

###############
##### OTS #####
###############

dm_new_ots = dm_new.filter({"Years" : years_ots})

#######################
##### FTS LEVEL 1 #####
#######################

# level 1: continuing as is
dm_new_fts_level1 = dm_new.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 2 #####
#######################

# TODO: level 2 to do, for the moment we set it continuing as is
dm_new_fts_level2 = dm_new.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 3 #####
#######################

# TODO: level 3 to do, for the moment we set it continuing as is
dm_new_fts_level3 = dm_new.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 4 #####
#######################

# make level 4 with levels in eucalc
dm_new_level4 = dm_new.copy()
years_fts = list(range(2025,2055,5))
idx = dm_new_level4.idx
for y in years_fts:
    dm_new_level4.array[idx["EU27"],idx[y],:,:,:] = np.nan
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["ICE-gasoline"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["ICE-gas"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["ICE-diesel"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["PHEV-gasoline"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["PHEV-diesel"]] = 0
for y in range(1990,2023+1):
    dm_new_level4.array[idx["EU27"],idx[y],:,idx["LDV"],idx["FCEV"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["FCEV"]] = 0.1
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["LDV"],idx["BEV"]] = 0.9
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["2W"],idx["ICE-gasoline"]] = 1
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["bus"],idx["ICE-gasoline"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["bus"],idx["ICE-gas"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["bus"],idx["ICE-diesel"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["bus"],idx["BEV"]] = 1
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["metrotram"],idx["mt"]] = 1
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["rail"],idx["ICE-diesel"]] = 0
dm_new_level4.array[idx["EU27"],idx[2050],:,idx["rail"],idx["CEV"]] = 1
dm_new_level4 = linear_fitting(dm_new_level4, years_fts)
# dm_new_level4.filter({"Country" : ["EU27"]}).flatten().datamatrix_plot(stacked=True)
dm_new_fts_level4 = dm_new_level4.filter({"Years" : years_fts})
# dm_new_fts_level4.filter({"Country" : ["EU27"]}).flatten().datamatrix_plot(stacked=True)

################
##### SAVE #####
################

# split between ots and fts
DM_new = {"ots": {"passenger_technology-share_new" : []}, "fts": {"passenger_technology-share_new" : dict()}}
DM_new["ots"]["passenger_technology-share_new"] = dm_new_ots.copy()
DM_new["fts"]["passenger_technology-share_new"][1] = dm_new_fts_level1.copy()
DM_new["fts"]["passenger_technology-share_new"][2] = dm_new_fts_level2.copy()
DM_new["fts"]["passenger_technology-share_new"][3] = dm_new_fts_level3.copy()
DM_new["fts"]["passenger_technology-share_new"][4] = dm_new_fts_level4.copy()

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_passenger_technology-share_new.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_new, handle, protocol=pickle.HIGHEST_PROTOCOL)









