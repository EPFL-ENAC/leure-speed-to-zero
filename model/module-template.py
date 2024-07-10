#######################################################################################################################
# SECTION: Import Packages, Classes & Functions
#######################################################################################################################

import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)
import pandas as pd

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.interface_class import Interface

# ImportFunctions
from model.common.io_database import read_database_to_ots_fts_dict
from model.common.auxiliary_functions import read_level_data, filter_geoscale



#######################################################################################################################
# ModelSetting - Module name
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
# DataLever - Module
#######################################################################################################################

    # Database - Power - Lever: Solar PV capacity
    file = 'power_pv-capacity'
    lever = 'pv-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1,baseyear=baseyear, years=years_all,

#######################################################################################################################
# DataFixedAssumptions - Power
#######################################################################################################################


#######################################################################################################################
# DataConstants - Power
#######################################################################################################################


#######################################################################################################################
# DataMatrices - Power Data Matrix
#######################################################################################################################


#######################################################################################################################
# DataPickle - Power
#######################################################################################################################


# update_interaction_constant_from_file('interactions_constants_local') # uncomment to update constant
# database_from_csv_to_datamatrix()  # un-comment to update

#######################################################################################################################
# DataSubMatrices - Power
#######################################################################################################################

def read_data(data_file, lever_setting):
    with open(data_file, 'rb') as handle:
        DM_power = pickle.load(handle)

    # FXA data matrix
    # dm_fxa_caf_food = DM_lifestyles['fxa']['caf_food']

    DM_ots_fts = read_level_data(DM_power, lever_setting)

    # Capacity per technology (fuel-based)

    dm_coal = DM_ots_fts['coal-capacity']
    dm_capacity = dm_coal.copy()

    dm_oil = DM_ots_fts['oil-capacity']
    dm_capacity.append(dm_oil, dim='Categories1')

    dm_gas = DM_ots_fts['gas-capacity']
    dm_capacity.append(dm_gas, dim='Categories1')

    dm_nuclear = DM_ots_fts['nuclear-capacity']
    dm_capacity.append(dm_nuclear, dim='Categories1')

    dm_biogas = DM_ots_fts['biogas-capacity']
    dm_capacity.append(dm_biogas, dim='Categories1')

    dm_biomass = DM_ots_fts['biomass-capacity']
    dm_capacity.append(dm_biomass, dim='Categories1')

    # Capacity per technology (non-fuel based)

    dm_pv = DM_ots_fts['pv-capacity']
    dm_capacity.append(dm_pv, dim='Categories1')

    dm_csp = DM_ots_fts['csp-capacity']
    dm_capacity.append(dm_csp, dim='Categories1')

    dm_offshore_wind = DM_ots_fts['offshore-wind-capacity']
    dm_capacity.append(dm_offshore_wind, dim='Categories1')

    dm_onshore_wind = DM_ots_fts['onshore-wind-capacity']
    dm_capacity.append(dm_onshore_wind, dim='Categories1')

    dm_hydroelectric = DM_ots_fts['hydroelectric-capacity']
    dm_capacity.append(dm_hydroelectric, dim='Categories1')

    dm_geothermal = DM_ots_fts['geothermal-capacity']
    dm_capacity.append(dm_geothermal, dim='Categories1')

    dm_marine = DM_ots_fts['marine-capacity']
    dm_capacity.append(dm_marine, dim='Categories1')

    dm_ccus = DM_ots_fts['carbon-storage-capacity']

    # Aggregated Data Matrix - Non-fuel-based power production


    cdm_const = DM_power['constant']

    return dm_capacity, dm_ccus, cdm_const


#######################################################################################################################
# LocalInterfaces - Module
#######################################################################################################################
def simulate_climate_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-climate-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_climate = DataMatrix.create_from_df(df, num_cat=1)

    return dm_climate

#######################################################################################################################
# CalculationTree - Module - sub flow
#######################################################################################################################
def yearly_production_workflow(dm_climate, dm_capacity, dm_ccus, cdm_const):

    ######################################
    # CalculationLeafs - Gross electricity production [GWh]
    ######################################
    # Tuto: Tree parallel (array)
    idx_cap = dm_capacity.idx
    idx_clm = dm_climate.idx
    ay_gross_yearly_production = dm_capacity.array[:,:,idx_cap['pow_existing-capacity'],:] \
                                 * dm_climate.array[:,:,idx_clm['clm_capacity-factor'],:]*8760
    dm_capacity.add(ay_gross_yearly_production, dim='Variables', col_label='pow_gross-yearly-production', unit='GWh')

#######################################################################################################################
# CoreModule - Power
#######################################################################################################################

def power(lever_setting, years_setting, interface=Interface()):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    power_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/power.pickle')
    dm_capacity, dm_ccus, cdm_const = read_data(power_data_file,lever_setting)
    dm_climate = simulate_climate_to_power_input()
    if interface.has_link(from_sector='agriculture', to_sector='power'):
        dm_agr_electricity = interface.get_link(from_sector='agriculture', to_sector='power')
    else:
        dm_agr_electricity = simulate_agriculture_to_power_input()
    if interface.has_link(from_sector='buildings', to_sector='power'):
        DM_bld = interface.get_link(from_sector='buildings', to_sector='power')
    else:
        DM_bld = simulate_buildings_to_power_input()


    DM_ind = simulate_industry_to_power_input()

    dm_amm_electricity, dm_amm_hydrogen = simulate_ammonia_to_power_input()
    DM_tra = simulate_transport_to_power_input()

    # filter local interface country list
    cntr_list = dm_capacity.col_labels['Country']
    dm_climate = dm_climate.filter({'Country': cntr_list})

    # To send to TPE (result run)
    dm_fake_1, dm_fake_2 = yearly_production_workflow(dm_climate, dm_capacity, dm_ccus, cdm_const)
    dm_fake_3, dm_fake_4, dm_fake_5 = yearly_demand_workflow(DM_bld, dm_ind_electricity,dm_amm_electricity,
                                                             dm_agr_electricity, DM_tra, dm_ind_hydrogen,
                                                             dm_amm_hydrogen)# input fonctions
    # same number of arg than the return function

    # concatenate all results to df

    results_run = dm_fake_1
    return results_run


#######################################################################################################################
# LocalRun - Power
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


# results_run = local_power_run()