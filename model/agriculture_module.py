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

# DatabaseToDatamatrix
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

    # FixedAssumptionsToDatamatrix
    dict_fxa = {}
    file = 'agriculture_fixed-assumptions_pathwaycalc'
    lever = 'none'
    #edit_database(file, lever, column='eucalc-name', mode='rename',pattern={'meat_': 'meat-', 'abp_': 'abp-'})
    # LIVESTOCK MANURE - N2O emissions
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'ef_liv_N2O-emission_ef.*'})
    dm_ef_N2O = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['ef_liv_N2O-emission'] = dm_ef_N2O
    # LIVESTOCK MANURE - CH4 emissions
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'ef_liv_CH4-emission_treated.*'})
    dm_ef_CH4 = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['ef_liv_CH4-emission_treated'] = dm_ef_CH4
    # LIVESTOCK MANURE - N stock
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'liv_manure_n-stock.*'})
    dm_nstock = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['liv_manure_n-stock'] = dm_nstock

    # CalibrationFactorsToDatamatrix
    # Data - Fixed assumptions
    file = 'agriculture_calibration-factors_pathwaycalc'
    lever = 'none'
    # Renaming to correct format : Calibration factors - Livestock domestic production
    # edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'production_liv': 'production-liv',
     #                                                                        'abp_': 'abp-', 'meat_': 'meat-',
     #                                                                        'liv-population_liv-population': 'liv-population'})
    # Renaming to correct format : Calibration factors - Livestock CH4 emissions
    #edit_database(file, lever, column='eucalc-name', mode='rename', pattern={'enteric_meat-bovine': 'meat-bovine_enteric',
    #                                                                         'enteric_meat-oth-animals': 'meat-oth-animals_enteric',
    #                                                                         'enteric_meat-pig': 'meat-pig_enteric',
    #                                                                         'enteric_meat-poultry': 'meat-poultry_enteric',
    #                                                                         'enteric_meat-sheep': 'meat-sheep_enteric',
    #                                                                         'enteric_abp-dairy-milk': 'abp-dairy-milk_enteric',
    #                                                                         'enteric_abp-hens-egg': 'abp-hens-egg_enteric'})
    #edit_database(file, lever, column='eucalc-name', mode='rename',
    #              pattern={'treated_meat-bovine': 'meat-bovine_treated',
    #                       'treated_meat-oth-animals': 'meat-oth-animals_treated',
    #                       'treated_meat-pig': 'meat-pig_treated',
    #                       'treated_meat-poultry': 'meat-poultry_treated',
    #                       'treated_meat-sheep': 'meat-sheep_treated',
    #                       'treated_abp-dairy-milk': 'abp-dairy-milk_treated',
    #                       'treated_abp-hens-egg': 'abp-hens-egg_treated',
    #                       'meat-abp': 'abp'})

    # Data - Fixed assumptions - Calibration factors - Livestock domestic production
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_domestic-production-liv.*'})
    dm_caf_liv_dom_prod = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['caf_agr_domestic-production-liv'] = dm_caf_liv_dom_prod

    # Data - Fixed assumptions - Calibration factors - Livestock population
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_liv-population.*'})
    dm_caf_liv_pop = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['caf_agr_liv-population'] = dm_caf_liv_pop

    # Data - Fixed assumptions - Calibration factors - Livestock CH4 emissions
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_liv_CH4-emission.*'})
    dm_caf_liv_CH4 = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['caf_agr_liv_CH4-emission'] = dm_caf_liv_CH4


    # Data - Fixed assumptions - Calibration factors - Livestock N2O emissions
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'caf_agr_liv_N2O-emission.*'})
    dm_caf_liv_N2O = DataMatrix.create_from_df(df, num_cat=2)
    dict_fxa['caf_agr_liv_N2O-emission'] = dm_caf_liv_N2O

    # Create a dictionnay with all the fixed assumptions
    dict_fxa = {
        'caf_agr_domestic-production-liv': dm_caf_liv_dom_prod,
        'caf_agr_liv-population': dm_caf_liv_pop,
        'caf_agr_liv_CH4-emission': dm_caf_liv_CH4,
        'caf_agr_liv_N2O-emission': dm_caf_liv_N2O,
        'ef_liv_N2O-emission': dm_ef_N2O,
        'ef_liv_CH4-emission_treated': dm_ef_CH4,
        'liv_manure_n-stock': dm_nstock
    }


    #####################
    ###### LEVERS #######
    #####################
    # LeversToDatamatrix
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
    #edit_database(file,lever,column='eucalc-name',pattern={'_CH4-emission':''},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1, 1, 0, 1, 2], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['climate-smart-livestock_losses.*', 'climate-smart-livestock_yield.*',
                                                                            'climate-smart-livestock_slaughtered.*', 'climate-smart-livestock_density',
                                                                            'climate-smart-livestock_enteric.*', 'climate-smart-livestock_manure.*'])

    # Read biomass hierarchy
    file = 'agriculture_biomass-use-hierarchy_pathwaycalc'
    lever = 'biomass-hierarchy'
    # Rename to correct format
    #edit_database(file,lever,column='eucalc-name',pattern={'bev_ibp_use_oth':'bev-ibp-use-oth', 'biomass-hierarchy_bev':'biomass-hierarchy-bev', 'solid_bioenergy':'solid-bioenergy'},mode='rename')
    #edit_database(file,lever,column='eucalc-name',pattern={'liquid_eth_':'liquid_eth-', 'liquid_oil_':'liquid_oil-', 'lgn_btl_':'lgn-btl-', 'lgn_ezm_':'lgn-ezm-'},mode='rename')
    #edit_database(file,lever,column='eucalc-name',pattern={'biodiesel_tec_':'biodiesel_', 'biogasoline_tec_':'biogasoline_', 'biojetkerosene_tec_':'biojetkerosene_'},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1, 1, 1, 1, 1, 1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['.*biomass-hierarchy-bev-ibp-use-oth.*',
                                                                            'biomass-hierarchy_biomass-mix_digestor.*',
                                                                            'biomass-hierarchy_biomass-mix_solid.*',
                                                                            'biomass-hierarchy_biomass-mix_liquid.*',
                                                                            'biomass-hierarchy_bioenergy_liquid_biodiesel.*',
                                                                            'biomass-hierarchy_bioenergy_liquid_biogasoline.*',
                                                                            'biomass-hierarchy_bioenergy_liquid_biojetkerosene.*'])

    # Read bioenergy capacity
    file = 'agriculture_bioenergy-capacity_pathwaycalc'
    lever = 'bioenergy-capacity'
    # Rename to correct format
    #edit_database(file,lever,column='eucalc-name',pattern={'capacity_solid-biofuel':'capacity_elec_solid-biofuel', 'capacity_biogases':'capacity_elec_biogases'},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1, 1, 1, 1], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['bioenergy-capacity_load-factor.*', 'bioenergy-capacity_bgs-mix.*',
                                                                            'bioenergy-capacity_efficiency.*', 'bioenergy-capacity_liq_b.*', 'bioenergy-capacity_elec.*'])


    # num_cat_list=[1 = nb de cat de losses, 1 = nb de cat yield]

    #####################
    ###### CONSTANTS #######
    #####################
    # ConstantsToDatamatrix
    # Data - Constants (use 'xx|xx|xx' to add)
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants',
                                                    pattern='cp_ibp_liv_.*_brf_fdk_afat|cp_ibp_liv_.*_brf_fdk_offal|cp_ibp_bev_.*|cp_liquid_tec.*|cp_load_hours',
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
    dm_fxa_caf_liv_CH4 = DM_agriculture['fxa']['caf_agr_liv_CH4-emission']
    dm_fxa_caf_liv_N2O = DM_agriculture['fxa']['caf_agr_liv_N2O-emission']
    #dm_fxa_caf_liv_CH4.rename_col_regex(str1="caf_agr_liv_CH4-emission_", str2="", dim="Variables")
    #dm_fxa_caf_liv_N2O.rename_col_regex(str1="caf_agr_liv_N2O-emission_", str2="", dim="Variables")
    dm_fxa_ef_liv_N2O = DM_agriculture['fxa']['ef_liv_N2O-emission']
    #dm_fxa_ef_liv_N2O.rename_col_regex(str1="fxa_ef_liv_N2O-emission_", str2="", dim="Variables")
    dm_fxa_ef_liv_CH4_treated = DM_agriculture['fxa']['ef_liv_CH4-emission_treated']
    dm_fxa_liv_nstock = DM_agriculture['fxa']['liv_manure_n-stock']

    # Extract sub-data-matrices according to the flow
    # Sub-matrix for the FOOD DEMAND
    dm_food_net_import_pro = DM_ots_fts['food-net-import'].filter_w_regex({'Categories1': 'pro-.*', 'Variables': 'agr_food-net-import'})

    # Sub-matrix for LIVESTOCK
    dm_livestock_losses = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_losses']
    dm_livestock_yield = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_yield']
    dm_livestock_slaughtered = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_slaughtered']
    dm_livestock_density = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_density']


    # Sub-matrix for ALCOHOLIC BEVERAGES
    dm_alc_bev = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy-bev-ibp-use-oth']

    # Sub-matrix for BIOENERGY
    dm_bioenergy_cap_load_factor = DM_ots_fts['bioenergy-capacity']['bioenergy-capacity_load-factor']
    dm_bioenergy_cap_bgs_mix = DM_ots_fts['bioenergy-capacity']['bioenergy-capacity_bgs-mix']
    dm_bioenergy_cap_efficiency = DM_ots_fts['bioenergy-capacity']['bioenergy-capacity_efficiency']
    dm_bioenergy_cap_liq = DM_ots_fts['bioenergy-capacity']['bioenergy-capacity_liq_b']
    dm_bioenergy_cap_elec = DM_ots_fts['bioenergy-capacity']['bioenergy-capacity_elec']
    dm_bioenergy_mix_digestor = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_biomass-mix_digestor']
    dm_bioenergy_mix_solid = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_biomass-mix_solid']
    dm_bioenergy_mix_liquid = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_biomass-mix_liquid']
    dm_bioenergy_liquid_biodiesel = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_bioenergy_liquid_biodiesel']
    dm_bioenergy_liquid_biogasoline = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_bioenergy_liquid_biogasoline']
    dm_bioenergy_liquid_biojetkerosene = DM_ots_fts['biomass-hierarchy']['biomass-hierarchy_bioenergy_liquid_biojetkerosene']
    dm_bioenergy_cap_elec.append(dm_bioenergy_cap_load_factor, dim='Variables')
    dm_bioenergy_cap_elec.append(dm_bioenergy_cap_efficiency, dim='Variables')

    # Sub-matrix for LIVESTOCK MANURE MANGEMENT & GHG EMISSIONS
    dm_livestock_enteric_emissions = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_enteric']
    dm_livestock_manure = DM_ots_fts['climate-smart-livestock']['climate-smart-livestock_manure']
    dm_livestock_manure.rename_col_regex(str1="agr_climate-smart-livestock_manure_", str2="", dim="Variables")

    # Aggregate datamatrix by theme/flow
    # Aggregated Data Matrix - FOOD DEMAND
    DM_food_demand = {
        'food-net-import-pro': dm_food_net_import_pro
    }

    # Aggregated Data Matrix - LIVESTOCK
    DM_livestock = {
        'losses': dm_livestock_losses,
        'yield': dm_livestock_yield,
        'liv_slaughtered_rate': dm_livestock_slaughtered,
        'caf_liv_prod': dm_fxa_caf_liv_prod,
        'caf_liv_population': dm_fxa_caf_liv_pop,
        'ruminant_density': dm_livestock_density
    }

    # Aggregated Data Matrix - ALCOHOLIC BEVERAGES
    DM_alc_bev = {
        'biomass_hierarchy': dm_alc_bev
    }

    # Aggregated Data Matrix - BIOENERGY
    DM_bioenergy = {
        'electricity_production': dm_bioenergy_cap_elec,
        'bgs-mix': dm_bioenergy_cap_bgs_mix,
        'liq': dm_bioenergy_cap_liq,
        'digestor-mix': dm_bioenergy_mix_digestor,
        'solid-mix': dm_bioenergy_mix_solid,
        'liquid-mix': dm_bioenergy_mix_liquid,
        'liquid-biodiesel': dm_bioenergy_liquid_biodiesel,
        'liquid-biogasoline': dm_bioenergy_liquid_biogasoline,
        'liquid-biojetkerosene': dm_bioenergy_liquid_biojetkerosene
    }

    # Aggregated Data Matrix - LIVESTOCK MANURE MANAGEMENT & GHG EMISSIONS
    DM_manure = {
        'enteric_emission': dm_livestock_enteric_emissions,
        'manure': dm_livestock_manure,
        'caf_liv_CH4': dm_fxa_caf_liv_CH4,
        'caf_liv_N2O': dm_fxa_caf_liv_N2O,
        'ef_liv_N2O': dm_fxa_ef_liv_N2O ,
        'ef_liv_CH4_treated': dm_fxa_ef_liv_CH4_treated,
        'liv_n-stock': dm_fxa_liv_nstock
    }

    cdm_const = DM_agriculture['constant']

    return DM_ots_fts, DM_food_demand, DM_livestock, DM_alc_bev, DM_bioenergy, DM_manure, cdm_const

# SimulateInteractions
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
def simulate_buildings_to_agriculture_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-buildings-to-agriculture_renamed.xlsx")
    # the renamed version has - instead of _
    df = pd.read_excel(f, sheet_name="default")
    dm_bld = DataMatrix.create_from_df(df, num_cat=1)

    return dm_bld
def simulate_industry_to_agriculture_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-industry-to-agriculture.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_ind = DataMatrix.create_from_df(df, num_cat=0)

    return dm_ind
def simulate_transport_to_agriculture_input():
    # Read input from lifestyle : food waste & diet
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-transport-to-agriculture_renamed.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_tra = DataMatrix.create_from_df(df, num_cat=1)

    return dm_tra

# CalculationLeaf FOOD DEMAND TO DOMESTIC FOOD PRODUCTION --------------------------------------------------------------
def food_demand_workflow(DM_food_demand, dm_lfs):

    # Overall food demand [kcal] = food demand [kcal] + food waste [kcal]
    dm_lfs.operation('lfs_diet', '+', 'lfs_food-wastes', out_col='agr_demand', unit='kcal')

    # Filtering dms to only keep pro
    dm_lfs_pro = dm_lfs.filter_w_regex({'Categories1': 'pro-.*', 'Variables': 'agr_demand'})
    food_net_import_pro = DM_food_demand['food-net-import-pro'].filter_w_regex(
        {'Categories1': 'pro-.*', 'Variables': 'agr_food-net-import'})
    # Dropping the unwanted columns
    food_net_import_pro.drop(dim='Categories1', col_label=['pro-crop-processed-cake', 'pro-crop-processed-molasse'])

    # Sorting the dms alphabetically
    food_net_import_pro.sort(dim='Categories1')
    dm_lfs_pro.sort(dim='Categories1')

    # Domestic production processed food [kcal] = agr_demand_pro_(.*) [kcal] * net-imports_pro_(.*) [%]
    idx_lfs = dm_lfs_pro.idx
    idx_import = food_net_import_pro.idx
    agr_domestic_production = dm_lfs_pro.array[:, :, idx_lfs['agr_demand'], :] \
                              * food_net_import_pro.array[:, :, idx_import['agr_food-net-import'], :]

    # Adding agr_domestic_production to dm_lfs_pro
    dm_lfs_pro.add(agr_domestic_production, dim='Variables', col_label='agr_domestic_production', unit='kcal')

    # Checking that the results are similar to KNIME
    dm_temp = dm_lfs_pro.copy()
    df_temp = dm_temp.write_df()
    filtered_df_pro = df_temp[df_temp['Country'].str.contains('France')]

    dm_temp = dm_lfs.copy()
    df_temp = dm_temp.write_df()
    filtered_df = df_temp[df_temp['Country'].str.contains('France')]

    return dm_lfs, dm_lfs_pro

# CalculationLeaf ANIMAL SOURCED FOOD DEMAND TO LIVESTOCK POPULATION AND LIVESTOCK PRODUCTS ----------------------------
def livestock_workflow(DM_livestock, cdm_const, dm_lfs_pro):

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
    DM_livestock['losses'].operation('agr_climate-smart-livestock_losses', '*', 'agr_domestic_production',
                                     out_col='agr_domestic_production_liv_afw', unit='kcal')

    # Calibration Livestock domestic production
    dm_liv_prod = DM_livestock['losses'].filter({'Variables': ['agr_domestic_production_liv_afw']})
    dm_liv_prod.drop(dim='Categories1', col_label=['abp-processed-offal',
                                                   'abp-processed-afat'])  # Filter dm_liv_prod to drop offal & afats
    DM_livestock['caf_liv_prod'].append(dm_liv_prod, dim='Variables')  # Append to caf
    DM_livestock['caf_liv_prod'].operation('caf_agr_domestic-production-liv', '*', 'agr_domestic_production_liv_afw',
                                           # Calibrate
                                           dim="Variables", out_col='cal_agr_domestic_production_liv_afw', unit='kcal')

    # Livestock slaughtered [lsu] = meat demand [kcal] / livestock meat content [kcal/lsu]
    dm_liv_slau = DM_livestock['caf_liv_prod'].filter({'Variables': ['cal_agr_domestic_production_liv_afw']})
    DM_livestock['yield'].append(dm_liv_slau, dim='Variables')  # Append cal_agr_domestic_production_liv_afw in yield
    DM_livestock['yield'].operation('cal_agr_domestic_production_liv_afw', '/', 'agr_climate-smart-livestock_yield',
                                    dim="Variables", out_col='agr_liv_population', unit='lsu')

    # Livestock population for meat [lsu] = Livestock slaughtered [lsu] / slaughter rate [%]
    dm_liv_slau_meat = DM_livestock['yield'].filter({'Variables': ['agr_liv_population'],
                                                     'Categories1': ['meat-bovine', 'meat-pig', 'meat-poultry',
                                                                     'meat-sheep', 'meat-oth-animals']})
    DM_livestock['liv_slaughtered_rate'].append(dm_liv_slau_meat, dim='Variables')
    DM_livestock['liv_slaughtered_rate'].operation('agr_liv_population', '/', 'agr_climate-smart-livestock_slaughtered',
                                                   dim="Variables", out_col='agr_liv_population_meat', unit='lsu')

    # Processeing for calibration: Livestock population for meat, eggs and dairy ( meat pop & slaughtered livestock for eggs and dairy)
    # Filtering eggs, dairy and meat
    dm_liv_slau_egg_dairy = DM_livestock['yield'].filter(
        {'Variables': ['agr_liv_population'], 'Categories1': ['abp-dairy-milk', 'abp-hens-egg']})
    dm_liv_slau_meat = DM_livestock['liv_slaughtered_rate'].filter({'Variables': ['agr_liv_population_meat']})
    # Rename dm_liv_slau_meat variable to match with dm_liv_slau_egg_dairy
    dm_liv_slau_meat.rename_col('agr_liv_population_meat', 'agr_liv_population', dim='Variables')
    # Appending between livestock population
    dm_liv_slau_egg_dairy.append(dm_liv_slau_meat, dim='Categories1')

    # Calibration Livestock population
    DM_livestock['caf_liv_population'].append(dm_liv_slau_egg_dairy, dim='Variables')  # Append to caf
    DM_livestock['caf_liv_population'].operation('caf_agr_liv-population', '*', 'agr_liv_population',
                                                 dim="Variables", out_col='cal_agr_liv_population', unit='lsu')

    # GRAZING LIVESTOCK
    # Filtering ruminants (bovine & sheep)
    dm_liv_ruminants = DM_livestock['caf_liv_population'].filter(
        {'Variables': ['cal_agr_liv_population'], 'Categories1': ['meat-bovine', 'meat-sheep']})
    # Ruminant livestock [lsu] = population bovine + population sheep
    dm_liv_ruminants.operation('meat-bovine', '+', 'meat-sheep', dim="Categories1", out_col='ruminant')
    # Append to relevant dm
    dm_liv_ruminants = dm_liv_ruminants.filter({'Variables': ['cal_agr_liv_population'], 'Categories1': ['ruminant']})
    dm_liv_ruminants = dm_liv_ruminants.flatten()  # change from category to variable
    DM_livestock['ruminant_density'].append(dm_liv_ruminants, dim='Variables')  # Append to caf
    # Agriculture grassland [ha] = ruminant livestock [lsu] / livestock density [lsu/ha]
    DM_livestock['ruminant_density'].operation('cal_agr_liv_population_ruminant', '/',
                                               'agr_climate-smart-livestock_density',
                                               dim="Variables", out_col='agr_lus_land_grassland', unit='ha')

    # LIVESTOCK BYPRODUCTS
    # Filter ibp constants for offal
    cdm_cp_ibp_offal = cdm_const.filter_w_regex({'Variables': 'cp_ibp_liv_.*_brf_fdk_offal'})
    cdm_cp_ibp_offal.rename_col_regex('_brf_fdk_offal', '', dim='Variables')
    cdm_cp_ibp_offal.rename_col_regex('liv_', 'liv_meat-', dim='Variables')
    cdm_cp_ibp_offal.deepen(based_on='Variables')  # Creating categories

    # Filter ibp constants for afat
    cdm_cp_ibp_afat = cdm_const.filter_w_regex({'Variables': 'cp_ibp_liv_.*_brf_fdk_afat'})
    cdm_cp_ibp_afat.rename_col_regex('_brf_fdk_afat', '', dim='Variables')
    cdm_cp_ibp_afat.rename_col_regex('liv_', 'liv_meat-', dim='Variables')
    cdm_cp_ibp_afat.deepen(based_on='Variables')  # Creating categories

    # Filter cal_agr_liv_population for meat
    cal_liv_population_meat = DM_livestock['caf_liv_population'].filter_w_regex(
        {'Variables': 'cal_agr_liv_population', 'Categories1': 'meat'})
    DM_livestock['liv_slaughtered_rate'].append(cal_liv_population_meat,
                                                dim='Variables')  # Appending to the dm that has the same categories

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
                                                             'Categories1': ['abp-processed-offal',
                                                                             'abp-processed-afat']})
    dm_processed_offal_afat.rename_col_regex(str1="abp-processed-", str2="", dim="Categories1")
    dm_liv_ibp.append(dm_processed_offal_afat, dim='Variables')

    # Offal/afats for feedstock [kcal] = produced offal/afats [kcal] - processed offal/afat [kcal]
    dm_liv_ibp.operation('agr_ibp_total', '-', 'agr_domestic_production_liv_afw', out_col='agr_ibp_liv_fdk',
                         unit='kcal')

    # Total offal and afats for feedstock [kcal] = Offal for feedstock [kcal] + Afats for feedstock [kcal]
    dm_ibp_fdk = dm_liv_ibp.filter({'Variables': ['agr_ibp_liv_fdk']})
    dm_liv_ibp.groupby({'total': '.*'}, dim='Categories1', regex=True, inplace=True)

    return DM_livestock, dm_liv_ibp, dm_liv_ibp

# CalculationLeaf ALCOHOLIC BEVERAGES INDUSTRY -------------------------------------------------------------------------
def alcoholic_beverages_workflow(DM_alc_bev, cdm_const, dm_lfs_pro):
    # From FOOD DEMAND filtering domestic production bev and renaming
    # Beer
    dm_bev_beer = dm_lfs_pro.filter_w_regex({'Categories1': 'pro-bev-beer.*', 'Variables': 'agr_domestic_production'})
    dm_bev_beer.rename_col_regex(str1="pro-bev-", str2="", dim="Categories1")
    dm_bev_beer = dm_bev_beer.flatten()
    # Bev-alc
    dm_bev_alc = dm_lfs_pro.filter_w_regex({'Categories1': 'pro-bev-bev-alc.*', 'Variables': 'agr_domestic_production'})
    dm_bev_alc.rename_col_regex(str1="pro-bev-", str2="", dim="Categories1")
    dm_bev_alc = dm_bev_alc.flatten()
    # Bev-fer
    dm_bev_fer = dm_lfs_pro.filter_w_regex({'Categories1': 'pro-bev-bev-fer.*', 'Variables': 'agr_domestic_production'})
    dm_bev_fer.rename_col_regex(str1="pro-bev-", str2="", dim="Categories1")
    dm_bev_fer = dm_bev_fer.flatten()
    # Wine
    dm_bev_wine = dm_lfs_pro.filter_w_regex({'Categories1': 'pro-bev-wine.*', 'Variables': 'agr_domestic_production'})
    dm_bev_wine.rename_col_regex(str1="pro-bev-", str2="", dim="Categories1")
    dm_bev_wine = dm_bev_wine.flatten()

    # From CDM_CONSTANT filtering relevant constants and sorting according to bev type (beer, wine, bev-alc, bev-fer)
    cdm_cp_ibp_bev_beer = cdm_const.filter_w_regex({'Variables': 'cp_ibp_bev_beer.*'})
    cdm_cp_ibp_bev_wine = cdm_const.filter_w_regex({'Variables': 'cp_ibp_bev_wine.*'})
    cdm_cp_ibp_bev_alc = cdm_const.filter_w_regex({'Variables': 'cp_ibp_bev_bev-alc.*'})
    cdm_cp_ibp_bev_fer = cdm_const.filter_w_regex({'Variables': 'cp_ibp_bev_bev-fer.*'})

    # Byproducts per bev type [kcal] = agr_domestic_production bev [kcal] * yields [%]
    # Beer - Feedstock Yeast
    idx_dm_bev_beer = dm_bev_beer.idx
    idx_cdm_ibp_beer = cdm_cp_ibp_bev_beer.idx
    agr_ibp_bev_beer_fdk_yeast = dm_bev_beer.array[:, :, idx_dm_bev_beer['agr_domestic_production_beer']] \
                                 * cdm_cp_ibp_bev_beer.array[idx_cdm_ibp_beer['cp_ibp_bev_beer_brf_fdk_yeast']]
    dm_bev_beer.add(agr_ibp_bev_beer_fdk_yeast, dim='Variables', col_label='agr_ibp_bev_beer_fdk_yeast', unit='kcal')

    # Beer - Feedstock Cereal
    idx_dm_bev_beer = dm_bev_beer.idx
    idx_cdm_ibp_beer = cdm_cp_ibp_bev_beer.idx
    agr_ibp_bev_beer_fdk_cereal = dm_bev_beer.array[:, :, idx_dm_bev_beer['agr_domestic_production_beer']] \
                                  * cdm_cp_ibp_bev_beer.array[idx_cdm_ibp_beer['cp_ibp_bev_beer_brf_fdk_cereal']]
    dm_bev_beer.add(agr_ibp_bev_beer_fdk_cereal, dim='Variables', col_label='agr_ibp_bev_beer_fdk_cereal', unit='kcal')

    # Beer - Crop Cereal
    idx_dm_bev_beer = dm_bev_beer.idx
    idx_cdm_ibp_beer = cdm_cp_ibp_bev_beer.idx
    agr_ibp_bev_beer_crop_cereal = dm_bev_beer.array[:, :, idx_dm_bev_beer['agr_domestic_production_beer']] \
                                   * cdm_cp_ibp_bev_beer.array[idx_cdm_ibp_beer['cp_ibp_bev_beer_brf_crop_cereal']]
    dm_bev_beer.add(agr_ibp_bev_beer_crop_cereal, dim='Variables', col_label='agr_ibp_bev_beer_crop_cereal',
                    unit='kcal')

    # Bev-alc - Crop fruit
    idx_dm_bev_alc = dm_bev_alc.idx
    idx_cdm_ibp_alc = cdm_cp_ibp_bev_alc.idx
    agr_ibp_bev_alc_crop_fruit = dm_bev_alc.array[:, :, idx_dm_bev_alc['agr_domestic_production_bev-alc']] \
                                 * cdm_cp_ibp_bev_alc.array[idx_cdm_ibp_alc['cp_ibp_bev_bev-alc_brf_crop_fruit']]
    dm_bev_alc.add(agr_ibp_bev_alc_crop_fruit, dim='Variables', col_label='agr_ibp_bev_bev-alc_crop_fruit',
                   unit='kcal')

    # Bev-fer - Crop cereal
    idx_dm_bev_fer = dm_bev_fer.idx
    idx_cdm_ibp_fer = cdm_cp_ibp_bev_fer.idx
    agr_ibp_bev_fer_crop_cereal = dm_bev_fer.array[:, :, idx_dm_bev_fer['agr_domestic_production_bev-fer']] \
                                  * cdm_cp_ibp_bev_fer.array[idx_cdm_ibp_fer['cp_ibp_bev_bev-fer_brf_crop_cereal']]
    dm_bev_fer.add(agr_ibp_bev_fer_crop_cereal, dim='Variables', col_label='agr_ibp_bev_bev-fer_crop_cereal',
                   unit='kcal')

    # Wine - Feedstock Marc
    idx_dm_bev_wine = dm_bev_wine.idx
    idx_cdm_ibp_wine = cdm_cp_ibp_bev_wine.idx
    agr_ibp_bev_wine_fdk_marc = dm_bev_wine.array[:, :, idx_dm_bev_wine['agr_domestic_production_wine']] \
                                * cdm_cp_ibp_bev_wine.array[idx_cdm_ibp_wine['cp_ibp_bev_wine_brf_fdk_marc']]
    dm_bev_wine.add(agr_ibp_bev_wine_fdk_marc, dim='Variables', col_label='agr_ibp_bev_wine_fdk_marc', unit='kcal')

    # Wine - Feedstock Lees
    idx_dm_bev_wine = dm_bev_wine.idx
    idx_cdm_ibp_wine = cdm_cp_ibp_bev_wine.idx
    agr_ibp_bev_wine_fdk_lees = dm_bev_wine.array[:, :, idx_dm_bev_wine['agr_domestic_production_wine']] \
                                * cdm_cp_ibp_bev_wine.array[idx_cdm_ibp_wine['cp_ibp_bev_wine_brf_fdk_lees']]
    dm_bev_wine.add(agr_ibp_bev_wine_fdk_lees, dim='Variables', col_label='agr_ibp_bev_wine_fdk_lees', unit='kcal')

    # Wine - Crop Grape
    idx_dm_bev_wine = dm_bev_wine.idx
    idx_cdm_ibp_wine = cdm_cp_ibp_bev_wine.idx
    agr_ibp_bev_wine_crop_grape = dm_bev_wine.array[:, :, idx_dm_bev_wine['agr_domestic_production_wine']] \
                                  * cdm_cp_ibp_bev_wine.array[idx_cdm_ibp_wine['cp_ibp_bev_wine_brf_crop_grape']]
    dm_bev_wine.add(agr_ibp_bev_wine_crop_grape, dim='Variables', col_label='agr_ibp_bev_wine_crop_grape', unit='kcal')

    # Byproducts for other uses [kcal] = sum (wine byproducts [kcal])
    dm_bev_ibp_use_oth = dm_bev_wine.groupby(
        {'agr_bev_ibp_use_oth': 'agr_ibp_bev_wine_fdk_marc|agr_ibp_bev_wine_fdk_lees'}, dim='Variables',
        regex=True)

    # Byproducts biomass use per sector = byproducts for other uses * share of bev biomass per sector [%]
    idx_bev_ibp_use_oth = dm_bev_ibp_use_oth.idx
    idx_bev_biomass_hierarchy = DM_alc_bev['biomass_hierarchy'].idx
    agr_bev_ibp_use_oth = dm_bev_ibp_use_oth.array[:, :, idx_bev_ibp_use_oth['agr_bev_ibp_use_oth'], np.newaxis] * \
                          DM_alc_bev['biomass_hierarchy'].array[:, :,
                          idx_bev_biomass_hierarchy['agr_biomass-hierarchy-bev-ibp-use-oth'], :]
    DM_alc_bev['biomass_hierarchy'].add(agr_bev_ibp_use_oth, dim='Variables', col_label='agr_bev_ibp_use_oth',
                                        unit='kcal')

    # Cereal bev byproducts allocated to feed [kcal] = sum (beer byproducts for feedstock [kcal])
    dm_bev_ibp_cereal_feed = dm_bev_beer.groupby(
        {'agr_use_bev_ibp_cereal_feed': 'agr_ibp_bev_beer_fdk_yeast|agr_ibp_bev_beer_fdk_cereal'}, dim='Variables',
        regex=True)

    # (Not used after) Fruits bev allocated to non-food [kcal] = dom prod bev alc + dom prod bev wine + bev byproducts for fertilizer

    # (Not used after) Cereals bev allocated to non-food [kcal] = dom prod bev beer + dom prod bev fer + bev byproducts for fertilizer
    # change the double count of bev byproducts for fertilizer in fruits/cereals bev allocated to non-food [kcal]

    # (Not used after) Fruits bev allocated to bioenergy [kcal] = bp bev for solid bioenergy (+ bp use for ethanol (not found in knime))
    return DM_alc_bev, dm_bev_ibp_cereal_feed

# CalculationLeaf BIOENERGY CAPACITY ----------------------------------------------------------------------------------
def bioenergy_workflow(DM_bioenergy, cdm_const, dm_ind, dm_bld, dm_tra):

    # Electricity production
    # Bioenergy capacity [TWh] = bioenergy capacity [GW] * load hours per year [h] (accounting for unit change)
    idx_bio_cap_elec = DM_bioenergy['electricity_production'].idx
    idx_const = cdm_const.idx
    dm_bio_cap = DM_bioenergy['electricity_production'].array[:, :, idx_bio_cap_elec['agr_bioenergy-capacity_elec'], :] \
                 * cdm_const.array[idx_const['cp_load_hours-per-year-twh']]
    DM_bioenergy['electricity_production'].add(dm_bio_cap, dim='Variables', col_label='agr_bioenergy-capacity_lfe',
                                               unit='TWh')

    # Electricity production [TWh] = bioenergy capacity [TWh] * load-factors per technology [%]
    DM_bioenergy['electricity_production'].operation('agr_bioenergy-capacity_lfe', '*',
                                                     'agr_bioenergy-capacity_load-factor',
                                                     out_col='agr_bioenergy-capacity_elec-prod', unit='TWh')

    # Feedstock requirements [TWh] = Electricity production [TWh] / Efficiency per technology [%]
    DM_bioenergy['electricity_production'].operation('agr_bioenergy-capacity_elec-prod', '*',
                                                     'agr_bioenergy-capacity_efficiency',
                                                     out_col='agr_bioenergy-capacity_fdk-req', unit='TWh')

    # Filtering input from other modules
    # Industry
    dm_ind_bioenergy = dm_ind.filter_w_regex({'Variables': 'ind_bioenergy'})
    dm_ind_bioenergy.deepen()
    dm_ind_biomaterial = dm_ind.filter_w_regex({'Variables': 'ind_biomaterial'})
    dm_ind_biomaterial.deepen()

    # BIOGAS -----------------------------------------------------------------------------------------------------------
    # Biogas feedstock requirements [TWh] =
    # (transport + bld + industry bioenergy + industry biomaterial) bio gas demand + biogases feedstock requirements
    idx_bld = dm_bld.idx
    idx_ind_bioenergy = dm_ind_bioenergy.idx
    idx_ind_biomaterial = dm_ind_biomaterial.idx
    idx_tra = dm_tra.idx
    idx_elec = DM_bioenergy['electricity_production'].idx

    dm_bio_gas_demand = dm_bld.array[:, :, idx_bld['bld_bioenergy'], idx_bld['gas']] \
                        + dm_ind_bioenergy.array[:, :, idx_ind_bioenergy['ind_bioenergy'], idx_ind_bioenergy['gas-bio']] \
                        + dm_ind_biomaterial.array[:, :, idx_ind_biomaterial['ind_biomaterial'],
                          idx_ind_biomaterial['gas-bio']] \
                        + dm_tra.array[:, :, idx_tra['tra_bioenergy'], idx_tra['gas']] \
                        + DM_bioenergy['electricity_production'].array[:, :, idx_elec['agr_bioenergy-capacity_fdk-req'],
                          idx_elec['biogases']] \
                        + DM_bioenergy['electricity_production'].array[:, :, idx_elec['agr_bioenergy-capacity_fdk-req'],
                          idx_elec['biogases-hf']]

    dm_biogas = dm_ind.filter({'Variables': [
        'ind_bioenergy_gas-bio']})  # FIXME backup I do not know how to create a blanck dm with Country & Years
    dm_biogas.add(dm_bio_gas_demand, dim='Variables', col_label='agr_bioenergy-capacity_biogas-req', unit='TWh')
    dm_biogas.drop(dim='Variables', col_label=['ind_bioenergy_gas-bio'])  # FIXME to empty when upper comment fixed

    # Biogas per type [TWh] = Biogas feedstock requirements [GWh] * biogas technology share [%]
    idx_biogas = dm_biogas.idx
    idx_mix = DM_bioenergy['bgs-mix'].idx
    dm_biogas_mix = dm_biogas.array[:, :, idx_biogas['agr_bioenergy-capacity_biogas-req'], np.newaxis] * \
                    DM_bioenergy['bgs-mix'].array[:, :, idx_mix['agr_bioenergy-capacity_bgs-mix'], :]
    DM_bioenergy['bgs-mix'].add(dm_biogas_mix, dim='Variables', col_label='agr_bioenergy-capacity_bgs-tec', unit='TWh')

    # Digestor feedstock per type [TWh] = biogas demand for digestor [TWh] * biomass share for digestor [%]
    dm_digestor_demand = DM_bioenergy['bgs-mix'].filter({'Variables': ['agr_bioenergy-capacity_bgs-tec'],
                                                         'Categories1': ['digestor']})
    dm_digestor_demand = dm_digestor_demand.flatten()
    idx_demand_digestor = dm_digestor_demand.idx
    idx_mix_digestor = DM_bioenergy['digestor-mix'].idx
    dm_biogas_demand_digestor = dm_digestor_demand.array[:, :,
                                idx_demand_digestor['agr_bioenergy-capacity_bgs-tec_digestor'], np.newaxis] * \
                                DM_bioenergy['digestor-mix'].array[:, :,
                                idx_mix_digestor['agr_biomass-hierarchy_biomass-mix_digestor'], :]
    DM_bioenergy['digestor-mix'].add(dm_biogas_demand_digestor, dim='Variables',
                                     col_label='agr_bioenergy_biomass-demand_biogas', unit='TWh')

    # SOLID BIOFUEL ----------------------------------------------------------------------------------------------------
    # Solid biomass feedstock requirements [TWh] =
    # (bld + industry) solid bioenergy demand + solid biofuel feedstock requirements (hf and not)
    idx_bld = dm_bld.idx
    idx_ind_bioenergy = dm_ind_bioenergy.idx
    idx_elec = DM_bioenergy['electricity_production'].idx

    dm_solid_demand = dm_bld.array[:, :, idx_bld['bld_bioenergy'], idx_bld['solid-pellets']] \
                      + dm_bld.array[:, :, idx_bld['bld_bioenergy'], idx_bld['solid-woodlogs']] \
                      + dm_ind_bioenergy.array[:, :, idx_ind_bioenergy['ind_bioenergy'], idx_ind_bioenergy['solid-bio']] \
                      + DM_bioenergy['electricity_production'].array[:, :, idx_elec['agr_bioenergy-capacity_fdk-req'],
                        idx_elec['solid-biofuel']] \
                      + DM_bioenergy['electricity_production'].array[:, :, idx_elec['agr_bioenergy-capacity_fdk-req'],
                        idx_elec['solid-biofuel-hf']]

    dm_solid = dm_ind.filter({'Variables': [
        'ind_bioenergy_gas-bio']})  # FIXME backup I do not know how to create a blanck dm with Country & Years
    dm_solid.add(dm_solid_demand, dim='Variables', col_label='agr_bioenergy-capacity_solid-biofuel-req', unit='TWh')
    dm_solid.drop(dim='Variables', col_label=['ind_bioenergy_gas-bio'])  # FIXME to empty when upper comment fixed

    # Solid feedstock per type [TWh] = solid demand for  biofuel [TWh] * biomass share solid [%]
    idx_demand_solid = dm_solid.idx
    idx_mix_solid = DM_bioenergy['solid-mix'].idx
    dm_solid_fdk = dm_solid.array[:, :, idx_demand_solid['agr_bioenergy-capacity_solid-biofuel-req'], np.newaxis] * \
                   DM_bioenergy['solid-mix'].array[:, :, idx_mix_solid['agr_biomass-hierarchy_biomass-mix_solid'], :]
    DM_bioenergy['solid-mix'].add(dm_solid_fdk, dim='Variables', col_label='agr_bioenergy_biomass-demand_solid',
                                  unit='TWh')

    # LIQUID BIOFUEL ----------------------------------------------------------------------------------------------------

    # Liquid biofuel per type [TWh] = liquid biofuel capacity [TWh] * share per technology [%]
    # Biodiesel
    dm_biodiesel = DM_bioenergy['liq'].filter({'Categories1': ['biodiesel']})
    dm_biodiesel = dm_biodiesel.flatten()
    idx_biodiesel_cap = dm_biodiesel.idx
    idx_biodiesel_tec = DM_bioenergy['liquid-biodiesel'].idx
    dm_biodiesel_temp = dm_biodiesel.array[:, :, idx_biodiesel_cap['agr_bioenergy-capacity_liq_biodiesel'],
                        np.newaxis] * \
                        DM_bioenergy['liquid-biodiesel'].array[:, :,
                        idx_biodiesel_tec['agr_biomass-hierarchy_bioenergy_liquid_biodiesel'], :]
    DM_bioenergy['liquid-biodiesel'].add(dm_biodiesel_temp, dim='Variables',
                                         col_label='agr_bioenergy-capacity_liq-bio-prod_biodiesel', unit='TWh')

    # Biogasoline
    dm_biogasoline = DM_bioenergy['liq'].filter({'Categories1': ['biogasoline']})
    dm_biogasoline = dm_biogasoline.flatten()
    idx_biogasoline_cap = dm_biogasoline.idx
    idx_biogasoline_tec = DM_bioenergy['liquid-biogasoline'].idx
    dm_biogasoline_temp = dm_biogasoline.array[:, :, idx_biogasoline_cap['agr_bioenergy-capacity_liq_biogasoline'],
                          np.newaxis] * \
                          DM_bioenergy['liquid-biogasoline'].array[:, :,
                          idx_biogasoline_tec['agr_biomass-hierarchy_bioenergy_liquid_biogasoline'], :]
    DM_bioenergy['liquid-biogasoline'].add(dm_biogasoline_temp, dim='Variables',
                                           col_label='agr_bioenergy-capacity_liq-bio-prod_biogasoline', unit='TWh')

    # Biojetkerosene
    dm_biojetkerosene = DM_bioenergy['liq'].filter({'Categories1': ['biojetkerosene']})
    dm_biojetkerosene = dm_biojetkerosene.flatten()
    idx_biojetkerosene_cap = dm_biojetkerosene.idx
    idx_biojetkerosene_tec = DM_bioenergy['liquid-biojetkerosene'].idx
    dm_biojetkerosene_temp = dm_biojetkerosene.array[:, :,
                             idx_biojetkerosene_cap['agr_bioenergy-capacity_liq_biojetkerosene'],
                             np.newaxis] * \
                             DM_bioenergy['liquid-biojetkerosene'].array[:, :,
                             idx_biojetkerosene_tec['agr_biomass-hierarchy_bioenergy_liquid_biojetkerosene'], :]
    DM_bioenergy['liquid-biojetkerosene'].add(dm_biojetkerosene_temp, dim='Variables',
                                              col_label='agr_bioenergy-capacity_liq-bio-prod_biojetkerosene',
                                              unit='TWh')

    # Liquid biofuel feedtsock requirements [kcal] = Liquid biofuel per type [TWh] * share per technology [kcal/TWh]

    # Constant pre-processing
    cdm_biodiesel = cdm_const.filter_w_regex(({'Variables': 'cp_liquid_tec_biodiesel'}))
    cdm_biodiesel.rename_col_regex(str1="_fdk_oil", str2="", dim="Variables")
    cdm_biodiesel.rename_col_regex(str1="_fdk_lgn", str2="", dim="Variables")
    cdm_biodiesel.deepen()
    cdm_biogasoline = cdm_const.filter_w_regex(({'Variables': 'cp_liquid_tec_biogasoline'}))
    cdm_biogasoline.rename_col_regex(str1="_fdk_eth", str2="", dim="Variables")
    cdm_biogasoline.rename_col_regex(str1="_fdk_lgn", str2="", dim="Variables")
    cdm_biogasoline.deepen()
    cdm_biojetkerosene = cdm_const.filter_w_regex(({'Variables': 'cp_liquid_tec_biojetkerosene'}))
    cdm_biojetkerosene.rename_col_regex(str1="_fdk_oil", str2="", dim="Variables")
    cdm_biojetkerosene.rename_col_regex(str1="_fdk_lgn", str2="", dim="Variables")
    cdm_biojetkerosene.deepen()

    # Biodiesel
    idx_cdm = cdm_biodiesel.idx
    idx_bio = DM_bioenergy['liquid-biodiesel'].idx
    dm_calc = DM_bioenergy['liquid-biodiesel'].array[:, :, idx_bio['agr_bioenergy-capacity_liq-bio-prod_biodiesel'], :] \
              * cdm_biodiesel.array[idx_cdm['cp_liquid_tec_biodiesel'], :]
    DM_bioenergy['liquid-biodiesel'].add(dm_calc, dim='Variables',
                                         col_label='agr_bioenergy-capacity_liq-bio-prod_fdk-req_biodiesel',
                                         unit='kcal')

    # Biogasoline
    idx_cdm = cdm_biogasoline.idx
    idx_bio = DM_bioenergy['liquid-biogasoline'].idx
    dm_calc = DM_bioenergy['liquid-biogasoline'].array[:, :, idx_bio['agr_bioenergy-capacity_liq-bio-prod_biogasoline'],
              :] \
              * cdm_biogasoline.array[idx_cdm['cp_liquid_tec_biogasoline'], :]
    DM_bioenergy['liquid-biogasoline'].add(dm_calc, dim='Variables',
                                           col_label='agr_bioenergy-capacity_liq-bio-prod_fdk-req_biogasoline',
                                           unit='kcal')

    # Biojetkerosene
    idx_cdm = cdm_biojetkerosene.idx
    idx_bio = DM_bioenergy['liquid-biojetkerosene'].idx
    dm_calc = DM_bioenergy['liquid-biojetkerosene'].array[:, :,
              idx_bio['agr_bioenergy-capacity_liq-bio-prod_biojetkerosene'], :] \
              * cdm_biojetkerosene.array[idx_cdm['cp_liquid_tec_biojetkerosene'], :]
    DM_bioenergy['liquid-biojetkerosene'].add(dm_calc, dim='Variables',
                                              col_label='agr_bioenergy-capacity_liq-bio-prod_fdk-req_biojetkerosene',
                                              unit='kcal')

    # Total liquid biofuel feedstock req per feedstock type [kcal]
    # = liquid biofuel fdk req per fdk type (biodiesel + biogasoline + biojetkerosene)
    # Feedstock types : lgn => lignin, eth => ethanol, oil

    # Filter the dms
    dm_biofuel_fdk = DM_bioenergy['liquid-biodiesel'].filter(
        {'Variables': ['agr_bioenergy-capacity_liq-bio-prod_fdk-req_biodiesel']})
    dm_biogasoline = DM_bioenergy['liquid-biogasoline'].filter(
        {'Variables': ['agr_bioenergy-capacity_liq-bio-prod_fdk-req_biogasoline']})
    dm_biojetkerosene = DM_bioenergy['liquid-biojetkerosene'].filter(
        {'Variables': ['agr_bioenergy-capacity_liq-bio-prod_fdk-req_biojetkerosene']})
    # Flatten
    dm_biofuel_fdk = dm_biofuel_fdk.flatten()
    dm_biogasoline = dm_biogasoline.flatten()
    dm_biojetkerosene = dm_biojetkerosene.flatten()
    # Append the dms together
    dm_biofuel_fdk.append(dm_biogasoline, dim='Variables')
    dm_biofuel_fdk.append(dm_biojetkerosene, dim='Variables')
    # Create dms for each feedstock (eth, lgn & oil)
    # dm_eth = cdm_const.filter_w_regex(({'Variables': 'eth'}))

    # Sum using group by for each feedstock (fer => eth, btl & ezm => lgn, hvo & est =>oil)
    dm_biofuel_fdk.groupby({'agr_bioenergy_biomass-demand_liquid_eth': '.*_fer'}, dim='Variables', regex=True,
                           inplace=True)
    dm_biofuel_fdk.groupby({'agr_bioenergy_biomass-demand_liquid_lgn': '.*_btl|.*_ezm'}, dim='Variables', regex=True,
                           inplace=True)
    dm_biofuel_fdk.groupby({'agr_bioenergy_biomass-demand_liquid_oil': '.*_hvo|.*_est'}, dim='Variables', regex=True,
                           inplace=True)

    # Liquid biofuel demand per type [kcal] = Total liquid biofuel feedstock req per fdk type [kcal]
    # * biomass hierarchy per type [%]

    # Filtering liquid-mix per fdk type
    dm_eth = DM_bioenergy['liquid-mix'].filter_w_regex(({'Categories1': 'eth'}))
    dm_lgn = DM_bioenergy['liquid-mix'].filter_w_regex(({'Categories1': 'lgn'}))
    dm_oil = DM_bioenergy['liquid-mix'].filter_w_regex(({'Categories1': 'oil'}))

    # computation for each fdk type using a tree split method
    # eth
    idx_eth_mix = dm_eth.idx
    idx_eth_demand = dm_biofuel_fdk.idx
    dm_temp = dm_biofuel_fdk.array[:, :, idx_eth_demand['agr_bioenergy_biomass-demand_liquid_eth'], np.newaxis] * \
              dm_eth.array[:, :, idx_eth_mix['agr_biomass-hierarchy_biomass-mix_liquid'], :]
    dm_eth.add(dm_temp, dim='Variables', col_label='agr_bioenergy_biomass-demand_liquid_eth',
               unit='kcal')

    # lgn
    idx_lgn_mix = dm_lgn.idx
    idx_lgn_demand = dm_biofuel_fdk.idx
    dm_temp = dm_biofuel_fdk.array[:, :, idx_lgn_demand['agr_bioenergy_biomass-demand_liquid_lgn'], np.newaxis] * \
              dm_lgn.array[:, :, idx_lgn_mix['agr_biomass-hierarchy_biomass-mix_liquid'], :]
    dm_lgn.add(dm_temp, dim='Variables', col_label='agr_bioenergy_biomass-demand_liquid_lgn',
               unit='kcal')

    # oil
    idx_oil_mix = dm_oil.idx
    idx_oil_demand = dm_biofuel_fdk.idx
    dm_temp = dm_biofuel_fdk.array[:, :, idx_oil_demand['agr_bioenergy_biomass-demand_liquid_oil'], np.newaxis] * \
              dm_oil.array[:, :, idx_oil_mix['agr_biomass-hierarchy_biomass-mix_liquid'], :]
    dm_oil.add(dm_temp, dim='Variables', col_label='agr_bioenergy_biomass-demand_liquid_oil',
               unit='kcal')

    # Cellulosic liquid biofuel per type [kcal] : In KNIME but not computed as not used later
    return DM_bioenergy

# CalculationLeaf LIVESTOCK MANURE MANAGEMENT & GHG EMISSIONS ----------------------------------------------------------
def livestock_manure_workflow(DM_manure, DM_livestock, cdm_const):

    # Pre processing livestock population
    dm_liv_pop = DM_livestock['caf_liv_population'].filter({'Variables': ['cal_agr_liv_population']})
    DM_manure['liv_n-stock'].append(dm_liv_pop, dim='Variables')
    DM_manure['enteric_emission'].append(dm_liv_pop, dim='Variables')
    DM_manure['ef_liv_CH4_treated'].append(dm_liv_pop, dim='Variables')

    # N2O
    # Manure production [tN] = livestock population [lsu] * Manure yield [t/lsu]
    DM_manure['liv_n-stock'].operation('fxa_liv_manure_n-stock', '*', 'cal_agr_liv_population',
                                       out_col='agr_liv_n-stock', unit='t')

    # Manure management practices [MtN] = Manure production [MtN] * Share of management practices [%]
    idx_nstock = DM_manure['liv_n-stock'].idx
    idx_split = DM_manure['manure'].idx
    dm_temp = DM_manure['liv_n-stock'].array[:, :, idx_nstock['agr_liv_n-stock'], :, np.newaxis] * \
              DM_manure['manure'].array[:, :, idx_split['agr_climate-smart-livestock_manure'], :, :]
    DM_manure['ef_liv_N2O'].add(dm_temp, dim='Variables', col_label='agr_liv_n-stock_split',
                                unit='t')

    # Manure emission [MtN2O] = Manure management practices [MtN] * emission factors per practices [MtN2O/Mt]
    DM_manure['ef_liv_N2O'].operation('agr_liv_n-stock_split', '*', 'fxa_ef_liv_N2O-emission_ef',
                                      out_col='agr_liv_N2O-emission', unit='t')

    # Calibration N2O
    dm_liv_N2O = DM_manure['ef_liv_N2O'].filter({'Variables': ['agr_liv_N2O-emission']})
    DM_manure['caf_liv_N2O'].append(dm_liv_N2O, dim='Variables')  # Append to caf
    DM_manure['caf_liv_N2O'].operation('caf_agr_liv_N2O-emission', '*', 'agr_liv_N2O-emission',
                                       dim="Variables", out_col='cal_agr_liv_N2O-emission', unit='t')

    # CH4
    # Enteric emission [tCH4] = livestock population [lsu] * enteric emission factor [tCH4/lsu]
    DM_manure['enteric_emission'].operation('agr_climate-smart-livestock_enteric', '*', 'cal_agr_liv_population',
                                            dim="Variables", out_col='agr_liv_CH4-emission', unit='t')

    # Manure emission [tCH4] = livestock population [lsu] * emission factors treated manure [tCH4/lsu]
    DM_manure['ef_liv_CH4_treated'].operation('fxa_ef_liv_CH4-emission_treated', '*', 'cal_agr_liv_population',
                                              dim="Variables", out_col='agr_liv_CH4-emission', unit='t')

    # Processing for calibration (putting enteric and treated CH4 emission in the same dm)
    # Treated
    dm_CH4 = DM_manure['ef_liv_CH4_treated'].filter({'Variables': ['agr_liv_CH4-emission']})
    dm_CH4.rename_col_regex(str1="meat", str2="treated_meat", dim="Categories1")
    dm_CH4.rename_col_regex(str1="abp", str2="treated_abp", dim="Categories1")
    dm_CH4.deepen()
    dm_CH4.switch_categories_order(cat1='Categories2', cat2='Categories1')
    # Enteric
    dm_CH4_enteric = DM_manure['enteric_emission'].filter({'Variables': ['agr_liv_CH4-emission']})
    dm_CH4_enteric.rename_col_regex(str1="meat", str2="enteric_meat", dim="Categories1")
    dm_CH4_enteric.rename_col_regex(str1="abp", str2="enteric_abp", dim="Categories1")
    dm_CH4_enteric.deepen()
    dm_CH4_enteric.switch_categories_order(cat1='Categories2', cat2='Categories1')
    # Appending
    dm_CH4.append(dm_CH4_enteric, dim='Categories2')

    # Calibration CH4
    DM_manure['caf_liv_CH4'].append(dm_CH4, dim='Variables')  # Append to caf
    DM_manure['caf_liv_CH4'].operation('caf_agr_liv_CH4-emission', '*', 'agr_liv_CH4-emission',
                                       dim="Variables", out_col='cal_agr_liv_CH4-emission', unit='t')
    return DM_manure

# ----------------------------------------------------------------------------------------------------------------------
# AGRICULTURE ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
def agriculture(lever_setting, years_setting):


    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    agriculture_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/agriculture.pickle')
    DM_ots_fts, DM_food_demand, DM_livestock, DM_alc_bev, DM_bioenergy, DM_manure, cdm_const = read_data(agriculture_data_file, lever_setting)

    # Simulate data from other modules
    dm_lfs = simulate_lifestyles_to_agriculture_input()
    dm_bld = simulate_buildings_to_agriculture_input()
    dm_ind = simulate_industry_to_agriculture_input()
    dm_tra = simulate_transport_to_agriculture_input()

    # Filter by country
    cntr_list = DM_food_demand['food-net-import-pro'].col_labels['Country']
    dm_lfs = dm_lfs.filter({'Country': cntr_list})
    dm_bld = dm_bld.filter({'Country': cntr_list})
    dm_ind = dm_ind.filter({'Country': cntr_list})
    dm_tra = dm_tra.filter({'Country': cntr_list})

    # CalculationTree

    dm_lfs, dm_lfs_pro = food_demand_workflow(DM_food_demand, dm_lfs)
    DM_livestock, dm_liv_ibp, dm_liv_ibp= livestock_workflow(DM_livestock, cdm_const, dm_lfs_pro)
    DM_alc_bev, dm_bev_ibp_cereal_feed = alcoholic_beverages_workflow(DM_alc_bev, cdm_const, dm_lfs_pro)
    DM_bioenergy = bioenergy_workflow(DM_bioenergy, cdm_const, dm_ind, dm_bld, dm_tra)
    DM_manure = livestock_manure_workflow(DM_manure, DM_livestock, cdm_const)



    print('hello')
    return


def agriculture_local_run():
    years_setting, lever_setting = init_years_lever()
    agriculture(lever_setting, years_setting)
    return

# Creates the pickle, to do only once
#database_from_csv_to_datamatrix()

# Run the code in local
agriculture_local_run()
