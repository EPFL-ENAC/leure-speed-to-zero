import pandas as pd

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data
import pickle
import json
import os
import numpy as np
import time

#__file__ = "/Users/crosnier/Documents/PathwayCalc/training/transport_module_notebook.py"


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


#######################################################################################################
######################################### LOAD AGRICULTURE DATA #########################################
#######################################################################################################
def database_from_csv_to_datamatrix():
    #############################################
    ##### database_from_csv_to_datamatrix() #####
    #############################################

    years_setting, lever_setting = init_years_lever()

    # Set years range
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) # make list with years from 1990 to 2015
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int)) # make list with years from 2020 to 2050 (steps of 5 years)
    years_all = years_ots + years_fts

    #####################
    # FIXED ASSUMPTIONS #
    #####################

    # Read database
    file = 'agriculture_fixed-assumptions'
    lever = 'fixed-assumption'
    # edit_database(file, lever, column='eucalc-name', mode='rename',pattern={'meat_': 'meat-', 'abp_': 'abp-'})

    # Create dm for relevant fxa categories
    # Read fixed assumptions & create dict_fxa
    dict_fxa = {}
    # this is just a dataframe of zeros
    # df = read_database_fxa(file, filter_dict={'eucalc-name': 'bld_CO2-factors-GHG'})

    # Food demand to domestic production

    df = read_database_fxa(file, filter_dict={'eucalc-name': 'agr_food-net-import_pro'})
    # dm_food_net_import = DataMatrix.create_from_df(df, num_cat=1)
    # dict_fxa['food_net_import_pro'] = dm_food_net_import

    #####################
    ###### LEVERS #######
    #####################

    dict_ots = {}
    dict_fts = {}

    # Read self-sufficiency
    file = 'agriculture_self-sufficiency_pathwaycalc'
    lever = 'food-net-import'
    # Rename to correct format
    edit_database(file,lever,column='eucalc-name',pattern={'processeced':'processed'},mode='rename')
    edit_database(file,lever,column='eucalc-name',pattern={'meat_':'meat-', 'abp_':'abp-', 'processed_':'processed-', 'pro_':'pro-','liv_':'liv-','crop_':'crop-','bev_':'bev-'},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                           dict_ots=dict_ots, dict_fts=dict_fts)

    # Group all datamatrix in a single structure
    DM_agriculture = {
        #'fxa': dict_fxa,
        #'constant': cdm_const,
        'fts': dict_fts,
        'ots': dict_ots
    }

    # write datamatrix to pickle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/agriculture.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_agriculture, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return


def read_data(data_file, lever_setting):

    with open(data_file, 'rb') as handle:
        DM_agriculture = pickle.load(handle)

    # Read fts based on lever_setting
    DM_ots_fts = read_level_data(DM_agriculture, lever_setting)

    return DM_ots_fts


def simulate_lifestyles_to_agriculture_input():
    # Read input from lifestyle : food waste & diet
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-agriculture.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_lfs = DataMatrix.create_from_df(df, num_cat=1)

    # other way to do the step before but does not add it to the dm
    #idx = dm_lfs.idx
    #overall_food_demand = dm_lfs.array[:,:,idx['lfs_diet'],:] + dm_lfs.array[:,:,idx['lfs_food-wastes'],:]

    # Renaming to correct format to match iterators (simultaneously changes in lfs_diet, lfs_fwaste and agr_demand)
    # Adding meat prefix
    pro_liv_meat = ['bov', 'sheep', 'pigs', 'poultry', 'oth-animals']
    for cat in pro_liv_meat:
        new_cat = 'pro-liv-meat-'+cat
        # Dropping the -s at the end of pigs (for name matching reasons)
        if new_cat.endswith('pigs'):
            new_cat = new_cat[:-1]
        # Replacing bov by bovine (for name matching reasons)
        if new_cat == 'pro-liv-meat-bov':
            new_cat = 'pro-liv-meat-bovine'
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding bev prefix
    pro_bev = ['beer', 'bev-fer', 'bev-alc', 'wine']
    for cat in pro_bev:
        new_cat = 'pro-bev-' + cat
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding milk prefix
    pro_milk = ['milk']
    for cat in pro_milk:
        new_cat = 'pro-liv-abp-dairy-' + cat
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding egg prefix
    pro_egg = ['egg']
    for cat in pro_egg:
        new_cat = 'pro-liv-abp-hens-' + cat
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding crop prefix
    crop = ['cereals', 'oilcrops', 'pulses', 'starch', 'fruits', 'veg']
    for cat in crop:
        new_cat = 'crop-' + cat
        # Dropping the -s at the end of cereals, oilcrops, pulses, fruits (for name matching reasons)
        if new_cat.endswith('s'):
            new_cat = new_cat[:-1]
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding abp-processed prefix
    processed = ['afats', 'offal']
    for cat in processed:
        new_cat = 'pro-liv-abp-processed-' + cat
        # Dropping the -s at the end afats (for name matching reasons)
        if new_cat.endswith('s'):
            new_cat = new_cat[:-1]
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    # Adding crop processed prefix
    processed = ['voil', 'sweet', 'sugar']
    for cat in processed:
        new_cat = 'pro-crop-processed-' + cat
        dm_lfs.rename_col(cat, new_cat, dim='Categories1')

    return dm_lfs


def agriculture(lever_setting, years_setting):
    #####################
    # CALCULATION TREE  #
    #####################

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    # !FIXME: change path to '../_database/data/datamatrix/agriculture.pickle'
    agriculture_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/agriculture.pickle')
    DM_ots_fts = read_data(agriculture_data_file, lever_setting)

    dm_lfs = simulate_lifestyles_to_agriculture_input()
    # Filter by country
    cntr_list = DM_ots_fts['food-net-import'].col_labels['Country']
    dm_lfs = dm_lfs.filter({'Country': cntr_list})

    # FOOD DEMAND TO DOMESTIC FOOD PRODUCTION ------------------------------------------------------------------------------
    # Overall food demand [kcal] = food demand [kcal] + food waste [kcal]
    dm_lfs.operation('lfs_diet', '+', 'lfs_food-wastes', out_col='agr_demand', unit='kcal')

    # Filtering dms to only keep pro
    dm_lfs_pro = dm_lfs.filter_w_regex({'Categories1':'pro-.*','Variables':'agr_demand'})
    food_net_import_pro = DM_ots_fts['food-net-import'].filter_w_regex({'Categories1':'pro-.*','Variables':'agr_food-net-import'})
    # Dropping the unwanted columns
    food_net_import_pro.drop(dim='Categories1', col_label=['pro-crop-processed-cake', 'pro-crop-processed-molasse'])

    # Sorting the dms alphabetically
    food_net_import_pro.sort(dim='Categories1')
    dm_lfs_pro.sort(dim='Categories1')

    # Domestic production processed food [kcal] = agr_demand_pro_(.*) [kcal] * net-imports_pro_(.*) [%]
    idx_lfs = dm_lfs_pro.idx
    idx_import = food_net_import_pro.idx
    agr_domestic_production = dm_lfs_pro.array[:,:,idx_lfs['agr_demand'],:] \
                              * food_net_import_pro.array[:,:,idx_import['agr_food-net-import'],:]

    dm_lfs_pro.add(agr_domestic_production, dim='Variables', col_label='agr_domestic_production', unit='kcal')


    # idx = dm_lfs.idx
    # overall_food_demand = dm_lfs.array[:,:,idx['lfs_diet'],:] + dm_lfs.array[:,:,idx['lfs_food-wastes'],:]

    print('hello') # list: the 3 dimensions, i.e. country, years and variables
    return


def agriculture_local_run():
    years_setting, lever_setting = init_years_lever()
    agriculture(lever_setting, years_setting)
    return


database_from_csv_to_datamatrix()  # Creates the pickle, to do only once
agriculture_local_run()
