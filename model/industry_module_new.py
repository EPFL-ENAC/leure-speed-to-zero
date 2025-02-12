
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, read_database_to_ots_fts_dict
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_level_data
from model.common.auxiliary_functions import simulate_input, material_decomposition, calibration_rates, cost
from model.common.auxiliary_functions import material_switch, energy_switch
import pickle
import json
import os
import numpy as np
import re
import warnings
import time
import pandas as pd
warnings.simplefilter("ignore")

def read_data(data_file, lever_setting):
    
    # load dm
    with open(data_file, 'rb') as handle:
        DM_industry = pickle.load(handle)

    # get fxa
    DM_fxa = DM_industry['fxa']

    # Get ots fts based on lever_setting
    DM_ots_fts = read_level_data(DM_industry, lever_setting)

    # get calibration
    dm_cal = DM_industry['calibration']

    # get constants
    CMD_const = DM_industry['constant']

    # clean
    del handle, DM_industry, data_file, lever_setting
    
    # return
    return DM_fxa, DM_ots_fts, dm_cal, CMD_const

def simulate_transport_to_industry_input():
    dm_transport = simulate_input(from_sector='transport', to_sector='industry')

    # rename
    # dm_transport.rename_col_regex(str1 = "tra_", str2 = "tra_product-demand_", dim = "Variables")
    dm_transport.deepen()

    # infra
    dm_demand_tra_infra = dm_transport.filter({"Variables" : ['tra_product-demand'],
                                               "Categories1" : ['rail','road','trolley-cables']})
    dm_demand_tra_infra.units["tra_product-demand"] = "km"

    # vehicules
    dm_demand_tra_veh = dm_transport.filter({"Variables" : ['tra_product-demand'],
                                             "Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                              'planes', 'ships', 'trains',
                                                              'trucks-EV', 'trucks-FCV', 'trucks-ICE']})
    dm_demand_tra_veh.units["tra_product-demand"] = "num"
    
    # waste
    dm_waste_veh =  dm_transport.filter({"Variables" : ['tra_product-waste'],
                                         "Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                          'planes', 'ships', 'trains',
                                                          'trucks-EV', 'trucks-FCV', 'trucks-ICE']})
    dm_waste_veh.units["tra_product-waste"] = "num"
    
    # stock
    dm_stock_veh =  dm_transport.filter({"Variables" : ['tra_product-stock'],
                                         "Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                          'planes', 'ships', 'trains',
                                                          'trucks-EV', 'trucks-FCV', 'trucks-ICE']})
    dm_stock_veh.units["tra_product-stock"] = "num"
    

    DM_transport = {
        "tra-infra-demand": dm_demand_tra_infra,
        "tra-veh-demand": dm_demand_tra_veh,
        "tra-veh-waste" : dm_waste_veh,
        "tra-veh-stock" : dm_stock_veh
    }

    return DM_transport

def simulate_lifestyles_to_industry_input():
    dm_lifestyles = simulate_input(from_sector='lifestyles', to_sector='industry')

    dm_lifestyles.rename_col_regex(str1="lfs_", str2="lfs_product-demand_", dim="Variables")
    dm_lifestyles.deepen()

    return dm_lifestyles

def simulate_buildings_to_industry_input():
    dm_buildings = simulate_input(from_sector='buildings', to_sector='industry')

    # rename
    dm_buildings.rename_col_regex(str1 = "bld_", str2 = "bld_product-demand_", dim = "Variables")
    dm_buildings.rename_col_regex(str1 = "_new_",str2 = "-new-",dim = "Variables")
    dm_buildings.rename_col_regex(str1 = "_reno_",str2 = "-reno-",dim = "Variables")
    dm_buildings.rename_col_regex(str1 = "-new-dhg_pipe",str2 = "_new-dhg-pipe",dim = "Variables")

    # deepen
    dm_buildings.deepen()

    # pipes
    dm_demand_bld_pipe = dm_buildings.filter_w_regex({"Categories1" : ".*pipe"})
    dm_demand_bld_pipe.units["bld_product-demand"] = "km"

    # floor
    dm_demand_bld_floor = dm_buildings.filter_w_regex({"Categories1" : ".*floor"})
    dm_demand_bld_floor.units["bld_product-demand"] = "m2"

    # domestic appliances
    dm_demand_bld_domapp = dm_buildings.filter({"Categories1" : ['computer', 'dishwasher', 'dryer',
                                                                  'freezer', 'fridge', 'phone',
                                                                  'tv', 'wmachine']})
    dm_demand_bld_domapp.units["bld_product-demand"] = "num"

    DM_buildings = {
        "bld-pipe-demand" : dm_demand_bld_pipe,
        "bld-floor-demand" : dm_demand_bld_floor,
        "bld-domapp-demand" : dm_demand_bld_domapp
    }

    return DM_buildings

def industry_agriculture_interface(DM_material_production, DM_energy_demand):
    
    DM_agr = {}
    
    # natfibers
    dm_temp = DM_material_production["natfiber"].copy()
    dm_temp.rename_col('material-decomposition', "ind_dem", "Variables")
    DM_agr["natfibers"] = dm_temp.flatten()
    
    # bioenergy
    dm_temp = DM_energy_demand["bioener_bybiomat"].copy()
    dm_temp.rename_col("energy-demand_bioenergy", "ind_bioenergy", "Variables")
    dm_temp = dm_temp.filter({"Categories1" : ['gas-bio', 'solid-bio']})
    DM_agr["bioenergy"] = dm_temp
    
    # biomaterial
    dm_temp = DM_energy_demand["feedstock_bybiomat"].copy()
    dm_temp.rename_col("energy-demand-feedstock", "ind_biomaterial", "Variables")
    dm_temp = dm_temp.filter({"Categories1" : ['gas-bio']})
    DM_agr["biomaterial"] = dm_temp
    
    return DM_agr

def industry_ammonia_interface(DM_material_production, DM_energy_demand, write_xls = False):
    
    dm_amm_matprod = DM_material_production["bymat"].filter({"Categories1" : ["chem"]})
    dm_amm_endem = DM_energy_demand["bymatcarr"].filter({"Categories1" : ['chem']})
    DM_amm = {"material-production" : dm_amm_matprod,
              "energy-demand" : dm_amm_endem}
    
    # df_agr
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        dm_amm = dm_amm_matprod.flatten()
        dm_amm.append(dm_amm_endem.flatten().flatten(),"Variables")
        df_amm = dm_amm.write_df()
        df_amm.to_excel(current_file_directory + "/../_database/data/xls/" + 'All-Countries-interface_from-industry-to-ammonia.xlsx', index=False)
    
    return DM_amm

def industry_landuse_interface(DM_material_production, DM_energy_demand, write_xls = False):
    
    DM_lus = {}
    
    # timber
    dm_timber = DM_material_production["bymat"].filter({"Categories1" : ["timber"]})
    dm_timber.rename_col("material-production", "ind_material-production", "Variables")
    dm_timber = dm_timber.flatten()
    DM_lus["timber"] = dm_timber
    
    # woodpuplp
    dm_woodpulp = DM_material_production["bytech"].filter({"Categories1" : ['paper_woodpulp']})
    dm_woodpulp.rename_col("material-production", "ind_material-production", "Variables")
    DM_lus["woodpulp"] = dm_woodpulp.flatten()
    
    # biomaterial solid bio
    dm_temp = DM_energy_demand["feedstock_bybiomat"].copy()
    dm_temp.rename_col("energy-demand-feedstock", "ind_biomaterial", "Variables")
    dm_temp = dm_temp.filter({"Categories1" : ['solid-bio']})
    DM_lus["biomaterial"] = dm_temp.flatten()
        
    # df_agr
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        
        dm_lus = DM_lus["timber"].copy()
        dm_lus.append(DM_lus["woodpulp"], "Variables")
        dm_lus.append(DM_lus["biomaterial"], "Variables")
        
        dm_lus = dm_lus.write_df()
        dm_lus.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-agriculture.xlsx', index=False)

    # return
    return DM_lus

def industry_power_interface(DM_energy_demand, write_xls = False):
    
    # dm_elc
    dm_elc = DM_energy_demand["bycarr"].filter(
        {"Categories1" : ['electricity','hydrogen']})
    dm_elc.rename_col("energy-demand", "ind_energy-demand", "Variables")
    dm_elc = dm_elc.flatten()

    dm_elc.change_unit('ind_energy-demand_electricity', factor=1e3, old_unit='TWh', new_unit='GWh')
    dm_elc.change_unit('ind_energy-demand_hydrogen', factor=1e3, old_unit='TWh', new_unit='GWh')

    DM_pow = {
        'electricity': dm_elc.filter({'Variables': ['ind_energy-demand_electricity']}),
        'hydrogen': dm_elc.filter({'Variables': ['ind_energy-demand_hydrogen']})
    }

    # df_elc
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        dm_elc = dm_elc.write_df()
        dm_elc.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-power.xlsx', index=False)
        
    # return
    return DM_pow

def industry_refinery_interface(DM_energy_demand, write_xls = False):
    
    # dm_elc
    dm_ref = DM_energy_demand["bycarr"].filter(
        {"Categories1": ['liquid-ff-oil_diesel', 'liquid-ff-oil_fuel-oil',
                          'gas-ff-natural', 'solid-ff-coal']})
    dm_ref.rename_col("energy-demand", "ind_energy-demand", "Variables")
    dm_ref.rename_col_regex('liquid-ff-oil_', '', dim='Categories1')
    dm_ref.sort("Categories1")

    # df_elc
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        dm_ref = dm_ref.write_df()
        dm_ref.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-refinery.xlsx', index=False)
        
    # return
    return dm_ref

def industry_water_inferface(DM_energy_demand, DM_material_production, write_xls = False):
    
    # dm_water
    dm_water = DM_energy_demand["bycarr"].filter(
        {"Categories1" : ['electricity', 'gas-ff-natural', 'hydrogen', 'liquid-ff-oil', 
                          'solid-ff-coal']}).flatten()
    dm_water.append(DM_material_production["bytech"].filter(
        {"Categories1" : ['aluminium_prim', 'aluminium_sec', 'cement_dry-kiln', 'cement_geopolym', 
                          'cement_wet-kiln', 'chem_chem-tech', 'copper_tech', 'glass_glass', 'lime_lime',
                          'paper_recycled', 'paper_woodpulp', 'steel_BF-BOF', 'steel_hisarna', 
                          'steel_hydrog-DRI', 'steel_scrap-EAF']}).flatten(), "Variables")
    variables = dm_water.col_labels["Variables"]
    for i in variables:
        dm_water.rename_col(i, "ind_" + i, "Variables")
    dm_water.sort("Variables")

    # df_water
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_water = dm_water.write_df()
        df_water.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-water.xlsx', index=False)

    # return
    return dm_water

def industry_ccus_interface(DM_emissions, write_xls = False):
    
    # adjust variables' names
    variables = DM_emissions["capt_w_cc_bytech"].col_labels["Categories1"]
    variables_new = [rename_tech_fordeepen(i) for i in variables]
    for i in range(len(variables)):
        DM_emissions["capt_w_cc_bytech"].rename_col(variables[i], variables_new[i], dim = "Categories1")
    DM_emissions["capt_w_cc_bytech"].rename_col('CO2-capt-w-cc','ind_CO2-emissions-CC',"Variables")

    # dm_ccus
    dm_ccus = DM_emissions["capt_w_cc_bytech"].filter(
        {"Categories1" : ['aluminium_prim', 'aluminium_sec', 'cement_dry-kiln', 'cement_geopolym', 
                          'cement_wet-kiln', 'chem_chem-tech', 'lime_lime',
                          'paper_recycled', 'paper_woodpulp', 'steel_BF-BOF', 'steel_hisarna', 
                          'steel_hydrog-DRI', 'steel_scrap-EAF']}).flatten()
    dm_ccus.sort("Variables")

    # df_ccus
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_ccus = dm_ccus.write_df()
        df_ccus.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-ccus.xlsx', index=False)
        
    # return
    return dm_ccus
    
def industry_gtap_interface(DM_energy_demand, DM_material_production, write_xls = False):
    
    # adjust variables' names
    dm_temp = DM_energy_demand["bymatcarr"].copy()
    dm_temp.rename_col("energy-demand", "l_nrg","Variables")
    dm_temp.array = dm_temp.array * 1000
    dm_temp.units["l_nrg"] = "GWh"
    variables = dm_temp.col_labels["Categories1"]
    variables_new = ['al', 'ce', 'ch', 'co', 'fb', 'gl', 'li', 'me', 'oi', 'pa', 'st', 'tx', 'tr', 'ww']
    for i in range(len(variables)):
        dm_temp.rename_col(variables[i],variables_new[i],"Categories1")
    variables = dm_temp.col_labels["Categories2"]
    variables_new = ['el','gb','ga','hy','lb','ol','sb','cl','sw']
    for i in range(len(variables)):
        dm_temp.rename_col(variables[i],variables_new[i],"Categories2")

    dm_temp2 = DM_material_production["bymat"].filter(
        {"Categories1" : ['aluminium', 'cement', 'chem', 'copper','glass', 'lime', 
                          'paper', 'steel']})
    variables = dm_temp2.col_labels["Categories1"]
    variables_new = ['al', 'ce', 'ch', 'co', 'gl', 'li', 'pa', 'st']
    for i in range(len(variables)):
        dm_temp2.rename_col(variables[i],variables_new[i],"Categories1")
    dm_temp2.rename_col("material-production","l_mat","Variables")
    dm_temp2.array = dm_temp2.array / 1000
    dm_temp2.units["l_mat"] = "Mt"

    # dm_gtap
    dm_gtap = dm_temp.flatten()
    dm_gtap = dm_gtap.flatten()
    dm_gtap.append(dm_temp2.flatten(), "Variables")
    dm_gtap.sort("Variables")

    # df_gtap
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_gtap = dm_gtap.write_df()
        df_gtap.columns = df_gtap.columns.str.removesuffix("[Mt]")
        df_gtap.columns = df_gtap.columns.str.removesuffix("[GWh]")
        df_gtap.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-gtap.xlsx', index=False)
        
    # return
    return dm_gtap

def industry_minerals_interface(DM_material_production, DM_production, DM_ots_fts, write_xls = False):
    
    DM_ind = {}
    
    # aluminium pack
    dm_alupack = DM_production["lfs"].filter({"Categories1" : ["aluminium-pack"]})
    DM_ind["aluminium-pack"] = dm_alupack.flatten()
    
    # material production
    dm_matprod = DM_material_production["bymat"].filter({"Categories1": ["timber", 'glass', 'cement']})
    dm_paper_woodpulp = DM_material_production["bytech"].filter({"Categories1": ['paper_woodpulp']})
    dm_matprod.append(dm_paper_woodpulp, "Categories1")
    dm_matprod.rename_col("material-production", "ind_material-production", "Variables")
    DM_ind["material-production"] = dm_matprod.flatten()
    
    # technology development
    dm_techdev = DM_ots_fts['technology-development'].filter(
        {"Categories1" : ['aluminium-prim', 'aluminium-sec','copper-tech',
                          'steel-BF-BOF', 'steel-hisarna', 'steel-hydrog-DRI', 
                          'steel-scrap-EAF']})
    variables = dm_techdev.col_labels["Categories1"]
    variables_new = ['aluminium_primary', 'aluminium_secondary','copper_secondary',
                      'steel_BF-BOF', 'steel_hisarna', 'steel_hydrog-DRI', 
                      'steel_scrap-EAF']
    for i in range(len(variables)):
        dm_techdev.rename_col(variables[i], variables_new[i], dim = "Categories1")
    dm_techdev.rename_col("ind_technology-development","ind_proportion","Variables")
    DM_ind["technology-development"] = dm_techdev.flatten()
    
    # material efficiency
    DM_ind["material-efficiency"] = DM_ots_fts['material-efficiency'].filter(
        {"Variables" : ['ind_material-efficiency'],
         "Categories1" : ['aluminium','copper','steel']})
    
    # material switch
    dm_temp = DM_ots_fts['material-switch'].filter(
        {"Categories1" : ['build-steel-to-timber', 'cars-steel-to-chem', 
                          'trucks-steel-to-aluminium', 'trucks-steel-to-chem']}).flatten()
    dm_temp.rename_col_regex("material-switch_","material-switch-","Variables")
    DM_ind["material-switch"] = dm_temp
    
    # product net import
    dm_temp = DM_ots_fts["product-net-import"].filter(
        {"Variables" : ["ind_product-net-import"],
         "Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'computer', 'dishwasher', 'dryer',
                          'freezer', 'fridge','phone','planes','rail','road', 'ships', 'trains',
                          'trolley-cables', 'trucks-EV', 'trucks-FCV', 'trucks-ICE', 'tv', 
                          'wmachine','new-dhg-pipe']})
    dm_temp.rename_col_regex("cars","LDV","Categories1")
    dm_temp.rename_col_regex("trucks","HDVL","Categories1")
    dm_temp.rename_col("computer","electronics-computer","Categories1")
    dm_temp.rename_col("phone","electronics-phone","Categories1")
    dm_temp.rename_col("tv","electronics-tv","Categories1")
    dm_temp.rename_col("dishwasher","dom-appliance-dishwasher","Categories1")
    dm_temp.rename_col("dryer","dom-appliance-dryer","Categories1")
    dm_temp.rename_col("freezer","dom-appliance-freezer","Categories1")
    dm_temp.rename_col("fridge","dom-appliance-fridge","Categories1")
    dm_temp.rename_col("wmachine","dom-appliance-wmachine","Categories1")
    dm_temp.rename_col("new-dhg-pipe","infra-pipe","Categories1")
    dm_temp.rename_col("rail","infra-rail","Categories1")
    dm_temp.rename_col("road","infra-road","Categories1")
    dm_temp.rename_col("trolley-cables","infra-trolley-cables","Categories1")
    dm_temp.rename_col("planes","other-planes","Categories1")
    dm_temp.rename_col("ships","other-ships","Categories1")
    dm_temp.rename_col("trains","other-trains","Categories1")
    dm_temp.rename_col_regex('FCV', 'FCEV', 'Categories1')
    dm_temp.sort("Categories1")
    DM_ind["product-net-import"] = dm_temp.flatten()

    # df_min
    if write_xls is True:
        
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        
        dm_min = DM_ind['aluminium-pack']
        dm_min.append(DM_ind['material-production'], "Variables")
        dm_min.append(DM_ind['technology-development'], "Variables")
        dm_min.append(DM_ind['material-efficiency'].flatten(), "Variables")
        dm_min.append(DM_ind['material-switch'], "Variables")
        dm_min.append(DM_ind['product-net-import'], "Variables")
        dm_min.sort("Variables")
        
        df_min = dm_min.write_df()
        df_min.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-minerals.xlsx', index=False)
        
    # return
    return DM_ind

def industry_employment_interface(DM_material_demand, DM_energy_demand, DM_material_production, DM_cost, DM_ots_fts, write_xls = False):
    
    # get material demand for appliances
    DM_material_demand["appliances"] = \
        DM_material_demand["material-demand"].filter(
            {"Categories1" : ["computer", "dishwasher", "dryer",
                              "freezer", "fridge", "tv"]}).group_all("Categories1",
                                                                   inplace=False)
    DM_material_demand["appliances"].rename_col("material-decomposition", "material-demand_appliances", "Variables")
    
    # get material demand for transport
    DM_material_demand["transport"] = \
        DM_material_demand["material-demand"].filter(
            {"Categories1": ['cars-EV', 'cars-FCV', 'cars-ICE',
                              'trucks-EV', 'trucks-FCV', 'trucks-ICE',
                              'planes', 'ships', 'trains']}).group_all("Categories1", inplace=False)
    DM_material_demand["transport"].rename_col("material-decomposition", "material-demand_transport", "Variables")
    
    # get material demand for construction
    DM_material_demand["construction"] = \
        DM_material_demand["material-demand"].filter(
            {"Categories1": ['floor-area-new-non-residential', 'floor-area-new-residential',
                              'floor-area-reno-non-residential', 'floor-area-reno-residential',
                              'rail', 'road', 'trolley-cables']}).group_all("Categories1", inplace = False)
    DM_material_demand["construction"].rename_col("material-decomposition", "material-demand_construction", "Variables")
    
    # dm_emp
    dm_emp = DM_material_demand["appliances"].flatten()
    dm_emp.append(DM_material_demand["transport"].flatten(), "Variables")
    dm_emp.append(DM_material_demand["construction"].flatten(), "Variables")
    dm_emp.append(DM_energy_demand["bymat"].flatten(), "Variables")
    dm_emp.append(DM_energy_demand["bymatcarr"].flatten().flatten(), "Variables")
    dm_emp.append(DM_material_production["bymat"].filter(
        {"Categories1" : DM_energy_demand["bymat"].col_labels["Categories1"]}).flatten(), "Variables")
    dm_emp.append(DM_cost["material-production_capex"].flatten(), "Variables")
    dm_emp.append(DM_cost["material-production_opex"].flatten(), "Variables")
    dm_emp.append(DM_cost["CO2-capt-w-cc_capex"].flatten(), "Variables")
    dm_emp.append(DM_cost["CO2-capt-w-cc_opex"].flatten(), "Variables")
    variables = dm_emp.col_labels["Variables"]
    for i in variables:
        dm_emp.rename_col(i, "ind_" + i, "Variables")
    dm_emp.append(DM_ots_fts["material-net-import"].filter(
        {"Categories1" : ['aluminium', 'cement', 'chem', 'copper', 'glass', 'lime', 
                          'paper', 'steel', 'timber'],}).flatten(), "Variables")
    dm_emp.sort("Variables")

    # df_emp
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_emp = dm_emp.write_df()
        df_emp.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-employment.xlsx', index=False)

    # return
    return dm_emp

def industry_emissions_interface(DM_emissions, write_xls = False):
    
    # adjust variables' names
    dm_temp = DM_emissions["bygasmat"].flatten().flatten()
    dm_temp.deepen()
    dm_temp.rename_col_regex("_","-","Variables")
    DM_emissions["combustion_bio_capt_w_cc_neg_bymat"].rename_col("emissions-biogenic-negative","emissions-CO2_biogenic","Variables")
    dm_temp1 = DM_emissions["combustion_bio_capt_w_cc_neg_bymat"].flatten()
    dm_temp1.rename_col_regex("CO2-capt-w-cc_","","Categories1")

    # dm_ems
    dm_ems = dm_temp.flatten()
    dm_ems.append(dm_temp1.flatten(), "Variables")
    variables = dm_ems.col_labels["Variables"]
    for i in variables:
        dm_ems.rename_col(i, "ind_" + i, "Variables")
    dm_ems.sort("Variables")

    # dm_cli
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        dm_ems = dm_ems.write_df()
        dm_ems.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-emissions.xlsx', index=False)

    # return
    return dm_ems

def industry_airpollution_interface(DM_material_production, DM_energy_demand, write_xls = False):
    
    # dm_airpoll
    dm_airpoll = DM_material_production["bytech"].flatten()
    dm_airpoll.append(DM_energy_demand["bymatcarr"].flatten().flatten(), "Variables")
    variables = dm_airpoll.col_labels["Variables"]
    for i in variables:
        dm_airpoll.rename_col(i, "ind_" + i, "Variables")
    dm_airpoll.sort("Variables")

    # write
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_airpoll = dm_airpoll.write_df()
        df_airpoll.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-air_pollution.xlsx', index=False)
        
    # return
    return dm_airpoll

def industry_district_heating_interface(DM_energy_demand, write_xls = False):
    
    # FIXME!: make dummy values for dh (this is like this also in KNIME, to be seen what to do)
    dm_dh = DM_energy_demand["bycarr"].filter({"Categories1" : ["electricity"]})
    dm_dh = dm_dh.flatten()
    dm_dh.add(0, dim = "Variables", col_label = "dhg_energy-demand_contribution_heat-waste", unit = "TWh/year", dummy = True)
    dm_dh.drop("Variables", 'energy-demand_electricity')

    # dm_dh
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_dh = dm_dh.write_df()
        df_dh.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-district_heating.xlsx', index=False)
        
    # return
    return dm_dh

def industry(lever_setting, years_setting, interface = Interface(), calibration = False):

    # industry data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    industry_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/industry.pickle')
    DM_fxa, DM_ots_fts, dm_cal, CDM_const = read_data(industry_data_file, lever_setting)

    cntr_list = dm_cal.col_labels['Country']

    if interface.has_link(from_sector='transport', to_sector='industry'):
        DM_transport = interface.get_link(from_sector='transport', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing transport to industry interface')
        DM_transport = simulate_transport_to_industry_input()
        for key in DM_transport.keys():
            DM_transport[key].filter({'Country': cntr_list}, inplace=True)

    if interface.has_link(from_sector='lifestyles', to_sector='industry'):
        dm_demand_lfs = interface.get_link(from_sector='lifestyles', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing lifestyles to industry interface')
        dm_demand_lfs = simulate_lifestyles_to_industry_input()
        dm_demand_lfs.filter({'Country': cntr_list}, inplace=True)

    if interface.has_link(from_sector='buildings', to_sector='industry'):
        DM_buildings = interface.get_link(from_sector='buildings', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing buildings to industry interface')
        DM_buildings = simulate_buildings_to_industry_input()
        for key in DM_buildings.keys():
            DM_buildings[key].filter({'Country': cntr_list}, inplace=True)

    # get product import
    dm_import = DM_ots_fts["product-net-import"]
    
    # get product production
    DM_production = product_production(DM_buildings["bld-pipe-demand"], DM_buildings["bld-floor-demand"], DM_buildings["bld-domapp-demand"], 
                                       DM_transport["tra-infra-demand"], DM_transport["tra-veh-demand"], 
                                       dm_demand_lfs, dm_import)
    
    # get material demand
    DM_material_demand = apply_material_decomposition(DM_production["bld-pipe"], DM_production["bld-floor"], DM_production["bld-domapp"],
                                                      DM_production["tra-infra"], DM_production["tra-veh"], DM_production["lfs"].copy(),
                                                      CDM_const["material-decomposition_pipe"], CDM_const["material-decomposition_floor"], CDM_const["material-decomposition_domapp"],
                                                      CDM_const["material-decomposition_infra"], CDM_const["material-decomposition_veh"], CDM_const["material-decomposition_lfs"])
    
    # do material switch (writes in DM_material_demand and DM_input_matswitchimpact)
    DM_input_matswitchimpact = {} # create dict to save material switch that will be used later for environmental impact
    apply_material_switch(DM_material_demand["material-demand"], DM_ots_fts["material-switch"], 
                          CDM_const["material-switch"], DM_input_matswitchimpact)
    
    # get material production
    DM_material_production = material_production(DM_ots_fts['material-efficiency'], DM_ots_fts['material-net-import'], 
                                                 DM_material_demand["material-demand"], DM_fxa["prod"])

    # calibrate material production (writes in DM_material_production)
    if calibration is True:
        calibration_material_production(dm_cal, DM_material_production["bymat"], DM_material_production)
        
    # get end of life
    DM_eol = end_of_life(DM_transport["tra-veh-waste"].filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}), 
                         DM_ots_fts['eol-waste-management'].filter({"Variables" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}),
                         DM_ots_fts['eol-material-recovery'].filter({"Variables" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}),
                         CDM_const["material-decomposition_veh"].filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}),
                         DM_material_production["bymat"])
        
    # get material production by technology (writes in DM_material_production)
    DM_material_production["bytech"] = material_production_by_technology(DM_ots_fts['technology-share'], 
                                                                         DM_material_production["bymat"].copy(),
                                                                         DM_eol["material-recovered"])
    
    # get energy demand for material production
    DM_energy_demand = energy_demand(DM_material_production["bytech"], CDM_const)
    
    # calibrate energy demand for material production (writes in DM_energy_demand)
    if calibration is True:
        calibration_energy_demand(dm_cal, DM_energy_demand["bycarr"], DM_energy_demand["bytechcarr"], DM_energy_demand)
        
    # compute energy demand for material production after taking into account technology development (writes in DM_energy_demand)
    technology_development(DM_ots_fts['technology-development'], DM_energy_demand["bytechcarr"])
    
    # do energy switch (writes in DM_energy_demand["bytechcarr"])
    apply_energy_switch(DM_ots_fts['energy-carrier-mix'], DM_energy_demand["bytechcarr"])
    
    # compute specific energy demands that will be used for tpe (writes in DM_energy_demand)
    add_specific_energy_demands(DM_fxa["liquid"], DM_energy_demand["bytechcarr"], 
                                DM_energy_demand["feedstock_bytechcarr"], DM_energy_demand)
    
    # get emissions
    DM_emissions = emissions(CDM_const["emission-factor-process"], CDM_const["emission-factor"], 
                             DM_energy_demand["bytechcarr"], DM_material_production["bytech"])
    
    # compute captured carbon (writes in DM_emissions)
    carbon_capture(DM_ots_fts['cc'], DM_emissions["bygastech"], DM_emissions["combustion_bio"], 
                   DM_emissions)
    
    # calibrate emissions (writes in DM_emissions)
    if calibration is True:
        calibration_emissions(dm_cal, DM_emissions["bygas"], 
                              DM_emissions["bygastech"], DM_emissions)
    
    # comute specific groups of emissions that will be used for tpe (writes in DM_emissions)
    DM_emissions["bygasmat"] = sum_over_techs(dm = DM_emissions["bygastech"], category_with_techs = "Categories2")
    DM_emissions["bygasmat"].rename_col("tra","tra-equip","Categories2")
        
    # TODO: the code below on stock and flows will be moved to minerals or tpe
    # # do stock and flows of materials
    # material_flows(DM_transport["tra-stock-veh"].filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}), 
    #                DM_eol["material-towaste"], DM_eol["material-recovered"],
    #                CDM_const["material-decomposition_veh"].filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']}),
    #                DM_emissions["bygasmat"])

    # get costs (capex and opex) for material production and carbon catpure
    DM_cost = compute_costs(DM_fxa["cost-matprod"], DM_fxa["cost-CC"], 
                            DM_material_production["bytech"], DM_emissions["capt_w_cc_bytech"])
    
    # get variables for tpe (also writes in DM_cost, dm_bld_matswitch_savings_bymat, DM_emissions and DM_material_production for renaming)
    df = variables_for_tpe(DM_cost["material-production_capex"], DM_cost["CO2-capt-w-cc_capex"], 
                           DM_emissions["bygas"], DM_material_production["bytech"], 
                           DM_material_production["bymat"], DM_energy_demand["bymat"],
                           DM_energy_demand["bymatcarr"], DM_energy_demand["bioener"])
    
    # interface agriculture
    DM_agr = industry_agriculture_interface(DM_material_production, DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='agriculture', dm=DM_agr)
    
    # interface ammonia
    DM_amm = industry_ammonia_interface(DM_material_production, DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='ammonia', dm=DM_amm)
    
    # interface landuse
    DM_lus = industry_landuse_interface(DM_material_production, DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='land-use', dm=DM_lus)
    
    # interface power
    DM_pow = industry_power_interface(DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='power', dm=DM_pow)
    
    # interface refinery
    dm_refinery = industry_refinery_interface(DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='oil-refinery', dm=dm_refinery)
    
    # interface district heating
    dm_dh = industry_district_heating_interface(DM_energy_demand)
    interface.add_link(from_sector='industry', to_sector='district-heating', dm=dm_dh)
    
    # interface emissions
    dm_ems = industry_emissions_interface(DM_emissions)
    interface.add_link(from_sector='industry', to_sector='emissions', dm=dm_ems)
    
    # # interface water
    # dm_water = industry_water_inferface(DM_energy_demand, DM_material_production)
    # interface.add_link(from_sector='industry', to_sector='water', dm=dm_water)
    
    # # interface ccus
    # dm_ccus = industry_ccus_interface(DM_emissions)
    # interface.add_link(from_sector='industry', to_sector='ccus', dm=dm_ccus)
    
    # # interface gtap
    # dm_gtap = industry_gtap_interface(DM_energy_demand, DM_material_production)
    # interface.add_link(from_sector='industry', to_sector='gtap', dm=dm_gtap)
    
    # # interface minerals
    # DM_ind = industry_minerals_interface(DM_material_production, DM_production, DM_ots_fts)
    # interface.add_link(from_sector='industry', to_sector='minerals', dm=DM_ind)
    
    # # interface employment
    # dm_emp = industry_employment_interface(DM_material_demand, DM_energy_demand, DM_material_production, DM_cost, DM_ots_fts)
    # interface.add_link(from_sector='industry', to_sector='employment', dm=dm_emp)
    
    # # interface air pollution
    # dm_airpoll = industry_airpollution_interface(DM_material_production, DM_energy_demand)
    # interface.add_link(from_sector='industry', to_sector='air-pollution', dm=dm_airpoll)
    
    # return
    return df
    
def local_industry_run():
    
    # get years and lever setting
    years_setting = [1990, 2015, 2050, 5]
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
    lever_setting = json.load(f)[0]
    # lever_setting["lever_energy-carrier-mix"] = 3
    # lever_setting["lever_cc"] = 3
    # lever_setting["lever_material-switch"] = 3
    # lever_setting["lever_technology-share"] = 4
    
    # get geoscale
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    # run
    results_run = industry(lever_setting, years_setting)
    
    # return
    return results_run

# run local
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/industry_module_new.py"
# database_from_csv_to_datamatrix()
start = time.time()
results_run = local_industry_run()
end = time.time()
print(end-start)
