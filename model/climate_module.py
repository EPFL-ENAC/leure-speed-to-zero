# Import the Packages

import pandas as pd
import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.auxiliary_functions import read_level_data
from model.common.interface_class import Interface

# ImportFunctions
from model.common.io_database import read_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.auxiliary_functions import filter_geoscale, read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups


# filtering the constants & read csv and prepares it for the pickle format

# Lever setting for local purpose


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


# Setting up the database in the module
def database_from_csv_to_datamatrix():
    
    # Set years range
    years_setting = [1990, 2015, 2100, 1]
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) 
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int))
    years_all = years_ots + years_fts

    # Initiate the dictionary for ots & fts
    dict_ots = {}
    dict_fts = {}

    # Data - Lever - Climate temperature
    file = 'climate_temperature'
    lever = "temp"

    # Creates the datamatrix for lifestyles population
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[0, 0], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name', group_list=[
                                                                            'bld_climate-impact-space',
                                                                            'bld_climate-impact_average'])

    #  Create the data matrix for lifestyles
    DM_climate = {
        'fts': dict_fts,
        'ots': dict_ots
    }

    # Pickle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))  # creates local path variable
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/climate.pickle')
    # creates path variable for the pickle
    with open(f, 'wb') as handle:  # 'wb': writing binary / standard protocol for pickle
        pickle.dump(DM_climate, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return DM_climate

def read_data(data_file, lever_setting):
    
    # load dm
    with open(data_file, 'rb') as handle:
        DM_climate = pickle.load(handle)

    # get lever
    DM_ots_fts = read_level_data(DM_climate, lever_setting)

    return DM_ots_fts

def sum_emissions_by_gas(DM_interface):
    
    # NOTE: this is work in progress, to be recovered when we do climate
    
    # buildings
    dm_emi = DM_interface["buildings"].filter_w_regex({"Variables" : "bld.*gas-ff-natural.*|bld.*heat-ambient.*|bld.*heat-geothermal.*|bld.*heat-solar.*|bld.*liquid-ff-heatingoil.*|bld.*solid-ff-coal.*|bld.*solid-bio.*"})
    dm_emi.deepen()
    dm_emi.group_all("Categories1")
    dm_emi.deepen()
    dm_emi.add(np.nan, "Categories1", "emissions-CH4", unit = "Mt", dummy = True)
    dm_emi.add(np.nan, "Categories1", "emissions-N2O", unit = "Mt", dummy = True)
    dm_emi.sort("Categories1")
    
    # transport
    dm_tra = DM_interface["transport"].filter_w_regex({"Variables" : "tra.*LDV.*|tra.*2W.*|tra.*rail.*|tra.*bus.*|tra.*metro-tram.*|tra.*aviation.*|tra.*marine.*|tra.*IWW.*|tra.*HDV.*"})
    dm_tra.deepen_twice()
    dm_tra.group_all("Categories1")
    dm_tra.group_all("Categories1")
    dm_tra.deepen()
    dm_emi.append(dm_tra, "Variables")
    
    # district heating
    dm_dh = DM_interface["district-heating"].filter_w_regex({"Variables" : "dhg.*gas-ff-natural.*|dhg.*heat-ambient.*|dhg.*heat-geothermal.*|dhg.*heat-solar.*|dhg.*liquid-ff-heatingoil.*|dhg.*solid-ff-coal.*|dhg.*solid-bio.*"})
    dm_dh.deepen_twice()
    dm_dh.group_all("Categories2")
    dm_emi.append(dm_dh, "Variables")
    
    # industry
    dm_ind = DM_interface["industry"]
    dm_ind.deepen()
    dm_temp = dm_ind.filter({"Variables" : ['ind_emissions-CO2', 'ind_emissions-CO2_biogenic']})
    dm_ind.drop(dim = "Variables", col_label = "ind_emissions-CO2_biogenic")
    idx = dm_ind.idx
    dm_ind.array[:,:,idx["ind_emissions-CO2"],:] = np.nansum(dm_temp.array, axis = -2)
    dm_ind.group_all("Categories1")
    dm_ind.deepen()
    dm_emi.append(dm_ind, "Variables")
    
    # ammonia
    dm_amm = DM_interface["ammonia"]
    dm_amm.deepen_twice()
    dm_amm.group_all("Categories2")
    dm_emi.append(dm_amm, "Variables")
    
    # land use
    dm_lus = DM_interface["land-use"]
    dm_lus.deepen_twice()
    dm_lus.group_all("Categories2")
    dm_lus.add(np.nan, "Categories1", "emissions-CH4", unit = "Mt", dummy = True)
    dm_lus.add(np.nan, "Categories1", "emissions-N2O", unit = "Mt", dummy = True)
    dm_lus.sort("Categories1")
    dm_emi.append(dm_lus, "Variables")
    
    # biodiversity
    dm_bdy = DM_interface["biodiversity"]
    dm_bdy.deepen()
    dm_emi.append(dm_bdy, "Variables")
    
    # agriculture
    dm_agr = DM_interface["agriculture"]
    dm_agr.deepen()
    dm_agr.group_all("Categories1")
    dm_agr.deepen()
    dm_emi.append(dm_agr, "Variables")
    
    # dm_agr_sub = dm_agr.filter_w_regex({"Variables": ".*crop.*"})
    # dm_agr_sub.deepen_twice()
    # dm_agr_sub.group_all("Categories2")
    
    # dm_agr_liv = dm_agr.filter_w_regex({"Variables": ".*liv.*"})
    # dm_agr_liv.deepen()
    # dm_agr_liv.deepen(based_on = "Variables")
    # dm_agr_liv.deepen(based_on = "Variables")
    # dm_agr_liv.group_all("Categories3")
    # dm_agr_liv.group_all("Categories2")
    # dm_agr_liv.group_all("Categories1")
    # dm_agr_liv.deepen(based_on = "Variables")
    # dm_agr_sub.append(dm_agr_liv, "Categories1")
    # dm_agr_sub.group_all("Categories1")
    # dm_agr_sub.deepen()
    
    # dm_agr_input = dm_agr.filter_w_regex({"Variables": ".*input.*"})
    # dm_agr_input.deepen()
    # dm_agr_input.group_all("Categories1")
    # dm_agr_input.rename_col(col_in = 'agr_input-use_emissions-CO2', col_out = 'agr_emissions-CO2_input-use', dim = "Variables")
    # dm_agr_input.deepen()
    
    # electricity
    dm_elc = DM_interface["electricity"].filter({"Variables" : ["elc_emissions-CO2"]})
    dm_elc.deepen()
    dm_elc.add(np.nan, "Categories1", "emissions-CH4", unit = "Mt", dummy = True)
    dm_elc.add(np.nan, "Categories1", "emissions-N2O", unit = "Mt", dummy = True)
    dm_emi.append(dm_elc, "Variables")
    
    # oil refinery
    dm_ref = DM_interface["refinery"]
    dm_ref.deepen()
    dm_ref.add(np.nan, "Categories1", "emissions-CH4", unit = "Mt", dummy = True)
    dm_ref.add(np.nan, "Categories1", "emissions-N2O", unit = "Mt", dummy = True)
    dm_emi.append(dm_ref, "Variables")
    
    # sum
    variables = dm_emi.col_labels["Variables"]
    for i in variables:
        dm_emi.rename_col(i, "clm_" + i, "Variables")
    dm_emi.deepen(based_on = "Variables")
    dm_emi.group_all("Categories2")
    
    del dm_agr, dm_amm, dm_bdy, dm_dh, dm_elc, dm_ind, dm_lus, dm_ref, dm_temp, \
        dm_tra, i, idx, variables
    
    return dm_emi

def climate_buildings_interface(DM_ots_fts, write_xls = False):
    
    # append
    dm_bld = DM_ots_fts["temp"]["bld_climate-impact-space"]
    dm_bld.append(DM_ots_fts["temp"]["bld_climate-impact_average"], "Variables")
        
    # df_bld
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_bld = dm_bld.write_df()
        df_bld.to_excel(current_file_directory + "/../_database/data/xls/" + 'climate-to-buildings.xlsx', index=False)

    # return
    return dm_bld

# CORE module
def climate(lever_setting, years_setting, interface = Interface(), calibration = False):
    
    # climate data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    climate_data_file = os.path.join(current_file_directory,'../_database/data/datamatrix/geoscale/climate.pickle')
    DM_ots_fts = read_data(climate_data_file, lever_setting)
    
    # interface buildings
    dm_bld = climate_buildings_interface(DM_ots_fts)
    interface.add_link(from_sector='climate', to_sector='buildings', dm=dm_bld)

    # TODO: interface water when water is ready

    results_run = {}
    return results_run


# Local run of lifestyles
def local_climate_run():
    
    # Initiate the year & lever setting
    years_setting, lever_setting = init_years_lever()
    climate(lever_setting, years_setting)

    # get geoscale
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    # run
    results_run = climate(lever_setting, years_setting)

    return results_run

# # local
# __file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/climate_module.py"
# # database_from_csv_to_datamatrix()
# results_run = local_climate_run()



