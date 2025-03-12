
# packages
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/transport/EU/python/transport_fxa_passenger_tech.py"

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
#################################### FLEET ####################################
###############################################################################

################################################
################### GET DATA ###################
################################################

DM_tra["fxa"]["passenger_tech"].units
categories2_all = DM_tra["fxa"]["passenger_tech"].col_labels["Categories2"]

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

##############
##### 2W #####
##############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Stock of vehicles - total (vehicles)",
                "sheet_last_row" : "Powered two-wheelers",
                "sub_variables" : ["Powered two-wheelers"],
                "calc_names" : ["2W"]}
dm_fleet_2w = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# make other variables
# assumption: 2w are mostly ICE-gasoline, so the energy efficiency we have will be assigned
# to 2W_ICE-gasoline, and the rest will be missing values for now
dm_fleet_2w.rename_col("2W","2W_ICE-gasoline","Variables")
dm_fleet_2w.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_fleet_2w.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_fleet_2w.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_fleet_2w.sort("Categories1")


###############
##### LDV #####
###############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Stock of vehicles - total (vehicles)",
                "sheet_last_row" : "Battery electric vehicles",
                "categories" : "Passenger cars",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Plug-in hybrid electric",
                                    "Battery electric vehicles"],
                "calc_names" : ["LDV_ICE-gasoline","LDV_ICE-diesel","LDV_gas-lpg",
                                "LDV_gas-natural","LDV_PHEV","LDV_BEV"]}
dm_fleet_ldv = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_fleet_ldv.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_fleet_ldv.groupby(mapping_calc, dim='Categories1', aggregation = "sum", regex=False, inplace=True)

# make PHEV diesel and PHEV gasoline
# assumption: they are the same proportion of ldv diesel and ldv gasoline
dm_temp = dm_fleet_ldv.filter({"Categories1" : ["PHEV"]})
dm_temp.rename_col("PHEV","PHEV-gasoline","Categories1")
dm_temp.add(dm_temp.array, col_label="PHEV-diesel", dim="Categories1")
dm_temp.sort("Categories1")
dm_temp1 = dm_fleet_ldv.filter({"Categories1" : ['ICE-diesel', 'ICE-gasoline']})
dm_temp1.normalise("Categories1")
dm_temp.array = dm_temp.array * dm_temp1.array
dm_fleet_ldv.drop("Categories1","PHEV")
dm_fleet_ldv.append(dm_temp,"Categories1")
dm_fleet_ldv.sort("Categories1")

# make other variables
# assumption: for now, rest is assumed to be missing
categories2_missing = categories2_all.copy()
for cat in dm_fleet_ldv.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_fleet_ldv.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_fleet_ldv.sort("Categories1")

#################
##### BUSES #####
#################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "Stock of vehicles - total (vehicles)",
                "categories" : "Motor coaches, buses and trolley buses",
                "sheet_last_row" : "Battery electric vehicles",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Battery electric vehicles"],
                "calc_names" : ["bus_ICE-gasoline","bus_ICE-diesel","bus_gas-lpg",
                                "bus_gas-natural","bus_BEV"]}
dm_fleet_bus = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_fleet_bus.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_fleet_bus.groupby(mapping_calc, dim='Categories1', aggregation = "mean", regex=False, inplace=True)

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_fleet_bus.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_fleet_bus.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_fleet_bus.sort("Categories1")

################
##### RAIL #####
################

# get data
# note: I assume that all high speed passenger trains are electric, and I'll take an average
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "Stock of vehicles - total (representative train configuration)",
                "sheet_last_row" : "High speed passenger trains",                
                "sub_variables" : ["Metro and tram, urban light rail",
                                    "Diesel oil",
                                    "Electric",
                                    "High speed passenger trains"],
                "calc_names" : ["metrotram_mt","train-conv_ICE-diesel","train-conv_CEV","train-hs_CEV"]}
dm_fleet_rail = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# aggregate trains and deepen
mapping_calc = {'rail_CEV': ['train-conv_CEV', 'train-hs_CEV'],
                'rail_ICE-diesel' : ["train-conv_ICE-diesel"]}
dm_fleet_rail.groupby(mapping_calc, dim='Variables', aggregation = "mean", regex=False, inplace=True)
dm_fleet_rail.deepen()

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_fleet_rail.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_fleet_rail.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_fleet_rail.sort("Categories1")

# fix unit
dm_fleet_rail.units["metrotram"] = "vehicles"
dm_fleet_rail.units["rail"] = "vehicles"

########################
##### PUT TOGETHER #####
########################

dm_fleet = dm_fleet_2w.copy()
dm_fleet.append(dm_fleet_ldv,"Variables")
dm_fleet.append(dm_fleet_bus,"Variables")
dm_fleet.append(dm_fleet_rail,"Variables")
dm_fleet.sort("Variables")
dm_fleet.sort("Country")

# check
# dm_fleet.flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()

# there is a problem with fleet LDV ice gasoline before 2014. Seeing
# that also in Eurostat it's missing, I assume there is a problem with JRC data
# and I put it missing
dm_fleet = dm_fleet.flatten()
idx = dm_fleet.idx
years_fix = list(range(2000,2013+1))
for y in years_fix:
    dm_fleet.array[:,idx[y],idx["LDV_ICE-gasoline"]] = np.nan
dm_fleet.deepen()

# fix units
for v in dm_fleet.col_labels["Variables"]:
    dm_fleet.units[v] = "number"

# check
# dm_fleet.flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()


###################
##### FIX OTS #####
###################

# flatten
dm_fleet = dm_fleet.flatten()

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

dict_call = {"2W_ICE-gasoline" : {"n_adj" : 1},
             "LDV_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "LDV_ICE-diesel" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "LDV_ICE-gas" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "LDV_ICE-gasoline" : {"n_adj" : 1},
             "LDV_PHEV-diesel" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "LDV_PHEV-gasoline" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "bus_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "bus_ICE-diesel" : {"n_adj" : 1},
             "bus_ICE-gas" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "bus_ICE-gasoline" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "metrotram_mt" :  {"n_adj" : 1},
             "rail_CEV" :  {"n_adj" : 1},
             "rail_ICE-diesel" :  {"n_adj" : 1}}

for key in dict_call.keys():
    if len(dict_call[key]) > 1:
        dict_new[key] = make_ots(dm_fleet, key, dict_call[key])
    else:
        dict_new[key] = make_ots(dm_fleet, key, dict_call[key], years_ots)

# append
dm_fleet = dict_new["2W_ICE-gasoline"].copy()
mylist = list(dict_call.keys())
mylist.remove("2W_ICE-gasoline")
for v in mylist:
    dm_fleet.append(dict_new[v],"Variables")
dm_fleet.sort("Variables")

# # if 1990 value is 0.1, put value of 1991
# dm_fleet_1990 = dm_fleet.filter({"Years" : [1990]})
# dm_fleet_1991 = dm_fleet.filter({"Years" : [1991]})
# dm_fleet_1990.array[dm_fleet_1990.array == 0.1] = dm_fleet_1991.array[dm_fleet_1990.array == 0.1]
# dm_fleet.drop("Years",[1990])
# dm_fleet.append(dm_fleet_1990, "Years")
# dm_fleet.sort("Years")

# check
# dm_fleet.filter({"Country" : ["EU27"]}).datamatrix_plot()

################################################
##### FIX LAST YEARS FOR ELECTRIC VEHICLES #####
################################################

# put nan foe 2022-2023
idx = dm_fleet.idx
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    dm_fleet.array[idx["EU27"],idx[2022],idx[v]] = np.nan
    dm_fleet.array[idx["EU27"],idx[2023],idx[v]] = np.nan

# take increase rates in 2020-2021
rates = {}
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    rates[v] = \
    (dm_fleet.array[idx["EU27"],idx[2021],idx[v]] - dm_fleet.array[idx["EU27"],idx[2020],idx[v]])/\
    dm_fleet.array[idx["EU27"],idx[2020],idx[v]]

# apply rates to obtain 2022 and 2023
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    dm_fleet.array[idx["EU27"],idx[2022],idx[v]] = dm_fleet.array[idx["EU27"],idx[2021],idx[v]] * (1 + rates[v])
    dm_fleet.array[idx["EU27"],idx[2023],idx[v]] = dm_fleet.array[idx["EU27"],idx[2022],idx[v]] * (1 + rates[v])

# check
# dm_fleet.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM_tra["fxa"]["passenger_tech"].units

# get it in shares
dm_fleet.drop("Variables","total")

# rename and deepen
for v in dm_fleet.col_labels["Variables"]:
    dm_fleet.rename_col(v,"tra_passenger_technology-share_fleet_" + v, "Variables")
dm_fleet.deepen_twice()
dm_fleet_final = dm_fleet.copy()

# check
# dm_fleet_pc.flatten().flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()

# clean
del cat, categories2_all, categories2_missing, dict_call, dict_iso2, dict_iso2_jrc, \
    dict_new, dm_fleet_2w, dm_fleet_bus, dm_fleet_ldv, dm_fleet_rail, dm_temp, \
    dm_temp1, filepath, handle, idx, key, v, y, years_fix, mapping_calc, mylist, \
    dm_fleet

###############################################################################
############################### VEHICLE EFFICIENCY ############################
###############################################################################

################################################
################### GET DATA ###################
################################################

DM_tra["fxa"]["passenger_tech"].units
DM_tra["fxa"]["passenger_tech"].write_df().columns
categories2_all = DM_tra["fxa"]["passenger_tech"].col_labels["Categories2"]

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

# note on data in JRC
# On efficiency of total stock:
# Vehicle-efficiency - effective (kgoe/100 km) = Test cycle efficiency of total stock (kgoe/100 km) * Discrepancy between effective and test cycle efficiencies (ratio)
# The discrepancy factors have been created to match the data of the energy balances
# On efficiency of new:
# Test cycle efficiency of new vehicles (kgoe/100 km)

##############
##### 2W #####
##############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_ene",
                "variable" : "Vehicle-efficiency - effective (kgoe/100 km)",
                "sheet_last_row" : "Powered two-wheelers",
                "sub_variables" : ["Powered two-wheelers"],
                "calc_names" : ["2W"]}
dm_eneff_2w = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# make other variables
# assumption: 2w are mostly ICE-gasoline, so the energy efficiency we have will be assigned
# to 2W_ICE-gasoline, and the rest will be missing values for now
dm_eneff_2w.rename_col("2W","2W_ICE-gasoline","Variables")
dm_eneff_2w.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_eneff_2w.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_eneff_2w.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_eneff_2w.sort("Categories1")


###############
##### LDV #####
###############


# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_ene",
                "variable" : "Vehicle-efficiency - effective (kgoe/100 km)",
                "sheet_last_row" : "Battery electric vehicles",
                "categories" : "Passenger cars",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Plug-in hybrid electric",
                                    "Battery electric vehicles"],
                "calc_names" : ["LDV_ICE-gasoline","LDV_ICE-diesel","LDV_gas-lpg",
                                "LDV_gas-natural","LDV_PHEV","LDV_BEV"]}
dm_eneff_ldv = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_eneff_ldv.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_eneff_ldv.groupby(mapping_calc, dim='Categories1', aggregation = "mean", regex=False, inplace=True)

# make PHEV diesel and PHEV gasoline
# assumption: they have the same efficiency
dm_temp = dm_eneff_ldv.filter({"Categories1" : ["PHEV"]})
dm_temp1 = dm_temp.copy()
dm_temp1.rename_col("PHEV","PHEV-gasoline","Categories1")
dm_temp1.append(dm_temp,"Categories1")
dm_temp1.rename_col("PHEV","PHEV-diesel","Categories1")
dm_eneff_ldv.drop("Categories1","PHEV")
dm_eneff_ldv.append(dm_temp1,"Categories1")
dm_eneff_ldv.sort("Categories1")

# make other variables
# TODO: FCEV energy efficiency can be same of Switzerland, to be added at the end, for now missing
# assumption: for now, rest is assumed to be missing
categories2_missing = categories2_all.copy()
for cat in dm_eneff_ldv.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_eneff_ldv.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_eneff_ldv.sort("Categories1")


#################
##### BUSES #####
#################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_ene",
                "variable" : "Vehicle-efficiency - effective (kgoe/100 km)",
                "sheet_last_row" : "Battery electric vehicles",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Battery electric vehicles"],
                "calc_names" : ["bus_ICE-gasoline","bus_ICE-diesel","bus_gas-lpg",
                                "bus_gas-natural","bus_BEV"],
                "categories" : "Motor coaches, buses and trolley buses"}
dm_eneff_bus = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_eneff_bus.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_eneff_bus.groupby(mapping_calc, dim='Categories1', aggregation = "mean", regex=False, inplace=True)

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_eneff_bus.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_eneff_bus.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_eneff_bus.sort("Categories1")

################
##### RAIL #####
################

# get data
# note: I assume that all high speed passenger trains are electric, and I'll take an average
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_ene",
                "variable" : "Vehicle-efficiency (kgoe/100 km)",
                "sheet_last_row" : "High speed passenger trains",                
                "sub_variables" : ["Metro and tram, urban light rail",
                                    "Diesel oil",
                                    "Electric",
                                    "High speed passenger trains"],
                "calc_names" : ["metrotram_mt","train-conv_ICE-diesel","train-conv_CEV","train-hs_CEV"]}
dm_eneff_rail = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# aggregate trains and deepen
mapping_calc = {'rail_CEV': ['train-conv_CEV', 'train-hs_CEV'],
                'rail_ICE-diesel' : ["train-conv_ICE-diesel"]}
dm_eneff_rail.groupby(mapping_calc, dim='Variables', aggregation = "mean", regex=False, inplace=True)
dm_eneff_rail.deepen()

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_eneff_rail.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_eneff_rail.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_eneff_rail.sort("Categories1")

########################
##### PUT TOGETHER #####
########################

dm_eneff = dm_eneff_2w.copy()
dm_eneff.append(dm_eneff_ldv,"Variables")
dm_eneff.append(dm_eneff_bus,"Variables")
dm_eneff.append(dm_eneff_rail,"Variables")
dm_eneff.sort("Variables")
dm_eneff.sort("Country")

# substitute zero values with missing
dm_eneff.array[dm_eneff.array==0] = np.nan

###################
##### FIX OTS #####
###################

# do linear fitting of each variable with wathever is available
# note: bus_ICE-diesel: until before 2000 until 2012, after 2021 after 2012
dm_eneff_bus_icedie = dm_eneff.filter({"Variables" : ["bus"],"Categories1" : ["ICE-diesel"]})
dm_eneff = linear_fitting(dm_eneff, years_ots, min_t0=0,min_tb=0)
dm_eneff_bus_icedie = linear_fitting(dm_eneff_bus_icedie, list(range(startyear,1999+1)),based_on=list(range(2000,2012+1)), min_t0=0.1,min_tb=0.1)
dm_eneff_bus_icedie = linear_fitting(dm_eneff_bus_icedie, list(range(2022,2023+1)),based_on=list(range(2012,2020+1)), min_t0=0.1,min_tb=0.1)
dm_eneff = dm_eneff.flatten()
dm_eneff.drop("Variables","bus_ICE-diesel")
dm_eneff.append(dm_eneff_bus_icedie.flatten(),"Variables")
dm_eneff.deepen()

# check
# dm_eneff.filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_eneff.write_df()
# df.columns


####################
##### MAKE FTS #####
####################

# TODO: it seems that for FTS is all nan in pre processing, check with Paola

# =============================================================================
# # make function to fill in missing years fts for EU27 with linear fitting
# def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
#              min_t0=0.1, min_tb=0.1, years_fts = years_fts): # I put minimum to 1 so it does not go to zero
#     dm = dm.copy()
#     idx = dm.idx
#     based_on_yars = list(range(year_start, year_end + 1, 1))
#     dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
#                              years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
#     idx_temp = dm_temp.idx
#     if dim == "Variables":
#         dm.array[idx[country],:,idx[variable],...] = \
#             dm_temp.array[idx_temp[country],:,idx_temp[variable],...]
#     if dim == "Categories1":
#         dm.array[idx[country],:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,idx_temp[variable]]
#     if dim == "Categories2":
#         dm.array[idx[country],:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]]
#     if dim == "Categories3":
#         dm.array[idx[country],:,:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]]
#     
#     return dm
# 
# 
# # set default time window for linear trend
# baseyear_start = 2000
# baseyear_end = 2019
# 
# # flatten
# dm_eneff = dm_eneff.flatten()
# 
# # check
# # dm_eneff.filter({"Country" : ["EU27"]}).datamatrix_plot()
# 
# # # try fts
# # product = "LDV_BEV"
# # (make_fts(dm_eneff, product, baseyear_start, baseyear_end, dim = "Variables").
# #  datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : [product]}))
# 
# # make fts
# dm_eneff = make_fts(dm_eneff, "2W_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_BEV", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_PHEV-diesel", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "LDV_PHEV-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "bus_BEV", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "bus_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "bus_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "bus_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "metrotram_mt", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "rail_CEV", baseyear_start, baseyear_end, dim = "Variables")
# dm_eneff = make_fts(dm_eneff, "rail_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
# 
# # check
# # dm_eneff.filter({"Country" : ["EU27"]}).datamatrix_plot()
# =============================================================================

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM_tra["fxa"]["passenger_tech"].units

# rename and deepen
for v in dm_eneff.col_labels["Variables"]:
    dm_eneff.rename_col(v,"tra_passenger_veh-efficiency_fleet_" + v, "Variables")
dm_eneff.deepen(based_on="Variables")
dm_eneff.switch_categories_order("Categories1","Categories2")

# get it in MJ over km
dm_eneff.change_unit("tra_passenger_veh-efficiency_fleet", 41.868, "kgoe/100 km", "MJ/100 km")
dm_eneff.change_unit("tra_passenger_veh-efficiency_fleet", 1e-2, "MJ/100 km", "MJ/km")
dm_eneff_final = dm_eneff.copy()

# clean
del cat, categories2_all, categories2_missing, dict_iso2, dict_iso2_jrc, \
    dm_eneff_2w, dm_eneff_bus, dm_eneff_ldv, dm_eneff_rail, dm_temp, \
    dm_temp1, mapping_calc, dm_eneff_bus_icedie, \
    v, dm_eneff

###############################################################################
################################## NEW VEHICLES ###############################
###############################################################################

################################################
################### GET DATA ###################
################################################

DM_tra["fxa"]["passenger_tech"].units
categories2_all = DM_tra["fxa"]["passenger_tech"].col_labels["Categories2"]

# get iso codes
dict_iso2 = eurostat_iso2_dict()
dict_iso2.pop('CH')  # Remove Switzerland
dict_iso2_jrc = jrc_iso2_dict()

##############
##### 2W #####
##############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "New vehicle-registrations",
                "sheet_last_row" : "Powered two-wheelers",
                "sub_variables" : ["Powered two-wheelers"],
                "calc_names" : ["2W"]}
dm_new_2w = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# make other variables
# assumption: 2w are mostly ICE-gasoline, so the energy efficiency we have will be assigned
# to 2W_ICE-gasoline, and the rest will be missing values for now
dm_new_2w.rename_col("2W","2W_ICE-gasoline","Variables")
dm_new_2w.deepen()
categories2_missing = categories2_all.copy()
for cat in dm_new_2w.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_new_2w.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_new_2w.sort("Categories1")


###############
##### LDV #####
###############

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "New vehicle-registrations",
                "sheet_last_row" : "Battery electric vehicles",
                "categories" : "Passenger cars",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Plug-in hybrid electric",
                                    "Battery electric vehicles"],
                "calc_names" : ["LDV_ICE-gasoline","LDV_ICE-diesel","LDV_gas-lpg",
                                "LDV_gas-natural","LDV_PHEV","LDV_BEV"]}
dm_new_ldv = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_new_ldv.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_new_ldv.groupby(mapping_calc, dim='Categories1', aggregation = "sum", regex=False, inplace=True)

# make PHEV diesel and PHEV gasoline
# assumption: they are the same proportion of ldv diesel and ldv gasoline
dm_temp = dm_new_ldv.filter({"Categories1" : ["PHEV"]})
dm_temp.rename_col("PHEV","PHEV-gasoline","Categories1")
dm_temp.add(dm_temp.array, col_label="PHEV-diesel", dim="Categories1")
dm_temp.sort("Categories1")
dm_temp1 = dm_new_ldv.filter({"Categories1" : ['ICE-diesel', 'ICE-gasoline']})
dm_temp1.normalise("Categories1")
dm_temp.array = dm_temp.array * dm_temp1.array
dm_new_ldv.drop("Categories1","PHEV")
dm_new_ldv.append(dm_temp,"Categories1")
dm_new_ldv.sort("Categories1")

# make other variables
# assumption: for now, rest is assumed to be missing
categories2_missing = categories2_all.copy()
for cat in dm_new_ldv.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_new_ldv.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_new_ldv.sort("Categories1")

#################
##### BUSES #####
#################

# get data
dict_extract = {"database" : "Transport",
                "sheet" : "TrRoad_act",
                "variable" : "New vehicle-registrations",
                "categories" : "Motor coaches, buses and trolley buses",
                "sheet_last_row" : "Battery electric vehicles",
                "sub_variables" : ["Gasoline engine",
                                    "Diesel oil engine",
                                    "LPG engine", "Natural gas engine", 
                                    "Battery electric vehicles"],
                "calc_names" : ["bus_ICE-gasoline","bus_ICE-diesel","bus_gas-lpg",
                                "bus_gas-natural","bus_BEV"]}
dm_new_bus = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# deepen and sum gas
dm_new_bus.deepen()
mapping_calc = {'ICE-gas': ['gas-lpg', 'gas-natural']}
dm_new_bus.groupby(mapping_calc, dim='Categories1', aggregation = "mean", regex=False, inplace=True)

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_new_bus.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_new_bus.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_new_bus.sort("Categories1")

################
##### RAIL #####
################

# get data
# note: I assume that all high speed passenger trains are electric, and I'll take an average
dict_extract = {"database" : "Transport",
                "sheet" : "TrRail_act",
                "variable" : "New vehicles - total (representative train configuration)",
                "sheet_last_row" : "High speed passenger trains",                
                "sub_variables" : ["Metro and tram, urban light rail",
                                    "Diesel oil",
                                    "Electric",
                                    "High speed passenger trains"],
                "calc_names" : ["metrotram_mt","train-conv_ICE-diesel","train-conv_CEV","train-hs_CEV"]}
dm_new_rail = get_jrc_data(dict_extract, dict_iso2_jrc, current_file_directory)

# aggregate trains and deepen
mapping_calc = {'rail_CEV': ['train-conv_CEV', 'train-hs_CEV'],
                'rail_ICE-diesel' : ["train-conv_ICE-diesel"]}
dm_new_rail.groupby(mapping_calc, dim='Variables', aggregation = "mean", regex=False, inplace=True)
dm_new_rail.deepen()

# make rest of the variables (assuming they are all missing for now)
categories2_missing = categories2_all.copy()
for cat in dm_new_rail.col_labels["Categories1"]: categories2_missing.remove(cat)
dm_new_rail.add(np.nan, col_label=categories2_missing, dummy=True, dim="Categories1")
dm_new_rail.sort("Categories1")

# fix unit
dm_new_rail.units["metrotram"] = "vehicles"
dm_new_rail.units["rail"] = "vehicles"

########################
##### PUT TOGETHER #####
########################

dm_new = dm_new_2w.copy()
dm_new.append(dm_new_ldv,"Variables")
dm_new.append(dm_new_bus,"Variables")
dm_new.append(dm_new_rail,"Variables")
dm_new.sort("Variables")
dm_new.sort("Country")

# check
# dm_new.flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()

# there is a problem with new LDV ice gasoline before 2014. Seeing
# that also in Eurostat it's missing, I assume there is a problem with JRC data
# and I put it missing
dm_new = dm_new.flatten()
idx = dm_new.idx
years_fix = list(range(2000,2013+1))
for y in years_fix:
    dm_new.array[:,idx[y],idx["LDV_ICE-gasoline"]] = np.nan

# put LDV_ICE-gas 2000 as missing
dm_new.array[:,idx[2000],idx["LDV_ICE-gas"]] = np.nan

# deepen
dm_new.deepen()

# check
# dm_new.flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()


###################
##### FIX OTS #####
###################

# flatten
dm_new = dm_new.flatten()

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

dict_call = {"2W_ICE-gasoline" : {"n_adj" : 2, "year_end_first_adj" : 2007, "year_start_second_adj" : 2021},
             "LDV_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "LDV_ICE-diesel" : {"n_adj" : 2, "year_end_first_adj" : 2006, "year_start_second_adj" : 2017},
             "LDV_ICE-gas" : {"n_adj" : 2, "year_end_first_adj" : 2003, "year_start_second_adj" : 2020},
             "LDV_ICE-gasoline" : {"n_adj" : 1},
             "LDV_PHEV-diesel" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "LDV_PHEV-gasoline" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "bus_BEV" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2021},
             "bus_ICE-diesel" : {"n_adj" : 2, "year_end_first_adj" : 2008, "year_start_second_adj" : 2020},
             "bus_ICE-gas" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "bus_ICE-gasoline" : {"n_adj" : 2, "year_end_first_adj" : 2010, "year_start_second_adj" : 2020},
             "metrotram_mt" :  {"n_adj" : 1},
             "rail_CEV" :  {"n_adj" : 2, "year_end_first_adj" : 2000, "year_start_second_adj" : 2005},
             "rail_ICE-diesel" :  {"n_adj" : 1}}

for key in dict_call.keys():
    if len(dict_call[key]) > 1:
        dict_new[key] = make_ots(dm_new, key, dict_call[key])
    else:
        dict_new[key] = make_ots(dm_new, key, dict_call[key], years_ots)

# append
dm_new = dict_new["2W_ICE-gasoline"].copy()
mylist = list(dict_call.keys())
mylist.remove("2W_ICE-gasoline")
for v in mylist:
    dm_new.append(dict_new[v],"Variables")
dm_new.sort("Variables")

# # if 1990 value is 0.1, put value of 1991
# dm_new_1990 = dm_new.filter({"Years" : [1990]})
# dm_new_1991 = dm_new.filter({"Years" : [1991]})
# dm_new_1990.array[dm_new_1990.array == 0.1] = dm_new_1991.array[dm_new_1990.array == 0.1]
# dm_new.drop("Years",[1990])
# dm_new.append(dm_new_1990, "Years")
# dm_new.sort("Years")

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

################################################
##### FIX LAST YEARS FOR ELECTRIC VEHICLES #####
################################################

# put nan foe 2022-2023
idx = dm_new.idx
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    dm_new.array[idx["EU27"],idx[2022],idx[v]] = np.nan
    dm_new.array[idx["EU27"],idx[2023],idx[v]] = np.nan

# take increase rates in 2020-2021
rates = {}
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    rates[v] = \
    (dm_new.array[idx["EU27"],idx[2021],idx[v]] - dm_new.array[idx["EU27"],idx[2020],idx[v]])/\
    dm_new.array[idx["EU27"],idx[2020],idx[v]]

# apply rates to obtain 2022 and 2023
for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
    dm_new.array[idx["EU27"],idx[2022],idx[v]] = dm_new.array[idx["EU27"],idx[2021],idx[v]] * (1 + rates[v])
    dm_new.array[idx["EU27"],idx[2023],idx[v]] = dm_new.array[idx["EU27"],idx[2022],idx[v]] * (1 + rates[v])

# check
# dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()

####################
##### MAKE FTS #####
####################

# TODO: it seems that for FTS is all nan in pre processing, check with Paola

# =============================================================================
# # make function to fill in missing years fts for EU27 with linear fitting
# def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
#              min_t0=0.1, min_tb=0.1, years_fts = years_fts): # I put minimum to 1 so it does not go to zero
#     dm = dm.copy()
#     idx = dm.idx
#     based_on_yars = list(range(year_start, year_end + 1, 1))
#     dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
#                              years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
#     idx_temp = dm_temp.idx
#     if dim == "Variables":
#         dm.array[idx[country],:,idx[variable],...] = \
#             dm_temp.array[idx_temp[country],:,idx_temp[variable],...]
#     if dim == "Categories1":
#         dm.array[idx[country],:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,idx_temp[variable]]
#     if dim == "Categories2":
#         dm.array[idx[country],:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]]
#     if dim == "Categories3":
#         dm.array[idx[country],:,:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]]
#     
#     return dm
# 
# # # make a total
# # dm_total = dm_new.groupby({"total" : dm_new.col_labels["Variables"]}, dim='Variables', 
# #                             aggregation = "sum", regex=False, inplace=False)
# # dm_new.append(dm_total,"Variables")
# 
# # get fleet
# dm_fleet = dm_fleet_final.copy()
# dm_fleet = dm_fleet.flatten().flatten()
# dm_fleet.rename_col_regex("tra_passenger_technology-share_fleet_","","Variables")
# 
# # check
# # dm_fleet.filter({"Country" : ["EU27"]}).datamatrix_plot()
# 
# # add missing years fts
# dm_new.add(np.nan, col_label=years_fts, dummy=True, dim='Years')
# 
# # drop 2022-2023 for the electric vehicles (to avoid a flat line)
# idx = dm_new.idx
# for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
#     dm_new.array[idx["EU27"],idx[2022],idx[v]] = np.nan
#     dm_new.array[idx["EU27"],idx[2023],idx[v]] = np.nan
# 
# # set default time window for linear trend
# baseyear_start = 2000
# baseyear_end = 2023
# 
# # 2W
# dm_new = make_fts(dm_new, "2W_ICE-gasoline", 2012, baseyear_end, dim = "Variables")
# 
# # for electric vehicles, get % change of fleet over 2023-2050 and apply it to new vehicles
# 
# # bev
# idx = dm_fleet.idx
# product = "LDV_BEV"
# rate_increase = (dm_fleet.array[idx["EU27"],idx[2050],idx[product]] - 
#                  dm_fleet.array[idx["EU27"],idx[2021],idx[product]])/\
#     dm_fleet.array[idx["EU27"],idx[2021],idx[product]]
# idx = dm_new.idx
# value_2050 = round(dm_new.array[idx["EU27"],idx[2021],idx[product]] * rate_increase,0)
# dm_new.array[idx["EU27"],idx[2050],idx[product]] = value_2050
# dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : [product]}), years_ots + years_fts)
# idx_temp = dm_temp.idx
# dm_new.array[idx["EU27"],:,idx[product]] = dm_temp.array[idx_temp["EU27"],:,idx_temp[product]]
# 
# # ice
# dm_new = make_fts(dm_new, "LDV_ICE-diesel", 2017, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "LDV_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "LDV_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# 
# # LDV_PHEV-diesel
# idx = dm_fleet.idx
# product = "LDV_PHEV-diesel"
# rate_increase = (dm_fleet.array[idx["EU27"],idx[2050],idx[product]] - 
#                  dm_fleet.array[idx["EU27"],idx[2021],idx[product]])/\
#     dm_fleet.array[idx["EU27"],idx[2021],idx[product]]
# idx = dm_new.idx
# value_2050 = round(dm_new.array[idx["EU27"],idx[2021],idx[product]] * rate_increase,0)
# dm_new.array[idx["EU27"],idx[2050],idx[product]] = value_2050
# dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : [product]}), years_ots + years_fts)
# idx_temp = dm_temp.idx
# dm_new.array[idx["EU27"],:,idx[product]] = dm_temp.array[idx_temp["EU27"],:,idx_temp[product]]
# 
# # LDV_PHEV-gasoline
# idx = dm_fleet.idx
# product = "LDV_PHEV-gasoline"
# rate_increase = (dm_fleet.array[idx["EU27"],idx[2050],idx[product]] - 
#                  dm_fleet.array[idx["EU27"],idx[2021],idx[product]])/\
#     dm_fleet.array[idx["EU27"],idx[2021],idx[product]]
# idx = dm_new.idx
# value_2050 = round(dm_new.array[idx["EU27"],idx[2021],idx[product]] * rate_increase,0)
# dm_new.array[idx["EU27"],idx[2050],idx[product]] = value_2050
# dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : [product]}), years_ots + years_fts)
# idx_temp = dm_temp.idx
# dm_new.array[idx["EU27"],:,idx[product]] = dm_temp.array[idx_temp["EU27"],:,idx_temp[product]]
# 
# # bus_BEV
# idx = dm_fleet.idx
# product = "bus_BEV"
# rate_increase = (dm_fleet.array[idx["EU27"],idx[2050],idx[product]] - 
#                  dm_fleet.array[idx["EU27"],idx[2021],idx[product]])/\
#     dm_fleet.array[idx["EU27"],idx[2021],idx[product]]
# idx = dm_new.idx
# value_2050 = round(dm_new.array[idx["EU27"],idx[2021],idx[product]] * rate_increase,0)
# dm_new.array[idx["EU27"],idx[2050],idx[product]] = value_2050
# dm_temp = linear_fitting(dm_new.filter({"Country" : ["EU27"], "Variables" : [product]}), years_ots + years_fts)
# idx_temp = dm_temp.idx
# dm_new.array[idx["EU27"],:,idx[product]] = dm_temp.array[idx_temp["EU27"],:,idx_temp[product]]
# 
# # rest
# dm_new = make_fts(dm_new, "bus_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "bus_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "bus_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "metrotram_mt", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "rail_CEV", baseyear_start, baseyear_end, dim = "Variables")
# dm_new = make_fts(dm_new, "rail_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
# 
# # check
# # dm_new.filter({"Country" : ["EU27"]}).datamatrix_plot()
# =============================================================================

####################################
##### MAKE AS FINAL DATAMATRIX #####
####################################

DM_tra["fxa"]["passenger_tech"].units

# rename and deepen
for v in dm_new.col_labels["Variables"]:
    dm_new.rename_col(v,"tra_passenger_new-vehicles_" + v, "Variables")
dm_new.deepen_twice()
dm_new_final = dm_new.copy()

# check
# dm_new.flatten().flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()

# clean
del cat, categories2_all, categories2_missing, dict_iso2, dict_call, dict_iso2_jrc, \
    dict_new, dm_new_2w, dm_new_bus, dm_new_ldv, dm_new_rail, dm_temp, \
    dm_temp1, idx, key, v, y, years_fix, mapping_calc, mylist, \
    dm_new

###############################################################################
##################################### WASTE ###################################
###############################################################################

##################################################
################## PUT TOGETHER ##################
##################################################

dm_tech = dm_fleet_final.copy()
dm_tech.append(dm_eneff_final, "Variables")
dm_tech.append(dm_new_final, "Variables")

###############################################
################## GET WASTE ##################
###############################################

# check
# dm_tech.flatten().flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_tech.write_df()
# idx = dm_tech.idx
# dm_tech.array[idx["EU27"],idx[2021],idx['tra_passenger_technology-share_fleet'],idx["LDV"],idx["BEV"]] - \
#     dm_tech.array[idx["EU27"],idx[2020],idx['tra_passenger_technology-share_fleet'],idx["LDV"],idx["BEV"]]
# dm_tech.array[idx["EU27"],idx[2021],idx['tra_passenger_new-vehicles'],idx["LDV"],idx["BEV"]]

def compute_renewal_rate_and_adjust(dm, var_names, max_rr):
    """
    It computes the renewal rate and it adjusts the new-vehicles before 2005, where the fleet split was not known
    """
    # Extract variable names
    s_col = var_names['stock']
    new_col = var_names['new']
    waste_col = var_names['waste']
    rr_col = var_names['renewal-rate']

    stock_unit = dm.units[s_col]

    # COMPUTE RENEWAL-RATE
    # Lag stock
    dm.lag_variable(pattern=s_col, shift=1, subfix='_tm1')
    # waste(t) = fleet(t-1) - fleet(t) + new-veh(t)
    dm.operation(s_col + '_tm1', '-', s_col, out_col='tra_delta_stock', unit=stock_unit)
    dm.operation('tra_delta_stock', '+', new_col, out_col=waste_col,
                 unit=stock_unit)
    # rr(t-1) = waste(t) / fleet(t-1)
    dm.operation(waste_col, '/', s_col + '_tm1', out_col='tmp', unit='%')
    dm.lag_variable(pattern='tmp', shift=-1, subfix='_rr')
    dm.rename_col('tmp_rr', rr_col, dim='Variables')
    dm.filter({'Variables': [s_col, s_col + '_tm1', rr_col]}, inplace=True)

    # FIX RENEWAL-RATE
    # move variables col to end
    dm_rr = dm.filter({'Variables': [rr_col]}, inplace=False)
    mask = (dm_rr.array < 0) | (dm_rr.array > max_rr)
    dm_rr.array[mask] = np.nan
    dm_rr.fill_nans('Years')
    dm.drop(dim='Variables', col_label=rr_col)
    dm.append(dm_rr, dim='Variables')

    # RECOMPUTE NEW FLEET
    dm.lag_variable(pattern=rr_col, shift=1, subfix='_tm1')
    # waste(t) = rr(t-1) * fleet(t-1)
    dm.operation(rr_col + '_tm1', '*', s_col + '_tm1', out_col=waste_col, unit=stock_unit)
    # new(t) = fleet(t) - fleet(t-1) + waste(t)
    dm.operation(s_col, '-', s_col + '_tm1', out_col='tra_delta_stock', unit=stock_unit)
    dm.operation('tra_delta_stock', '+', waste_col, out_col=new_col, unit=stock_unit)
    dm.filter({'Variables': [s_col, new_col, waste_col, rr_col]}, inplace=True)

    # FIX NEW FLEET
    dm_new = dm.filter({'Variables': [new_col]}, inplace=False)
    mask = (dm_new.array < 0)
    dm_new.array[mask] = np.nan
    dm_new.fill_nans('Years')
    dm.drop(dim='Variables', col_label=new_col)
    dm.append(dm_new, dim='Variables')

    # RECOMPUTE STOCK
    idx = dm.idx
    for t in dm.col_labels['Years'][1:]:
        s_tm1 = dm.array[:, idx[t-1], idx[s_col], ...]
        new_t = dm.array[:, idx[t], idx[new_col], ...]
        waste_t = dm.array[:, idx[t], idx[waste_col], ...]
        s_t = s_tm1 + new_t - waste_t
        dm.array[:, idx[t], idx[s_col], ...] = s_t

    return

# get waste and adjust new vehicles
dm_temp = dm_tech.filter({"Variables" : ['tra_passenger_veh-efficiency_fleet']})
var_names = {'stock': 'tra_passenger_technology-share_fleet', 'new': 'tra_passenger_new-vehicles',
             'waste': 'tra_passenger_vehicle-waste', 'renewal-rate': 'tra_passenger_renewal-rate'}
compute_renewal_rate_and_adjust(dm_tech, var_names, max_rr=0.1)
dm_renrate = dm_tech.filter({"Variables" : ['tra_passenger_renewal-rate']})
dm_tech.drop("Variables",'tra_passenger_renewal-rate')
dm_tech.append(dm_temp,"Variables")
dm_tech.sort("Variables")

########################################################
################## MAKE FTS FOR FLEET ##################
########################################################

# get fleet
dm_fleet = dm_tech.filter({"Variables" : ["tra_passenger_technology-share_fleet"]})
dm_fleet = dm_fleet.flatten().flatten()
dm_fleet.rename_col_regex("tra_passenger_technology-share_fleet_","","Variables")

# make a total
dm_total = dm_fleet.groupby({"total" : '2W|LDV|bus'}, dim='Variables', 
                            aggregation = "sum", regex=True, inplace=False)
dm_fleet.append(dm_total,"Variables")

# add missing years
dm_fleet.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

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

# set default time window for linear trend
baseyear_start = 2000
baseyear_end = 2023

# check
# dm_fleet.filter({"Country" : ["EU27"]}).datamatrix_plot()

# # try fts
# product = "LDV_PHEV-diesel"
# (make_fts(dm_fleet, product, baseyear_start, baseyear_end, dim = "Variables").
#   datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : [product]}))

# make fts
dm_fleet = make_fts(dm_fleet, "total", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "2W_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")

# get 2050 values for bev and phev
# note: assuming 8% of total fleet being electric in 2050
# source: https://www.eea.europa.eu/publications/electric-vehicles-and-the-energy/download
idx = dm_fleet.idx
electric_2050 = dm_fleet.array[idx["EU27"],idx[2050],idx["total"]] * 0.08
dm_share = dm_fleet.filter({"Country" : ["EU27"], "Years" : [2023], "Variables" : ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]})
dm_share.normalise("Variables")
idx_share = dm_share.idx
BEV_2050 = dm_share.array[:,:,idx_share["LDV_BEV"]] * electric_2050
PHEV_diesel_2050 = dm_share.array[:,:,idx_share["LDV_PHEV-diesel"]] * electric_2050
PHEV_gasoline_2050 = dm_share.array[:,:,idx_share["LDV_PHEV-gasoline"]] * electric_2050
bus_BEV_2050 = dm_share.array[:,:,idx_share["bus_BEV"]] * electric_2050

# # drop 2022-2023 for the electric vehicles (to avoid a flat line)
# idx = dm_fleet.idx
# for v in ["LDV_BEV","LDV_PHEV-diesel","LDV_PHEV-gasoline","bus_BEV"]:
#     dm_fleet.array[idx["EU27"],idx[2022],idx[v]] = np.nan
#     dm_fleet.array[idx["EU27"],idx[2023],idx[v]] = np.nan

# bev
dm_fleet.array[idx["EU27"],idx[2050],idx["LDV_BEV"]] = BEV_2050
dm_temp = linear_fitting(dm_fleet.filter({"Country" : ["EU27"], "Variables" : ["LDV_BEV"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_fleet.array[idx["EU27"],:,idx["LDV_BEV"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["LDV_BEV"]]

# ice
dm_fleet = make_fts(dm_fleet, "LDV_ICE-diesel", 2020, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "LDV_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "LDV_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")

# phev
dm_fleet.array[idx["EU27"],idx[2050],idx["LDV_PHEV-diesel"]] = PHEV_diesel_2050
dm_temp = linear_fitting(dm_fleet.filter({"Country" : ["EU27"], "Variables" : ["LDV_PHEV-diesel"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_fleet.array[idx["EU27"],:,idx["LDV_PHEV-diesel"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["LDV_PHEV-diesel"]]
dm_fleet.array[idx["EU27"],idx[2050],idx["LDV_PHEV-gasoline"]] = PHEV_gasoline_2050
dm_temp = linear_fitting(dm_fleet.filter({"Country" : ["EU27"], "Variables" : ["LDV_PHEV-gasoline"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_fleet.array[idx["EU27"],:,idx["LDV_PHEV-gasoline"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["LDV_PHEV-gasoline"]]

# bus bev
dm_fleet.array[idx["EU27"],idx[2050],idx["bus_BEV"]] = bus_BEV_2050
dm_temp = linear_fitting(dm_fleet.filter({"Country" : ["EU27"], "Variables" : ["bus_BEV"]}), years_ots + years_fts)
idx_temp = dm_temp.idx
dm_fleet.array[idx["EU27"],:,idx["bus_BEV"]] = dm_temp.array[idx_temp["EU27"],:,idx_temp["bus_BEV"]]

# rest
dm_fleet = make_fts(dm_fleet, "bus_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "bus_ICE-gas", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "bus_ICE-gasoline", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "metrotram_mt", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "rail_CEV", baseyear_start, baseyear_end, dim = "Variables")
dm_fleet = make_fts(dm_fleet, "rail_ICE-diesel", baseyear_start, baseyear_end, dim = "Variables")

# check
# dm_fleet.filter({"Country" : ["EU27"]}).datamatrix_plot()

# append
dm_tech.drop("Variables","tra_passenger_technology-share_fleet")
dm_fleet.drop("Variables","total")
for v in dm_fleet.col_labels["Variables"]:
    dm_fleet.rename_col(v,"tra_passenger_technology-share_fleet_" + v,"Variables")
dm_fleet.deepen_twice()
dm_tech.add(np.nan, col_label=years_fts, dummy=True, dim='Years')
dm_tech.append(dm_fleet,"Variables")
dm_tech.sort("Variables")

###############################################
################## DROP 1989 ##################
###############################################

dm_tech.drop("Years",startyear)
dm_renrate.drop("Years",startyear)

############################################
################## CHECKS ##################
############################################

# # check
# dm_tech.flatten().flatten().filter({"Country" : ["EU27"]}).datamatrix_plot()
# df = dm_tech.filter({"Country" : ["EU27"]}).write_df()
# fleet_2021 = np.array(df.loc[df["Years"] == 2021,"tra_passenger_technology-share_fleet_LDV_ICE-gasoline[num]"])
# fleet_2020 = np.array(df.loc[df["Years"] == 2020,"tra_passenger_technology-share_fleet_LDV_ICE-gasoline[num]"])
# waste_2021 = np.array(df.loc[df["Years"] == 2021,"tra_passenger_vehicle-waste_LDV_ICE-gasoline[num]"])
# new_2021 = np.array(df.loc[df["Years"] == 2021,"tra_passenger_new-vehicles_LDV_ICE-gasoline[num]"])
# fleet_2021 - fleet_2020 + waste_2021 == new_2021
# # yes ok


##########################################
################## SAVE ##################
##########################################

# get shares of fleet
dm_fleet = dm_tech.filter({"Variables" : ["tra_passenger_technology-share_fleet"]})
dm_fleet_pc = dm_fleet.normalise("Categories2",inplace=False)
dm_fleet_pc.rename_col_regex("_share","","Variables")
dm_tech.drop("Variables","tra_passenger_technology-share_fleet")
dm_tech.append(dm_fleet_pc,"Variables")
dm_tech.sort("Variables")

# add FCEV as missing
dm_tech.add(np.nan, col_label="FCEV", dummy=True, dim="Categories2")
dm_tech.sort("Categories2")

# order
dm_temp = dm_tech.filter({"Variables" : ['tra_passenger_technology-share_fleet']})
dm_temp.append(dm_tech.filter({"Variables" : ['tra_passenger_veh-efficiency_fleet']}),"Variables")
dm_temp.append(dm_tech.filter({"Variables" : ['tra_passenger_new-vehicles']}),"Variables")
dm_temp.append(dm_tech.filter({"Variables" : ['tra_passenger_vehicle-waste']}),"Variables")
dm_tech = dm_temp.copy()

# checks
list(DM_tra["fxa"])
DM_tra["fxa"]["passenger_tech"].units
dm_tech.units

# save
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_fleet.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm_fleet, handle, protocol=pickle.HIGHEST_PROTOCOL)
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_new-vehicles.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm_tech.filter({"Variables" : ['tra_passenger_new-vehicles']}), handle, protocol=pickle.HIGHEST_PROTOCOL)
f = os.path.join(current_file_directory, '../data/datamatrix/intermediate_files/passenger_renewal-rate.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm_renrate, handle, protocol=pickle.HIGHEST_PROTOCOL)
f = os.path.join(current_file_directory, '../data/datamatrix/fxa_passenger_tech.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm_tech, handle, protocol=pickle.HIGHEST_PROTOCOL)


