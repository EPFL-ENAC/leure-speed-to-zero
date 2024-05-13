#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 12 10:37:22 2024

@author: echiarot
"""

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_database_to_ots_fts_dict, read_level_data
import pandas as pd
import pickle
import json
import os
import numpy as np
import re
import warnings
warnings.simplefilter("ignore")

__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/training/minerals_module_notebook.py"


############################################################
#################### CREATE DATA PICKLE ####################
############################################################

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

#############################
##### FIXED ASSUMPTIONS #####
#############################

# Read fixed assumptions to datamatrix
df = read_database_fxa('industry_fixed-assumptions') # weird warning as there seems to be no repeated lines
dm = DataMatrix.create_from_df(df, num_cat=0)

# df[df.duplicated()]
# A = pd.DataFrame({'isin' : df.groupby('Country')['amm_liquid-ff-oil_diesel[%]'].agg(len).index, 
#                    'variab' : df.groupby('Country')['amm_liquid-ff-oil_diesel[%]'].agg(len).values
#                   })
# A = A[A['variab']>33]

# Keep only ots and fts years
dm = dm.filter(selected_cols={'Years': years_all})

# save
dm_liquid = dm.filter({"Variables" : ['amm_liquid-ff-oil_diesel', 'amm_liquid-ff-oil_fuel-oil', 
                                      'ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
dm_prod = dm.filter({"Variables" : ['ind_prod_fbt', 'ind_prod_mae', 'ind_prod_ois', 'ind_prod_textiles', 
                                    'ind_prod_tra-equip', 'ind_prod_wwp']})

dict_fxa = {
    'liquid': dm_liquid,
    'prod': dm_prod,
}

##################
##### LEVERS #####
##################

dict_ots = {}
dict_fts = {}

# levers = ["material-switch","material-efficiency","technology-share",
#           "technology-development","material-net-import","product-net-import",
#           "energy-carrier-mix","carbon-capture"]
# files = ["industry_" + i for i in levers]

# # material switch
# for i in range(len(levers)):
#     file = files[i]
#     lever = levers[i]
#     dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# material switch
file = 'industry_material-switch'
lever = 'material-switch'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# material efficiency
file = 'industry_material-efficiency'
lever = "material-efficiency"
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # carbon capture (run just once, delete this chunk the end)
# filename = 'industry_cc'
# filename = filename.replace('.csv', '')  # drop .csv extension
# current_file_directory = os.path.dirname(os.path.abspath(__file__))
# folderpath = os.path.join(current_file_directory, "../_database/data/csv/")
# file = folderpath + filename + '.csv'
# df_db = pd.read_csv(file, sep=";")
# variables = ["eucalc-name","lever","item","interaction-file"]
# for v in variables:
#     df_db[v] = [df_db[v][i].replace("CC","cc") for i in range(len(df_db))]
# df_db.to_csv(file, sep=";", index=False)

# technology share, technology development and carbon capture (CC)
levers = ["technology-share", "technology-development", "cc"]
for lever in levers:
    
    # get ots and fts
    file = 'industry_' + lever
    df_ots, df_fts = read_database(file, lever, level='all')
    
    # get current variables names
    variabs = df_ots.columns
    variabs_ots_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
    variabs = df_fts.columns
    variabs_fts_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
    
    # after prefix, substitute _ with -
    variabs = [i.split(lever + '_')[1] for i in variabs_ots_old]
    variabs = [i.replace("_","-") for i in variabs]
    
    # rename variables
    variabs_ots_new = ["ots_ind_" + lever + "_" + i for i in variabs]
    variabs_fts_new = ["fts_ind_" + lever + "_" + i for i in variabs]
    for i in range(len(variabs_ots_new)):
        df_ots.rename(columns={variabs_ots_old[i]: variabs_ots_new[i]}, inplace=True)
        df_fts.rename(columns={variabs_fts_old[i]: variabs_fts_new[i]}, inplace=True)
    
    # load
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                       df_ots=df_ots, df_fts=df_fts)

# material net import
file = 'industry_material-net-import'
lever = "material-net-import"
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# product net import
file = 'industry_product-net-import'
lever = "product-net-import"
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# energy carrier mix import
file = 'industry_energy-carrier-mix'
lever = "energy-carrier-mix"
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

#######################
##### CALIBRATION #####
#######################

# Read calibration
df = read_database_fxa('industry_calibration')
dm_cal = DataMatrix.create_from_df(df, num_cat=0)

################
##### SAVE #####
################

DM_industry = {
    'fxa': dict_fxa,
    'fts': dict_fts,
    'ots': dict_ots,
    'cal': dm_cal
}

current_file_directory = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(current_file_directory, '../_database/data/datamatrix/industry.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_industry, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
# clean
del baseyear, df, df_fts, df_ots, dict_fts, dict_fxa, dict_ots, dm, dm_cal, DM_industry,\
    dm_liquid, dm_prod, f, file, handle, i, lastyear, lever, levers, startyear, step_fts, variabs, variabs_fts_old,\
    variabs_fts_new, variabs_ots_new, variabs_ots_old, years_all, years_fts, years_ots, years_setting


###################################################
#################### READ DATA ####################
###################################################

# industry data file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/industry.pickle')

# lever setting
f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
lever_setting = json.load(f)[0]

# load dm
with open(data_file, 'rb') as handle:
    DM_industry = pickle.load(handle)

# get fxa
DM_fxa = DM_industry['fxa']

# Get ots fts based on lever_setting
DM_ots_fts = read_level_data(DM_industry, lever_setting)

# get calibration
dm_cal = DM_industry['cal']

# clean
del handle, f, DM_industry


#############################################################
#################### SIMULATE INTERFACES ####################
#############################################################

# empty dict
DM_interface = {}

# files' names
current_file_directory = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(current_file_directory, "../_database/data/xls")
files = np.array(os.listdir(f))
files = files[[bool(re.search("industry", str(i), flags=re.IGNORECASE)) for i in files]]
files = files[[not bool(re.search("tpe", str(i), flags=re.IGNORECASE)) for i in files]].tolist()
keys = [i.split("from-")[1].split("-to")[0] for i in files]

# get files
for i in range(len(files)):
    
    f = os.path.join(current_file_directory, "../_database/data/xls/" + files[i])
    df = pd.read_excel(f)
    dm = DataMatrix.create_from_df(df, num_cat=0)
    DM_interface[keys[i]] = dm






