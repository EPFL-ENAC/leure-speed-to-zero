#######################################################################################################################
# Import Packages, Classes & Functions
#######################################################################################################################

import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.auxiliary_functions import read_level_data

# ImportFunctions
from model.common.io_database import read_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups,\
    update_interaction_constant_from_file


#######################################################################################################################
# Database - Power - Setting up database
#######################################################################################################################

def database_from_csv_to_datamatrix():
    years_setting = [1990, 2015, 2050, 5]  # Set the timestep for historical years & scenarios
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int))
    # Defines the part of dataset that is historical years
    years_fts = list(
        np.linspace(start=baseyear + step_fts, stop=lastyear, num=int((lastyear - baseyear) / step_fts)).astype(int))
    # Defines the part of dataset that is scenario
    years_all = years_ots + years_fts  # Defines all years

    # Initiate the dictionary for ots & fts
    dict_ots = {}
    dict_fts = {}

#######################################################################################################################
# Database - Power - Levers
#######################################################################################################################

    # Database - Power - Lever: Solar PV capacity
    file = 'power_pv-capacity'
    lever = 'pv-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Solar CSP capacity
    file = 'power_csp-capacity'
    lever = 'csp-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Offshore Wind Power capacity
    file = 'power_offshore-wind-capacity'
    lever = 'offshore-wind-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Onshore Wind Power capacity
    file = 'power_onshore-wind-capacity'
    lever = 'onshore-wind-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Biogas capacity
    file = 'power_biogas-capacity'
    lever = 'biogas-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Biomass capacity
    file = 'power_biomass-capacity'
    lever = 'biomass-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Hydroelectric capacity
    file = 'power_hydroelectric-capacity'
    lever = 'hydroelectric-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Geothermal capacity
    file = 'power_geothermal-capacity'
    lever = 'geothermal-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Marine energy capacity
    file = 'power_marine-capacity'
    lever = 'marine-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Gas capacity
    file = 'power_gas-capacity'
    lever = 'gas-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Oil capacity
    file = 'power_oil-capacity'
    lever = 'oil-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Coal capacity
    file = 'power_coal-capacity'
    lever = 'coal-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

    # Database - Power - Lever: Nuclear capacity
    file = 'power_nuclear-capacity'
    lever = 'nuclear-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots,dict_fts=dict_fts)

#######################################################################################################################
# Database - Power - FXA
#######################################################################################################################





#######################################################################################################################
# Database - Power - Constants
#######################################################################################################################



    cdm_const_cat0 = ConstantDataMatrix.extract_constant('interactions_constants',
                                                        pattern='cp_timestep_hours-a-year|'
                                                                'cp_carbon-capture_power-self-consumption|', num_cat=0)

    cdm_const_cat1 = ConstantDataMatrix.extract_constant('interactions_constants',
                                                        pattern='cp_power-unit-self-consumption|'
                                                                'cp_fuel-based-power-efficiency', num_cat=1)

    dict_const = {
        'constant_0': cdm_const_cat0,
        'constant_1': cdm_const_cat1
    }

#######################################################################################################################
# Database - Power Data Matrix
#######################################################################################################################

    DM_power = {
        'fts': dict_fts,
        'ots': dict_ots,
        #'fxa': dict_fxa,
        'constant': dict_const
    }
#######################################################################################################################
# Database - Power - Pickle Update
#######################################################################################################################

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/power.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_power, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return

update_interaction_constant_from_file('interactions_constants_local')
database_from_csv_to_datamatrix()  # un-comment to update

#######################################################################################################################
# Database - Power - Sub Data Matrices
#######################################################################################################################

def read_data(data_file, lever_setting):
    with open(data_file, 'rb') as handle:
        DM_power = pickle.load(handle)

    # FXA data matrix
    # dm_fxa_caf_food = DM_lifestyles['fxa']['caf_food']

    DM_ots_fts = read_level_data(DM_power, lever_setting)

    # Capacity per technology (fuel-based)

    dm_coal = DM_ots_fts['coal-capacity']
    dm_capacity_fuel_based = dm_coal.copy()

    dm_oil = DM_ots_fts['oil-capacity']
    dm_capacity_fuel_based.append(dm_oil, dim='Categories1')

    dm_gas = DM_ots_fts['gas-capacity']
    dm_capacity_fuel_based.append(dm_gas, dim='Categories1')

    dm_nuclear = DM_ots_fts['nuclear-capacity']
    dm_capacity_fuel_based.append(dm_nuclear, dim='Categories1')

    dm_biogas = DM_ots_fts['biogas-capacity']
    dm_capacity_fuel_based.append(dm_biogas, dim='Categories1')

    dm_biomass = DM_ots_fts['biomass-capacity']
    dm_capacity_fuel_based.append(dm_biomass, dim='Categories1')

    # Capacity per technology (non-fuel based)

    dm_pv = DM_ots_fts['pv-capacity']
    dm_capacity_non_fuel_based=dm_pv.copy()

    dm_csp = DM_ots_fts['csp-capacity']
    dm_capacity_non_fuel_based.append(dm_csp, dim='Categories1')

    dm_offshore_wind = DM_ots_fts['offshore-wind-capacity']
    dm_capacity_non_fuel_based.append(dm_offshore_wind, dim='Categories1')

    dm_onshore_wind = DM_ots_fts['onshore-wind-capacity']
    dm_capacity_non_fuel_based.append(dm_onshore_wind, dim='Categories1')

    dm_hydroelectric = DM_ots_fts['hydroelectric-capacity']
    dm_capacity_non_fuel_based.append(dm_hydroelectric, dim='Categories1')

    dm_geothermal = DM_ots_fts['geothermal-wind-capacity']
    dm_capacity_non_fuel_based.append(dm_geothermal, dim='Categories1')

    dm_marine = DM_ots_fts['marine-capacity']
    dm_capacity_non_fuel_based.append(dm_marine, dim='Categories1')

    # Aggregated Data Matrix - Non-fuel-based power production

    DM_nfb_capacity = {
        'pv-capacity': dm_pv,
        'csp-capacity': dm_csp,
        'offshore-wind-capacity': dm_offshore_wind,
        'onshore-wind-capacity': dm_onshore_wind,
        'hydroelectric-capacity': dm_hydroelectric,
        'geothermal-capacity': dm_geothermal,
        'marine-capacity': dm_marine
    }

    DM_fb_capacity = {
        'coal-capacity': dm_coal,
        'gas-capacity': dm_gas,
        'oil-capacity': dm_oil,
        'nuclear-capacity': dm_nuclear,
        'biogas-capacity': dm_biogas,
        'biomass-capacity': dm_biomass
    }

    cdm_const = DM_power['constant']

    return DM_nfb_capacity, DM_fb_capacity, cdm_const


#######################################################################################################################
# Calculation tree - Power - Production
#######################################################################################################################

#######################################################################################################################
# Calculation tree - Power - Demand
#######################################################################################################################

#######################################################################################################################
# CORE module - Power
#######################################################################################################################

def power(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    power_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/power.pickle')
    DM_nfb_capacity, DM_fb_capacity, cdm_const = read_data(power_data_file,lever_setting)

    # To send to TPE (result run)
    dm_diet = dm_diet_split.filter({'Variables': ['cal_diet']})
    dm_diet.rename_col('cal_diet', 'lfs_diet', dim="Variables")
    df_diet = dm_diet.write_df()

    # concatenate all results to df

    results_run = df_diet
    return results_run


#######################################################################################################################
# Local run - Power module
#######################################################################################################################

def local_power_run():
    # Function to run only transport module without converter and tpe
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]

    global_vars = {'geoscale': 'Switzerland'}
    filter_geoscale(global_vars)

    results_run = power(lever_setting, years_setting)

    return results_run


results_run = local_power_run()
