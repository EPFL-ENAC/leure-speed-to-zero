#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 10:37:30 2024

@author: echiarot
"""

# %reset

import pandas as pd

# in Spyder, go to PYTHONPATH manager and put the directory containing all files (for me is /Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc)
# in Jupyter, this should work automatically
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale, read_level_data
from training.common.transport_auxiliary_functions import compute_fts_tech_split, add_biofuel_efuel, rename_and_group
import pickle
import json
import os
import numpy as np

__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/training/transport_module_notebook.py"

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
df = read_database_fxa('transport_fixed-assumptions')
dm = DataMatrix.create_from_df(df, num_cat=0) # this is a 3 dimensional arrays for the fixed assumptions in transport

# explore dm

print(dm.dim_labels) # list: the 3 dimensions, i.e. country, years and variables
print(dm.col_labels) # dictionary: the columns in each dimension
print(dm.idx) # dictionary: the indexes assigned to coilumns in each of the 3 dimensions
print(dm.units) # dictionary: the units of columns in each of the 3 dimensions
print(dm.array) # array: the data
print(dm.array.shape) # this is the size of the array (32 countries for 33 years for 139 variables)

# Austria 1990 'tra_freight_length_rails'
dm.array[0,0,0]
idx = dm.idx
dm.array[(idx['Austria'],idx['France']), idx[1990], idx["tra_freight_length_rails"]] # yes

# tra_freight_length_rails for all countries and years. The output is a matrix with countries for rows (32) and years for columns (33)
dm.array[:,:,idx["tra_freight_length_rails"]]
dm.array[:,:,0].shape

# =============================================================================
# def show_value(dm, dict_dim_pattern):
# 
#     # get boolean indexes for dm
#     idx_bool = list()
#     for d in dm.dim_labels:
#         label = dict_dim_pattern[d]
#         idx_label = [dm.col_labels[d][i] == label for i in range(len(dm.col_labels[d]))]
#         idx_bool.append(idx_label)
#         
#     # get value
#     output = float(dm.array[idx_bool[0],idx_bool[1], idx_bool[2]])
#     
#     # return output
#     return(output)
# show_value(dm = dm, dict_dim_pattern = {'Country':'Austria','Years':1990,'Variables':'tra_freight_length_rails'}) # yes
# =============================================================================

# Keep only ots and fts years
dm = dm.filter(selected_cols={'Years': years_all})
dm.array.shape

# make data matrixes with specific data using regular expression (regex)
dm_freight_tech = dm.filter_w_regex({'Variables': 'tra_freight_technology-share.*|tra_freight_vehicle-efficiency.*'})
dm_passenger_tech = dm.filter_w_regex({'Variables': 'tra_passenger_technology-share.*|tra_passenger_veh-efficiency_fleet.*'})
dm_passenger_mode_road = dm.filter_w_regex({'Variables': 'tra_passenger_vehicle-lifetime.*'})
dm_passenger_mode_other = dm.filter_w_regex({'Variables': 'tra_passenger_avg-pkm-by-veh.*|tra_passenger_renewal-rate.*'})
dm_freight_mode_other = dm.filter_w_regex({'Variables': 'tra_freight_tkm-by-veh.*|tra_freight_renewal-rate.*'})
dm_freight_mode_road = dm.filter_w_regex({'Variables': 'tra_freight_lifetime.*'})

# Add metrotram to passenger_tech
metrotram_tech = np.ones((dm_passenger_tech.array.shape[0], dm_passenger_tech.array.shape[1]))
metrotram_tech.shape # array 32 by 33 (rows are for countries and cols are for years)
dm_passenger_tech.add(metrotram_tech, dim="Variables", col_label='tra_passenger_technology-share_fleet_metrotram_mt', unit='%')
dm_passenger_tech.rename_col(col_in='tra_passenger_veh-efficiency_fleet_metrotram',
                             col_out='tra_passenger_veh-efficiency_fleet_metrotram_mt', dim='Variables')
dm_passenger_tech.col_labels["Variables"] # check variables names ... personal note: the row above is useless in theory and can be dropped

# Add dimensions
dm_freight_tech.array.shape # array: (32 x 33 x 68)
dm_freight_tech.col_labels["Variables"]
dm_freight_tech.deepen_twice()
dm_freight_tech.array.shape # array: (32 x 33 x 2 x 7 x 9)
dm_freight_tech.col_labels # so this is the same datamatrix, just we have split the variables in subsets following their names
idx = dm_freight_tech.idx
dm_freight_tech.array[idx["Austria"],idx[1990],idx["tra_freight_vehicle-efficiency_fleet"],
                      idx["HDVH"], idx["PHEV-diesel"]] # this is the value for austria 1990 for the variable tra_freight_vehicle-efficiency_fleet_HDVH_PHEV-diesel

dm_passenger_tech.deepen_twice()
dm_passenger_mode_road.deepen()
dm_passenger_mode_other.deepen()
dm_freight_mode_other.deepen()
dm_freight_mode_road.deepen()

dict_fxa = {
    'freight_tech': dm_freight_tech,
    'passenger_tech': dm_passenger_tech,
    'passenger_mode_road': dm_passenger_mode_road,
    'passenger_mode_other': dm_passenger_mode_other,
    'freight_mode_other': dm_freight_mode_other,
    'freight_mode_road': dm_freight_mode_road
}

##########
# LEVERS #
##########

dict_ots = {}
dict_fts = {}

# Read passenger levers
file = 'transport_passenger-aviation-pkm'
lever = 'passenger-aviation-pkm'
# dm_passenger_aviation
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

type(dict_ots["passenger-aviation-pkm"]) # datamatrix put inside a dictionary for original time series
dict_ots["passenger-aviation-pkm"].array.shape # (32, 26, 1, 1)
dict_ots["passenger-aviation-pkm"].dim_labels # ['Country', 'Years', 'Variables', 'Categories1'], here there is already categories1 as we have specified that in read_database_to_ots_fts_dict()


# Read passenger efficiency
file = 'transport_passenger-efficiency'
lever = 'passenger_veh-efficiency_new'
df_ots, df_fts = read_database(file, lever, level='all')
df_ots.columns = df_ots.columns.str.replace('MJ/pkm', 'MJ/km')
df_fts.columns = df_fts.columns.str.replace('MJ/pkm', 'MJ/km')
df_ots.columns = df_ots.columns.str.replace('metrotram', 'metrotram_mt')
df_fts.columns = df_fts.columns.str.replace('metrotram', 'metrotram_mt')
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts) # here you have 2 categories ... and note that we are adding this new databases in the dictionaries, and we will do this for any new database

# Read passenger modal split urban rural
file = 'transport_passenger-modal-split'
lever = 'passenger_modal-share'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# Read passenger occupancy
file = 'transport_passenger-occupancy'
lever = 'passenger_occupancy'
# dm_passenger_occupancy
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# Read passenger technology split
file = 'transport_passenger-technology-split'
lever = 'passenger_technology-share_new'
df_ots, df_fts = read_database(file, lever, level='all')
df_ots['tra_passenger_technology-share_new_metrotram_mt[%]'] = 1
df_fts['tra_passenger_technology-share_new_metrotram_mt[%]'] = 1
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

# Read passenger use rate
file = 'transport_passenger-use-rate'
lever = 'passenger_utilization-rate'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                   years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# Read freight levers
# Efficiency
file = 'transport_freight-efficiency'
lever = 'freight_vehicle-efficiency_new'
df_ots, df_fts = read_database(file, lever, level='all')
df_ots.columns = df_ots.columns.str.replace('tkm', 'km')
df_fts.columns = df_fts.columns.str.replace('tkm', 'km')
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

# Load factors & utilisation rate
file = 'transport_freight-load-factor'
lever_1 = 'freight_load-factor'
lever = 'freight_utilization-rate'
# there is a problem with the lever name in the original file
# !FIXME this should be merged with freight use-rate
df_ots, df_fts = read_database(file, lever_1, level='all')
df_ots.rename(columns={lever_1: lever}, inplace=True)
df_fts.rename(columns={lever_1: lever}, inplace=True)
df_ots_2, df_fts_2 = read_database('transport_freight-use-rate', lever, level='all')
df_ots = df_ots.merge(df_ots_2, on=['Country', 'Years', lever])
df_fts = df_fts.merge(df_fts_2, on=['Country', 'Years', lever])
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

# Modal split
file = 'transport_freight-modal-split'
lever = 'freight_modal-share'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts)

# Technology split
file = 'transport_freight-technology-split'
lever = 'freight_technology-share_new'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts)

# Volume
file = 'transport_freight-volume'
lever = 'freight_tkm'
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts)

# Read fuel mix for efuel and biofuels
fuels = ['biofuels', 'efuel']
mode = ['marine', 'road', 'aviation']
lever = 'fuel-mix'
i = 0
for f in fuels:
    for m in mode:
        file = 'transport_fuel-mix-' + m + '-' + f
        if f == 'biofuels':
            f = 'biofuel'
        lever_i = 'fuel-mix_' + f + '-' + m
        df_ots_i, df_fts_i = read_database(file, lever_i, level='all')
        df_ots_i.rename(columns={lever_i: lever}, inplace=True)
        df_fts_i.rename(columns={lever_i: lever}, inplace=True)
        df_ots_i.columns = df_ots_i.columns.str.replace('biofuel-', 'biofuel_')
        df_ots_i.columns = df_ots_i.columns.str.replace('efuel-', 'efuel_')
        df_fts_i.columns = df_fts_i.columns.str.replace('biofuel-', 'biofuel_')
        df_fts_i.columns = df_fts_i.columns.str.replace('efuel-', 'efuel_')
        if i == 0:
            df_ots = df_ots_i
            df_fts = df_fts_i
        else:
            df_ots = df_ots.merge(df_ots_i, on=['Country', 'Years', lever])
            df_fts = df_fts.merge(df_fts_i, on=['Country', 'Years', lever])
        if f == 'biofuel':
            f = 'biofuels'
        i = i + 1
dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                   dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

#############
# CONSTANTS #
#############

# Load constants
cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_tra_emission-factor.*', num_cat=2)


########
# SAVE #
########

DM_transport = {
    'fxa': dict_fxa,
    'fts': dict_fts,
    'ots': dict_ots,
    'constant': cdm_const
}

current_file_directory = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(current_file_directory, '../_database/data/datamatrix/transport.pickle')
# data_file_path = wd_path + "/_database/data/datamatrix/transport.pickle"
with open(f, 'wb') as handle:
    pickle.dump(DM_transport, handle, protocol=pickle.HIGHEST_PROTOCOL)


#######################################################################################################
######################################## TRANSPORT CORE MODULE ########################################
#######################################################################################################

# set paths
current_file_directory = os.path.dirname(os.path.abspath(__file__))

##########################################
##### begin of local_transport_run() #####
##########################################

# In transport_module.py, this function runs the function transport(lever_setting, years_setting). This function
# does not have arguments and it is solely used to run code.

# set years
years_setting = [1990, 2015, 2050, 5]

# load lever setting
# f = open('../config/lever_position.json')
lever_setting_file = os.path.join(current_file_directory, '../config/lever_position.json')
f = open(lever_setting_file)
lever_setting = json.load(f)[0]

# # select countries
# global_vars = {'geoscale': 'Switzerland'}
# filter_geoscale(global_vars)

############################################################
##### begin of transport(lever_setting, years_setting) #####
############################################################

# Description: in transport_module.py, this function is used in local_transport_run() to run the transport module.

########################################################
##### begin of read_data(data_file, lever_setting) #####
########################################################

# Description: in transport_module.py, this function is used in transport(lever_setting, years_setting) to read the data in the pickle.

# load datamatrixes
transport_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/transport.pickle')
with open(transport_data_file, 'rb') as handle:
    DM_transport = pickle.load(handle)

# get fixed assumptions
dict_fxa = DM_transport['fxa']
dm_freight_tech = dict_fxa['freight_tech']
dm_passenger_tech = dict_fxa['passenger_tech']
dm_passenger_mode_road = dict_fxa['passenger_mode_road']
dm_passenger_mode_other = dict_fxa['passenger_mode_other']
dm_freight_mode_other = dict_fxa['freight_mode_other']
dm_freight_mode_road = dict_fxa['freight_mode_road']

# Read fts based on lever_setting
DM_ots_fts = read_level_data(DM_transport, lever_setting)


# PASSENGER
dm_passenger_aviation = DM_ots_fts['passenger-aviation-pkm']
dm_passenger_tech.append(DM_ots_fts['passenger_veh-efficiency_new'], dim='Variables')
dm_passenger_tech.append(DM_ots_fts['passenger_technology-share_new'], dim='Variables')
dm_passenger_modal = DM_ots_fts['passenger_modal-share']
dm_passenger_mode_road.append(DM_ots_fts['passenger_occupancy'], dim='Variables')
dm_passenger_mode_road.append(DM_ots_fts['passenger_utilization-rate'], dim='Variables')

# FREIGHT
dm_freight_tech.append(DM_ots_fts['freight_vehicle-efficiency_new'], dim='Variables')
dm_freight_tech.append(DM_ots_fts['freight_technology-share_new'], dim='Variables')
dm_freight_mode_road.append(DM_ots_fts['freight_utilization-rate'], dim='Variables')
dm_freight_modal_share = DM_ots_fts['freight_modal-share']
dm_freight_demand = DM_ots_fts['freight_tkm']

# OTHER
dm_fuels = DM_ots_fts['fuel-mix']

DM_passenger = {
    'passenger_tech': dm_passenger_tech,
    'passenger_mode_other': dm_passenger_mode_other,
    'passenger_aviation': dm_passenger_aviation,
    'passenger_modal_split': dm_passenger_modal,
    'passenger_mode_road': dm_passenger_mode_road
    }

DM_freight = {
    'freight_tech': dm_freight_tech,
    'freight_mode_other': dm_freight_mode_other,
    'freight_mode_road': dm_freight_mode_road,
    'freight_demand': dm_freight_demand,
    'freight_modal_split': dm_freight_modal_share
}

DM_other = {
    'fuels': dm_fuels
}

cdm_const = DM_transport['constant']

#######################################################
##### end of read_data(data_file, lever_setting) ######
#######################################################

# get countries
cntr_list = DM_passenger['passenger_modal_split'].col_labels['Country']


################################################
##### begin of simulate_lifestyles_input() #####
################################################

# Description: in transport_module.py, this function is used in transport(lever_setting, years_setting) to
# make the fake interface data from lifestyle. This function does not have arguments and it is solely used to run code.

# Read input from lifestyle
f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-transport.xlsx")
df = pd.read_excel(f, sheet_name="default")
dm = DataMatrix.create_from_df(df, num_cat=0) # dimensions (32, 33, 3)

# get population and passenger demand
dm_pop = dm.filter_w_regex({'Variables': 'lfs_pop.*'})
dm_passenger_demand = dm.filter_w_regex({'Variables': 'lfs_passenger-travel-demand.*'}) # dimensions (32, 33, 2)
dm_passenger_demand.deepen() # dimensions (32, 33, 1, 2)

# save
DM_lfs = {
    'lfs_pop': dm_pop,
    'lfs_passenger_demand': dm_passenger_demand
}

##############################################
##### end of simulate_lifestyles_input() #####
##############################################

# for lifestyle interfaces, keep only the countries in cntr_list
for key in DM_lfs.keys():
    DM_lfs[key] = DM_lfs[key].filter({'Country': cntr_list})
    
# PASSENGER

# make datamatrix for constants for passenger
cdm_const_passenger = cdm_const.copy()

#####################################################################################################
##### begin of passenger_fleet_energy(DM_passenger, DM_lfs, DM_other, cdm_const, years_setting) #####
#####################################################################################################

# Description: in transport_module.py, this function is used in transport(lever_setting, years_setting) to compute the energy
# demand for the passenger fleet

# Compute pkm demand by mode
# dm_demand_by_mode [pkm] = modal_shares(urban) * demand_pkm(urban) + modal_shares(non-urban) * demand_pkm(non-urban)

# get datamatrixes for modal split and passenger demand
dm_modal_split = DM_passenger['passenger_modal_split']
dm_lfs_demand = DM_lfs['lfs_passenger_demand']

#################################################################################
########## begin of compute_pkm_demand(modal_split, urb_nonurb_demand) ##########
#################################################################################

# Description: in transport_module.py, this function is used in passenger_fleet_energy() to
# make the datamatrix for demand in pkm by multiplying the modal split for urban and non urban
# by the demand from lifestyle.

# rename modal split and lfs demand as function arguments
modal_split = dm_modal_split
urb_nonurb_demand = dm_lfs_demand

# get indexes to index urb_nonurb_demand and modal_split
idx_d = urb_nonurb_demand.idx
idx_m = modal_split.idx

# get the demand in pkm
# multiply values for all countries, years, and variables (just in this case), for non-urban demand with values for all countries, years and variables for nonurban modal split. Do the same for urban.
# Note that we do this manually and not with the operation() function as we are multiplying 2 different arrays (if we multiplied elements of the same array, we could have used operation()).
# Note that urb_nonurb_demand.array[:, :, :, idx_d['non-urban']] would have shape (32, 33, 1), while urb_nonurb_demand.array[:, :, :, idx_d['non-urban'], np.newaxis] allows to have shape (32, 33, 1, 1).
tmp_nonurb = urb_nonurb_demand.array[:, :, :, idx_d['non-urban'], np.newaxis] * \
             modal_split.array[:, :, :, idx_m['nonurban'], :]
tmp_urb = urb_nonurb_demand.array[:, :, :, idx_d['urban'], np.newaxis] * \
          modal_split.array[:, :, :, idx_m['urban'], :]
tmp_demand = tmp_nonurb + tmp_urb

# save the demand in pkm in datamatrix
cols = {
    'Country': modal_split.col_labels['Country'].copy(),
    'Years': modal_split.col_labels['Years'].copy(),
    'Variables': ['tra_passenger_transport-demand'],
    'Categories1': modal_split.col_labels['Categories2'].copy()
}
demand = DataMatrix(col_labels=cols, units={'tra_passenger_transport-demand': 'pkm'})
demand.array = tmp_demand
dm_demand_by_mode = demand

###############################################################################
########## end of compute_pkm_demand(modal_split, urb_nonurb_demand) ##########
###############################################################################

# delete some datamatrices
del dm_modal_split, dm_lfs_demand, modal_split, urb_nonurb_demand, demand

# Remove walking and biking
dm_demand_by_mode.drop(dim='Categories1', col_label='walk|bike')

# Aviation pkm
# demand_aviation [pkm] = demand aviation [pkm/cap] * pop
dm_aviation_pkm = DM_passenger['passenger_aviation']
dm_pop = DM_lfs['lfs_pop']
tmp_aviation = dm_aviation_pkm.array[..., 0] * dm_pop.array[...]
dm_demand_by_mode.add(tmp_aviation, dim='Categories1', col_label='aviation')
del dm_aviation_pkm, tmp_aviation

# Split between road and other passenger transport data
dm_demand_road = dm_demand_by_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'LDV|bus|2W'})
dm_demand_other = dm_demand_by_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'aviation|metrotram|rail'})

dm_road = DM_passenger['passenger_mode_road']
dm_road.append(dm_demand_road, dim='Variables')
del dm_demand_road, dm_demand_by_mode

# demand [vkm] = demand [pkm] / occupancy [pkm/vkm]
dm_road.operation('tra_passenger_transport-demand', '/', 'tra_passenger_occupancy',
                  dim="Variables", out_col='tra_passenger_transport-demand-vkm', unit='vkm', div0="error")
# vehicle-fleet [number] = demand [vkm] / utilisation-rate [vkm/veh/year]
dm_road.operation('tra_passenger_transport-demand-vkm', '/', 'tra_passenger_utilisation-rate',
                  dim="Variables", out_col='tra_passenger_vehicle-fleet', unit='number', div0="error", type=int)
# renewal-rate [%] = utilisation-rate [vkm/veh/year] /  vehicle-lifetime [years]
dm_road.operation('tra_passenger_utilisation-rate', '/', 'tra_passenger_vehicle-lifetime',
                  dim="Variables", out_col='tra_passenger_renewal-rate', unit='%', div0="error")

dm_other = DM_passenger['passenger_mode_other']
dm_other.append(dm_demand_other, dim='Variables')
del dm_demand_other

# vehicle-fleet[number] = demand [pkm] / avg-pkm-by-veh [pkm/veh]
dm_other.operation('tra_passenger_transport-demand', '/', 'tra_passenger_avg-pkm-by-veh',
                   dim="Variables", out_col='tra_passenger_vehicle-fleet', unit='number', div0="error", type=int)

# Compute vehicle waste and new vehicles for both road and other
dm_other_tmp = dm_other.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
dm_mode = dm_road.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
dm_other.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
dm_road.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')

dm_mode.append(dm_other_tmp, dim='Categories1')
del dm_other_tmp

dm_mode.sort(dim='Categories1')
compute_stock(dm_mode, 'tra_passenger_renewal-rate', 'tra_passenger_vehicle-fleet',
              waste_col='tra_passenger_vehicle-waste', new_col='tra_passenger_new-vehicles')

# Compute fleet by technology type
dm_tech = DM_passenger['passenger_tech']
idx_t = dm_tech.index_all()
idx_m = dm_mode.index_all()
tmp_1 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_passenger_vehicle-fleet'], :, np.newaxis]
tmp_2 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_passenger_vehicle-waste'], :, np.newaxis]
tmp_3 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_new'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_passenger_new-vehicles'], :, np.newaxis]
dm_tech.add(tmp_1, col_label='tra_passenger_vehicle-fleet', dim='Variables', unit='number')
dm_tech.add(tmp_2, col_label='tra_passenger_vehicle-waste', dim='Variables', unit='number')
dm_tech.add(tmp_3, col_label='tra_passenger_new-vehicles', dim='Variables', unit='number')
del tmp_1, tmp_2, tmp_3

# compute fts tech split
cols = {
    'renewal-rate': 'tra_passenger_renewal-rate',
    'tot': 'tra_passenger_vehicle-fleet',
    'waste': 'tra_passenger_vehicle-waste',
    'new': 'tra_passenger_new-vehicles',
    'tech_tot': 'tra_passenger_technology-share_fleet',
    'eff_tot': 'tra_passenger_veh-efficiency_fleet',
    'eff_new': 'tra_passenger_veh-efficiency_new'
}

##################################################################################
##### begin of compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting) #####
##################################################################################

# Description: in transport_module.py, this function is used in passenger_fleet_energy() to compute the split
# between fts and tech. Note that compute_fts_tech_split() does not return anything, it just runs the code.

compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting)


################################################################################
##### end of compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting) #####
################################################################################

# Extract passenger transport demand vkm for road and pkm for others, join and compute transport demand by technology
dm_demand_km = dm_road.filter(selected_cols={'Variables': ['tra_passenger_transport-demand-vkm']})
dm_demand_km_other = dm_other.filter(selected_cols={'Variables': ['tra_passenger_transport-demand']})
dm_demand_km_other.units['tra_passenger_transport-demand'] = 'km'
dm_demand_km.units['tra_passenger_transport-demand-vkm'] = 'km'
dm_demand_km.rename_col('tra_passenger_transport-demand-vkm', 'tra_passenger_transport-demand', dim='Variables')
dm_demand_km.append(dm_demand_km_other, dim='Categories1')
dm_demand_km.sort(dim='Categories1')
idx_t = dm_tech.index_all()
tmp = dm_demand_km.array[:, :, 0, :, np.newaxis] \
      * dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], ...]
dm_tech.add(tmp, dim='Variables', col_label='tra_passenger_transport-demand', unit='km')
del tmp, dm_demand_km, dm_demand_km_other
# Compute energy consumption
dm_tech.operation('tra_passenger_veh-efficiency_fleet', '*', 'tra_passenger_transport-demand',
                  out_col='tra_passenger_energy-demand', unit='MJ')

# Add e-fuel and bio-fuel to energy consumption
dm_fuel = DM_other['fuels']
mapping_cat = {'road': ['LDV', '2W', 'rail', 'metrotram', 'bus'], 'aviation': ['aviation']}
dm_energy = dm_tech.filter({'Variables': ['tra_passenger_energy-demand']})

##############################################################################
##### begin of add_biofuel_efuel(dm_energy, dm_fuel_shares, mapping_cat) #####
##############################################################################

# Description: in transport_module.py, this function is used in passenger_fleet_energy() to add biofuel and 
# efuel. Note that add_biofuel_efuel() does not return anything, it just runs the code.

add_biofuel_efuel(dm_energy, dm_fuel, mapping_cat)

############################################################################
##### end of add_biofuel_efuel(dm_energy, dm_fuel_shares, mapping_cat) #####
############################################################################


# Deal with PHEV and electricity. For each mode of transport,
# sum PHEV energy demand and multiply it by 0.1 to obtain a new category, the PHEV_elec
dm_energy_phev = dm_energy.filter_w_regex({'Variables': 'tra_passenger_energy-demand', 'Categories2': 'PHEV.*'})
PHEV_elec = 0.1 * np.nansum(dm_energy_phev.array, axis=-1)
dm_energy.add(PHEV_elec, dim='Categories2', col_label='PHEV-elec')

dm_energy.array = dm_energy.array*0.277778
dm_energy.units['tra_passenger_energy-demand'] = 'TWh'

dict1 = {'FCEV': 'FCV-hydrogen', 'BEV': 'BEV-elec', 'CEV': 'CEV-elec', 'metrotram_mt': 'metrotram_elec',
         'aviation_ICEefuel': 'aviation_ejetfuel', 'aviation_ICEbio': 'aviation_biojetfuel',
         'aviation_ICE': 'aviation_kerosene', 'PHEVbio': 'dieselbio', 'PHEVefuel': 'dieselefuel'}

dm_energy_new_cat = dm_energy.flatten()

# Rename the columns based on the substring mapping
for substring, replacement in dict1.items():
    dm_energy_new_cat.rename_col_regex(substring, replacement, dim='Categories1')
dm_energy_new_cat.rename_col('2W_PHEV', '2W_diesel', dim='Categories1')

grouping = ['dieselbio', 'gasolinebio', 'gasbio', 'gasoline', 'diesel', 'gas', 'dieselefuel', 'gasolineefuel',
            'gasefuel', 'hydrogen', "elec", 'biojetfuel', 'kerosene', 'ejetfuel']
dict2 = {'dieselbio': 'biodiesel', 'gasolinebio': 'bioethanol', 'gasbio': 'biogas', 'dieselefuel': 'ediesel',
         'gasolineefuel': 'egasoline', 'gasefuel': 'egas', 'elec': 'electricity'}

###################################################################################################
##### begin of rename_and_group(dm_new_cat, groups, dict_end, grouped_var='tra_total-energy') #####
###################################################################################################

# Description: in transport_module.py, this function is used in passenger_fleet_energy() to rename and group
# the total energy demand for passenger fleet

dm_tot_energy = rename_and_group(dm_energy_new_cat, grouping, dict2, grouped_var='tra_passenger_total-energy')


#################################################################################################
##### end of rename_and_group(dm_new_cat, groups, dict_end, grouped_var='tra_total-energy') #####
#################################################################################################

# Compute emission by fuel

# Filter fuels for which we have emissions
cdm_const.drop(col_label='marinefueloil', dim='Categories2')
dm_energy_em = dm_tot_energy.filter({'Categories1': cdm_const.col_labels['Categories2']})

# Sort categories to make sure they match
dm_energy_em.sort(dim='Categories1')
cdm_const.sort(dim='Categories2')
idx_e = dm_energy_em.idx
idx_c = cdm_const.idx

# emissions = energy * emission-factor
tmp = dm_energy_em.array[:, :, idx_e['tra_passenger_total-energy'], np.newaxis, :] \
      * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], :, :]
tmp = np.moveaxis(tmp, -2, -1)

# Save emissions by fuel in a datamatrix
col_labels = dm_energy_em.col_labels.copy()
col_labels['Variables'] = ['tra_passenger_emissions']
col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
unit = {'tra_passenger_emissions': 'Mt'}
dm_emissions_by_fuel = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_fuel.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
del dm_energy_em, tmp, col_labels, unit

# Compute emissions by mode
dm_energy_em = dm_energy_new_cat.filter({'Categories3': cdm_const.col_labels['Categories2']})
dm_energy_em.sort(dim='Categories3')
cdm_const.sort(dim='Categories2')
idx_e = dm_energy_em.idx
idx_c = cdm_const.idx
tmp_en = np.nansum(dm_energy_em.array, axis=-2)  # remove technology split
tmp = tmp_en[:, :, idx_e['tra_passenger_energy-demand'], :, np.newaxis, :] \
      * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], np.newaxis, :, :]
tmp = np.nansum(tmp, axis=-1)  # Remove split by fuel
col_labels = dm_energy_em.col_labels.copy()
col_labels.pop('Categories3')
col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
col_labels['Variables'] = ['tra_passenger_emissions']
unit = {'tra_passenger_emissions': 'Mt'}
dm_emissions_by_mode = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_mode.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
del tmp, unit, col_labels, idx_e, idx_c, tmp_en, dm_energy_em

# Group emissions by GHG gas
tmp = np.nansum(dm_emissions_by_mode.array, axis=-2)
col_labels = dm_emissions_by_mode.col_labels.copy()
col_labels['Categories1'] = col_labels['Categories2'].copy()
col_labels.pop('Categories2')
unit = dm_emissions_by_mode.units
dm_emissions_by_GHG = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_GHG.array = tmp[:, :, np.newaxis, :]
del tmp, unit, col_labels

tmp = np.nansum(dm_energy.array, axis=(-1,-2))
col_labels = dm_energy.col_labels.copy()
col_labels.pop('Categories1')
col_labels.pop('Categories2')
dm_no_cat = DataMatrix(col_labels=col_labels, units=dm_energy.units.copy())
dm_no_cat.array = tmp[:, :, np.newaxis]

dm_tech.rename_col('tra_passenger_technology-share_fleet', 'tra_passenger_technology-share-fleet', dim='Variables')

idx = dm_tech.idx
tmp = np.nansum(dm_tech.array[:, :, idx['tra_passenger_transport-demand'], :, :], axis=-1)
dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_transport-demand-by-mode', unit='pkm')

# Compute passenger demand by mode
idx = dm_energy.idx
tmp = np.nansum(dm_energy.array[:, :, idx['tra_passenger_energy-demand'], :, :], axis=-1)
dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_energy-demand-by-mode', unit='TWh')

# Compute CO2 emissions by mode
idx = dm_emissions_by_mode.idx
tmp = dm_emissions_by_mode.array[:, :, idx['tra_passenger_emissions'], :, idx['CO2']]
dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_emissions-by-mode_CO2', unit='Mt')

dm_tot_energy.rename_col(col_in='tra_passenger_total-energy', col_out='tra_passenger_energy-demand-by-fuel', dim='Variables')

###################################################################################################
##### end of passenger_fleet_energy(DM_passenger, DM_lfs, DM_other, cdm_const, years_setting) #####
###################################################################################################

# rename objects
dm_pass_mode, dm_pass_tech, dm_pass_fuel = dm_mode, dm_tech, dm_tot_energy

# FREIGHT
cdm_const_freight = cdm_const.copy()

#########################################################################################
##### begin of freight_fleet_energy(DM_freight, DM_other, cdm_const, years_setting) #####
#########################################################################################

# FREIGHT
dm_tkm = DM_freight['freight_demand']
dm_mode = DM_freight['freight_modal_split']
# From bn tkm to tkm by mode of transport
tmp = dm_tkm.array[:, :, 0, np.newaxis] * 1e9 * dm_mode.array[:, :, 0, :]
dm_mode.add(tmp, dim='Variables', col_label='tra_freight_transport-demand', unit='tkm')

dm_mode_road = DM_freight['freight_mode_road']
dm_mode_road.append(dm_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'HDV.*'}), dim='Variables')
dm_mode_road.operation('tra_freight_transport-demand', '/', 'tra_freight_load-factor',
                       out_col='tra_freight_transport-demand-vkm', unit='vkm')
dm_mode_road.operation('tra_freight_transport-demand-vkm', '/', 'tra_freight_utilisation-rate',
                       out_col='tra_freight_vehicle-fleet', unit='number')
dm_mode_road.operation('tra_freight_utilisation-rate', '/', 'tra_freight_lifetime',
                       out_col='tra_freight_renewal-rate', unit='%')

dm_mode_other = DM_freight['freight_mode_other']
dm_mode_other.append(dm_mode.filter({'Categories1': ['IWW', 'marine', 'aviation', 'rail']}), dim='Variables')
dm_mode_other.operation('tra_freight_transport-demand', '/', 'tra_freight_tkm-by-veh',
                        out_col='tra_freight_vehicle-fleet', unit='number')

# Compute vehicle waste and new vehicles for both road and other
dm_other_tmp = dm_mode_other.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
dm_road_tmp = dm_mode_road.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
dm_mode_other.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
dm_mode_road.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
dm_road_tmp.append(dm_other_tmp, dim='Categories1')
dm_mode.append(dm_road_tmp, dim='Variables')
del dm_road_tmp, dm_other_tmp

compute_stock(dm_mode, rr_regex='tra_freight_renewal-rate', tot_regex='tra_freight_vehicle-fleet',
              waste_col='tra_freight_vehicle-waste', new_col='tra_freight_new-vehicles')

# Compute fleet by technology type
dm_tech = DM_freight['freight_tech']
idx_t = dm_tech.index_all()
idx_m = dm_mode.index_all()
tmp_1 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_freight_vehicle-fleet'], :, np.newaxis]
tmp_2 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_freight_vehicle-waste'], :, np.newaxis]
tmp_3 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_new'], :, :] \
        * dm_mode.array[:, :, idx_m['tra_freight_new-vehicles'], :, np.newaxis]
dm_tech.add(tmp_1, col_label='tra_freight_vehicle-fleet', dim='Variables', unit='number')
dm_tech.add(tmp_2, col_label='tra_freight_vehicle-waste', dim='Variables', unit='number')
dm_tech.add(tmp_3, col_label='tra_freight_new-vehicles', dim='Variables', unit='number')
del tmp_1, tmp_2, tmp_3
#
cols = {
    'renewal-rate': 'tra_freight_renewal-rate',
    'tot': 'tra_freight_vehicle-fleet',
    'waste': 'tra_freight_vehicle-waste',
    'new': 'tra_freight_new-vehicles',
    'tech_tot': 'tra_freight_technology-share_fleet',
    'eff_tot': 'tra_freight_vehicle-efficiency_fleet',
    'eff_new': 'tra_freight_vehicle-efficiency_new'
}


##################################################################################
##### begin of compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting) #####
##################################################################################

# Description: in transport_module.py, this function is used in freight_fleet_energy() to compute the split
# between fts and tech. Note that compute_fts_tech_split() does not return anything, it just runs the code.

compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting)


################################################################################
##### end of compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting) #####
################################################################################

# Extract freight transport demand vkm for road and tkm for others, join and compute transport demand by technology
dm_demand_km = dm_mode_road.filter(selected_cols={'Variables': ['tra_freight_transport-demand-vkm']})
dm_demand_km_other = dm_mode_other.filter(selected_cols={'Variables': ['tra_freight_transport-demand']})
dm_demand_km_other.units['tra_freight_transport-demand'] = 'km'
dm_demand_km.units['tra_freight_transport-demand-vkm'] = 'km'
dm_demand_km.rename_col('tra_freight_transport-demand-vkm', 'tra_freight_transport-demand', dim='Variables')
dm_demand_km.append(dm_demand_km_other, dim='Categories1')
dm_demand_km.sort(dim='Categories1')
idx_t = dm_tech.index_all()
tmp = dm_demand_km.array[:, :, 0, :, np.newaxis] \
      * dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], ...]
dm_tech.add(tmp, dim='Variables', col_label='tra_freight_transport-demand', unit='km')
del tmp, dm_demand_km, dm_demand_km_other
# Compute energy consumption
dm_tech.operation('tra_freight_vehicle-efficiency_fleet', '*', 'tra_freight_transport-demand',
                  out_col='tra_freight_energy-demand', unit='MJ')

# Compute biofuel and efuel and extract energy as standalone dm
dm_fuel = DM_other['fuels']
mapping_cat = {
    'road': ['HDVH', 'HDVM', 'HDVL'],
    'aviation': ['aviation'],
    'rail': ['rail'],
    'marine': ['IWW', 'marine']
}
dm_energy = dm_tech.filter({'Variables': ['tra_freight_energy-demand']})


##############################################################################
##### begin of add_biofuel_efuel(dm_energy, dm_fuel_shares, mapping_cat) #####
##############################################################################

# Description: in transport_module.py, this function is used in freight_fleet_energy() to add biofuel and 
# efuel. Note that compute_fts_tech_split() does not return anything, it just runs the code.

add_biofuel_efuel(dm_energy, dm_fuel, mapping_cat)

############################################################################
##### end of add_biofuel_efuel(dm_energy, dm_fuel_shares, mapping_cat) #####
############################################################################


# Deal with PHEV and electricity. For each mode of transport,
# sum PHEV energy demand and multiply it by 0.1 to obtain a new category, the PHEV_elec
dm_energy_phev = dm_energy.filter_w_regex({'Variables': 'tra_freight_energy-demand', 'Categories2': 'PHEV.*'})
PHEV_elec = 0.1 * np.nansum(dm_energy_phev.array, axis=-1)
dm_energy.add(PHEV_elec, dim='Categories2', col_label='PHEV-elec')

dm_energy.array = dm_energy.array*0.277778
dm_energy.units['tra_freight_energy-demand'] = 'TWh'

dict1 = {'FCEV': 'FCV-hydrogen', 'BEV': 'BEV-elec', 'CEV': 'CEV-elec',
         'aviation_ICEefuel': 'aviation_ejetfuel', 'aviation_ICEbio': 'aviation_biojetfuel',
         'aviation_ICE': 'aviation_kerosene'}

dm_energy_new_cat = dm_energy.flatten()
# Rename the columns based on the substring mapping
for substring, replacement in dict1.items():
    dm_energy_new_cat.rename_col_regex(substring, replacement, dim='Categories1')

grouping = ['dieselbio', 'gasolinebio', 'gasbio', 'gasoline', 'diesel', 'gas', 'dieselefuel', 'gasolineefuel',
            'gasefuel', 'hydrogen', "elec", "ICEbio", "ICEefuel", "ICE", 'biojetfuel', 'kerosene', 'ejetfuel']

dict2 = {'dieselbio': 'biodiesel', 'gasolinebio': 'bioethanol', 'gasbio': 'biogas',
         'dieselefuel': 'ediesel', 'gasolineefuel': 'egasoline', 'gasefuel': 'egas', 'elec': 'electricity',
         'ICEbio': 'biomarinefueloil', 'ICEefuel': 'emarinefueloil', 'IWW_ICE': 'IWW_marinefueloil',
         'marine_ICE': 'marine_marinefueloil'}

###################################################################################################
##### begin of rename_and_group(dm_new_cat, groups, dict_end, grouped_var='tra_total-energy') #####
###################################################################################################

# Description: in transport_module.py, this function is used in freight_fleet_energy() to rename and group
# the total energy demand for passenger fleet

dm_total_energy = rename_and_group(dm_energy_new_cat, grouping, dict2, grouped_var='tra_freight_total-energy')


#################################################################################################
##### end of rename_and_group(dm_new_cat, groups, dict_end, grouped_var='tra_total-energy') #####
#################################################################################################

dm_total_energy.rename_col('ICE', 'marinefueloil', dim='Categories1')

# Compute emission by fuel
# Filter fuels for which we have emissions
dm_energy_em = dm_total_energy.filter({'Categories1': cdm_const.col_labels['Categories2']})
# Sort categories to make sure they match
dm_energy_em.sort(dim='Categories1')
cdm_const.sort(dim='Categories2')
idx_e = dm_energy_em.idx
idx_c = cdm_const.idx

# emissions = energy * emission-factor
tmp = dm_energy_em.array[:, :, idx_e['tra_freight_total-energy'], np.newaxis, :] \
      * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], :, :]
tmp = np.moveaxis(tmp, -2, -1)

# Save emissions by fuel in a datamatrix
col_labels = dm_energy_em.col_labels.copy()
col_labels['Variables'] = ['tra_freight_emissions']
col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
unit = {'tra_freight_emissions': 'Mt'}
dm_emissions_by_fuel = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_fuel.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
del dm_energy_em, tmp, col_labels, unit

# Compute emissions by mode
dm_energy_em = dm_energy_new_cat.filter({'Categories3': cdm_const.col_labels['Categories2']})
dm_energy_em.sort(dim='Categories3')
cdm_const.sort(dim='Categories2')
idx_e = dm_energy_em.idx
idx_c = cdm_const.idx
tmp_en = np.nansum(dm_energy_em.array, axis=-2)  # remove technology split
tmp = tmp_en[:, :, idx_e['tra_freight_energy-demand'], :, np.newaxis, :] \
      * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], np.newaxis, :, :]
tmp = np.nansum(tmp, axis=-1)  # Remove split by fuel
col_labels = dm_energy_em.col_labels.copy()
col_labels.pop('Categories3')
col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
unit = {'tra_freight_emissions': 'Mt'}
dm_emissions_by_mode = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_mode.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
del tmp, unit, col_labels, idx_e, idx_c, tmp_en, dm_energy_em

tmp = np.nansum(dm_emissions_by_mode.array, axis=-2)
col_labels = dm_emissions_by_mode.col_labels.copy()
col_labels['Categories1'] = col_labels['Categories2'].copy()
col_labels.pop('Categories2')
unit = dm_emissions_by_mode.units
dm_emissions_by_GHG = DataMatrix(col_labels=col_labels, units=unit)
dm_emissions_by_GHG.array = tmp[:, :, np.newaxis, :]
del tmp, unit, col_labels

tmp = np.nansum(dm_energy.array, axis=(-1, -2))
col_labels = dm_energy.col_labels.copy()
col_labels.pop('Categories1')
col_labels.pop('Categories2')
dm_no_cat = DataMatrix(col_labels=col_labels, units=dm_energy.units.copy())
dm_no_cat.array = tmp[:, :, np.newaxis]

dm_tech.rename_col('tra_freight_technology-share_fleet', 'tra_freight_techology-share-fleet', dim='Variables')

# rename
dm_fre_mode, dm_fre_tech, dm_fre_energy = dm_mode, dm_tech, dm_energy

#######################################################################################
##### end of freight_fleet_energy(DM_freight, DM_other, cdm_const, years_setting) #####
#######################################################################################

dm_keep_mode = dm_pass_mode.filter({'Variables': ['tra_passenger_transport-demand-by-mode',
                                                  'tra_passenger_energy-demand-by-mode',
                                                  'tra_passenger_emissions-by-mode_CO2']})
dm_keep_tech = dm_pass_tech.filter({'Variables': ['tra_passenger_technology-share-fleet']})

dm_keep_fuel = dm_pass_fuel

# Turn datamatrix to dataframe (because converter and TPE work with dataframes)
df = dm_keep_mode.write_df()
df2 = dm_keep_tech.write_df()
df = pd.concat([df, df2.drop(columns=['Country', 'Years'])], axis=1)
df3 = dm_keep_fuel.write_df()
df = pd.concat([df, df3.drop(columns=['Country', 'Years'])], axis=1)

# Dummy variable
# !FIXME: update this with actual total energy demand
df['tra_energy-demand_total[TWh]'] = 1

results_run = {'transport': df}

##########################################################
##### end of transport(lever_setting, years_setting) #####
##########################################################

########################################
##### end of local_transport_run() #####
########################################















