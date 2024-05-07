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
from model.common.auxiliary_functions import read_level_data, filter_geoscale

# ImportFunctions
from model.common.io_database import read_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups,\
    update_interaction_constant_from_file


#######################################################################################################################
# ModelSetting - Power
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
# DataLever - Power
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

    # Database - Power - Lever: CCUS capacity
    file = 'power_carbon-storage'
    lever = 'carbon-storage-capacity'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

#######################################################################################################################
# DataFixedAssumptions - Power
#######################################################################################################################





#######################################################################################################################
# DataConstants - Power
#######################################################################################################################



    cdm_const_cat0 = ConstantDataMatrix.extract_constant('interactions_constants',
                                                        pattern='cp_timestep_hours-a-year|'
                                                                'cp_carbon-capture_power-self-consumption', num_cat=0)

    cdm_const_cat1 = ConstantDataMatrix.extract_constant('interactions_constants',
                                                        pattern='cp_power-unit-self-consumption|'
                                                                'cp_fuel-based-power-efficiency', num_cat=1)

    dict_const = {
        'constant_0': cdm_const_cat0,
        'constant_1': cdm_const_cat1
    }

#######################################################################################################################
# DataMatrices - Power Data Matrix
#######################################################################################################################

    DM_power = {
        'fts': dict_fts,
        'ots': dict_ots,
        #'fxa': dict_fxa,
        'constant': dict_const
    }
#######################################################################################################################
# DataPickle - Power
#######################################################################################################################

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/power.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_power, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return

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
# LocalInterfaces - Climate
#######################################################################################################################
def simulate_climate_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-climate-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_climate = DataMatrix.create_from_df(df, num_cat=1)

    return dm_climate

#######################################################################################################################
# LocalInterfaces - Buildings
#######################################################################################################################

def simulate_buildings_to_power_input():
    # Tuto: Local module interface
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-buildings-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=2)

    # Space heating flow:
    dm_bld_heating = dm.filter_w_regex({'Categories2': 'space-heating'})
    dm_bld_cooling = dm.filter_w_regex({'Categories2': 'space-cooling'})
    dm_bld_appliances = dm.filter_w_regex({'Categories2': 'cooking|hot-water|lighting|appliances'})
    dm_bld_heatpump = dm.filter_w_regex({'Categories2': 'heatpumps'})

    DM_bld= {
        'appliance': dm_bld_appliances,
        'space-heating': dm_bld_heating,
        'cooling': dm_bld_cooling,
        'heatpump': dm_bld_heatpump
    }

    return DM_bld

#######################################################################################################################
# LocalInterfaces - Transport
#######################################################################################################################

def simulate_transport_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-transport-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    DM_tra = DataMatrix.create_from_df(df, num_cat=1)

    return DM_tra

#######################################################################################################################
# LocalInterfaces - Industry
#######################################################################################################################

def simulate_industry_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-industry-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)

    # Space heating flow:
    dm_ind_electricity = dm.filter_w_regex({'Variables': 'ind_energy-demand_electricity'})
    dm_ind_hydrogen = dm.filter_w_regex({'Variables': 'ind_energy-demand_hydrogen'})

    return dm_ind_electricity, dm_ind_hydrogen

#######################################################################################################################
# LocalInterfaces - Ammonia
#######################################################################################################################

def simulate_ammonia_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-ammonia-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)

    # Space heating flow:
    dm_amm_electricity = dm.filter_w_regex({'Variables': 'amm_energy-demand_electricity'})
    dm_amm_hydrogen = dm.filter_w_regex({'Variables': 'amm_energy-demand_hydrogen'})

    return dm_amm_electricity, dm_amm_hydrogen

#######################################################################################################################
# LocalInterfaces - Agriculture
#######################################################################################################################

def simulate_agriculture_to_power_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-agriculture-to-power.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)

    # Space heating flow:
    dm_agr_electricity = dm.filter_w_regex({'Variables': 'agr_energy-demand_electricity'})

    return dm_agr_electricity

#######################################################################################################################
# CalculationTree - Power - Yearly Production
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

    #######################################################
    # CalculationLeafs - Net production (fuel based, self-consumption) [GWh]
    #######################################################
    # Tuto: Tree Split & constants
    cdm_self_consumption = cdm_const['constant_1']
    idx_const = cdm_self_consumption.idx
    dm_fb_capacity = dm_capacity.filter_w_regex({'Categories1': 'biogas|biomass|coal|gas|oil|nuclear'})
    ay_self_consumption = dm_fb_capacity.array[:, :, idx_cap['pow_gross-yearly-production'], :] \
                          * cdm_self_consumption.array[np.newaxis, np.newaxis,
                            idx_const['cp_power-unit-self-consumption'],:]
    dm_fb_capacity.add(ay_self_consumption, dim='Variables', col_label='pow_net-yearly-production', unit='GWh')

    #########################################
    # CalculationLeafs - Self consumption of power units [GWh]
    #########################################
    # Tuto: Tree parallel (operation)
    dm_fb_capacity.operation('pow_gross-yearly-production', '-', 'pow_net-yearly-production',
                            dim="Variables", out_col='pow_power-loss-self-consumption', unit='GWh')

    #########################################
    # CalculationLeafs - Self consumption of power units [GWh]
    #########################################

    idx_cap = dm_fb_capacity.idx
    cdm_fuel_efficiency = cdm_const['constant_1']
    idx_const = cdm_fuel_efficiency.idx
    ay_fuel_consumption = dm_fb_capacity.array[:, :, idx_cap['pow_gross-yearly-production'], :] \
                          / cdm_fuel_efficiency.array[np.newaxis, np.newaxis,
                            idx_const['cp_fuel-based-power-efficiency'], :]
    dm_fb_capacity.add(ay_fuel_consumption, dim='Variables', col_label='pow_fuel-demand-for-power', unit='GWh')

    #########################################
    # CalculationLeafs - Production share under CCUS [GWh]
    #########################################

    idx_cap = dm_fb_capacity.idx
    idx_ccus = dm_ccus.idx
    ay_ccus_production = dm_fb_capacity.array[:, :, idx_cap['pow_net-yearly-production'], :] \
                          * dm_ccus.array[:, :, idx_ccus['pow_carbon-capture-storage'], idx_ccus['ratio'],np.newaxis]
    dm_fb_capacity.add(ay_ccus_production,
                       dim='Variables', col_label='pow_gross-yearly-production-with-ccs', unit='GWh')

    #########################################
    # CalculationLeafs - Production share without CCUS [GWh]
    #########################################

    idx_cap = dm_fb_capacity.idx
    idx_ccus = dm_ccus.idx
    ay_ccus_production = dm_fb_capacity.array[:, :, idx_cap['pow_net-yearly-production'], :] \
                         * dm_ccus.array[:, :, idx_ccus['pow_carbon-capture-storage'], idx_ccus['reverse-ratio'], np.newaxis]
    dm_fb_capacity.add(ay_ccus_production,
                       dim='Variables', col_label='pow_net-yearly-production-without-ccs', unit='GWh')

    ###########################################################################
    # CalculationLeafs - Net fuel-based production accounting for CCUS process consumption [GWh]
    ###########################################################################

    idx_cap = dm_fb_capacity.idx
    cdm_ccus_efficiency = cdm_const['constant_0']
    idx_const = cdm_ccus_efficiency.idx
    ay_net_production_ccus = dm_fb_capacity.array[:, :, idx_cap['pow_gross-yearly-production-with-ccs'], :] \
                          * cdm_fuel_efficiency.array[np.newaxis, np.newaxis,
                            idx_const['cp_carbon-capture_power-self-consumption'], :]
    dm_fb_capacity.add(ay_net_production_ccus, dim='Variables',
                       col_label='pow_net-yearly-production-with-ccs', unit='GWh')

    ###########################################################################
    # CalculationLeafs - CCUS process consumption [GWh]
    ###########################################################################

    dm_fb_capacity.operation('pow_gross-yearly-production-with-ccs', '-', 'pow_net-yearly-production-with-ccs',
                             dim="Variables", out_col='pow_power-consumption-ccus', unit='GWh')

    #####################################################################################
    # CalculationLeafs - Net power production [GWh] - Fuel based - Accounting for self & CCUS consumption
    #####################################################################################

    dm_fb_capacity.drop(col_label=['pow_net-yearly-production'], dim='Variables')
    dm_fb_capacity.operation('pow_net-yearly-production-with-ccs', '+', 'pow_net-yearly-production-without-ccs',
                             dim="Variables", out_col='pow_net-yearly-production', unit='GWh')

    #####################################################################################
    # CalculationLeafs - Aggregated net power production with no hourly profiles
    #####################################################################################

    # Filter - Energy production with no hourly profile
    dm_fb_np = dm_fb_capacity.filter({'Variables': ['pow_net-yearly-production']})

    # Filter - Renewable energy production
    dm_nfb = dm_capacity.filter({'Variables': ['pow_gross-yearly-production']})
    dm_nfb.rename_col(col_in='pow_gross-yearly-production', col_out='pow_net-yearly-production', dim='Variables')
    dm_nfb = dm_nfb.filter({'Categories1':['hydroelectric','solar-csp','geothermal','marine','solar-pv',
                                           'wind-onshore','wind-offshore']})

    # Data Matrix - Yearly production [GWh]
    dm_yearly_production = dm_fb_np.copy()
    dm_yearly_production.append(dm_nfb, dim='Categories1')

    # Sub Data Matrix - Yearly production [GWh] (no hourly profiles)

    dm_production_np = dm_yearly_production.filter_w_regex({'Categories1': 'hydroelectric|solar-csp|geothermal|marine|'
                                                                    'oil|gas|coal|biomass|biogas|nuclear'})

    # Sum - Total (Categories1) energy production with no hourly profile
    ay_total_np = np.nansum(dm_production_np.array[...], axis=-1)
    dm_production_np.add(ay_total_np, dim='Categories1', col_label='total')

    #####################################################################################
    # CalculationLeafs - Net power production with hourly profiles
    #####################################################################################

    # Sub Data Matrix - Yearly production [GWh] (hourly profiles)

    dm_production_p = dm_yearly_production.filter_w_regex({'Categories1': 'solar-pv|wind-onshore|wind-offshore'})

    return dm_capacity, dm_fb_capacity, dm_production_np, dm_production_p

#######################################################################################################################
# CalculationTree - Power - Building yearly demand
#######################################################################################################################

def yearly_demand_workflow(DM_bld, dm_ind_electricity, dm_amm_electricity, dm_agr_electricity, DM_tra,
                           dm_ind_hydrogen, dm_amm_hydrogen):

    #########################################################################
    # CalculationLeafs - Electricity demand - Appliances [GWh]
    #########################################################################

    #Tuto: Group Tree Merge appender & overwrite

    dm_bld_appliances = DM_bld['appliance']
    ay_x = np.nansum(dm_bld_appliances.array[...],axis=-1)
    dm_bld_appliances.add(ay_x, dim='Categories2', col_label='total')

    #############################################################################
    # CalculationLeafs - Electricity demand - Other sectors [GWh] (no-profiles)
    #############################################################################

    dm_tra_electricity = DM_tra.filter_w_regex({'Categories1': 'other'})
    dm_tra_electricity = dm_tra_electricity.flatten()
    dm_demand_other = dm_tra_electricity.copy()

    # Tuto: Append matrices
    dm_demand_other.append(dm_agr_electricity, dim='Variables')
    dm_demand_other.append(dm_ind_electricity, dim='Variables')
    dm_demand_other.append(dm_amm_electricity, dim='Variables')

    ay_total = np.nansum(dm_demand_other.array[...], axis=-1)
    dm_demand_other.add(ay_total, dim='Variables', col_label='total')

    #############################################################################
    # CalculationLeafs - Electricity demand - Hydrogen [GWh]
    #############################################################################

    dm_tra_hydrogen = DM_tra.filter_w_regex({'Categories1': 'hydrogen'})
    dm_tra_hydrogen = dm_tra_hydrogen.flatten()
    dm_demand_hydrogen = dm_tra_hydrogen.copy()

    dm_demand_hydrogen.append(dm_amm_hydrogen, dim='Variables')
    dm_demand_hydrogen.append(dm_ind_hydrogen, dim='Variables')

    ay_total = np.nansum(dm_demand_hydrogen.array[...], axis=-1)
    dm_demand_hydrogen.add(ay_total, dim='Variables', col_label='total')

    return dm_bld_appliances, dm_demand_other, dm_demand_hydrogen

#######################################################################################################################
# CoreModule - Power
#######################################################################################################################

def power(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    power_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/power.pickle')
    dm_capacity, dm_ccus, cdm_const = read_data(power_data_file,lever_setting)
    dm_climate = simulate_climate_to_power_input()
    dm_agr_electricity = simulate_agriculture_to_power_input()
    DM_bld = simulate_buildings_to_power_input()
    dm_ind_electricity, dm_ind_hydrogen = simulate_industry_to_power_input()
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


results_run = local_power_run()