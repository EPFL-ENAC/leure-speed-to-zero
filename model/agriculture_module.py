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

    # Data - Fixed assumptions
    file = 'agriculture_fixed-assumptions'
    lever = 'fixed-assumption'
    # edit_database(file, lever, column='eucalc-name', mode='rename',pattern={'meat_': 'meat-', 'abp_': 'abp-'})

    # Data - Fixed assumptions
    dict_fxa = {}
    file = 'agriculture_calibration-factors_pathwaycalc'
    lever = 'none'
    # Renaming to correct format : Calibration factors - Livestock domestic production
    edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'production_liv': 'production-liv',
                                                                             'abp_': 'abp-', 'meat_': 'meat-',
                                                                             'liv-population_liv-population': 'liv-population'})

    # Data - Fixed assumptions - Calibration factors - Livestock domestic production
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_domestic-production-liv.*'})
    dm_caf_liv_dom_prod = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['caf_agr_domestic-production-liv'] = dm_caf_liv_dom_prod

    # Data - Fixed assumptions - Calibration factors - Livestock population
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_liv-population.*'})
    dm_caf_liv_pop = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['caf_agr_liv-population'] = dm_caf_liv_pop

    # Create a dictionnay with all the fixed assumptions
    dict_fxa = {
        'caf_agr_domestic-production-liv': dm_caf_liv_dom_prod,
        'caf_agr_liv-population': dm_caf_liv_pop
    }


    #####################
    ###### LEVERS #######
    #####################

    dict_ots = {}
    dict_fts = {}

    # Read self-sufficiency
    file = 'agriculture_self-sufficiency_pathwaycalc'
    lever = 'food-net-import'
    # Rename to correct format
    #edit_database(file,lever,column='eucalc-name',pattern={'processeced':'processed'},mode='rename')
    #edit_database(file,lever,column='eucalc-name',pattern={'meat_':'meat-', 'abp_':'abp-', 'processed_':'processed-', 'pro_':'pro-','liv_':'liv-','crop_':'crop-','bev_':'bev-'},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                           dict_ots=dict_ots, dict_fts=dict_fts)

    # Read climate smart livestock
    file = 'agriculture_climate-smart-livestock_pathwaycalc_renamed'
    lever = 'climate-smart-livestock'
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1, 1, 0], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['climate-smart-livestock_losses.*', 'climate-smart-livestock_yield.*', 'climate-smart-livestock_slaughtered.*', 'climate-smart-livestock_density'])

    # num_cat_list=[1 = nb de cat de losses, 1 = nb de cat yield]

    #####################
    ###### CONSTANTS #######
    #####################

    # Data - Constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants',
                                                    pattern='cp_ibp_liv_.*_brf_fdk_afat|cp_ibp_liv_.*_brf_fdk_offal', #use 'xx|xx|xx' to add
                                                    num_cat=0)

    # Group all datamatrix in a single structure
    DM_agriculture = {
        'fxa': dict_fxa,
        'constant': cdm_const,
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

    # FXA data matrix
    dm_fxa_caf_liv_prod = DM_agriculture['fxa']['caf_agr_domestic-production-liv']
    dm_fxa_caf_liv_pop = DM_agriculture['fxa']['caf_agr_liv-population']

    # Extract sub-data-matrices according to the flow (parallel)
    # Diet sub-matrix for the food demand to domestic production sub-flow
    dm_food_net_import_pro = DM_ots_fts['food-net-import'].filter_w_regex({'Categories1': 'pro-.*', 'Variables': 'agr_food-net-import'})

    # Diet sub-matrix for the food demand to domestic production sub-flow
    dm_livestock_losses = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_losses']
    dm_livestock_yield = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_yield']
    dm_livestock_slaughtered = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_slaughtered']
    dm_livestock_density = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_density']

    # Aggregate datamatrix by theme/flow
    # Aggregated Data Matrix - Food demand to domestic production
    DM_food_demand = {
        'food-net-import-pro': dm_food_net_import_pro
    }

    # Aggregated Data Matrix - ASF to livestock population and livestock products
    DM_livestock = {
        'losses': dm_livestock_losses,
        'yield': dm_livestock_yield,
        'liv_slaughtered_rate': dm_livestock_slaughtered,
        'caf_liv_prod': dm_fxa_caf_liv_prod,
        'caf_liv_population': dm_fxa_caf_liv_pop,
        'ruminant_density': dm_livestock_density
    }

    cdm_const = DM_agriculture['constant']

    return DM_ots_fts, DM_food_demand, DM_livestock, cdm_const


def simulate_lifestyles_to_agriculture_input():
    # Read input from lifestyle : food waste & diet
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-agriculture_EUCALC.xlsx")
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
    DM_ots_fts, DM_food_demand, DM_livestock, cdm_const = read_data(agriculture_data_file, lever_setting)

    # Simulate data from lifestyles
    dm_lfs = simulate_lifestyles_to_agriculture_input()
    # Filter by country
    cntr_list = DM_food_demand['food-net-import-pro'].col_labels['Country']
    dm_lfs = dm_lfs.filter({'Country': cntr_list})

    # FOOD DEMAND TO DOMESTIC FOOD PRODUCTION ------------------------------------------------------------------------------
    # Overall food demand [kcal] = food demand [kcal] + food waste [kcal]
    dm_lfs.operation('lfs_diet', '+', 'lfs_food-wastes', out_col='agr_demand', unit='kcal')

    # Filtering dms to only keep pro
    dm_lfs_pro = dm_lfs.filter_w_regex({'Categories1':'pro-.*','Variables':'agr_demand'})
    food_net_import_pro = DM_food_demand['food-net-import-pro'].filter_w_regex({'Categories1':'pro-.*','Variables':'agr_food-net-import'})
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

    # Adding agr_domestic_production to dm_lfs_pro
    dm_lfs_pro.add(agr_domestic_production, dim='Variables', col_label='agr_domestic_production', unit='kcal')

    # Checking that the results are similar to KNIME
    dm_temp = dm_lfs_pro.copy()
    df_temp = dm_temp.write_df()
    filtered_df_pro = df_temp[df_temp['Country'].str.contains('France')]

    dm_temp = dm_lfs.copy()
    df_temp = dm_temp.write_df()
    filtered_df = df_temp[df_temp['Country'].str.contains('France')]

    # ANIMAL SOURCED FOOD DEMAND TO LIVESTOCK POPULATION AND LIVESTOCK PRODUCTS ------------------------------------------------------------------------------

    # Filter dm_lfs_pro to only have livestock products
    dm_lfs_pro_liv = dm_lfs_pro.filter_w_regex({'Categories1': 'pro-liv.*', 'Variables': 'agr_domestic_production'})
    # Drop the pro- prefix of the categories
    dm_lfs_pro_liv.rename_col_regex(str1="pro-liv-", str2="", dim="Categories1")
    # Sort the dms
    dm_lfs_pro_liv.sort(dim='Categories1')
    DM_livestock['losses'].sort(dim='Categories1')
    DM_livestock['yield'].sort(dim='Categories1')

    # Append dm_lfs_pro_liv to DM_livestock['losses']
    DM_livestock['losses'].append(dm_lfs_pro_liv, dim='Variables')

    # Livestock domestic prod with losses [kcal] = livestock domestic prod [kcal] * Production losses livestock [%]
    DM_livestock['losses'].operation('agr_climate-smart-livestock_losses', '*', 'agr_domestic_production', out_col='agr_domestic_production_liv_afw', unit='kcal')

    # Calibration Livestock domestic production
    dm_liv_prod = DM_livestock['losses'].filter({'Variables': ['agr_domestic_production_liv_afw']})
    dm_liv_prod.drop(dim='Categories1', col_label=['abp-processed-offal', 'abp-processed-afat'])# Filter dm_liv_prod to drop offal & afats
    DM_livestock['caf_liv_prod'].append(dm_liv_prod, dim='Variables') # Append to caf
    DM_livestock['caf_liv_prod'].operation('caf_agr_domestic-production-liv', '*', 'agr_domestic_production_liv_afw', # Calibrate
                                            dim="Variables", out_col='cal_agr_domestic_production_liv_afw', unit='kcal')

    # Livestock slaughtered [lsu] = meat demand [kcal] / livestock meat content [kcal/lsu]
    dm_liv_slau = DM_livestock['caf_liv_prod'].filter({'Variables': ['cal_agr_domestic_production_liv_afw']})
    DM_livestock['yield'].append(dm_liv_slau, dim='Variables') # Append cal_agr_domestic_production_liv_afw in yield
    DM_livestock['yield'].operation('cal_agr_domestic_production_liv_afw', '/', 'agr_climate-smart-livestock_yield',
                                           dim="Variables", out_col='agr_liv_population', unit='lsu')

    # Livestock population for meat [lsu] = Livestock slaughtered [lsu] / slaughter rate [%]
    dm_liv_slau_meat = DM_livestock['yield'].filter({'Variables': ['agr_liv_population'], 'Categories1': ['meat-bovine', 'meat-pig', 'meat-poultry', 'meat-sheep', 'meat-oth-animals']})
    DM_livestock['liv_slaughtered_rate'].append(dm_liv_slau_meat, dim='Variables')
    DM_livestock['liv_slaughtered_rate'].operation('agr_liv_population', '/', 'agr_climate-smart-livestock_slaughtered',
                                    dim="Variables", out_col='agr_liv_population_meat', unit='lsu')

    # Processeing for calibration: Livestock population for meat, eggs and dairy ( meat pop & slaughtered livestock for eggs and dairy)
    # Filtering eggs, dairy and meat
    dm_liv_slau_egg_dairy = DM_livestock['yield'].filter({'Variables': ['agr_liv_population'], 'Categories1': ['abp-dairy-milk', 'abp-hens-egg']})
    dm_liv_slau_meat = DM_livestock['liv_slaughtered_rate'].filter({'Variables': ['agr_liv_population_meat']})
    # Rename dm_liv_slau_meat variable to match with dm_liv_slau_egg_dairy
    dm_liv_slau_meat.rename_col('agr_liv_population_meat', 'agr_liv_population', dim='Variables')
    # Appending between livestock population
    dm_liv_slau_egg_dairy.append(dm_liv_slau_meat, dim='Categories1')

    # Calibration Livestock population
    DM_livestock['caf_liv_population'].append(dm_liv_slau_egg_dairy, dim='Variables')  # Append to caf
    DM_livestock['caf_liv_population'].operation('caf_agr_liv-population', '*', 'agr_liv_population',
                                           dim="Variables", out_col='cal_agr_liv_population', unit='lsu')


    # Grazing livestock
    # Filtering ruminants (bovine & sheep)
    dm_liv_ruminants = DM_livestock['caf_liv_population'].filter({'Variables': ['cal_agr_liv_population'], 'Categories1': ['meat-bovine', 'meat-sheep']})
    # Ruminant livestock [lsu] = population bovine + population sheep
    dm_liv_ruminants.operation('meat-bovine', '+', 'meat-sheep', dim="Categories1", out_col='ruminant')
    # Append to relevant dm
    dm_liv_ruminants = dm_liv_ruminants.filter({'Variables': ['cal_agr_liv_population'], 'Categories1': ['ruminant']})
    dm_liv_ruminants = dm_liv_ruminants.flatten() # change from category to variable
    DM_livestock['ruminant_density'].append(dm_liv_ruminants, dim='Variables')  # Append to caf
    # Agriculture grassland [ha] = ruminant livestock [lsu] / livestock density [lsu/ha]
    DM_livestock['ruminant_density'].operation('cal_agr_liv_population_ruminant', '/', 'agr_climate-smart-livestock_density',
                                               dim="Variables", out_col='agr_lus_land_grassland', unit='ha')

    # Livestock byproducts

    # Filter ibp constants for offal
    cdm_cp_ibp_offal = cdm_const.filter_w_regex({'Variables': 'cp_ibp_liv_.*_brf_fdk_offal'})
    cdm_cp_ibp_offal.rename_col_regex('_brf_fdk_offal', '', dim='Variables')
    cdm_cp_ibp_offal.rename_col_regex('liv_', 'liv_meat-', dim='Variables')
    cdm_cp_ibp_offal.deepen(based_on='Variables') # Creating categories

    # Filter ibp constants for afat
    cdm_cp_ibp_afat = cdm_const.filter_w_regex({'Variables': 'cp_ibp_liv_.*_brf_fdk_afat'})
    cdm_cp_ibp_afat.rename_col_regex('_brf_fdk_afat', '', dim='Variables')
    cdm_cp_ibp_afat.rename_col_regex('liv_', 'liv_meat-', dim='Variables')
    cdm_cp_ibp_afat.deepen(based_on='Variables')  # Creating categories

    # Filter cal_agr_liv_population for meat
    cal_liv_population_meat = DM_livestock['caf_liv_population'].filter_w_regex({'Variables': 'cal_agr_liv_population', 'Categories1': 'meat'})
    DM_livestock['liv_slaughtered_rate'].append(cal_liv_population_meat, dim='Variables') # Appending to the dm that has the same categories

    # Sort categories ?? already in correct order

    # Offal per livestock type [kcal] = livestock population meat [lsu] * yield offal [kcal/lsu]
    idx_liv_pop = DM_livestock['liv_slaughtered_rate'].idx
    idx_cdm_offal = cdm_cp_ibp_offal.idx
    agr_ibp_offal = DM_livestock['liv_slaughtered_rate'].array[:, :, idx_liv_pop['cal_agr_liv_population'], :] \
                              * cdm_cp_ibp_offal.array[idx_cdm_offal['cp_ibp_liv']]
    DM_livestock['liv_slaughtered_rate'].add(agr_ibp_offal, dim='Variables', col_label='agr_ibp_offal', unit='kcal')

    # Afat per livestock type [kcal] = livestock population meat [lsu] * yield afat [kcal/lsu]
    idx_liv_pop = DM_livestock['liv_slaughtered_rate'].idx
    idx_cdm_afat = cdm_cp_ibp_afat.idx
    agr_ibp_afat = DM_livestock['liv_slaughtered_rate'].array[:, :, idx_liv_pop['cal_agr_liv_population'], :] \
                    * cdm_cp_ibp_afat.array[idx_cdm_afat['cp_ibp_liv']]
    DM_livestock['liv_slaughtered_rate'].add(agr_ibp_afat, dim='Variables', col_label='agr_ibp_afat', unit='kcal')

    # Totals offal/afat [kcal] = sum (Offal/afat per livestock type [kcal])
    dm_offal = DM_livestock['liv_slaughtered_rate'].filter({'Variables': ['agr_ibp_offal']})
    dm_liv_ibp = dm_offal.copy()
    dm_liv_ibp.groupby({'offal': '.*'}, dim='Categories1', regex=True, inplace=True)
    dm_afat = DM_livestock['liv_slaughtered_rate'].filter({'Variables': ['agr_ibp_afat']})
    dm_total_afat = dm_afat.copy()
    dm_total_afat.groupby({'afat': '.*'}, dim='Categories1', regex=True, inplace=True)

    # Append Totals offal with total afat and rename variable
    dm_liv_ibp.append(dm_total_afat, dim='Categories1')
    dm_liv_ibp.rename_col('agr_ibp_offal', 'agr_ibp_total', dim='Variables')

    # Filter Processed offal/afats afw (not calibrated), rename and append with dm_liv_ibp
    dm_processed_offal_afat = DM_livestock['losses'].filter({'Variables': ['agr_domestic_production_liv_afw'],
                                                          'Categories1': ['abp-processed-offal','abp-processed-afat']})
    dm_processed_offal_afat.rename_col_regex(str1="abp-processed-", str2="", dim="Categories1")
    dm_liv_ibp.append(dm_processed_offal_afat, dim='Variables')

    # Offal/afats for feedstock [kcal] = produced offal/afats [kcal] - processed offal/afat [kcal]
    dm_liv_ibp.operation('agr_ibp_total', '-', 'agr_domestic_production_liv_afw', out_col='agr_ibp_liv_fdk', unit='kcal')

    # Total offal and afats for feedstock [kcal] = Offal for feedstock [kcal] + Afats for feedstock [kcal]
    dm_ibp_fdk = dm_liv_ibp.filter({'Variables': ['agr_ibp_liv_fdk']})
    dm_ibp_fdk.groupby({'total': '.*'}, dim='Categories1', regex=True, inplace=True)

    print('hello') # list: the 3 dimensions, i.e. country, years and variables
    return


def agriculture_local_run():
    years_setting, lever_setting = init_years_lever()
    agriculture(lever_setting, years_setting)
    return

# Creates the pickle, to do only once
#database_from_csv_to_datamatrix()

# Run the code un local
agriculture_local_run()
