import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.interface_class import Interface
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database, read_database_w_filter
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data, filter_geoscale, compute_stock
import pickle
import json
import os
import numpy as np
import warnings
import time

warnings.simplefilter("ignore")



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
    df = read_database_fxa(file, filter_dict={'eucalc-name': "bld_appliance-efficiency|bld_conversion-rates|bld_fixed-assumptions|bld_heat-district_energy-demand|cp_|lfs_|bld_lighting-demand|bld_capex_new-pipes"})
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
        'surface-per-floorarea': DM_buildings['fxa']['surface'].copy()
    }

    DM_energy = {
        'building_mix': DM_ots_fts['building-renovation-rate']['bld_building'].filter_w_regex({'Variables': '.*mix'}).copy(),
        'heating': DM_ots_fts['building-renovation-rate']['bld_energy'].filter({'Variables': ['bld_energy-need_space-heating']}),
        'heatcool-tech-fuel': DM_ots_fts['heatcool-technology-fuel']['bld_heatcool-technology'].copy(),
        'renovation-energy': DM_buildings['fxa']['renovation-energy'].copy(),
        'heatcool-efficiency': DM_buildings['fxa']['energy'].filter({'Variables': ['bld_heatcool-efficiency', 'bld_heatcool-efficiency-reference-year']}),
        'district-heating': DM_ots_fts['district-heating-share'].copy()
    }

    dm_appliance = DM_ots_fts['appliance-efficiency'].copy()
    dm_appliance.append(DM_buildings['fxa']['appliances'].filter({'Variables': ['bld_appliance-lifetime']}).copy(), dim='Variables')
    dm_appliance.drop(dim='Categories1', col_label='ac')

    DM_appliances = {
        'appliances': dm_appliance
    }

    DM_costs = {
        'appliances-capex': DM_buildings['fxa']['appliances'].filter({'Variables': ['bld_capex']}),
        'renovation-capex': DM_buildings['fxa']['capex'],
        'other': DM_buildings['fxa']['various'].filter({'Variables': ['bld_heat-district_energy-demand_residential_hot-water',
                                                                      'cp_district-heating_new-pipe-factor',
                                                                      'cp_district-heating_pipe-factor',
                                                                      'bld_capex_new-pipes']})
    }

    # Light heating and cooling workflow data

    DM_light_heat = {
        'ac-efficiency': DM_ots_fts['appliance-efficiency'].filter({'Categories1': ['ac']}),
        'hot-water': DM_buildings['fxa']['various'].filter_w_regex({'Variables': '.*hot-water|.*lighting'}),
        'energy': DM_buildings['fxa']['energy'].filter({'Variables': ['bld_heatcool-efficiency',
                                                                      'bld_hot-water-demand-non-residential',
                                                                      'bld_hot-water-demand-residential',
                                                                      'bld_residential-cooking-energy-demand',
                                                                      'bld_space-cooling-energy-demand_non-residential',
                                                                      'bld_space-cooling-energy-demand_residential']})
    }

    # Split heatcool techology between renewable and fossil
    #!FIXME: heatcool shares by type of fuel should sum to 1, this is mostly the case but some countries are off
    #!FIXME: you should calibrate non-residential + residential to sum to 'heatcool-technology-fuel'
    dm_heatcool = DM_ots_fts['heatcool-technology-fuel']['bld_heatcool-technology'].copy()
    dm_heatcool_renewable_res = dm_heatcool.filter_w_regex({'Variables': 'bld_heatcool-technology-fuel_residential.*',
                                                            'Categories1': 'electricity-heatpumps|heat.*|.*bio|solid-waste'})
    dm_heatcool_fossil = dm_heatcool.filter({'Categories1': ['electricity', 'gas-ff-natural',
                                                             'liquid-ff-heatingoil', 'solid-ff-coal']})
    dm_heatcool_fossil.drop(col_label=['bld_heatcool-technology-fuel'], dim='Variables')

    DM_fuel_switch = {
        'heatcool-shares-renew': dm_heatcool_renewable_res,
        'heatcool-shares-fossil': dm_heatcool_fossil
    }

    cdm_const = DM_buildings['constant']

    return DM_floor_area, DM_energy, DM_appliances, DM_costs, DM_light_heat, DM_fuel_switch, cdm_const


def simulate_lifestyles_to_buildings_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-buildings.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)
    dm_lfs_appliance = dm.filter_w_regex({'Variables': '.*appliance.*|.*substitution-rate.*'})
    dm_lfs_appliance.deepen()
    dm_lfs_floor = dm.filter_w_regex({'Variables': 'lfs_floor-space_cool|lfs_floor-space_total'})
    dm_lfs_other = dm.filter_w_regex({'Variables': 'lfs_heatcool-behaviour_degrees'})
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


def compute_new_area_KNIME_version(dm_floor_area, dm_rates):

    # Floor area increase (t) [Mm2] = floor-area (t) [Mm2] - floor-area (t-1) [Mm2]
    dm_floor_area.operation('bld_floor-area', '-', 'bld_floor-area-previous-year',
                            out_col='bld_floor-area-increase', unit='Mm2')

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

    return dm_floor_area


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
        # previous year floor area is in Mm2, building-mix is in 1000m2
        dm_floor_area.array[:, :, idx_f['bld_floor-area-previous-year'], idx_f[cat]] = \
            dm_building_mix.array[:, :, idx_b['bld_floor-area-previous-year'], idx_b[cat]]/1000

    # Change units to million m2
    dm_floor_area.change_unit('bld_floor-area', 1e-3, '1000m2', 'Mm2')

    #################
    # COMPUTE STOCK #
    #################
    # It uses the total-floor area and the demolition rate to obtain floor area demolished constructed
    # if we want to use the stock function here, the demolition-rate is the renewal-rate,
    # the floor-area is the total stock. the demolished is the 'waste' and the constructed is the 'new'.
    # demolished = total-floor area * demolition rate
    # constructed = demolished + increase
    # dm_floor_area = compute_new_area_KNIME_version(dm_floor_area, DM_floor_area['buildings_rates'])
    dm_floor_area.drop('Variables', 'bld_floor-area-previous-year')
    # !FIXME the values of these rates are off (plot to see) - probably because they were 'cumulated' before
    dm_rr = DM_floor_area['buildings_rates'].filter({'Variables': ['bld_building-demolition-rate'], 'Categories2': ['exi']})
    dm_rr.group_all('Categories2')
    dm_floor_area.append(dm_rr, dim='Variables')
    # call to compute_stock
    compute_stock(dm_floor_area, rr_regex='bld_building-demolition-rate', tot_regex='bld_floor-area',
                  waste_col='bld_floor-area-demolished', new_col='bld_floor-area-constructed', out_type=float)

    # renovated area [Mm2] = renovation-rate [%] * floor area [Mm2]
    dm_rates = DM_floor_area['buildings_rates']
    idx_r = dm_rates.idx
    idx_f = dm_floor_area.idx
    arr_renovated = dm_rates.array[:, :, idx_r['bld_building-renovation-rate'], :, idx_r['exi']] \
                    * dm_floor_area.array[:, :, idx_f['bld_floor-area'], :]
    dm_floor_area.add(arr_renovated, dim='Variables', col_label='bld_floor-area-renovated', unit='Mm2')

    # unrenovated area [Mm2] = total floor area [Mm2] - constructed [Mm2] - renovated [Mm2]
    dm_floor_area.operation('bld_floor-area', '-', 'bld_floor-area-constructed',
                            out_col='bld_floor-area_minus_constructed', unit='Mm2')
    dm_floor_area.operation('bld_floor-area_minus_constructed', '-', 'bld_floor-area-renovated',
                            out_col='bld_floor-area-unrenovated', unit='Mm2')
    dm_floor_area.drop('Variables', 'bld_floor-area_minus_constructed')

    # Save area constructed in output for industry
    dm_constructed = dm_floor_area.filter({'Variables': ['bld_floor-area-constructed']})
    # Save renovated area for Costs
    dm_renovated = dm_floor_area.filter({'Variables': ['bld_floor-area-renovated']})

    #################
    ### MATERIALS ###
    #################

    # Surface-area = floor-area * surface-per-floor-area
    idx_f = dm_floor_area.idx
    dm_surface = DM_floor_area['surface-per-floorarea']
    idx_s = dm_surface.idx
    arr_surf_renovated = dm_surface.array[:, :, idx_s['bld_surface-per-floorarea'], :, :] * \
                         dm_floor_area.array[:, :, idx_f['bld_floor-area-renovated'], :, np.newaxis]
    arr_surf_constructed = dm_surface.array[:, :, idx_s['bld_surface-per-floorarea'], :, :] * \
                           dm_floor_area.array[:, :, idx_f['bld_floor-area-constructed'], :, np.newaxis]
    dm_surface.add(arr_surf_renovated, dim='Variables', col_label='bld_renovated-surface-area', unit='Mm2')
    dm_surface.add(arr_surf_constructed, dim='Variables', col_label='bld_constructed-surface-area', unit='Mm2')

    del arr_surf_constructed, arr_surf_renovated
    ### END OF MATERIALS


    DM_floor_out = {}
    DM_floor_out['wf_energy'] = dm_floor_area
    DM_floor_out['wf_costs'] = dm_renovated
    DM_floor_out['industry'] = {
        'renovated-wall': dm_surface.filter({'Variables': ['bld_renovated-surface-area'], 'Categories2': ['wall']}),
        'constructed-area': dm_constructed
    }

    return DM_floor_out


def bld_energy_workflow(DM_energy, DM_clm, dm_floor_area, cdm_const):
    # Compute renovation area by building type (e.g. office, households, ..)
    # and renovation type aka depth (e.g. dep, exi, med, shl)
    dm_mix = DM_energy['building_mix']
    idx_m = dm_mix.idx
    idx_f = dm_floor_area.idx
    arr_renovated_area_mix = dm_floor_area.array[:, :, idx_f['bld_floor-area-renovated'], :, np.newaxis] \
                             * dm_mix.array[:, :, idx_m['bld_building-renovation-mix'], :, :]
    dm_mix.add(arr_renovated_area_mix, dim='Variables', col_label='bld_floor-area-renovated', unit='Mm2')
    del arr_renovated_area_mix

    # Compute construction mix by building type and depth
    idx_m = dm_mix.idx
    arr_construction_area_mix = dm_floor_area.array[:, :, idx_f['bld_floor-area-constructed'], :, np.newaxis]\
                                * dm_mix.array[:, :, idx_m['bld_building-construction-mix'], :, :]
    dm_mix.add(arr_construction_area_mix, dim='Variables', col_label='bld_floor-area-constructed', unit='Mm2')
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
    # !FIXME: introducing the same 'error' as in KNIME
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
    dm_mix.operation('bld_building-renovation-energy-achieved', '*', 'bld_floor-area-renovated',
                     out_col='bld_energy-need_space-heating_renovated', unit='GWh')
    dm_mix.operation('bld_building-renovation-energy-achieved', '*', 'bld_floor-area-constructed',
                     out_col='bld_energy-need_space-heating_constructed', unit='GWh')

    # energy need space heating unrenovated [GWh] = energy need [kWh/m2] * floor area unrenovated (constructed) [GWh]
    idx_f = dm_floor_area.idx
    idx_m = dm_mix.idx
    arr_unren_exi = dm_floor_area.array[:, :, idx_f['bld_floor-area-unrenovated'], :] \
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
    dm_TPE_out = dm_energy_heating.copy()
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
    dm_depth = dm_mix.filter({'Variables': ['bld_floor-area-renovated', 'bld_floor-area-constructed']})
    dm_depth.group_all(dim='Categories1')

    idx = dm_floor_area.idx
    arr_unrenovated = np.nansum(dm_floor_area.array[:, :, idx['bld_floor-area-unrenovated'], :], axis=-1)
    arr_demolished = np.nansum(dm_floor_area.array[:, :, idx['bld_floor-area-demolished'], :], axis=-1)
    dm_depth.add(np.nan, dim='Variables', col_label=['bld_floor-area-unrenovated', 'bld_floor-area-demolished'],
                 unit=['Mm2', 'Mm2'], dummy=True)
    idx = dm_depth.idx
    dm_depth.array[:, :, idx['bld_floor-area-unrenovated'], idx['exi']] = arr_unrenovated
    dm_depth.array[:, :, idx['bld_floor-area-demolished'], idx['exi']] = arr_demolished
    del arr_demolished, arr_unrenovated

    # Add energy need for space heating 'constructed' 'renovated' 'unrenovated' as variables to dm_depth
    # (drop buildings type split)
    dm_space_heat = dm_energy_heating.filter({'Variables': ['bld_energy-need_space-heating']})
    # Drop building types
    dm_space_heat.group_all('Categories1')
    dm_space_heat.switch_categories_order('Categories1', 'Categories2')
    dm_space_heat = dm_space_heat.flatten().flatten()
    dm_space_heat.deepen()
    dm_space_heat.rename_col_regex('bld_energy-need_space-heating_', 'bld_energy-need_space-heating-', 'Variables')

    dm_depth.append(dm_space_heat, dim='Variables')

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
        'floor-area': dm_floor_area.filter({'Variables': ['bld_floor-area', 'bld_space-heating']}),
        'heat-emissions-by-bld': dm_floor_area.filter({'Variables': ['bld_CO2-emissions']}),
        'energy-demand-by-fuel': dm_heating,
        'renovation': dm_mix.filter({'Variables': ['bld_floor-area-renovated', 'bld_floor-area-constructed']}),
        'unrenovated': dm_floor_area.filter({'Variables': ['bld_floor-area-unrenovated']}),
        'energy-reno': dm_TPE_out
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
        'heat-emissions-by-fuel':  dm_CO2_by_fuel
    }

    DM_energy_out['wf_materials'] = {
        'area_increase_unrenovated': dm_floor_area.filter_w_regex({'Variables': '.*increase|.*unrenovated|.*demolished'}),
        'area_constructed_renovated': dm_mix.filter_w_regex({'Variables': '.*renovated|.*constructed'})
    }

    DM_energy_out['wf_costs'] = {
        'households-dh': dm_energy_heating.filter_w_regex({'Variables': 'bld_district-heating-space-heating-supply',
                                                           'Categories1': '.*households'})
    }

    dm_refinery = dm_heating.group_all(dim='Categories1', inplace=False)
    dm_refinery.filter({'Variables': ['bld_space-heating-energy-demand']}, inplace=True)
    dm_refinery.rename_col('bld_space-heating-energy-demand', 'bld_energy-demand', 'Variables')
    dm_refinery.filter({'Categories1': ['gas-ff-natural', 'liquid-ff-heatingoil', 'solid-ff-coal']}, inplace=True)
    dm_refinery.change_unit('bld_energy-demand', 1e-3, old_unit='GWh', new_unit='TWh')
    DM_energy_out['oil-refinery'] = dm_refinery

    # Prepare energy output
    # Residential heating
    dm_energy_pow_res = dm_heating.filter({'Variables': ['bld_space-heating-energy-demand'],
                                           'Categories1': ['multi-family-households', 'single-family-households'],
                                           'Categories2': ['electricity', 'electricity-heatpumps']})
    arr_res = np.nansum(dm_energy_pow_res.array, axis=-2)
    cols = {
        'Country': dm_energy_pow_res.col_labels['Country'],
        'Years': dm_energy_pow_res.col_labels['Years'],
        'Variables': ['bld_power-demand_residential'],
        'Categories1': ['space-heating', 'heatpumps']
    }
    dm_energy_pow = DataMatrix(cols, {'bld_power-demand_residential': 'GWh'})
    dm_energy_pow.array = arr_res
    # Non-residential heating
    dm_energy_pow_nonres = dm_heating.filter({'Variables': ['bld_space-heating-energy-demand'],
                                              'Categories2': ['electricity', 'electricity-heatpumps']})
    dm_energy_pow_nonres.drop(col_label=['single-family-households', 'multi-family-households'], dim='Categories1')
    arr_nonres = np.nansum(dm_energy_pow_nonres.array, axis=-2)
    dm_energy_pow.add(arr_nonres, col_label='bld_power-demand_non-residential', dim='Variables', unit='GWh')
    dm_energy_pow = dm_energy_pow.flatten()

    DM_energy_out['power'] = dm_energy_pow

    return DM_energy_out


def bld_appliances_workflow(DM_appliances):
    dm_appliance = DM_appliances['appliances']
    # Lifetime adj by people substitution rate
    dm_appliance.operation('lfs_product-substitution-rate', '*', 'bld_appliance-lifetime', out_col='bld_appliance-lifetime-adj', unit='a')
    # New appliances
    dm_appliance.operation('lfs_appliance-own', '/', 'bld_appliance-lifetime-adj', out_col='bld_appliance-new', unit='num', div0='error')
    # Energy demand
    dm_appliance.operation('lfs_total-appliance-use', '*', 'bld_appliance-efficiency', out_col='bld_energy-demand_appliances', unit='KWh')
    # Total energy demand
    dm_energy = dm_appliance.filter({'Variables': ['bld_energy-demand_appliances']})
    dm_energy.group_all(dim='Categories1')
    dm_energy.rename_col('bld_energy-demand_appliances', 'bld_power-demand_residential_appliances', dim='Variables')
    dm_energy.array = dm_energy.array/1e6
    dm_energy.units['bld_power-demand_residential_appliances'] = 'GWh'

    DM_appliance_out = {
        'wf_costs': dm_appliance.filter({'Variables': ['bld_appliance-new']}),
        'power': dm_energy,
        'industry': dm_appliance.filter({'Variables': ['bld_appliance-new']})
    }

    return DM_appliance_out


def bld_costs_workflow(DM_costs, dm_district_heat_supply, dm_new_appliance, dm_floor_renovated):
    # Compute total energy-need for district heating of households
    dm_district_heat_supply = dm_district_heat_supply['households-dh']
    dm_other = DM_costs['other']
    idx_d = dm_district_heat_supply.idx
    idx = dm_other.idx
    arr_tot_en_dh = np.nansum(dm_district_heat_supply.array[:, :, idx_d['bld_district-heating-space-heating-supply'], ...], axis=(-1, -2, -3)) \
                    + dm_other.array[:, :, idx['bld_heat-district_energy-demand_residential_hot-water']]
    dm_other.add(arr_tot_en_dh, dim='Variables', col_label='bld_energy-need_district-heating', unit='GWh')
    # Total pipe needs
    dm_other.operation('cp_district-heating_pipe-factor', '*', 'bld_energy-need_district-heating',
                       out_col='bld_district-heating_total-pipe-need', unit='km')
    # New pipe need
    dm_other.operation('bld_district-heating_total-pipe-need', '*', 'cp_district-heating_new-pipe-factor',
                       out_col='bld_district-heating_new-pipe-need', unit='km')

    # New pipes cost
    dm_other.operation('bld_district-heating_new-pipe-need', '*', 'bld_capex_new-pipes',
                       out_col='bld_district-heating_costs', unit='MEUR')

    # Appliance cost
    DM_costs['appliances-capex'].drop(col_label='ac', dim='Categories1')
    dm_new_appliance.append(DM_costs['appliances-capex'], dim='Variables')
    dm_new_appliance.operation('bld_appliance-new', '*', 'bld_capex', out_col='bld_appliances_costs', unit='MEUR')

    # Renovation cost
    dm_cost_renov = DM_costs['renovation-capex']
    idx_c = dm_cost_renov.idx
    idx_r = dm_floor_renovated.idx
    # Cost by building and renovation type based on area renovated
    arr_cost_bld_ren = dm_cost_renov.array[:, :, idx_c['bld_capex'], :, :] \
                       * dm_floor_renovated.array[:, :, idx_r['bld_floor-area-renovated'], :, np.newaxis]
    # Cost of bld renovation by bld type (sum over renovation type)
    arr_cost_bld = np.nansum(arr_cost_bld_ren, axis=-1)
    dm_floor_renovated.add(arr_cost_bld, dim='Variables', col_label='bld_capex_reno', unit='MEUR')
    # Cost of bld renovation by renovation type (sum over building type)
    arr_cost_ren = np.nansum(arr_cost_bld_ren, axis=-2)
    ref_col = dm_cost_renov.col_labels
    col_labels = {'Country': ref_col['Country'], 'Years': ref_col['Years'],
                  'Variables': ['bld_capex_reno'], 'Categories1': ref_col['Categories2']}
    dm_cost_renov_by_depth = DataMatrix(col_labels, units={'bld_capex_reno': 'MEUR'})
    dm_cost_renov_by_depth.array = arr_cost_ren

    DM_costs_out = {}
    DM_costs_out['TPE'] = {
        'cost-renovation_bld': dm_floor_renovated.filter({'Variables': ['bld_capex_reno']}),
        'cost-renovation_depth': dm_cost_renov_by_depth,
        'cost-appliances': dm_new_appliance.filter({'Variables': ['bld_appliances_costs']})
    }
    DM_costs_out['industry'] = dm_other.filter({'Variables': ['bld_district-heating_new-pipe-need']})

    return DM_costs_out


def bld_light_heat_cool_workflow(DM_light_heat, DM_lfs, DM_clm, baseyear):
    # Extract relevant lfs data
    dm_floor = DM_lfs['floor'].filter({'Variables': ['lfs_floor-space_cool']})
    dm_lfs = DM_lfs['other'].filter({'Variables': ['lfs_heatcool-behaviour_degrees']})
    dm_lfs.append(dm_floor, dim='Variables')
    del dm_floor
    dm_clm = DM_clm['climate-impact-average']
    idx_l = dm_lfs.idx
    idx_c = dm_clm.idx
    # bld_index_lfs_heatcool-behaviour_degrees\[#\]|bld_index_lfs_floor-space_cool\[#\]|bld_climate-impact_average\[%\]
    arr_tmp = dm_clm.array[:, :, idx_c['bld_climate-impact_average']] *\
              dm_lfs.array[:, :, idx_l['lfs_floor-space_cool']]/dm_lfs.array[:, np.newaxis, idx_l[baseyear], idx_l['lfs_floor-space_cool']] *\
              dm_lfs.array[:, :, idx_l['lfs_heatcool-behaviour_degrees']]/dm_lfs.array[:, np.newaxis, idx_l[baseyear], idx_l['lfs_heatcool-behaviour_degrees']]
    # !FIXME this should be the same unit as climate-impact_average
    dm_lfs.add(arr_tmp, dim='Variables', col_label='bld_lifestyles-impact-factor', unit='#')

    dm_water_light = DM_light_heat['hot-water']
    dm_ac = DM_light_heat['ac-efficiency']
    # Rescale to reference year
    idx = dm_ac.idx
    arr_tmp = dm_ac.array[:, :, idx['bld_appliance-efficiency'], :]\
              /dm_ac.array[:, idx[baseyear], np.newaxis, idx['bld_appliance-efficiency'], :]
    dm_ac.array[:, :, idx['bld_appliance-efficiency'], :] = arr_tmp
    dm_ac = dm_ac.flatten()

    # lighting demand * rescaled efficiency
    dm_water_light.append(dm_ac, dim='Variables')
    del dm_ac
    dm_water_light.operation('bld_lighting-demand_non-residential_electricity', '/', 'bld_appliance-efficiency_ac',
                             out_col='bld_lighting-energy-demand_non-residential_electricity', unit='GWh', div0='interpolate')
    dm_water_light.operation('bld_lighting-demand_residential_electricity', '/', 'bld_appliance-efficiency_ac',
                             out_col='bld_lighting-energy-demand_residential_electricity', unit='GWh', div0='interpolate')
    # Remove raw lighting demand
    #dm_water_light.drop(col_label='bld_lighting-demand.*', dim='Variables')

    # Extract cooling and hot water
    # !FIXME this rename should happen in the csv directly
    dm_cooling = DM_light_heat['energy'].filter({'Variables': ['bld_space-cooling-energy-demand_non-residential',
                                                               'bld_space-cooling-energy-demand_residential'],
                                                               'Categories1': ['electricity', 'gas-bio', 'gas-ff-natural']})
    dm_cooling.deepen(based_on='Variables')

    # Correct space cooling by climate and lifestyle factor
    idx = dm_cooling.idx
    idx_l = dm_lfs.idx
    idx_w = dm_water_light.idx
    arr_tmp = dm_cooling.array[:, :, idx['bld_space-cooling-energy-demand'], :, :] \
              * dm_lfs.array[:, :, idx_l['bld_lifestyles-impact-factor'], np.newaxis, np.newaxis] \
              * dm_water_light.array[:, :, idx_w['bld_appliance-efficiency_ac'], np.newaxis, np.newaxis]
    dm_cooling.array[:, :, idx['bld_space-cooling-energy-demand'], :, :] = arr_tmp

    # Adjust heatcool-efficiency to reference year
    dm_other = DM_light_heat['energy'].filter({'Variables': ['bld_heatcool-efficiency', 'bld_residential-cooking-energy-demand']})
    idx = dm_other.idx
    dm_other.array[:, :, idx['bld_heatcool-efficiency'], :] = dm_other.array[:, :, idx['bld_heatcool-efficiency'], :] \
                                                             /dm_other.array[:, idx[baseyear], np.newaxis, idx['bld_heatcool-efficiency'], :]

    # Adj hot water demand by heat-cool efficiency factor
    dm_water = DM_light_heat['energy'].filter({'Variables': ['bld_hot-water-demand-non-residential',
                                                             'bld_hot-water-demand-residential']})
    dm_water.rename_col_regex('demand-non-residential', 'demand_non-residential', dim='Variables')
    dm_water.rename_col_regex('demand-residential', 'demand_residential', dim='Variables')
    dm_water.deepen(based_on='Variables')
    idx_c = dm_water.idx
    dm_water.array[:, :, idx_c['bld_hot-water-demand'], :, :] = dm_water.array[:, :, idx_c['bld_hot-water-demand'], :, :] \
                                                                * dm_other.array[:, :, idx['bld_heatcool-efficiency'], :, np.newaxis]

    ### Prepare wf_emissions output
    dm_cooking = dm_other.filter({'Variables': ['bld_residential-cooking-energy-demand'],
                                  'Categories1': ['gas-bio', 'gas-ff-natural', 'solid-bio', 'solid-ff-coal']})
    dm_cool = dm_cooling.filter({'Variables': ['bld_space-cooling-energy-demand'],
                                 'Categories1': ['gas-bio', 'gas-ff-natural']})

    # Prepare energy output
    # cooking electricity
    dm_energy = dm_other.filter({'Variables': ['bld_residential-cooking-energy-demand'], 'Categories1': ['electricity']})
    dm_energy = dm_energy.flatten()
    dm_energy.rename_col('bld_residential-cooking-energy-demand_electricity', 'bld_power-demand_residential_cooking', dim='Variables')
    # lighting electricity
    dm_lighting = dm_water_light.filter({'Variables': ['bld_lighting-energy-demand_non-residential_electricity',
                                           'bld_lighting-energy-demand_residential_electricity']})
    dm_lighting.rename_col('bld_lighting-energy-demand_non-residential_electricity', 'bld_power-demand_non-residential_lighting', dim='Variables')
    dm_lighting.rename_col('bld_lighting-energy-demand_residential_electricity', 'bld_power-demand_residential_lighting', dim='Variables')
    dm_energy.append(dm_lighting, dim='Variables')
    # cooling electricity
    dm_pow_cooling = dm_cooling.filter({'Categories1': ['electricity']})
    dm_pow_cooling.switch_categories_order()
    dm_pow_cooling.rename_col('bld_space-cooling-energy-demand', 'bld_power-demand', dim='Variables')
    dm_pow_cooling.rename_col('electricity', 'space-cooling', dim='Categories2')
    dm_pow_cooling = dm_pow_cooling.flatten()
    dm_pow_cooling = dm_pow_cooling.flatten()
    dm_energy.append(dm_pow_cooling, dim='Variables')
    del dm_lighting, dm_pow_cooling

    # (cooking), (space-heating), appliances, hot-water, (lighting), (space-cooling),
    DM_light_heat_out = {
        'wf_fuel_switch': dm_water,
        # 'district-heating': dm_district_heating,
        'wf_emissions_appliances': {'cooking': dm_cooking, 'cooling': dm_cool},
        'power': dm_energy
    }
    return DM_light_heat_out


def bld_fuel_switch_workflow(DM_fuel_switch, dm_fuel_switch, baseyear):
    lastyear = dm_fuel_switch.col_labels['Years'][-1]
    dm_renewable = DM_fuel_switch['heatcool-shares-renew'].copy()
    # Compute percentage change
    dm_renewable.operation('bld_heatcool-technology-fuel_residential_current', '-',
                           'bld_heatcool-technology-fuel_residential_reference-year',
                           out_col='bld_percentage-change', unit='%')
    # % increase-normalised = % increase / sum( % increase)
    idx = dm_renewable.idx
    arr_sum_increase = np.nansum(dm_renewable.array[:, :, idx['bld_percentage-change'], :], axis=-1, keepdims=True)
    arr_norm = dm_renewable.array[:, :, idx['bld_percentage-change'], :]/arr_sum_increase
    dm_renewable.add(arr_norm, col_label='bld_substitution-per-renewable_residential', dim='Variables', unit='%')
    # Drop unnecessary columns
    dm_renewable = dm_renewable.filter({'Variables': ['bld_substitution-per-renewable_residential']})
    # !FIXME the fact that we are using the ratio for fossil fuel and the difference for renewable doesn't make sense
    dm_fossil = DM_fuel_switch['heatcool-shares-fossil'].copy()
    dm_fossil.operation('bld_heatcool-technology-fuel_residential_current', '/',
                        'bld_heatcool-technology-fuel_residential_reference-year',
                           out_col='bld_percentage-change_residential', unit='%')
    dm_fossil.operation('bld_heatcool-technology-fuel_nonresidential_current', '/',
                        'bld_heatcool-technology-fuel_nonresidential_reference-year',
                        out_col='bld_percentage-change_nonresidential', unit='%')
    idx = dm_fossil.idx
    arr_max_res_nonres = np.maximum(dm_fossil.array[:, :, idx['bld_percentage-change_residential'], :],
                                    dm_fossil.array[:, :, idx['bld_percentage-change_nonresidential'], :])
    # !FIXME I'm also adding the normalisation here because it makes sense, similarly to what done for renewables
    dm_fossil.add(arr_max_res_nonres, col_label='bld_space-heating-fuel-mix', dim='Variables', unit='%')
    # Drop unnecessary columns
    dm_fossil = dm_fossil.filter({'Variables': ['bld_space-heating-fuel-mix']})

    # Sum residential and non-residential hot water and compute share by fuel
    arr_hot_water = np.nansum(dm_fuel_switch.array, axis=-1)
    tot_hot_water = np.nansum(arr_hot_water, axis=-1)
    shares_hot_water = arr_hot_water/tot_hot_water[:, :, :, np.newaxis]
    new_col = dm_fuel_switch.col_labels.copy()
    new_col.pop('Categories2')
    new_col['Variables'] = ['bld_hot-water-energy-demand']
    dm_hot_water = DataMatrix(new_col, units={'bld_hot-water-energy-demand': '%'})
    dm_hot_water.array = shares_hot_water

    # !FIXME I don't think this makes sense, it is using baseyear data for 2050
    #  (also somehow this should not apply to electricity)
    # Multiplies hot water energy fossil share by the space heating fuel mix for the baseyear
    # Also here electricity is not included, but probably then it should be excluded also
    # when doing the assessment above for fossil fuel
    dm_space_heating = dm_fossil.copy()
    dm_space_heating.drop(col_label=['electricity'], dim='Categories1')
    dm_hot_water_fossil = dm_hot_water.filter({'Categories1': dm_space_heating.col_labels['Categories1']})
    idx = dm_hot_water_fossil.idx
    idx_f = dm_fossil.idx
    # sum.fuel-type ( hot-water-demand-fossil (t=2050) [%]
    #               - hot-water-demand-fossil (t=2015) [%] * heating-fuel-mix (t=2015) [%])
    # --> bld_hot-water_total-substitution
    arr_tmp = dm_hot_water_fossil.array[:, idx[baseyear], idx['bld_hot-water-energy-demand'], :] \
             * dm_space_heating.array[:, idx_f[baseyear], idx_f['bld_space-heating-fuel-mix'], :]
    dm_hot_water_fossil_2050 = dm_hot_water_fossil.filter({'Years': [lastyear]})
    dm_hot_water_fossil_2050.array = arr_tmp[:, np.newaxis, np.newaxis, :]
    arr_tmp = np.nansum(dm_hot_water_fossil.array[:, idx[lastyear], idx['bld_hot-water-energy-demand'], :] - \
                        arr_tmp, axis=-1)
    # bld_substitution-per-renewable_residential.by_RES (t=2050) =
    # bld_hot-water_total-substitution (t=2050) * bld_substitution-per-renewable_residential.by_RES (t=2050)
    idx = dm_renewable.idx
    arr_renew = dm_renewable.array[:, idx[lastyear], idx['bld_substitution-per-renewable_residential'], :] \
                * arr_tmp[:, np.newaxis]
    dm_hot_water_renew = dm_hot_water.filter({'Categories1': dm_renewable.col_labels['Categories1']})
    # bld_hot-water-fuel-mix-2050 = bld_hot-water-energy-demand +
    #                               bld_substitution-per-renewable_residential * bld_hot-water_total-substitution
    idx = dm_hot_water_renew.idx
    arr_hot_water_renew = dm_hot_water_renew.array[:, idx[lastyear], idx['bld_hot-water-energy-demand'], :] + arr_renew[:, :]
    dm_hot_water_renew_2050 = dm_hot_water_renew.filter({'Years': [lastyear]})
    dm_hot_water_renew_2050.array = arr_hot_water_renew[:, np.newaxis, np.newaxis, :]
    del arr_hot_water_renew, arr_hot_water, arr_norm, arr_max_res_nonres, arr_renew, arr_sum_increase, arr_tmp, new_col

    dm_hot_water_2050 = dm_hot_water_renew_2050
    dm_hot_water_2050.append(dm_hot_water_fossil_2050, dim='Categories1')
    # Extract electricity
    dm_hot_water_elect_2050 = dm_hot_water.filter({'Categories1': ['electricity'], 'Years': [lastyear]})
    dm_hot_water_2050.append(dm_hot_water_elect_2050, dim='Categories1')
    dm_hot_water_2050.sort(dim='Categories1')
    # Put 2050 data into hot_water datamatrix
    idx = dm_hot_water.idx
    dm_hot_water.array[:, idx[lastyear], :, :] = dm_hot_water_renew_2050.array[:, 0, :, :]
    # Perform linear interpolation between 2015 - 2050
    dm_hot_water.array[:, idx[baseyear]+1:idx[lastyear], :, :] = np.nan
    dm_hot_water.fill_nans(dim_to_interp='Years')

    # Use these newly computed shares to project the demand_hot_water in GWh for both residential and non-residential
    idx = dm_fuel_switch.idx
    # sum over fuel type, mantain residential & non-residential split
    arr = np.nansum(dm_fuel_switch.array[:, :, idx['bld_hot-water-demand'], :, :], axis=-2)
    idx_h = dm_hot_water.idx
    # for FTS : hot-water-demand.by_fuel_res_type = hot-water-demand.by_fuel_type[%] * hot-water-demand.by_res_non-res[GWh]
    arr_tmp = dm_hot_water.array[:, :, idx_h['bld_hot-water-energy-demand'], np.newaxis, :] * arr[:, :, :, np.newaxis]
    dm_fuel_switch.switch_categories_order()
    idx = dm_fuel_switch.idx
    dm_fuel_switch.array[:, idx[baseyear]:, idx['bld_hot-water-demand'], :, :] = arr_tmp[:, idx[baseyear]:, :, :]

    # Prepare power module output
    dm_water_pow = dm_fuel_switch.filter({'Categories2': ['electricity']})
    dm_water_pow.rename_col('bld_hot-water-demand', 'bld_power-demand', dim='Variables')
    dm_water_pow.rename_col('electricity', 'hot-water', dim='Categories2')
    dm_water_pow = dm_water_pow.flatten()
    dm_water_pow = dm_water_pow.flatten()

    dm_energy = dm_fuel_switch.group_all('Categories1', inplace=False)

    DM_fuel_switch_out = {
        'wf_emissions_appliances': dm_fuel_switch,
        'power': dm_water_pow,
        'TPE': dm_energy
    }

    return DM_fuel_switch_out


def bld_emissions_appliances_workflow(DM_cooking_cooling, dm_hot_water, cdm_const):
    # In order to have split by fuel in categories1
    dm_cooking = DM_cooking_cooling['cooking']
    dm_cooking.rename_col('bld_residential-cooking-energy-demand', 'bld_cooking-energy-demand_residential', dim='Variables')
    dm_cooking.deepen(based_on='Variables')

    dm_hot_water.switch_categories_order()
    DM_emissions = {
        'cooking': dm_cooking,
        'cooling': DM_cooking_cooling['cooling'],
        'hot_water': dm_hot_water
    }
    # Initialize numpy array to gather residential and non-residential CO2 emissions
    arr_CO2_res = np.zeros((len(dm_hot_water.col_labels['Country']), len(dm_hot_water.col_labels['Years'])))
    arr_CO2_nonres = np.zeros((len(dm_hot_water.col_labels['Country']), len(dm_hot_water.col_labels['Years'])))
    for key in DM_emissions.keys():
        dm_tmp = DM_emissions[key]
        # From GWh to TWh
        for var in dm_tmp.col_labels['Variables']:
            dm_tmp.change_unit(var, factor=1e-3, old_unit='GWh', new_unit='TWh')
        cdm_const_tmp = cdm_const.filter({'Categories1': dm_tmp.col_labels['Categories1']})
        assert cdm_const_tmp.col_labels['Categories1'] == dm_tmp.col_labels['Categories1'], f"Fuels categories do not match"
        # Multiply energy * emissions-factors
        arr_emission = dm_tmp.array[:, :, 0, ...] * cdm_const_tmp.array[np.newaxis, np.newaxis, 0, :, np.newaxis]
        new_var = var + '_CO2-emissions'
        dm_tmp.add(arr_emission, col_label=new_var, dim='Variables', unit='Mt')
        DM_emissions[key] = dm_tmp
        # Sum emissions for all fuel types by residential and non-residential
        idx = dm_tmp.idx
        arr_CO2_res = arr_CO2_res + np.nansum(DM_emissions[key].array[:, :, idx[new_var], :, idx['residential']], axis=-1)
        if 'non-residential' in idx.keys():
            arr_CO2_nonres = arr_CO2_nonres + np.nansum(DM_emissions[key].array[:, :, idx[new_var], :, idx['non-residential']], axis=-1)

    # Gather tot 'appliances' (incl. hot water) emissions by residential and not residential in new datamatrix
    ay_em_appliances = np.concatenate((arr_CO2_nonres[..., np.newaxis, np.newaxis],
                                       arr_CO2_res[..., np.newaxis, np.newaxis]), axis=-1)
    dm_format = dm_cooking.group_all(dim='Categories2', inplace=False)
    dm_em_appliances = DataMatrix.based_on(ay_em_appliances, format=dm_format,
                                           change={'Variables': ['bld_CO2-emissions_appliances'],
                                                   'Categories1': ['non-residential', 'residential']},
                                           units={'bld_CO2-emissions_appliances': 'Mt'})

    DM_emissions_appliances_out = {'emissions': dm_em_appliances}

    return DM_emissions_appliances_out


def bld_district_heating_interface(DM_heat, dm_pipe, write_xls=False):

    dm_heat_supply = DM_heat['heat-supply']
    # Split heat supply between residential and non-residential
    cols_non_residential = [col for col in dm_heat_supply.col_labels['Categories1'] if 'households' not in col]
    dm_heat_supply.groupby({'residential': ['multi-family-households', 'single-family-households'],
                            'non-residential': cols_non_residential}, dim='Categories1', inplace=True)
    # Sum over all renovations types 'dep', 'exi', 'shl', 'med'
    dm_heat_supply.group_all(dim='Categories2', inplace=True)
    # Sum 'constructed', 'renovated', 'unrenovated'
    dm_heat_supply.group_all(dim='Categories2', inplace=True)

    # This section on electricity is not needed because district-heating does not use it
    # Extract heat demand in the form of electricity
    # dm_heat_demand_elec = DM_heat['heat-electricity']
    # Group households into residential and others into non-residential
    # dm_heat_demand_elec.groupby({'residential': ['multi-family-households', 'single-family-households'],
    #                              'non-residential': cols_non_residential}, dim='Categories1', inplace=True)
    # Drop 'electricity' category
    # dm_heat_demand_elec.group_all(dim='Categories2', inplace=True)
    # Rename variable to contain 'electricity' in it
    # dm_heat_demand_elec.rename_col('bld_space-heating-energy-demand', 'bld_electricity-demand_space-heating', dim='Variables')

    # rename electricity demand to have the structure bld_electricity-demand_use_residential or non-residential
    # dm_elec.rename_col_regex('_energy-demand', '', dim='Variables')
    # dm_elec.rename_col_regex('-energy-demand', '', dim='Variables')
    # dm_elec.rename_col_regex('-demand', '', dim='Variables')
    # dm_elec.rename_col_regex('bld_', 'bld_electricity-demand_', dim='Variables')
    # dm_elec.rename_col_regex('residential-cooking', 'cooking_residential', dim='Variables')
    # dm_elec.group_all(dim='Categories1', inplace=True)
    # dm_elec.deepen_twice()

    # dm_heat_demand_elec.deepen(based_on='Variables')
    # dm_heat_demand_elec.switch_categories_order('Categories1', 'Categories2')

    # dm_elec.append(dm_heat_demand_elec, dim='Categories1')

    dm_dhg = dm_heat_supply
    # Pipe
    dm_pipe.rename_col('bld_district-heating_new-pipe-need', 'bld_new_dh_pipes', dim='Variables')
    dm_pipe.deepen()

    DM_dhg = {
        'heat': dm_dhg,
        'pipe': dm_pipe
    }

    if write_xls:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        xls_file = 'All-Countries-interface_from-buildings-to-district-heating.xlsx'
        file_path = os.path.join(current_file_directory, '../_database/data/xls/', xls_file)
        df = dm_dhg.write_df()
        df_pipe = dm_pipe.write_df()
        df = pd.concat([df, df_pipe.drop(columns=['Country', 'Years'])], axis=1)
        df.to_excel(file_path, index=False)

    return DM_dhg

def bld_power_interface(dm_appliances, dm_energy, dm_fuel, dm_light_heat):

    dm_light_heat.append(dm_appliances, dim='Variables')  # append appliances
    dm_light_heat.append(dm_fuel, dim='Variables')  # append hot-water
    dm_light_heat.deepen_twice()

    # space-cooling to separate dm
    dm_cooling = dm_light_heat.filter({'Categories2': ['space-cooling']})
    dm_light_heat.drop(col_label='space-cooling', dim='Categories2')

    # split space-heating and heatpumps
    dm_energy.deepen_twice()
    dm_heating = dm_energy.filter({'Categories2': ['space-heating']})
    dm_heatpumps = dm_energy.filter({'Categories2': ['heatpumps']})

    DM_pow = {
        'appliance': dm_light_heat,
        'space-heating': dm_heating,
        'heatpump': dm_heatpumps,
        'cooling': dm_cooling
    }
    return DM_pow

def bld_emissions_interface(dm_appliances, DM_energy):

    dm_emissions_fuel = DM_energy['heat-emissions-by-fuel'].filter({"Categories1" : ["gas-ff-natural", "heat-ambient", 
                                   "heat-geothermal", "heat-solar", 
                                   "liquid-ff-heatingoil", "solid-bio", 
                                   "solid-ff-coal"]})
    dm_emissions_fuel.rename_col('bld_CO2-emissions', 'bld_emissions-CO2', dim='Variables')

    dm_appliances = dm_appliances.filter({"Categories1" : ["non-residential"]})
    dm_appliances.rename_col('bld_CO2-emissions_appliances', 'bld_emissions-CO2_appliances', dim='Variables')
    # dm_appliances.rename_col('bld_CO2-emissions_appliances', 'bld_residential-emissions-CO2', dim='Variables')
    # dm_appliances.rename_col('non-residential', 'non_appliances', dim='Categories1')
    # dm_appliances.rename_col('residential', 'appliances', dim='Categories1')

    dm_emissions_fuel = dm_emissions_fuel.flatten()
    dm_appliances = dm_appliances.flatten()

    dm_emissions_fuel.append(dm_appliances, dim='Variables')

    return dm_emissions_fuel


def bld_industry_interface(DM_floor, dm_appliances, dm_pipes):
    # Renovated wall + new floor area constructed
    groupby_dict = {'floor-area-reno-residential': ['single-family-households', 'multi-family-households'],
                    'floor-area-reno-non-residential': ['education', 'health', 'hotels', 'offices', 'other', 'trade']}
    dm_reno = DM_floor['renovated-wall'].group_all(dim='Categories2', inplace=False)
    dm_reno.groupby(groupby_dict, dim='Categories1', inplace=True, regex=False)
    dm_reno.rename_col('bld_renovated-surface-area', 'bld_product-demand', dim='Variables')

    groupby_dict = {'floor-area-new-residential': ['single-family-households', 'multi-family-households'],
                    'floor-area-new-non-residential': ['education', 'health', 'hotels', 'offices', 'other', 'trade']}
    dm_constructed = DM_floor['constructed-area']
    dm_constructed.groupby(groupby_dict, dim='Categories1', inplace=True, regex=False)
    dm_constructed.rename_col('bld_floor-area-constructed', 'bld_product-demand', dim='Variables')

    dm_constructed.append(dm_reno, dim='Categories1')

    # Pipes
    dm_pipes.rename_col('bld_district-heating_new-pipe-need', 'bld_product-demand_new-dhg-pipe', dim='Variables')
    dm_pipes.deepen()

    # Appliances
    dm_appliances.rename_col('bld_appliance-new', 'bld_product-demand', dim='Variables')
    dm_appliances.rename_col('comp', 'computer', dim='Categories1')

    DM_industry = {
        'bld-pipe': dm_pipes,
        'bld-floor': dm_constructed,
        'bld-domapp': dm_appliances
    }

    return DM_industry


def bld_minerals_interface(DM_industry, write_xls):
    # Pipe
    dm_pipe = DM_industry['bld-pipe'].copy()
    dm_pipe.rename_col('bld_product-demand', 'product-demand', dim='Variables')
    dm_pipe.rename_col('new-dhg-pipe', 'infra-pipe', dim='Categories1')

    # Appliances
    dm_appliances = DM_industry['bld-domapp'].copy()
    dm_appliances.rename_col('bld_product-demand', 'product-demand', dim='Variables')
    cols_in = ['dishwasher', 'dryer', 'freezer', 'fridge', 'wmachine', 'computer', 'phone', 'tv']
    cols_out = ['dom-appliance-dishwasher', 'dom-appliance-dryer', 'dom-appliance-freezer', 'dom-appliance-fridge',
                'dom-appliance-wmachine', 'electronics-computer', 'electronics-phone', 'electronics-tv']
    dm_appliances.rename_col(cols_in, cols_out, dim='Categories1')
    dm_electronics = dm_appliances.filter_w_regex({'Categories1': 'electronics.*'}, inplace=False)
    dm_appliances.filter_w_regex({'Categories1': 'dom-appliance.*'}, inplace=True)

    # Floor
    dm_floor = DM_industry['bld-floor'].copy()
    dm_floor.rename_col('bld_product-demand', 'product-demand', dim='Variables')

    DM_minerals = {
        'bld-pipe': dm_pipe,
        'bld-floor': dm_floor,
        'bld-appliance': dm_appliances,
        'bld-electr': dm_electronics
    }

    return DM_minerals


def bld_agriculture_interface(dm_agriculture):

    dm_agriculture.filter({'Categories2': ['gas-bio', 'solid-bio']}, inplace=True)
    dm_agriculture.group_all('Categories1')
    dm_agriculture.rename_col('bld_space-heating-energy-demand', 'bld_bioenergy', 'Variables')
    dm_agriculture.change_unit('bld_bioenergy', factor=1e-3, old_unit='GWh', new_unit='TWh')

    return dm_agriculture


def bld_TPE_interface(DM_energy, dm_appliances, dm_hot_water, dm_elec_other):

    dm_floor_energy = DM_energy['floor-area_energy-demand'].copy()
    dm_floor = DM_energy['floor-area'].copy()
    dm_emissions = DM_energy['heat-emissions-by-bld'].copy()

    dm_emissions.rename_col('bld_CO2-emissions', 'bld_emissions-CO2e_by-bld-type', 'Variables')

    # Heat energy demand by fuel type
    dm_energy_heat = DM_energy['energy-demand-by-fuel'].filter({'Variables': ['bld_space-heating-energy-demand']})

    # Sum heat and hot water
    dm_energy_tot = dm_energy_heat.group_all('Categories1', inplace=False)
    dm_energy_tot.append(dm_hot_water, dim='Variables')
    dm_energy_tot.groupby({'bld_energy-demand_tot': ['bld_hot-water-demand', 'bld_space-heating-energy-demand']}, dim='Variables', inplace=True)

    # Group electricity demand from appliances, cooking, space-cooling, lighting
    dm_electricity = dm_elec_other.copy()
    dm_electricity.append(dm_appliances, dim='Variables')
    dm_electricity.groupby({'bld_energy-demand_electricity': '.*'}, dim='Variables', inplace=True, regex=True)

    # Add electricity demand to total bld energy demand
    idx = dm_energy_tot.idx
    idx_el = dm_electricity.idx
    dm_energy_tot.array[:, :, idx['bld_energy-demand_tot'], idx['electricity']] += \
        dm_electricity.array[:, :, idx_el['bld_energy-demand_electricity']]

    # From GWh to TWh
    dm_energy_tot.change_unit('bld_energy-demand_tot', factor=1e-3, old_unit='GWh', new_unit='TWh')

    # Renovation
    dm_reno = DM_energy['renovation']
    dm_reno.group_all('Categories1', inplace=True)
    dm_unreno = DM_energy['unrenovated']
    dm_unreno.group_all('Categories1', inplace=True)
    dm_unreno.rename_col('bld_floor-area-unrenovated', 'bld_floor-area-unrenovated_exi', 'Variables')
    dm_energy_reno = DM_energy['energy-reno']
    dm_energy_reno.group_all('Categories1', inplace=True)
    dm_energy_reno.rename_col_regex('bld_energy-need_space-heating_', 'bld_energy-demand-space-heating-', 'Variables')

    df = dm_floor_energy.write_df()
    df2 = dm_floor.write_df()
    df3 = dm_emissions.write_df()
    df4 = dm_energy_tot.write_df()
    df5 = dm_reno.write_df()
    df6 = dm_unreno.write_df()
    df7 = dm_energy_reno.write_df()

    df = pd.concat([df, df2.drop(columns=['Country', 'Years'])], axis=1)
    df = pd.concat([df, df3.drop(columns=['Country', 'Years'])], axis=1)
    df = pd.concat([df, df4.drop(columns=['Country', 'Years'])], axis=1)
    df = pd.concat([df, df5.drop(columns=['Country', 'Years'])], axis=1)
    df = pd.concat([df, df6.drop(columns=['Country', 'Years'])], axis=1)
    df = pd.concat([df, df7.drop(columns=['Country', 'Years'])], axis=1)

    return df

def buildings(lever_setting, years_setting, interface=Interface()):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    buildings_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/buildings.pickle')
    # Read data into workflow datamatrix dictionaries
    DM_floor_area, DM_energy, DM_appliances, DM_costs, DM_light_heat, DM_fuel_switch, cdm_const = read_data(buildings_data_file, lever_setting)

    # Simulate lifestyle input
    if interface.has_link(from_sector='lifestyles', to_sector='buildings'):
        DM_lfs = interface.get_link(from_sector='lifestyles', to_sector='buildings')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing lifestyles to buildings interface')
        DM_lfs = simulate_lifestyles_to_buildings_input()
        cntr_list = DM_floor_area['floor_area'].col_labels['Country']
        for key in DM_lfs.keys():
            DM_lfs[key] = DM_lfs[key].filter({'Country': cntr_list})

    if interface.has_link(from_sector='climate', to_sector='buildings'):
        DM_clm = interface.get_link(from_sector='climate', to_sector='buildings')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing climate to buildings interface')
        DM_clm = simulate_climate_to_buildings_input()
        cntr_list = DM_floor_area['floor_area'].col_labels['Country']
        for key in DM_clm.keys():
            DM_clm[key] = DM_clm[key].filter({'Country': cntr_list})

    # Floor area workflow
    baseyear = years_setting[1]
    # Floor Area, Comulated floor area, Construction material
    DM_floor_out = bld_floor_area_workflow(DM_floor_area, DM_lfs['floor'], baseyear)

    del DM_floor_area
    # Total Energy demand, Renovation and Construction per depth, GHG emissions (for Space Heating)
    DM_energy_out = bld_energy_workflow(DM_energy, DM_clm, DM_floor_out['wf_energy'], cdm_const)
    del DM_energy
    # Appliances
    # join appliance data from lfs with lever & fxa data
    DM_appliances['appliances'].append(DM_lfs['appliance'], dim='Variables')
    DM_appliances_out = bld_appliances_workflow(DM_appliances)
    del DM_appliances
    # Costs
    DM_costs_out = bld_costs_workflow(DM_costs, DM_energy_out['wf_costs'], DM_appliances_out['wf_costs'],  DM_floor_out['wf_costs'])
    del DM_costs
    # Light-heat-cool
    DM_light_heat_out = bld_light_heat_cool_workflow(DM_light_heat, DM_lfs, DM_clm, baseyear)
    del DM_light_heat
    # Fuel switch
    DM_fuel_switch_out = bld_fuel_switch_workflow(DM_fuel_switch, DM_light_heat_out['wf_fuel_switch'], baseyear)
    del DM_fuel_switch
    # Emissions appliances
    DM_emissions_appliances_out = bld_emissions_appliances_workflow(DM_light_heat_out['wf_emissions_appliances'],
                                                                    DM_fuel_switch_out['wf_emissions_appliances'],
                                                                    cdm_const)

    # TPE
    results_run = bld_TPE_interface(DM_energy_out['TPE'], DM_appliances_out['power'],
                                    DM_fuel_switch_out['TPE'], DM_light_heat_out['power'])

    # 'District-heating' module interface
    DM_dhg = bld_district_heating_interface(DM_energy_out['district-heating'], DM_costs_out['industry'].copy(), write_xls=False)
    interface.add_link(from_sector='buildings', to_sector='district-heating', dm=DM_dhg)

    DM_pow = bld_power_interface(DM_appliances_out['power'], DM_energy_out['power'], DM_fuel_switch_out['power'], DM_light_heat_out['power'])
    interface.add_link(from_sector='buildings', to_sector='power', dm=DM_pow)

    dm_emissions = bld_emissions_interface(DM_emissions_appliances_out['emissions'], DM_energy_out['emissions'])
    interface.add_link(from_sector='buildings', to_sector='emissions', dm=dm_emissions)

    DM_industry = bld_industry_interface(DM_floor_out['industry'], DM_appliances_out['industry'], DM_costs_out['industry'])
    interface.add_link(from_sector='buildings', to_sector='industry', dm=DM_industry)

    DM_minerals = bld_minerals_interface(DM_industry, write_xls=False)
    interface.add_link(from_sector='buildings', to_sector='minerals', dm=DM_minerals)

    dm_agriculture = bld_agriculture_interface(DM_energy_out['agriculture']['energy-demand'])
    interface.add_link(from_sector='buildings', to_sector='agriculture', dm=dm_agriculture)

    interface.add_link(from_sector='buildings', to_sector='oil-refinery', dm=DM_energy_out['oil-refinery'])

    return results_run


def buildings_local_run():
    # Function to run module as stand alone without other modules/converter or TPE
    years_setting, lever_setting = init_years_lever()
    # Function to run only transport module without converter and tpe

    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    buildings(lever_setting, years_setting)
    return


# database_from_csv_to_datamatrix()
# buildings_local_run()



