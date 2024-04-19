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
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'bld_CO2-factors': 'bld_CO2-factors-GHG'},
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

    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'residential': 'residential_current'})
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'reference-year_residential_current': 'residential_reference-year'})
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'reference-year_nonresidential_current': 'nonresidential_reference-year'})

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
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_building-renovation-energy-achieved"})
    dm_ren_energy = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['renovation-energy'] = dm_ren_energy
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_capex_.*Mm2"})
    dm_capex = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['capex'] = dm_capex
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
        'building_mix': DM_buildings['fxa']['bld_type'].filter_w_regex({'Variables': 'bld_building-mix.*', 'Categories1': '.*households'}),
        'surface-per-floorarea': DM_buildings['fxa']['surface']
    }

    DM_energy = {
        'building_mix': DM_ots_fts['building-renovation-rate']['bld_building'].filter_w_regex({'Variables': '.*mix'}).copy(),
        'heating': DM_ots_fts['building-renovation-rate']['bld_energy'].filter({'Variables': ['bld_energy-need_space-heating']}),
        'heatcool-tech-fuel': DM_ots_fts['heatcool-technology-fuel']['bld_heatcool-technology'],
        'renovation-energy': DM_buildings['fxa']['renovation-energy'],
        'heatcool-efficiency': DM_buildings['fxa']['energy'].filter({'Variables': ['bld_heatcool-efficiency', 'bld_heatcool-efficiency-reference-year']}),
        'district-heating': DM_ots_fts['district-heating-share']
    }


    cdm_const = DM_buildings['constant']

    return DM_floor_area, DM_energy, cdm_const


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


def simulate_climate_to_buildings_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-climate-to-buildings.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)
    dm_clm_energy = dm.filter_w_regex({'Variables': 'bld_climate-impact-space'})
    dm_clm_energy.deepen()
    dm_clm_average = dm.filter_w_regex({'Variables': 'bld_climate-impact_average'})
    DM_clm = {
        'climate-impact-space': dm_clm_energy,
        'climate-impact-average': dm_clm_average
    }
    return DM_clm


def bld_floor_area_workflow(DM_floor_area, dm_lfs, baseyear):
    # Floor area and material workflow

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
    dm_floor_area.operation('bld_floor-area', '-', 'bld_floor-area-previous-year',
                            out_col='bld_cumulated-floor-area-increase', unit='Mm2')

    dm_rates = DM_floor_area['buildings_rates']

    # Floor area demolished (t) [Mm2] = floor-area (t-1) [Mm2] * demolition-rate-exi (t) [%]
    dm_demolition = dm_rates.filter({'Variables': ['bld_building-demolition-rate'], 'Categories2': ['exi']})
    arr_demolition = dm_demolition.array[:, :, 0, :, 0]
    dm_floor_area.add(arr_demolition, dim='Variables', col_label='bld_building-demolition-rate', unit='%')
    dm_floor_area.operation('bld_floor-area-previous-year', '*', 'bld_building-demolition-rate', out_col='bld_floor-area-demolished', unit='Mm2')

    # New area constructed [Mm2] = Area demolished + Area increase
    dm_floor_area.operation('bld_building-demolition-rate', '+', 'bld_cumulated-floor-area-increase', out_col='bld_floor-area-constructed', unit='Mm2')
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

    #################
    ### MATERIALS ###
    #################

    # Floor area renovated and constructed for fts take into account the gap years
    # Therefore to obtain the renovated and construction areas only for the year of interest
    # we need to devide by 1 for ots and 5 for fts
    gap_years = np.array(dm_floor_area.col_labels['Years'][1:]) - np.array(dm_floor_area.col_labels['Years'][:-1])
    gap_years = np.concatenate(([1], gap_years))
    arr_renovated = dm_floor_area.array[:, :, idx['bld_floor-area-renovated'], :]/gap_years[np.newaxis, :, np.newaxis]
    arr_constructed = dm_floor_area.array[:, :, idx['bld_floor-area-constructed'], :]/gap_years[np.newaxis, :, np.newaxis]
    dm_surface = DM_floor_area['surface-per-floorarea']
    idx = dm_surface.idx
    arr_surf_renovated = dm_surface.array[:, :, idx['bld_surface-per-floorarea'], :, :] * arr_renovated[..., np.newaxis]
    arr_surf_constructed = dm_surface.array[:, :, idx['bld_surface-per-floorarea'], :, :] * arr_constructed[..., np.newaxis]
    dm_surface.add(arr_surf_renovated, dim='Variables', col_label='bld_renovated-surface-area-renovated', unit='Mm2')
    dm_surface.add(arr_surf_constructed, dim='Variables', col_label='bld_renovated-surface-area-constructed', unit='Mm2')
    del arr_surf_constructed, arr_constructed, arr_demolition, arr_renovated, arr_surf_renovated

    # Compute cumulation of demolished renovated and constructed area from baseyear onwards
    # Note that the rates already accounted for the fact that we only have one in 5 years
    variables = ['bld_floor-area-demolished', 'bld_floor-area-constructed', 'bld_floor-area-renovated']
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
    dm_floor_area.drop(col_label=['bld_floor-area-previous-year', 'bld_building-demolition-rate'], dim='Variables')

    dm_floor_area.operation('bld_cumulated-floor-area-constructed', '+', 'bld_cumulated-floor-area-renovated',
                            out_col= 'bld_floor-area-new-and-renovated', unit='Mm2')

    dm_floor_area.operation('bld_floor-area', '-', 'bld_floor-area-new-and-renovated',
                            out_col='bld_cumulated-floor-area-unrenovated', unit='Mm2')

    return dm_floor_area


def bld_energy_workflow(DM_energy, DM_clm, dm_floor_area, cdm_const):
    # Compute renovation area by building type (e.g. office, households, ..)
    # and renovation type aka depth (e.g. dep, exi, med, shl)
    dm_mix = DM_energy['building_mix']
    idx_m = dm_mix.idx
    idx_f = dm_floor_area.idx
    arr_renovated_area_mix = dm_floor_area.array[:, :, idx_f['bld_cumulated-floor-area-renovated'], :, np.newaxis] \
                             * dm_mix.array[:, :, idx_m['bld_building-renovation-mix'], :, :]
    dm_mix.add(arr_renovated_area_mix, dim='Variables', col_label='bld_cumulated-floor-area-renovated', unit='Mm2')
    del arr_renovated_area_mix

    # Compute construction mix by building type and depth
    idx_m = dm_mix.idx
    arr_construction_area_mix = dm_floor_area.array[:, :, idx_f['bld_cumulated-floor-area-constructed'], :, np.newaxis]\
                                * dm_mix.array[:, :, idx_m['bld_building-construction-mix'], :, :]
    dm_mix.add(arr_construction_area_mix, dim='Variables', col_label='bld_cumulated-floor-area-constructed', unit='Mm2')
    del arr_construction_area_mix

    # Climate impacts
    # climate impacts are considered through the temperature impacts on heating demand
    dm_renovation_energy = DM_energy['renovation-energy']
    ## Add dummy 'exi' to dm_renovation_energy
    nan_arr = np.nan * np.ones(dm_renovation_energy.array[:, :, :, 0, :].shape)
    dm_renovation_energy.add(nan_arr, dim='Categories1', col_label='exi')
    dm_renovation_energy.sort(dim='Categories1')
    ## Multiply climate impact by energy achieved
    dm_clm_impact_space = DM_clm['climate-impact-space']
    idx_c = dm_clm_impact_space.idx
    idx_r = dm_renovation_energy.idx
    arr_renovation_energy = dm_clm_impact_space.array[:, :, idx_c['bld_climate-impact-space-heating'], :, np.newaxis] \
                            * dm_renovation_energy.array[:, :, idx_r['bld_building-renovation-energy-achieved'], :, :]
    dm_renovation_energy.array[:, :, idx_r['bld_building-renovation-energy-achieved'], :, :] = arr_renovation_energy
    del arr_renovation_energy, nan_arr, idx_r

    # energy need space heating = climate impact space heating * energy need
    dm_heating = DM_energy['heating']
    idx_h = dm_heating.idx
    arr = dm_clm_impact_space.array[:, :, idx_c['bld_climate-impact-space-heating'], :, np.newaxis] \
          * dm_heating.array[:, :, idx_h['bld_energy-need_space-heating'], np.newaxis, :]
    arr = np.moveaxis(arr, -2, -1)  # invert the position of the last two axis
    dm_mix.add(arr, col_label='bld_energy-need-climate-impact_space-heating', dim='Variables', unit='kwh/m2/year')
    del arr, idx_h, idx_c, dm_clm_impact_space, dm_heating

    # add dummy 'other' category to dm_renovation_energy
    dm_renovation_energy.add(np.nan, dim='Categories2', col_label='other', dummy=True)
    dm_renovation_energy.sort(dim='Categories2')

    # Switch the position of Categories1 and Categories1 for dm_renovation_energy
    dm_renovation_energy.array = np.moveaxis(dm_renovation_energy.array, -2, -1)
    tmp = dm_renovation_energy.col_labels['Categories1']
    dm_renovation_energy.col_labels['Categories1'] = dm_renovation_energy.col_labels['Categories2']
    dm_renovation_energy.col_labels['Categories2'] = tmp
    # join renovation energy achieved with energy mix
    dm_mix.append(dm_renovation_energy, dim='Variables')
    del dm_renovation_energy, tmp

    # energy need space heating [GWh] = renovation-energy-achieved [kWh/m2] * floor area renovated (constructed) [GWh]
    dm_mix.operation('bld_building-renovation-energy-achieved', '*', 'bld_cumulated-floor-area-renovated',
                     out_col='bld_energy-need_space-heating_renovated', unit='GWh')
    dm_mix.operation('bld_building-renovation-energy-achieved', '*', 'bld_cumulated-floor-area-constructed',
                     out_col='bld_energy-need_space-heating_constructed', unit='GWh')

    # energy need space heating unrenovated [GWh] = energy need [kWh/m2] * floor area unrenovated (constructed) [GWh]
    idx_f = dm_floor_area.idx
    idx_m = dm_mix.idx
    arr_unren_exi = dm_floor_area.array[:, :, idx_f['bld_cumulated-floor-area-unrenovated'], :] \
        * dm_mix.array[:, :, idx_m['bld_energy-need-climate-impact_space-heating'], :, idx_m['exi']]
    # Put renovated / constructed / unrenovated together
    # Add dummy energy need unrenovated variable and then assign to 'exi' cat the above computation
    dm_mix.add(np.nan, dummy=True, col_label='bld_energy-need_space-heating_unrenovated', dim='Variables', unit='GWh')
    idx_m = dm_mix.idx
    dm_mix.array[:, :, idx_m['bld_energy-need_space-heating_unrenovated'], :, idx_m['exi']] = arr_unren_exi
    del idx_m, idx_f, arr_unren_exi

    # Add constructed, unrenovated, renovated category
    list_var = ['bld_energy-need_space-heating_unrenovated', 'bld_energy-need_space-heating_renovated',
                'bld_energy-need_space-heating_constructed']
    dm_energy_heating = dm_mix.filter({'Variables': list_var})
    dm_energy_heating.deepen(based_on='Variables')
    dm_mix.drop(col_label=list_var, dim='Variables')
    del list_var

    # 'bld_district-heating-space-heating-supply' = energy space heating * district_heating %
    arr_dh_supply = dm_energy_heating.array*DM_energy['district-heating'].array[..., np.newaxis, np.newaxis, np.newaxis]
    dm_energy_heating.add(arr_dh_supply, dim='Variables', col_label='bld_district-heating-space-heating-supply', unit='GWh')
    del arr_dh_supply

    # in house supply = energy need - district heating supply
    dm_energy_heating.operation('bld_energy-need_space-heating', '-', 'bld_district-heating-space-heating-supply',
                                out_col='bld_in-house-space-heating-supply', unit='GWh')

    # Sum bld_energy-need_space-heating
    idx = dm_energy_heating.idx
    arr_energy_by_bld = np.nansum(dm_energy_heating.array[:, :, idx['bld_energy-need_space-heating'], :, :, :], axis=(-1, -2))
    dm_floor_area.add(arr_energy_by_bld, dim='Variables', unit='GWh', col_label='bld_space-heating')
    del arr_energy_by_bld

    # HEATCOOL
    # !FIXME this rename and restructuring could be done before the pickle is created
    # Extract heatcool technology
    dm_heatcool = DM_energy['heatcool-tech-fuel'].filter_w_regex({'Variables': '.*residential.*'})
    dm_heatcool.deepen(based_on='Variables')
    # Extract heatcool efficiency
    dm_heatcool_eff = DM_energy['heatcool-efficiency']
    dm_heatcool_eff.rename_col('bld_heatcool-efficiency', 'bld_heatcool-efficiency_current', dim='Variables')
    dm_heatcool_eff.rename_col('bld_heatcool-efficiency-reference-year', 'bld_heatcool-efficiency_reference-year', dim='Variables')
    dm_heatcool_eff.deepen(based_on='Variables')

    dm_heatcool.append(dm_heatcool_eff, dim='Variables')
    del dm_heatcool_eff
    dm_heatcool.operation('bld_heatcool-efficiency', '*', 'bld_heatcool-technology-fuel_residential',
                          out_col='bld_technology-factor_residential', unit='%')
    dm_heatcool.operation('bld_heatcool-efficiency', '*', 'bld_heatcool-technology-fuel_nonresidential',
                          out_col='bld_technology-factor_nonresidential', unit='%')

    # multiply space heating energy demand with technology factor for residential and nonresidential buildings
    dm_heating_res = dm_floor_area.filter({'Variables': ['bld_space-heating'],
                                                  'Categories1': ['multi-family-households', 'single-family-households']})
    dm_heating_nonres = dm_floor_area.filter({'Variables': ['bld_space-heating']})
    dm_heating_nonres.drop(dim='Categories1', col_label=['single-family-households', 'multi-family-households'])

    idx_h = dm_heatcool.idx
    arr_res = dm_heating_res.array[:, :, 0, np.newaxis, :, np.newaxis] \
              * dm_heatcool.array[:, :, idx_h['bld_technology-factor_residential'], np.newaxis, np.newaxis, :, idx_h['current']]
    arr_nonres = dm_heating_nonres.array[:, :, 0, np.newaxis, :, np.newaxis] \
                 * dm_heatcool.array[:, :, idx_h['bld_technology-factor_nonresidential'], np.newaxis, np.newaxis, :, idx_h['current']]

    # Create new dataframe with categories bld type and fuel type
    res_cols = {
        'Country': dm_heating_res.col_labels['Country'],
        'Years': dm_heating_res.col_labels['Years'],
        'Variables': ['bld_space-heating-energy-demand'],
        'Categories1': dm_heating_res.col_labels['Categories1'],
        'Categories2': dm_heatcool.col_labels['Categories1']
    }
    nonres_cols = {
        'Country': dm_heating_res.col_labels['Country'],
        'Years': dm_heating_res.col_labels['Years'],
        'Variables': ['bld_space-heating-energy-demand'],
        'Categories1': dm_heating_nonres.col_labels['Categories1'],
        'Categories2': dm_heatcool.col_labels['Categories1']
    }
    new_units = {'bld_space-heating-energy-demand': 'GWh'}

    # Join residential and non-residential
    dm_heating = DataMatrix(res_cols, new_units)
    dm_heating.array = arr_res
    dm_heating_nonres = DataMatrix(nonres_cols, new_units)
    dm_heating_nonres.array = arr_nonres
    dm_heating.append(dm_heating_nonres, dim='Categories1')
    del dm_heating_res, dm_heating_nonres, idx, idx_h, new_units, arr_nonres, arr_res, res_cols, nonres_cols

    # Sum floor area and energy-need over building type
    idx = dm_mix.idx
    arr_renovated = np.nansum(dm_mix.array[:, :, idx['bld_cumulated-floor-area-renovated'], :, :], axis=-2)
    arr_constructed = np.nansum(dm_mix.array[:, :, idx['bld_cumulated-floor-area-constructed'], :, :], axis=-2)
    idx = dm_floor_area.idx
    arr_unrenovated = np.nansum(dm_floor_area.array[:, :, idx['bld_cumulated-floor-area-unrenovated'], :], axis=-1)
    arr_demolished = np.nansum(dm_floor_area.array[:, :, idx['bld_cumulated-floor-area-demolished'], :], axis=-1)

    idx = dm_energy_heating.idx
    arr_energy_need = np.nansum(dm_energy_heating.array[:, :, idx['bld_energy-need_space-heating'], :, :, :], axis=-3)

    # Create datamatrix by depth
    col_labels = {
        'Country': dm_mix.col_labels['Country'].copy(),
        'Years': dm_mix.col_labels['Years'].copy(),
        'Variables': ['bld_floor-area-renovated'],
        'Categories1': dm_mix.col_labels['Categories2'].copy()
    }
    dm_depth = DataMatrix(col_labels, units={'bld_floor-area-renovated': 'Mm2'})
    dm_depth.array = arr_renovated[:, :, np.newaxis, :]
    dm_depth.add(arr_constructed, dim='Variables', col_label='bld_floor-area-constructed', unit='Mm2')
    dm_depth.add(np.nan, dim='Variables', col_label=['bld_floor-area-unrenovated', 'bld_floor-area-demolished'],
                 unit=['Mm2', 'Mm2'], dummy=True)
    idx = dm_depth.idx
    dm_depth.array[:, :, idx['bld_floor-area-unrenovated'], idx['exi']] = arr_unrenovated
    dm_depth.array[:, :, idx['bld_floor-area-demolished'], idx['exi']] = arr_demolished

    # Add energy to dataframe
    # Build the col_labels
    var_name_list = []
    for cat in dm_energy_heating.col_labels['Categories3']:
        var_name_list.append('bld_energy-demand-space-heating-' + cat)
    # Switch the last two axis
    arr_energy_need = np.moveaxis(arr_energy_need, -2, -1)
    dm_depth.add(arr_energy_need, dim='Variables', col_label=var_name_list, unit=['GWh', 'GWh', 'GWh'])
    del arr_constructed, arr_demolished, arr_energy_need, arr_renovated, arr_unrenovated, col_labels, cat, var_name_list

    ###################
    ###  EMISSIONS  ###
    ###################
    # Filter emissions from fuel used in building
    cdm_const = cdm_const.filter({'Categories1': dm_heating.col_labels['Categories2']})
    # Compute emissions by building type and fuel
    arr_emissions = cdm_const.array[np.newaxis, np.newaxis, :, np.newaxis, :] * dm_heating.array/1000  # converts to TWh
    dm_heating.add(arr_emissions, dim='Variables', col_label='bld_CO2-emissions', unit='Mt')
    # Compute emissions by building type
    idx = dm_heating.idx
    arr_CO2_by_bld = np.nansum(dm_heating.array[:, :, idx['bld_CO2-emissions'], :, :], axis=-1)
    dm_floor_area.add(arr_CO2_by_bld, dim='Variables', col_label='bld_CO2-emissions', unit='Mt')
    # Compute emissions by fuel type
    arr_CO2_by_fuel = np.nansum(dm_heating.array[:, :, idx['bld_CO2-emissions'], :, :], axis=-2)
    cols_by_fuel = {
        'Country': dm_heating.col_labels['Country'].copy(),
        'Years': dm_heating.col_labels['Years'].copy(),
        'Variables': ['bld_CO2-emissions'],
        'Categories1': dm_heating.col_labels['Categories2'].copy()
    }
    dm_CO2_by_fuel = DataMatrix(cols_by_fuel, units={'bld_CO2-emissions': 'Mt'})
    dm_CO2_by_fuel.array = arr_CO2_by_fuel[:, :, np.newaxis, :]

    # Prepare output
    DM_energy_out = {}

    DM_energy_out['TPE'] = {
        'floor-area_energy-demand': dm_depth,
        'floor-area': dm_floor_area.filter({'Variables': ['bld_floor-area', 'bld_space-heating']})
    }

    DM_energy_out['district-heating'] = {
        'heat-supply': dm_energy_heating.filter({'Variables': ['bld_district-heating-space-heating-supply']}),
        'heat-electricity': dm_heating.filter({'Variables': ['bld_space-heating-energy-demand'],
                                               'Categories2': ['electricity']})
    }

    DM_energy_out['air-pollution'] = {
        'energy-demand': dm_heating.filter({'Variables': ['bld_space-heating-energy-demand'],
                                            'Categories2': ['electricity', 'gas-ff-natural', 'heat-ambient',
                                                            'liquid-ff-heatingoil', 'solid-bio', 'solid-ff-coal']})
    }

    DM_energy_out['agriculture'] = {
        'energy-demand': dm_heating.filter({'Variables': ['bld_space-heating-energy-demand'],
                                            'Categories2': ['liquid-bio-gasoline', 'liquid-bio-diesel', 'gas-bio', 'solid-bio']})
    }

    DM_energy_out['emissions'] = {
        'heat-emissions-by-bld':  dm_floor_area.filter({'Variables': ['bld_CO2-emissions']}),
        'heat-emissions-by-fuel': dm_CO2_by_fuel
    }

    DM_energy_out['wf_materials'] = {
        'area_increase_unrenovated': dm_floor_area.filter_w_regex({'Variables': '.*increase|.*unrenovated|.*demolished'}),
        'area_constructed_renovated': dm_mix.filter_w_regex({'Variables': '.*renovated|.*constructed'})
    }

    DM_energy_out['wf_costs'] = {
        'households-dh': dm_energy_heating.filter_w_regex({'Variables': 'bld_district-heating-space-heating-supply',
                                                           'Categories1': '.*households'})
    }

    return DM_energy_out



def buildings(lever_setting, years_setting):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    buildings_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/buildings.pickle')
    # Read data into workflow datamatrix dictionaries
    DM_floor_area, DM_energy, cdm_const = read_data(buildings_data_file, lever_setting)

    # Simulate lifestyle input
    DM_lfs = simulate_lifestyles_to_buildings_input()
    cntr_list = DM_floor_area['floor_area'].col_labels['Country']
    for key in DM_lfs.keys():
        DM_lfs[key] = DM_lfs[key].filter({'Country': cntr_list})

    DM_clm = simulate_climate_to_buildings_input()
    cntr_list = DM_floor_area['floor_area'].col_labels['Country']
    for key in DM_clm.keys():
        DM_clm[key] = DM_clm[key].filter({'Country': cntr_list})

    # Floor area workflow
    baseyear = years_setting[1]
    dm_floor_area = bld_floor_area_workflow(DM_floor_area, DM_lfs['floor'], baseyear)
    DM_energy_wf = bld_energy_workflow(DM_energy, DM_clm, dm_floor_area, cdm_const)



    return


def buildings_local_run():
    # Function to run module as stand alone without other modules/converter or TPE
    years_setting, lever_setting = init_years_lever()
    buildings(lever_setting, years_setting)
    return


#database_from_csv_to_datamatrix()
#buildings_local_run()

