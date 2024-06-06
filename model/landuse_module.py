#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 15:11:12 2024

@author: echiarot
"""

import pandas as pd

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, edit_database
from model.common.interface_class import Interface
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale, read_database_to_ots_fts_dict_w_groups
from model.common.auxiliary_functions import read_level_data, simulate_input
from scipy.optimize import linprog
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
    years_setting = [1990, 2015, 2050, 5]
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) # make list with years from 1990 to 2015
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int)) # make list with years from 2020 to 2050 (steps of 5 years)
    years_all = years_ots + years_fts

    #############################
    ##### FIXED ASSUMPTIONS #####
    #############################
    
    dict_fxa = {}
    file = 'agriculture_fixed-assumptions_pathwaycalc_non_nan'
    
    # LAND USE --------------------------------------------------------------------------------------------------------
    # LAND ALLOCATION - Total area
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'lus_land_total-area'})
    dm_land_total = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['lus_land_total-area'] = dm_land_total
    # CARBON STOCK - c-stock biomass & soil
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'land-man_ef'})
    dm_ef_biomass = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['land-man_ef'] = dm_ef_biomass
    # CARBON STOCK - soil type
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'land-man_soil-type'})
    dm_soil = DataMatrix.create_from_df(df, num_cat=0)
    dict_fxa['land-man_soil-type'] = dm_soil
    # AGROFORESTRY CROP - emission factors
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'agr_climate-smart-crop_ef_agroforestry'})
    dm_crop_ef_agroforestry = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['agr_climate-smart-crop_ef_agroforestry'] = dm_crop_ef_agroforestry
    # AGROFORESTRY livestock - emission factors
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'agr_climate-smart-livestock_ef_agroforestry'})
    dm_livestock_ef_agroforestry = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['agr_climate-smart-livestock_ef_agroforestry'] = dm_livestock_ef_agroforestry
    # AGROFORESTRY Forestry - natural losses & others
    df = read_database_fxa(file, filter_dict={'eucalc-name': 'agr_climate-smart-forestry'})
    dm_agroforestry = DataMatrix.create_from_df(df, num_cat=1)
    dict_fxa['agr_climate-smart-forestry'] = dm_agroforestry

    ##################
    ##### LEVERS #####
    ##################

    dict_ots = {}
    dict_fts = {}
    
    # Read land management
    file = 'agriculture_land-management_pathwaycalc'
    lever = 'land-man'
    # edit_database(file,lever,column='eucalc-name',pattern={'_rem_':'_', '_to_':'_'},mode='rename')
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 1, 1, 1],
                                                                baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name',
                                                                group_list=['agr_land-man_use.*',
                                                                            'agr_land-man_dyn.*',
                                                                            'agr_land-man_gap.*',
                                                                            'agr_land-man_matrix.*'])
    

    #######################
    ##### CALIBRATION #####
    #######################

    # # Read calibration
    # df = read_database_fxa('industry_calibration')
    # dm_cal = DataMatrix.create_from_df(df, num_cat=0)

    #####################
    ##### CONSTANTS #####
    #####################
    
    # get constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants_pathwaycalc',
                                                    pattern='cp_ibp_liv_.*_brf_fdk_afat|cp_ibp_liv_.*_brf_fdk_offal|cp_ibp_bev_.*|cp_liquid_tec.*|cp_load_hours|cp_ibp_aps_insect.*|cp_ibp_aps_algae.*|cp_efficiency_liv.*|cp_ibp_processed.*|cp_ef_urea.*|cp_ef_liming|cp_emission-factor_CO2.*|cp_fst_ef_emissions-CH4_burnt|cp_fst_ef_emissions-CO2_burnt|cp_fst_ef_emissions-N2O_burnt',
                                                    num_cat=0)


    ################
    ##### SAVE #####
    ################

    DM_landuse = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        # 'calibration': dm_cal,
        "constant" : cdm_const
    }


    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/landuse.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_landuse, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # clean
        
    return

def read_data(data_file, lever_setting):
    
    with open(data_file, 'rb') as handle:
        DM_landuse = pickle.load(handle)

    # Read fts based on lever_setting
    DM_ots_fts = read_level_data(DM_landuse, lever_setting)

    # Sub-matrix for LAND USE - Land allocation
    dm_land_man_use = DM_ots_fts['land-man']['agr_land-man_use']
    dm_land_total = DM_landuse['fxa']['lus_land_total-area']
    dm_land_man_dyn = DM_ots_fts['land-man']['agr_land-man_dyn']

    # Sub-matrix for LAND USE - Land matrix
    dm_land_man_gap = DM_ots_fts['land-man']['agr_land-man_gap']
    dm_land_man_matrix = DM_ots_fts['land-man']['agr_land-man_matrix']
    dm_land_man_matrix.rename_col_regex(str1="agr_land-man_matrix", str2="agr_matrix", dim="Variables")
    #dm_land_man_matrix = dm_land_man_matrix.flatten()
    dm_land_man_matrix.deepen(based_on='Variables')

    # Sub-matrix for LAND USE - Carbon dynamics
    dm_c_stock = DM_landuse['fxa']['land-man_ef']
    dm_c_stock.rename_col_regex(str1="c-stock_", str2="", dim="Variables")
    dm_c_stock.rename_col_regex(str1="ef_", str2="ef_c-stock_", dim="Variables")
    dm_c_stock.rename_col_regex(str1="soil_", str2="soil-", dim="Variables")
    dm_c_stock.rename_col_regex(str1="biomass_", str2="biomass-", dim="Variables")
    dm_c_stock.deepen(based_on='Variables')
    dm_c_stock.deepen(based_on='Variables')
    dm_c_stock.deepen(based_on='Variables')
    dm_soil_type = DM_landuse['fxa']['land-man_soil-type']
    dm_soil_type.deepen(based_on='Variables')
    dm_soil_type.deepen(based_on='Variables')

    # Sub-matrix for LAND USE - Agroforestry
    dm_agroforestry_crop = DM_landuse['fxa']['agr_climate-smart-crop_ef_agroforestry']
    dm_agroforestry_liv = DM_landuse['fxa']['agr_climate-smart-livestock_ef_agroforestry']
    dm_forestry = DM_landuse['fxa']['agr_climate-smart-forestry']

    # Aggregated Data Matrix - LAND USE
    DM_land_use = {
        'land_man_use': dm_land_man_use,
        'land_total': dm_land_total,
        'land_man_dyn': dm_land_man_dyn,
        'land_man_gap': dm_land_man_gap,
        'land_matrix': dm_land_man_matrix,
        'land_c-stock' : dm_c_stock,
        'land_soil-type' : dm_soil_type,
        'crop_ef_agroforestry': dm_agroforestry_crop,
        'liv_ef_agroforestry': dm_agroforestry_liv,
        'forestry': dm_forestry
    }

    cdm_const = DM_land_use['constant']
    
    # return
    return DM_ots_fts, DM_land_use, cdm_const

# CalculationLeaf WOOD
def wood_workflow(DM_bioenergy, dm_lgn, dm_ind):
    # WOOD FUEL DEMAND  ------------------------------------------------------------------------------------------------
    # Unit conversion : bioenergy biomass demand [kcal] => [TWh]
    dm_lgn.add(0.00000000000116222, dummy=True, col_label='kcal_to_TWh', dim='Variables', unit='TWh')
    dm_lgn.operation('agr_bioenergy_biomass-demand_liquid_lgn', '*', 'kcal_to_TWh',
                      out_col='agr_bioenergy_biomass-demand_liquid_lgn_TWh', unit='TWh')

    # Pre processing
    dm_wood = DM_bioenergy['solid-mix'].filter({'Variables': ['agr_bioenergy_biomass-demand_solid'],
                                                'Categories1': ['fuelwood-and-res']})

    dm_wood_liquid = dm_lgn.filter({'Variables': ['agr_bioenergy_biomass-demand_liquid_lgn_TWh'],
                                    'Categories1': ['lgn-btl-fuelwood-and-res']})
    dm_wood_liquid.rename_col('lgn-btl-fuelwood-and-res', 'fuelwood-and-res', dim='Categories1')
    dm_wood.append(dm_wood_liquid, dim='Variables')

    # Wood-fuel demand [TWh] = sum bioenergy demand  for fuelwood (solid & liquid biomass) FIXME only solid in KNIME calculation
    dm_wood.operation('agr_bioenergy_biomass-demand_solid', '+', 'agr_bioenergy_biomass-demand_liquid_lgn_TWh',
                      out_col='lus_fst_demand_rwe_wood-fuel', unit='TWh')

    # Processing
    dm_wood = dm_wood.filter({'Variables': ['lus_fst_demand_rwe_wood-fuel']})
    dm_wood = dm_wood.flatten()
    dm_wood.rename_col('lus_fst_demand_rwe_wood-fuel_fuelwood-and-res', 'lus_fst_demand_rwe_wood-fuel_temp',
                       dim='Variables')

    # Unit conversion : Wood-fuel demand [TWh] => [m3]
    dm_wood.add(174420.0, dummy=True, col_label='TWh_to_cubic_m', dim='Variables', unit='m3')
    dm_wood.operation('lus_fst_demand_rwe_wood-fuel_temp', '*', 'TWh_to_cubic_m',
                      out_col='lus_fst_demand_rwe_wood-fuel', unit='m3')
    dm_wood = dm_wood.filter({'Variables': ['lus_fst_demand_rwe_wood-fuel']})

    # WOOD PRODUCT CONVERSION ------------------------------------------------------------------------------------------
    # Timber, Woodpulp & Biomaterial from Industry module : Unit conversion to m3 and renaming
    # Timber
    dm_timber = dm_ind.filter({'Variables': ['ind_timber']})
    dm_timber.rename_col('ind_timber', 'lus_fst_demand_rwe_ind-sawlog_temp', dim='Variables')
    dm_timber.add(1500.0, dummy=True, col_label='kt_to_cubic_m', dim='Variables', unit='m3')
    dm_timber.operation('lus_fst_demand_rwe_ind-sawlog_temp', '*', 'kt_to_cubic_m',
                        out_col='lus_fst_demand_rwe_ind-sawlog', unit='m3')
    dm_timber = dm_timber.filter({'Variables': ['lus_fst_demand_rwe_ind-sawlog']})

    # Woodpulp
    dm_woodpulp = dm_ind.filter({'Variables': ['ind_material-production_paper_woodpulp']})
    dm_woodpulp.rename_col('ind_material-production_paper_woodpulp', 'lus_fst_demand_rwe_pulp_temp', dim='Variables')
    dm_woodpulp.add(4500000.0, dummy=True, col_label='Mt_to_cubic_m', dim='Variables', unit='m3')
    dm_woodpulp.operation('lus_fst_demand_rwe_pulp_temp', '*', 'Mt_to_cubic_m',
                          out_col='lus_fst_demand_rwe_pulp', unit='m3')
    dm_woodpulp = dm_woodpulp.filter({'Variables': ['lus_fst_demand_rwe_pulp']})

    # Biomaterial
    dm_biomaterial = dm_ind.filter({'Variables': ['ind_biomaterial_solid-bio']})
    dm_biomaterial.rename_col('ind_biomaterial_solid-bio', 'lus_fst_demand_rwe_oth-ind-wood_temp', dim='Variables')
    dm_biomaterial.add(174420.0, dummy=True, col_label='TWh_to_cubic_m', dim='Variables', unit='m3')
    dm_biomaterial.operation('lus_fst_demand_rwe_oth-ind-wood_temp', '*', 'TWh_to_cubic_m',
                             out_col='lus_fst_demand_rwe_oth-ind-wood', unit='m3')
    dm_biomaterial = dm_biomaterial.filter({'Variables': ['lus_fst_demand_rwe_oth-ind-wood']})

    # Appending to dm_wood & deepen
    dm_wood.append(dm_timber, dim='Variables')
    dm_wood.append(dm_woodpulp, dim='Variables')
    dm_wood.append(dm_biomaterial, dim='Variables')
    dm_wood.deepen()

    # Total wood demand [m3] = Wood-fuel demand + Timber + Woodpulp + Wood for other uses
    dm_wood.groupby({'total': '.*'}, dim='Categories1', regex=True, inplace=True)

    # Calibration Wood demand

    return dm_wood

def land_allocation_workflow(DM_land_use, dm_land_use):
    # CalculationLeaf LAND ALLOCATION

    # TOTAL LAND DYNAMICS ----------------------------------------------------------------------------------------------
    # Appending cropland and grassland to DM_land_use FIXME use calibrated land
    dm_land_use = dm_land_use.filter({'Variables': ['agr_lus_land']})
    dm_land_use.rename_col('agr_lus_land', 'agr_land-man_use', dim='Variables')
    DM_land_use['land_man_use'].append(dm_land_use, dim='Categories1')
    DM_land_use['land_man_use'].sort(dim='Categories1')

    # Creating a copy for land demand
    dm_land_demand = DM_land_use['land_man_use'].copy()

    # Land demand [ha] = cropland + grassland + forest + other + settlement + wetland
    dm_land_demand.groupby({'total-land': '.*'}, dim='Categories1', regex=True, inplace=True)
    dm_land_demand.rename_col('agr_land-man_use', 'lus_demand', dim='Variables')
    dm_land_demand = dm_land_demand.flatten()

    # Land dynamics [ha] = total land - land demand
    DM_land_use['land_total'].append(dm_land_demand, dim='Variables')
    DM_land_use['land_total'].operation('lus_land_total-area', '-', 'lus_demand_total-land',
                                        out_col='lus_land_dynamics', unit='ha')

    # ALLOCATION OF AVAILABLE LAND -------------------------------------------------------------------------------------

    # Filtering available and deforested land (If there is not enough land available, we assume deforestation)
    # Available land [ha] = Land dynamics [ha] >= 0
    dm_temp = DM_land_use['land_total'].filter({'Variables': ['lus_land_dynamics']})
    array_land_dynamics = dm_temp.array[:, :, :]
    array_available_land = np.maximum(array_land_dynamics, 0)
    DM_land_use['land_total'].add(array_available_land, dim='Variables', col_label='lus_dyn_available-land', unit='ha')

    # Deforestation land [ha] = Land dynamics [ha] < 0
    dm_temp = DM_land_use['land_total'].filter({'Variables': ['lus_land_dynamics']})
    array_land_dynamics = dm_temp.array[:, :, :]
    array_deforestation = -np.maximum(-array_land_dynamics, 0)
    DM_land_use['land_total'].add(array_deforestation, dim='Variables', col_label='lus_dyn_deforestation', unit='ha')

    # Land allocation [ha] = land available [ha] * Land management (grassland, forest, unmanaged) [%]
    idx_dyn = DM_land_use['land_man_dyn'].idx
    idx_land = DM_land_use['land_total'].idx
    array_temp = DM_land_use['land_man_dyn'].array[:, :, idx_dyn['agr_land-man_dyn'], :] \
                 * DM_land_use['land_total'].array[:, :, idx_land['lus_dyn_available-land'], np.newaxis]
    DM_land_use['land_man_dyn'].add(array_temp, dim='Variables', col_label='lus_dyn', unit='ha')

    # LAND DYNAMICS ACCOUNTING FOR ALLOCATED AVAILABLE LAND ------------------------------------------------------------

    # Pre processing land use dynamics
    DM_land_use['land_man_dyn'].rename_col('unmanaged', 'cropland',
                                           dim='Categories1')  # (approximation because unmanaged land has negative impacts)
    DM_land_use['land_man_dyn'].add(0.0, dummy=True, col_label='settlement', dim='Categories1', unit='ha')
    DM_land_use['land_man_dyn'].add(0.0, dummy=True, col_label='wetland', dim='Categories1', unit='ha')
    DM_land_use['land_man_dyn'].add(0.0, dummy=True, col_label='other', dim='Categories1', unit='ha')
    DM_land_use['land_man_dyn'].sort(dim='Categories1')

    # Pre processing deforestation
    dm_deforestation_temp = DM_land_use['land_total'].filter({'Variables': ['lus_dyn_deforestation']})
    dm_deforestation_temp.rename_col('lus_dyn_deforestation', 'lus_dyn_deforestation_forest', dim='Variables')
    dm_deforestation_temp.deepen()
    dm_deforestation_temp.add(0.0, dummy=True, col_label='cropland', dim='Categories1', unit='ha')
    dm_deforestation_temp.add(0.0, dummy=True, col_label='grassland', dim='Categories1', unit='ha')
    dm_deforestation_temp.add(0.0, dummy=True, col_label='settlement', dim='Categories1', unit='ha')
    dm_deforestation_temp.add(0.0, dummy=True, col_label='wetland', dim='Categories1', unit='ha')
    dm_deforestation_temp.add(0.0, dummy=True, col_label='other', dim='Categories1', unit='ha')
    dm_deforestation_temp.sort(dim='Categories1')

    # Appending dms
    DM_land_use['land_man_use'].append(dm_deforestation_temp, dim='Variables')
    DM_land_use['land_man_use'].append(DM_land_use['land_man_dyn'].filter({'Variables': ['lus_dyn']}), dim='Variables')

    # Performing operation
    # Cropland demand [ha] = cropland demand for agriculture + unmanaged land (approximation because unmanaged land has negative impacts)
    # Grassland demand [ha] = grassland demand for agriculture + land allocated to grassland
    # Forest demand [ha] = current land use forest + land allocated to forest - deforested land
    DM_land_use['land_man_use'].operation('agr_land-man_use', '+', 'lus_dyn_deforestation', out_col='lus_land_temp',
                                          unit='ha')
    DM_land_use['land_man_use'].operation('lus_land_temp', '+', 'lus_dyn', out_col='lus_land',
                                          unit='ha')
    DM_land_use['land_man_use'].drop(dim='Variables', col_label=['lus_land_temp'])

    #dm_temp = DM_land_use['land_man_use'].filter({'Variables': ['lus_land']})
    #dm_temp = DM_land_use['land_man_use'].copy()
    #df_temp = dm_temp.write_df()
    #print(df_temp.head(50))

    return DM_land_use

# CalculationLeaf LAND USE MATRIX
def land_matrix_workflow(DM_land_use):

    # LAND USE INITIAL AREA --------------------------------------------------------------------------------------------

    # Land initial area per land type [ha] = lus_land from previous year
    dm_temp = DM_land_use['land_man_use'].filter({'Variables': ['lus_land']})
    array_temp = dm_temp.array
    array_initial_area = np.zeros_like(array_temp)
    array_initial_area[1:] = array_temp[:-1]
    DM_land_use['land_man_gap'].add(array_temp, dim='Variables', col_label='lus_land_initial-area', unit='ha')

    # Land initial area UNFCCC [ha] = land initial area per land type [ha] + land gap per land type [ha]
    # Fills the gap between FAO and UNFCCC data
    DM_land_use['land_man_gap'].operation('lus_land_initial-area', '+', 'agr_land-man_gap',
                                          out_col='lus_land_initial-area_unfccc', unit='ha')

    # LAND TO-CROP & LAND EXCESS ---------------------------------------------------------------------------------------
    # Appending dm
    dm_temp = DM_land_use['land_man_use'].filter({'Variables': ['lus_land']})
    DM_land_use['land_man_gap'].append(dm_temp, dim='Variables')

    # Land difference [ha] = Land demand - Land initial area UNFCCC [ha]
    # For: other, settlement, wetland, cropland, grassland, forest
    DM_land_use['land_man_gap'].operation('lus_land', '-', 'lus_land_initial-area_unfccc',
                                          out_col='lus_land_diff', unit='ha')

    # Sum (Land difference [ha])
    dm_land_total = DM_land_use['land_man_gap'].groupby({'total': '.*'}, dim='Categories1', regex=True, inplace=False)
    DM_land_use['land_man_gap'].append(dm_land_total, dim='Categories1')

    # Assigning Sum (Land difference [ha]) to forests (by default) to have a land change sum of 0
    dm_temp = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land_diff']})
    dm_temp.operation('forest', '-', 'total',
                      dim="Categories1", out_col='forest_new', unit='ha')

    # Clean the dm to only keep the correct Categories, rename and append to relevant dm
    dm_temp.drop(dim='Categories1', col_label=['forest', 'total'])
    dm_temp.rename_col('forest_new', 'forest', dim='Categories1')
    dm_temp.rename_col('lus_land_diff', 'lus_land_diff_adjusted', dim='Variables')
    DM_land_use['land_man_gap'].drop(dim='Categories1', col_label=['total'])
    DM_land_use['land_man_gap'].append(dm_temp, dim='Variables')

    # Filtering between land to crop from other lands (diff>0) and excess land available for other land type (diff<0)
    # Land to-crop [ha] = Land difference [ha] >= 0
    dm_temp = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land_diff_adjusted']})
    array_temp = dm_temp.array[:, :, :, :]
    array_land_to_crop = np.maximum(array_temp, 0)
    DM_land_use['land_man_gap'].add(array_land_to_crop, dim='Variables', col_label='lus_land_to-crop', unit='ha')

    # Land excess [ha] = Land difference [ha] < 0 (& changing the sign)
    dm_temp = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land_diff_adjusted']})
    array_temp = dm_temp.array[:, :, :, :]
    array_land_excess = np.maximum(-array_temp, 0)
    DM_land_use['land_man_gap'].add(array_land_excess, dim='Variables', col_label='lus_land_excess', unit='ha')

    # LAND USE CHANGE MATRIX -------------------------------------------------------------------------------------------

    # Creating a blank land use matrix (cat1 = TO, cat2 = FROM) (per year & per country)
    # cat1 = cat2 : cropland, grassland, forest, settlement, wetland, other, total
    # Creating a NaN array of dimension [32, 33, 1, 6, 6]
    array_temp = np.full((32, 33, 1, 6, 6), np.nan)
    # Adding it to the dm with the relevant structure
    DM_land_use['land_matrix'].add(array_temp, dim='Variables', col_label='matrix', unit='ha')
    # Dropping the unuesed variables (we only take the dm for its structure)
    DM_land_use['land_matrix'].drop(dim='Variables', col_label=['agr_matrix'])

    # Adding dummy categories 1 'total_to-crop' & categories 2 'total_excess'
    # Add a new cat1 = 'total_to-crop' with the land to crop (land type to "create")
    dm_land_to_crop = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land_to-crop']})

    # Add a new cat2 = 'total_excess' with the land excess (land type to "change")
    dm_land_excess = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land_excess']})

    # Solve the values of the matrix so that the sum of the rows/columns are equal to 'total_to-crop/excess'

    # Defining arrays to solve
    dm_matrix = DM_land_use['land_matrix'].filter({'Variables': ['matrix']})
    arr_to_solve = dm_matrix.array
    arr_to_crop = dm_land_to_crop.array
    arr_excess = dm_land_excess.array

    # Number of variables (elements in arr_tol_solve, for 1 Country, Year & Variable at the time)
    n_vars = arr_to_solve[0, 0, 0, :, :].size

    # Coefficients matrix for the linear system
    # We need 12 equations: 6 for rows and 6 for columns
    A_eq = np.zeros((12, n_vars))

    # Row constraints
    for i in range(6):
        A_eq[i, i * 6:(i + 1) * 6] = 1

    # Column constraints
    for j in range(6):
        A_eq[6 + j, j::6] = 1

    # Since we are dealing with a linear system without a specific objective function, we can use linprog with zero cost function
    c = np.zeros(n_vars)

    # Loop over the first three dimensions and solve the linear system for each 6x6 sub-matrix
    for i in range(arr_to_crop.shape[0]):
        for j in range(arr_to_crop.shape[1]):
            for k in range(arr_to_crop.shape[2]):
                # Right-hand side for the current sub-matrix
                b_eq = np.concatenate((arr_to_crop[i, j, k, :], arr_excess[i, j, k, :]))

                # Solve the system using linprog
                res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')

                # Check if the solver found a solution
                if res.success:
                    arr_to_solve[i, j, k, :, :] = res.x.reshape(6, 6)
                else:
                    print(f"No solution found for sub-matrix at index ({i}, {j}, {k})")

    # Adding the array to relevant dm
    DM_land_use['land_matrix'].add(arr_to_solve, col_label='land_use_change_without_rem', dim='Variables')

    # (Check that net change = 0 ?)

    # LAND USE CHANGE MATRIX - INCLUDING LAND REMAINING LAND -----------------------------------------------------------

    # Land use remaining same land use [ha] = (if land diff > 0) land initial area [ha] FIXME check logic with Gino
    #                                       = (else if land diff > 0) land demand [ha]
    # In other terms : (if land demand > initial area) = land initial area [ha]
    #                  (else if land demand < initial area) = land demand [ha]

    variable_names = ['lus_land', 'lus_land_initial-area_unfccc']
    dm_temp = DM_land_use['land_man_gap'].filter({'Variables': variable_names})
    index_lus_land = variable_names.index('lus_land')
    index_lus_land_initial_area_unfccc = variable_names.index('lus_land_initial-area_unfccc')
    arr_land = dm_temp.array
    arr_remaining = np.minimum(arr_land[:, :, index_lus_land, :], arr_land[:, :, index_lus_land_initial_area_unfccc, :])
    DM_land_use['land_man_gap'].add(arr_remaining, col_label='land_remaining_land', dim='Variables')

    # Transforming the remaining in land to the relevant format (from 1 cat to 2 cat with values = diagonal and 0 otherwise)
    arr_temp = np.zeros((32, 33, 6, 6))
    for cat in range(arr_remaining.shape[2]):
        arr_temp[:, :, cat, cat] = arr_remaining[:, :, cat]
    DM_land_use['land_matrix'].add(arr_temp, col_label='land_remaining_land_matrix', dim='Variables')

    # Land use change matrix [ha] = Land remaining land matrix [ha] + land use change matrix without remaining [ha]
    DM_land_use['land_matrix'].operation('land_use_change_without_rem', '+', 'land_remaining_land_matrix',
               dim="Variables", out_col='lus_land_matrix', unit='ha')


    return DM_land_use

# CalculationLeaf CARBON DYNAMICS
def land_carbon_dynamics_workflow(DM_land_use):

    # SOIL CARBON STOCK ------------------------------------------------------------------------------------------------

    # Mineral soil [ha] = Land use matrix [ha] * mineral content per soil type [%]
    dm_land_matrix = DM_land_use['land_matrix'].filter({'Variables': ['lus_land_matrix']})
    DM_land_use['land_soil-type'].append(dm_land_matrix, dim='Variables')
    DM_land_use['land_soil-type'].operation('lus_land_matrix', '*', 'fxa_land-man_soil-type_mineral',
                                            out_col='lus_land_matrix_mineral', unit='ha')

    # Organic soil [ha] = Land use matrix [ha] * organic content per soil type [%]
    DM_land_use['land_soil-type'].operation('lus_land_matrix', '*', 'fxa_land-man_soil-type_organic',
                                            out_col='lus_land_matrix_organic', unit='ha')

    # C stock soil pre processing
    dm_soil_c_stock = DM_land_use['land_c-stock'].filter({'Categories1': ['soil-mineral', 'soil-organic']})
    dm_soil_c_stock = dm_soil_c_stock.flatten()
    dm_soil_c_stock = dm_soil_c_stock.flatten()
    dm_soil_c_stock = dm_soil_c_stock.flatten()
    dm_soil_c_stock.deepen(based_on='Variables')
    dm_soil_c_stock.deepen(based_on='Variables')
    DM_land_use['land_soil-type'].append(dm_soil_c_stock, dim='Variables')

    # Soil mineral carbon stock per land use [tC] = Mineral soil [ha] * Mineral soil emission factor [tC/ha]
    DM_land_use['land_soil-type'].operation('lus_land_matrix_organic', '*', 'fxa_land-man_ef_c-stock_soil-mineral',
                                            out_col='lus_land_c-stock_mineral-soil', unit='tC')

    # Soil organic carbon stock per land use [tC] = Organic soil [ha] * Organic soil emission factor [tC/ha]
    DM_land_use['land_soil-type'].operation('lus_land_matrix_organic', '*', 'fxa_land-man_ef_c-stock_soil-organic',
                                            out_col='lus_land_c-stock_organic-soil', unit='tC')

    # Total soil carbon [tC] = sum soil carbon (mineral, organic)
    DM_land_use['land_soil-type'].operation('lus_land_c-stock_organic-soil', '+', 'lus_land_c-stock_mineral-soil',
                                            out_col='lus_land_c-stock_total-soil', unit='tC')

    # BIOMASS CARBON STOCK ---------------------------------------------------------------------------------------------

    # C stock biomass pre processing
    dm_biomass_c_stock = DM_land_use['land_c-stock'].filter_w_regex(
        {'Categories1': 'biomass-.*', 'Variables': 'fxa_land-man_ef_c-stock'})
    dm_biomass_c_stock = dm_biomass_c_stock.flatten()
    dm_biomass_c_stock = dm_biomass_c_stock.flatten()
    dm_biomass_c_stock = dm_biomass_c_stock.flatten()
    dm_biomass_c_stock.deepen(based_on='Variables')
    dm_biomass_c_stock.deepen(based_on='Variables')
    DM_land_use['land_matrix'].append(dm_biomass_c_stock, dim='Variables')

    # Biomass carbon stock per loss/gain/deadwood land use [tC] =  Biomass carbon stock loss/gain/deadwood [tC/ha] * Land use matrix [ha]
    DM_land_use['land_matrix'].operation('lus_land_matrix', '*', 'fxa_land-man_ef_c-stock_biomass-dead-wood',
                                         out_col='lus_land_c-stock_biomass-dead-wood', unit='tC')
    DM_land_use['land_matrix'].operation('lus_land_matrix', '*', 'fxa_land-man_ef_c-stock_biomass-gain',
                                         out_col='lus_land_c-stock_biomass-gain', unit='tC')
    DM_land_use['land_matrix'].operation('lus_land_matrix', '*', 'fxa_land-man_ef_c-stock_biomass-loss',
                                         out_col='lus_land_c-stock_biomass-loss', unit='tC')

    # Total biomass carbon stock [tC] = sum biomass carbon stock (gain, loss, deadwood)
    DM_land_use['land_matrix'].operation('lus_land_c-stock_biomass-dead-wood', '+', 'lus_land_c-stock_biomass-gain',
                                         out_col='lus_land_c-stock_biomass-dead-wood-and-gain', unit='tC')
    DM_land_use['land_matrix'].operation('lus_land_c-stock_biomass-dead-wood-and-gain', '+',
                                         'lus_land_c-stock_biomass-loss',
                                         out_col='lus_land_c-stock_biomass-total', unit='tC')

    # CARBON STOCK FROM LAND USE CHANGE ---------------------------------------------------------------------------------

    # Carbon stock [tC] = sum (soil + biomass carbon stock)
    DM_land_use['land_matrix'].append(
        DM_land_use['land_soil-type'].filter({'Variables': ['lus_land_c-stock_total-soil']}), dim='Variables')
    DM_land_use['land_matrix'].operation('lus_land_c-stock_total-soil', '+',
                                         'lus_land_c-stock_biomass-total',
                                         out_col='lus_land_lulucf', unit='tC')

    # Total carbon stock from land converted/remaining to XXX [tC] = sum(Carbon stock [tC] from land converted/remaining to XXX)
    # (sum along the rows (cat2) of the sub matrix 6x6 for each country, year)
    dm_total_c_stock = DM_land_use['land_matrix'].filter({'Variables': ['lus_land_lulucf']})
    dm_total_c_stock.groupby({'total': '.*'}, dim='Categories2', regex=True, inplace=True)

    # Processing and adding to DM_land_use['land_man_gap'] because correct categories
    array_temp = dm_total_c_stock.array
    arr_transformed = np.squeeze(array_temp,
                                 axis=-1)  # removing singleton dimension of last axis ('total from groupby')
    DM_land_use['land_man_gap'].add(arr_transformed, col_label='lus_land_lulucf_to_tC', dim='Variables')

    # UNIT CONVERSION FROM tC to tCO2 ----------------------------------------------------------------------------------

    # Add dummy column
    DM_land_use['land_man_gap'].add(-3.667, dummy=True, col_label='tC_to_tCO2', dim='Variables', unit='t')

    # Unit conversion : tC stocked/emitted => tCO2 emitted/stocked
    DM_land_use['land_man_gap'].operation('lus_land_lulucf_to_tC', '*', 'tC_to_tCO2', out_col='lus_land_lulucf_to',
                                          unit='t')
    return DM_land_use

# CalculationLeaf FORESTRY
def forestry_workflow(DM_land_use, dm_wood, dm_land_use):

    # AGROFORESTRY CARBON STOCK ----------------------------------------------------------------------------------------

    # (KNIME : previous step to compute carbon emissions factor cropland/grassland [tC/ha])

    # Pre processing FIXME use calibrated land
    dm_crop_land_agr = dm_land_use.filter({'Variables': ['agr_lus_land'], 'Categories1': ['cropland']})
    dm_grass_land_agr = dm_land_use.filter({'Variables': ['agr_lus_land'], 'Categories1': ['grassland']})
    dm_crop_land_agr = dm_crop_land_agr.flatten()
    dm_grass_land_agr = dm_grass_land_agr.flatten()

    # C-stock from agroforestry cropland [tC] = carbon emissions factor cropland [tC/ha] * cropland for agriculture [ha]
    idx_land = dm_crop_land_agr.idx
    idx_ef = DM_land_use['crop_ef_agroforestry'].idx
    array_temp = dm_crop_land_agr.array[:, :, :, np.newaxis] \
                 * DM_land_use['crop_ef_agroforestry'].array[:, :, :, :]
    DM_land_use['crop_ef_agroforestry'].add(array_temp, dim='Variables',
                                            col_label='lus_land_lulucf_agroforestry_cropland', unit='tC')

    # C-stock from agroforestry grassland [tC] = carbon emissions factor grassland [tC/ha] * grassland for agriculture [ha]
    idx_land = dm_grass_land_agr.idx
    idx_ef = DM_land_use['liv_ef_agroforestry'].idx
    array_temp = dm_crop_land_agr.array[:, :, :, np.newaxis] \
                 * DM_land_use['liv_ef_agroforestry'].array[:, :, :, :]
    DM_land_use['liv_ef_agroforestry'].add(array_temp, dim='Variables',
                                           col_label='lus_land_lulucf_agroforestry_grassland', unit='tC')

    # CLIMATE SMART FORESTRY -------------------------------------------------------------------------------------------

    # Pre processing
    dm_forest = DM_land_use['land_man_gap'].filter({'Variables': ['lus_land'], 'Categories1': ['forest']})
    dm_forest = dm_forest.flatten()
    DM_land_use['forestry'] = DM_land_use['forestry'].flatten()
    DM_land_use['forestry'].append(dm_forest, dim='Variables')

    # Incremental biomass gain from forestry [m3] = biomass yield from managed agroforestry [m3/ha] * Forest land [ha]
    DM_land_use['forestry'].operation('lus_land_forest', '*', 'fxa_agr_climate-smart-forestry_csf-man',
                                      out_col='lus_climate-smart-forestry_biomass_csf-inc', unit='m3')

    # Incremental CO2 capture from forestry [Mt] = Incremental biomass gain from forestry [m3] * CO2 capture factor [Mt/m3]
    DM_land_use['forestry'].add(-0.0000009, dummy=True, col_label='CO2_capture_factor', dim='Variables', unit='Mt/m3')
    DM_land_use['forestry'].operation('CO2_capture_factor', '*', 'lus_climate-smart-forestry_biomass_csf-inc',
                                      out_col='lus_climate-smart-forestry_biomass_csf-inc_CO2-capture', unit='Mt')

    # Gross biomass gain from forest growth [m3] = Forest incremental growth [m3/ha] * Forest land [ha]
    DM_land_use['forestry'].operation('lus_land_forest', '*', 'fxa_agr_climate-smart-forestry_g-inc',
                                      out_col='lus_forestry_biomass_gross-increment', unit='m3')

    # Gross biomass forest available for wood supply [m3] = Gross biomass gain from forest growth [m3]
    #                                                       * share of forest wood available for wood supply [%]
    DM_land_use['forestry'].operation('lus_forestry_biomass_gross-increment', '*',
                                      'fxa_agr_climate-smart-forestry_faws-share',
                                      out_col='lus_forestry_biomass_faws_gross-increment', unit='m3')

    # Harvested biomass forest available for wood supply [m3] = Gross biomass forest available for wood supply [m3]
    #                                                           * harvesting rate [%]
    DM_land_use['forestry'].operation('lus_forestry_biomass_faws_gross-increment', '*',
                                      'fxa_agr_climate-smart-forestry_h-rate',
                                      out_col='lus_forestry_biomass_faws_harvested', unit='m3')

    # FORESTRY SELF-SUFFICIENCY ----------------------------------------------------------------------------------------

    # Pre processing total wood demand
    dm_wood = dm_wood.flatten()
    DM_land_use['forestry'].append(dm_wood, dim='Variables')

    # Wood trade balance [m3] = Harvested biomass forest available for wood supply [m3] -  Total wood demand [m3]
    DM_land_use['forestry'].operation('lus_forestry_biomass_faws_harvested', '-',
                                      'lus_fst_demand_rwe_total', out_col='', unit='m3')

    # (KNIME filtering exports/imports but does not seem to be used after)

    return DM_land_use

# CalculationLeaf BIOMASS EMISSIONS
def forestry_biomass_emissions_workflow(DM_land_use, cdm_const):

    # FORESTRY LOSSES --------------------------------------------------------------------------------------------------

    # Total yield forestry biomass losses from natural causes [m3/ha] = sum (yield losses from natural causes [m3/ha])
    DM_land_use['forestry'].groupby({'yield_nat-losses_total': 'fxa_agr_climate-smart-forestry_nat-losses.*'},
                                    dim='Variables', regex=True, inplace=True)

    # Total forestry biomass loss from natural causes [m3] = Forest land [ha] *
    #                                                   Total yield forestry biomass losses from natural causes [m3/ha]

    DM_land_use['forestry'].operation('lus_land_forest', '*',
                                      'yield_nat-losses_total', out_col='lus_forestry_biomass_loss', unit='m3')

    # Total forestry biomass loss (fuel & burnt) [m3] = Total forestry biomass loss from natural causes [m3]
    #                                                   * yield forestry biomass loss from deforestation [%]
    DM_land_use['forestry'].operation('lus_forestry_biomass_loss', '*', 'fxa_agr_climate-smart-forestry_def-wood-fuel',
                                      out_col='lus_forestry_biomass_loss_def-wood-fuel', unit='m3')
    DM_land_use['forestry'].operation('lus_forestry_biomass_loss', '*', 'fxa_agr_climate-smart-forestry_def-burnt',
                                      out_col='lus_forestry_biomass_loss_def-burnt', unit='m3')

    # BURNT BIOMASS EMISSIONS ------------------------------------------------------------------------------------------

    # Filtering constants
    cdm_burnt = cdm_const.filter({'Variables': ['cp_fst_ef_emissions-N2O_burnt', 'cp_fst_ef_emissions-CH4_burnt',
                                                'cp_fst_ef_emissions-CO2_burnt'], 'units': ['t/m3']})

    # GHG emissions from burnt forest biomass [t] = Total forestry biomass loss burnt [m3]
    #                                               * emission factor burnt biomass [t/m3]
    # CH4
    idx_cdm = cdm_burnt.idx
    idx_forestry = DM_land_use['forestry'].idx
    array_temp = DM_land_use['forestry'].array[:, :, idx_forestry['lus_forestry_biomass_loss_def-burnt']] \
                 * cdm_burnt.array[idx_cdm['cp_fst_ef_emissions-CH4_burnt']]
    DM_land_use['forestry'].add(array_temp, dim='Variables',
                                col_label='lus_emissions_emissions-CO2_forest_to_land_biomass_emissions-CH4', unit='t')
    # N2O
    idx_cdm = cdm_burnt.idx
    idx_forestry = DM_land_use['forestry'].idx
    array_temp = DM_land_use['forestry'].array[:, :, idx_forestry['lus_forestry_biomass_loss_def-burnt']] \
                 * cdm_burnt.array[idx_cdm['cp_fst_ef_emissions-N2O_burnt']]
    DM_land_use['forestry'].add(array_temp, dim='Variables',
                                col_label='lus_emissions_emissions-CO2_forest_to_land_biomass_emissions-N2O', unit='t')

    # CO2
    idx_cdm = cdm_burnt.idx
    idx_forestry = DM_land_use['forestry'].idx
    array_temp = DM_land_use['forestry'].array[:, :, idx_forestry['lus_forestry_biomass_loss_def-burnt']] \
                 * cdm_burnt.array[idx_cdm['cp_fst_ef_emissions-CO2_burnt']]
    DM_land_use['forestry'].add(array_temp, dim='Variables',
                                col_label='lus_emissions_emissions-CO2_forest_to_land_biomass_emissions-CO2', unit='t')
    return DM_land_use

def simulate_industry_to_landuse_input():
    
    dm_ind = simulate_input(from_sector='industry', to_sector='agriculture')

    return dm_ind

def simulate_agriculture_to_landuse_input():
    
    dm_lus = simulate_input(from_sector='agriculture', to_sector='landuse')
    
    
    variables = list()
    DM_bioenergy = dm_lus.filter({"Variables" : variables})
    dm_lgn = {}
    dm_land_use = {}
    
    return DM_bioenergy, dm_lgn, dm_land_use

def land_use(lever_setting, years_setting, interface = Interface(), calibration = False):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    landuse_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/landuse.pickle')
    DM_ots_fts, DM_land_use, cdm_const = read_data(landuse_data_file, lever_setting)

    if interface.has_link(from_sector='industry', to_sector='agriculture'):
        dm_ind = interface.get_link(from_sector='industry', to_sector='agriculture')
    else:
        dm_ind = simulate_industry_to_landuse_input()
        
    if interface.has_link(from_sector='agriculture', to_sector='landuse'):
        dm_ind = interface.get_link(from_sector='agriculture', to_sector='landuse')
    else:
        DM_bioenergy, dm_lgn, dm_land_use = simulate_agriculture_to_landuse_input()

    # CalculationTree LAND USE
    dm_wood = wood_workflow(DM_bioenergy, dm_lgn, dm_ind)
    DM_land_use = land_allocation_workflow(DM_land_use, dm_land_use)
    DM_land_use = land_matrix_workflow(DM_land_use)
    DM_land_use = land_carbon_dynamics_workflow(DM_land_use)
    DM_land_use = forestry_workflow(DM_land_use, dm_wood, dm_land_use)
    DM_land_use = forestry_biomass_emissions_workflow(DM_land_use, cdm_const)

    # CalculationLeaf Deforestation patterns (does not appear to be used after)

    return

def local_land_use_run():
    years_setting, lever_setting = init_years_lever()
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)
    land_use(lever_setting, years_setting)
    return

# run local
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/landuse_module.py"
# database_from_csv_to_datamatrix()
start = time.time()
results_run = local_land_use_run()
end = time.time()
print(end-start)