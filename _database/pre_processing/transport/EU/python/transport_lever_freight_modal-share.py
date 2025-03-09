
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_freight_modal-share.py"

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

DM["ots"]["freight_modal-share"].units

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

###############
##### HDV #####
###############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Freight transport (mio tkm)",
                "sheet_last_row" : "Heavy goods vehicles",
                "sub_variables" : ["Light commercial vehicles",
                                    "Heavy goods vehicles"],
                "calc_names" : ["HDVL","HDVH"]}
dm_hdvl = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# make hdvm as average between hdvh and hdvl (as it's tkm, the medium ones should carry around the average)
dm_temp = dm_hdvl.groupby({"HDVM" : ["HDVL","HDVH"]}, 
                          dim='Variables', aggregation = "mean", regex=False, inplace=False)
dm_hdvl.append(dm_temp, "Variables")
dm_hdvl.sort("Variables")

###############
##### IWW #####
###############

# get data on energy efficiency
dict_extract = {"database" : "Transport",
                "sheet" : "TrNavi_act",
                "variable" : "Transport activity (Mtkm)",
                "sheet_last_row" : "Inland waterways",
                "sub_variables" : ["Inland waterways"],
                "calc_names" : ["IWW"]}
dm_iww = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

####################
##### aviation #####
####################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrAvia_act",
                "variable" : "Freight transport (mio tkm)",
                "sheet_last_row" : "Freight transport (mio tkm)",
                "sub_variables" : ["Freight transport (mio tkm)"],
                "calc_names" : ["aviation"]}
dm_avi = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

####################
##### maritime #####
####################

# get data on energy efficiency
dict_extract = {"database" : "Transport",
                "sheet" : "MBunk_act",
                "variable" : "Transport activity (mio tkm)",
                "sheet_last_row" : "Intra-EEA",
                "sub_variables" : ["Intra-EEA"],
                "calc_names" : ["marine"]}
dm_mar = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)


################
##### RAIL #####
################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "Freight transport (mio tkm)",
                "sheet_last_row" : "Freight transport (mio tkm)",
                "sub_variables" : ["Freight transport (mio tkm)"],
                "calc_names" : ["rail"]}
dm_tkm_rail = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

########################
##### PUT TOGETHER #####
########################

dm_tkm = dm_hdvl.copy()
dm_tkm.append(dm_iww,"Variables")
dm_tkm.append(dm_avi,"Variables")
dm_tkm.append(dm_mar,"Variables")
dm_tkm.append(dm_tkm_rail,"Variables")
dm_tkm.sort("Variables")
dm_tkm.sort("Country")
dm_tkm.units["IWW"] = "mio tkm"

# check
# dm_tkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

###################
##### FIX OTS #####
###################

dm_tkm = linear_fitting(dm_tkm, years_ots)

# check
# dm_tkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

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
dm_tkm.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# set default time window for linear trend
baseyear_start = 2000
baseyear_end = 2019

# # try fts
# product = "rail"
# (make_fts(dm_tkm, product, baseyear_start, baseyear_end, dim = "Variables").
#   datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : [product]}))

# make fts
dm_tkm = make_fts(dm_tkm, "HDVH", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "HDVL", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "HDVM", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "IWW", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "aviation", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "marine", baseyear_start, baseyear_end, dim = "Variables")
dm_tkm = make_fts(dm_tkm, "rail", baseyear_start, baseyear_end, dim = "Variables")

# check
# dm_tkm.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM["ots"]["freight_modal-share"]

# rename and deepen
for v in dm_tkm.col_labels["Variables"]:
    dm_tkm.rename_col(v,"tra_freight_modal-share_" + v, "Variables")
dm_tkm.deepen()

# get it in tkm
dm_tkm.change_unit("tra_freight_modal-share", 1e6, "mio tkm", "tkm")

# do the percentages
dm_tkm_pc = dm_tkm.normalise("Categories1", inplace=False, keep_original=False)
dm_tkm_pc.rename_col("tra_freight_modal-share_share","tra_freight_modal-share","Variables")

# check
# dm_tkm.filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_tkm_pc.group_all("Categories1", inplace=False).write_df()

################
##### SAVE #####
################

# split between ots and fts
DM_mod = {"ots": {"freight_modal-share" : []}, "fts": {"freight_modal-share" : dict()}}
DM_mod["ots"]["freight_modal-share"] = dm_tkm_pc.filter({"Years" : years_ots})
DM_mod["ots"]["freight_modal-share"].drop("Years",startyear)
for i in range(1,4+1):
    DM_mod["fts"]["freight_modal-share"][i] = dm_tkm_pc.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_freight_modal-share.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_mod, handle, protocol=pickle.HIGHEST_PROTOCOL)

# split between ots and fts
dm_tkm.rename_col("tra_freight_modal-share","tra_freight_tkm","Variables")
DM_tkm = {"ots": {"freight_tkm" : []}, "fts": {"freight_tkm" : dict()}}
DM_tkm ["ots"]["freight_tkm"] = dm_tkm.filter({"Years" : years_ots})
DM_tkm ["ots"]["freight_tkm"].drop("Years",startyear)
for i in range(1,4+1):
    DM_tkm["fts"]["freight_tkm"][i] = dm_tkm.filter({"Years" : years_fts})
    
# save
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/freight_tkm.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_tkm, handle, protocol=pickle.HIGHEST_PROTOCOL)
