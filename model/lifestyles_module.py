# Import the Packages

import pandas as pd
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


# filtering the constants & read csv and prepares it for the pickle format

# Lever setting for local purpose


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


# Setting up the database in the module
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

    # Data - Fixed Assumptions - Calibration factors

    # Initiate the dictionary for ots & fts
    dict_ots = {}
    dict_fts = {}

    # [TUTORIAL] Data - Lever - Population
    file = 'lifestyles_population'  # File name to read
    lever = 'pop'  # Lever name to match the JSON?

    # Creates the datamatrix for lifestyles population
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 0, 0], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['lfs_demography_.*',
                                                                            'lfs_macro-scenarii_.*',
                                                                            'lfs_population_.*'])

    # Data - Lever - Diet
    file = 'lifestyles_diet'
    lever = 'diet'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['lfs_consumers-diet_.*', 'share_.*'])

    # Data - Lever - Energy requirements
    file = 'lifestyles_energy-requirement'
    lever = 'kcal-req'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    # Data - Lever - Food wastes
    file = 'lifestyles_food-wastes'
    lever = 'fwaste'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    # Data - Lever - Urban population
    file = 'lifestyles_urban-population'
    lever = 'urbpop'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Passenger distance
    file = 'lifestyles_passenger-distance'
    lever = 'pkm'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Appliance use
    file = 'lifestyles_appliance-use'
    lever = 'appliance-use'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    # Data - Lever - Appliance ownership
    file = 'lifestyles_appliance-ownership'
    lever = 'appliance-own'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Product substitution rate
    file = 'lifestyles_product-substitution-rate'
    lever = 'product-substitution-rate'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Packaging
    file = 'lifestyles_paper-and-packaging'
    lever = 'paperpack'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Heat & Cooling behaviour
    file = 'lifestyles_heating-behaviour'
    lever = 'heatcool-behaviour'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Floor Intensity
    file = 'lifestyles_floor-intensity'
    lever = 'floor-intensity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Lever - Cooled floors
    file = 'lifestyles_cooled-floor-fraction'
    lever = 'floor-area-fraction'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Data - Fixed assumptions
    df = read_database_fxa('lifestyles_calibration-factors',
                           filter_dict={'eucalc-name': 'caf_lfs_food-wastes|caf_lfs_diet'})
    dm_caf_food = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa = {}
    dict_fxa['caf_food'] = dm_caf_food

    # Data - Constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants',
                                                    pattern='cp_time_days-per-year.*|cp_appliances_charging-time-share|'
                                                            'cp_packaging_aluminium-factor',
                                                    num_cat=0)

    #  Create the data matrix for lifestyles
    DM_lifestyles = {
        'fts': dict_fts,
        'ots': dict_ots,
        'fxa': dict_fxa,
        'constant': cdm_const
    }

    current_file_directory = os.path.dirname(os.path.abspath(__file__))  # creates local path variable
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/lifestyles.pickle')
    # creates path variable for the pickle
    with open(f, 'wb') as handle:  # 'wb': writing binary / standard protocol for pickle
        pickle.dump(DM_lifestyles, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return


# Update/Create the Pickle
#  database_from_csv_to_datamatrix()  # un-comment to update


#  Reading the Pickle
def read_data(data_file, lever_setting):
    with open(data_file, 'rb') as handle:  # read binary (rb)
        DM_lifestyles = pickle.load(handle)
    # FXA data matrix
    dm_fxa_caf_food = DM_lifestyles['fxa']['caf_food']

    DM_ots_fts = read_level_data(DM_lifestyles, lever_setting)  # creates the datamatrix according to the lever setting?

    # Extract sub-data-matrices according to the flow (parallel)
    # Diet sub-matrix for the lifestyles dietary behaviour sub-flow

    dm_demography = DM_ots_fts['pop']['lfs_demography_']
    dm_diet_requirement = DM_ots_fts['kcal-req']
    dm_diet_split = DM_ots_fts['diet']['lfs_consumers-diet_']
    dm_diet_share = DM_ots_fts['diet']['share_']
    dm_diet_fwaste = DM_ots_fts['fwaste']
    dm_population = DM_ots_fts['pop']['lfs_population_']

    # Appliances sub-matrix for the lifestyles
    dm_appliance_use = DM_ots_fts['appliance-use']
    dm_appliance_own = DM_ots_fts['appliance-own']
    dm_appliance_substitution = DM_ots_fts['product-substitution-rate']
    dm_floor_intensity = DM_ots_fts['floor-intensity']
    dm_household = dm_floor_intensity.filter({'Variables': ['household-size']})

    # Transport sub-matrix for the lifestyles
    dm_pop_urban = DM_ots_fts['urbpop']
    dm_passenger_distance = DM_ots_fts['pkm']

    # Industry sub-flow data
    dm_population = DM_ots_fts['pop']['lfs_population_']
    dm_macro = DM_ots_fts['pop']['lfs_macro-scenarii_']
    dm_packaging = DM_ots_fts['paperpack']


    # Aggregate datamatrix by theme/flow
    # Aggregated Data Matrix - Food
    DM_food = {
        'energy-requirement': dm_diet_requirement,
        'diet-split': dm_diet_split,
        'diet-share': dm_diet_share,
        'diet-fwaste': dm_diet_fwaste,
        'demography': dm_demography,
        'population': dm_population,
        'food-caf': dm_fxa_caf_food
    }

    # Aggregated Data Matrix - Appliances

    DM_appliance = {
        'population': dm_population,
        'appliance-use': dm_appliance_use,
        'appliance-own': dm_appliance_own,
        'product-substitution-rate': dm_appliance_substitution,
        'household-size': dm_household
    }

    # Aggregated Data Matrix - Appliances

    DM_transport = {
        'population': dm_population,
        'urbpop': dm_pop_urban,
        'pkm': dm_passenger_distance
    }

    DM_industry = {
        'macro': dm_macro,
        'population': dm_population,
        'paperpack': dm_packaging
    }

    cdm_const = DM_lifestyles['constant']
    return DM_food, DM_appliance, DM_transport, DM_industry, cdm_const


# Calculation tree - Lifestyles
# Calculation tree - Diet (Functions)
def food_workflow(DM_food, cdm_const):
    # Total kcal consumed
    dm_diet_split = DM_food['diet-split']
    ay_diet_intake = dm_diet_split.array[:, :, 0, :].sum(axis=-1)

    # [TUTORIAL] Gap from healthy diet (Tree Parallel)
    dm_diet_requirement = DM_food['energy-requirement']
    dm_diet_requirement.add(ay_diet_intake, dim='Variables', col_label='lfs_energy-intake_total', unit='kcal/cap/day')
    dm_diet_requirement.operation('lfs_kcal-req_req', '-', 'lfs_energy-intake_total',
                                  dim="Variables", out_col='lfs_healthy-gap', unit='kcal/cap/day')

    # [TUTORIAL] Consumer diet (operation with matrices with different structure/array specs)
    dm_diet_share = DM_food['diet-share']
    idx = dm_diet_requirement.idx
    ay_diet_consumers = dm_diet_share.array[:, :, 0, :] * dm_diet_requirement.array[:, :, idx['lfs_healthy-gap'],
                                                          np.newaxis]
    dm_diet_share.add(ay_diet_consumers, dim='Variables', col_label='lfs_consumers-diet', unit='kcal/cap/day')

    # Total Consumers food wastes
    dm_population = DM_food['population']
    dm_diet_fwaste = DM_food['diet-fwaste']
    idx = dm_population.idx
    idx_const = cdm_const.idx
    ay_total_fwaste = dm_diet_fwaste.array[:, :, 0, :] * dm_population.array[:, :, idx['lfs_population_total'],
                                                         np.newaxis] \
                      * cdm_const.array[idx_const['cp_time_days-per-year']]
    dm_diet_fwaste.add(ay_total_fwaste, dim='Variables', col_label='lfs_food-wastes', unit='kcal')

    # Total Consumers food supply (Total food intake)
    ay_total_food = dm_diet_split.array[:, :, 0, :] * dm_population.array[:, :, idx['lfs_population_total'], np.newaxis] \
                    * cdm_const.array[idx_const['cp_time_days-per-year']]
    dm_diet_split.add(ay_total_food, dim='Variables', col_label='lfs_diet', unit='kcal')

    # Calibration - Food supply
    dm_fxa_caf_food = DM_food['food-caf']
    dm_diet_split.append(dm_diet_share, dim='Categories1')
    dm_diet_split.drop(dim='Categories1', col_label=['rice', 'afats'])
    dm_diet_split.append(dm_fxa_caf_food, dim='Variables')
    dm_diet_split.operation('lfs_diet', '*', 'caf_lfs_diet',
                            dim="Variables", out_col='cal_diet', unit='kcal')

    # Calibration - Food wastes
    dm_diet_fwaste.drop(dim='Categories1', col_label=['rice', 'afats'])
    dm_diet_fwaste.append(dm_fxa_caf_food, dim='Variables')
    dm_diet_fwaste.operation('lfs_food-wastes', '*', 'caf_lfs_food-wastes',
                             dim="Variables", out_col='cal_food-wastes', unit='kcal')

    # Data to return to the TPE
    return dm_diet_split


# Calculation tree - Appliances (Functions)
def appliances_workflow(DM_appliance, cdm_const):
    # Total households
    dm_household = DM_appliance['household-size']
    dm_population = DM_appliance['population']
    idx = dm_population.idx
    ay_total_household = dm_population.array[:, :, idx['lfs_population_total']] / dm_household.array[:, :, 0]
    dm_household.add(ay_total_household, dim='Variables', col_label='lfs_households', unit='#')

    # Appliances per households
    dm_appliance_own = DM_appliance['appliance-own']
    idx_appown = dm_appliance_own.idx
    idx_hsl = dm_household.idx
    ay_appliance_household = dm_household.array[:, :, idx_hsl['household-size'], np.newaxis] * dm_appliance_own.array[:,
                                                                                               :, idx_appown[
                                                                                                      'lfs_appliance-own'],
                                                                                               :]
    dm_appliance_own.add(ay_appliance_household, dim='Variables', col_label='lfs_households-appliance-ownership',
                         unit='#')

    # Phone use
    dm_appliance_use = DM_appliance['appliance-use']
    idx_const = cdm_const.idx
    idx = dm_appliance_use.idx
    dm_appliance_use.array[:, :, idx['lfs_appliance-use'], idx['phone']] = \
        dm_appliance_use.array[:, :, idx['lfs_appliance-use'], idx['phone']] \
        * cdm_const.array[idx_const['cp_appliances_charging-time-share']]

    # Use of appliances [hours]
    dm_appliance_use.append(dm_appliance_own, dim='Variables')
    dm_appliance_use.operation('lfs_appliance-use', '*', 'lfs_households-appliance-ownership',
                               dim="Variables", out_col='lfs_total-appliance-use', unit='h')

    return dm_household  # TODO:Dummy to update when connecting TPE

# Calculation tree - Transport (Functions)

def transport_workflow(DM_transport):

    # Urban population
    dm_population_urban = DM_transport['urbpop']
    dm_population = DM_transport['population']
    idx_pop = dm_population.idx
    idx_urb = dm_population_urban.idx
    ay_population_urban = dm_population.array[:, :, idx_pop['lfs_population_total'], np.newaxis] * \
                          dm_population_urban.array[:, :, idx_urb['lfs_demography'],:]
    dm_population_urban.add(ay_population_urban, dim='Variables', col_label='lfs_population', unit='inhabitants')

    # TODO: Paola transport flow

    return dm_population_urban


# [TUTORIAL] Calculation tree - Industry (Functions) - (Tree Split)
def industry_workflow(DM_industry, cdm_const):
    # Consumption of packaging
    dm_population = DM_industry['population']
    dm_packaging = DM_industry['paperpack']
    idx_pop = dm_population.idx
    idx_pak = dm_packaging.idx
    ay_packaging = dm_population.array[:, :, idx_pop['lfs_population_total'], np.newaxis] * \
                          dm_packaging.array[:, :, idx_pak['lfs_paperpack'], :]
    dm_packaging.add(ay_packaging, dim='Variables', col_label='lfs', unit='t/cap')

    # Aluminium conversion
    idx_const = cdm_const.idx
    idx = dm_packaging.idx
    dm_packaging.array[:, :, idx['lfs_paperpack'], idx['aluminium-pack']] = \
        dm_packaging.array[:, :, idx['lfs_paperpack'], idx['aluminium-pack']] \
        * cdm_const.array[idx_const['cp_packaging_aluminium-factor']]

    return dm_packaging

# CORE module
def lifestyles(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    lifestyles_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/lifestyles.pickle')
    DM_food, DM_appliance, DM_transport, DM_industry, cdm_const = read_data(lifestyles_data_file, lever_setting)

    # To send to TPE (result run)
    dm_diet_split = food_workflow(DM_food, cdm_const)
    dm_household = appliances_workflow(DM_appliance, cdm_const)
    dm_population_urban = transport_workflow(DM_transport)
    dm_packaging = industry_workflow(DM_industry, cdm_const)

    dm_diet = dm_diet_split.filter({'Variables': ['cal_diet']})
    dm_diet.rename_col('cal_diet', 'lfs_diet', dim="Variables")

    df_diet = dm_diet.write_df()

    # concatenate all results to df

    results_run = df_diet
    return results_run


# Local run of lifestyles
def local_lifestyles_run():
    # Initiate the year & lever setting
    years_setting, lever_setting = init_years_lever()
    lifestyles(lever_setting, years_setting)

    return


local_lifestyles_run()  # to un-comment to run in local
