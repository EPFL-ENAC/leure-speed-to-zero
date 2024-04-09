import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database, read_database_w_filter
from model.common.auxiliary_functions import compute_stock, constant_filter
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups
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
    file = 'buildings_climate'
    lever = 'climate'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

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

    file = 'buildings_residential-appeff'
    lever = 'residential-appeff'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

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


