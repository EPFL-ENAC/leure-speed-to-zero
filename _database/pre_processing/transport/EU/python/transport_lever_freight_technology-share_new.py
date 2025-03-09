
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_lever_freight_technology-share_new.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# load current transport pickle
filepath = os.path.join(current_file_directory, '../../../../data/datamatrix/transport.pickle')
with open(filepath, 'rb') as handle:
    DM_tra = pickle.load(handle)

# Set years range
years_setting = [1989, 2023, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(range(startyear, baseyear+1, 1))
years_fts = list(range(baseyear+2, lastyear+1, step_fts))
years_all = years_ots + years_fts

###############################################################################
###################################### NEW ####################################
###############################################################################

################################################
################### GET DATA ###################
################################################

DM_tra["ots"]["freight_technology-share_new"].units
df = DM_tra["ots"]["freight_technology-share_new"].write_df()
categories2_all = DM_tra["ots"]["freight_technology-share_new"].col_labels["Categories2"]

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

################
##### HDVL #####
################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_tech",
                "variable" : "New vehicle-registrations",
                "categories" : "Light commercial vehicles",
                "sheet_last_row" : "Battery electric vehicles",
                "sub_variables" : ["Gasoline engine","Diesel oil engine","LPG engine",
                                    "Natural gas engine","Battery electric vehicles"],
                "calc_names" : ["HDVL_ICE-gasoline","HDVL_ICE-diesel","HDVL_ICE-gas-lpg",
                                "HDVL_ICE-gas-natural","HDVL_BEV"]}
dm_hdvl = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# substitute 0 with nans (to avoid that zeroes get in the averages)
dm_hdvl.array[dm_hdvl.array==0] = np.nan

# aggregate gas
dm_hdvl.groupby({"HDVL_ICE-gas" : ["HDVL_ICE-gas-lpg","HDVL_ICE-gas-natural"]}, 
                dim='Variables', aggregation = "sum", regex=False, inplace=True)

# make other variables
dm_hdvl.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_hdvl.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_hdvl.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_hdvl.sort("Categories1")

################
##### HDVH #####
################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_tech",
                "variable" : "New vehicle-registrations",
                "sheet_last_row" : "Heavy goods vehicles",
                "sub_variables" : ["Heavy goods vehicles"],
                "calc_names" : ["HDVH"]}
dm_hdvh = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# substitute 0 with nans (to avoid that zeroes get in the averages)
dm_hdvh.array[dm_hdvh.array==0] = np.nan

# use same ratios of HDVL to make the split between types of engines
dm_temp = dm_hdvl.flatten()
dm_temp1 = dm_temp.groupby({"HDVL" : ['HDVL_BEV', 'HDVL_ICE-diesel', 'HDVL_ICE-gas', 'HDVL_ICE-gasoline']}, 
                           dim='Variables', aggregation = "sum", regex=False, inplace=False)
dm_temp.append(dm_temp1,"Variables")
idx = dm_temp.idx
dm_temp.array = dm_temp.array/dm_temp.array[...,idx["HDVL"],np.newaxis]
dm_temp.drop("Variables",["HDVL"])
dm_temp.array = dm_temp.array * dm_hdvh.array
dm_temp.rename_col_regex("HDVL","HDVH","Variables")
dm_hdvh = dm_temp.copy()

# make other variables
dm_hdvh.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_hdvh.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_hdvh.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_hdvh.sort("Categories1")

################
##### HDVM #####
################

# put together
dm_new = dm_hdvl.copy()
dm_new.append(dm_hdvh,"Variables")

# In 2024, light and medium trucks were 13% of all HDV sales, and remaining 77% is HDVH
# source: https://theicct.org/publication/r2z-eu-hdv-market-development-quarterly-jan-dec-2024-feb25/?utm_source=chatgpt.com
dm_temp = dm_new.copy()
# dm_temp.operation("HDVL", '+', 'HDVH', out_col='total', unit="vehicles")
dm_temp.normalise("Variables")
dm_temp.filter({"Variables" : ["HDVH"]},inplace=True)
dm_temp.array = dm_temp.array - 0.77
dm_temp.array[dm_temp.array<0]=0
dm_hdvm = dm_new.filter({"Variables" : ["HDVH"]})
dm_hdvm.array = np.round(dm_hdvm.array * dm_temp.array,0)
dm_hdvm.rename_col("HDVH","HDVM","Variables")

# # check
# df = dm_hdvm.write_df()

# make other variables
categories2_missing = categories2_all.copy()
for cat in dm_hdvm.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_hdvm.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_hdvm.sort("Categories1")

# put together
dm_new.append(dm_hdvm,"Variables")
dm_new.sort("Variables")
dm_new.sort("Country")
dm_new.sort("Years")

# check
df = dm_new.write_df()

####################
##### aviation #####
####################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrAvia_act",
                "variable" : "New aircrafts",
                "sheet_last_row" : "Freight transport",
                "sub_variables" : ["Freight transport"],
                "calc_names" : ["aviation"]}
dm_avi = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# assuming most planes are kerosene, which here I call gasoline
dm_avi.rename_col("aviation","aviation_ICE","Variables")
dm_avi.deepen()

# assuming that all else is nan
categories2_missing = categories2_all.copy()
for cat in dm_avi.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_avi.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_avi.sort("Categories1")

################
##### RAIL #####
################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "New vehicles - total (representative train configuration)",
                "sheet_last_row" : "Electric",
                "categories": "Freight transport",
                "sub_variables" : ["Diesel oil",
                                    "Electric"],
                "calc_names" : ["rail_ICE-diesel","rail_CEV"]}
dm_new_rail = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# make rest of the variables (assuming they are all missing for now)
dm_new_rail.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_new_rail.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_new_rail.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_new_rail.sort("Categories1")

########################
##### PUT TOGETHER #####
########################

dm_new.append(dm_avi,"Variables")
dm_new.append(dm_new_rail,"Variables")

# I do not have data on new for iww and marine, so all missing
dm_new.add(np.nan, col_label="IWW", dummy=True, dim="Variables",unit="vehicles")
dm_new.add(np.nan, col_label="marine", dummy=True, dim="Variables",unit="vehicles")
dm_new.sort("Variables")
dm_new.sort("Country")

# substitute zero values with missing
dm_new.array[dm_new.array==0] = np.nan

###################
##### FIX OTS #####
###################

# flatten
dm_new = dm_new.flatten()

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

# put 2000 values as missing
idx = dm_new.idx
dm_new.array[:,idx[2000],...] = np.nan

# # add missing years
# dm_new.add(np.nan,col_label=list(range(1990,1999+1)), dummy=True, dim='Years')
# dm_new.add(np.nan,col_label=list(range(2022,2023+1)), dummy=True, dim='Years')
# dm_new.sort("Years")

# new variabs list
dict_new = {}

def make_ots(dm, variable, periods_dicts, years_ots = None):
    
    dm_temp = dm.filter({"Variables" : [variable]})
    if periods_dicts["n_adj"] == 1:
        dm_temp = linear_fitting(dm_temp, years_ots, min_t0=0.1,min_tb=0.1)
    if periods_dicts["n_adj"] == 2:
        dm_temp = linear_fitting(dm_temp, list(range(startyear,1999+1)), 
                                 based_on=list(range(2000,periods_dicts["year_end_first_adj"]+1)), 
                                 min_t0=0.1,min_tb=0.1)
        dm_temp = linear_fitting(dm_temp, list(range(2022,2023+1)), 
                                 based_on=list(range(periods_dicts["year_start_second_adj"],2021+1)), 
                                 min_t0=0.1,min_tb=0.1)
    return dm_temp

dict_call = {"HDVH_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "HDVH_ICE-diesel" : {"n_adj" : 1},
             "HDVH_ICE-gas" : {"n_adj" : 1},
             "HDVH_ICE-gasoline": {"n_adj" : 1},
             "HDVL_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "HDVL_ICE-diesel" : {"n_adj" : 1},
             "HDVL_ICE-gas" : {"n_adj" : 1},
             "HDVL_ICE-gasoline" : {"n_adj" : 1},
             "aviation_ICE" : {"n_adj" :1},
             "rail_CEV" : {"n_adj" : 1},
             "rail_ICE-diesel" : {"n_adj" : 1}}

for key in dict_call.keys():
    if len(dict_call[key]) > 1:
        dict_new[key] = make_ots(dm_new, key, dict_call[key])
    else:
        dict_new[key] = make_ots(dm_new, key, dict_call[key], years_ots)

# append
dm_new = dict_new["HDVH_BEV"].copy()
mylist = list(dict_call.keys())
mylist.remove("HDVH_BEV")
for v in mylist:
    dm_new.append(dict_new[v],"Variables")
dm_new.sort("Variables")

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

################################################
##### FIX LAST YEARS FOR ELECTRIC VEHICLES #####
################################################

# put nan foe 2022-2023
idx = dm_new.idx
for v in ["HDVH_BEV","HDVL_BEV"]:
    dm_new.array[idx["EU27"],idx[2022],idx[v]] = np.nan
    dm_new.array[idx["EU27"],idx[2023],idx[v]] = np.nan

# take increase rates in 2020-2021
rates = {}
for v in ["HDVH_BEV","HDVL_BEV"]:
    rates[v] = \
    (dm_new.array[idx["EU27"],idx[2021],idx[v]] - dm_new.array[idx["EU27"],idx[2020],idx[v]])/\
    dm_new.array[idx["EU27"],idx[2020],idx[v]]

# apply rates to obtain 2022 and 2023
for v in ["HDVH_BEV","HDVL_BEV"]:
    dm_new.array[idx["EU27"],idx[2022],idx[v]] = dm_new.array[idx["EU27"],idx[2021],idx[v]] * (1 + rates[v])
    dm_new.array[idx["EU27"],idx[2023],idx[v]] = dm_new.array[idx["EU27"],idx[2022],idx[v]] * (1 + rates[v])

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()


####################
##### MAKE FTS #####
####################

# make function to fill in missing years fts for EU27 with linear fitting
def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
             min_t0=0.1, min_tb=0.1, years_fts = years_fts): # I put minimum to 1 so it does not go to zero
    dm = dm.copy()
    idx = dm.idx
    based_on_yars = list(range(year_start, year_end + 1, 1))
    dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
                             years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
    idx_temp = dm_temp.idx
    if dim == "Variables":
        dm.array[idx[country],:,idx[variable],...] = \
            dm_temp.array[idx_temp[country],:,idx_temp[variable],...]
    if dim == "Categories1":
        dm.array[idx[country],:,:,idx[variable]] = \
            dm_temp.array[idx_temp[country],:,:,idx_temp[variable]]
    if dim == "Categories2":
        dm.array[idx[country],:,:,:,idx[variable]] = \
            dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]]
    if dim == "Categories3":
        dm.array[idx[country],:,:,:,:,idx[variable]] = \
            dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]]
    
    return dm

# make a total
dm_total = dm_new.groupby({"total_HDV" : ['HDVH_BEV', 'HDVH_ICE-diesel', 'HDVH_ICE-gas', 'HDVH_ICE-gasoline',
                                            'HDVL_BEV', 'HDVL_ICE-diesel', 'HDVL_ICE-gas', 'HDVL_ICE-gasoline']}, 
                            dim='Variables', 
                            aggregation = "sum", regex=False, inplace=False)
dm_new.append(dm_total,"Variables")

# add missing years fts
dm_new.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# set default time window for linear trend
baseyear_start = 2000
baseyear_end = 2023

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

# make fts
dm_new = make_fts(dm_new, "total_HDV", baseyear_start, baseyear_end, dim = "Variables")

# get 2050 values for bev and phev
# note: assuming 8% of total new being electric in 2050
# source: https://www.eea.europa.eu/publications/electric-vehicles-and-the-energy/download
idx = dm_new.idx
electric_2050 = dm_new.array[idx["EU27"],idx[2050],idx["total_HDV"]] * 0.08
dm_share = dm_new.filter({"Country" : ["EU27"], "Years" : [2023], "Variables" : ["HDVH_BEV","HDVL_BEV"]})
dm_share.normalise("Variables")
idx_share = dm_share.idx
HDVH_BEV_2050 = dm_share.array[:,:,idx_share["HDVH_BEV"]] * electric_2050
HDVL_BEV_2050 = dm_share.array[:,:,idx_share["HDVL_BEV"]] * electric_2050

# hdvh bev
dm_new.array[idx["EU27"],idx[2050],idx["HDVH_BEV"]] = HDVH_BEV_2050
dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : ["HDVH_BEV"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_new.array[idx["EU27"],:,idx["HDVH_BEV"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["HDVH_BEV"]]

# hdvl bev
dm_new.array[idx["EU27"],idx[2050],idx["HDVL_BEV"]] = HDVL_BEV_2050
dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : ["HDVL_BEV"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_new.array[idx["EU27"],:,idx["HDVL_BEV"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["HDVL_BEV"]]

# rest
dm_new = make_fts(dm_new, "HDVH_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "HDVH_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "HDVH_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "HDVL_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "HDVL_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "HDVL_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "aviation_ICE", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "rail_CEV", baseyear_start, baseyear_end, dim = "Variables")
dm_new = make_fts(dm_new, "rail_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

# deepen
dm_new.drop("Variables","total_HDV")
dm_new.deepen()


####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM_tra["ots"]["freight_technology-share_new"].units

# rename and deepen
for v in dm_new.col_labels["Variables"]:
    dm_new.rename_col(v,"tra_freight_technology-share_new_" + v, "Variables")
dm_new.deepen(based_on="Variables")
dm_new.switch_categories_order("Categories1","Categories2")
dm_new_pc = dm_new.copy()
dm_new_pc.normalise("Categories2")

# make rest of the variables for new pc
categories1_missing = DM_tra["fxa"]["freight_tech"].col_labels["Categories1"].copy()
categories2_missing = categories2_all.copy()
for cat in dm_new_pc.col_labels["Categories1"]: categories1_missing.remove(cat)
for cat in dm_new_pc.col_labels["Categories2"]: categories2_missing.remove(cat)
dm_new_pc.add(np.nan, col_label=categories1_missing, dummy=True, dim="Categories1")
dm_new_pc.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories2")
dm_new_pc.sort("Categories1")
dm_new_pc.sort("Categories2")
dm_new_pc_final = dm_new_pc.copy()

# make rest of the variables for new
categories1_missing = DM_tra["fxa"]["freight_tech"].col_labels["Categories1"].copy()
categories2_missing = categories2_all.copy()
for cat in dm_new.col_labels["Categories1"]: categories1_missing.remove(cat)
for cat in dm_new.col_labels["Categories2"]: categories2_missing.remove(cat)
dm_new.add(np.nan, col_label=categories1_missing, dummy=True, dim="Categories1")
dm_new.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories2")
dm_new.sort("Categories1")
dm_new.sort("Categories2")
dm_new.units["tra_freight_technology-share_new"] = "number"
dm_new_final = dm_new.copy()

# check
# dm_new.flatten().flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()

# clean
del baseyear_end, baseyear_start, cat, categories2_all, categories2_missing, df, \
    dict_call, dict_iso2, dict_iso2_jrc, dict_new, dm_avi, dm_new_rail, dm_hdvh, \
    dm_hdvl, dm_hdvm, dm_share, dm_temp, dm_temp1, dm_total, electric_2050, \
    handle, HDVH_BEV_2050, HDVL_BEV_2050, idx, idx_temp, idx_share, key, mylist, rates, v, dm_new, dm_new_pc
    
################
##### SAVE #####
################

# split between ots and fts
DM_new = {"ots": {"freight_technology-share_new" : []}, "fts": {"freight_technology-share_new" : dict()}}
DM_new["ots"]["freight_technology-share_new"] = dm_new_pc_final.filter({"Years" : years_ots})
DM_new["ots"]["freight_technology-share_new"].drop("Years",startyear)
for i in range(1,4+1):
    DM_new["fts"]["freight_technology-share_new"][i] = dm_new_pc_final.filter({"Years" : years_fts})

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_freight_technology-share_new.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_new, handle, protocol=pickle.HIGHEST_PROTOCOL)








