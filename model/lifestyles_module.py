# Import the Packages

import pandas as pd
import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.interface_class import Interface

# ImportFunctions
from model.common.io_database import edit_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.io_database import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data, filter_geoscale

import time

# filtering the constants & read csv and prepares it for the pickle format


# Lever setting for local purpose
def database_pre_processing():
    # Changes to the EUcalc version
    file = 'lifestyles_floor-intensity'
    lever = 'floor-intensity'
    edit_database(file, lever, column='eucalc-name', pattern='lighting|cold-setpoint_degrees|heat-setpoint_degrees',
                  mode='remove')
    return

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
    dict_fxa = {}
    file = 'lifestyles_calibration-factors'

    # Data - Fixed assumptions - Calibration factors - Food
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_lfs_food-wastes|caf_lfs_diet'})
    dm_caf_food = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['caf_food'] = dm_caf_food

    # Data - Fixed assumptions - Calibration factors - Food
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_lfs_floor-space'})
    dm_caf_intensity = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['caf_intensity'] = dm_caf_intensity

    dict_fxa = {
        'caf_food': dm_caf_food,
        'caf_intensity': dm_caf_intensity
    }

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


#  Reading the Pickle
def read_data(data_file, lever_setting):
    with open(data_file, 'rb') as handle:  # read binary (rb)
        DM_lifestyles = pickle.load(handle)

    DM_ots_fts = read_level_data(DM_lifestyles, lever_setting)  # creates the datamatrix according to the lever setting?

    # Extract sub-data-matrices according to the flow (parallel)
    # Diet sub-matrix for the lifestyles dietary behaviour sub-flow

    dm_demography = DM_ots_fts['pop']['lfs_demography_']
    dm_diet_requirement = DM_ots_fts['kcal-req']
    dm_diet_split = DM_ots_fts['diet']['lfs_consumers-diet_']
    dm_diet_share = DM_ots_fts['diet']['share_']
    dm_diet_fwaste = DM_ots_fts['fwaste']
    dm_population = DM_ots_fts['pop']['lfs_population_']

    # Industry sub-flow data
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
    }

    DM_industry = {
        'macro': dm_macro,
        'population': dm_population,
        'paperpack': dm_packaging
    }

    cdm_const = DM_lifestyles['constant']
    return DM_food, DM_industry, cdm_const


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

    dm_population = DM_food['population']
    idx_p = dm_population.idx
    # [TUTORIAL] Consumer diet (operation with matrices with different structure/array specs)
    dm_diet_share = DM_food['diet-share']
    idx = dm_diet_requirement.idx
    ay_diet_consumers = dm_diet_share.array[:, :, 0, :] * dm_diet_requirement.array[:, :, idx['lfs_healthy-gap'],
                                                          np.newaxis]
    dm_diet_share.add(ay_diet_consumers, dim='Variables', col_label='lfs_consumers-diet', unit='kcal/cap/day')
    idx_d = dm_diet_share.idx
    # Calculate ay_total_diet
    ay_total_diet = dm_diet_share.array[:, :, idx_d['lfs_consumers-diet'], :] * \
                    dm_population.array[:, :, idx_p['lfs_population_total'], np.newaxis] * 365
    start = time.time()
    dm_diet_tmp = DataMatrix.based_on(ay_total_diet[:, :, np.newaxis, :], dm_diet_share,
                                      change={'Variables': ['lfs_diet']}, units={'lfs_diet': 'kcal'})

    # Total Consumers food wastes
    dm_diet_fwaste = DM_food['diet-fwaste']
    idx = dm_population.idx
    idx_const = cdm_const.idx
    ay_total_fwaste = 365 * dm_diet_fwaste.array[:, :, 0, :]\
                      * dm_population.array[:, :, idx['lfs_population_total'], np.newaxis]
    dm_diet_fwaste.add(ay_total_fwaste, dim='Variables', col_label='lfs_food-wastes', unit='kcal')
    dm_diet_fwaste.filter({'Variables': ['lfs_food-wastes']}, inplace=True)

    # Total Consumers food supply (Total food intake)
    ay_total_food = 365 * dm_diet_split.array[:, :, 0, :] \
                    * dm_population.array[:, :, idx['lfs_population_total'], np.newaxis]
    dm_diet_food = DataMatrix.based_on(ay_total_food[:, :, np.newaxis, :], dm_diet_split,
                                       change={'Variables': ['lfs_diet']}, units={'lfs_diet': 'kcal'})
    dm_diet_food.append(dm_diet_tmp, dim='Categories1')
    dm_diet_food.filter({'Variables': ['lfs_diet']}, inplace=True)

    # Data to return to the TPE
    dm_diet_food.append(dm_diet_fwaste, dim='Variables')

    return dm_diet_food


# Calculation tree - Appliances (Functions)
def appliances_workflow(DM_appliance, cdm_const):
    # Total households
    dm_household = DM_appliance['household-size']
    dm_population = DM_appliance['population']
    dm_household.append(dm_population, dim='Variables')
    dm_household.operation('lfs_population_total', '/', 'household-size', out_col='lfs_households', unit='#')

    # Appliances per households
    # Group appliances data
    dm_appliance = DM_appliance['appliance-own']
    dm_appliance.append(DM_appliance['appliance-use'], dim='Variables')
    dm_appliance.append(DM_appliance['product-substitution-rate'], dim='Variables')

    idx_a = dm_appliance.idx
    idx_h = dm_household.idx
    ay_appliance_household = dm_household.array[:, :, idx_h['lfs_households'], np.newaxis] \
                             * dm_appliance.array[:, :, idx_a['lfs_appliance-own'], :]
    dm_appliance.add(ay_appliance_household, dim='Variables', col_label='lfs_households-appliance-ownership', unit='#')

    # Phone use
    idx_const = cdm_const.idx
    idx_a = dm_appliance.idx
    dm_appliance.array[:, :, idx_a['lfs_appliance-use'], idx_a['phone']] = \
        dm_appliance.array[:, :, idx_a['lfs_appliance-use'], idx_a['phone']] \
        * cdm_const.array[idx_const['cp_appliances_charging-time-share']]

    # Use of appliances [hours]
    dm_appliance.operation('lfs_appliance-use', '*', 'lfs_households-appliance-ownership',
                            dim="Variables", out_col='lfs_total-appliance-use', unit='h')

    DM_appliance_out = {
        'buildings': dm_appliance.filter({'Variables': ['lfs_total-appliance-use', 'lfs_product-substitution-rate', 'lfs_appliance-own']})
    }
    return DM_appliance_out  # TODO:Dummy to update when connecting TPE

# Calculation tree - Transport (Functions)

def transport_workflow(DM_transport):

    # Prepare urban rural population share
    dm_urban_rural_share = DM_transport['urbpop']
    arr_pop_rural = 100 - dm_urban_rural_share.array
    dm_urban_rural_share.add(arr_pop_rural, dim='Categories1', col_label='non-urban')
    dm_urban_rural_share.rename_col('urban-population', 'urban', dim='Categories1')
    dm_urban_rural_share.rename_col('lfs_demography', 'lfs_pop-share', dim='Variables')
    dm_urban_rural_share.array = dm_urban_rural_share.array/100
    del arr_pop_rural

    dm_tra = DM_transport['pkm']

    # Compute urb_factor
    idx_u = dm_urban_rural_share.idx
    idx_t = dm_tra.idx
    # factor_a is obtained by computing: urb_pkm_cap / rur_pkm_cap = factor_a
    # urb_pkm_cap * urb_pop + urb_pkm_cap / factor_a * rural_pop = total_pkm
    # urb_pkm_cap * (urb_pop + rural_pop / factor_a) = total_pkm
    # urb_pkm_cap = total_pkm / (urb_pop + rural_pop / factor_a)
    # rural_pkm_cap = urb_pkm_cap / factor_a
    # urb_factor [%] = urb-pop[%] + rur-pop[%]/factor-a[%]
    arr_urb_factor = dm_urban_rural_share.array[:, :, idx_u['lfs_pop-share'], idx_u['urban']] \
                  + dm_urban_rural_share.array[:, :, idx_u['lfs_pop-share'], idx_u['non-urban']]\
                     /dm_tra.array[:, :, idx_t['lfs_tra-factor-a']]
    dm_tra.add(arr_urb_factor, dim='Variables', col_label='lfs_urb-factor-pkm', unit='%')
    del arr_urb_factor, idx_t

    dm_tra.operation('lfs_pkm_pkm', '/', 'lfs_urb-factor-pkm', out_col='lfs_pkm-cap_urban', unit='pkm/cap')
    dm_tra.operation('lfs_pkm-cap_urban', '/', 'lfs_tra-factor-a', out_col='lfs_pkm-cap_non-urban', unit='pkm/cap')

    dm_pkm_cap = dm_tra.filter({'Variables': ['lfs_pkm-cap_urban', 'lfs_pkm-cap_non-urban']})
    dm_pkm_cap.deepen()

    # Turn urban-rural share in urban rural pop
    dm_pop = DM_transport['population']
    idx_p = dm_pop.idx
    idx_u = dm_urban_rural_share.idx
    dm_urban_rural_share.array = dm_urban_rural_share.array[:, :, idx_u['lfs_pop-share'], np.newaxis, :] \
                                 * dm_pop.array[:, :, idx_p['lfs_population_total'], np.newaxis, np.newaxis]
    dm_urban_rural_share.rename_col('lfs_pop-share', 'lfs_pop', dim='Variables')
    dm_pkm_cap.append(dm_urban_rural_share, dim='Variables')
    del dm_urban_rural_share, dm_tra, idx_p, idx_u
    # Compute total pkm
    dm_pkm_cap.operation('lfs_pkm-cap', '*', 'lfs_pop', out_col='lfs_passenger-travel-demand', unit='pkm')

    # Prepare output for transport
    dm_tra = dm_pkm_cap.filter({'Variables': ['lfs_passenger-travel-demand']})

    DM_transport_out = {}

    DM_transport_out['transport'] = {
        'lfs_pop': dm_pop,
        'lfs_passenger_demand': dm_tra
    }
    return DM_transport_out


# [TUTORIAL] Calculation tree - Industry (Functions) - (Tree Split)
def industry_workflow(DM_industry, cdm_const):
    # Consumption of packaging
    dm_population = DM_industry['population']
    dm_packaging = DM_industry['paperpack']
    idx_pop = dm_population.idx
    idx_pak = dm_packaging.idx
    ay_packaging = dm_population.array[:, :, idx_pop['lfs_population_total'], np.newaxis] *\
                   dm_packaging.array[:, :, idx_pak['lfs_paperpack'], :]
    dm_packaging.add(ay_packaging, dim='Variables', col_label='lfs_product-demand', unit='t')

    # Aluminium conversion
    idx_const = cdm_const.idx
    idx = dm_packaging.idx
    dm_packaging.array[:, :, idx['lfs_product-demand'], idx['aluminium-pack']] = \
        dm_packaging.array[:, :, idx['lfs_product-demand'], idx['aluminium-pack']] \
        * cdm_const.array[idx_const['cp_packaging_aluminium-factor']]

    dm_packaging.filter({'Variables': ['lfs_product-demand']}, inplace=True)

    return dm_packaging


# Calculation tree - Building (Functions)
def building_workflow(DM_building):

    dm_building = DM_building['building']

    # Compute floor area
    dm_building.operation('lfs_population_total', '*', 'lfs_floor-intensity_space-cap', unit='1000m2', out_col='lfs_floor-space_total')
    idx = dm_building.idx
    dm_building.array[:, :, idx['lfs_floor-space_total']] = dm_building.array[:, :, idx['lfs_floor-space_total']]/1000
    # Calibration of Space area
    dm_building.array[:, :, idx['lfs_floor-space_total']] = dm_building.array[:, :, idx['lfs_floor-space_total']] \
                                                            * dm_building.array[:, :, idx['caf_lfs_floor-space']]

    dm_building.operation('lfs_floor-area-fraction_perc', '*', 'lfs_floor-space_total',
                           dim="Variables", out_col='lfs_floor-space_cool', unit='1000m2')

    DM_building_out = {
        'floor': dm_building.filter({'Variables': ['lfs_floor-space_total', 'lfs_floor-space_cool']}),
        'other': DM_building['unchanged']  # These variables go straight to building without being modified in lifestyle
    }

    return DM_building_out


def lfs_agriculture_interface(dm_agriculture):

    cat_lfs = ['afats', 'beer', 'bev-alc', 'bev-fer', 'bov', 'cereals', 'coffee', 'dfish', 'egg', 'ffish', 'fruits', \
               'milk', 'offal', 'oilcrops', 'oth-animals', 'oth-aq-animals', 'pfish', 'pigs', 'poultry', 'pulses',
               'rice', 'seafood', 'sheep', 'starch', 'stm', 'sugar', 'sweet', 'veg', 'voil', 'wine']
    cat_agr = ['pro-liv-abp-processed-afat', 'pro-bev-beer', 'pro-bev-bev-alc', 'pro-bev-bev-fer', 'pro-liv-meat-bovine',
               'crop-cereal', 'coffee', 'dfish', 'pro-liv-abp-hens-egg', 'ffish', 'crop-fruit', 'pro-liv-abp-dairy-milk',
               'pro-liv-abp-processed-offal', 'crop-oilcrop', 'pro-liv-meat-oth-animals', 'oth-aq-animals', 'pfish',
               'pro-liv-meat-pig', 'pro-liv-meat-poultry', 'crop-pulse', 'rice', 'seafood', 'pro-liv-meat-sheep',
               'crop-starch', 'stm', 'pro-crop-processed-sugar', 'pro-crop-processed-sweet', 'crop-veg',
               'pro-crop-processed-voil', 'pro-bev-wine']

    dm_agriculture.rename_col(cat_lfs, cat_agr, 'Categories1')
    dm_agriculture.sort('Categories1')

    return dm_agriculture


def lifestyles_TPE_interface(dm_diet):

    df_diet = dm_diet.write_df()

    #dm_own = dm_appliances.filter({'Variables': ['lfs_appliance-own']})
    #df_own = dm_own.write_df()

    #dm_use = dm_appliances.filter({'Variables': ['lfs_total-appliance-use']})
    #dm_use.filter({'Categories1': ['comp', 'phone', 'tv']})
    #df_use = dm_use.write_df()

    #df = pd.concat([df_diet, df_own.drop(columns=['Country', 'Years'])], axis=1)
    #df = pd.concat([df, df_use.drop(columns=['Country', 'Years'])], axis=1)

    return df_diet


# CORE module
def lifestyles(lever_setting, years_setting, interface=Interface()):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    lifestyles_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/lifestyles.pickle')
    DM_food, DM_industry, cdm_const = read_data(lifestyles_data_file, lever_setting)

    # To send to TPE (result run)
    dm_pop = DM_food['population']
    dm_agriculture_out = food_workflow(DM_food, cdm_const)
    dm_industry_out = industry_workflow(DM_industry, cdm_const)

    # concatenate all results to df
    results_run = lifestyles_TPE_interface(dm_agriculture_out)

    # !FIXME: currently agriculture renames all of the lifestyles categories,
    #  we should rather keep lifestyles categories and rework agriculture
    dm_agriculture = lfs_agriculture_interface(dm_agriculture_out)
    interface.add_link(from_sector='lifestyles', to_sector='agriculture', dm=dm_agriculture)
    interface.add_link(from_sector='lifestyles', to_sector='transport', dm=dm_pop)
    interface.add_link(from_sector='lifestyles', to_sector='buildings', dm=dm_pop)
    interface.add_link(from_sector='lifestyles', to_sector='industry', dm=dm_industry_out)

    dm_minerals = DM_industry['macro']
    dm_minerals.append(DM_industry['population'], dim='Variables')
    interface.add_link(from_sector='lifestyles', to_sector='minerals', dm=dm_minerals)

    return results_run


# Local run of lifestyles
def local_lifestyles_run():
    # Initiate the year & lever setting
    years_setting, lever_setting = init_years_lever()

    global_vars = {'geoscale': 'Switzerland|Vaud'}
    filter_geoscale(global_vars)

    lifestyles(lever_setting, years_setting)
    return

# Update/Create the Pickle
#database_from_csv_to_datamatrix()  # un-comment to update
#local_lifestyles_run()  # to un-comment to run in local

