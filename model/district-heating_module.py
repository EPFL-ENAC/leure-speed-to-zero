# Import Python packages
import pandas as pd
import pickle
import json
import os
import numpy as np
import warnings
import time

# Import classes
from model.common.data_matrix_class import DataMatrix
from model.common.interface_class import Interface
from model.common.constant_data_matrix_class import ConstantDataMatrix

# Import functions
from model.common.io_database import read_database, read_database_fxa, edit_database, read_database_w_filter
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data

warnings.simplefilter("ignore")


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


def database_from_csv_to_datamatrix():

    # Read database
    # Set years range
    years_setting, lever_setting = init_years_lever()
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int))
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int))
    years_all = years_ots + years_fts

    dict_ots = {}
    dict_fts = {}

    # Read heatcool-efficiency share
    file = 'buildings_heatcool-efficiency'
    lever = 'heatcool-efficiency'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    file = 'buildings_heatcool-technology-fuel'
    lever = 'heatcool-technology-fuel'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['bld_heat-district-technology'])

    # Read fixed assumptions & create dict_fxa
    file = 'district-heating_fixed-assumptions'
    dict_fxa = {}
    # this is just a dataframe of zeros
    # df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_CO2-factors-GHG'})
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_district-capacity_'})
    dm_dhg_capacity = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['dhg-capacity'] = dm_dhg_capacity
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_district-fixed-assumptions_'})
    dm_dhg_replacement = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['dhg-replacement-rate'] = dm_dhg_replacement

    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_emission-factor_.*',
                                                    num_cat=2)

    # group all datamatrix in a single structure
    DM_district_heating = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        'constant': cdm_const
    }

    # write datamatrix to pickle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/district-heating.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_district_heating, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return


def read_data(data_file, lever_setting):

    with open(data_file, 'rb') as handle:
        DM_district_heating = pickle.load(handle)

    # Read fts based on lever_setting
    DM_ots_fts = read_level_data(DM_district_heating, lever_setting)

    dm = DM_ots_fts['heatcool-efficiency']
    dm.append(DM_ots_fts['heatcool-technology-fuel']['bld_heat-district-technology'], dim='Variables')

    cdm_const = DM_district_heating['constant']

    return dm, cdm_const


def simulate_power_to_district_heating_input():

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file = 'All-Countries-interface_from-power-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df = pd.read_excel(file_path, sheet_name="default")
    dm_pow = DataMatrix.create_from_df(df, num_cat=0)
    return dm_pow


def simulate_industry_to_district_heating_input():

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file = 'All-Countries-interface_from-industry-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df = pd.read_excel(file_path, sheet_name="default")
    dm_ind = DataMatrix.create_from_df(df, num_cat=0)

    return dm_ind


def simulate_buildings_to_district_heating_input():

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file = 'All-Countries-interface_from-buildings-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df = pd.read_excel(file_path)
    dm_bld = DataMatrix.create_from_df(df, num_cat=0)
    dm_elec = dm_bld.filter_w_regex({'Variables': 'bld_electricity-demand.*'})
    dm_elec.deepen_twice()
    dm_heat_supply = dm_bld.filter_w_regex({'Variables': 'bld_district-heating.*'})
    dm_heat_supply.deepen()

    DM_bld = {
        'electricity-demand': dm_elec,
        'district-heat-demand': dm_heat_supply
    }
    return DM_bld


def bld_energy_demand_workflow(dm_dhg, dm_bld, dm_pow, dm_ind):
    # technology-fuel-% * efficiency-by-fuel
    dm_dhg.operation('bld_heat-district-efficiency', '*', 'bld_heat-district-technology-fuel',
                     out_col='dhg_energy-need-technology-share', unit='%')
    idx_d = dm_dhg.idx
    # Normalise the energy-need
    dm_dhg.array[:, :, idx_d['dhg_energy-need-technology-share'], :] \
        = dm_dhg.array[:, :, idx_d['dhg_energy-need-technology-share'], :]\
        / np.nansum(dm_dhg.array[:, :, idx_d['dhg_energy-need-technology-share'], :], axis=-1, keepdims=True)
    dm_dhg.drop(dim='Variables', col_label=['bld_heat-district-technology-fuel'])

    # sum space heating residential + non-residential demand
    dm_bld.group_all(dim='Categories1')
    idx_b = dm_bld.idx
    idx_t = dm_dhg.idx
    # note: from GWh to TWh
    arr_energy_by_tech = dm_dhg.array[:, :, idx_t['dhg_energy-need-technology-share'], :] \
                         * dm_bld.array[:, :, idx_b['bld_district-heating-space-heating-supply'], np.newaxis]/1000
    dm_dhg.add(arr_energy_by_tech, dim='Variables', col_label='dhg_energy-need', unit='TWh')
    # !FIXME: we have already multiplied by the efficiency earlier, check if this is correct
    # energy-need-by-fuel * efficiency-by-fuel
    dm_dhg.operation('dhg_energy-need', '*', 'bld_heat-district-efficiency', out_col='dhg_energy-demand-prelim', unit='TWh')

    # Summ all energy need
    dm_tot_demand = dm_dhg.filter({'Variables': ['dhg_energy-demand-prelim']})
    dm_tot_demand.group_all(dim='Categories1')

    # Share of energy need not from waste
    dm_tot_demand.append(dm_ind, dim='Variables')
    dm_tot_demand.operation('dhg_energy-demand-prelim', '-', 'ind_supply_heat-waste', out_col='dhg_diff', unit='TWh')
    dm_tot_demand.operation('dhg_diff', '/', 'dhg_energy-demand-prelim',
                            out_col='dhg_energy-demand-share_heat-district-addition', unit='%')
    ## If less than 0, replace with 0
    var = 'dhg_energy-demand-share_heat-district-addition'
    idx = dm_tot_demand.idx
    dm_tot_demand.array[:, :, idx[var]] = np.maximum(dm_tot_demand.array[:, :, idx[var]], 0)

    # Filter heat supply from CHP, sum bio + fossil, rename
    dm_CHP = dm_pow.filter({'Variables': ['elc_heat-supply-CHP_bio', 'elc_heat-supply-CHP_fossil']})
    dm_CHP.deepen()
    dm_CHP.group_all(dim='Categories1')
    dm_CHP.rename_col('elc_heat-supply-CHP', 'dhg_energy-demand_contribution_CHP', dim='Variables')
    del dm_pow

    # !FIXME: you are here, which coincides with the max-in-args math formula

    return


def district_heating(lever_setting, years_setting, interface=Interface()):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    district_heating_data_file = os.path.join(current_file_directory,
                                              '../_database/data/datamatrix/district-heating.pickle')
    dm_dhg, cdm_const = read_data(district_heating_data_file, lever_setting)

    if interface.has_link(from_sector='power', to_sector='district-heating'):
        dm_pow = interface.get_link(from_sector='power', to_sector='district-heating')
    else:
        dm_pow = simulate_power_to_district_heating_input()

    if interface.has_link(from_sector='industry', to_sector='district-heating'):
        dm_ind = interface.get_link(from_sector='industry', to_sector='district-heating')
    else:
        dm_ind = simulate_industry_to_district_heating_input()

    if interface.has_link(from_sector='buildings', to_sector='district-heating'):
        DM_bld = interface.get_link(from_sector='buildings', to_sector='district-heating')
    else:
        DM_bld = simulate_buildings_to_district_heating_input()

    bld_energy_demand_workflow(dm_dhg, DM_bld['district-heat-demand'], dm_pow, dm_ind)

    return


def district_heating_local_run():
    # Function to run module as stand alone without other modules/converter or TPE
    years_setting, lever_setting = init_years_lever()
    district_heating(lever_setting, years_setting)
    return


# database_from_csv_to_datamatrix()
district_heating_local_run()



def dummy_countries_power():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file = 'EUCalc-interface_from-electricity_supply-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df = pd.read_excel(file_path, sheet_name="default")
    vaud = 1
    eu27 = 1
    paris = 1
    if vaud:
        df_vd = df.loc[df['Country'] == 'Switzerland']
        df_vd['Country'] = 'Vaud'
        df_vd['elc_heat-supply-CHP_bio[TWh]'] = df_vd['elc_heat-supply-CHP_bio[TWh]']*0.1
        df_vd['elc_heat-supply-CHP_fossil[TWh]'] = df_vd['elc_heat-supply-CHP_bio[TWh]']*0.1
        df = pd.concat([df, df_vd], axis=0)
    if eu27:
        df_eu = df.loc[df['Country'] == 'Germany']
        df_eu['Country'] = 'EU27'
        df = pd.concat([df, df_eu], axis=0)
    if paris:
        df_p = df.loc[df['Country'] == 'France']
        df_p['Country'] = 'Paris'
        df_p['elc_heat-supply-CHP_bio[TWh]'] = df_p['elc_heat-supply-CHP_bio[TWh]']*0.19
        df_p['elc_heat-supply-CHP_fossil[TWh]'] = df_p['elc_heat-supply-CHP_bio[TWh]']*0.19
        df = pd.concat([df, df_p], axis=0)
    file = 'All-Countries-interface_from-power-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df.to_excel(file_path, sheet_name="default", index=False)
    return

def dummy_countries_industry():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file = 'EUCalc-interface_from-industry-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df = pd.read_excel(file_path, sheet_name="default")
    vaud = 1
    eu27 = 1
    paris = 1
    if vaud:
        df_vd = df.loc[df['Country'] == 'Switzerland']
        df_vd['Country'] = 'Vaud'
        df = pd.concat([df, df_vd], axis=0)
    if eu27:
        df_eu = df.loc[df['Country'] == 'Germany']
        df_eu['Country'] = 'EU27'
        df = pd.concat([df, df_eu], axis=0)
    if paris:
        df_p = df.loc[df['Country'] == 'France']
        df_p['Country'] = 'Paris'
        df = pd.concat([df, df_p], axis=0)
    file = 'All-Countries-interface_from-industry-to-district-heating.xlsx'
    file_path = os.path.join(current_file_directory, '../_database/data/xls/', file)
    df.to_excel(file_path, sheet_name="default", index=False)
    return

