import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database, read_database_w_filter
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data
import pickle
import json
import os
import numpy as np
import time


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


def database_pre_processing():
    # Function developed to migrate from KNIME database eucalc-names to new eucalc-name
    # It modifies _database/data/csv/ directly
    file = 'buildings_fixed-assumptions'
    lever = '`bld_fixed-assumptions`'
    edit_database(file, lever, column='lever', mode='rename',
                  pattern={lever: 'bld_fixed-assumptions'})
    lever = 'bld_fixed-assumptions'
    edit_database(file, lever, column='eucalc-name', mode='rename',pattern={'bld_CO2-factors': 'bld_CO2-factors-GHG'},
                  filter_dict={'eucalc-name': '_CH4|_N2O|_SO2'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_heatcool-efficiency': 'bld_heatcool-efficiency-reference-year'},
                  filter_dict={'eucalc-name': 'reference-year'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_reference-year': ''},
                  filter_dict={'eucalc-name': 'bld_heatcool-efficiency'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_hot-water-demand': 'bld_hot-water-demand-non-residential'},
                  filter_dict={'eucalc-name': '_non-residential'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_non-residential': ''},
                  filter_dict={'eucalc-name': 'bld_hot-water-demand'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_hot-water-demand': 'bld_hot-water-demand-residential'},
                  filter_dict={'eucalc-name': '_residential'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_residential': ''},
                  filter_dict={'eucalc-name': 'bld_hot-water-demand'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_residential_cooking': 'bld_residential-cooking-energy-demand'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_energy-demand': ''},
                  filter_dict={'eucalc-name': 'bld_residential-cooking-energy-demand'})

    file = 'buildings_heatcool-technology-fuel'
    lever = 'heatcool-technology-fuel'

    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_residential': '-residential'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_non-residential': '-nonresidential'})
    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'_reference-year': '-reference-year'})

    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_heatcool-technology-fuel': 'bld_heatcool-technology-fuel_residential'},
                  filter_dict={'eucalc-name': '-residential'})
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'-residential': ''})

    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_heatcool-technology-fuel': 'bld_heatcool-technology-fuel_nonresidential'},
                  filter_dict={'eucalc-name': '-nonresidential'})
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'-nonresidential': ''})

    edit_database(file, lever, column='eucalc-name', mode='rename',
                  pattern={'bld_heatcool-technology-fuel': 'bld_heatcool-technology-fuel_reference-year'},
                  filter_dict={'eucalc-name': '-reference-year'})
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'-reference-year': ''})

    return


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

    # Read renovation data
    file = 'buildings_building-renovation-rate'
    lever = 'building-renovation-rate'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[2, 1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name', group_list=['bld_building.*', 'bld_energy.*'])
    # Reads appliance efficiency
    file = 'buildings_appliance-efficiency'
    lever = 'appliance-efficiency'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    # Read climate lever
    # file = 'buildings_climate'
    # lever = 'climate'
    # dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
    #                                                    dict_ots=dict_ots, dict_fts=dict_fts)

    # Read district-heating share
    file = 'buildings_district-heating-share'
    lever = 'district-heating-share'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    # Read heatcool-efficiency share
    file = 'buildings_heatcool-efficiency'
    lever = 'heatcool-efficiency'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    file = 'buildings_heatcool-technology-fuel'
    lever = 'heatcool-technology-fuel'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['bld_heat-district-technology', 'bld_heatcool-technology'])

    #file = 'buildings_residential-appeff'
    #lever = 'residential-appeff'
    #dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
    #                                                            years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Read fixed assumptions & create dict_fxa
    file = 'buildings_fixed-assumptions'
    dict_fxa = {}
    # this is just a dataframe of zeros
    # df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_CO2-factors-GHG'})
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_CO2-factors_'})
    dm_emissions = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['emissions'] = dm_emissions
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_heatcool-efficiency|bld_hot-water-demand|bld_residential-cooking|bld_space-cooling-energy-demand"})
    dm_energy = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['energy'] = dm_energy
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_appliance-efficiency|bld_conversion-rates|bld_fixed-assumptions|bld_heat-district_energy-demand|cp_|lfs_|bld_lighting-demand"})
    dm_various = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['various'] = dm_various
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_appliance-lifetime|bld_capex.*#'})
    dm_appliances = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['appliances'] = dm_appliances
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_building-mix|bld_floor-area-previous-year|bld_floor-area"})
    dm_bld_type = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['bld_type'] = dm_bld_type
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_building-renovation-energy-achieved|bld_capex_.*Mm2"})
    dm_bld_double = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['bld_double'] = dm_bld_double
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_surface-per-floorarea"})
    dm_surface = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['surface'] = dm_surface

    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_emission-factor_CO2.*',
                                                    num_cat=1)

    # group all datamatrix in a single structure
    DM_buildings = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        'constant': cdm_const
    }

    # write datamatrix to pickle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/buildings.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_buildings, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return

def read_data(data_file, lever_setting):

    with open(data_file, 'rb') as handle:
        DM_buildings = pickle.load(handle)

    # Read fts based on lever_setting
    DM_ots_fts = read_level_data(DM_buildings, lever_setting)

    DM_floor_area = {
        'buildings_rates': DM_ots_fts['building-renovation-rate']['bld_building'].filter_w_regex({'Variables': '.*rate'}),
        'floor_area': DM_buildings['fxa']['bld_type'].filter_w_regex({'Variables': 'bld_floor-area.*'}),
        'building_mix': DM_buildings['fxa']['bld_type'].filter_w_regex({'Variables': 'bld_building-mix.*', 'Categories1': '.*households'})
    }


    return DM_floor_area



def simulate_lifestyles_to_buildings_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-buildings.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)
    dm_lfs_appliance = dm.filter_w_regex({'Variables': 'appliance|substitution-rate'})
    dm_lfs_appliance.deepen()
    dm_lfs_floor = dm.filter_w_regex({'Variables': 'lfs_floor-space_cool|lfs_floor-space_total'})
    dm_lfs_other = dm.filter_w_regex({'Variables': 'lfs_household_population|lfs_heatcool-behaviour_degrees|lighting'})
    DM_lfs = {
        'appliance': dm_lfs_appliance,
        'floor': dm_lfs_floor,
        'other': dm_lfs_other
    }
    return DM_lfs


def floor_area_workflow(DM_floor_area, dm_lfs):

    dm_building_mix = DM_floor_area['building_mix']
    idx_b = dm_building_mix.idx
    idx = dm_lfs.idx
    # Floor area single (multi) family household [m2] = floor-space_total [m2] * building-mix single (multi) family household [%]
    ay_floor_area = dm_building_mix.array[:, :, idx_b['bld_building-mix'], :] \
                    * dm_lfs.array[:, :, idx['lfs_floor-space_total'], np.newaxis]
    dm_building_mix.add(ay_floor_area, dim='Variables', col_label='bld_floor-area', unit='1000m2')
    # Compute lagged floor area for residential
    dm_building_mix.lag_variable('bld_floor-area', shift=1, subfix='-previous-year')
    # Update floor area values for residential
    dm_floor_area = DM_floor_area['floor_area']
    idx_f = dm_floor_area.idx
    idx_b = dm_building_mix.idx
    categories = ['multi-family-households', 'single-family-households']
    for cat in categories:
        dm_floor_area.array[:, :, idx_f['bld_floor-area'], idx_f[cat]] = \
            dm_building_mix.array[:, :, idx_b['bld_floor-area'], idx_b[cat]]
        dm_floor_area.array[:, :, idx_f['bld_floor-area-previous-year'], idx_f[cat]] = \
            dm_building_mix.array[:, :, idx_b['bld_floor-area-previous-year'], idx_b[cat]]

    # Change units to million m2
    dm_floor_area.array = dm_floor_area.array/1000
    dm_floor_area.units['bld_floor-area'] = 'Mm2'

    # Floor area increase (t) [Mm2] = floor-area (t) [Mm2] - floor-area (t-1) [Mm2]
    dm_floor_area.operation('bld_floor-area', '-', 'bld_floor-area-previous-year', out_col='bld_floor-area-increase', unit='Mm2')

    dm_rates = DM_floor_area['buildings_rates']

    # Floor area demolished (t) [Mm2] = floor-area (t-1) [Mm2] * demolition-rate-exi (t) [%]
    dm_demolition = dm_rates.filter({'Variables': ['bld_building-demolition-rate'], 'Categories2': ['exi']})
    arr_demolition = dm_demolition.array[:, :, 0, :, 0]
    dm_floor_area.add(arr_demolition, dim='Variables', col_label='bld_building-demolition-rate', unit='%')
    dm_floor_area.operation('bld_floor-area-previous-year', '*', 'bld_building-demolition-rate', out_col='bld_floor-area-demolished', unit='Mm2')

    # New area constructed [Mm2] = Area demolished + Area increase
    dm_floor_area.operation('bld_building-demolition-rate', '+', 'bld_floor-area-increase', out_col='bld_floor-area-constructed', unit='Mm2')
    # Remove negative
    idx = dm_floor_area.idx
    dm_floor_area.array[:, :, idx['bld_floor-area-constructed'], :] = \
        np.where(dm_floor_area.array[:, :, idx['bld_floor-area-constructed'], :] < 0, 0, dm_floor_area.array[:, :, idx['bld_floor-area-constructed'], :])

    # renovated area [Mm2] = renovation-rate [%] * floor area [Mm2]
    idx_r = dm_rates.idx
    idx_f = dm_floor_area.idx
    arr_renovated = dm_rates.array[:, :, idx_r['bld_building-renovation-rate'], :, idx_r['exi']] \
                    * dm_floor_area.array[:, :, idx_f['bld_floor-area'], :]
    dm_floor_area.add(arr_renovated, dim='Variables', col_label='bld_floor-area-renovated', unit='Mm2')

    # Compute cumulation of demolished renovated and constructed area from baseyear onwards
    # Note that the rates already accounted for the fact that we only have one in 5 years
    variables = ['bld_floor-area-demolished', 'bld_floor-area-constructed', 'bld_floor-area-renovated']
    baseyear = 2015
    idx = dm_floor_area.idx
    for var in variables:
        # comulate dum of constructed, demolished, renovated
        dm_floor_area.array[:, idx[baseyear]+1:, idx[var], :] = np.cumsum(dm_floor_area.array[:, idx[baseyear]+1:, idx[var], :], axis=1)
        # set ots years to 0
        dm_floor_area.array[:, 0:idx[baseyear]+1, idx[var], :] = 0
        # rename the variable
        new_var = var.replace('bld_', 'bld_cumulated-')
        dm_floor_area.rename_col(var, new_var, dim='Variables')

    # Keep only floor area and cumulated floor area
    dm_floor_area.drop(col_label=['bld_floor-area-previous-year', 'bld_floor-area-increase', 'bld_building-demolition-rate'], dim='Variables')


    return


def buildings(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    buildings_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/buildings.pickle')
    # Read data into workflow datamatrix dictionaries
    DM_floor_area = read_data(buildings_data_file, lever_setting)

    # Simulate lifestyle input
    DM_lfs = simulate_lifestyles_to_buildings_input()
    cntr_list = DM_floor_area['floor_area'].col_labels['Country']
    for key in DM_lfs.keys():
        DM_lfs[key] = DM_lfs[key].filter({'Country': cntr_list})

    # Floor area workflow
    floor_area_workflow(DM_floor_area, DM_lfs['floor'])


def buildings_local_run():
    # Function to run module as stand alone without other modules/converter or TPE
    years_setting, lever_setting = init_years_lever()
    buildings(lever_setting, years_setting)
    return


#database_from_csv_to_datamatrix() 
#buildings_local_run()
