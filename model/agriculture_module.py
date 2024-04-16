import pandas as pd

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data
import pickle
import json
import os
import numpy as np
import time

__file__ = "/Users/crosnier/Documents/PathwayCalc/training/transport_module_notebook.py"

#######################################################################################################
######################################### LOAD AGRICULTURE DATA #########################################
#######################################################################################################

#############################################
##### database_from_csv_to_datamatrix() #####
#############################################

# Description: this chunk of code makes the pickle with all the datamatrixes inside. In transport_module.py is defined as a function
# without arguments. This function runs the code and saves the pickle (it will not be used as a function later on).
# Using a function without arguments is just a way to embed in a function a piece of code that needs to run.

# Read database
file = 'agriculture_fixed-assumptions'
lever = 'fixed-assumption'
#edit_database(file, lever, column='eucalc-name', mode='rename',pattern={'meat_': 'meat-', 'abp_': 'abp-'})

# Create dm for relevant fxa categories
# Read fixed assumptions & create dict_fxa
dict_fxa = {}
# this is just a dataframe of zeros
# df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_CO2-factors-GHG'})

# Food demand to domestic production

df = read_database_fxa(file, filter_dict={'eucalc-name': 'agr_food-net-import_pro'})
#dm_food_net_import = DataMatrix.create_from_df(df, num_cat=1)
#dict_fxa['food_net_import_pro'] = dm_food_net_import

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

#####################
###### LEVERS #######
#####################

dict_ots = {}
dict_fts = {}

# Read input from lifestyle : food waste & diet
current_file_directory = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-agriculture.xlsx")
df = pd.read_excel(f, sheet_name="default")
dm_lfs = DataMatrix.create_from_df(df, num_cat=1)

# Read self-sufficiency
file = 'agriculture_self-sufficiency'
lever = 'food-net-import'
# Rename to correct format
edit_database(file,lever,column='eucalc-name',pattern={'processeced':'processed'},mode='rename')
edit_database(file,lever,column='eucalc-name',pattern={'meat_':'meat-', 'abp_':'abp-', 'processed_':'processed-', 'pro_':'pro-','liv_':'liv-','crop_':'crop-','bev_':'bev-'},mode='rename')
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)


#####################
# CALCULATION TREE  #
#####################

# FOOD DEMAND TO DOMESTIC FOOD PRODUCTION ------------------------------------------------------------------------------
# Overall food demand [kcal] = food demand [kcal] + food waste [kcal]
dm_lfs.operation('lfs_diet', '+', 'lfs_food-wastes', out_col='agr_demand', unit='kcal')
# other way to do the step before but does not add it to the dm
#idx = dm_lfs.idx
#overall_food_demand = dm_lfs.array[:,:,idx['lfs_diet'],:] + dm_lfs.array[:,:,idx['lfs_food-wastes'],:]


# Renaming to correct format to match iterators (simultaneously changes in lfs_diet, lfs_fwaste and agr_demand)
# Adding meat prefix
pro_liv_meat = ['bov', 'sheep', 'pigs', 'poultry', 'oth-animals']
for cat in pro_liv_meat:
    new_cat = 'pro-liv-meat-'+cat
    dm_lfs.rename_col(cat, new_cat, dim='Categories1')

# Adding bev prefix
pro_bev = ['beer', 'bev-fer', 'bev-alc', 'wine']
for cat in pro_bev:
    new_cat = 'pro-bev-' + cat
    dm_lfs.rename_col(cat, new_cat, dim='Categories1')

# Adding crop prefix
crop = ['cereals', 'oilcrops', 'pulses', 'starch', 'fruits', 'veg']
for cat in crop:
    new_cat = 'pro-crop-' + cat
    dm_lfs.rename_col(cat, new_cat, dim='Categories1')
# Dropping the -s at the end of cereals, oilcrops, pulses, fruits ??
######

# Adding crop processed prefix
processed = ['voil', 'sweet', 'sugar', 'afats', 'offal']
for cat in processed:
    new_cat = 'pro-crop-processed-' + cat
    dm_lfs.rename_col(cat, new_cat, dim='Categories1')

# Domestic production [kcal] = agr_demand [kcal] * net-imports [%] (processed food)
# Filtering dms to only keep pro

# idx = dm_lfs.idx
# overall_food_demand = dm_lfs.array[:,:,idx['lfs_diet'],:] + dm_lfs.array[:,:,idx['lfs_food-wastes'],:]

print('hello') # list: the 3 dimensions, i.e. country, years and variables
