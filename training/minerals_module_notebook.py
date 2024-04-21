#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 19 17:27:44 2024

@author: echiarot
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 15:48:29 2024

@author: echiarot
"""

# %reset

import pandas as pd

# in Spyder, go to PYTHONPATH manager and put the directory containing all files (for me is /Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc)
# in Jupyter, this should work automatically
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database, update_database_from_db
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale, read_level_data
import pickle
import json
import os
import numpy as np
import re

from tqdm import tqdm, trange
import time

__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/training/minerals_module_notebook.py"
current_file_directory = os.path.dirname(os.path.abspath(__file__))

#######################################################################################################
######################################### LOAD TRANSPORT DATA #########################################
#######################################################################################################

#############################################
##### database_from_csv_to_datamatrix() #####
#############################################

# Description: this chunk of code makes the pickle with all the datamatrixes inside. In transport_module.py is defined as a function
# without arguments. This function runs the code and saves the pickle (it will not be used as a function later on). 
# Using a function without arguments is just a way to embed in a function a piece of code that needs to run.

# Read database

# Set years range
years_setting = [1990, 2015, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) # make list with years from 1990 to 2015
years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int)) # make list with years from 2020 to 2050 (steps of 5 years)
years_all = years_ots + years_fts

#####################
# FIXED ASSUMPTIONS #
#####################

# Read fixed assumptions to datamatrix
# edit_database(filename = 'minerals_fixed-assumptions', lever = 'fixed-assumptions', 
#               column = 'geoscale', pattern = 'Test', mode = 'remove') # had to do this to drop an additional country "Test"
df = read_database_fxa('minerals_fixed-assumptions')
dm = DataMatrix.create_from_df(df, num_cat=0) # this is a 3 dimensional arrays for the fixed assumptions in transport

# Keep only ots and fts years
dm = dm.filter(selected_cols={'Years': years_all})
dm.col_labels

# make data matrixes with specific data using regular expression (regex)
dm_elec_new = dm.filter_w_regex({'Variables': 'elc_new_RES.*|elc_new.*|.*solar.*'})
dm_elec_new.col_labels
dm_min_other = dm.filter_w_regex({'Variables': 'min_other.*'})
dm_min_proportion = dm.filter_w_regex({'Variables': 'min_proportion.*'})

# save
dict_fxa = {
    'elec_new': dm_elec_new,
    'min_other': dm_min_other,
    'min_proportion': dm_min_proportion
}

#############
# CONSTANTS #
#############

# load new constants in the constant dataframe file
# chunk of code to clean the current version of minerals_constants, save it, and update the interactions_constants with  

# =============================================================================
# df = read_database(filename = 'minerals_constants', lever = 'none', folderpath="default", db_format=True, level='all')
# df['eucalc-name'] = [i[0] for i in [i.split('+') for i in df['eucalc-name']]]
# df['eucalc-name'] = "cp_" + df['eucalc-name']
# df['string-pivot'] = [i[1] for i in [i.split('+') for i in df['string-pivot']]]
# # filepath = os.path.join(current_file_directory, '../_database/data/csv/minerals_constants.csv')
# # df.to_csv(filepath)
# folderpath = os.path.join(current_file_directory, '../_database/data/csv/')
# update_database_from_db(filename = 'interactions_constants', db_new = df, folderpath=folderpath)
# =============================================================================

# Load constants
# df = read_database(filename = 'interactions_constants', lever = 'none', folderpath="default", db_format=True, level='all')
cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_ind_material-efficiency.*|cp_min.*', num_cat=0)
[not bool(re.search("solar", str(i), flags=re.IGNORECASE)) for i in cdm_const.col_labels['Variables']]

########
# SAVE #
########

DM_minerals = {
    'fxa': dict_fxa,
    'constant': cdm_const
}

f = os.path.join(current_file_directory, '../_database/data/datamatrix/minerals.pickle')
# data_file_path = wd_path + "/_database/data/datamatrix/transport.pickle"
with open(f, 'wb') as handle:
    pickle.dump(DM_minerals, handle, protocol=pickle.HIGHEST_PROTOCOL)
    

del baseyear, cdm_const, df, dict_fxa, dm, dm_elec_new, dm_min_other, dm_min_proportion, DM_minerals, f, handle, lastyear,\
    startyear, step_fts, years_all, years_fts, years_ots, years_setting


######################################################################################################
######################################## MINERALS CORE MODULE ########################################
######################################################################################################

# set years
years_setting = [1990, 2015, 2050, 5]

# load datamatrixes
minerals_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/minerals.pickle')
with open(minerals_data_file, 'rb') as handle:
    DM_minerals = pickle.load(handle)

# get countries
cntr_list = DM_minerals["fxa"]["elec_new"].col_labels['Country']


########################################
##### begin of simulate_interfaces #####
########################################

# Description: in transport_module.py, this function is used in transport(lever_setting, years_setting) to
# make the fake interface data from lifestyle. This function does not have arguments and it is solely used to run code.

# get files' names
f = os.path.join(current_file_directory, "../_database/data/xls")
files = np.array(os.listdir(f))
files = files[
              [bool(re.search("All-Countries", str(i), flags=re.IGNORECASE)) for i in files] and
              [bool(re.search("minerals", str(i), flags=re.IGNORECASE)) for i in files]
              ]

# drop the ones that already run
files = files[[not bool(re.search("tpe", str(i), flags=re.IGNORECASE)) for i in files]]
files = files[[not bool(re.search("lifestyles", str(i), flags=re.IGNORECASE)) for i in files]]
files = files[[not bool(re.search("buildings", str(i), flags=re.IGNORECASE)) for i in files]]

# function to get data and add missing geoscales
def myfun(x):
    
    # read
    f = os.path.join(current_file_directory, "../_database/data/xls/" + x)
    df = pd.read_excel(f, sheet_name="default")
    
    # do eu27, paris and vaud
    df_eu27 = df.loc[df["Country"] == "Germany"].copy()
    df_eu27["Country"] = "EU27"
    df_paris = df.loc[df["Country"] == "Germany"].copy()
    df_paris["Country"] = "Paris"
    df_vaud = df.loc[df["Country"] == "Germany"].copy()
    df_vaud["Country"] = "Vaud"
    df = pd.concat([df, df_eu27, df_paris, df_vaud])
    df.sort_values(by=["Country","Years"])
    
    # get data matrix
    dm = DataMatrix.create_from_df(df, num_cat=0)
    
    return dm

# run function per file and save in dictionary
DM_interface = {}
keys = [i[0] for i in [i.split('-to-minerals') for i in files]]
keys = [i[1] for i in [i.split('All-Countries-interface_from-') for i in keys]]
for i in range(len(keys)): 
    DM_interface[keys[i]] = myfun(files[i])

# add buildings and lifestyle
# read
f = os.path.join(current_file_directory, "../_database/data/xls/" + "All-Countries-interface_from-buildings-to-minerals.xlsx")
df = pd.read_excel(f, sheet_name="default")
dm_buildings = DataMatrix.create_from_df(df, num_cat=0)
DM_interface["buildings"] = dm_buildings

f = os.path.join(current_file_directory, "../_database/data/xls/" + "All-Countries-interface_from-lifestyles-to-minerals.xlsx")
df = pd.read_excel(f, sheet_name="default")
dm_lifestyles = DataMatrix.create_from_df(df, num_cat=0)
DM_interface["lifestyles"] = dm_lifestyles

# keep only the countries in cntr_list
for i in keys:
    DM_interface[i] = DM_interface[i].filter({'Country': cntr_list})
    
del df, dm_buildings, dm_lifestyles, f, files, handle, i, keys


####################################
##### end of simulate__input() #####
####################################

#############################
##### RENAME INTERFACES #####
#############################

# get excel for renaming
filepath = os.path.join(current_file_directory, '../_database/data/csv/minerals_variables-names.csv')
df_names = pd.read_csv(filepath, sep=",")

# rename
for key in DM_interface.keys():
    
    if key in df_names["module_input"].values:
        
        dm_temp = DM_interface[key] # puntator
        
        idx_temp = df_names["old_name"].isin(dm_temp.col_labels["Variables"])
        old_name = df_names.loc[idx_temp,"old_name"].values.tolist()
        new_name = df_names.loc[idx_temp,"new_name"].values.tolist()
        
        if len(old_name)>0:
            for i in range(len(old_name)):
                dm_temp.rename_col(col_in = old_name[i], col_out = new_name[i], dim = "Variables")

# clean
del df_names, dm_temp, i, idx_temp, key, new_name, old_name, filepath

########################################################
#################### PRODUCT DEMAND ####################
########################################################

# get constants
cdm_constants = DM_minerals["constant"].copy()
cdm_constants.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")

# order:
# variables for product demand (unit)
# variables for product net import share (%), and therefore indir, exp and dir
# if you want minerals which will be used later, i.e. potahs and phosphate (from agri), fossil, wood, and glass sand

# get fxa
DM_fxa = DM_minerals['fxa'].copy()

# get datamatrixes
dm_tra = DM_interface["transport"].copy()
dm_bld = DM_interface["buildings"].copy()
dm_str = DM_interface["storage"].copy()
dm_ind = DM_interface["industry"].copy()

#####################
##### TRANSPORT #####
#####################

# make 2020 as mean of before and after for subways, planes, ships, trains
idx = dm_tra.idx
variabs = ["tra_other-subways","tra_other-planes","tra_other-ships","tra_other-trains"]
for i in variabs:
    dm_tra.array[:,idx[2020],idx[i]] = (dm_tra.array[:,idx[2015],idx[i]] + \
                                        dm_tra.array[:,idx[2025],idx[i]])/2
del idx, variabs

# demand for vehicles [num]
tra_veh = ['HDVH-EV','HDVH-FCEV','HDVH-ICE','HDVH-PHEV','HDVL-EV','HDVL-FCEV',
           'HDVL-ICE','HDVL-PHEV','HDVM-EV','HDVM-FCEV','HDVM-ICE','HDVM-PHEV','LDV-EV','LDV-FCEV','LDV-ICE','LDV-PHEV',
           '2W-EV','2W-FCEV','2W-ICE','2W-PHEV','bus-EV','bus-FCEV','bus-ICE','bus-PHEV',
           'other-planes', 'other-ships', 'other-subways', 'other-trains']

find = ["tra_" + i for i in tra_veh]
dm_tra_veh = dm_tra.filter(selected_cols = {"Variables":find})
dm_tra_veh.deepen()
dm_tra_veh.rename_col(col_in = "tra", col_out = "product-demand", dim="Variables")
# note that in dm_tra_veh.idx now product-demand appears as last, but this is fine as the order of idx is not important, what's important
# is the value of the key


#######################
##### ELECTRONICS #####
#######################

# filter
electr = ['electronics-computer','electronics-phone', 'electronics-tv']
find = ["bld_" + i for i in electr]
dm_electr = dm_bld.filter(selected_cols = {"Variables":find})

# deepen
dm_electr.deepen()
dm_electr.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")


#####################
##### BATTERIES #####
#####################

# this is demand for installed capacity of batteries, expressed in kWh

# get demand for batteries from energy sector
dm_battery = dm_str.filter_w_regex({"Variables": ".*battery.*"})
    
# convert from GW to kWh
dm_battery.array = dm_battery.array * 1000000
dm_battery.units['str_energy-battery'] = "kWh"

# deepen
dm_battery.deepen()
dm_battery.rename_col(col_in = "str", col_out = "product-demand", dim="Variables")

# get demand for batteries from transport and electronics

# get kWh from constants
cdm_temp = cdm_constants.filter_w_regex({"Variables": ".*batveh.*"}).copy()
cdm_temp.deepen()

# get transport and electronics variables which correspond to the constants

cdm_variabs = cdm_temp.col_labels["Categories1"]
dm_tra_veh_variabs = dm_tra_veh.col_labels["Categories1"]
dm_electr_variabs = dm_electr.col_labels["Categories1"]

dm_tra_veh_variabs = np.array(dm_tra_veh_variabs)[[i in cdm_variabs for i in dm_tra_veh_variabs]].tolist()
dm_electr_variabs = np.array(dm_electr_variabs)[[i in cdm_variabs for i in dm_electr_variabs]].tolist()

# put them together
dm_temp = dm_tra_veh.filter({"Categories1":dm_tra_veh_variabs})
dm_temp2 = dm_electr.filter({"Categories1":dm_electr_variabs})

dm_temp.append(dm_temp2, dim = "Categories1")

# sort
dm_temp.sort(dim = "Categories1")
cdm_temp.sort(dim = "Categories1")

# multiply demand of product (item) and kWh
arr_temp = dm_temp.array * cdm_temp.array[np.newaxis,np.newaxis,...]
# note that here we do an item-by-item multiplication, of matrixes (32, 33, 1, 14) and (1, 1, 1, 14). In theory we should multiply
# matrixes of same size, i.e. (32, 33, 1, 14) and (32, 33, 1, 14). Here python assumes that it needs to stack (1, 1, 1, 14) for all
# countries and years. This allows to avoid to have to do np.repeat().
dm_temp.add(arr_temp, dim = "Variables", col_label = "battery_demand", unit="kWh")

# split between transport and electronics
dm_temp_tra = dm_temp.filter({"Categories1":dm_tra_veh_variabs})
dm_temp_tra = dm_temp_tra.filter({"Variables":["battery_demand"]})

dm_temp_electr = dm_temp.filter({"Categories1":dm_electr_variabs})
dm_temp_electr = dm_temp_electr.filter({"Variables":["battery_demand"]})

# sum and put in dm_battery
arr_temp = np.nansum(dm_temp_tra.array, axis=-1, keepdims = True)
dm_battery.add(arr_temp, dim = "Categories1", col_label = "transport-battery")

arr_temp = np.nansum(dm_temp_electr.array, axis=-1, keepdims = True)
dm_battery.add(arr_temp, dim = "Categories1", col_label = "electronics-battery")

# clean
del arr_temp, cdm_temp, cdm_variabs, dm_electr_variabs, dm_temp, dm_temp2, dm_temp_electr, dm_temp_tra,\
    dm_tra_veh_variabs, i

##########################
##### INFRASTRUCTURE #####
##########################

# demand for infrastructure [km]
tra_inf = ['infra-rail', 'infra-road', 'infra-trolley-cables']
find = ["tra_" + i for i in tra_inf]
dm_infra = dm_tra.filter(selected_cols = {"Variables":find})

# get infra in bld
bld_infra = ['infra-pipe']
find = ["bld_" + i for i in bld_infra]
dm_infra_temp = dm_bld.filter({"Variables": find})
dm_infra_temp.rename_col_regex(str1 = "bld", str2 = "tra", dim="Variables")

# append
dm_infra.append(dm_infra_temp, dim = "Variables")

# deepen
dm_infra.deepen()
dm_infra.rename_col(col_in = "tra", col_out = "product-demand", dim="Variables")

del dm_infra_temp

##############################
##### DOMESTIC APPLIANCE #####
##############################

# get domestic appliances in bld
domapp = ['dom-appliance-dishwasher','dom-appliance-dryer','dom-appliance-freezer',
          'dom-appliance-fridge','dom-appliance-wmachine',]
find = ["bld_" + i for i in domapp]
dm_domapp = dm_bld.filter({"Variables": find})

# deepen
dm_domapp.deepen()
dm_domapp.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")

########################
##### CONSTRUCTION #####
########################

# get floor area
constr = ['floor-area-new-non-residential', 'floor-area-new-residential', 
         'floor-area-reno-non-residential', 'floor-area-reno-residential']
find = ["bld_" + i for i in constr]
dm_constr = dm_bld.filter({"Variables": find})

# deepen
dm_constr.deepen()
dm_constr.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")

##################
##### ENERGY #####
##################

# this is the demand for energy that comes from different energy sources, expressed in GW (power)

# get fts, which are in dm_str

energy = ['energy-coal', 'energy-csp', 'energy-gas', 'energy-geo', 'energy-hydro', 
          'energy-marine', 'energy-nuclear', 'energy-off-wind', 'energy-oil', 
          'energy-on-wind','energy-pvroof','energy-pvutility']
find = ["elc_" + i for i in energy]
dm_energy_fts = dm_str.filter({"Variables": find})

# add pvroof and pvutility
dm_energy_fts.operation('elc_energy-pvroof', "+", 'elc_energy-pvutility', dim = "Variables", out_col="elc_pv", unit="GW", div0="error")
dm_energy_fts.drop(dim = "Variables", col_label = ['elc_energy-pvroof','elc_energy-pvutility'])

# new variables
energy = ['energy-coal', 'energy-csp', 'energy-gas', 'energy-geo', 'energy-hydro', 
          'energy-marine', 'energy-nuclear', 'energy-off-wind', 'energy-oil', 
          'energy-on-wind','energy-pv']

# deepen
dm_energy_fts.deepen()

# get ots, which are in fxa

dm_energy_ots = DM_fxa["elec_new"].copy()
dm_energy_ots.rename_col_regex("_tech", "", dim = "Variables")
dm_energy_ots.rename_col_regex("_new_RES", "", dim = "Variables")
dm_energy_ots.rename_col_regex("_new_fossil", "", dim = "Variables")
dm_energy_ots.rename_col_regex("elc_", "elc_energy-", dim = "Variables")
# !FIXME: at the moment we do not have ots for oil and coal

# make all zeroes for oil and coal ots for the moment
c , y = len(dm_energy_ots.col_labels["Country"]), len(dm_energy_ots.col_labels["Years"])
arr_temp = np.zeros((c, y))
dm_energy_ots.add(arr_temp, dim = "Variables", col_label = "elc_energy-coal", unit="GW")
dm_energy_ots.add(arr_temp, dim = "Variables", col_label = "elc_energy-oil", unit="GW")

# deepen
dm_energy_ots.deepen()

# sort
dm_energy_fts.sort(dim = "Categories1")
dm_energy_ots.sort(dim = "Categories1")

# add and save in dm_energy
arr_temp = dm_energy_ots.array + dm_energy_fts.array
dm_energy = dm_energy_ots.copy()
dm_energy.add(arr_temp, dim = "Variables", col_label = "product-demand", unit="GW")
dm_energy.drop(dim = "Variables", col_label = ['elc'])

# clean
del arr_temp, c, dm_energy_fts, dm_energy_ots, find, y

########################
##### PUT TOGETHER #####
########################

DM_demand = {"vehicles" : dm_tra_veh,
             "electronics" : dm_electr, 
              "batteries" : dm_battery, 
              "infrastructure" : dm_infra, 
              "dom-appliance" : dm_domapp, 
              "construction" : dm_constr, 
              "energy" : dm_energy}

# clean
del dm_tra_veh, dm_electr, dm_battery, dm_infra, dm_domapp, dm_constr, dm_energy


##############################################################################
#################### IMPORTS (IN SHARE OF PRODUCT DEMAND) ####################
##############################################################################

# get imports and rename
dm_import = dm_ind.filter_w_regex({"Variables":".*import.*"})
dm_import.rename_col_regex(str1 = "_product-net-import", str2 = "", dim = "Variables")

# add net imports for categories of vehicles we do not have
variabs = ["LDV-ICE", "HDVL-ICE", "other-trains", "LDV-ICE","LDV-ICE","LDV-ICE","LDV-ICE","HDVL-ICE","HDVL-ICE",
           "HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE"]
variabs = ["ind_" + i for i in variabs]
variabs_new = ["LDV-PHEV","HDVL-PHEV","other-subways","2W-EV","2W-ICE","2W-FCEV","2W-PHEV","bus-EV","bus-ICE",
               "bus-FCEV","bus-PHEV","HDVM-EV","HDVM-ICE","HDVM-FCEV","HDVM-PHEV","HDVH-EV","HDVH-ICE","HDVH-FCEV","HDVH-PHEV"]
variabs_new = ["ind_" + i for i in variabs_new]

idx = dm_import.idx
for i in range(len(variabs)):
    dm_import.add(dm_import.array[:,:,idx[variabs[i]]], dim="Variables", col_label=variabs_new[i], unit="%")
    
# clean
del i, idx, variabs, variabs_new


#########################################################################################################################
#################### PRODUCT INDIRECT DEMAND, NET EXPORT, DIRECT DEMAND (IN SHARE OF PRODUCT DEMAND) ####################
#########################################################################################################################

# demand split
dm_demand_split_share = dm_import.copy()

# product indirect demand
name_old = dm_demand_split_share.col_labels["Variables"]
name_new = [i + "_indir" for i in name_old]
for i in range(len(name_old)):
    dm_demand_split_share.rename_col(col_in = name_old[i], col_out = name_new[i], dim = "Variables")

# deepen
dm_demand_split_share.deepen_twice()
dm_demand_split_share.rename_col(col_in = "ind", col_out = "product-demand-split-share", dim = "Variables")

# product net export
arr_temp = -dm_demand_split_share.array
dm_demand_split_share.add(arr_temp, dim = "Categories2", col_label = "exp", unit = "%")

# product direct demand
idx = dm_demand_split_share.idx
arr_temp = dm_demand_split_share.array[:,:,:,:,idx["indir"]]-dm_demand_split_share.array[:,:,:,:,idx["indir"]]+1
dm_demand_split_share.add(arr_temp, dim = "Categories2", col_label = "dir", unit = "%")

# add to dm_trade the share for other products from constants

def cdm_to_dm(cdm, countries_list, years_list):
    arr_temp = cdm.array[np.newaxis, np.newaxis, ...]
    arr_temp = np.repeat(arr_temp, len(countries_list), axis=0)
    arr_temp = np.repeat(arr_temp, len(years_list), axis=1)
    cy_cols = {
        'Country': countries_list.copy(),
        'Years': years_list.copy(),
    }
    new_cols = {**cy_cols, **cdm.col_labels}
    dm = DataMatrix(col_labels=new_cols, units=cdm.units)
    dm.array = arr_temp
    return dm

countries_list = dm_demand_split_share.col_labels["Country"]
years_list = dm_demand_split_share.col_labels["Years"]
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*trade*"}).copy()
cdm_temp = cdm_to_dm(cdm_temp, countries_list, years_list)

# deepen
cdm_temp.deepen_twice()
cdm_temp.rename_col(col_in = "min_trade", col_out = "product-demand-split-share", dim = "Variables")

# append
dm_demand_split_share.append(cdm_temp, dim = "Categories1")

# clean
del arr_temp, cdm_temp, i, idx, name_new, name_old

####################################################################################################
#################### PRODUCT INDIRECT DEMAND, NET EXPORT, DIRECT DEMAND (UNITS) ####################
####################################################################################################

# create empty dictionary without constructions (they are assumed not to be traded)
DM_demand_split = dict.fromkeys(["vehicles","electronics", "batteries", 
                                 "infrastructure", "dom-appliance", "energy"])

for key in DM_demand_split.keys():

    # get demand
    dm_demand_temp = DM_demand[key]
    
    # get corresponding split share
    dm_demand_split_temp = dm_demand_split_share.filter({"Categories1": dm_demand_temp.col_labels["Categories1"]})
    
    # multiply demand with split share to make split in unit
    arr_temp = dm_demand_temp.array[...,np.newaxis] * dm_demand_split_temp.array
    
    # add split in unit as a variable
    dm_demand_split_temp.add(arr_temp, dim = "Variables", 
                             col_label = "product-demand-split-unit", unit=dm_demand_temp.units["product-demand"])
    
    # drop product demand split share
    dm_demand_split_temp.drop(dim = "Variables", col_label = ["product-demand-split-share"])
    
    # put dm in dictionary
    DM_demand_split[key] = dm_demand_split_temp


# clean
del key, dm_demand_temp, dm_demand_split_temp, arr_temp


###############################################################
#################### MINERAL DECOMPOSITION ####################
###############################################################

def get_mindec(dm, cdm):
    
    # sort
    dm.sort("Categories1")
    dm.sort("Categories2")
    cdm.sort("Categories2")
    
    # col names
    cols = {"Country" : dm.col_labels["Country"],
            "Years" : dm.col_labels["Years"],
            "Variables" : ["mineral-decomposition"],
            "Categories1" : dm.col_labels["Categories1"],
            "Categories2" : dm.col_labels["Categories2"],
            "Categories3" : cdm.col_labels["Categories2"]
            }
    
    # dim labels
    dim_labels_new = list(cols)
    
    # idx
    values = cols["Country"]
    idx_new = dict(zip(iter(values), iter(list(range(0,len(values))))))
    myrange = list(cols)[1:len(list(cols))]
    for key in myrange:
        values = cols[key]
        mydict = dict(zip(iter(values), iter(list(range(0,len(values))))))
        idx_new.update(mydict)
    
    # unit
    unit = cdm.units
    key_old = list(unit)[0]
    unit["mineral-decomposition"] = unit.pop(key_old)
    value_old = list(unit.values())[0]
    unit["mineral-decomposition"] = value_old.split("/")[0]
    
    # data matrix
    dm_out = DataMatrix(col_labels=cols, units=unit)
    dm_out.idx = idx_new
    dm_out.dim_labels = dim_labels_new
    
    # get array
    arr = dm.array[...,np.newaxis] * cdm.array[np.newaxis,np.newaxis,:,:,np.newaxis,:]
    
    # insert array
    dm_out.array = arr
    
    return dm_out


# def add_missing_minerals(minerals_list, DM):

#     for key in DM.keys():
        
#         # get dm (puntator)
#         dm = DM[key]
        
#         # get missing minerals
#         minerals = dm.col_labels["Categories3"]
#         minerals_missing = np.array(minerals_list)[[i not in minerals for i in minerals_list]].tolist()
        
#         # add nan arrays for missing minerals
#         for i in minerals_missing:
#             arr = dm.array[:,:,:,:,:,0]
#             arr.fill(np.NaN)
#             dm.add(arr, dim = "Categories3", col_label = i)
            
#         # sort
#         dm.sort("Categories3")


def add_nan(dm, variables_list, dim):

    # get missing variables
    variables = dm.col_labels[dim]
    variables_missing = np.array(variables_list)[[i not in variables for i in variables_list]].tolist()
    
    # add nan arrays for missing variables
    for i in variables_missing:
        arr = dm.array[...,0]
        arr = arr[...,np.newaxis]
        arr.fill(np.NaN)
        dm.add(arr, dim = dim, col_label = i)
        
    # sort
    dm.sort(dim)
    
minerals = ['aluminium','copper','graphite','lead','lithium','manganese','nickel','steel']

#####################
##### BATTERIES #####
#####################

# get product demand split unit
dm_temp = DM_demand_split["batteries"]

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*battery*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|energytech).)*$"})
cdm_temp.deepen_twice()

# idx = cdm_temp.idx
# cdm_temp.array[:,idx["transport-battery"],idx["aluminium"]] # this is nan so it will give nan, as transport batteries do not have alu

# get minderal decomposition
dm_battery_mindec = get_mindec(dm_temp, cdm_temp)

# clean
del dm_temp, cdm_temp

######################
##### CARS (LDV) #####
######################

# get names
tra_ldv = np.array(tra_veh)[[bool(re.search("LDV", str(i), flags=re.IGNORECASE)) for i in tra_veh]].tolist()

# get product demand split unit
dm_temp = DM_demand_split["vehicles"]
dm_temp = dm_temp.filter_w_regex({"Categories1":".*LDV*"})

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*LDV*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
cdm_temp.deepen_twice()

# get minderal decomposition
dm_veh_ldv_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across vehicles
arr_temp = np.nansum(dm_veh_ldv_mindec.array, axis=-3, keepdims = True)
dm_veh_ldv_mindec.add(arr_temp, dim = "Categories1", col_label = "LDV")
dm_veh_ldv_mindec.drop(dim = "Categories1", col_label = tra_ldv)

# get mineral switch parameter
dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-cars*"})

# set variables with mineral that is switched
mineral_in = "steel"
mineral_out = "other"

mineral_in_unadj = mineral_in + "-unadj"
mineral_switched = mineral_in + "-switched-to-" + mineral_out

dm_veh_ldv_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")

# for mineral that is switched, get how much is switched and add it as new variable
idx = dm_veh_ldv_mindec.idx
arr_temp = dm_veh_ldv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
dm_veh_ldv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

# do mineral unadjusted - mineral switched
dm_veh_ldv_mindec.operation(col1 = mineral_in_unadj, operator = "-", col2 = mineral_switched, dim = "Categories3",
                        out_col = mineral_in)

# for indir, substitute back the unadjusted one (adjustment is only done on exp and dir)
dm_veh_ldv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_veh_ldv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]

# drop
dm_veh_ldv_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_switched])

# clean
del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_switched, mineral_in_unadj, idx, arr_temp


########################
##### TRUCKS (HDV) #####
########################

# get names
tra_hdv = np.array(tra_veh)[[bool(re.search("HDV", str(i), flags=re.IGNORECASE)) for i in tra_veh]].tolist()

# get product demand split unit
dm_temp = DM_demand_split["vehicles"]
dm_temp = dm_temp.filter_w_regex({"Categories1":".*HDV*"})

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*HDV*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
cdm_temp.deepen_twice()

# get minderal decomposition
dm_veh_hdv_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across vehicles
arr_temp = np.nansum(dm_veh_hdv_mindec.array, axis=-3, keepdims = True)
dm_veh_hdv_mindec.add(arr_temp, dim = "Categories1", col_label = "HDV")
dm_veh_hdv_mindec.drop(dim = "Categories1", col_label = tra_hdv)

# do the switch steel to other and steel to aluminium

# get mineral switch parameter
dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-trucks-steel-other*"})
dm_temp_alu = dm_ind.filter_w_regex({"Variables":".*switch-trucks-steel-aluminium*"})

# set variables with mineral that is switched
mineral_in = "steel"
mineral_out = "other"
mineral_out2 = "aluminium"

mineral_in_unadj = mineral_in + "-unadj"
mineral_out2_unadj = mineral_out2 + "-unadj"

mineral_switched = mineral_in + "-switched-to-" + mineral_out
mineral_switched2 = mineral_in + "-switched-to-" + mineral_out2

dm_veh_hdv_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")
dm_veh_hdv_mindec.rename_col(col_in = mineral_out2, col_out = mineral_out2_unadj, dim = "Categories3")

# for mineral that is switched, get how much is switched and add it as new variable
idx = dm_veh_hdv_mindec.idx

arr_temp = dm_veh_hdv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
dm_veh_hdv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

arr_temp = dm_veh_hdv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
arr_temp = arr_temp[...,np.newaxis] * dm_temp_alu.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
dm_veh_hdv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched2)

# do mineral unadjusted - mineral switched
dm_veh_hdv_mindec.operation(col1 = mineral_in_unadj, operator = "-", col2 = mineral_switched, dim = "Categories3",
                        out_col = mineral_in)

# do aluminium + steel-switched-to-aluminium
dm_veh_hdv_mindec.operation(col1 = mineral_out2_unadj, operator = "+", col2 = mineral_switched2, dim = "Categories3",
                        out_col = mineral_out2)

# for indir, substitute back the unadjusted ones (adjustment is only done on exp and dir)
dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]
dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_out2]] = dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_out2_unadj]]

# drop
dm_veh_hdv_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_out2_unadj, mineral_switched, mineral_switched2])

# sort
dm_veh_hdv_mindec.sort("Categories3")

# clean
del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_out2, mineral_switched, \
    mineral_switched2, mineral_in_unadj, mineral_out2_unadj, idx, arr_temp, dm_temp_alu


##########################
##### OTHER VEHICLES #####
##########################

# get other vehicles
tra_oth = ['2W-EV','2W-FCEV','2W-ICE','2W-PHEV','bus-EV','bus-FCEV','bus-ICE','bus-PHEV',
           'other-planes', 'other-ships', 'other-subways', 'other-trains']

# get product demand split unit
dm_temp = DM_demand_split["vehicles"]
dm_temp = dm_temp.filter({"Categories1":tra_oth})

# get constants for mineral decomposition
find = [".*" + i + ".*" for i in tra_oth]
cdm_temp = cdm_constants.filter_w_regex({"Variables": "|".join(find)})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
cdm_temp.deepen_twice()

# get minderal decomposition
dm_veh_oth_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across vehicles
arr_temp = np.nansum(dm_veh_oth_mindec.array, axis=-3, keepdims = True)
dm_veh_oth_mindec.add(arr_temp, dim = "Categories1", col_label = "other")
dm_veh_oth_mindec.drop(dim = "Categories1", col_label = tra_oth)

# clean
del dm_temp, cdm_temp, arr_temp, find


###########################
##### TRANSPORT TOTAL #####
###########################

# get batteries for transport
dm_veh_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['transport-battery']})

# add missing minerals to the dms
DM_temp = {"ldv": dm_veh_ldv_mindec, 
           "hdv": dm_veh_hdv_mindec, 
           "oth": dm_veh_oth_mindec, 
           "batt" : dm_veh_batt_mindec}

for key in DM_temp.keys():
    add_nan(dm = DM_temp[key], variables_list = minerals, dim = "Categories3")

# sum across vehicles and batteries
dm_veh_mindec = dm_veh_ldv_mindec.copy()
arr_temp = dm_veh_ldv_mindec.array + dm_veh_hdv_mindec.array + dm_veh_oth_mindec.array + dm_veh_batt_mindec.array
dm_veh_mindec.add(arr_temp, dim = "Categories1", col_label = "transport")
dm_veh_mindec.drop(dim = "Categories1", col_label = "LDV")

del dm_veh_ldv_mindec, dm_veh_hdv_mindec, dm_veh_oth_mindec, arr_temp, DM_temp


##########################
##### INFRASTRUCTURE #####
##########################

infra = tra_inf + bld_infra

# get product demand split unit
dm_temp = DM_demand_split["infrastructure"]

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*infra*"})
cdm_temp.rename_col_regex(str1 = "infra_", str2 = "infra-", dim = "Variables")
cdm_temp.deepen_twice()

# get minderal decomposition
dm_infra_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across infra
arr_temp = np.nansum(dm_infra_mindec.array, axis=-3, keepdims = True)
dm_infra_mindec.add(arr_temp, dim = "Categories1", col_label = "infra")
dm_infra_mindec.drop(dim = "Categories1", col_label = infra)

# clean
del dm_temp, cdm_temp, arr_temp

##############################
##### DOMESTIC APPLIANCE #####
##############################

# get product demand split unit
dm_temp = DM_demand_split["dom-appliance"]

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*appliance*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!min_other).)*$"})
cdm_temp.rename_col_regex(str1 = "appliance", str2 = "dom-appliance", dim = "Variables")
cdm_temp.deepen_twice()

# get minderal decomposition
dm_domapp_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across dom appliance
arr_temp = np.nansum(dm_domapp_mindec.array, axis=-3, keepdims = True)
dm_domapp_mindec.add(arr_temp, dim = "Categories1", col_label = "dom-appliance")
dm_domapp_mindec.drop(dim = "Categories1", col_label = domapp)

# get factor for materials coming from unaccounted appliances
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*min_other_dom*"})
cdm_temp.rename_col_regex(str1 = "other_dom-appliances", str2 = "other-dom-appliance", dim = "Variables")
cdm_temp.deepen_twice()
cdm_temp.sort("Categories2")

# divide mineral split by this factor (to get mineral + extra mineral from unaccounted sectors)
dm_domapp_mindec.array = dm_domapp_mindec.array / cdm_temp.array[np.newaxis,np.newaxis,np.newaxis,...]

# get aluminium packages (t) and add it to aluminium from dom appliance
dm_temp = dm_ind.filter({"Variables":["ind_product_aluminium-pack"]})
dm_temp.array = dm_temp.array * 1000 # make Mt

idx = dm_domapp_mindec.idx
dm_domapp_mindec.array[:,:,:,:,:,idx["aluminium"]] = dm_domapp_mindec.array[:,:,:,:,:,idx["aluminium"]] + \
    dm_temp.array[...,np.newaxis,np.newaxis]

# clean
del dm_temp, cdm_temp, arr_temp, idx


#######################
##### ELECTRONICS #####
#######################

# get product demand split unit
dm_temp = DM_demand_split["electronics"]

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*electr*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|batveh|battery).)*$"})
cdm_temp.rename_col_regex(str1 = "electronics_", str2 = "electronics-", dim = "Variables")
cdm_temp.deepen_twice()

# get minderal decomposition
dm_electr_cotvph_mindec = get_mindec(dm_temp, cdm_temp)

# get batteries for electronics
dm_electr_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['electronics-battery']})

# add missing minerals to the dms
DM_temp = {"electr": dm_electr_cotvph_mindec, 
           "batt": dm_electr_batt_mindec}

for key in DM_temp.keys():
    add_nan(dm = DM_temp[key], variables_list = minerals, dim = "Categories3")
    
# append
dm_electr_cotvph_mindec.append(dm_electr_batt_mindec, dim = "Categories1")

# get sum across electr
arr_temp = np.nansum(dm_electr_cotvph_mindec.array, axis=-3, keepdims = True)
dm_electr_cotvph_mindec.add(arr_temp, dim = "Categories1", col_label = "electronics")
electr = electr + ["electronics-battery"]
dm_electr_cotvph_mindec.drop(dim = "Categories1", col_label = electr)

# copy
dm_electr_mindec = dm_electr_cotvph_mindec.copy()

# clean
del dm_electr_cotvph_mindec, dm_electr_batt_mindec, dm_temp, cdm_temp, arr_temp, DM_temp, key, 

########################
##### CONSTRUCTION #####
########################

# get product demand split unit
dm_temp = DM_demand["construction"].copy()

# convert Mm2 to m2
dm_temp.array = dm_temp.array * 1000000
dm_temp.units["product-demand"] = "m2"

# expand of 1 dimension
dm_temp.array = dm_temp.array[...,np.newaxis]
dm_temp.col_labels["Categories2"] = ["dir"]
dm_temp.dim_labels = dm_temp.dim_labels + ["Categories2"]
dm_temp.idx["Categories2"] = 0

# add exp and indir as nan 
variables_list = ["dir", "exp", "indir"]
add_nan(dm = dm_temp, variables_list = variables_list, dim = "Categories2")

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*building*"})
cdm_temp.rename_col_regex(str1 = "building_", str2 = "building-", dim = "Variables")
cdm_temp.rename_col_regex(str1 = "new_", str2 = "new-", dim = "Variables")
cdm_temp.rename_col_regex(str1 = "reno_", str2 = "reno-", dim = "Variables")
cdm_temp.deepen_twice()

# get mineral decomposition
dm_constr_mindec = get_mindec(dm_temp, cdm_temp)

# get sum across buildings
arr_temp = np.nansum(dm_constr_mindec.array, axis=-3, keepdims = True)
dm_constr_mindec.add(arr_temp, dim = "Categories1", col_label = "construction")
dm_constr_mindec.drop(dim = "Categories1", col_label = constr)

# get mineral switch parameter
dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-build*"})

# set variables with mineral that is switched
mineral_in = "steel"
mineral_out = "timber"

mineral_in_unadj = mineral_in + "-unadj"
mineral_switched = mineral_in + "-switched-to-" + mineral_out

dm_constr_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")

# for mineral that is switched, get how much is switched and add it as new variable
idx = dm_constr_mindec.idx
arr_temp = dm_constr_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
dm_constr_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

# do mineral unadjusted - mineral switched
dm_constr_mindec.operation(col1 = mineral_in_unadj, operator = "-", col2 = mineral_switched, dim = "Categories3",
                        out_col = mineral_in)

# for indir and exp, substitute back the unadjusted one (adjustment is only done on exp and dir)
dm_constr_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_constr_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]
dm_constr_mindec.array[:,:,:,:,idx["exp"],idx[mineral_in]] = dm_constr_mindec.array[:,:,:,:,idx["exp"],idx[mineral_in_unadj]]

# drop
dm_constr_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_switched])

# clean
del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_switched, mineral_in_unadj, idx, arr_temp, variables_list


##################
##### ENERGY #####
##################

# get product demand split unit
dm_temp = DM_demand_split["energy"].copy()

# get constants for mineral decomposition
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*energy*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|battery).)*$"})
cdm_temp.deepen_twice()

# get constants for thin film
cdm_temp2 = cdm_constants.filter_w_regex({"Variables":".*min_share_pv_*"})
cdm_temp2.rename_col_regex(str1 = "pv_", str2 = "pv-", dim = "Variables")

# get indir, exp and dir for energy-pv-csi (by multipilication with the thin film and csi factors)
idx = dm_temp.idx
idx2 = cdm_temp2.idx

arr_temp = dm_temp.array[:,:,:,idx["energy-pv"],:] * cdm_temp2.array[idx2["min_share_pv-csi"]]
dm_temp.add(arr_temp, dim = "Categories1", col_label = "energy-pv-csi")

arr_temp = dm_temp.array[:,:,:,idx["energy-pv"],:] * cdm_temp2.array[idx2["min_share_pv-thinfilm"]]
dm_temp.add(arr_temp, dim = "Categories1", col_label = "energy-pv-thinfilm")

dm_temp.drop(dim = "Categories1", col_label = ["energy-pv"])
energy = energy[0:-1]
energy = energy + ['energy-pv-csi','energy-pv-thinfilm']

# get mineral decomposition
dm_energy_tech_mindec = get_mindec(dm_temp, cdm_temp)

# get batteries for energy
dm_energy_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['energy-battery']})

# add missing minerals to the dms
DM_temp = {"energy": dm_energy_tech_mindec, 
           "batt": dm_energy_batt_mindec}

for key in DM_temp.keys():
    add_nan(dm = DM_temp[key], variables_list = minerals, dim = "Categories3")
    
# append
dm_energy_tech_mindec.append(dm_energy_batt_mindec, dim = "Categories1")
dm_energy_mindec = dm_energy_tech_mindec.copy()

# get sum across energy
arr_temp = np.nansum(dm_energy_mindec.array, axis=-3, keepdims = True)
dm_energy_mindec.add(arr_temp, dim = "Categories1", col_label = "energy")
energy = energy + ["energy-battery"]
dm_energy_mindec.drop(dim = "Categories1", col_label = energy)

# get electricity demand total (GWh) and constant for amount of copper in wires (kg/GWh)
dm_temp = dm_str.filter({"Variables":["elc_electricity-demand_total"]})
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*wire_copper*"})

# multiply demand times amount of copper in wires to get amount of copper in wires (kg)
dm_temp.array = dm_temp.array * cdm_temp.array[0]
dm_temp.units["elc_electricity-demand_total"] = "kg"

# add amount of coppers in wires to copper from energy
idx = dm_energy_mindec.idx
arr_temp = dm_energy_mindec.array[...,idx["copper"]]
arr_temp = arr_temp + dm_temp.array[...,np.newaxis,np.newaxis]
dm_energy_mindec.array[...,idx["copper"]] = arr_temp

# clean
del dm_energy_tech_mindec, dm_energy_batt_mindec, dm_temp, cdm_temp, arr_temp, cdm_temp2, idx, idx2, \
    DM_temp, key


########################
##### ALL MINERALS #####
########################


# add minerals as nans for those dms which do not have all minerals

DM_mindec = {"veh": dm_veh_mindec, 
             "infra": dm_infra_mindec,
             "domapp": dm_domapp_mindec,
             "electr": dm_electr_mindec, 
             "constr": dm_constr_mindec, 
             "energy" : dm_energy_mindec}

for key in DM_mindec.keys():
    
    dm_temp = DM_mindec[key]
    minerals_temp = dm_temp.col_labels["Categories3"]
    
    if not minerals_temp == minerals:
        add_nan(dm = dm_temp, variables_list = minerals, dim = "Categories3")
        

# sum minerals across all sectors
dm_mindec = dm_veh_mindec.copy()
arr_temp = dm_veh_mindec.array + dm_infra_mindec.array + dm_domapp_mindec.array + \
           dm_electr_mindec.array  + dm_constr_mindec.array + dm_energy_mindec.array
dm_mindec.add(arr_temp, dim = "Categories1", col_label = "all-sectors")
dm_mindec.drop(dim = "Categories1", col_label ="transport")


#############################################
##### MINERALS FROM UNACCOUNTED SECTORS #####
#############################################

# add aluminium, copper, lead and steel from unaccounted sectors

# get constants
cdm_temp = cdm_constants.filter_w_regex({"Variables":".*other*"})
cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!vehicle|appliance).)*$"})
cdm_temp.deepen_twice()







# additional minerals from industry and unaccounted sectors


###################################################################################################
#################### ADDITIONAL MINERALS FROM INDUSTRY AND UNACCOUNTED SECTORS ####################
###################################################################################################

















