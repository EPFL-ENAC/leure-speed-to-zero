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

# Add dimensions
# to do later for dm_min_proportion

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
# =============================================================================
# chunk of code to clean the current version of minerals_constants, save it, and update the interactions_constants with  
# df = read_database(filename = 'minerals_constants', lever = 'none', folderpath="default", db_format=True, level='all')
# df['eucalc-name'] = [i[0] for i in [i.split('+') for i in df['eucalc-name']]]
# df['eucalc-name'] = "cp_" + df['eucalc-name']
# df['string-pivot'] = [i[1] for i in [i.split('+') for i in df['string-pivot']]]
# filepath = os.path.join(current_file_directory, '../_database/data/csv/minerals_constants.csv')
# df.to_csv(filepath)
# update_database_from_db('interactions_constants', df, folderpath="default")
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

f = os.path.join(current_file_directory, '../_database/data/datamatrix/transport.pickle')
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
minerals_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/transport.pickle')
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


########################################################################
############################## FORMATTING ##############################
########################################################################

# dm = dm_str
# string = "bio"

def col_names_search(dm, string):
    
    variabs = np.array(dm.col_labels["Variables"].copy())
    variabs_sel = variabs[[bool(re.search(string, str(i), flags=re.IGNORECASE)) for i in variabs]]
    
    if len(variabs_sel) == 1:
        return variabs_sel.tolist()[0]
    else:
        return variabs_sel.tolist()

# def col_names_search_multi(dm, string):
    
#     variabs = np.array(dm.col_labels["Variables"].copy())
#     variabs_sel = variabs[[bool(re.search(string, str(i), flags=re.IGNORECASE)) for i in variabs]]
#     return variabs_sel.tolist()

######################
##### GET THINGS #####
######################

# get fixed assumptions
dict_fxa = DM_minerals['fxa'].copy()
dm_elec_new = dict_fxa['elec_new'].copy()
dm_min_other = dict_fxa['min_other'].copy()
dm_min_proportion = dict_fxa['min_proportion'].copy()

# get constants
cdm_constants = DM_minerals["constant"].copy()
cdm_constants.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")

# get storage
dm_str = DM_interface["storage"].copy()

# variabs = ["demand","battery"]
# variabs = [col_names_search(dm_str,i) for i in variabs]
# dm_str_elcdemtot = dm_str.filter(selected_cols={"Variables": [variabs[0]]}).copy()
# dm_str_battery = dm_str.filter(selected_cols={"Variables": [variabs[1]]}).copy()
# dm_str_battery.rename_col(col_in = variabs[1], col_out = "tra_energy-battery", dim = "Variables")
# dm_str_battery.rename_col(col_in = col_names_search(dm_str_battery,"battery"), 
#                          col_out = "tra_energy-battery", dim = "Variables")

# dm_str = DM_interface["storage"].copy()
dm_str_elcdemtot = dm_str.filter_w_regex({"Variables": ".*demand.*"}).copy()
dm_str_battery = dm_str.filter_w_regex({"Variables": ".*battery.*"}).copy()
dm_str_battery.col_labels['Variables'] = ['tra_energy-battery']

drop = ["bio_gas","bio_mass","ptx","caes","flywheel","phs"]
drop = [col_names_search(dm_str, i) for i in drop]
drop = drop + dm_str_elcdemtot.col_labels["Variables"] + dm_str_battery.col_labels["Variables"]
dm_str.drop("Variables", col_label = "|".join(drop))

oldname = ["onshore","offshore","geo","hydro","marine","csp","nuclear","coal","gas","oil","pvroof","pvutility"]
oldname = [col_names_search(dm_str,i) for i in oldname]
newname = ["on-wind","off-wind","geo","hydro","marine","csp","nuclear","coal","gas","oil","solar_Pvroof","solar_Pvutility"]
newname = ["elc_FTS_" + i for i in newname]
for i in range(len(oldname)):
    dm_str.rename_col(col_in = oldname[i], col_out = newname[i], dim = "Variables")
    
# industry
dm_ind = DM_interface["industry"].copy()
dm_ind.drop("Variables", col_label = "material_switch_ratios")
dm_ind.rename_col_regex("technology-development", "proportion", dim = "Variables")

# oldname = ["cars-steel-to-chem","trucks-steel-to-chem","trucks-steel-to-aluminium","build-steel-to-timber"]
# oldname = [col_names_search(dm_ind,i) for i in oldname]
# newname = ["cars_steel_other","trucks-steel-other","trucks_steel_aluminium","build-steel-timber"]
# newname = ["ind_material-switch" + i for i in newname]
# for i in range(len(oldname)):
#     dm_ind.rename_col(col_in = oldname[i], col_out = newname[i], dim = "Variables")

dm_ind.rename_col(col_in = "ind_material-switch_cars-steel-to-chem", col_out = "ind_material-switch_cars_steel_other", dim = "Variables")
dm_ind.rename_col(col_in = "ind_material-switch_trucks-steel-to-chem", col_out = "ind_material-switch_trucks_steel_other", dim = "Variables")
dm_ind.rename_col(col_in = "ind_material-switch_trucks-steel-to-aluminium", col_out = "ind_material-switch_trucks_steel_aluminium", dim = "Variables")
dm_ind.rename_col(col_in = "ind_material-switch_build-steel-to-timber", col_out = "ind_material-switch_build_steel_timber", dim = "Variables")
    
dm_ind.rename_col_regex("cars", "LDV", dim = "Variables")
dm_ind.rename_col_regex("trucks", "HDVL", dim = "Variables")

dm_ind.rename_col(col_in = "ind_proportion_aluminium_prim", col_out = "ind_proportion_aluminium_primary", dim = "Variables")
dm_ind.rename_col(col_in = "ind_proportion_aluminium_sec", col_out = "ind_proportion_aluminium_secondary", dim = "Variables")
dm_ind.rename_col(col_in = "ind_proportion_copper_tech", col_out = "ind_proportion_copper_secondary", dim = "Variables")

dm_ind.rename_col(col_in = "ind_product-net-import_new_dhg_pipe", col_out = "ind_product-net-import_infra-pipe", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_road", col_out = "ind_product-net-import_infra-road", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_rail", col_out = "ind_product-net-import_infra-rail", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_trolley-cables", col_out = "ind_product-net-import_infra-trolley-cables", dim = "Variables")

dm_ind.rename_col(col_in = "ind_product-net-import_fridge", col_out = "ind_product-net-import_dom-appliance-fridge", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_dishwasher", col_out = "ind_product-net-import_dom-appliance-dishwasher", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_wmachine", col_out = "ind_product-net-import_dom-appliance-wmachine", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_freezer", col_out = "ind_product-net-import_dom-appliance-freezer", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_dryer", col_out = "ind_product-net-import_dom-appliance-dryer", dim = "Variables")

dm_ind.rename_col(col_in = "ind_product-net-import_ships", col_out = "ind_product-net-import_other-ships", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_trains", col_out = "ind_product-net-import_other-trains", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_planes", col_out = "ind_product-net-import_other-planes", dim = "Variables")

dm_ind.rename_col(col_in = "ind_product-net-import_tv", col_out = "ind_product-net-import_electronics-tv", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_phone", col_out = "ind_product-net-import_electronics-phone", dim = "Variables")
dm_ind.rename_col(col_in = "ind_product-net-import_computer", col_out = "ind_product-net-import_electronics-computer", dim = "Variables")

dm_ind.rename_col(col_in = "ind_material-production_glass", col_out = "min_tot_dir_glass", dim = "Variables")

# mimerals other fxa
dm_min_other.drop("Variables", col_label = "min_other_lithium.*")

# transport
dm_tra = DM_interface["transport"].copy()
dm_tra.rename_col(col_in = "tra_ships", col_out = "tra_other-ships", dim = "Variables")
dm_tra.rename_col(col_in = "tra_planes", col_out = "tra_other-planes", dim = "Variables")
dm_tra.rename_col(col_in = "tra_trains", col_out = "tra_other-trains", dim = "Variables")
dm_tra.rename_col(col_in = "tra_subways", col_out = "tra_other-subways", dim = "Variables")
dm_tra.rename_col(col_in = "tra_road", col_out = "tra_infra-road", dim = "Variables")
dm_tra.rename_col(col_in = "tra_rail", col_out = "tra_infra-rail", dim = "Variables")
dm_tra.rename_col(col_in = "tra_trolley-cables", col_out = "tra_infra-trolley-cables", dim = "Variables")
dm_tra.rename_col_regex("_ICE", "-ICE", dim = "Variables")
dm_tra.rename_col_regex("_PHEV", "-PHEV", dim = "Variables")
dm_tra.rename_col_regex("_EV", "-EV", dim = "Variables")
dm_tra.rename_col_regex("_EV", "-EV", dim = "Variables")
dm_tra.rename_col_regex("_FCEV", "-FCEV", dim = "Variables")
for i in dm_tra.units.keys():
    if dm_tra.units[i] == "number":
        dm_tra.units[i] = "num"
        
# fossil
dm_fossil = DM_interface["oil-refinery"].copy()
dm_fossil.rename_col(col_in = "fos_primary-demand_gas", col_out = "min_energy_gas", dim = "Variables")
dm_fossil.rename_col(col_in = "fos_primary-demand_oil", col_out = "min_energy_oil", dim = "Variables")
dm_fossil.rename_col(col_in = "fos_primary-demand_coal", col_out = "min_energy_coal", dim = "Variables")

# ccus
dm_ccus = DM_interface["ccus"].copy()
dm_ccus.rename_col(col_in = "ccu_ccus_gas-ff-natural", col_out = "min_ccus_gas", dim = "Variables")

# agriculture
dm_agr = DM_interface["agriculture"].copy()
dm_agr.rename_col_regex("agr_demand", "min_agr", dim = "Variables")

# buildings
dm_bld = DM_interface["buildings"].copy()
dm_bld.rename_col_regex("bld_appliance-new_", "tra_dom-appliance_", dim = "Variables")
dm_bld.rename_col(col_in = "tra_dom-appliance_tv", col_out = "tra_electronics-tv", dim = "Variables")
dm_bld.rename_col(col_in = "tra_dom-appliance_comp", col_out = "tra_electronics-computer", dim = "Variables")
dm_bld.rename_col(col_in = "tra_dom-appliance_phone", col_out = "tra_electronics-phone", dim = "Variables")
dm_bld.rename_col(col_in = "bld_district-heating_new-pipe-need", col_out = "tra_infra-pipe", dim = "Variables")

# electricity fxa
dm_elec_new.rename_col_regex("elc_new_RES", "elc_OTS", dim = "Variables")
dm_elec_new.rename_col_regex("elc_new_fossil", "elc_OTS", dim = "Variables")
dm_elec_new.rename_col_regex("_tech", "", dim = "Variables")

# clean
del drop, i, newname, oldname


##################
##### FORMAT #####
##################

# get elc_new-capacity_RES_pv
pvroof = col_names_search(dm_str, "pvroof")
pvutiliy = col_names_search(dm_str, "pvutility")
dm_str.operation(pvroof, "+", pvutiliy, dim = "Variables", out_col="elc_FTS_pv", unit="GW", div0="error")
dm_str.drop("Variables", col_label = pvroof + "|" + pvutiliy)

# get elc_new by putting together OTS and FTS by energy source

# apppend
dm_str.append(dm_elec_new, dim='Variables')
dm_str.deepen()

# sum
dm_str.operation('elc_FTS', '+', 'elc_OTS', dim="Variables", out_col='elc_energy', unit='GW', div0="error")
# !FIXME: here for OTS we have 9 sources while for FTS we have 11 ... we should add the 2 missing for OTS

# convert fossil from TWh to Mt
idx = dm_fossil.idx
gas, coal, oil = col_names_search(dm_fossil, "gas"), col_names_search(dm_fossil, "coal"), col_names_search(dm_fossil, "oil")

dm_fossil.array[:,:,idx[gas]] = dm_fossil.array[:,:,idx[gas]] * 0.076
dm_fossil.units[gas] = "Mt"

dm_fossil.array[:,:,idx[coal]] = dm_fossil.array[:,:,idx[coal]] * 0.123
dm_fossil.units[coal] = "Mt"

dm_fossil.array[:,:,idx[oil]] = dm_fossil.array[:,:,idx[oil]] * 0.086
dm_fossil.units[oil] = "Mt"

del idx, gas, coal, oil

# get overall phosphate and potash
idx_agr = dm_agr.idx
idx_oth = dm_min_other.idx
tmp_pho = dm_agr.array[:,:,idx_agr[col_names_search(dm_agr, "phosphate")]] + \
          dm_min_other.array[:,:,idx_oth[col_names_search(dm_min_other, "phosphate")]]
tmp_pot = dm_agr.array[:,:,idx_agr[col_names_search(dm_agr, "potash")]] + \
          dm_min_other.array[:,:,idx_oth[col_names_search(dm_min_other, "potash")]]
dm_agr.add(tmp_pho, dim="Variables", col_label="min_extraction_phosphate", unit="Mt")
dm_agr.add(tmp_pot, dim="Variables", col_label="min_extraction_potash", unit="Mt")
del tmp_pho, tmp_pot, idx_agr, idx_oth

# get bioenergy wood total
dm_agr.operation(col_names_search(dm_agr, "liquid"), '+', col_names_search(dm_agr, "solid"), 
                     dim="Variables", out_col='min_bioenergy_wood', unit='Mt', div0="error")

# get glass sand
idx = dm_ind.idx
ind_glass_sand = dm_ind.array[:,:,idx[col_names_search(dm_ind, "glass")]] * 1.9 / 2.4
dm_ind.add(ind_glass_sand, dim="Variables", col_label="ind_material-production_glass_sand", unit="Mt")
del idx, ind_glass_sand

# make 2020 as mean of before and after for subways, planes, ships, trains
idx = dm_tra.idx
variabs = [col_names_search(dm_tra, "subways"),col_names_search(dm_tra, "planes"),col_names_search(dm_tra, "ships"),col_names_search(dm_tra, "trains")]
for i in variabs:
    dm_tra.array[:,idx[2020],idx[i]] = (dm_tra.array[:,idx[2015],idx[i]] + \
                                        dm_tra.array[:,idx[2025],idx[i]])/2
del idx, variabs

# avoid negative values for gas
# in the ambitious pathway, the supply of ccus (which include biogas) is more than the demand for gaz leading
# to gas demand being negative. The following operation serves to correct this difference by substracting
# the negative gas demand by the over supply of ccus.
idx_fossil = dm_fossil.idx
idx_ccus = dm_ccus.idx
# =============================================================================
# e = dm_fossil.array[:,:,idx["min_energy_gas"]] < 0
# e.shape
# np.all(e == False)
# =============================================================================
ccus_gas = col_names_search(dm_ccus, "ccus_gas")
fossil_gas = col_names_search(dm_fossil, "gas")
dm_ccus.array[:,:,idx_ccus[ccus_gas]][dm_fossil.array[:,:,idx_fossil[fossil_gas]] < 0] = \
    dm_ccus.array[:,:,idx_ccus[ccus_gas]][dm_fossil.array[:,:,idx_fossil[fossil_gas]] < 0] + \
    dm_fossil.array[:,:,idx_fossil[fossil_gas]][dm_fossil.array[:,:,idx_fossil[fossil_gas]] < 0]
# !FIXME: the code in knime is output_table['min_ccus_gas[Mt]'][input_table['min_energy_gas[Mt]']< 0] = input_table['min_ccus_gas[Mt]'] + input_table['min_energy_gas[Mt]'] though this does not make much sense in terms of dimensions ...
# for the moment I have put here a code that should be fine dimension wise, to be understood later how to correct this
del idx_fossil, idx_ccus, ccus_gas, fossil_gas

# clean
del i, pvroof, pvutiliy

####################################################################################
#################### INDIRECT DEMAND, NET EXPORT, DIRECT DEMAND ####################
####################################################################################

# add net imports for categories of vehicles we do not have
variabs = ["LDV-ICE", "HDVL-ICE", "trains",
           "LDV-ICE","LDV-ICE","LDV-ICE","LDV-ICE",
           "HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE",
           "HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE",
           "HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE"]
variabs = [col_names_search(dm_ind, i) for i in variabs]
variabs_new = ["LDV-PHEV","HDVL-PHEV","subways",
               "2W-EV","2W-ICE","2W-FCEV","2W-PHEV",
               "bus-EV","bus-ICE","bus-FCEV","bus-PHEV",
               "HDVM-EV","HDVM-ICE","HDVM-FCEV","HDVM-PHEV",
               "HDVH-EV","HDVH-ICE","HDVH-FCEV","HDVH-PHEV"]
prefix = variabs[0].split("LDV-ICE")[0]
variabs_new = [prefix + i for i in variabs_new]

idx = dm_ind.idx
for i in range(len(variabs)):
    dm_ind.add(dm_ind.array[:,:,idx[variabs[i]]], dim="Variables", col_label=variabs_new[i], unit="%")

# get product indirect demand share
variabs = dm_ind.col_labels["Variables"].copy()
for i in range(len(variabs)):
    if bool(re.search(prefix, variabs[i])):
        col_in = variabs[i]
        col_out = variabs[i].replace(prefix, "min_trade_") + "_indir"
        dm_ind.rename_col(col_in, col_out, dim = "Variables")

# get product net export share
variabs = np.array(dm_ind.col_labels["Variables"].copy())
variabs = variabs[[bool(re.search("min_trade_", str(i), flags=re.IGNORECASE)) for i in variabs]]
for i in variabs:
    col_new = i.replace("_indir", "_exp")
    dm_ind.add(-dm_ind.array[:,:,idx[i]], dim="Variables", col_label=col_new, unit="%")
    
# get product direct demand share
for i in variabs:
    col_new = i.replace("_indir", "_dir")
    dm_ind.add(dm_ind.array[:,:,idx[i]]-dm_ind.array[:,:,idx[i]]+1, dim="Variables", col_label=col_new, unit="%")
    
# clean
del col_in, col_new, col_out, i, idx, prefix, variabs, variabs_new


################################################################################
########## CAPACITY FOR BATTERIES INSIDE EVS, ELECTRONICS AND STORAGE ##########
################################################################################

# get subset of constants and deepen
variabs_const = col_names_search(cdm_constants, "batveh")
cdm_temp = cdm_constants.filter(selected_cols={"Variables": variabs_const}).copy()
cdm_temp.deepen()

# get subset of number of transport by mode
variabs = [i[1] for i in [i.split("batveh_") for i in variabs_const]]
variabs_tra = [col_names_search(dm_tra, i) for i in variabs]
variabs_tra = list(filter(None, variabs_tra))
dm_temp = dm_tra.filter(selected_cols={"Variables": variabs_tra}).copy()

# get subset of number of electronics (computers and phones)
variabs_bld = [col_names_search(dm_bld, i) for i in variabs]
variabs_bld = list(filter(None, variabs_bld))
dm_temp2 = dm_bld.filter(selected_cols={"Variables": variabs_bld}).copy()

# put together and deepen
dm_temp.append(dm_temp2, dim='Variables')
dm_temp.deepen()

# mutliply num * constant to get battery capacity by product and add in dm
arr_temp = dm_temp.array * cdm_temp.array[np.newaxis,np.newaxis,...]
dm_temp.add(arr_temp, dim='Variables', col_label='tra_energy-battery', unit = "kWh")

# sum all products to get the total demand (in capacity) of batteries in EVs and in electronics [kWh]
dic_temp = {"tra_transport-battery": variabs_tra, 
            "tra_electronics-battery": variabs_bld}
for key in dic_temp.keys():
    
    # get variables
    variabs_temp = [i[1] for i in [i.split("tra_") for i in dic_temp[key]]]
    
    # subset dm
    dm_battery_temp = dm_temp.filter(selected_cols={"Categories1": variabs_temp}).copy()
    
    # get array with sum
    idx = dm_battery_temp.idx
    arr_battery_temp = np.nansum(dm_battery_temp.array[:,:,idx["tra_energy-battery"],:], axis=-1)
    
    # add the array to dm_str_battery
    dm_str_battery.add(arr_battery_temp, dim='Variables', col_label=key, unit = "kWh")

del arr_battery_temp, arr_temp, cdm_temp, dic_temp, dm_temp, idx, key, variabs, \
    variabs_bld, variabs_const, variabs_temp, variabs_tra












