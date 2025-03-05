
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_lever_passenger_occupancy.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# load current transport pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/transport.pickle')
with open(filepath, 'rb') as handle:
    DM_tra = pickle.load(handle)

# load pkm
filepath = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_pkm.pickle')
with open(filepath, 'rb') as handle:
    DM_pkm = pickle.load(handle)

# Set years range
years_setting = [1990, 2023, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(range(startyear, baseyear+1, 1))
years_fts = list(range(baseyear+2, lastyear+1, step_fts))
years_all = years_ots + years_fts

################################################
################### GET DATA ###################
################################################

DM_tra["ots"]["passenger_occupancy"].units

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

########################
##### LDV, 2W, BUS #####
########################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Vehicle-km driven (mio km)",
                "sheet_last_row" : "Freight transport",
                "sub_variables" : ["Powered two-wheelers",
                                    "Passenger cars",
                                    "Motor coaches, buses and trolley buses"],
                "calc_names" : ["2W","LDV","bus"]}
dm_vkm_ltb = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# sort
dm_vkm_ltb.sort("Variables")

# check
# dm_vkm_ltb.filter({"Country" : ["EU27"]}).datamatrix_plot()

################
##### RAIL #####
################

# note: also taking this one directly from JRC

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "Vehicle-km (mio km)",
                "sheet_last_row" : "High speed passenger trains",
                "sub_variables" : ["Metro and tram, urban light rail",
                                    "Conventional passenger trains",
                                    "High speed passenger trains"],
                "calc_names" : ["metrotram","train-conv","train-hs"]}
dict_iso2_jrc = jrc_iso2_dict()
dm_vkm_r = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# groupby trains
mapping_calc = {'rail': ['train-conv', 'train-hs']}
dm_vkm_r.groupby(mapping_calc, dim='Variables', aggregation = "sum", regex=False, inplace=True)

########################
##### PUT TOGETHER #####
########################

dm_vkm = dm_vkm_ltb.copy()
dm_vkm.append(dm_vkm_r,"Variables")
dm_vkm.sort("Variables")
dm_vkm.sort("Country")

###################
##### FIX OTS #####
###################

# before 2000: do trend on 2000-2019, and for 2w do 2000-2016 (before the drop)
dm_2w = dm_vkm.filter({"Variables" : ["2W"]})
dm_vkm.drop("Variables",["2W"])
years_fitting = list(range(startyear,1999+1))
dm_vkm = linear_fitting(dm_vkm, years_fitting, based_on=list(range(2000,2019)))
dm_2w = linear_fitting(dm_2w, years_fitting, based_on=list(range(2000,2015)))
dm_vkm.append(dm_2w,"Variables")
dm_vkm.sort("Variables")

# check
# dm_vkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

# for 2022-2023: do trend on 2000-2019 (when we have data pre covid)
dm_vkm = linear_fitting(dm_vkm , [2022,2023], based_on=list(range(2000,2019+1)))

# check
# dm_vkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################
##### MAKE FTS #####
####################

# make function to fill in missing years fts for EU27 with linear fitting
def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
             min_t0=0, min_tb=0, years_fts = years_fts): # I put minimum to 1 so it does not go to zero
    dm = dm.copy()
    idx = dm.idx
    based_on_yars = list(range(year_start, year_end + 1, 1))
    dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
                             years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
    idx_temp = dm_temp.idx
    if dim == "Variables":
        dm.array[idx[country],:,idx[variable],...] = \
            np.round(dm_temp.array[idx_temp[country],:,idx_temp[variable],...],0)
    if dim == "Categories1":
        dm.array[idx[country],:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,idx_temp[variable]], 0)
    if dim == "Categories2":
        dm.array[idx[country],:,:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]], 0)
    if dim == "Categories3":
        dm.array[idx[country],:,:,:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]], 0)
    
    return dm

# add missing years fts
dm_vkm.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# set default time window for linear trend
baseyear_start = 2000
baseyear_end = 2019

# # try fts
# product = "rail"
# (make_fts(dm_vkm, product, baseyear_start, baseyear_end, dim = "Variables").
#   datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : [product]}))

# make fts
dm_vkm = make_fts(dm_vkm, "2W", baseyear_start, baseyear_end, dim = "Variables")
dm_vkm = make_fts(dm_vkm, "LDV", baseyear_start, baseyear_end, dim = "Variables")
dm_vkm = make_fts(dm_vkm, "bus", baseyear_start, baseyear_end, dim = "Variables")
dm_vkm = make_fts(dm_vkm, "metrotram", baseyear_start, baseyear_end, dim = "Variables")
dm_vkm = make_fts(dm_vkm, "rail", baseyear_start, baseyear_end, dim = "Variables")

# check
# dm_vkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM_tra["ots"]["passenger_occupancy"].units

# rename and deepen
for v in dm_vkm.col_labels["Variables"]:
    dm_vkm.rename_col(v,"tra_passenger_vkm_" + v, "Variables")
dm_vkm.deepen()

# get it in vkm
dm_vkm.change_unit("tra_passenger_vkm", 1e6, "mio km", "vkm")

# do pkm/vkm
dm_pkm = DM_pkm["ots"]["passenger_pkm"].copy()
dm_pkm.append(DM_pkm["fts"]["passenger_pkm"][1],"Years")
dm_pkm.sort("Years")
dm_occ = dm_pkm.copy()
dm_occ.array = dm_occ.array/dm_vkm.array
dm_occ.rename_col("tra_passenger_pkm","tra_passenger_occupancy","Variables")
dm_occ.units["tra_passenger_occupancy"] = "pkm/vkm"

# check
# dm_occ.filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_occ.group_all("Categories1", inplace=False).write_df()


################
##### SAVE #####
################

# split between ots and fts
DM_occ = {"ots": {"passenger_occupancy" : []}, "fts": {"passenger_occupancy" : dict()}}
DM_occ ["ots"]["passenger_occupancy"] = dm_occ.filter({"Years" : years_ots})
for i in range(1,4+1):
    DM_occ["fts"]["passenger_occupancy"][i] = dm_occ.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_passenger_occupancy.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_occ, handle, protocol=pickle.HIGHEST_PROTOCOL)

# split between ots and fts
DM_vkm = {"ots": {"passenger_vkm" : []}, "fts": {"passenger_vkm" : dict()}}
DM_vkm ["ots"]["passenger_vkm"] = dm_vkm.filter({"Years" : years_ots})
for i in range(1,4+1):
    DM_vkm["fts"]["passenger_vkm"][i] = dm_vkm.filter({"Years" : years_fts})
    
# save
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_vkm.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_vkm, handle, protocol=pickle.HIGHEST_PROTOCOL)

















