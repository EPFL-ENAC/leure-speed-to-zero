
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_passenger_modal-share.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# load current transport pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/transport.pickle')
with open(filepath, 'rb') as handle:
    DM = pickle.load(handle)

# Set years range
years_setting = [1989, 2023, 2050, 5]
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

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland

########################
##### LDV, 2W, BUS #####
########################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Passenger transport (mio pkm)",
                "sheet_last_row" : "Motor coaches, buses and trolley buses",
                "sub_variables" : ["Powered two-wheelers",
                                    "Passenger cars",
                                    "Motor coaches, buses and trolley buses"],
                "calc_names" : ["2W","LDV","bus"]}
dict_iso2_jrc = jrc_iso2_dict()
dm_pkm_ltb = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# sort
dm_pkm_ltb.sort("Variables")
dm_pkm_ltb.sort("Country")

# check
# dm_pkm_ltb.filter({"Country" : ["EU27"]}).datamatrix_plot()

################
##### RAIL #####
################

# note: also taking this one directly from JRC

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "Passenger transport (mio pkm)",
                "sheet_last_row" : "High speed passenger trains",
                "sub_variables" : ["Metro and tram, urban light rail",
                                    "Conventional passenger trains",
                                    "High speed passenger trains"],
                "calc_names" : ["metrotram","train-conv","train-hs"]}
dict_iso2_jrc = jrc_iso2_dict()
dm_pkm_r = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# sort countries
dm_pkm_r.sort("Country")

# groupby trains
mapping_calc = {'rail': ['train-conv', 'train-hs']}
dm_pkm_r.groupby(mapping_calc, dim='Variables', aggregation = "sum", regex=False, inplace=True)

########################
##### PUT TOGETHER #####
########################

dm_pkm = dm_pkm_ltb.copy()
dm_pkm.append(dm_pkm_r,"Variables")
dm_pkm.sort("Variables")

###################
##### FIX OTS #####
###################

# before 2000: do trend on 2000-2019, and for 2w do 2000-2016 (before the drop)
dm_2w = dm_pkm.filter({"Variables" : ["2W"]})
dm_pkm.drop("Variables",["2W"])
years_fitting = list(range(startyear,1999+1))
dm_pkm = linear_fitting(dm_pkm, years_fitting, based_on=list(range(2000,2019)))
dm_2w = linear_fitting(dm_2w, years_fitting, based_on=list(range(2000,2015)))
dm_pkm.append(dm_2w,"Variables")
dm_pkm.sort("Variables")

# check
# dm_pkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

# for 2022-2023: do trend on 2000-2019 (when we have data pre covid)
dm_pkm = linear_fitting(dm_pkm , [2022,2023], based_on=list(range(2000,2019+1)))

# check
# dm_pkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

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
dm_pkm.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# set default time window for linear trend
baseyear_start = 2000
baseyear_end = 2019

# # try fts
# product = "rail"
# (make_fts(dm_pkm, product, baseyear_start, baseyear_end, dim = "Variables").
#   datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : [product]}))

# make fts
dm_pkm = make_fts(dm_pkm, "2W", baseyear_start, baseyear_end, dim = "Variables")
dm_pkm = make_fts(dm_pkm, "LDV", baseyear_start, baseyear_end, dim = "Variables")
dm_pkm = make_fts(dm_pkm, "bus", baseyear_start, baseyear_end, dim = "Variables")
dm_pkm = make_fts(dm_pkm, "metrotram", baseyear_start, baseyear_end, dim = "Variables")
dm_pkm = make_fts(dm_pkm, "rail", baseyear_start, baseyear_end, dim = "Variables")

# check
# dm_pkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM["ots"]["passenger_modal-share"]

# rename and deepen
for v in dm_pkm.col_labels["Variables"]:
    dm_pkm.rename_col(v,"tra_passenger_modal-share_" + v, "Variables")
dm_pkm.deepen()

# get it in pkm
dm_pkm.change_unit("tra_passenger_modal-share", 1e6, "mio pkm", "pkm")

# do the percentages
dm_pkm_pc = dm_pkm.normalise("Categories1", inplace=False, keep_original=False)
dm_pkm_pc.rename_col('tra_passenger_modal-share_share','tra_passenger_modal-share',"Variables")

# check
# dm_pkm.filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_pkm.group_all("Categories1", inplace=False).write_df()

# add variables we do not have
# for now, I put 0 for bike and walk, as pkm may be very low compared to other modes (source: https://www.eea.europa.eu/en/analysis/publications/sustainability-of-europes-mobility-systems/passenger-transport-activity)
# Alternatively, we could consider this data hlth_ehis_pe6e, but other assumptions would need to be made.
dm_pkm_pc.add(0, col_label=["bike","walk"], dummy=True, dim='Categories1')
dm_pkm_pc.sort("Categories1")

################
##### SAVE #####
################

# split between ots and fts
DM_mod = {"ots": {"passenger_modal-share" : []}, "fts": {"passenger_modal-share" : dict()}}
DM_mod["ots"]["passenger_modal-share"] = dm_pkm_pc.filter({"Years" : years_ots})
DM_mod["ots"]["passenger_modal-share"].drop("Years",startyear)
for i in range(1,4+1):
    DM_mod["fts"]["passenger_modal-share"][i] = dm_pkm_pc.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_passenger_modal-share.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_mod, handle, protocol=pickle.HIGHEST_PROTOCOL)

# split between ots and fts
dm_pkm.rename_col("tra_passenger_modal-share","tra_passenger_pkm","Variables")
DM_pkm = {"ots": {"passenger_pkm" : []}, "fts": {"passenger_pkm" : dict()}}
DM_pkm["ots"]["passenger_pkm"] = dm_pkm.filter({"Years" : years_ots})
DM_pkm["ots"]["passenger_pkm"].drop("Years",startyear)
for i in range(1,4+1):
    DM_pkm["fts"]["passenger_pkm"][i] = dm_pkm.filter({"Years" : years_fts})
    
# save
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_pkm.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_pkm, handle, protocol=pickle.HIGHEST_PROTOCOL)
