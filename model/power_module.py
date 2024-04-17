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
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups


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
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Solar CSP capacity
    file = 'power_csp-capacity'
    lever = 'csp-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Offshore Wind Power capacity
    file = 'power_offshore-wind-capacity'
    lever = 'offshore-wind-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Onshore Wind Power capacity
    file = 'power_onshore-wind-capacity'
    lever = 'onshore-wind-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Biogas capacity
    file = 'power_biogas-capacity'
    lever = 'biogas-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Biomass capacity
    file = 'power_biomass-capacity'
    lever = 'biomass-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Hydroelectric capacity
    file = 'power_hydroelectric-capacity'
    lever = 'hydroelectric-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Geothermal capacity
    file = 'power_geothermal'
    lever = 'geothermal-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Marine energy capacity
    file = 'power_marine-capacity'
    lever = 'marine-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Gas capacity
    file = 'power_gas-capacity'
    lever = 'gas-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Oil capacity
    file = 'power_oil-capacity'
    lever = 'oil-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Coal capacity
    file = 'power_coal-capacity'
    lever = 'coal-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

    # Database - Power - Lever: Nuclear capacity
    file = 'power_nuclear-capacity'
    lever = 'nuclear-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0, 0, 0, 0],
                                                                baseyear=baseyear, years=years_all, dict_ots=dict_ots,
                                                                dict_fts=dict_fts, column='eucalc-name',
                                                                group_list=['pow_decommisioned-capacity',
                                                                            'pow_existing-capacity',
                                                                            'pow_installed_capacity',
                                                                            'pow_new-capacity',
                                                                            'pow_renewed-capacity'])

#######################################################################################################################
# Database - Power - FXA
#######################################################################################################################

#######################################################################################################################
# Database - Power - Constants
#######################################################################################################################

#######################################################################################################################
# Database - Power Data Matrix
#######################################################################################################################

#######################################################################################################################
# Database - Power - Pickle Update
#######################################################################################################################

#######################################################################################################################
# Database - Power - Sub Data Matrices
#######################################################################################################################

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
    lifestyles_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/power.pickle')
    DM_food, DM_appliance, DM_transport, DM_industry, DM_building, cdm_const = read_data(lifestyles_data_file,
                                                                                         lever_setting)

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
