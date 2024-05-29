
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 26 14:29:08 2024

@author: echiarot
"""

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_database_to_ots_fts_dict, read_level_data, simulate_input, get_mindec, calibration_rates, cost
import pickle
import json
import os
import numpy as np
import re
import warnings
warnings.simplefilter("ignore")

def material_switch_ammonia(dm, dm_ots_fts, cdm_const, material_in, material_out, product, switch_percentage_prefix, switch_ratio_prefix, dict_for_output = None):
    
    # note that this function overwrites directly into the dm. dm should be set as dm_matdec
    # dict_for_output is a dictionary where the function saves variables that will be used later for material switch impact in emissions
    
    # get name of materials in-to-out
    material_in_to_out = [material_in + "-to-" + i for i in material_out]
    
    # if one of the materials out is not in data, create it
    idx_matindata = [i in dm.col_labels["Categories2"] for i in material_out]
    if not all(idx_matindata):
        dm.add(np.nan, dim = "Categories2", col_label = np.array(material_out)[[not i for i in idx_matindata]].tolist(), dummy = True)
        dm.sort("Categories2")
    
    # get material in and material out
    dm_temp = dm.filter({"Categories1" : [product]})
    dm_temp = dm_temp.filter({"Categories2" : [material_in] + material_out})
    
    # get switch percentages
    dm_temp2 = dm_ots_fts.filter({"Categories1" : [switch_percentage_prefix + i for i in material_in_to_out]})
    
    # get switch ratios
    dm_temp3 = cdm_const.filter({"Variables" : [switch_ratio_prefix + i for i in material_in_to_out]})
    
    # get materials out
    idx = dm.idx
    idx_temp = dm_temp.idx
    idx_temp2 = dm_temp2.idx
    idx_temp3 = dm_temp3.idx
    for i in range(len(material_out)):
        
        # get material in-to-out
        arr_temp = dm_temp.array[:,:,:,:,idx_temp[material_in]] * \
            dm_temp2.array[:,:,:,idx_temp2[switch_percentage_prefix + material_in_to_out[i]],np.newaxis]
        dm_temp.add(arr_temp, dim = "Categories2", col_label = material_in_to_out[i])
        dm_temp.add(arr_temp * -1, dim = "Categories2", col_label = material_in_to_out[i] + "_minus")
        
        # get material in-to-out-times-switch-ratio
        arr_temp = dm_temp.array[:,:,:,:,idx_temp[material_in_to_out[i]]] * \
            dm_temp3.array[idx_temp3[switch_ratio_prefix + material_in_to_out[i]]]
        dm_temp.add(arr_temp, dim = "Categories2", col_label = material_in_to_out[i] + "_times_ratio")
        
        # get material out
        if idx_matindata[i]:
            dm_temp4 = dm_temp.filter({"Categories2" : [material_out[i], material_in_to_out[i] + "_times_ratio"]})
            dm.array[:,:,:,idx[product],idx[material_out[i]]] = np.nansum(dm_temp4.array[:,:,0,:,:], axis = -1)
        else:
            dm_temp4 = dm_temp.filter({"Categories2" : [material_in_to_out[i] + "_times_ratio"]})
            dm.array[:,:,:,idx[product],idx[material_out[i]]] = dm_temp4.array[:,:,0,0,:]
        
    # get material in and write
    dm_temp4 = dm_temp.filter({"Categories2" : [material_in] + [i + "_minus" for i in material_in_to_out]})
    dm.array[:,:,:,idx[product],idx[material_in]] = np.nansum(dm_temp4.array[:,:,0,:,:], axis = -1)
    
    # get material in-to-out and write
    if dict_for_output is not None:
        dict_for_output[product + "_" + material_in_to_out[0]] = dm_temp.filter({"Categories2" : material_in_to_out})

def energy_switch_ammonia(dm_energy_demand, dm_energy_carrier_mix, carrier_in, carrier_out, dm_energy_carrier_mix_prefix):
    
    # get carriers
    carrier_all = dm_energy_demand.col_labels["Categories2"]
    carrier_in_exclude = np.array(carrier_all)[[i not in carrier_in for i in carrier_all]].tolist()
    
    # for all material-technologies, get energy demand for all carriers but carrier out and excluded ones
    dm_temp1 = dm_energy_demand.filter_w_regex({"Categories2" : "^((?!" + "|".join(carrier_in_exclude) + ").)*$"})
    
    # get percentages of energy switched to carrier out for each of material-technology
    dm_temp2 = dm_energy_carrier_mix.filter_w_regex({"Categories2" : ".*" + dm_energy_carrier_mix_prefix})
    
    # for all material-technologies, get additional demand for carrier out for each energy carrier
    names = dm_temp1.col_labels["Categories2"]
    for i in names:
        dm_temp1.rename_col(i, i + "_total", "Categories2")
    dm_temp1.deepen()
    dm_temp1.add(dm_temp1.array, dim = "Categories3", col_label = dm_energy_carrier_mix_prefix)
    idx_temp1 = dm_temp1.idx
    dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] = \
        dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] * dm_temp2.array
    
    # get total carrier out switched
    dm_temp3 = dm_temp1.group_all(dim='Categories2', inplace = False)
    dm_temp3.drop("Categories2", "total")
    
    # sum this additional demand for carrier out due to switch to carrier-out demand
    dm_temp3.append(dm_energy_demand.filter({"Categories2" : [carrier_out]}), "Categories2")
    idx = dm_energy_demand.idx
    dm_energy_demand.array[:,:,:,:,idx[carrier_out]] = np.nansum(dm_temp3.array, axis = -1)
    
    # for each energy carrier, subtract additional demand for carrier out due to switch
    dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] = \
        dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] * -1 # this is to do minus with np.nansum
    dm_temp1.add(np.nansum(dm_temp1.array, axis = -1, keepdims=True), dim = "Categories3", col_label = "final")
    dm_temp1.drop("Categories3", ['total', dm_energy_carrier_mix_prefix])
    dm_temp1 = dm_temp1.flatten()
    dm_temp1.rename_col_regex(str1 = "_final", str2 = "", dim = "Categories2")
    drops = dm_temp1.col_labels["Categories2"]
    dm_energy_demand.drop("Categories2", drops)
    dm_energy_demand.append(dm_temp1, "Categories2")
    dm_energy_demand.sort("Categories2")
    
def rename_tech_ammonia(word):
    last = "-".join([word.split("_")[-2], word.split("_")[-1]])
    first = "_".join(word.split("_")[0:-2])
    word_new = first + "_" + last
    return word_new

def rename_tech_fordeepen_ammonia(word):
    first = word.split("-")[0]
    last = word.split("-")[1:]
    if len(last) > 1:
        last = ["-".join(last)]
    word_new = first + "_" + last[0]
    return word_new

def sum_over_techs_ammonia(dm, category_with_techs, 
                   material_tech_multi = ['aluminium-prim', 'aluminium-sec', 'cement-dry-kiln', 
                                          'cement-geopolym', 'cement-wet-kiln', 'paper-recycled', 
                                          'paper-woodpulp', 'steel-BF-BOF', 'steel-hisarna', 
                                          'steel-hydrog-DRI', 'steel-scrap-EAF'],
                   material_tech_single = ['chem-chem-tech', 'copper-tech', 'fbt-tech', 'glass-glass', 
                                           'lime-lime', 'mae-tech', 'ois-tech','textiles-tech', 
                                           'tra-equip-tech', 'wwp-tech']):

    if material_tech_multi is not None:
        # activity with different techs
        dm_out = dm.filter({category_with_techs : material_tech_multi})
        variables_new = [rename_tech_fordeepen_ammonia(i) for i in material_tech_multi]
        for i in range(len(material_tech_multi)):
            dm_out.rename_col(material_tech_multi[i], variables_new[i], category_with_techs)
        dm_out.deepen(based_on = category_with_techs)
        category_last = np.array(dm_out.dim_labels)[-1]
        dm_out.group_all(category_last, inplace = True)
    
    # append the other activities
    dm_out_sub = dm.filter({category_with_techs : material_tech_single})
    variables_new = [re.split("-", i)[0] for i in material_tech_single]
    for i in range(len(material_tech_single)):
        dm_out_sub.rename_col(material_tech_single[i], variables_new[i], category_with_techs)
    if material_tech_multi is not None:
        dm_out.append(dm_out_sub, category_with_techs)
    else:
        dm_out = dm_out_sub
    dm_out.sort(category_with_techs)
    
    # return
    return dm_out

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

    # Read fixed assumptions to datamatrix
    df = read_database_fxa('industry_fixed-assumptions') # weird warning as there seems to be no repeated lines
    dm_ind = DataMatrix.create_from_df(df, num_cat=0)

    df = read_database_fxa('costs_fixed-assumptions') # weird warning as there seems to be no repeated lines
    dm_cost = DataMatrix.create_from_df(df, num_cat=0)

    # Keep only ots and fts years
    dm_ind = dm_ind.filter(selected_cols={'Years': years_all})

    # save
    dm_liquid = dm_ind.filter({"Variables" : ['amm_liquid-ff-oil_diesel', 'amm_liquid-ff-oil_fuel-oil', 
                                          'ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
    dm_prod = dm_ind.filter({"Variables" : ['ind_prod_fbt', 'ind_prod_mae', 'ind_prod_ois', 'ind_prod_textiles', 
                                        'ind_prod_tra-equip', 'ind_prod_wwp']})

    # TODO: put dm_cal in here
    dict_fxa = {
        'liquid': dm_liquid,
        'prod': dm_prod,
        'cost': dm_cost
    }

    ##################
    ##### LEVERS #####
    ##################

    dict_ots = {}
    dict_fts = {}

    # material switch
    file = 'industry_material-switch'
    lever = 'material-switch'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # material efficiency
    file = 'industry_material-efficiency'
    lever = "material-efficiency"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # technology share, technology development and carbon capture (CC)
    levers = ["technology-share", "technology-development", "cc"]
    for lever in levers:
        
        # get ots and fts
        file = 'industry_' + lever
        df_ots, df_fts = read_database(file, lever, level='all')
        
        # get current variables names
        variabs = df_ots.columns
        variabs_ots_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
        variabs = df_fts.columns
        variabs_fts_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
        
        # after prefix, substitute _ with -
        variabs = [i.split(lever + '_')[1] for i in variabs_ots_old]
        variabs = [i.replace("_","-") for i in variabs]
        
        # rename variables
        variabs_ots_new = ["ots_ind_" + lever + "_" + i for i in variabs]
        variabs_fts_new = ["fts_ind_" + lever + "_" + i for i in variabs]
        for i in range(len(variabs_ots_new)):
            df_ots.rename(columns={variabs_ots_old[i]: variabs_ots_new[i]}, inplace=True)
            df_fts.rename(columns={variabs_fts_old[i]: variabs_fts_new[i]}, inplace=True)
        
        # load
        dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                            years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                            df_ots=df_ots, df_fts=df_fts)

    # material net import
    file = 'industry_material-net-import'
    lever = "material-net-import"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # product net import
    file = 'industry_product-net-import'
    lever = "product-net-import"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # energy carrier mix import
    file = 'industry_energy-carrier-mix'
    lever = "energy-carrier-mix"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    #######################
    ##### CALIBRATION #####
    #######################

    # Read calibration
    df = read_database_fxa('industry_calibration')
    dm_cal = DataMatrix.create_from_df(df, num_cat=0)

    #####################
    ##### CONSTANTS #####
    #####################

    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_tec_|cp_cost-ind', num_cat=0)

    ################
    ##### SAVE #####
    ################

    DM_industry = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        'calibration': dm_cal,
        "constant" : cdm_const
    }


    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/industry.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_industry, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # clean
    del baseyear, df, df_fts, df_ots, dict_fts, dict_fxa, dict_ots, dm_cost, dm_ind, dm_cal, DM_industry,\
        dm_liquid, dm_prod, f, file, handle, i, lastyear, lever, levers, startyear, step_fts, variabs, variabs_fts_old,\
        variabs_fts_new, variabs_ots_new, variabs_ots_old, years_all, years_fts, years_ots, years_setting, cdm_const
        
    return

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
    cdm_const = DM_industry['constant']
    cdm_const.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")

    # clean
    del handle, DM_industry, data_file, lever_setting
    
    # return
    return DM_fxa, DM_ots_fts, dm_cal, cdm_const

def product_demand(DM_interface):
    
    dm_demand_agr = DM_interface["agriculture"]
    dm_demand_agr.rename_col_regex(str1 = "agr_", str2 = "agr_product-demand_", dim = "Variables")
    dm_demand_agr.deepen()
    DM_demand = {"agr" : dm_demand_agr}
    del dm_demand_agr
        
    # return
    return DM_demand

def product_import(DM_ots_fts):
    
    dm_imp = DM_ots_fts["product-net-import"].copy()
    dm_imp = dm_imp.filter({"Variables" : ["ind_product-net-import"], "Categories1" : ["fertilizer"]})
    
    # return
    return dm_imp

def product_production(DM_demand, dm_imp):
    
    # production [%] = 1 - net import
    dm_prod = dm_imp.copy()
    arr_temp = dm_prod.array
    arr_temp[arr_temp > 1] = 1
    arr_temp = 1 - arr_temp
    dm_prod.array = arr_temp
    dm_prod.rename_col(col_in = "ind_product-net-import", col_out = "ind_product-production", dim = "Variables")
    DM_production = {"agr" : dm_prod}
    del dm_prod, arr_temp
        
    # return
    return DM_production

def material_decomposition(DM_production, cdm_const):
    
    # material production [t] = product production [unit] * material decomposition coefficient [t/unit]

    dm_temp = DM_production["agr"]
    cdm_temp = cdm_const.filter_w_regex({"Variables":".*fert.*"})
    cdm_temp.deepen_twice()
    dm_fert_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)
    dm_fert_matdec = dm_fert_matdec.filter({"Categories2" : ["ammonia"]})
    DM_material_demand = {"material-demand" : dm_fert_matdec}

    del dm_temp, cdm_temp, dm_fert_matdec
    
    return DM_material_demand

def material_production(DM_fxa, DM_ots_fts, DM_material_demand):
    
    # get aggregate demand
    dm_matdec_agg = DM_material_demand["material-demand"].group_all(dim='Categories1', inplace=False)
    dm_matdec_agg.array = dm_matdec_agg.array * 0.001
    dm_matdec_agg.units["mineral-decomposition"] = "kt"
    
    # efficiency
    dm_temp = DM_ots_fts['material-efficiency'].copy()
    dm_temp.filter({"Variables" : ['ind_material-efficiency']}, inplace = True)
    dm_temp.filter({"Categories1" : ["ammonia"]}, inplace = True)
    dm_matdec_agg.array = dm_matdec_agg.array * (1 - dm_temp.array)

    # material production [kt] = material demand [kt] * (1 - material net import [%])

    # get net import % and make production %
    dm_temp = DM_ots_fts['material-net-import'].copy()
    dm_temp.filter({"Categories1" : ["ammonia"]}, inplace = True)
    dm_temp.array = 1 - dm_temp.array

    # get material production
    dm_material_production_bymat = dm_matdec_agg.copy()
    dm_material_production_bymat.array = dm_matdec_agg.array * dm_temp.array
    dm_material_production_bymat.rename_col(col_in = 'mineral-decomposition', col_out = 'material-production', dim = "Variables")
    
    DM_material_production = {"bymat" : dm_material_production_bymat}

    del dm_material_production_bymat, dm_matdec_agg, dm_temp

    # return
    return DM_material_production

def calibration_material_production(dm_cal, DM_material_production):
    
    # get calibration series
    dm_cal_sub = dm_cal.copy()
    dm_cal_sub.deepen()
    dm_cal_sub.filter({"Categories1" : ["ammonia"]}, inplace = True)
    dm_cal_sub.filter({"Variables" : ['cal_ind_production-calibration']}, inplace = True)

    # get calibration rates
    DM_material_production["calib_rates_bymat"] = calibration_rates(dm = DM_material_production["bymat"], dm_cal = dm_cal_sub)

    # do calibration
    DM_material_production["bymat"].array = DM_material_production["bymat"].array * DM_material_production["calib_rates_bymat"].array

    del dm_cal_sub
    
    return

def material_production_by_technology(DM_ots_fts, DM_material_production):
    
    # this is by material-technology

    # get tech share
    dm_temp = DM_ots_fts['technology-share'].copy()
    dm_temp = dm_temp.filter({"Categories1" : ['ammonia-amm-tech']})

    # create dm_material_production_bytech
    dm_material_production_bytech = DM_material_production["bymat"].copy()

    # get material production by technology
    dm_material_production_bytech.array = dm_material_production_bytech.array * dm_temp.array
    dm_material_production_bytech.array = dm_material_production_bytech.array * 0.001
    dm_material_production_bytech.units["material-production"] = "Mt"
    dm_material_production_bytech.rename_col("ammonia","ammonia-amm-tech","Categories1")
    DM_material_production["bytech"] = dm_material_production_bytech

    del dm_temp, dm_material_production_bytech
    
    # return
    return

def energy_demand(cdm_const, DM_material_production):
    
    # this is by material-technology and carrier

    # get energy demand for material production by technology both without and with feedstock
    feedstock = ["excl-feedstock", "feedstock"]
    DM_energy_demand = {}

    for f in feedstock:

        # get constants for energy demand for material production by technology
        search = "tec_energy_specific-" + f
        cdm_temp = cdm_const.filter_w_regex({"Variables" : ".*" + search + ".*"})
        cdm_temp.rename_col_regex(str1 = search + "_", str2 = "", dim = "Variables")
        cdm_temp.deepen()
        cdm_temp.rename_col_regex("_", "-", dim = "Variables")
        cdm_temp = cdm_temp.filter({"Variables" : ['ammonia-amm-tech']})
        
        # create dm for energy demand for material production by technology
        names = cdm_temp.col_labels["Variables"]
        for i in names:
            cdm_temp.rename_col(i, "energy-demand-" + f + "_" + i, "Variables")
        cdm_temp.deepen(based_on="Variables")
        cdm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')
        dm_energy_demand = cdm_to_dm(cdm_temp, 
                                     DM_material_production["bytech"].col_labels["Country"], 
                                     DM_material_production["bytech"].col_labels["Years"])
        
        # get energy demand for material production by technology
        dm_energy_demand.array = dm_energy_demand.array * DM_material_production["bytech"].array[...,np.newaxis]
        dm_energy_demand.units["energy-demand-" + f] = "TWh"
        DM_energy_demand[f] = dm_energy_demand

    # get overall energy demand
    dm_energy_demand_temp = DM_energy_demand["excl-feedstock"].copy()
    dm_energy_demand_temp.append(DM_energy_demand["feedstock"], dim = "Variables")
    dm_energy_demand_bytechcarr = DM_energy_demand["excl-feedstock"].copy()
    dm_energy_demand_bytechcarr.array = np.nansum(dm_energy_demand_temp.array, axis = -3, keepdims= True)
    dm_energy_demand_bytechcarr.rename_col(col_in = 'energy-demand-excl-feedstock', col_out = "energy-demand", dim = "Variables")
    dm_energy_demand_feedstock_bytechcarr = DM_energy_demand["feedstock"]

    DM_energy_demand = {"bytechcarr" : dm_energy_demand_bytechcarr, 
                        "feedstock_bytechcarr" : dm_energy_demand_feedstock_bytechcarr}

    del feedstock, search, cdm_temp, f, names, i, dm_energy_demand_temp, dm_energy_demand, \
        dm_energy_demand_bytechcarr, dm_energy_demand_feedstock_bytechcarr

    # return
    return DM_energy_demand
    
def technology_development(DM_ots_fts, DM_energy_demand):
    
    # this is by material-technology and carrier

    # get technology development
    dm_temp = DM_ots_fts['technology-development'].copy()
    dm_temp = dm_temp.filter({"Categories1" : ['ammonia-amm-tech']}) # drop ammonia

    # get energy demand after technology development
    DM_energy_demand["bytechcarr"].array = DM_energy_demand["bytechcarr"].array * (1 - dm_temp.array[...,np.newaxis])

    del dm_temp

    # return
    return


def apply_energy_switch(DM_ots_fts, DM_energy_demand):
    
    # this is by material-technology and carrier

    # energy demand for electricity [TWh] = (energy demand [TWh] * electricity share) + energy demand coming from switch to electricity [TWh]

    # get energy mix
    dm_temp = DM_ots_fts['energy-carrier-mix'].copy()
    dm_temp.rename_col_regex(str1 = "ind_energy-carrier-mix_", str2 = "", dim = "Variables")
    dm_temp.rename_col_regex("_", "-", dim = "Variables")
    dm_temp = dm_temp.filter({"Variables" : ['ammonia-amm-tech']})
    names = dm_temp.col_labels["Variables"]
    for i in names:
        dm_temp.rename_col(i, "energy-mix_" + i, "Variables")
    dm_temp.deepen(based_on="Variables")
    dm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')

    #######################
    ##### ELECTRICITY #####
    #######################

    carrier_in = DM_energy_demand["bytechcarr"].col_labels["Categories2"].copy()
    carrier_in.remove("electricity")
    carrier_in.remove("hydrogen")
    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = carrier_in, carrier_out = "electricity", 
                        dm_energy_carrier_mix_prefix = "to-electricity")

    ####################
    ##### HYDROGEN #####
    ####################

    carrier_in = DM_energy_demand["bytechcarr"].col_labels["Categories2"].copy()
    carrier_in.remove("electricity")
    carrier_in.remove("hydrogen")
    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = carrier_in, carrier_out = "hydrogen", 
                        dm_energy_carrier_mix_prefix = "to-hydrogen")

    ###############
    ##### GAS #####
    ###############

    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = ["solid-ff-coal"], carrier_out = "gas-ff-natural", 
                        dm_energy_carrier_mix_prefix = "solid-to-gas")

    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = ["liquid-ff-oil"], carrier_out = "gas-ff-natural", 
                        dm_energy_carrier_mix_prefix = "liquid-to-gas")


    ###########################
    ##### SYNTHETIC FUELS #####
    ###########################

    # TODO: TO BE DONE (ALSO IN KNIME)

    #####################
    ##### BIO FUELS #####
    #####################

    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = ["solid-ff-coal"], carrier_out = "solid-bio", 
                        dm_energy_carrier_mix_prefix = "to-biomass")

    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = ["liquid-ff-oil"], carrier_out = "liquid-bio", 
                        dm_energy_carrier_mix_prefix = "to-biomass")

    energy_switch_ammonia(dm_energy_demand = DM_energy_demand["bytechcarr"], dm_energy_carrier_mix = dm_temp, 
                        carrier_in = ["gas-ff-natural"], carrier_out = "gas-bio", 
                        dm_energy_carrier_mix_prefix = "to-biomass")

    del dm_temp, names, i, carrier_in

    # return
    return

def add_specific_energy_demands(DM_fxa, DM_energy_demand):
    
    # get demand by material and carrier
    dm_energy_demand_bymatcarr = sum_over_techs_ammonia(dm = DM_energy_demand["bytechcarr"], 
                                                material_tech_multi = None,
                                                material_tech_single = ['ammonia-amm-tech'],
                                                category_with_techs = "Categories1")

    # get demand for biomaterial from feedstock
    DM_energy_demand["feedstock_bytechcarr"].switch_categories_order("Categories1", "Categories2")
    dm_energy_demand_feedstock_bycarr = DM_energy_demand["feedstock_bytechcarr"].group_all("Categories2", inplace = False)
    dm_energy_demand_feedstock_bybiomat = dm_energy_demand_feedstock_bycarr.filter(
        {"Categories1" : ["solid-bio", 'gas-bio', 'liquid-bio']})

    # get demand for industrial waste
    dm_energy_demand_bycarr = DM_energy_demand["bytechcarr"].group_all("Categories1", inplace = False)
    dm_energy_demand_indwaste = dm_energy_demand_bycarr.filter({"Categories1" : ['solid-waste']})

    # get demand for bioenergy solid, bioenergy gas, bioenergy liquid
    dm_energy_demand_bioener_bybiomat = dm_energy_demand_bycarr.filter({"Categories1" : ['solid-bio', 'gas-bio', 'liquid-bio']})
    dm_energy_demand_bioener_bybiomat.rename_col("energy-demand","energy-demand_bioenergy","Variables")
    dm_energy_demand_bioener = dm_energy_demand_bioener_bybiomat.group_all("Categories1", inplace = False)

    # get demand by material
    dm_energy_demand_bymat = dm_energy_demand_bymatcarr.group_all("Categories2", inplace = False)

    # get demand by carrier
    dm_energy_demand_bycarr = dm_energy_demand_bymatcarr.group_all("Categories1", inplace = False)

    # get liquid-ff-oil split between diesel and oil
    dm_temp = DM_fxa["liquid"].filter({"Variables" : ['ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
    idx = dm_energy_demand_bycarr.idx
    dm_temp.array = dm_temp.array * dm_energy_demand_bycarr.array[:,:,:,idx["liquid-ff-oil"]] 
    dm_temp.units['ind_liquid-ff-oil_diesel'] = "TWh"
    dm_temp.units['ind_liquid-ff-oil_fuel-oil'] = "TWh"
    dm_temp.deepen_twice()
    dm_temp = dm_temp.flatten()
    dm_temp.rename_col_regex("ind_","energy-demand","Variables")
    dm_energy_demand_bycarr.append(dm_temp, "Categories1")

    # put in DM
    DM_energy_demand["bymatcarr"] = dm_energy_demand_bymatcarr
    DM_energy_demand["feedstock_bybiomat"] = dm_energy_demand_feedstock_bybiomat
    DM_energy_demand["indwaste"] = dm_energy_demand_indwaste
    DM_energy_demand["bioener_bybiomat"] = dm_energy_demand_bioener_bybiomat
    DM_energy_demand["bioener"] = dm_energy_demand_bioener
    DM_energy_demand["bymat"] = dm_energy_demand_bymat
    DM_energy_demand["bycarr"] = dm_energy_demand_bycarr

    del dm_energy_demand_bymatcarr, dm_energy_demand_feedstock_bybiomat, dm_energy_demand_indwaste, \
        dm_energy_demand_bioener, dm_energy_demand_bymat, dm_energy_demand_bioener_bybiomat, \
        dm_energy_demand_bycarr, dm_temp, idx, dm_energy_demand_feedstock_bycarr


    # return
    return

def emissions(cdm_const, DM_energy_demand, DM_material_production):
    
    # get emission factors
    cdm_temp1 = cdm_const.filter_w_regex({"Variables":".*emission-factor-process.*"})
    cdm_temp2 = cdm_const.filter_w_regex({"Variables":".*emission-factor_.*"})

    # rename emission factors process
    variables = cdm_temp1.col_labels["Variables"]
    variables_new = [rename_tech_ammonia(i) for i in variables]
    for i in range(len(variables)):
        cdm_temp1.rename_col(variables[i], variables_new[i], "Variables")
        
    # deepen
    cdm_temp1.deepen_twice()
    cdm_temp2.deepen_twice()

    # drop synfuel (as for now we do not have demand) and ammonia
    cdm_temp2.drop(dim = "Categories2", col_label = ['gas-synfuel', 'liquid-synfuel'])
    cdm_temp1 = cdm_temp1.filter({"Categories2" : ['ammonia-amm-tech']})

    # emissions = energy demand * emission factor

    # combustion
    dm_emissions_combustion = DM_energy_demand["bytechcarr"].copy()
    dm_emissions_combustion.rename_col('energy-demand', "emissions", "Variables")
    dm_emissions_combustion.units["emissions"] = "Mt"
    names = dm_emissions_combustion.col_labels["Categories1"]
    for i in names:
        dm_emissions_combustion.rename_col(i, "CH4_" + i, "Categories1")
    dm_emissions_combustion.deepen("_", based_on = "Categories1")
    idx = dm_emissions_combustion.idx
    arr_temp = dm_emissions_combustion.array[:,:,:,idx["CH4"],:,:]
    dm_emissions_combustion.add(arr_temp[:,:,:,np.newaxis,:,:], "Categories1", col_label = "CO2")
    dm_emissions_combustion.add(arr_temp[:,:,:,np.newaxis,:,:], "Categories1", col_label = "N20")
    dm_emissions_combustion.array = dm_emissions_combustion.array * \
        cdm_temp2.array[np.newaxis,np.newaxis,:,:,:,np.newaxis]

    # biogenic total
    bio = ['gas-bio','liquid-bio','solid-bio']
    dm_emissions_combustion_bio = dm_emissions_combustion.filter({"Categories2" : bio}, inplace = False)
    dm_emissions_combustion_bio = dm_emissions_combustion_bio.filter({"Categories1" : ["CO2"]}, inplace = False)
    dm_emissions_combustion_bio.group_all("Categories2")
    dm_emissions_combustion_bio.rename_col("emissions", "emissions-biogenic", dim = "Variables")
     
    # process
    dm_emissions_process = DM_material_production["bytech"].copy()
    dm_emissions_process.rename_col('material-production', "emissions-process_CO2", "Variables")
    dm_emissions_process.deepen("_", based_on = "Variables")
    dm_emissions_process.switch_categories_order("Categories1", "Categories2")
    cdm_temp1 = cdm_temp1.filter({"Categories1" : ["CO2"]})
    dm_emissions_process.array = dm_emissions_process.array * cdm_temp1.array[np.newaxis,np.newaxis,...]
    dm_emissions_process.add(0, dim = "Categories1", col_label = "N20", unit = "Mt", dummy = True)
    dm_emissions_process.add(0, dim = "Categories1", col_label = "CH4", unit = "Mt", dummy = True)
    dm_emissions_process.sort("Categories1")
    # TODO: flassing here that in KNIME process emissions have a name typo so in the end they do not sum them, here I sum them, so the number for CO2 ammonia will different slightly between here and KNIME

    # total emissions per technology
    dm_emissions_bygastech = dm_emissions_combustion.group_all("Categories2", inplace = False)
    dm_emissions_bygastech.append(dm_emissions_process, dim = "Variables")
    dm_emissions_bygastech.add(np.nansum(dm_emissions_bygastech.array, -3, keepdims=True), 
                           dim = "Variables", col_label = "emissions-total", unit = "Mt")
    dm_emissions_bygastech.drop("Variables", ['emissions', 'emissions-process'])
    dm_emissions_bygastech.rename_col("emissions-total","emissions", "Variables")

    # put in dict
    DM_emissions = {"bygastech" : dm_emissions_bygastech,
                    "combustion_bio" : dm_emissions_combustion_bio}

    del cdm_temp1, cdm_temp2, variables, arr_temp, i, idx, names, variables_new, bio, \
        dm_emissions_bygastech, dm_emissions_combustion_bio, dm_emissions_process, \
        dm_emissions_combustion
    
    # return
    return DM_emissions

def carbon_capture(DM_ots_fts, DM_emissions):
    
    # get carbon capture
    dm_temp = DM_ots_fts['cc'].copy()
    dm_temp = dm_temp.filter({"Categories1" : ['ammonia-amm-tech']})

    # subtract carbon captured to total CO2 emissions per technology
    idx = DM_emissions["bygastech"].idx
    arr_temp = DM_emissions["bygastech"].array[:,:,:,idx["CO2"],:] * (1 - dm_temp.array)
    DM_emissions["bygastech"].add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "after-cc")

    # get emissions captured with carbon capture
    idx = DM_emissions["bygastech"].idx
    arr_temp = DM_emissions["bygastech"].array[:,:,:,idx["CO2"],:] - DM_emissions["bygastech"].array[:,:,:,idx["after-cc"],:]
    DM_emissions["bygastech"].add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "CO2-capt-w-cc")
    dm_emissions_capt_w_cc_bytech = DM_emissions["bygastech"].filter({"Categories1" : ['CO2-capt-w-cc']})
    dm_emissions_capt_w_cc_bytech = dm_emissions_capt_w_cc_bytech.flatten()
    dm_emissions_capt_w_cc_bytech.rename_col_regex("CO2-capt-w-cc_", "", dim = "Categories1")
    dm_emissions_capt_w_cc_bytech.rename_col('emissions', "CO2-capt-w-cc", "Variables")
    DM_emissions["bygastech"].drop("Categories1", "CO2")
    DM_emissions["bygastech"].rename_col(col_in = 'after-cc', col_out = "CO2", dim = "Categories1")
    DM_emissions["bygastech"].sort("Categories1")

    # do the same for biogenic emissions
    keep = ['ammonia-amm-tech']
    dm_emissions_combustion_bio_capt_w_cc = DM_emissions["combustion_bio"].filter({"Categories2" : keep})
    dm_temp1 = dm_temp.filter({"Categories1" : keep})
    idx = dm_emissions_combustion_bio_capt_w_cc.idx
    arr_temp = dm_emissions_combustion_bio_capt_w_cc.array[:,:,:,idx["CO2"],:] * (1 - dm_temp1.array)
    dm_emissions_combustion_bio_capt_w_cc.add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "after-cc")
    idx = dm_emissions_combustion_bio_capt_w_cc.idx
    arr_temp = dm_emissions_combustion_bio_capt_w_cc.array[:,:,:,idx["CO2"],:] - \
        dm_emissions_combustion_bio_capt_w_cc.array[:,:,:,idx["after-cc"],:]
    dm_emissions_combustion_bio_capt_w_cc.add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "capt-w-cc")
    dm_emissions_combustion_bio_capt_w_cc.drop("Categories1", "CO2")
    dm_emissions_combustion_bio_capt_w_cc.drop("Categories1", "after-cc")
    dm_emissions_combustion_bio_capt_w_cc.rename_col(col_in = 'capt-w-cc', col_out = "CO2-capt-w-cc", dim = "Categories1")

    # sum these captured biogenic emissions across materials
    keep_new = ['ammonia_amm-tech']
    for i in range(len(keep)):
        dm_emissions_combustion_bio_capt_w_cc.rename_col(keep[i], keep_new[i], dim = "Categories2")
    dm_emissions_combustion_bio_capt_w_cc.deepen()
    dm_emissions_combustion_bio_capt_w_cc.group_all("Categories3")

    # make negative biogenic emissions to supply to the climate module
    dm_emissions_combustion_bio_capt_w_cc_neg_bymat = dm_emissions_combustion_bio_capt_w_cc.copy()
    dm_emissions_combustion_bio_capt_w_cc_neg_bymat.array = dm_emissions_combustion_bio_capt_w_cc_neg_bymat.array * -1
    dm_emissions_combustion_bio_capt_w_cc_neg_bymat.rename_col("emissions-biogenic", "emissions-biogenic-negative", "Variables")

    # store
    DM_emissions["combustion_bio_capt_w_cc_neg_bymat"] = dm_emissions_combustion_bio_capt_w_cc_neg_bymat
    DM_emissions["capt_w_cc_bytech"] = dm_emissions_capt_w_cc_bytech

    del arr_temp, dm_emissions_combustion_bio_capt_w_cc, \
        dm_temp, dm_temp1, i, idx, keep, keep_new, dm_emissions_combustion_bio_capt_w_cc_neg_bymat, \
        dm_emissions_capt_w_cc_bytech
        
    # return
    return

def add_specific_emissions(DM_emissions):
    
    # get aggregate emissions
    DM_emissions["bygas"] = DM_emissions["bygastech"].group_all("Categories2", inplace = False)
    
    # emissions with different techs
    DM_emissions["bygasmat"] = sum_over_techs_ammonia(dm = DM_emissions["bygastech"], 
                                              material_tech_multi = None, 
                                              material_tech_single = ['ammonia-amm-tech'], 
                                              category_with_techs = "Categories2")

    # return
    return 

def compute_costs(cdm_const, DM_fxa, DM_material_production, DM_emissions):
    
    # get unit costs constants
    cdm_cost = cdm_const.filter_w_regex({"Variables" : ".*cost-ind.*$"})
    cdm_cost.rename_col_regex("_productive-assets", "", dim = "Variables")
    cdm_cost.rename_col_regex("cost-ind_", "", dim = "Variables")
    variables = cdm_cost.col_labels["Variables"]
    keep = np.array(variables)[[bool(re.search("amm-tech", i)) for i in variables]].tolist()
    cdm_cost = cdm_cost.filter({"Variables" : keep})
    issues = ['capex-baseyear_amm-tech', 'capex-d-factor_amm-tech', 'evolution-method_amm-tech', 
              'opex-baseyear_amm-tech', 'opex-d-factor_amm-tech']
    correct = ['capex-baseyear_ammonia_amm-tech', 'capex-d-factor_ammonia_amm-tech', 'evolution-method_ammonia_amm-tech', 
              'opex-baseyear_ammonia_amm-tech', 'opex-d-factor_ammonia_amm-tech']
    for i in range(len(issues)):
        cdm_cost.rename_col(issues[i], correct[i], "Variables")

    # rename emission factors process
    variables = cdm_cost.col_labels["Variables"]
    variables_new = [rename_tech_ammonia(i) for i in variables]
    for i in range(len(variables)):
        cdm_cost.rename_col(variables[i], variables_new[i], "Variables")

    # get price index
    dm_price_index = DM_fxa['cost'].copy()

    ###############################
    ##### MATERIAL PRODUCTION #####
    ###############################

    # subset cdm and deepen
    cdm_cost_sub = cdm_cost.filter_w_regex({"Variables" : "^((?!CC).)*$"})
    cdm_cost_sub.deepen()

    # get material production by technology
    variables = DM_material_production["bytech"].col_labels["Categories1"]
    keep = np.array(variables)[[i in cdm_cost_sub.col_labels["Categories1"] for i in variables]].tolist()
    dm_material_techshare_sub = DM_material_production["bytech"].filter({"Categories1" : keep})
    dm_material_techshare_sub.array = dm_material_techshare_sub.array * 1000
    dm_material_techshare_sub.units["material-production"] = "kt"

    # get costs
    dm_material_techshare_sub_capex = cost(dm_activity = dm_material_techshare_sub, cdm_cost = cdm_cost_sub, 
                                           dm_price_index = dm_price_index, cost_type = "capex")

    dm_material_techshare_sub_opex = cost(dm_activity = dm_material_techshare_sub, cdm_cost = cdm_cost_sub, 
                                          dm_price_index = dm_price_index, cost_type = "opex")


    ######################################
    ##### EMISSIONS CAPTURED WITH CC #####
    ######################################

    # subset cdm and deepen
    cdm_cost_sub = cdm_cost.filter_w_regex({"Variables" : ".*CC.*"})
    cdm_cost_sub.rename_col_regex("CC_", "", dim = "Variables")
    cdm_cost_sub.deepen()

    # get emissions captured with carbon capture
    variables = DM_emissions["capt_w_cc_bytech"].col_labels["Categories1"]
    keep = np.array(variables)[[i in cdm_cost_sub.col_labels["Categories1"] for i in variables]].tolist()
    dm_emissions_capt_w_cc_sub = DM_emissions["capt_w_cc_bytech"].filter({"Categories1" : keep})
    dm_emissions_capt_w_cc_sub.array = dm_emissions_capt_w_cc_sub.array * 1000000
    dm_emissions_capt_w_cc_sub.units["CO2-capt-w-cc"] = "t"

    # get costs
    dm_emissions_capt_w_cc_sub_capex = cost(dm_activity = dm_emissions_capt_w_cc_sub, cdm_cost = cdm_cost_sub, 
                                                  dm_price_index = dm_price_index, cost_type = "capex")
    dm_emissions_capt_w_cc_sub_opex = cost(dm_activity = dm_emissions_capt_w_cc_sub, cdm_cost = cdm_cost_sub, 
                                                 dm_price_index = dm_price_index, cost_type = "opex")

    ########################
    ##### PUT TOGETHER #####
    ########################

    DM_cost = {"material-production_capex" : dm_material_techshare_sub_capex, 
               "material-production_opex" : dm_material_techshare_sub_opex,
               "CO2-capt-w-cc_capex" : dm_emissions_capt_w_cc_sub_capex,
               "CO2-capt-w-cc_opex" : dm_emissions_capt_w_cc_sub_opex}

    for key in DM_cost.keys():
        
        dm_temp1 = DM_cost[key]
        
        # put values before 2015 as nas
        idx = dm_temp1.idx
        years_na = np.array(range(1990,2015,1))
        dm_temp1.array[:,[idx[y] for y in years_na],...] = np.nan

    del cdm_cost, cdm_cost_sub, dm_emissions_capt_w_cc_sub, dm_emissions_capt_w_cc_sub_capex, \
        dm_emissions_capt_w_cc_sub_opex, dm_material_techshare_sub, dm_material_techshare_sub_capex, \
        dm_material_techshare_sub_opex, dm_price_index, dm_temp1, i, keep, key, \
        variables, variables_new, idx, years_na, correct, issues


    # return
    return DM_cost

def variables_for_tpe(DM_cost, DM_emissions, DM_material_production, DM_energy_demand):
    
    # adjust variables' names
    DM_cost["material-production_capex"].rename_col_regex("capex", "investment", "Variables")
    DM_cost["material-production_capex"].rename_col('ammonia-amm-tech','amm-tech',"Categories1")
    DM_cost["CO2-capt-w-cc_capex"].rename_col_regex("capex", "investment_CC", "Variables")
    DM_cost["CO2-capt-w-cc_capex"].rename_col_regex("ammonia-amm-tech", "amm-tech", "Categories1")
    DM_cost["material-production_opex"].rename_col_regex("opex", "operating-costs", "Variables")
    DM_cost["material-production_opex"].rename_col('ammonia-amm-tech','amm-tech',"Categories1")
    DM_cost["CO2-capt-w-cc_opex"].rename_col_regex("opex", "operating-costs_CC", "Variables")
    DM_cost["CO2-capt-w-cc_opex"].rename_col_regex("ammonia-amm-tech", "amm-tech", "Categories1")
    DM_emissions["bygas"] = DM_emissions["bygas"].flatten()
    DM_emissions["bygas"].rename_col_regex("_","-","Variables")
    variables = DM_material_production["bytech"].col_labels["Categories1"]
    variables_new = [rename_tech_fordeepen_ammonia(i) for i in variables]
    for i in range(len(variables)):
        DM_material_production["bytech"].rename_col(variables[i], variables_new[i], dim = "Categories1")
    DM_material_production["bymat"].array = DM_material_production["bymat"].array / 1000
    DM_material_production["bymat"].units["material-production"] = "Mt"

    # dm_tpe
    dm_tpe = DM_emissions["bygas"].copy()
    dm_tpe.append(DM_energy_demand["bymat"].flatten(), "Variables")
    dm_tpe.append(DM_energy_demand["bycarr"].flatten(), "Variables")
    dm_tpe.append(DM_cost["CO2-capt-w-cc_capex"].filter({"Variables" : ["investment_CC"]}).flatten(), "Variables")
    dm_tpe.append(DM_cost["material-production_capex"].filter({"Variables" : ["investment"]}).flatten(), "Variables")
    dm_tpe.append(DM_cost["CO2-capt-w-cc_opex"].filter({"Variables" : ["operating-costs_CC"]}).flatten(), "Variables")
    dm_tpe.append(DM_cost["material-production_opex"].filter({"Variables" : ["operating-costs"]}).flatten(), "Variables")
    dm_tpe.append(DM_material_production["bymat"].flatten(), "Variables")
    variables = dm_tpe.col_labels["Variables"]
    for i in variables:
        dm_tpe.rename_col(i, "amm_" + i, "Variables")
    variables = ['amm_investment_CC_amm-tech', 'amm_investment_amm-tech', 
                 'amm_operating-costs_CC_amm-tech', 'amm_operating-costs_amm-tech']
    variables_new = ['ind_investment_CC_amm-tech', 'ind_investment_amm-tech', 
                     'ind_operating-costs_CC_amm-tech', 'ind_operating-costs_amm-tech']
    for i in range(len(variables)):
        dm_tpe.rename_col(variables[i], variables_new[i], "Variables")
    dm_tpe.sort("Variables")

    # df_tpe
    df_tpe = dm_tpe.write_df()

    del dm_tpe, i, variables, variables_new
    
    # return
    return df_tpe

def ammonia_energy_interface(DM_energy_demand, write_xls = False):
    
    # dm_elc
    dm_elc = DM_energy_demand["bycarr"].filter(
        {"Categories1" : ['liquid-ff-oil_diesel', 'liquid-ff-oil_fuel-oil', 'electricity',
                          'gas-ff-natural', 'hydrogen', 'solid-ff-coal']})
    dm_elc.rename_col("energy-demand", "amm_energy-demand", "Variables")
    dm_elc = dm_elc.flatten()
    dm_elc.sort("Variables")

    # df_elc
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        dm_elc = dm_elc.write_df()
        dm_elc.to_excel(current_file_directory + "/../_database/data/xls/" + 'ammonia-to-electricity_supply.xlsx', index=False)
        
    # return
    return dm_elc

def ammonia_water_inferface(DM_energy_demand, DM_material_production, write_xls = False):
    
    # dm_water
    dm_water = DM_energy_demand["bycarr"].filter(
        {"Categories1" : ['electricity', 'gas-ff-natural', 'hydrogen', 'liquid-ff-oil', 
                          'solid-ff-coal']}).flatten()
    DM_material_production["bytech"].rename_col("ammonia_amm-tech","ammonia","Categories1")
    dm_water.append(DM_material_production["bytech"].flatten(), "Variables")
    variables = dm_water.col_labels["Variables"]
    for i in variables:
        dm_water.rename_col(i, "amm_" + i, "Variables")
    dm_water.sort("Variables")

    # df_water
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_water = dm_water.write_df()
        df_water.to_excel(current_file_directory + "/../_database/data/xls/" + 'ammonia-to-water.xlsx', index=False)

    # return
    return dm_water

def ammonia_ccus_interface(DM_emissions, write_xls = False):
    
    # adjust variables' names
    variables = DM_emissions["capt_w_cc_bytech"].col_labels["Categories1"]
    variables_new = [rename_tech_fordeepen_ammonia(i) for i in variables]
    for i in range(len(variables)):
        DM_emissions["capt_w_cc_bytech"].rename_col(variables[i], variables_new[i], dim = "Categories1")
    DM_emissions["capt_w_cc_bytech"].rename_col('CO2-capt-w-cc','ind_CO2-emissions-CC',"Variables")

    # dm_ccus
    dm_ccus = DM_emissions["capt_w_cc_bytech"].flatten()
    dm_ccus.sort("Variables")

    # df_ccus
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_ccus = dm_ccus.write_df()
        df_ccus.to_excel(current_file_directory + "/../_database/data/xls/" + 'ammonia-to-ccus.xlsx', index=False)
        
    # return
    return dm_ccus

def ammonia_climate_interface(DM_emissions, write_xls = False):
    
    # adjust variables' names
    dm_temp = DM_emissions["bygasmat"].flatten().flatten()
    dm_temp.deepen()
    dm_temp.rename_col_regex("_","-","Variables")

    # dm_cli
    dm_cli = dm_temp.flatten()
    variables = dm_cli.col_labels["Variables"]
    for i in variables:
        dm_cli.rename_col(i, "amm_" + i, "Variables")
    dm_cli.sort("Variables")

    # write
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_cli = dm_cli.write_df()
        df_cli.to_excel(current_file_directory + "/../_database/data/xls/" + 'ammonia-to-climate.xlsx', index=False)

    # return
    return dm_cli

def ammonia_airpollution_interface(DM_material_production, DM_energy_demand, write_xls = False):
    
    # dm_airpoll
    dm_airpoll = DM_material_production["bytech"].flatten()
    dm_airpoll.append(DM_energy_demand["bymatcarr"].flatten().flatten(), "Variables")
    variables = dm_airpoll.col_labels["Variables"]
    for i in variables:
        dm_airpoll.rename_col(i, "amm_" + i, "Variables")
    dm_airpoll.sort("Variables")

    # write
    if write_xls is True:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        df_airpoll = dm_airpoll.write_df()
        df_airpoll.to_excel(current_file_directory + "/../_database/data/xls/" + 'ammonia-to-air_pollution.xlsx', index=False)
        
    # return
    return dm_airpoll

def ammonia(lever_setting, years_setting, interface = Interface(), calibration = True):
    
    # industry data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    industry_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/industry.pickle')
    DM_fxa, DM_ots_fts, dm_cal, cdm_const = read_data(industry_data_file, lever_setting)
    
    # get / simulate interfaces
    DM_interface = {}
    from_sector = ['agriculture', 'transport', 'lifestyles', 'buildings']
    for i in from_sector:
        if interface.has_link(from_sector = i, to_sector = 'industry'):
            DM_interface[i] = interface.get_link(from_sector=i, to_sector='industry')
        else:
            DM_interface[i] = simulate_input(from_sector=i, to_sector="industry")
    del from_sector, i
    
    # get product demand
    DM_demand = product_demand(DM_interface)
    
    # get product import
    dm_imp = product_import(DM_ots_fts)
    
    # get product production
    DM_production = product_production(DM_demand, dm_imp)
    
    # get material demand
    DM_material_demand = material_decomposition(DM_production, cdm_const)
    
    # get material production
    DM_material_production = material_production(DM_fxa, DM_ots_fts, DM_material_demand)

    # calibrate material production (writes in DM_material_production)
    if calibration is True:
        calibration_material_production(dm_cal, DM_material_production)
        
    # get material production by technology (writes in DM_material_production)
    material_production_by_technology(DM_ots_fts, DM_material_production)
    
    # get energy demand for material production
    DM_energy_demand = energy_demand(cdm_const, DM_material_production)
    
    # TODO: there is no calibration of energy demand for ammonia at the moment, check later if this is fine
        
    # compute energy demand for material production after taking into account technology development (writes in DM_energy_demand)
    technology_development(DM_ots_fts, DM_energy_demand)
    
    # do energy switch (writes in DM_energy_demand)
    apply_energy_switch(DM_ots_fts, DM_energy_demand)
    
    # compute specific energy demands that will be used for tpe (writes in DM_energy_demand)
    add_specific_energy_demands(DM_fxa, DM_energy_demand)
    
    # get emissions
    DM_emissions = emissions(cdm_const, DM_energy_demand, DM_material_production)
    
    # compute captured carbon (writes in DM_emissions)
    carbon_capture(DM_ots_fts, DM_emissions)
    
    # TODO: there is no calibration of energy demand for ammonia at the moment, to see if to do it at some point
    
    # comute specific groups of emissions that will be used for tpe (writes in DM_emissions)
    add_specific_emissions(DM_emissions)
        
    # get costs (capex and opex) for material production and carbon catpure
    DM_cost = compute_costs(cdm_const, DM_fxa, DM_material_production, DM_emissions)
    
    # get variables for tpe (also writes in DM_cost, DM_emissions and DM_material_production for renaming)
    df = variables_for_tpe(DM_cost, DM_emissions, DM_material_production, DM_energy_demand)
    
    # interface energy
    dm_energy = ammonia_energy_interface(DM_energy_demand)
    interface.add_link(from_sector='ammonia', to_sector='energy', dm=dm_energy)
    
    # interface water
    dm_water = ammonia_water_inferface(DM_energy_demand, DM_material_production)
    interface.add_link(from_sector='ammonia', to_sector='water', dm=dm_water)
    
    # interface ccus
    dm_ccus = ammonia_ccus_interface(DM_emissions)
    interface.add_link(from_sector='ammonia', to_sector='ccus', dm=dm_ccus)
    
    # interface climate
    dm_cli = ammonia_climate_interface(DM_emissions)
    interface.add_link(from_sector='ammonia', to_sector='climate', dm=dm_cli)
    
    # interface air pollution
    dm_airpoll = ammonia_airpollution_interface(DM_material_production, DM_energy_demand)
    interface.add_link(from_sector='ammonia', to_sector='air-pollution', dm=dm_airpoll)
    
    # return
    return(df)
    
def local_ammonia_run():
    
    # get years and lever setting
    years_setting = [1990, 2015, 2050, 5]
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
    lever_setting = json.load(f)[0]
    # lever_setting["lever_energy-carrier-mix"] = 3
    # lever_setting["lever_cc"] = 3
    # lever_setting["lever_material-switch"] = 3
    
    # get geoscale
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    # run
    results_run = ammonia(lever_setting, years_setting)
    
    # return
    return results_run

# # run local
# __file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/industry_module.py"
# # database_from_csv_to_datamatrix()
# results_run = local_ammonia_run()
