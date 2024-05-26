#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 12 10:37:22 2024

@author: echiarot
"""

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, update_database_from_db
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_database_to_ots_fts_dict, read_level_data, simulate_input, get_mindec, calibration_rates, cost
import pandas as pd
import pickle
import json
import os
import numpy as np
import re
import warnings
warnings.simplefilter("ignore")

__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/training/industry_module_notebook.py"

def material_switch(dm, material_in, material_out, product, switch_percentage_prefix, switch_ratio_prefix, dict_for_output = None):
    
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
    dm_temp2 = DM_ots_fts["material-switch"].filter({"Categories1" : [switch_percentage_prefix + i for i in material_in_to_out]})
    
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

def energy_switch(dm_energy_demand, dm_energy_carrier_mix, carrier_in, carrier_out, dm_energy_carrier_mix_prefix):
    
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
    
def rename_tech(word):
    last = "-".join([word.split("_")[-2], word.split("_")[-1]])
    first = "_".join(word.split("_")[0:-2])
    word_new = first + "_" + last
    return word_new

def rename_tech_fordeepen(word):
    first = word.split("-")[0]
    last = word.split("-")[1:]
    if len(last) > 1:
        last = ["-".join(last)]
    word_new = first + "_" + last[0]
    return word_new

def sum_over_techs(dm, category_with_techs, 
                   material_tech_multi = ['aluminium-prim', 'aluminium-sec', 'cement-dry-kiln', 
                                          'cement-geopolym', 'cement-wet-kiln', 'paper-recycled', 
                                          'paper-woodpulp', 'steel-BF-BOF', 'steel-hisarna', 
                                          'steel-hydrog-DRI', 'steel-scrap-EAF'],
                   material_tech_single = ['chem-chem-tech', 'copper-tech', 'fbt-tech', 'glass-glass', 
                                           'lime-lime', 'mae-tech', 'ois-tech','textiles-tech', 
                                           'tra-equip-tech', 'wwp-tech']):

    # activity with different techs
    dm_out = dm.filter({category_with_techs : material_tech_multi})
    variables_new = [rename_tech_fordeepen(i) for i in material_tech_multi]
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
    dm_out.append(dm_out_sub, category_with_techs)
    dm_out.sort(category_with_techs)
    
    # return
    return dm_out

# ############################################################
# #################### CREATE DATA PICKLE ####################
# ############################################################

# # Read database

# # Set years range
# years_setting = [1990, 2015, 2050, 5]
# startyear = years_setting[0]
# baseyear = years_setting[1]
# lastyear = years_setting[2]
# step_fts = years_setting[3]
# years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) # make list with years from 1990 to 2015
# years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int)) # make list with years from 2020 to 2050 (steps of 5 years)
# years_all = years_ots + years_fts

# #############################
# ##### FIXED ASSUMPTIONS #####
# #############################

# # =============================================================================
# # # here below the code to make fxa for price index to be used for costs, delete at the end
# # 
# # current_file_directory = os.path.dirname(os.path.abspath(__file__))
# # xls_directory = os.path.join(current_file_directory, "../_database/data/xls")
# # files = np.array(os.listdir(xls_directory))
# # file = files[[bool(re.search("costs" + "-to-" + "industry", str(i))) for i in files]].tolist()[0]
# # xls_file_directory = xls_directory +  "/" + file
# # df = pd.read_excel(xls_file_directory)
# # 
# # index = ["Country","Years"]
# # df1 = df.loc[df["Country"] != "EU28",:]
# # df1 = df1.loc[:,index + ["ots_tec_price-indices_pli[%]"]]
# # df1 = pd.melt(df1, id_vars = index)
# # df1 = df1.rename(columns={"Country": "geoscale", "Years": "timescale", "variable" : "eucalc-name"})
# # df1["eucalc-name"] = "cost_price-indices_pli[%]"
# # df1["module"] = "cost"
# # df1["element"] = "price-indices"
# # df1["item"] = "pli"
# # df1["unit"] = "%"
# # df1["lever"] = "none"
# # df1["level"] = 0
# # df1["string-pivot"] = "none"
# # df1["type-prefix"] = "none"
# # df1["module-prefix"] = "cost"
# # df1["reference-id"] = "missing-reference"
# # df1["interaction-file"] = "cost_fixed-assumptions"
# # 
# # df1 = df1.loc[:,['geoscale', "timescale", "module", "eucalc-name", "lever", "level", "string-pivot",
# #                  "type-prefix", "module-prefix", "element", "item", "unit", "value", "reference-id", 
# #                  "interaction-file"]]
# # 
# # filepath = os.path.join(current_file_directory, '../_database/data/csv/costs_fixed-assumptions.csv')
# # df1.to_csv(filepath, sep = ";", index = False)
# # =============================================================================

# # Read fixed assumptions to datamatrix
# df = read_database_fxa('industry_fixed-assumptions') # weird warning as there seems to be no repeated lines
# dm_ind = DataMatrix.create_from_df(df, num_cat=0)

# df = read_database_fxa('costs_fixed-assumptions') # weird warning as there seems to be no repeated lines
# dm_cost = DataMatrix.create_from_df(df, num_cat=0)

# # df[df.duplicated()]
# # A = pd.DataFrame({'isin' : df.groupby('Country')['amm_liquid-ff-oil_diesel[%]'].agg(len).index, 
# #                    'variab' : df.groupby('Country')['amm_liquid-ff-oil_diesel[%]'].agg(len).values
# #                   })
# # A = A[A['variab']>33]

# # Keep only ots and fts years
# dm_ind = dm_ind.filter(selected_cols={'Years': years_all})

# # save
# dm_liquid = dm_ind.filter({"Variables" : ['amm_liquid-ff-oil_diesel', 'amm_liquid-ff-oil_fuel-oil', 
#                                       'ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
# dm_prod = dm_ind.filter({"Variables" : ['ind_prod_fbt', 'ind_prod_mae', 'ind_prod_ois', 'ind_prod_textiles', 
#                                     'ind_prod_tra-equip', 'ind_prod_wwp']})

# dict_fxa = {
#     'liquid': dm_liquid,
#     'prod': dm_prod,
#     'cost': dm_cost
# }

# ##################
# ##### LEVERS #####
# ##################

# dict_ots = {}
# dict_fts = {}

# # levers = ["material-switch","material-efficiency","technology-share",
# #           "technology-development","material-net-import","product-net-import",
# #           "energy-carrier-mix","carbon-capture"]
# # files = ["industry_" + i for i in levers]

# # # material switch
# # for i in range(len(levers)):
# #     file = files[i]
# #     lever = levers[i]
# #     dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
# #                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # material switch
# file = 'industry_material-switch'
# lever = 'material-switch'
# dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                     years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # material efficiency
# file = 'industry_material-efficiency'
# lever = "material-efficiency"
# dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                     years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # carbon capture (run just once, delete this chunk the end)
# # filename = 'industry_cc'
# # filename = filename.replace('.csv', '')  # drop .csv extension
# # current_file_directory = os.path.dirname(os.path.abspath(__file__))
# # folderpath = os.path.join(current_file_directory, "../_database/data/csv/")
# # file = folderpath + filename + '.csv'
# # df_db = pd.read_csv(file, sep=";")
# # variables = ["eucalc-name","lever","item","interaction-file"]
# # for v in variables:
# #     df_db[v] = [df_db[v][i].replace("CC","cc") for i in range(len(df_db))]
# # df_db.to_csv(file, sep=";", index=False)

# # technology share, technology development and carbon capture (CC)
# levers = ["technology-share", "technology-development", "cc"]
# for lever in levers:
    
#     # get ots and fts
#     file = 'industry_' + lever
#     df_ots, df_fts = read_database(file, lever, level='all')
    
#     # get current variables names
#     variabs = df_ots.columns
#     variabs_ots_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
#     variabs = df_fts.columns
#     variabs_fts_old = variabs[[i not in ['Country', 'Years', lever] for i in variabs]].tolist()
    
#     # after prefix, substitute _ with -
#     variabs = [i.split(lever + '_')[1] for i in variabs_ots_old]
#     variabs = [i.replace("_","-") for i in variabs]
    
#     # rename variables
#     variabs_ots_new = ["ots_ind_" + lever + "_" + i for i in variabs]
#     variabs_fts_new = ["fts_ind_" + lever + "_" + i for i in variabs]
#     for i in range(len(variabs_ots_new)):
#         df_ots.rename(columns={variabs_ots_old[i]: variabs_ots_new[i]}, inplace=True)
#         df_fts.rename(columns={variabs_fts_old[i]: variabs_fts_new[i]}, inplace=True)
    
#     # load
#     dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                         years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
#                                                         df_ots=df_ots, df_fts=df_fts)

# # material net import
# file = 'industry_material-net-import'
# lever = "material-net-import"
# dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                     years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # product net import
# file = 'industry_product-net-import'
# lever = "product-net-import"
# dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                     years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# # energy carrier mix import
# file = 'industry_energy-carrier-mix'
# lever = "energy-carrier-mix"
# dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
#                                                     years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

# #######################
# ##### CALIBRATION #####
# #######################

# # Read calibration
# df = read_database_fxa('industry_calibration')
# dm_cal = DataMatrix.create_from_df(df, num_cat=0)

# #####################
# ##### CONSTANTS #####
# #####################

# # =============================================================================
# # # here below the code to make interface technology to industry as constants, delete at the end
# # 
# # current_file_directory = os.path.dirname(os.path.abspath(__file__))
# # xls_directory = os.path.join(current_file_directory, "../_database/data/xls")
# # files = np.array(os.listdir(xls_directory))
# # file = files[[bool(re.search("technology" + "-to-" + "industry", str(i))) for i in files]].tolist()[0]
# # xls_file_directory = xls_directory +  "/" + file
# # df = pd.read_excel(xls_file_directory)
# # drops = [True] + [type(df.iloc[:,i].tolist()[0]) != str for i in range(1, len(df.columns))]
# # df = df.loc[:,drops]
# # 
# # variabs = df.iloc[0,1:len(df.columns)].index.tolist()
# # for i in range(6):
# #     variabs[i] = "tec_" + variabs[i]
# # element = [i.split("_")[1] for i in variabs]
# # item = [i.split("_")[2:] for i in variabs]
# # item = ["_".join(i) for i in item]
# # item = [i.split("[")[0] for i in item]
# # unit = [i.split("[")[1] for i in variabs]
# # unit = [i.split("]")[0] for i in unit]
# # 
# # df1 = pd.DataFrame({'geoscale' : "constant",
# #                     "timescale" : "constant",
# #                     "module" : "technology",
# #                     "eucalc-name" : ["cp_" + i for i in variabs],
# #                     "lever" : "none",
# #                     "level" : 0,
# #                     "string-pivot" : "none",
# #                     "type-prefix" : "cp",
# #                     "module-prefix" : "tec",
# #                     "element" : element,
# #                     "item" : item,
# #                     "unit" : unit,
# #                     "value" : df.iloc[0,1:len(df.columns)].values,
# #                     "reference-id" : "missing-reference",
# #                     "interaction-file" : "interactions_constants"})
# # 
# # filepath = os.path.join(current_file_directory, '../_database/data/csv/technology_constants.csv')
# # df1.to_csv(filepath, sep = ";", index = False)
# # folderpath = os.path.join(current_file_directory, '../_database/data/csv/')
# # update_database_from_db(filename = 'interactions_constants', db_new = df1, folderpath=folderpath)
# # =============================================================================

# # =============================================================================
# # # here below the code to make interface technology to industry for costs as constants, delete at the end
# # 
# # # filename = 'interactions_constants'
# # # filename = filename.replace('.csv', '')  # drop .csv extension
# # # current_file_directory = os.path.dirname(os.path.abspath(__file__))
# # # folderpath = os.path.join(current_file_directory, "../_database/data/csv/")
# # # file = folderpath + filename + '.csv'
# # # df_conts = pd.read_csv(file, sep=";")
# # 
# # current_file_directory = os.path.dirname(os.path.abspath(__file__))
# # xls_directory = os.path.join(current_file_directory, "../_database/data/xls")
# # files = np.array(os.listdir(xls_directory))
# # file = files[[bool(re.search("costs" + "-to-" + "industry", str(i))) for i in files]].tolist()[0]
# # xls_file_directory = xls_directory +  "/" + file
# # df = pd.read_excel(xls_file_directory)
# # 
# # index = ["sector", "technology_code","cost_classification","capex_unit","opex_unit"]
# # df1 = df.loc[df["Country"] == "EU28",:]
# # df1 = df1.loc[:,["capex_b_factor", "capex_d_factor", "capex_baseyear",
# #                  "opex_b_factor", "opex_d_factor", "opex_baseyear", "evolution_method"] + index]
# # df1 = pd.melt(df1, id_vars = index)
# # df1["cost_classification"] = [i.replace(" ", "-") for i in df1["cost_classification"].values.tolist()]
# # df1 = df1.dropna(subset=["value"])
# # 
# # df1["geoscale"] = "constant"
# # df1["timescale"] = "constant"
# # df1["module"] = "cost"
# # df1["element"] = df1["variable"]
# # df1["element"] = [i.replace("_", "-") for i in df1["element"].values.tolist()]
# # df1["item"] = df1["technology_code"] + "_" + df1["cost_classification"]
# # 
# # df1["unit"] = "num"
# # df1.loc[df1["element"] == "capex-baseyear","unit"] = "EUR/" + df1.loc[df1["element"] == "capex-baseyear","capex_unit"]
# # df1.loc[df1["element"] == "opex-baseyear","unit"] = "EUR/" + df1.loc[df1["element"] == "opex-baseyear","opex_unit"]
# # 
# # df1["eucalc-name"] = "cp_cost-" + df1["sector"] + "_" + df1["element"] + "_" + df1["item"] + "[" + df1["unit"] + "]"
# # df1["lever"] = "none"
# # df1["level"] = 0
# # df1["string-pivot"] = "none"
# # df1["type-prefix"] = "cp"
# # df1["module-prefix"] = "cost-" + df1["sector"]
# # df1["reference-id"] = "missing-reference"
# # df1["interaction-file"] = "interactions_constants"
# # 
# # df1 = df1.drop(index + ["variable"], axis = 1)
# # 
# # df1 = df1.loc[:,['geoscale', "timescale", "module", "eucalc-name", "lever", "level", "string-pivot",
# #                  "type-prefix", "module-prefix", "element", "item", "unit", "value", "reference-id", 
# #                  "interaction-file"]]
# # df1 = df1.sort_values(by=['geoscale', "timescale", "module", "eucalc-name"])
# # 
# # filepath = os.path.join(current_file_directory, '../_database/data/csv/costs_constants.csv')
# # df1.to_csv(filepath, sep = ";", index = False)
# # folderpath = os.path.join(current_file_directory, '../_database/data/csv/')
# # update_database_from_db(filename = 'interactions_constants', db_new = df1, folderpath=folderpath)
# # =============================================================================

# cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_tec_|cp_cost-ind', num_cat=0)

# ################
# ##### SAVE #####
# ################

# DM_industry = {
#     'fxa': dict_fxa,
#     'fts': dict_fts,
#     'ots': dict_ots,
#     'cal': dm_cal,
#     "constant" : cdm_const
# }


# current_file_directory = os.path.dirname(os.path.abspath(__file__))
# f = os.path.join(current_file_directory, '../_database/data/datamatrix/industry.pickle')
# with open(f, 'wb') as handle:
#     pickle.dump(DM_industry, handle, protocol=pickle.HIGHEST_PROTOCOL)

# # clean
# del baseyear, df, df_fts, df_ots, dict_fts, dict_fxa, dict_ots, dm_cost, dm_ind, dm_cal, DM_industry,\
#     dm_liquid, dm_prod, f, file, handle, i, lastyear, lever, levers, startyear, step_fts, variabs, variabs_fts_old,\
#     variabs_fts_new, variabs_ots_new, variabs_ots_old, years_all, years_fts, years_ots, years_setting, cdm_const


###################################################
#################### READ DATA ####################
###################################################

# industry data file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/industry.pickle')

# lever setting
f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
lever_setting = json.load(f)[0]
lever_setting["lever_energy-carrier-mix"] = 3 # REMEMBER TO COMMENT THIS OUT!!!
lever_setting["lever_cc"] = 3 # REMEMBER TO COMMENT THIS OUT!!!
lever_setting["lever_material-switch"] = 3 # REMEMBER TO COMMENT THIS OUT!!!

# load dm
with open(data_file, 'rb') as handle:
    DM_industry = pickle.load(handle)

# get fxa
DM_fxa = DM_industry['fxa']

# Get ots fts based on lever_setting
DM_ots_fts = read_level_data(DM_industry, lever_setting)

# get calibration
dm_cal = DM_industry['cal']

# get constants
cdm_const = DM_industry['constant']
cdm_const.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")

# clean
del handle, f, DM_industry, data_file, lever_setting

#############################################################
#################### SIMULATE INTERFACES ####################
#############################################################

DM_interface = {}

# get interface files
interface = Interface()
from_sector = ['agriculture', 'transport', 'lifestyles', 'buildings']
for i in from_sector:
    if interface.has_link(from_sector = i, to_sector = 'industry'):
        DM_interface[i] = interface.get_link(from_sector=i, to_sector='industry')
    else:
        DM_interface[i] = simulate_input(from_sector=i, to_sector="industry")

del from_sector, i, interface


########################################################
#################### PRODUCT DEMAND ####################
########################################################

#####################
##### BUILDINGS #####
#####################

dm_demand_bld = DM_interface["buildings"]

# rename
dm_demand_bld.rename_col_regex(str1 = "bld_", str2 = "bld_product-demand_", dim = "Variables")
dm_demand_bld.rename_col_regex(str1 = "_new_",str2 = "-new-",dim = "Variables")
dm_demand_bld.rename_col_regex(str1 = "_reno_",str2 = "-reno-",dim = "Variables")
dm_demand_bld.rename_col_regex(str1 = "-new-dhg_pipe",str2 = "_new-dhg-pipe",dim = "Variables")

# deepen
dm_demand_bld.deepen()

# pipes
dm_demand_bld_pipe = dm_demand_bld.filter_w_regex({"Categories1" : ".*pipe"})
dm_demand_bld_pipe.units["bld_product-demand"] = "km"

# floor
dm_demand_bld_floor = dm_demand_bld.filter_w_regex({"Categories1" : ".*floor"})
dm_demand_bld_floor.units["bld_product-demand"] = "m2"

# domestic appliances
dm_demand_bld_domapp = dm_demand_bld.filter({"Categories1" : ['computer', 'dishwasher', 'dryer', 
                                                              'freezer', 'fridge', 'phone',
                                                              'tv', 'wmachine']})
dm_demand_bld_domapp.units["bld_product-demand"] = "num"

#####################
##### TRANSPORT #####
#####################

dm_demand_tra = DM_interface["transport"]

# rename
dm_demand_tra.rename_col_regex(str1 = "tra_", str2 = "tra_product-demand_", dim = "Variables")

# deepen
dm_demand_tra.deepen()

# infra
dm_demand_tra_infra = dm_demand_tra.filter({"Categories1" : ['rail','road','trolley-cables']})
dm_demand_tra_infra.units["tra_product-demand"] = "km"

# vehicules
dm_demand_tra_veh = dm_demand_tra.filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                   'planes', 'ships', 'trains',
                                                   'trucks-EV', 'trucks-FCV', 'trucks-ICE']})
dm_demand_tra_veh.units["tra_product-demand"] = "num"

######################
##### LIFESTYLES #####
######################

dm_demand_lfs = DM_interface["lifestyles"]
dm_demand_lfs.rename_col_regex(str1 = "lfs_", str2 = "lfs_product-demand_", dim = "Variables")
dm_demand_lfs.deepen()

#######################
##### AGRICULTURE #####
#######################

dm_demand_agr = DM_interface["agriculture"]
dm_demand_agr.rename_col_regex(str1 = "agr_", str2 = "agr_product-demand_", dim = "Variables")
dm_demand_agr.deepen()

########################
##### PUT TOGETHER #####
########################

DM_demand = {"bld-pipe" : dm_demand_bld_pipe,
             "bld-floor" : dm_demand_bld_floor,
             "bld-domapp" : dm_demand_bld_domapp,
             "tra-infra" : dm_demand_tra_infra,
             "tra-veh" : dm_demand_tra_veh,
             "lfs" : dm_demand_lfs,
             "agr" : dm_demand_agr}

del dm_demand_agr, dm_demand_bld, dm_demand_bld_domapp, dm_demand_bld_floor, dm_demand_bld_pipe, \
    dm_demand_lfs, dm_demand_tra, dm_demand_tra_infra, dm_demand_tra_veh


########################################################
#################### PRODUCT IMPORT ####################
########################################################

# get product net imports
dm_imp = DM_ots_fts["product-net-import"].copy()

# fix floor area new and reno
dm_temp = dm_imp.filter({"Variables" : ['ind_product-net-import_floor-area_new', 
                                        'ind_product-net-import_floor-area_reno']})
dm_temp = dm_temp.filter({"Categories1" : ['residential',"non-residential"]})
dm_temp = dm_temp.flatten()
dm_temp.rename_col_regex(str1 = "_new_",str2 = "-new-",dim = "Variables")
dm_temp.rename_col_regex(str1 = "_reno_",str2 = "-reno-",dim = "Variables")
dm_temp.deepen()

# fix pipes
dm_temp2 = dm_imp.filter({"Variables" : ['ind_product-net-import_new_dhg']})
dm_temp2 = dm_temp2.filter({"Categories1" : ["pipe"]})
dm_temp2  = dm_temp2 .flatten()
dm_temp2.rename_col_regex(str1 = "_new_",str2 = "_new-",dim = "Variables")
dm_temp2.rename_col_regex(str1 = "_pipe",str2 = "-pipe",dim = "Variables")
dm_temp2.deepen()

# put back in
dm_imp.drop(dim = "Variables", col_label = ['ind_product-net-import_floor-area_new', 
                                            'ind_product-net-import_floor-area_reno',
                                            'ind_product-net-import_new_dhg'])
dm_imp.drop(dim = "Categories1", col_label = ['residential','non-residential','pipe'])
dm_imp.append(dm_temp, dim = "Categories1")
dm_imp.append(dm_temp2, dim = "Categories1")

del dm_temp, dm_temp2

############################################################
#################### PRODUCT PRODUCTION ####################
############################################################

# production [%] = 1 - net import
dm_prod = dm_imp.copy()
idx = dm_prod.idx
arr_temp = dm_prod.array[:,:,idx["ind_product-net-import"],:]
arr_temp[arr_temp > 1] = 1
arr_temp = 1 - arr_temp
dm_prod.array[:,:,idx["ind_product-net-import"],:] = arr_temp
dm_prod.rename_col(col_in = "ind_product-net-import", col_out = "ind_product-production", dim = "Variables")

#####################
##### BUILDINGS #####
#####################

# get production for buildings
dm_prod_bld_pipe = dm_prod.filter({"Categories1" : ['new-dhg-pipe']})
dm_prod_bld_floor = dm_prod.filter_w_regex({"Categories1": "floor-area"})
dm_prod_bld_domapp = dm_prod.filter({"Categories1" : ['computer', 'dishwasher', 'dryer', 
                                                      'freezer', 'fridge', 'phone',
                                                      'tv', 'wmachine']})

# get demand for buildings
dm_demand_bld_pipe = DM_demand["bld-pipe"]
dm_demand_bld_floor = DM_demand["bld-floor"]
dm_demand_bld_domapp = DM_demand["bld-domapp"]

# production (units) = demand * production [%]

# pipes
dm_prod_bld_pipe.array = dm_prod_bld_pipe.array * dm_demand_bld_pipe.array
dm_prod_bld_pipe.units["ind_product-production"] = dm_demand_bld_pipe.units["bld_product-demand"]

# floor
dm_prod_bld_floor.sort("Categories1")
dm_demand_bld_floor.sort("Categories1")
dm_prod_bld_floor.array = dm_prod_bld_floor.array * dm_demand_bld_floor.array
dm_prod_bld_floor.units["ind_product-production"] = dm_demand_bld_floor.units["bld_product-demand"]

# domestic appliances
dm_prod_bld_domapp.sort("Categories1")
dm_demand_bld_domapp.sort("Categories1")
dm_prod_bld_domapp.array = dm_prod_bld_domapp.array * dm_demand_bld_domapp.array
dm_prod_bld_domapp.units["ind_product-production"] = dm_demand_bld_domapp.units["bld_product-demand"]


#####################
##### TRANSPORT #####
#####################

# get production for transport
dm_prod_tra_infra = dm_prod.filter({"Categories1" : ['rail','road','trolley-cables']})
dm_prod_tra_veh = dm_prod.filter({"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                   'planes', 'ships', 'trains',
                                                   'trucks-EV', 'trucks-FCV', 'trucks-ICE']})

# get demand for transport
dm_demand_tra_infra = DM_demand["tra-infra"]
dm_demand_tra_veh = DM_demand["tra-veh"]

# production (units) = demand * production [%]

# infra
dm_prod_tra_infra.array = dm_prod_tra_infra.array * dm_demand_tra_infra.array
dm_prod_tra_infra.units["ind_product-production"] = dm_demand_tra_infra.units["tra_product-demand"]

# veh
dm_prod_tra_veh.array = dm_prod_tra_veh.array * dm_demand_tra_veh.array
dm_prod_tra_veh.units["ind_product-production"] = dm_demand_tra_veh.units["tra_product-demand"]


######################
##### LIFESTYLES #####
######################

# get production for lifestyles
dm_prod_lfs = dm_prod.filter({"Categories1" : ['aluminium-pack', 'glass-pack', 'paper-pack', 
                                               'paper-print', 'paper-san', 'plast-pack']})

# get demand for transport
dm_demand_lfs = DM_demand["lfs"]

# production (units) = demand * production [%]
dm_prod_lfs.array = dm_prod_lfs.array * dm_demand_lfs.array
dm_prod_lfs.units["ind_product-production"] = dm_demand_lfs.units["lfs_product-demand"]

########################
##### PUT TOGETHER #####
########################

DM_production = {"bld-pipe" : dm_prod_bld_pipe,
                 "bld-floor" : dm_prod_bld_floor,
                 "bld-domapp" : dm_prod_bld_domapp,
                 "tra-infra" : dm_prod_tra_infra,
                 "tra-veh" : dm_prod_tra_veh,
                 "lfs" : dm_prod_lfs}

del arr_temp, dm_demand_bld_domapp, dm_demand_bld_floor, dm_demand_bld_pipe, \
    dm_demand_lfs, dm_demand_tra_infra, dm_demand_tra_veh, dm_prod, idx, \
    dm_prod_bld_pipe, dm_prod_bld_floor, dm_prod_bld_domapp, dm_prod_tra_infra, \
    dm_prod_tra_veh, dm_prod_lfs, dm_imp

################################################################
#################### MATERIAL DECOMPOSITION ####################
################################################################

# material production [t] = product production [unit] * material decomposition coefficient [t/unit]

#####################
##### BUILDINGS #####
#####################

# pipe
dm_temp = DM_production["bld-pipe"]
cdm_temp = cdm_const.filter_w_regex({"Variables":".*pipe.*"})
cdm_temp.rename_col_regex(str1 = "_dhg_",str2 = "-dhg-",dim = "Variables")
cdm_temp.deepen_twice()
dm_bld_pipe_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

# floor
dm_temp = DM_production["bld-floor"]
cdm_temp = cdm_const.filter_w_regex({"Variables":".*floor.*"})
cdm_temp.rename_col_regex(str1 = "_new_",str2 = "-new-",dim = "Variables")
cdm_temp.rename_col_regex(str1 = "_reno_",str2 = "-reno-",dim = "Variables")
cdm_temp.deepen_twice()
dm_bld_floor_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

# domestic appliance
dm_temp = DM_production["bld-domapp"]
cdm_temp = cdm_const.filter_w_regex({"Variables":".*computer.*|.*dishwasher.*|.*dryer.*|.*freezer.*|.*fridge.*|.*phone.*|.*tv.*|.*wmachine.*"})
cdm_temp.deepen_twice()
dm_bld_domapp_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

#####################
##### TRANSPORT #####
#####################

# infra
dm_temp = DM_production["tra-infra"]
cdm_temp = cdm_const.filter_w_regex({"Variables":".*rail.*|.*road.*|.*cable.*"})
cdm_temp.deepen_twice()
dm_tra_infra_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

# veh
dm_temp = DM_production["tra-veh"]
cdm_temp = cdm_const.filter_w_regex({"Variables":".*car.*|.*truck.*|.*plane.*|.*ship.*|.*train.*"})
cdm_temp.deepen_twice()
dm_tra_veh_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

######################
##### LIFESTYLES #####
######################

# lfs
dm_temp = DM_production["lfs"].copy()
cdm_temp = cdm_const.filter_w_regex({"Variables":".*pack.*|.*print.*|.*san.*"})
dm_temp.drop(dim = "Categories1", col_label = ['aluminium-pack']) # note: this should be 100% aluminium, to be seen if they get it back later
cdm_temp.deepen_twice()
dm_lfs_matdec = get_mindec(dm = dm_temp, cdm = cdm_temp)

########################
##### PUT TOGETHER #####
########################

dm_matdec = dm_bld_pipe_matdec
dm_matdec.append(dm_bld_floor_matdec, dim = "Categories1")
dm_matdec.append(dm_bld_domapp_matdec, dim = "Categories1")
dm_matdec.append(dm_tra_infra_matdec, dim = "Categories1")
dm_matdec.append(dm_tra_veh_matdec, dim = "Categories1")
dm_matdec.append(dm_lfs_matdec, dim = "Categories1")

# TODO!: check if it's fine to call this material demand, as it's obtained from production variables
DM_material_demand = {"material-demand" : dm_matdec}
DM_material_demand["material-demand"].drop("Categories2", ["ammonia","other"])

# get material demand for appliances
DM_material_demand["appliances"] = \
    DM_material_demand["material-demand"].filter(
        {"Categories1" : ["computer","dishwasher","dryer",
                          "freezer","fridge","tv"]}).group_all("Categories1", 
                                                               inplace = False)
DM_material_demand["appliances"].rename_col("mineral-decomposition","material-demand_appliances","Variables")

# get material demand for transport
DM_material_demand["transport"] = \
    DM_material_demand["material-demand"].filter(
        {"Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE',
                          'trucks-EV', 'trucks-FCV', 'trucks-ICE',
                          'planes', 'ships', 'trains']}).group_all("Categories1", inplace = False)
DM_material_demand["transport"].rename_col("mineral-decomposition","material-demand_transport","Variables")

# get material demand for construction
DM_material_demand["construction"] = \
    DM_material_demand["material-demand"].filter(
        {"Categories1" : ['floor-area-new-non-residential', 'floor-area-new-residential',
                          'floor-area-reno-non-residential', 'floor-area-reno-residential',
                          'rail', 'road', 'trolley-cables']}).group_all("Categories1", inplace = False)
DM_material_demand["construction"].rename_col("mineral-decomposition","material-demand_construction","Variables")

del dm_temp, cdm_temp, dm_bld_pipe_matdec, dm_bld_floor_matdec, dm_bld_domapp_matdec, \
    dm_tra_infra_matdec, dm_tra_veh_matdec, dm_lfs_matdec


#########################################################
#################### MATERIAL SWITCH ####################
#########################################################

# material in-to-out [t] = material in [t] * in-to-out [%]
# material in [t] = material in [t] - material in-to-out [t]
# material out [t] = material out [t] + material in-to-out [t] * switch ratio [t/t]

# create dict to save material switch that will be used later for environmental impact
DM_input_matswitchimpact = {}

# get index
idx = dm_matdec.idx

#####################
##### TRANSPORT #####
#####################

material_switch(dm = dm_matdec, material_in = "steel", material_out = ["chem","aluminium"], product = "cars-ICE", 
                switch_percentage_prefix = "cars-", switch_ratio_prefix = "tec_material-switch-ratios_")

material_switch(dm = dm_matdec, material_in = "steel", material_out = ["chem","aluminium"], product = "trucks-ICE", 
                switch_percentage_prefix = "trucks-", switch_ratio_prefix = "tec_material-switch-ratios_")

#####################
##### BUILDINGS #####
#####################

# new buildings: switch to renewable materials (steel and cement to timber in new residential and non-residential)

material_switch(dm = dm_matdec, material_in = "steel", material_out = ["timber"], product = 'floor-area-new-residential', 
                switch_percentage_prefix = "build-", switch_ratio_prefix = "tec_material-switch-ratios_",
                dict_for_output = DM_input_matswitchimpact)

material_switch(dm = dm_matdec, material_in = "cement", material_out = ["timber"], product = 'floor-area-new-residential', 
                switch_percentage_prefix = "build-", switch_ratio_prefix = "tec_material-switch-ratios_",
                dict_for_output = DM_input_matswitchimpact)

material_switch(dm = dm_matdec, material_in = "steel", material_out = ["timber"], product = 'floor-area-new-non-residential', 
                switch_percentage_prefix = "build-", switch_ratio_prefix = "tec_material-switch-ratios_",
                dict_for_output = DM_input_matswitchimpact)

material_switch(dm = dm_matdec, material_in = "cement", material_out = ["timber"], product = 'floor-area-new-non-residential', 
                switch_percentage_prefix = "build-", switch_ratio_prefix = "tec_material-switch-ratios_",
                dict_for_output = DM_input_matswitchimpact)

# renovated buildings: switch to insulated surfaces (chemicals to paper and natural fibers in renovated residential and non-residential)

material_switch(dm = dm_matdec, material_in = "chem", material_out = ["paper","natfibers"], product = "floor-area-reno-residential", 
                switch_percentage_prefix = "reno-", switch_ratio_prefix = "tec_material-switch-ratios_")

material_switch(dm = dm_matdec, material_in = "chem", material_out = ["paper","natfibers"], product = "floor-area-reno-non-residential", 
                switch_percentage_prefix = "reno-", switch_ratio_prefix = "tec_material-switch-ratios_")

del idx

#############################################################
#################### MATERIAL PRODUCTION ####################
#############################################################

############################
##### AGGREGATE DEMAND #####
############################

# get aggregate demand
dm_matdec_agg = dm_matdec.group_all(dim='Categories1', inplace=False)
dm_matdec_agg.array = dm_matdec_agg.array * 0.001
dm_matdec_agg.units["mineral-decomposition"] = "kt"
# note: here "other" will be different as in knime they filtered out all "other" but for glass_pack_other

# subset aggregate demand for the materials we keep
materials = ['aluminium','cement', 'chem', 'copper','glass', 'lime','paper', 'steel','timber']
dm_material_production_natfiber = dm_matdec_agg.filter({"Categories1" : ["natfibers"]}) # this will be used for interface agriculture
dm_matdec_agg.filter({"Categories1" : materials}, inplace = True)

######################
##### EFFICIENCY #####
######################

dm_temp = DM_ots_fts['material-efficiency'].copy()
dm_temp.filter({"Variables" : ['ind_material-efficiency']}, inplace = True)
dm_temp.filter({"Categories1" : materials}, inplace = True)
dm_matdec_agg.array = dm_matdec_agg.array * (1 - dm_temp.array)

######################
##### PRODUCTION #####
######################

# material production [kt] = material demand [kt] * (1 - material net import [%])

# get net import % and make production %
dm_temp = DM_ots_fts['material-net-import'].copy()
dm_temp.filter({"Categories1" : materials}, inplace = True)
dm_temp.array = 1 - dm_temp.array

# get material production
dm_material_production_bymat = dm_matdec_agg.copy()
dm_material_production_bymat.array = dm_matdec_agg.array * dm_temp.array
dm_material_production_bymat.rename_col(col_in = 'mineral-decomposition', col_out = 'material-production', dim = "Variables")

# include other industries from fxa
dm_temp = DM_fxa["prod"].copy()
dm_temp.deepen()
dm_temp.rename_col(col_in = 'ind_prod', col_out = 'material-production', dim = "Variables")
dm_temp.units['material-production'] = "kt"
dm_material_production_bymat.append(data2 = dm_temp, dim = "Categories1")
dm_material_production_bymat.sort("Categories1")

del dm_matdec, dm_matdec_agg, dm_temp, materials


#########################################################################
#################### CALIBRATION MATERIAL PRODUCTION ####################
#########################################################################

# get calibration series
dm_cal_sub = dm_cal.copy()
dm_cal_sub.deepen()
materials = dm_material_production_bymat.col_labels["Categories1"]
dm_cal_sub.filter({"Categories1" : materials}, inplace = True)
dm_cal_sub.filter({"Variables" : ['cal_ind_production-calibration']}, inplace = True)

# get calibration rates
dm_material_production_calib_rates_bymat = calibration_rates(dm = dm_material_production_bymat, dm_cal = dm_cal_sub)

# do calibration
dm_material_production_bymat.array = dm_material_production_bymat.array * dm_material_production_calib_rates_bymat.array

del dm_cal_sub, materials


###########################################################################
#################### MATERIAL PRODUCTION BY TECHNOLOGY ####################
###########################################################################

# this is by material-technology

# FIXME!: TECH SHARE DOES NOT HAVE TIMBER (WE SHOULD PROBABLY ADD THE SHARE AS 100%)

# get tech share
dm_temp = DM_ots_fts['technology-share'].copy()
dm_temp.drop(dim = "Categories1", col_label = ['ammonia-amm-tech']) # drop ammonia

# create dm_material_production_bytech
dm_material_production_bytech = dm_material_production_bymat.copy()
dm_material_production_bytech.drop(dim = "Categories1", col_label = ['timber'])
names_present = dm_material_production_bytech.col_labels["Categories1"]
techs = ['aluminium-prim', 'cement-dry-kiln', 'chem-chem-tech', 'copper-tech', 'fbt-tech', 'glass-glass', 'lime-lime', 'mae-tech', 
         'ois-tech', 'paper-recycled', 'steel-BF-BOF', 'textiles-tech', 'tra-equip-tech', 'wwp-tech']
for i in range(len(names_present)):
    dm_material_production_bytech.rename_col(names_present[i], techs[i], dim = "Categories1")

# add missing in Categories1
techs_sub1 = ['aluminium-prim', 'cement-dry-kiln', 'cement-dry-kiln', 'paper-recycled',
              'steel-BF-BOF', 'steel-BF-BOF', 'steel-BF-BOF']
techs_sub2 = ['aluminium-sec', 'cement-geopolym', 'cement-wet-kiln', 'paper-woodpulp',
              'steel-hisarna', 'steel-hydrog-DRI', 'steel-scrap-EAF']
idx = dm_material_production_bytech.idx
for i in range(len(techs_sub1)):
    arr_temp = dm_material_production_bytech.array[:,:,:,idx[techs_sub1[i]]]
    dm_material_production_bytech.add(arr_temp[...,np.newaxis], dim = "Categories1", col_label = techs_sub2[i])
dm_material_production_bytech.sort("Categories1")

# get material production by technology
dm_material_production_bytech.array = dm_material_production_bytech.array * dm_temp.array
dm_material_production_bytech.array = dm_material_production_bytech.array * 0.001
dm_material_production_bytech.units["material-production"] = "Mt"

del dm_temp, techs, i, names_present, techs_sub1, techs_sub2, idx, arr_temp

##########################################################################
#################### PUT TOGETHER MATERIAL PRODUCTION ####################
##########################################################################

DM_material_production = {"bymat" : dm_material_production_bymat, 
                          "calib_rates_bymat" : dm_material_production_calib_rates_bymat,
                          "bytech" : dm_material_production_bytech,
                          "natfiber" : dm_material_production_natfiber}

del dm_material_production_bymat, dm_material_production_calib_rates_bymat, \
    dm_material_production_bytech, dm_material_production_natfiber

###############################################################################
#################### ENERGY DEMAND FOR MATERIAL PRODUCTION ####################
###############################################################################

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
    cdm_temp.drop(dim = "Variables", col_label = ['ammonia-amm-tech'])
    
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

del feedstock, DM_energy_demand, search, cdm_temp, f, names, i, dm_energy_demand_temp, dm_energy_demand


###################################################################
#################### CALIBRATION ENERGY DEMAND ####################
###################################################################

# this is by material-technology and carrier

# aggregate energy demand by energy carrier
dm_energy_demand_bycarr = dm_energy_demand_bytechcarr.group_all(dim='Categories1', inplace=False)

# get calibration series
dm_cal_sub = dm_cal.copy()
dm_cal_sub.deepen()
energy_carriers = dm_energy_demand_bycarr.col_labels["Categories1"]
dm_cal_sub.filter({"Categories1" : energy_carriers}, inplace = True)
dm_cal_sub.filter({"Variables" : ['cal_ind_energy']}, inplace = True)

# exclude switzerland from calibration as all series for Switzerland are 0
# FIXME!: FIX CALIBRATION RATE FOR SWITZERLAND (FOR THE MOMENT SET TO 1). IN KNIME, THE CALIBRATION RATE FOR CH (ALL YEARS) IS THE ONE OF SWEDEN IN 1990. HERE IT'S BEEN CORRECTED DIRECTLY TO 1 (NO CALIBRATION).
dm_energy_demand_agg_sub = dm_energy_demand_bycarr.copy()
dm_energy_demand_agg_sub.drop(dim = "Country", col_label = ['Switzerland'])
dm_cal_sub.drop(dim = "Country", col_label = ['Switzerland'])

# get calibration rates
dm_energy_demand_calib_rates_bycarr = calibration_rates(dm = dm_energy_demand_agg_sub, 
                                                     dm_cal = dm_cal_sub, calibration_start_year = 2000)
dm_energy_demand_calib_rates_bycarr.add(1 , dim = "Country", col_label = "Switzerland", dummy = True)
dm_energy_demand_calib_rates_bycarr.sort("Country")

# FIXME!: before 2000, instead of 1 put the calib rate of 2000 (it's done like this in the KNIME for industry, tbc what to do)
idx = dm_energy_demand_calib_rates_bycarr.idx
years_bef2000 = np.array(range(1990, 2000, 1)).tolist()
for i in years_bef2000:
    dm_energy_demand_calib_rates_bycarr.array[:,idx[i]] = dm_energy_demand_calib_rates_bycarr.array[:,idx[2000]]

# do calibration
dm_energy_demand_bycarr.array = dm_energy_demand_bycarr.array * dm_energy_demand_calib_rates_bycarr.array

# do calibratio for each technology (by applying aggregate calibration rates)
dm_energy_demand_bytechcarr.array = dm_energy_demand_bytechcarr.array * dm_energy_demand_calib_rates_bycarr.array[:,:,:,np.newaxis,:]

del dm_cal_sub, energy_carriers, dm_energy_demand_agg_sub, idx, years_bef2000

################################################################
#################### TECHNOLOGY DEVELOPMENT ####################
################################################################

# this is by material-technology and carrier

# get technology development
dm_temp = DM_ots_fts['technology-development'].copy()
dm_temp.drop(dim = "Categories1", col_label = ['ammonia-amm-tech']) # drop ammonia

# get energy demand after technology development
dm_energy_demand_bytechcarr.array = dm_energy_demand_bytechcarr.array * (1 - dm_temp.array[...,np.newaxis])

del dm_temp

#######################################################
#################### ENERGY SWITCH ####################
#######################################################

# this is by material-technology and carrier

# energy demand for electricity [TWh] = (energy demand [TWh] * electricity share) + energy demand coming from switch to electricity [TWh]

# get energy mix
dm_temp = DM_ots_fts['energy-carrier-mix'].copy()
dm_temp.rename_col_regex(str1 = "ind_energy-carrier-mix_", str2 = "", dim = "Variables")
dm_temp.rename_col_regex("_", "-", dim = "Variables")
dm_temp.drop(dim = "Variables", col_label = ['ammonia-amm-tech'])
names = dm_temp.col_labels["Variables"]
for i in names:
    dm_temp.rename_col(i, "energy-mix_" + i, "Variables")
dm_temp.deepen(based_on="Variables")
dm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')

#######################
##### ELECTRICITY #####
#######################

carrier_in = dm_energy_demand_bytechcarr.col_labels["Categories2"].copy()
carrier_in.remove("electricity")
carrier_in.remove("hydrogen")
energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = carrier_in, carrier_out = "electricity", 
              dm_energy_carrier_mix_prefix = "to-electricity")

####################
##### HYDROGEN #####
####################

carrier_in = dm_energy_demand_bytechcarr.col_labels["Categories2"].copy()
carrier_in.remove("electricity")
carrier_in.remove("hydrogen")
energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = carrier_in, carrier_out = "hydrogen", 
              dm_energy_carrier_mix_prefix = "to-hydrogen")

###############
##### GAS #####
###############

energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = ["solid-ff-coal"], carrier_out = "gas-ff-natural", 
              dm_energy_carrier_mix_prefix = "solid-to-gas")

energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = ["liquid-ff-oil"], carrier_out = "gas-ff-natural", 
              dm_energy_carrier_mix_prefix = "liquid-to-gas")


###########################
##### SYNTHETIC FUELS #####
###########################

# TODO: TO BE DONE (ALSO IN KNIME)

#####################
##### BIO FUELS #####
#####################

energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = ["solid-ff-coal"], carrier_out = "solid-bio", 
              dm_energy_carrier_mix_prefix = "to-biomass")

energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = ["liquid-ff-oil"], carrier_out = "liquid-bio", 
              dm_energy_carrier_mix_prefix = "to-biomass")

energy_switch(dm_energy_demand = dm_energy_demand_bytechcarr, dm_energy_carrier_mix = dm_temp, 
              carrier_in = ["gas-ff-natural"], carrier_out = "gas-bio", 
              dm_energy_carrier_mix_prefix = "to-biomass")

del dm_temp, names, i, carrier_in


####################################################################
#################### PUT TOGETHER ENERGY DEMAND ####################
####################################################################

# get demand by material and carrier
dm_energy_demand_bymatcarr = sum_over_techs(dm = dm_energy_demand_bytechcarr, 
                                            category_with_techs = "Categories1")
dm_energy_demand_bymatcarr.rename_col("tra","tra-equip","Categories1")

# get demand for biomaterial from feedstock
dm_energy_demand_feedstock_bytechcarr.switch_categories_order("Categories1", "Categories2")
dm_energy_demand_feedstock_bycarr = dm_energy_demand_feedstock_bytechcarr.group_all("Categories2", inplace = False)
dm_energy_demand_feedstock_bybiomat = dm_energy_demand_feedstock_bycarr.filter(
    {"Categories1" : ["solid-bio", 'gas-bio', 'liquid-bio']})

# get demand for industrial waste
dm_energy_demand_bycarr = dm_energy_demand_bytechcarr.group_all("Categories1", inplace = False)
dm_energy_demand_indwaste = dm_energy_demand_bycarr.filter({"Categories1" : ['solid-waste']})

# get demand for bioenergy solid, bioenergy gas, bioenergy liquid
dm_energy_demand_bioener_bybiomat = dm_energy_demand_bycarr.filter({"Categories1" : ['solid-bio', 'gas-bio', 'liquid-bio']})
dm_energy_demand_bioener_bybiomat.rename_col("energy-demand","energy-demand-bioenergy","Variables")
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
DM_energy_demand = {"bytechcarr" : dm_energy_demand_bytechcarr, 
                    "bycarr" : dm_energy_demand_bycarr, 
                    "calib_rates_bycarr" : dm_energy_demand_calib_rates_bycarr, 
                    "feedstock_bytechcarr" : dm_energy_demand_feedstock_bytechcarr}
DM_energy_demand["bymatcarr"] = dm_energy_demand_bymatcarr
DM_energy_demand["feedstock_bybiomat"] = dm_energy_demand_feedstock_bybiomat
DM_energy_demand["indwaste"] = dm_energy_demand_indwaste
DM_energy_demand["bioener_bybiomat"] = dm_energy_demand_bioener_bybiomat
DM_energy_demand["bioener"] = dm_energy_demand_bioener
DM_energy_demand["bymat"] = dm_energy_demand_bymat
DM_energy_demand["bycarr"] = dm_energy_demand_bycarr

del dm_energy_demand_bymatcarr, dm_energy_demand_feedstock_bybiomat, dm_energy_demand_indwaste, \
    dm_energy_demand_bioener, dm_energy_demand_bymat, dm_energy_demand_bioener_bybiomat, \
    dm_energy_demand_bycarr, dm_temp, idx, dm_energy_demand_bytechcarr, dm_energy_demand_calib_rates_bycarr, \
    dm_energy_demand_feedstock_bytechcarr, dm_energy_demand_feedstock_bycarr


###################################################
#################### EMISSIONS ####################
###################################################

# get emission factors
cdm_temp1 = cdm_const.filter_w_regex({"Variables":".*emission-factor-process.*"})
cdm_temp2 = cdm_const.filter_w_regex({"Variables":".*emission-factor_.*"})

# rename emission factors process
variables = cdm_temp1.col_labels["Variables"]
variables_new = [rename_tech(i) for i in variables]
for i in range(len(variables)):
    cdm_temp1.rename_col(variables[i], variables_new[i], "Variables")
    
# deepen
cdm_temp1.deepen_twice()
cdm_temp2.deepen_twice()

# drop synfuel (as for now we do not have demand) and ammonia
cdm_temp2.drop(dim = "Categories2", col_label = ['gas-synfuel', 'liquid-synfuel'])
cdm_temp1.drop(dim = "Categories2", col_label = ['ammonia-amm-tech'])

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
dm_emissions_process.rename_col('material-production', "emissions-process_CH4", "Variables")
dm_emissions_process.deepen("_", based_on = "Variables")
dm_emissions_process.switch_categories_order("Categories1", "Categories2")
idx = dm_emissions_process.idx
arr_temp = dm_emissions_process.array[:,:,:,idx["CH4"],:]
dm_emissions_process.add(arr_temp[:,:,:,np.newaxis,:], "Categories1", col_label = "CO2")
dm_emissions_process.add(arr_temp[:,:,:,np.newaxis,:], "Categories1", col_label = "N20")
dm_emissions_process.array = dm_emissions_process.array * cdm_temp1.array[np.newaxis,np.newaxis,...]

# total emissions per technology
dm_emissions_bygastech = dm_emissions_combustion.group_all("Categories2", inplace = False)
dm_emissions_bygastech.append(dm_emissions_process, dim = "Variables")
dm_emissions_bygastech.add(np.nansum(dm_emissions_bygastech.array, -3, keepdims=True), 
                       dim = "Variables", col_label = "emissions-total", unit = "Mt")
dm_emissions_bygastech.drop("Variables", ['emissions', 'emissions-process'])
dm_emissions_bygastech.rename_col("emissions-total","emissions", "Variables")

del cdm_temp1, cdm_temp2, variables, arr_temp, i, idx, names, variables_new, bio


########################################################
#################### CARBON CAPTURE ####################
########################################################

# get carbon capture
dm_temp = DM_ots_fts['cc'].copy()
dm_temp.drop("Categories1", ["ammonia-amm-tech"])

# subtract carbon captured to total CO2 emissions per technology
idx = dm_emissions_bygastech.idx
arr_temp = dm_emissions_bygastech.array[:,:,:,idx["CO2"],:] * (1 - dm_temp.array)
dm_emissions_bygastech.add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "after-cc")

# get emissions captured with carbon capture
idx = dm_emissions_bygastech.idx
arr_temp = dm_emissions_bygastech.array[:,:,:,idx["CO2"],:] - dm_emissions_bygastech.array[:,:,:,idx["after-cc"],:]
dm_emissions_bygastech.add(arr_temp[:,:,:,np.newaxis,:], dim = "Categories1", col_label = "CO2-capt-w-cc")
dm_emissions_capt_w_cc_bytech = dm_emissions_bygastech.filter({"Categories1" : ['CO2-capt-w-cc']})
dm_emissions_capt_w_cc_bytech = dm_emissions_capt_w_cc_bytech.flatten()
dm_emissions_capt_w_cc_bytech.rename_col_regex("CO2-capt-w-cc_", "", dim = "Categories1")
dm_emissions_capt_w_cc_bytech.rename_col('emissions', "CO2-capt-w-cc", "Variables")
dm_emissions_bygastech.drop("Categories1", "CO2")
dm_emissions_bygastech.rename_col(col_in = 'after-cc', col_out = "CO2", dim = "Categories1")
dm_emissions_bygastech.sort("Categories1")

# do the same for biogenic emissions
keep = ['cement-dry-kiln', 'cement-geopolym', 'cement-wet-kiln', 'chem-chem-tech', 'lime-lime',
        'paper-recycled', 'paper-woodpulp', 'steel-BF-BOF', 'steel-hisarna', 
        'steel-hydrog-DRI', 'steel-scrap-EAF',]
dm_emissions_combustion_bio_capt_w_cc = dm_emissions_combustion_bio.filter({"Categories2" : keep})
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
keep_new = ['cement_dry-kiln', 'cement_geopolym', 'cement_wet-kiln', 'chem_chem-tech', 'lime_lime',
            'paper_recycled', 'paper_woodpulp', 'steel_BF-BOF', 'steel_hisarna', 
            'steel_hydrog-DRI', 'steel_scrap-EAF',]
for i in range(len(keep)):
    dm_emissions_combustion_bio_capt_w_cc.rename_col(keep[i], keep_new[i], dim = "Categories2")
dm_temp = dm_emissions_combustion_bio_capt_w_cc.filter({"Categories2" : ['chem_chem-tech', 'lime_lime']})
dm_emissions_combustion_bio_capt_w_cc.drop("Categories2", ['chem_chem-tech', 'lime_lime'])
dm_emissions_combustion_bio_capt_w_cc.deepen()
dm_emissions_combustion_bio_capt_w_cc.group_all("Categories3")
dm_emissions_combustion_bio_capt_w_cc.append(dm_temp, "Categories2")
dm_emissions_combustion_bio_capt_w_cc.rename_col("chem_chem-tech", "chem", "Categories2")
dm_emissions_combustion_bio_capt_w_cc.rename_col("lime_lime", "lime", "Categories2")

# make negative biogenic emissions to supply to the climate module
dm_emissions_combustion_bio_capt_w_cc_neg_bymat = dm_emissions_combustion_bio_capt_w_cc.copy()
dm_emissions_combustion_bio_capt_w_cc_neg_bymat.array = dm_emissions_combustion_bio_capt_w_cc_neg_bymat.array * -1
dm_emissions_combustion_bio_capt_w_cc_neg_bymat.rename_col("emissions-biogenic", "emissions-biogenic-negative", "Variables")

del arr_temp, dm_emissions_combustion, dm_emissions_combustion_bio, dm_emissions_combustion_bio_capt_w_cc, \
    dm_emissions_process, dm_temp, dm_temp1, i, idx, keep, keep_new


###############################################################
#################### CALIBRATION EMISSIONS ####################
###############################################################

# get calibration series
dm_cal_sub = dm_cal.copy()
dm_cal_sub.filter({"Variables" : ['cal_ind_emissions_CH4', 'cal_ind_emissions_CO2', 'cal_ind_emissions_N2O']}, inplace = True)
dm_cal_sub.deepen()

# get aggregate emissions
dm_emissions_bygas = dm_emissions_bygastech.group_all("Categories2", inplace = False)

# get calibration rates
dm_emissions_calib_rates_bygas = calibration_rates(dm = dm_emissions_bygas, dm_cal = dm_cal_sub)

# do calibration
dm_emissions_bygas.array = dm_emissions_bygas.array * dm_emissions_calib_rates_bygas.array

# do calibration for each technology (by applying aggregate calibration rates)
dm_emissions_bygastech.array = dm_emissions_bygastech.array * dm_emissions_calib_rates_bygas.array[:,:,:,:,np.newaxis]

del dm_cal_sub

################################################################
#################### PUT TOGETHER EMISSIONS ####################
################################################################

DM_emissions = {"combustion_bio_capt_w_cc_neg_bymat" : dm_emissions_combustion_bio_capt_w_cc_neg_bymat,
                "bygastech" : dm_emissions_bygastech,
                "bygas" : dm_emissions_bygas,
                "calib_rates_bygas" : dm_emissions_calib_rates_bygas, 
                "capt_w_cc_bytech" : dm_emissions_capt_w_cc_bytech}

# emissions with different techs
dm_emissions_bygasmat = sum_over_techs(dm = DM_emissions["bygastech"], category_with_techs = "Categories2")
DM_emissions["bygasmat"] = dm_emissions_bygasmat
DM_emissions["bygasmat"].rename_col("tra","tra-equip","Categories2")

del dm_emissions_combustion_bio_capt_w_cc_neg_bymat, dm_emissions_bygastech, dm_emissions_bygas, \
    dm_emissions_calib_rates_bygas, dm_emissions_capt_w_cc_bytech, dm_emissions_bygasmat

##############################################################################
#################### MATERIAL-SWITCH IMPACT FOR BUILDINGS ####################
##############################################################################

# from buildings, get steel-to-timber and cement-to-timber
dm_matswitchimpact_bld = DM_input_matswitchimpact['floor-area-new-residential_steel-to-timber'].copy()
dm_matswitchimpact_bld.append(DM_input_matswitchimpact['floor-area-new-non-residential_steel-to-timber'], "Categories1")
dm_matswitchimpact_bld_temp = DM_input_matswitchimpact['floor-area-new-residential_cement-to-timber'].copy()
dm_matswitchimpact_bld_temp.append(DM_input_matswitchimpact['floor-area-new-non-residential_cement-to-timber'], "Categories1")
dm_matswitchimpact_bld.append(dm_matswitchimpact_bld_temp, "Categories2")
dm_matswitchimpact_bld.switch_categories_order("Categories1", "Categories2")
dm_matswitchimpact_bld.group_all("Categories2", inplace = True)
dm_matswitchimpact_bld.array = dm_matswitchimpact_bld.array / 1000
dm_matswitchimpact_bld.units["mineral-decomposition"] = "kt"
dm_matswitchimpact_bld.rename_col("steel-to-timber", "steel", "Categories1")
dm_matswitchimpact_bld.rename_col("cement-to-timber", "cement", "Categories1")

# get energy demand for cement and steel produced (TWh/kt)
dm_temp = DM_energy_demand["bymat"].filter({"Categories1" : ["cement","steel"]})
dm_temp.append(DM_material_production["bymat"].filter({"Categories1" : ["cement","steel"]}), "Variables")
dm_temp.operation("energy-demand", "/", "material-production", dim="Variables", 
                  out_col='energy-demand-specific', unit='TWh/kt', div0="error")
dm_temp.drop(dim = "Variables", col_label = ["energy-demand", "material-production"])

# get energy savings due to cement and steel switches to timber (TWh)
dm_temp.append(dm_matswitchimpact_bld, "Variables")
dm_temp.operation("energy-demand-specific", "*", "mineral-decomposition", dim="Variables", 
                  out_col='energy-savings', unit='TWh')
dm_temp.drop(dim = "Variables", col_label = ['energy-demand-specific', 'mineral-decomposition'])

# get emissions for cement and steel produced (Kt)
dm_temp1 = DM_emissions["bygasmat"].filter({"Categories2" : ["cement","steel"]})
dm_temp1 = dm_temp1.filter({"Categories1" : ["CO2"]})
dm_temp1 = dm_temp1.flatten()
dm_temp1.rename_col_regex("CO2_","","Categories1")
dm_temp1.array = dm_temp1.array * 1000
dm_temp1.units["emissions"] = "Kt"
dm_temp1.append(DM_material_production["bymat"].filter({"Categories1" : ["cement","steel"]}), "Variables")
dm_temp1.operation("emissions", "/", "material-production", dim="Variables", 
                  out_col='emissions-specific', unit='Kt', div0="error")
dm_temp1.drop(dim = "Variables", col_label = ["emissions", "material-production"])
dm_temp1.array = dm_temp1.array / 1000
dm_temp1.units["emissions-specific"] = "Mt"

# get emissions savings for cement and steel switches to timber (Kt)
dm_temp1.append(dm_matswitchimpact_bld, "Variables")
dm_temp1.operation("emissions-specific", "*", "mineral-decomposition", dim="Variables", 
                   out_col='emissions-savings', unit='Kt')
dm_temp1.drop(dim = "Variables", col_label = ['emissions-specific', 'mineral-decomposition'])

# put together
dm_bld_matswitch_savings_bymat = dm_temp
dm_bld_matswitch_savings_bymat.append(dm_temp1, "Variables")

del dm_matswitchimpact_bld, dm_temp, dm_temp1, dm_matswitchimpact_bld_temp

###############################################
#################### COSTS ####################
###############################################

# get unit costs constants
cdm_cost = cdm_const.filter_w_regex({"Variables" : ".*cost-ind.*$"})
cdm_cost.rename_col_regex("_productive-assets", "", dim = "Variables")
cdm_cost.rename_col_regex("cost-ind_", "", dim = "Variables")
variables = cdm_cost.col_labels["Variables"]
drop = np.array(variables)[[bool(re.search("amm-tech", i)) for i in variables]].tolist()
cdm_cost.drop(dim = "Variables", col_label = drop)

# rename emission factors process
variables = cdm_cost.col_labels["Variables"]
variables_new = [rename_tech(i) for i in variables]
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
cdm_cost_sub.drop("Categories1", "steel-DRI-EAF")

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
cdm_cost_sub.drop("Categories1", "steel-DRI-EAF")

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

# sum capex and opex by material
for key in DM_cost.keys():
    
    # subset dm for varibles that have more than one tech per material
    dm_temp = DM_cost[key].copy()
    dm_temp.filter({"Variables" : [re.split("_", key)[1]]}, inplace = True)
    variables = dm_temp.col_labels["Categories1"]
    variables = [re.split("-", i)[0] for i in variables]
    variables_unique = list(set(variables))
    variables_unique = np.array(variables_unique)[[sum([y in i for i in variables]) > 1 for y in variables_unique]].tolist()
    variables = dm_temp.col_labels["Categories1"]
    keep = np.array(variables)[[bool(re.search("|".join(variables_unique), i)) for i in variables]].tolist()
    dm_temp1 = dm_temp.filter({"Categories1" : keep})

    # change name of categories
    variables = dm_temp1.col_labels["Categories1"]
    variables_new = [rename_tech_fordeepen(i) for i in variables]
    for i in range(len(variables)):
        dm_temp1.rename_col(variables[i], variables_new[i], "Categories1")
    
    # deepen
    dm_temp1.deepen()
    
    # do the sum
    dm_temp1.group_all("Categories2", inplace = True)
    
    # put values before 2015 as nas
    idx = dm_temp1.idx
    years_na = np.array(range(1990,2015,1))
    dm_temp1.array[:,[idx[y] for y in years_na],...] = np.nan
    
    # append the other variables
    variables = dm_temp.col_labels["Categories1"]
    variables = np.array(variables)[[i not in keep for i in variables]].tolist()
    variables_new = [re.split("-", i)[0] for i in variables]
    dm_temp2 = dm_temp.filter({"Categories1" : variables})
    for i in range(len(variables)):
        dm_temp2.rename_col(variables[i], variables_new[i], "Categories1")
    dm_temp1.append(dm_temp2, "Categories1")
    dm_temp1.sort("Categories1")
    
    # rename variable
    dm_temp1.rename_col(re.split("_", key)[1], key, "Variables")
    
    # write over
    DM_cost[key] = dm_temp1

del cdm_cost, cdm_cost_sub, dm_emissions_capt_w_cc_sub, dm_emissions_capt_w_cc_sub_capex, \
    dm_emissions_capt_w_cc_sub_opex, dm_material_techshare_sub, dm_material_techshare_sub_capex, \
    dm_material_techshare_sub_opex, dm_price_index, dm_temp, dm_temp1, dm_temp2, drop, i, keep, key, \
    variables, variables_new, variables_unique, idx, years_na



#################################################
#################### OUTPUTS ####################
#################################################

#########################
########## TPE ##########
#########################

# adjust variables' names
DM_cost["material-production_capex"].rename_col_regex("material-production_capex", "investment", "Variables")
DM_cost["CO2-capt-w-cc_capex"].rename_col_regex("CO2-capt-w-cc_capex", "investment_CC", "Variables")
DM_cost["material-production_opex"].rename_col_regex("material-production_opex", "operating-costs", "Variables")
DM_cost["CO2-capt-w-cc_opex"].rename_col_regex("CO2-capt-w-cc_opex", "operating-costs_CC", "Variables")
dm_bld_matswitch_savings_bymat.rename_col_regex("-","_","Variables")
DM_emissions["bygas"] = DM_emissions["bygas"].flatten()
DM_emissions["bygas"].rename_col_regex("_","-","Variables")
variables = DM_material_production["bytech"].col_labels["Categories1"]
variables_new = [rename_tech_fordeepen(i) for i in variables]
for i in range(len(variables)):
    DM_material_production["bytech"].rename_col(variables[i], variables_new[i], dim = "Categories1")

# dm_tpe
dm_tpe = DM_emissions["bygas"].copy()
dm_tpe.append(DM_energy_demand["bymat"].flatten(), "Variables")
dm_temp = DM_energy_demand["bymatcarr"].flatten()
dm_tpe.append(dm_temp.flatten(), "Variables")
dm_tpe.append(DM_energy_demand["bioener"], "Variables")
dm_tpe.append(DM_cost["CO2-capt-w-cc_capex"].flatten(), "Variables")
dm_tpe.append(DM_cost["material-production_capex"].flatten(), "Variables")
dm_tpe.append(DM_cost["CO2-capt-w-cc_opex"].flatten(), "Variables")
dm_tpe.append(DM_cost["material-production_opex"].flatten(), "Variables")
dm_tpe.append(DM_material_production["bymat"].flatten(), "Variables")
dm_tpe.append(DM_material_production["bytech"].flatten(), "Variables")
variables = dm_tpe.col_labels["Variables"]
for i in variables:
    dm_tpe.rename_col(i, "ind_" + i, "Variables")
dm_tpe.append(dm_bld_matswitch_savings_bymat.flatten(), "Variables")
dm_tpe.sort("Variables")

# df_tpe
df_tpe = dm_tpe.write_df()

################################
########## INTERFACES ##########
################################

DM_interface = Interface()
# TODO: change this according to interactions() (probably put an if())

#######################
##### AGRICULTURE #####
#######################

# adjust variables' names
dm_timber = DM_material_production["bymat"].filter({"Categories1" : ["timber"]})
dm_timber = dm_timber.flatten()
dm_timber.rename_col("material-production_timber", "timber", "Variables")
DM_energy_demand["feedstock_bybiomat"].rename_col("energy-demand-feedstock", "biomaterial", "Variables")
dm_indwaste = DM_energy_demand["indwaste"]
dm_indwaste = dm_indwaste.flatten()
dm_indwaste.rename_col("energy-demand_solid-waste", "waste", "Variables")
DM_energy_demand["bioener_bybiomat"].rename_col("energy-demand-bioenergy", "bioenergy", "Variables")
DM_material_production["natfiber"].rename_col('mineral-decomposition', "dem", "Variables")

# dm_agr
dm_agr = dm_timber.copy()
dm_agr.append(DM_material_production["bytech"].filter({"Categories1" : ['paper_woodpulp']}).flatten(), "Variables")
dm_agr.append(DM_energy_demand["feedstock_bybiomat"].flatten(), "Variables")
dm_agr.append(dm_indwaste, "Variables")
dm_agr.append(DM_energy_demand["bioener_bybiomat"].flatten(), "Variables")
dm_agr.append(DM_material_production["natfiber"].flatten(), "Variables")
variables = dm_agr.col_labels["Variables"]
for i in variables:
    dm_agr.rename_col(i, "ind_" + i, "Variables")
dm_agr.sort("Variables")
    
# # df_agr
# df_agr = dm_agr.write_df()
# df_agr.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-agriculture.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_agr
DM_interface.add_link(from_sector = "industry", to_sector = "agriculture", dm = dm_agr)

##################
##### ENERGY #####
##################

# dm_elc
dm_elc = DM_energy_demand["bycarr"].filter(
    {"Categories1" : ['liquid-ff-oil_diesel', 'liquid-ff-oil_fuel-oil', 'electricity',
                      'gas-ff-natural', 'hydrogen', 'solid-ff-coal']})
dm_elc.rename_col("energy-demand", "ind_energy-demand", "Variables")
dm_elc = dm_elc.flatten()
variables = dm_elc.col_labels["Variables"]
for i in variables:
    dm_elc.rename_col(i, "ind_" + i, "Variables")
dm_elc.sort("Variables")

# # df_elc
# dm_elc = dm_elc.write_df()
# dm_elc.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-electricity_supply.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_elc
DM_interface.add_link(from_sector = "industry", to_sector = "electricity_supply", dm = dm_elc)

#################
##### WATER #####
#################

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

# # df_water
# df_water = dm_water.write_df()
# df_water.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-water.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_water
DM_interface.add_link(from_sector = "industry", to_sector = "water", dm = dm_water)

################
##### CCUS #####
################

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

# # df_ccus
# df_ccus = dm_ccus.write_df()
# df_ccus.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-ccus.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_ccus
DM_interface.add_link(from_sector = "industry", to_sector = "ccus", dm = dm_ccus)

################
##### GTAP #####
################

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

# # df_gtap
# df_gtap = dm_gtap.write_df()
# df_gtap.columns = df_gtap.columns.str.removesuffix("[Mt]")
# df_gtap.columns = df_gtap.columns.str.removesuffix("[GWh]")
# df_gtap.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-gtap.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_gtap
DM_interface.add_link(from_sector = "industry", to_sector = "gtap", dm = dm_gtap)

####################
##### MINERALS #####
####################

# unit conversions
dm_timber.array = dm_timber.array / 1000
dm_timber.units["timber"] = "Mt"
dm_glass = DM_material_production["bymat"].filter(
    {"Categories1" : ["glass"]})
dm_glass.array = dm_glass.array / 1000
dm_glass.units["material-production"] = "Mt"

dm_cement = DM_material_production["bymat"].filter(
    {"Categories1" : ['cement']})
dm_cement.array = dm_cement.array / 1000
dm_cement.units["material-production"] = "Mt"

# rename
dm_alupack = DM_production["lfs"].filter({"Categories1" : ["aluminium-pack"]})
dm_alupack.rename_col("ind_product-production","ind_prod","Variables")
dm_techdev = DM_ots_fts['technology-development'].filter(
    {"Categories1" : ['aluminium-prim', 'aluminium-sec','copper-tech',
                      'steel-BF-BOF', 'steel-hisarna', 'steel-hydrog-DRI', 
                      'steel-scrap-EAF']})
variables = dm_techdev.col_labels["Categories1"]
variables_new = [rename_tech_fordeepen(i) for i in variables]
for i in range(len(variables)):
    dm_techdev.rename_col(variables[i], variables_new[i], dim = "Categories1")

# dm_min
dm_min = dm_glass.flatten()
dm_min.append(dm_timber, "Variables")
dm_min.append(DM_material_production["bytech"].filter(
    {"Categories1" : ['paper_woodpulp']}).flatten(), "Variables")
dm_min.append(dm_cement.flatten(), "Variables")
variables = dm_min.col_labels["Variables"]
for i in variables:
    dm_min.rename_col(i, "ind_" + i, "Variables")
dm_min.append(DM_ots_fts['material-efficiency'].filter(
    {"Variables" : ['ind_material-efficiency'],
     "Categories1" : ['aluminium','copper','steel']}).flatten(), "Variables")
dm_min.append(DM_ots_fts['material-switch'].filter(
    {"Categories1" : ['build-steel-to-timber', 'cars-steel-to-chem', 
                      'trucks-steel-to-aluminium', 'trucks-steel-to-chem']}).flatten(), "Variables")
dm_min.append(dm_alupack.flatten(), "Variables")
dm_min.append(dm_techdev.flatten(), "Variables")
dm_min.append(DM_ots_fts["product-net-import"].filter(
    {"Variables" : ["ind_product-net-import"],
     "Categories1" : ['cars-EV', 'cars-FCV', 'cars-ICE', 'computer', 'dishwasher', 'dryer',
                      'freezer', 'fridge','phone','planes','rail','road', 'ships', 'trains',
                      'trolley-cables', 'trucks-EV', 'trucks-FCV', 'trucks-ICE', 'tv', 
                      'wmachine']}).flatten(), "Variables")
dm_min.append(DM_ots_fts["product-net-import"].filter(
    {"Variables" : ['ind_product-net-import_new_dhg'],
     "Categories1" : ['pipe']}).flatten(), "Variables")
dm_min.sort("Variables")

# # df_min
# df_min = dm_min.write_df()
# df_min.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-minerals.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_min
DM_interface.add_link(from_sector = "industry", to_sector = "minerals", dm = dm_min)


######################
##### EMPLOYMENT #####
######################

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

# # df_emp
# df_emp = dm_emp.write_df()
# df_emp.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-employment.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_emp
DM_interface.add_link(from_sector = "industry", to_sector = "employment", dm = dm_emp)


###################
##### CLIMATE #####
###################

# adjust variables' names
dm_temp = DM_emissions["bygasmat"].flatten().flatten()
dm_temp.deepen()
dm_temp.rename_col_regex("_","-","Variables")
DM_emissions["combustion_bio_capt_w_cc_neg_bymat"].rename_col("emissions-biogenic-negative","emissions-CO2_biogenic","Variables")
dm_temp1 = DM_emissions["combustion_bio_capt_w_cc_neg_bymat"].flatten()
dm_temp1.rename_col_regex("CO2-capt-w-cc_","","Categories1")

# dm_cli
dm_cli = dm_temp.flatten()
dm_cli.append(dm_temp1.flatten(), "Variables")
variables = dm_cli.col_labels["Variables"]
for i in variables:
    dm_cli.rename_col(i, "ind_" + i, "Variables")
dm_cli.sort("Variables")

# # dm_cli
# df_cli = dm_cli.write_df()
# df_cli.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-climate.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_cli
DM_interface.add_link(from_sector = "industry", to_sector = "climate", dm = dm_cli)


#########################
##### AIR POLLUTION #####
#########################

# dm_airpoll
dm_airpoll = DM_material_production["bytech"].flatten()
dm_airpoll.append(DM_energy_demand["bymatcarr"].flatten().flatten(), "Variables")
variables = dm_airpoll.col_labels["Variables"]
for i in variables:
    dm_airpoll.rename_col(i, "ind_" + i, "Variables")
dm_airpoll.sort("Variables")

# # dm_airpoll
# df_airpoll = dm_airpoll.write_df()
# df_airpoll.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-air_pollution.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_cli
DM_interface.add_link(from_sector = "industry", to_sector = "air_pollution", dm = dm_airpoll)


############################
##### DISTRICT HEATING #####
############################

# FIXME!: make dummy values for dh (this is like this also in KNIME, to be seen what to do)
dm_dh = DM_energy_demand["bycarr"].filter({"Categories1" : ["electricity"]})
dm_dh = dm_dh.flatten()
dm_dh.add(0, dim = "Variables", col_label = "ind_supply_heat-waste", unit = "TWh/year", dummy = True)
dm_dh.drop("Variables", 'energy-demand_electricity')

# # dm_dh
# df_dh = dm_dh.write_df()
# df_dh.to_excel(current_file_directory + "/../_database/data/xls/" + 'industry-to-district_heating.xlsx', index=False)
# TODO: uncomment this following what is done in interactions (probably put an if())

# interface_dh
DM_interface.add_link(from_sector = "industry", to_sector = "district_heating", dm = dm_dh)

del dm_agr, dm_airpoll, dm_alupack, dm_bld_matswitch_savings_bymat, dm_cal, dm_ccus, \
    dm_cement, dm_cli, DM_cost, DM_demand, dm_dh, dm_elc, DM_emissions, dm_emp, \
    DM_energy_demand, DM_fxa, dm_glass, dm_gtap, dm_indwaste, DM_input_matswitchimpact, \
    DM_material_demand, DM_material_production, dm_min, DM_production, dm_techdev, \
    dm_temp, dm_temp1, dm_temp2, dm_timber, dm_tpe, dm_water, i, variables, variables_new






