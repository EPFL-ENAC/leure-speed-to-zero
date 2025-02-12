#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 16:41:30 2024

@author: echiarot
"""

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

def rename_tech_fordeepen(word):
    
    # this function renames tech to get material_tech, to then aggregate
    # one example is turning steel-BF-BOF into steel_BF-BOF and steel-hydrog-DRI into steel_hydrog-DRI to then aggregate and get steel
    
    first = word.split("-")[0]
    last = word.split("-")[1:]
    if len(last) > 1:
        last = ["-".join(last)]
    word_new = first + "_" + last[0]
    return word_new

def sum_over_techs(dm, category_with_techs):
    
    # this function sums over techs to get the total by material
    # it uses rename_tech_fordeepen()
    
    # get material_tech_multi and material_tech_single
    # material_tech_multi are the techs for those materials that have more than one tech (like aluminium-prim and aluminium-sec)
    # material_tech_single are the techs for those materials that have only one tech (like copper-tech)
    techs = dm.col_labels[category_with_techs]
    ls_temp = [i.split("-")[0] for i in techs]
    materials = list(set(ls_temp))
    materials.sort()
    materials_with_multi_tech = np.array(materials)[[sum([m in i for i in ls_temp]) > 1 for m in materials]].tolist()
    pattern = "|".join(materials_with_multi_tech)
    material_tech_multi = np.array(techs)[[bool(re.search(pattern, i)) for i in ls_temp]].tolist()
    material_tech_single = np.array(techs)[[not bool(re.search(pattern, i)) for i in ls_temp]].tolist()

    if material_tech_multi is not None:
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
    if material_tech_multi is not None:
        dm_out.append(dm_out_sub, category_with_techs)
    else:
        dm_out = dm_out_sub
    dm_out.sort(category_with_techs)
    
    # return
    return dm_out

def database_from_csv_to_datamatrix():
    
    def rename_tech(word):
        last = "-".join([word.split("_")[-2], word.split("_")[-1]])
        first = "_".join(word.split("_")[0:-2])
        word_new = first + "_" + last
        return word_new
    
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
    df = read_database_fxa('industry_fixed-assumptions')
    dm_ind = DataMatrix.create_from_df(df, num_cat=0)

    df = read_database_fxa('costs_fixed-assumptions')
    dm_cost = DataMatrix.create_from_df(df, num_cat=0)
    dm_cost.drop("Country", "EU28")
    
    df = read_database_fxa('eol_fixed-assumptions')
    dm_matdec_eol = DataMatrix.create_from_df(df, num_cat=0)
    
    # costs
    dm_cost = dm_cost.filter_w_regex({"Variables" : ".*ind_.*"})
    dm_cost = dm_cost.filter_w_regex({"Variables" : "^((?!elc_).)*$"})
    dm_cost.rename_col_regex("ind_", "", dim = "Variables")
    variables = dm_cost.col_labels["Variables"]
    drop = np.array(variables)[[bool(re.search("amm-tech", i)) for i in variables]].tolist()
    dm_cost.drop(dim = "Variables", col_label = drop)
    variables = dm_cost.col_labels["Variables"]
    variables_new = [rename_tech(i) for i in variables]
    for i in range(len(variables)):
        dm_cost.rename_col(variables[i], variables_new[i], "Variables")
        
    # costs for material production
    dm_cost_matprod = dm_cost.filter_w_regex({"Variables" : "^((?!CC).)*$"})
    dm_cost_matprod.deepen()
    dm_cost_matprod.drop("Categories1", ["cement-geopolym","lime-lime","steel-DRI-EAF","steel-hisarna"])
    # TODO: for the moment I am creating the costs for the secondary materials as below, later on we
    # should add the actual cost for these technologies
    dm_temp = dm_cost_matprod
    dm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["aluminium-sec-precons"]]
    dm_temp.add(arr_temp, "Categories1", "aluminium-sec-postcons")
    dm_temp.rename_col("copper-tech", "copper-prim", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["copper-prim"]]
    dm_temp.add(arr_temp, "Categories1", "copper-sec-precons")
    dm_temp.add(arr_temp, "Categories1", "copper-sec-postcons")
    dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"]]
    dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
    dm_temp.sort("Categories1")
    
    # costs for cc
    dm_cost_cc = dm_cost.filter_w_regex({"Variables" : ".*CC.*"})
    dm_cost_cc.rename_col_regex("CC_", "", dim = "Variables")
    dm_cost_cc.deepen()
    dm_cost_cc.drop("Categories1", ["steel-DRI-EAF","steel-hisarna"])
    # TODO: for the moment I am creating the costs for the secondary materials as below, later on we
    # should add the actual cost for these technologies
    dm_temp = dm_cost_cc
    dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"]]
    dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
    dm_temp.sort("Categories1")
    
    # material decomposition eol
    dm_matdec_eol.drop("Years",[2016,2017,2018,2019])    
    
    # # batteries
    # dm_matdec_eol_batteries = dm_matdec_eol.filter_w_regex({"Variables" : ".*batteries.*"})
    # dm_matdec_eol_batteries.rename_col_regex("batteries_", "", "Variables")
    # dm_matdec_eol_batteries.deepen()
    # dm_temp = dm_matdec_eol_batteries.groupby({'cars-ICE': 'ICE.*|PHEV.*', 
    #                                            'cars-FCV': 'FCEV', 
    #                                            'cars-EV': 'BEV'}, 
    #                                           dim='Categories1', regex=True, inplace=True)
    
    # matdec vehicles
    dm_matdec_eol_veh = dm_matdec_eol.filter_w_regex({"Variables" : ".*cars.*|.*trucks.*"})
    dm_matdec_eol_veh = dm_matdec_eol_veh.filter_w_regex({"Variables" : "^((?!batteries).)*$"})
    dm_matdec_eol_veh.deepen()
    # dm_matdec_eol_veh.groupby({'cars-ICE': '.*cars-ICE.*|.*cars-PHEV.*', 'cars-FCV': '.*cars-FCEV.*', 
    #                            'cars-EV': '.*cars-BEV.*'}, 
    #                           dim='Variables', aggregation = "mean", regex=True, inplace=True)
    # dm_matdec_eol_veh.groupby({'trucks-ICE': '.*trucks-high-ICE.*|.*trucks-medium-ICE.*|.*trucks-low-ICE.*|.*trucks-high-PHEV.*|.*trucks-low-PHEV.*|.*trucks-medium-PHEV.*', 
    #                            'cars-FCV': '.*cars-FCEV.*', 
    #                            'cars-EV': '.*cars-BEV.*'}, 
    #                           dim='Variables', aggregation = "mean", regex=True, inplace=True)
    
    # matdec electronics
    dm_matdec_eol_elec = dm_matdec_eol.filter_w_regex({"Variables" : ".*pc.*|.*phone.*|.*tv.*"})
    dm_matdec_eol_elec.deepen()
    
    # mated domestic appliances
    dm_matdec_eol_domapp = dm_matdec_eol.filter_w_regex({"Variables" : ".*fridge.*|.*dishwasher.*|.*washing-machine.*"})
    dm_matdec_eol_domapp.deepen()
    
    # Keep only ots and fts years
    dm_ind = dm_ind.filter(selected_cols={'Years': years_all})
    # dm_matdec_eol_batteries = dm_matdec_eol_batteries.filter(selected_cols={'Years': years_all})
    dm_matdec_eol_veh = dm_matdec_eol_veh.filter(selected_cols={'Years': years_all})
    dm_matdec_eol_elec = dm_matdec_eol_elec.filter(selected_cols={'Years': years_all})
    dm_matdec_eol_domapp = dm_matdec_eol_domapp.filter(selected_cols={'Years': years_all})

    # save
    dm_liquid = dm_ind.filter({"Variables" : ['ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
    dm_prod = dm_ind.filter({"Variables" : ['ind_prod_fbt', 'ind_prod_mae', 'ind_prod_ois', 'ind_prod_textiles', 
                                        'ind_prod_tra-equip', 'ind_prod_wwp']})
    dict_fxa = {
        'liquid': dm_liquid,
        'prod': dm_prod,
        'cost-matprod': dm_cost_matprod,
        'cost-CC' : dm_cost_cc,
        # 'matdec_eol_batteries' : dm_matdec_eol_batteries,
        'matdec_eol_veh' : dm_matdec_eol_veh,
        'matdec_eol_elec' : dm_matdec_eol_elec,
        'matdec_eol_domapp' : dm_matdec_eol_domapp,
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
    df_ots, df_fts = read_database(file, lever, level='all')
    df_ots.columns = df_ots.columns.str.replace('tra_','tra-')
    df_fts.columns = df_fts.columns.str.replace('tra_','tra-')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                        df_ots=df_ots, df_fts=df_fts)
    
    # technology share, technology development and carbon capture (CC)
    levers = ["technology-development", "cc"]
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
        
        # add secondary techs
        # TODO: for the moment I am creating the developments for the secondary materials as below, later on we
        # should add the actual developments for these technologies
        dm_temp = dict_ots[lever]
        dm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["aluminium-sec-precons"]]
        dm_temp.add(arr_temp, "Categories1", "aluminium-sec-postcons")
        dm_temp.rename_col("copper-tech", "copper-prim", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["copper-prim"]]
        dm_temp.add(arr_temp, "Categories1", "copper-sec-precons")
        dm_temp.add(arr_temp, "Categories1", "copper-sec-postcons")
        dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"]]
        dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
        dm_temp.drop("Categories1", ["ammonia-amm-tech"])
        dm_temp.sort("Categories1")
        for i in range(1,5):
            dm_temp = dict_fts[lever][i]
            dm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories1")
            idx = dm_temp.idx
            arr_temp = dm_temp.array[...,idx["aluminium-sec-precons"]]
            dm_temp.add(arr_temp, "Categories1", "aluminium-sec-postcons")
            dm_temp.rename_col("copper-tech", "copper-prim", "Categories1")
            idx = dm_temp.idx
            arr_temp = dm_temp.array[...,idx["copper-prim"]]
            dm_temp.add(arr_temp, "Categories1", "copper-sec-precons")
            dm_temp.add(arr_temp, "Categories1", "copper-sec-postcons")
            dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
            idx = dm_temp.idx
            arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"]]
            dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
            dm_temp.drop("Categories1", ["ammonia-amm-tech"])
            dm_temp.sort("Categories1")
    
        
    # technology share
    file = 'industry_technology-share'
    lever = 'technology-share'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
        
    # drop ammonia
    dict_ots["technology-share"].filter_w_regex({"Categories1" : "^((?!ammonia).)*$"}, inplace = True)
    for i in range(1,5):
        dict_fts["technology-share"][i].filter_w_regex({"Categories1" : "^((?!ammonia).)*$"}, inplace = True)

    # dm_temp = dict_fts["technology-share"][4].copy()
    # idx = dm_temp.idx
    # dm_temp.array[idx["EU27"],idx[2020],:,idx["steel-scrap-EAF"]]
    
    # material net import
    file = 'industry_material-net-import'
    lever = "material-net-import"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    
    # product net import
    file = 'industry_product-net-import'
    lever = "product-net-import"
    df_ots, df_fts = read_database(file, lever, level='all')
    df_ots.columns = df_ots.columns.str.replace('_new_','-new-')
    df_ots.columns = df_ots.columns.str.replace('_reno_','-reno-')
    df_ots.columns = df_ots.columns.str.replace('-new-dhg_pipe','_new-dhg-pipe')
    df_fts.columns = df_fts.columns.str.replace('_new_','-new-')
    df_fts.columns = df_fts.columns.str.replace('_reno_','-reno-')
    df_fts.columns = df_fts.columns.str.replace('-new-dhg_pipe','_new-dhg-pipe')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                        df_ots=df_ots, df_fts=df_fts)

    # energy carrier mix
    file = 'industry_energy-carrier-mix'
    lever = "energy-carrier-mix"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    dm_temp = dict_ots['energy-carrier-mix']
    dm_temp.rename_col_regex(str1 = "ind_energy-carrier-mix_", str2 = "", dim = "Variables")
    dm_temp.rename_col_regex("_", "-", dim = "Variables")
    names = dm_temp.col_labels["Variables"]
    for i in names:
        dm_temp.rename_col(i, "energy-mix_" + i, "Variables")
    dm_temp.deepen(based_on="Variables")
    dm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')
    dm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["aluminium-sec-precons"],:]
    dm_temp.add(arr_temp, "Categories1", "aluminium-sec-postcons")
    dm_temp.rename_col("copper-tech", "copper-prim", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["copper-prim"],:]
    dm_temp.add(arr_temp, "Categories1", "copper-sec-precons")
    dm_temp.add(arr_temp, "Categories1", "copper-sec-postcons")
    dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
    idx = dm_temp.idx
    arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"],:]
    dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
    dm_temp.drop("Categories1", ["ammonia-amm-tech"])
    for i in range(1, 5):
        dm_temp = dict_fts['energy-carrier-mix'][i]
        dm_temp.rename_col_regex(str1 = "ind_energy-carrier-mix_", str2 = "", dim = "Variables")
        dm_temp.rename_col_regex("_", "-", dim = "Variables")
        names = dm_temp.col_labels["Variables"]
        for n in names:
            dm_temp.rename_col(n, "energy-mix_" + n, "Variables")
        dm_temp.deepen(based_on="Variables")
        dm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')
        dm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["aluminium-sec-precons"],:]
        dm_temp.add(arr_temp, "Categories1", "aluminium-sec-postcons")
        dm_temp.rename_col("copper-tech", "copper-prim", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["copper-prim"],:]
        dm_temp.add(arr_temp, "Categories1", "copper-sec-precons")
        dm_temp.add(arr_temp, "Categories1", "copper-sec-postcons")
        dm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories1")
        idx = dm_temp.idx
        arr_temp = dm_temp.array[...,idx["steel-scrap-EAF-precons"],:]
        dm_temp.add(arr_temp, "Categories1", "steel-sec-postcons")
        dm_temp.drop("Categories1", ["ammonia-amm-tech"])
    
    # eol waste management
    file = 'eol_waste-management'
    lever = "eol-waste-management"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    dm_temp = dict_ots["eol-waste-management"]
    dm_temp.groupby({'cars-ICE': 'cars-ICE.*|cars-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
    dm_temp.rename_col("cars-BEV","cars-EV","Variables")
    dm_temp.rename_col("cars-FCEV","cars-FCV","Variables")
    dm_temp.groupby({'trucks-ICE': 'trucks-.*-ICE.*|trucks-.*-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
    dm_temp.groupby({'trucks-EV': 'trucks-.*-BEV.*'}, dim='Variables', regex=True, inplace=True)
    dm_temp.groupby({'trucks-FCV': 'trucks-.*-FCEV.*'}, dim='Variables', regex=True, inplace=True)
    for i in range(1,5):
        dm_temp = dict_fts["eol-waste-management"][i]
        dm_temp.groupby({'cars-ICE': 'cars-ICE.*|cars-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
        dm_temp.rename_col("cars-BEV","cars-EV","Variables")
        dm_temp.rename_col("cars-FCEV","cars-FCV","Variables")
        dm_temp.groupby({'trucks-ICE': 'trucks-.*-ICE.*|trucks-.*-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
        dm_temp.groupby({'trucks-EV': 'trucks-.*-BEV.*'}, dim='Variables', regex=True, inplace=True)
        dm_temp.groupby({'trucks-FCV': 'trucks-.*-FCEV.*'}, dim='Variables', regex=True, inplace=True)
    
    ["waste-collected","waste-uncollected","export","littered"]
    dm_temp = dict_ots["eol-waste-management"].filter({"Variables" : ["cars-EV"],
                                                       "Categories1" :["recycling","energy-recovery","reuse","landfill","incineration"] }
                                                      ).group_all("Categories1", inplace = False)
    np.unique(dm_temp.array)
    
    # eol material recovery
    file = 'eol_material-recovery'
    lever = "eol-material-recovery"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    dm_temp = dict_ots["eol-material-recovery"]
    dm_temp.groupby({'cars-ICE': 'cars-ICE.*|cars-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
    dm_temp.rename_col("cars-BEV","cars-EV","Variables")
    dm_temp.rename_col("cars-FCEV","cars-FCV","Variables")
    dm_temp.groupby({'trucks-ICE': 'trucks-.*-ICE.*|trucks-.*-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
    dm_temp.groupby({'trucks-EV': 'trucks-.*-BEV.*'}, dim='Variables', regex=True, inplace=True)
    dm_temp.groupby({'trucks-FCV': 'trucks-.*-FCEV.*'}, dim='Variables', regex=True, inplace=True)
    for i in range(1,5):
        dm_temp = dict_fts["eol-material-recovery"][i]
        dm_temp.groupby({'cars-ICE': 'cars-ICE.*|cars-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
        dm_temp.rename_col("cars-BEV","cars-EV","Variables")
        dm_temp.rename_col("cars-FCEV","cars-FCV","Variables")
        dm_temp.groupby({'trucks-ICE': 'trucks-.*-ICE.*|trucks-.*-PHEV.*'}, dim='Variables', regex=True, aggregation = "mean", inplace=True)
        dm_temp.groupby({'trucks-EV': 'trucks-.*-BEV.*'}, dim='Variables', regex=True, inplace=True)
        dm_temp.groupby({'trucks-FCV': 'trucks-.*-FCEV.*'}, dim='Variables', regex=True, inplace=True)
    
    #######################
    ##### CALIBRATION #####
    #######################

    # Read calibration
    df = read_database_fxa('industry_calibration')
    dm_cal = DataMatrix.create_from_df(df, num_cat=0)

    #####################
    ##### CONSTANTS #####
    #####################
    
    # get constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_tec_|cp_cost-ind', num_cat=0)
    
    # rename
    cdm_const.rename_col_regex(str1 = "_dhg_",str2 = "-dhg-",dim = "Variables")
    cdm_const.rename_col_regex(str1 = "_new_",str2 = "-new-",dim = "Variables")
    cdm_const.rename_col_regex(str1 = "_reno_",str2 = "-reno-",dim = "Variables")
    cdm_const.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")
    
    # drop ammonia
    cdm_const = cdm_const.filter_w_regex({"Variables" : "^((?!ammonia).)*$"})
    
    # subset
    dict_const = {}
    
    # material switch
    dict_const["material-switch"] = cdm_const.filter_w_regex({"Variables" : ".*switch.*"})
    
    # material decomposition
    dict_const["material-decomposition_pipe"] = cdm_const.filter_w_regex({"Variables":".*pipe.*"})
    dict_const["material-decomposition_pipe"].deepen_twice()
    dict_const["material-decomposition_floor"] = cdm_const.filter_w_regex({"Variables":".*floor.*"})
    dict_const["material-decomposition_floor"].deepen_twice()
    dict_const["material-decomposition_domapp"] = cdm_const.filter_w_regex({"Variables":".*computer.*|.*dishwasher.*|.*dryer.*|.*freezer.*|.*fridge.*|.*phone.*|.*tv.*|.*wmachine.*"})
    dict_const["material-decomposition_domapp"].deepen_twice()
    dict_const["material-decomposition_infra"] = cdm_const.filter_w_regex({"Variables":".*rail.*|.*road.*|.*cable.*"})
    dict_const["material-decomposition_infra"].deepen_twice()
    dict_const["material-decomposition_veh"] = cdm_const.filter_w_regex({"Variables":".*car.*|.*truck.*|.*plane.*|.*ship.*|.*train.*"})
    dict_const["material-decomposition_veh"].deepen_twice()
    dict_const["material-decomposition_lfs"] = cdm_const.filter_w_regex({"Variables":".*pack.*|.*print.*|.*san.*"})
    dict_const["material-decomposition_lfs"].deepen_twice()
    
    # energy demand excl feedstock
    # TODO: for the moment I am creating the energy demand constants for the secondary materials as below, later on we
    # should add the actual energy demand constants for these technologies
    cdm_temp = cdm_const.filter_w_regex({"Variables" : ".*tec_energy_specific-excl-feedstock.*"})
    cdm_temp.rename_col_regex(str1 = "tec_energy_specific-excl-feedstock_", str2 = "", dim = "Variables")
    cdm_temp.deepen()
    cdm_temp.rename_col_regex("_", "-", dim = "Variables")
    
    cdm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["aluminium-sec-precons"],:]
    cdm_temp.add(arr_temp, "Variables", "aluminium-sec-postcons")
    
    cdm_temp.rename_col("copper-tech", "copper-prim", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["copper-prim"],:]
    cdm_temp.add(arr_temp, "Variables", "copper-sec-precons")
    cdm_temp.add(arr_temp, "Variables", "copper-sec-postcons")
    
    cdm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["steel-scrap-EAF-precons"],:]
    cdm_temp.add(arr_temp, "Variables", "steel-sec-postcons")
    
    cdm_temp.sort("Variables")
    dict_const["energy_excl-feedstock"]  = cdm_temp
    
    # energy demand feedstock
    # TODO: for the moment I am creating the energy demand constants for the secondary materials as below, later on we
    # should add the actual energy demand constants for these technologies
    cdm_temp = cdm_const.filter_w_regex({"Variables" : ".*tec_energy_specific-feedstock.*"})
    cdm_temp.rename_col_regex(str1 = "tec_energy_specific-feedstock_", str2 = "", dim = "Variables")
    cdm_temp.deepen()
    cdm_temp.rename_col_regex("_", "-", dim = "Variables")
    
    cdm_temp.rename_col("aluminium-sec", "aluminium-sec-precons", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["aluminium-sec-precons"],:]
    cdm_temp.add(arr_temp, "Variables", "aluminium-sec-postcons")
    
    cdm_temp.rename_col("copper-tech", "copper-prim", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["copper-prim"],:]
    cdm_temp.add(arr_temp, "Variables", "copper-sec-precons")
    cdm_temp.add(arr_temp, "Variables", "copper-sec-postcons")
    
    cdm_temp.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Variables")
    idx = cdm_temp.idx
    arr_temp = cdm_temp.array[idx["steel-scrap-EAF-precons"],:]
    cdm_temp.add(arr_temp, "Variables", "steel-sec-postcons")
    
    cdm_temp.sort("Variables")
    dict_const["energy_feedstock"]  = cdm_temp
    
    # emission factor process
    # TODO: for the moment I am creating the emission constants for the secondary materials as below, later on we
    # should add the actual emission constants for these technologies
    cdm_temp1 = cdm_const.filter_w_regex({"Variables":".*emission-factor-process.*"})
    variables = cdm_temp1.col_labels["Variables"]
    variables_new = [rename_tech(i) for i in variables]
    for i in range(len(variables)):
        cdm_temp1.rename_col(variables[i], variables_new[i], "Variables")
    cdm_temp1.deepen_twice()
    
    cdm_temp1.rename_col("aluminium-sec", "aluminium-sec-precons", "Categories2")
    idx = cdm_temp1.idx
    arr_temp = cdm_temp1.array[:,:,idx["aluminium-sec-precons"]]
    cdm_temp1.add(arr_temp, "Categories2", "aluminium-sec-postcons")
    
    cdm_temp1.rename_col("copper-tech", "copper-prim", "Categories2")
    idx = cdm_temp1.idx
    arr_temp = cdm_temp1.array[:,:,idx["copper-prim"]]
    cdm_temp1.add(arr_temp, "Categories2", "copper-sec-precons")
    cdm_temp1.add(arr_temp, "Categories2", "copper-sec-postcons")
    
    cdm_temp1.rename_col("steel-scrap-EAF", "steel-scrap-EAF-precons", "Categories2")
    idx = cdm_temp1.idx
    arr_temp = cdm_temp1.array[:,:,idx["steel-scrap-EAF-precons"]]
    cdm_temp1.add(arr_temp, "Categories2", "steel-sec-postcons")
    
    cdm_temp1.sort("Categories2")
    dict_const["emission-factor-process"] = cdm_temp1
    
    # emission factor
    cdm_temp2 = cdm_const.filter_w_regex({"Variables":".*emission-factor_.*"})
    cdm_temp2.deepen_twice()
    cdm_temp2.drop(dim = "Categories2", col_label = ['gas-synfuel', 'liquid-synfuel'])
    dict_const["emission-factor"] = cdm_temp2

    ################
    ##### SAVE #####
    ################

    DM_industry = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        'calibration': dm_cal,
        "constant" : dict_const
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
    CMD_const = DM_industry['constant']

    # clean
    del handle, DM_industry, data_file, lever_setting
    
    # return
    return DM_fxa, DM_ots_fts, dm_cal, CMD_const

def product_production(dm_demand_bld_pipe, dm_demand_bld_floor, dm_demand_bld_domapp, 
                       dm_demand_tra_infra, dm_demand_tra_veh, 
                       dm_demand_lfs, dm_import):
    
    # production [%] = 1 - net import [%]
    dm_prod = dm_import.copy()
    idx = dm_prod.idx
    arr_temp = dm_prod.array[:, :, idx["ind_product-net-import"], :]
    arr_temp[arr_temp > 1] = 1
    arr_temp = 1 - arr_temp
    dm_prod.array[:, :, idx["ind_product-net-import"], :] = arr_temp
    dm_prod.rename_col(col_in="ind_product-net-import", col_out="ind_product-production", dim="Variables")
    # TODO: the operations above are done only with product net import, so to increase the speed we could build a lever called product-production and load it, to be done later

    #####################
    ##### BUILDINGS #####
    #####################

    # get production for buildings
    dm_prod_bld_pipe = dm_prod.filter({"Categories1" : ['new-dhg-pipe']})
    dm_prod_bld_floor = dm_prod.filter_w_regex({"Categories1": "floor-area"})
    dm_prod_bld_domapp = dm_prod.filter({"Categories1" : ['computer', 'dishwasher', 'dryer', 
                                                          'freezer', 'fridge', 'phone',
                                                          'tv', 'wmachine']})

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
    dm_prod_tra_infra = dm_prod.filter({"Categories1": ['rail', 'road', 'trolley-cables']})
    dm_prod_tra_veh = dm_prod.filter({"Categories1": ['cars-EV', 'cars-FCV', 'cars-ICE',
                                                       'planes', 'ships', 'trains',
                                                       'trucks-EV', 'trucks-FCV', 'trucks-ICE']})
    
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
    dm_prod_lfs = dm_prod.filter({"Categories1": ['aluminium-pack', 'glass-pack', 'paper-pack',
                                                   'paper-print', 'paper-san', 'plast-pack']})


    # production (units) = demand * production [%]
    dm_prod_lfs.array = dm_prod_lfs.array * dm_demand_lfs.array
    dm_prod_lfs.units["ind_product-production"] = dm_demand_lfs.units["lfs_product-demand"]

    ########################
    ##### PUT TOGETHER #####
    ########################

    DM_production = {"bld-pipe": dm_prod_bld_pipe,
                     "bld-floor": dm_prod_bld_floor,
                     "bld-domapp": dm_prod_bld_domapp,
                     "tra-infra": dm_prod_tra_infra,
                     "tra-veh": dm_prod_tra_veh,
                     "lfs": dm_prod_lfs}
        
    # return
    return DM_production

def apply_material_decomposition(dm_production_bld_pipe, dm_production_bld_floor, dm_production_bld_domapp,  
                                 dm_production_tra_infra, dm_production_tra_veh, dm_production_lfs,
                                 cdm_matdec_pipe, cdm_matdec_floor, cdm_matdec_domapp,
                                 cdm_matdec_tra_infra, cdm_matdec_tra_veh, cdm_matdec_lfs):
    
    # material demand [t] = product production [unit] * material decomposition coefficient [t/unit]

    #####################
    ##### BUILDINGS #####
    #####################

    # pipe
    dm_bld_pipe_matdec = material_decomposition(dm=dm_production_bld_pipe, cdm=cdm_matdec_pipe)

    # floor
    dm_bld_floor_matdec = material_decomposition(dm=dm_production_bld_floor, cdm=cdm_matdec_floor)

    # domestic appliance
    dm_bld_domapp_matdec = material_decomposition(dm=dm_production_bld_domapp, cdm=cdm_matdec_domapp)
    
    #####################
    ##### TRANSPORT #####
    #####################

    # infra
    dm_tra_infra_matdec = material_decomposition(dm=dm_production_tra_infra, cdm=cdm_matdec_tra_infra)

    # veh
    dm_tra_veh_matdec = material_decomposition(dm=dm_production_tra_veh, cdm=cdm_matdec_tra_veh)

    ######################
    ##### LIFESTYLES #####
    ######################

    # lfs
    dm_production_lfs.drop(dim="Categories1", col_label=['aluminium-pack']) # note: this should be 100% aluminium, to be seen if they get it back later
    dm_lfs_matdec = material_decomposition(dm=dm_production_lfs, cdm=cdm_matdec_lfs)

    ########################
    ##### PUT TOGETHER #####
    ########################

    dm_matdec = dm_bld_pipe_matdec
    dm_matdec.append(dm_bld_floor_matdec, dim="Categories1")
    dm_matdec.append(dm_bld_domapp_matdec, dim="Categories1")
    dm_matdec.append(dm_tra_infra_matdec, dim="Categories1")
    dm_matdec.append(dm_tra_veh_matdec, dim="Categories1")
    dm_matdec.append(dm_lfs_matdec, dim="Categories1")

    # TODO!: check if it's fine to call this material demand, as it's obtained from production variables
    DM_material_demand = {"material-demand": dm_matdec}
    DM_material_demand["material-demand"].drop("Categories2", ["other"])

    # clean
    del dm_bld_pipe_matdec, dm_bld_floor_matdec, dm_bld_domapp_matdec, \
        dm_tra_infra_matdec, dm_tra_veh_matdec, dm_lfs_matdec

    # return
    return DM_material_demand

def apply_material_switch(dm_material_demand, dm_material_switch, cdm_material_switch, DM_input_matswitchimpact):
    
    # material in-to-out [t] = material in [t] * in-to-out [%]
    # material in [t] = material in [t] - material in-to-out [t]
    # material out [t] = material out [t] + material in-to-out [t] * switch ratio [t/t]

    #####################
    ##### TRANSPORT #####
    #####################

    material_switch(dm = dm_material_demand, dm_ots_fts=dm_material_switch,
                    cdm_const=cdm_material_switch, material_in="steel", material_out=["chem", "aluminium"],
                    product="cars-ICE", switch_percentage_prefix="cars-",
                    switch_ratio_prefix="tec_material-switch-ratios_")

    material_switch(dm=dm_material_demand, dm_ots_fts=dm_material_switch,
                    cdm_const=cdm_material_switch, material_in="steel", material_out=["chem", "aluminium"],
                    product="trucks-ICE", switch_percentage_prefix="trucks-",
                    switch_ratio_prefix="tec_material-switch-ratios_")

    #####################
    ##### BUILDINGS #####
    #####################

    # new buildings: switch to renewable materials (steel and cement to timber in new residential and non-residential)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "steel", material_out = ["timber"], 
                    product = 'floor-area-new-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "cement", material_out = ["timber"], 
                    product = 'floor-area-new-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "steel", material_out = ["timber"], 
                    product = 'floor-area-new-non-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "cement", material_out = ["timber"], 
                    product = 'floor-area-new-non-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    # renovated buildings: switch to insulated surfaces (chemicals to paper and natural fibers in renovated residential and non-residential)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "chem", material_out = ["paper","natfibers"], 
                    product = "floor-area-reno-residential", switch_percentage_prefix = "reno-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_")

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "chem", material_out = ["paper","natfibers"], 
                    product = "floor-area-reno-non-residential", switch_percentage_prefix = "reno-", 
                    switch_ratio_prefix = "tec_material-switch-ratios_")
    
    return

def material_production(dm_material_efficiency, dm_material_net_import, 
                        dm_material_demand, dm_matprod_other_industries):
    
    ######################
    ##### EFFICIENCY #####
    ######################
    
    # get efficiency coefficients
    dm_temp = dm_material_efficiency.copy()
    dm_temp.filter({"Categories1" : dm_material_demand.col_labels["Categories2"]}, inplace=True)
    dm_temp.add(0, "Categories1", "natfiber", unit="%", dummy=True)
    dm_temp.sort("Categories1")
    
    # apply formula to material demand (and overwrite)
    dm_material_demand.array = dm_material_demand.array * (1 - dm_temp.array[:,:,:,np.newaxis,:])
    
    ############################
    ##### AGGREGATE DEMAND #####
    ############################

    # get aggregate demand
    dm_matdec_agg = dm_material_demand.group_all(dim='Categories1', inplace=False)
    dm_matdec_agg.change_unit('material-decomposition', factor=1e-3, old_unit='t', new_unit='kt')
    # note: here "other" will be different as in knime they filtered out all "other" but for glass_pack_other

    # subset aggregate demand for the materials we keep
    materials = ['aluminium', 'cement', 'chem', 'copper', 'glass', 'lime', 'paper', 'steel', 'timber']
    dm_material_production_natfiber = dm_matdec_agg.filter({"Categories1": ["natfibers"]}) # this will be used for interface agriculture
    dm_matdec_agg.filter({"Categories1": materials}, inplace=True)

    ######################
    ##### PRODUCTION #####
    ######################

    # material production [kt] = material demand [kt] * (1 - material net import [%])
    # material production < 0 when material net import > 1, which means that the difference between import and export is larger than domestic demand
    # when this happens, I assume that material production is zero (a country that imports a lot to the point that the material net import is larger than domestic demand)
    # and later I will add whatever people do not consume of all this import to the material stock
    # this quantity equals (material net import - 1) * material demand
    # TODO: add this quantity to the material stock

    # get net import % and make production %
    dm_temp = dm_material_net_import.copy()
    dm_temp.filter({"Categories1" : materials}, inplace = True)
    dm_temp.array[dm_temp.array > 1] = 0
    dm_temp.array = 1 - dm_temp.array

    # get material production
    dm_material_production_bymat = dm_matdec_agg.copy()
    dm_material_production_bymat.array = dm_matdec_agg.array * dm_temp.array
    dm_material_production_bymat.rename_col(col_in = 'material-decomposition', col_out = 'material-production', dim = "Variables")

    # include other industries from fxa
    dm_temp = dm_matprod_other_industries.copy()
    dm_temp.deepen()
    dm_temp.rename_col(col_in = 'ind_prod', col_out = 'material-production', dim = "Variables")
    dm_temp.units['material-production'] = "kt"
    dm_material_production_bymat.append(data2 = dm_temp, dim = "Categories1")
    dm_material_production_bymat.sort("Categories1")
    
    # put together
    DM_material_production = {"bymat" : dm_material_production_bymat, 
                              "natfiber" : dm_material_production_natfiber}
    
    # clean
    del dm_matdec_agg, dm_temp, materials, dm_material_production_bymat, dm_material_production_natfiber
    
    # return
    return DM_material_production

def calibration_material_production(dm_cal, dm_material_production_bymat, DM_material_production):
    
    # get calibration series
    dm_cal_sub = dm_cal.copy()
    dm_cal_sub.deepen()
    materials = dm_material_production_bymat.col_labels["Categories1"]
    dm_cal_sub.filter({"Categories1" : materials}, inplace = True)
    dm_cal_sub.filter({"Variables" : ['cal_ind_production-calibration']}, inplace = True)

    # get calibration rates
    DM_material_production["calib_rates_bymat"] = calibration_rates(dm = dm_material_production_bymat, dm_cal = dm_cal_sub)

    # do calibration
    dm_material_production_bymat.array = dm_material_production_bymat.array * DM_material_production["calib_rates_bymat"].array

    # clean
    del dm_cal_sub, materials
    
    return

def end_of_life(dm_transport_waste, dm_waste_management, dm_matrec_veh, 
                cdm_matdec_veh, dm_material_production_bymat):
    
    
    # in general:
    # littered + export + uncolleted + collected = 1
    # recycling + energy recovery + reuse + landfill + (incineration) = 1
    # note on incineration: transport will not have incineration, while electric waste yes
    
    # # check
    # ["waste-collected","waste-uncollected","export","littered"]
    # dm_temp = dm_waste_management.filter({"Variables" : ["cars-EV"],
    #                                       "Categories1" : ["recycling","energy-recovery","reuse","landfill","incineration"]}
    #                                       ).group_all("Categories1", inplace = False)
    # np.unique(dm_temp.array)
    
    # TODO: for the moment I am doing waste management only for cars and trucks, this will have to be done
    # for 'planes', 'ships', 'trains', batteries (probably this will be in minerals), 
    # appliances (for which we'll have to update buildings) and
    # buildings (which is already present in buildings, though we need to develop the data on their eol).
    # So far, the split of waste categories should be the same for transport and appliances, with the
    # only difference that incineration will be positive values for appliances. That should be the only
    # difference, so same formulas should apply.
    
    # make waste-collected, waste-uncollected, export, littered
    layer1 = ["waste-collected","waste-uncollected","export","littered"]
    dm_waste_layer1 = dm_waste_management.filter({"Categories1" : layer1})
    arr_temp = dm_transport_waste.array[...,np.newaxis] * dm_waste_layer1.array[:,:,np.newaxis,:,:]
    dm_transport_waste_bywsm_layer1 = DataMatrix.based_on(arr_temp, dm_transport_waste, 
                                                          {'Categories2': layer1}, 
                                                          units = dm_transport_waste.units)
    
    # make recycling, energy recovery, reuse, landfill, incineration
    layer2 = ["recycling","energy-recovery","reuse","landfill","incineration"]
    dm_waste_layer2 = dm_waste_management.filter({"Categories1" : layer2})
    dm_waste_layer2.rename_col_regex("cars","waste-management_cars","Variables")
    dm_waste_layer2.rename_col_regex("trucks","waste-management_trucks","Variables")
    dm_waste_layer2.deepen("_","Variables")
    dm_waste_layer2.switch_categories_order("Categories1","Categories2")
    dm_waste_collected = dm_transport_waste_bywsm_layer1.filter({"Categories2" : ["waste-collected"]})
    arr_temp = dm_waste_collected.array[...,np.newaxis] * dm_waste_layer2.array[:,:,:,:,np.newaxis,:]
    dm_transport_waste_bywsm_layer2 = DataMatrix.based_on(arr_temp, dm_waste_collected, 
                                                          {'Categories3': layer2}, 
                                                          units = dm_waste_collected.units)
    dm_transport_waste_bywsm_layer2 = dm_transport_waste_bywsm_layer2.flatten()
    dm_transport_waste_bywsm_layer2.rename_col_regex("waste-collected_","","Categories2")
    
    # do material decomposition for recycling, energy recovery, reuse, landfill, incineration
    arr_temp = dm_transport_waste_bywsm_layer2.array[...,np.newaxis] * cdm_matdec_veh.array[np.newaxis,np.newaxis,:,:,np.newaxis,:]
    dm_transport_waste_bymat = DataMatrix.based_on(arr_temp, dm_transport_waste_bywsm_layer2, 
                                                   {'Categories3': cdm_matdec_veh.col_labels["Categories2"]}, 
                                                   units = "t")
    dm_transport_waste_bymat.units["tra_product-waste"] = "t" # not sure why command above did not work, to be checked later
    # TODO:for the moment I am using the material decomposition in constants to be consistent with the
    # rest of industry. At the moment, the new material decomposition (coming in as fixed assumption) is missing 
    # some of the products. When it will have all products, we can substitute in the new material decomposition.
    
    # get material recovered post consumer
    materials = dm_transport_waste_bymat.col_labels["Categories3"]
    materials_rec_veh = dm_matrec_veh.col_labels["Categories1"]
    materials_sub = np.array(materials_rec_veh)[[i in materials for i in materials_rec_veh]].tolist()
    dm_matrec_veh.filter({"Categories1" : materials_sub}, inplace = True)
    dm_transport_waste_bymat.filter({"Categories3" : materials_sub}, inplace = True)
    dm_transport_matrecovered_veh = dm_matrec_veh.copy()
    idx = dm_transport_waste_bymat.idx
    dm_transport_matrecovered_veh.array = dm_transport_waste_bymat.array[:,:,0,:,idx["recycling"],:] * dm_matrec_veh.array
    variables = dm_transport_matrecovered_veh.col_labels["Variables"]
    for v in variables: dm_transport_matrecovered_veh.units[v] = "t"
    
    # sum across products
    dm_transport_matrecovered_veh.groupby({'vehicles': '.*cars*|.*trucks.*'}, 
                                          dim='Variables', aggregation = "sum", regex=True, inplace=True)
    # dm_transport_matrecovered_veh = dm_transport_matrecovered_veh.flatten()
    # dm_transport_matrecovered_veh.rename_col_regex("vehicles_","","Variables")
    
    # get material recovered across sectors
    # TODO!: later on add here the other sectors, like buildings and batteries
    dm_matrecovered = dm_transport_matrecovered_veh.copy()
    dm_matrecovered.change_unit('vehicles', factor=1e-3, old_unit='t', new_unit='kt')
    dm_matrecovered.rename_col_regex("vehicles","material-recovered","Variables")
    
    # if material recovered is larger than material produced, impose material recovered to be equal to material produced
    materials = dm_matrecovered.col_labels["Categories1"]
    dm_temp = dm_matrecovered.copy()
    dm_temp1 = dm_material_production_bymat.filter({"Categories1" : materials})
    dm_temp.array = dm_matrecovered.array - dm_temp1.array # create a dm in which you do the difference
    dm_temp.array[dm_temp.array > 0] = 0 # where the difference is > 0, put difference = 0
    dm_temp.array = dm_temp.array + dm_temp1.array # sum back the material production, so where the difference > 0, the value of material recovered now equals the value of material production
    dm_matrecovered_corrected = dm_temp
    
    # save
    DM_eol = {
        "material-towaste": dm_transport_waste_bymat,
        "material-recovered" : dm_matrecovered_corrected
        }
    
    return DM_eol

def material_production_by_technology(dm_technology_share, dm_material_production_bymat, 
                                      dm_material_recovered):
    
    # TODO: new assumption is that the shares of aluminium-secondary and steel-scrap-EAF
    # are all pre consumer. So we will subtract whatever recovered material from post consumer,
    # and then we'll apply these percentages to whatever is left.
    
    # create dm_material_production_bytech
    dm_material_production_bytech = dm_material_production_bymat.copy()
    names_present = dm_material_production_bytech.col_labels["Categories1"]
    techs = ['aluminium-prim', 'cement-dry-kiln', 'chem-chem-tech', 'copper-tech', 'fbt-tech', 'glass-glass', 'lime-lime', 'mae-tech', 
             'ois-tech', 'paper-recycled', 'steel-BF-BOF', 'textiles-tech', 'timber-tech', 'tra-equip-tech', 'wwp-tech']
    for i in range(len(names_present)):
        dm_material_production_bytech.rename_col(names_present[i], techs[i], dim = "Categories1")

    # add missing in Categories1
    techs_sub1 = ['cement-dry-kiln', 'cement-dry-kiln', 'paper-recycled',
                  'steel-BF-BOF', 'steel-BF-BOF']
    techs_sub2 = ['cement-geopolym', 'cement-wet-kiln', 'paper-woodpulp',
                  'steel-hisarna', 'steel-hydrog-DRI']
    idx = dm_material_production_bytech.idx
    for i in range(len(techs_sub1)):
        arr_temp = dm_material_production_bytech.array[:,:,:,idx[techs_sub1[i]]]
        dm_material_production_bytech.add(arr_temp[...,np.newaxis], dim = "Categories1", col_label = techs_sub2[i])
    dm_material_production_bytech.sort("Categories1")

    # get material production by technology
    dm_material_production_bytech.array = dm_material_production_bytech.array * dm_technology_share.array
    
    # for aluminium and steel:
    # production = primary + secondary pre consumer + secondary post consumer
    
    # if primary >= production - secondary post consumer -> primary = production - secondary post consumer
    # or if primary - production + secondary post consumer >= 0 -> primary - production + secondary post consumer = 0
    dm_prim = dm_material_production_bytech.filter({"Categories1" : ['aluminium-prim', 'steel-BF-BOF', 
                                                                     'steel-hisarna', 'steel-hydrog-DRI']})
    dm_prim.groupby({'steel-prim': 'steel-BF-BOF|steel-hisarna|steel-hydrog-DRI'}, dim='Categories1', regex=True, inplace=True)
    dm_prod = dm_material_production_bymat.filter({"Categories1" : ["aluminium","steel"]})
    dm_post = dm_material_recovered.filter({"Categories1" : ["aluminium","steel"]})
    dm_temp = dm_prim.copy()
    dm_temp.array = dm_prim.array - dm_prod.array + dm_post.array
    dm_temp.array[dm_temp.array >= 0] = 0
    dm_temp.array = dm_temp.array + dm_prod.array - dm_post.array
    
    # adjust steel across 3 steel-making types via normalisation
    dm_temp1 = dm_technology_share.filter({"Categories1" : ['steel-BF-BOF','steel-hisarna', 'steel-hydrog-DRI']})
    dm_temp1.normalise("Categories1")
    dm_temp2 = dm_temp.filter({"Categories1" : ["steel-prim"]})
    dm_temp1.array = dm_temp1.array * dm_temp2.array
    dm_temp1.rename_col("ind_technology-share","material-production","Variables")
    dm_temp1.units["material-production"] = "kt"
    dm_temp.drop("Categories1","steel-prim")
    dm_temp.append(dm_temp1, "Categories1")
    
    # substitute back in the adjusted aluminium and steel
    dm_material_production_bytech.drop("Categories1",['aluminium-prim', 'steel-BF-BOF', 
                                                      'steel-hisarna', 'steel-hydrog-DRI'])
    dm_material_production_bytech.append(dm_temp, "Categories1")
    dm_material_production_bytech.sort("Categories1")
    
    # make secondary pre consumer
    # if primary < production - secondary post consumer -> secondary pre consumer = production - primary - secondary post consumer
    dm_prim = dm_material_production_bytech.filter({"Categories1" : ['aluminium-prim', 'steel-BF-BOF', 
                                                                     'steel-hisarna', 'steel-hydrog-DRI']})
    dm_prim.groupby({'steel': 'steel-BF-BOF|steel-hisarna|steel-hydrog-DRI'}, dim='Categories1', regex=True, inplace=True)
    dm_prim.rename_col("aluminium-prim","aluminium","Categories1")
    dm_prod = dm_material_production_bymat.filter({"Categories1" : ["aluminium","steel"]})
    dm_post = dm_material_recovered.filter({"Categories1" : ["aluminium","steel"]})
    techs = ["aluminium","steel"]
    countries = dm_prim.col_labels["Country"]
    years = dm_prim.col_labels["Years"]
    idx1 = dm_prim.idx
    idx2 = dm_prod.idx
    idx3 = dm_post.idx
    dm_temp = dm_prim.copy()
    dm_temp.array[:,:,:,:] = 0
    idx4 = dm_temp.idx
    for t in techs:
        for c in countries:
            for y in years:
                value = dm_prim.array[idx1[c],idx1[y],:,idx1[t]] -\
                    dm_prod.array[idx2[c],idx2[y],:,idx2[t]] +\
                        dm_post.array[idx3[c],idx3[y],:,idx3[t]]
                if value < 0:
                    dm_temp.array[idx4[c],idx4[y],:,idx4[t]] =\
                        dm_prod.array[idx2[c],idx2[y],:,idx2[t]] -\
                            dm_prim.array[idx1[c],idx1[y],:,idx1[t]] -\
                                dm_post.array[idx3[c],idx3[y],:,idx3[t]]
    dm_temp.rename_col("aluminium","aluminium-sec-precons","Categories1")
    dm_temp.rename_col("steel","steel-scrap-EAF-precons","Categories1")
    dm_material_production_bytech.append(dm_temp, "Categories1")
    dm_material_production_bytech.sort("Categories1")
    
    # copper:
    # for copper we currently do not have the share of primary, so:
    # production = primary + secondary post consumer
    # so production - secondary post consumer = primary
    # note that we have already imposed that production - secondary post consumer >= 0, so primary can be only 0 or positive
    dm_prod = dm_material_production_bymat.filter({"Categories1" : ["copper"]})
    dm_post = dm_material_recovered.filter({"Categories1" : ["copper"]})
    dm_prim = dm_prod.copy()
    dm_prim.array = dm_prod.array - dm_post.array
    dm_prim.rename_col("copper","copper-prim","Categories1")
    dm_material_production_bytech.append(dm_prim, "Categories1")
    dm_material_production_bytech.add(0, "Categories1", "copper-sec-precons", unit="kt", dummy=True)
    dm_material_production_bytech.drop("Categories1", "copper-tech")
    dm_material_production_bytech.sort("Categories1")
    
    # add secondary post consumer in dm_material_production_bytech
    dm_material_recovered.rename_col("aluminium","aluminium-sec-postcons","Categories1")
    dm_material_recovered.rename_col("steel","steel-sec-postcons","Categories1")
    dm_material_recovered.rename_col("copper","copper-sec-postcons","Categories1")
    dm_material_recovered.rename_col("material-recovered","material-production","Variables")
    dm_material_production_bytech.append(dm_material_recovered, "Categories1")
    dm_material_production_bytech.sort("Categories1")
    
    # # checks
    # # production = primary + secondary pre consumer + secondary post consumer
    # dm_prod = dm_material_production_bymat.copy()
    # idx1 = dm_prod.idx
    # dm_prod_bytech = dm_material_production_bytech.copy()
    # idx2 = dm_prod_bytech.idx
    # arr_temp =\
    #     dm_prod.array[:,:,:,idx1["aluminium"]] ==\
    #         dm_prod_bytech.array[:,:,:,idx2["aluminium-prim"]] +\
    #             dm_prod_bytech.array[:,:,:,idx2["aluminium-sec-precons"]] +\
    #                 dm_prod_bytech.array[:,:,:,idx2["aluminium-sec-postcons"]]
    # np.all(arr_temp)
    # arr_temp =\
    #     dm_prod.array[:,:,:,idx1["copper"]] ==\
    #         dm_prod_bytech.array[:,:,:,idx2["copper-prim"]] +\
    #             dm_prod_bytech.array[:,:,:,idx2["copper-sec-precons"]] +\
    #                 dm_prod_bytech.array[:,:,:,idx2["copper-sec-postcons"]]
    # np.all(arr_temp)
    # arr_temp =\
    #     dm_prod.array[:,:,:,idx1["steel"]] ==\
    #         dm_prod_bytech.array[:,:,:,idx2["steel-BF-BOF"]] +\
    #             dm_prod_bytech.array[:,:,:,idx2["steel-hisarna"]] +\
    #                 dm_prod_bytech.array[:,:,:,idx2["steel-hisarna"]] +\
    #                     dm_prod_bytech.array[:,:,:,idx2["steel-scrap-EAF-precons"]] +\
    #                         dm_prod_bytech.array[:,:,:,idx2["steel-sec-postcons"]]
    # np.all(arr_temp)
    # # df_temp = pd.merge(dm_prod.write_df(),dm_prod_bytech.write_df(), how="left", on=["Country","Years"])
    # # A = df_temp.loc[df_temp["material-production_steel[kt]"] !=\
    # #                 df_temp["material-production_steel-BF-BOF[kt]"] +\
    # #                     df_temp["material-production_steel-hisarna[kt]"] +\
    # #                         df_temp["material-production_steel-hydrog-DRI[kt]"] +\
    # #                             df_temp["material-production_steel-scrap-EAF-precons[kt]"] +\
    # #                                 df_temp["material-production_steel-sec-postcons[kt]"],
    # #                                 ["Country","Years","material-production_steel[kt]",
    # #                                   "material-production_steel-BF-BOF[kt]", "material-production_steel-hisarna[kt]",
    # #                                   "material-production_steel-hydrog-DRI[kt]",
    # #                                   "material-production_steel-scrap-EAF-precons[kt]", 
    # #                                   "material-production_steel-sec-postcons[kt]"]]
    # # A = A.reset_index(drop = True)
    # # A.loc[0,"material-production_steel[kt]"]
    # # A.loc[0,"material-production_steel-BF-BOF[kt]"] + A.loc[0,"material-production_steel-hisarna[kt]"] +\
    # #     A.loc[0,"material-production_steel-hydrog-DRI[kt]"] + A.loc[0,"material-production_steel-scrap-EAF-precons[kt]"] +\
    # #         A.loc[0,"material-production_steel-sec-postcons[kt]"]
    # # # ok it's fine it's a rounding problem
    
    # return
    return dm_material_production_bytech

def energy_demand(dm_material_production_bytech, CDM_const):
    
    # this is by material-technology and carrier

    # get energy demand for material production by technology both without and with feedstock
    feedstock = ["excl-feedstock", "feedstock"]
    DM_energy_demand = {}

    for f in feedstock:

        # get constants for energy demand for material production by technology
        cdm_temp = CDM_const["energy_" + f]
        
        # create dm for energy demand for material production by technology
        names = cdm_temp.col_labels["Variables"]
        for i in names:
            cdm_temp.rename_col(i, "energy-demand-" + f + "_" + i, "Variables")
        cdm_temp.deepen(based_on="Variables")
        cdm_temp.switch_categories_order(cat1='Categories1', cat2='Categories2')
        dm_energy_demand = cdm_to_dm(cdm_temp, 
                                     dm_material_production_bytech.col_labels["Country"], 
                                     dm_material_production_bytech.col_labels["Years"])
        
        # get energy demand for material production by technology
        dm_temp = dm_material_production_bytech.filter_w_regex({"Categories1" : "^((?!timber-tech).)*$"})
        dm_temp.change_unit('material-production', factor=1e-3, old_unit='kt', new_unit='Mt')
        dm_energy_demand.array = dm_energy_demand.array * dm_temp.array[...,np.newaxis]
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
    
    # aggregate energy demand by energy carrier
    DM_energy_demand["bycarr"] = DM_energy_demand["bytechcarr"].group_all(dim='Categories1', inplace=False)

    # return
    return DM_energy_demand

def calibration_energy_demand(dm_cal, dm_energy_demand_bycarr, dm_energy_demand_bytechcarr, DM_energy_demand):
    
    # this is by material-technology and carrier

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

    # store dm_energy_demand_calib_rates_bycarr
    DM_energy_demand["calib_rates_bycarr"] = dm_energy_demand_calib_rates_bycarr

    # do calibration
    dm_energy_demand_bycarr.array = dm_energy_demand_bycarr.array * dm_energy_demand_calib_rates_bycarr.array

    # do calibration for each technology (by applying aggregate calibration rates)
    dm_energy_demand_bytechcarr.array = dm_energy_demand_bytechcarr.array * dm_energy_demand_calib_rates_bycarr.array[:,:,:,np.newaxis,:]

    # clean
    del dm_cal_sub, energy_carriers, dm_energy_demand_agg_sub, idx, years_bef2000, \
        dm_energy_demand_calib_rates_bycarr
        
    # return
    return 

def technology_development(dm_technology_development, dm_energy_demand_bytechcarr):
    
    dm_temp = dm_energy_demand_bytechcarr.copy()

    # get energy demand after technology development
    dm_temp.array = dm_temp.array * (1 - dm_technology_development.array[...,np.newaxis])

    # return
    return dm_temp

def apply_energy_switch(dm_energy_carrier_mix, dm_energy_demand_bytechcarr):
    
    # this is by material-technology and carrier

    # energy demand for electricity [TWh] = (energy demand [TWh] * electricity share) + energy demand coming from switch to electricity [TWh]

    # get energy mix
    dm_temp = dm_energy_carrier_mix.copy()

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

    # clean
    del dm_temp, carrier_in

    # return
    return

def add_specific_energy_demands(dm_fxa_liquid, dm_energy_demand_bytechcarr, 
                                dm_energy_demand_feedstock_bytechcarr, DM_energy_demand):
    
    # TODO: now the split between diesel and oil will come directly in the energy
    # demand constants, so update this part of the code
    
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
    dm_energy_demand_bioener_bybiomat.rename_col("energy-demand","energy-demand_bioenergy","Variables")
    dm_energy_demand_bioener = dm_energy_demand_bioener_bybiomat.group_all("Categories1", inplace = False)

    # get demand by material
    dm_energy_demand_bymat = dm_energy_demand_bymatcarr.group_all("Categories2", inplace = False)

    # get demand by carrier
    dm_energy_demand_bycarr = dm_energy_demand_bymatcarr.group_all("Categories1", inplace = False)

    # get liquid-ff-oil split between diesel and oil
    dm_temp = dm_fxa_liquid.filter({"Variables" : ['ind_liquid-ff-oil_diesel', 'ind_liquid-ff-oil_fuel-oil']})
    idx = dm_energy_demand_bycarr.idx
    dm_temp.array = dm_temp.array * dm_energy_demand_bycarr.array[:,:,:,idx["liquid-ff-oil"]] 
    dm_temp.units['ind_liquid-ff-oil_diesel'] = "TWh"
    dm_temp.units['ind_liquid-ff-oil_fuel-oil'] = "TWh"
    dm_temp.deepen_twice()
    dm_temp = dm_temp.flatten()
    dm_temp.rename_col_regex("ind","energy-demand","Variables")
    dm_energy_demand_bycarr.append(dm_temp, "Categories1")
    
    # get energy demand by tech
    dm_energy_demand_bytech = dm_energy_demand_bytechcarr.group_all("Categories2", inplace = False)

    # put in DM
    DM_energy_demand["bymatcarr"] = dm_energy_demand_bymatcarr
    DM_energy_demand["feedstock_bybiomat"] = dm_energy_demand_feedstock_bybiomat
    DM_energy_demand["indwaste"] = dm_energy_demand_indwaste
    DM_energy_demand["bioener_bybiomat"] = dm_energy_demand_bioener_bybiomat
    DM_energy_demand["bioener"] = dm_energy_demand_bioener
    DM_energy_demand["bymat"] = dm_energy_demand_bymat
    DM_energy_demand["bycarr"] = dm_energy_demand_bycarr
    DM_energy_demand["bytech"] = dm_energy_demand_bytech

    # clean
    del dm_energy_demand_bymatcarr, dm_energy_demand_feedstock_bybiomat, dm_energy_demand_indwaste, \
        dm_energy_demand_bioener, dm_energy_demand_bymat, dm_energy_demand_bioener_bybiomat, \
        dm_energy_demand_bycarr, dm_temp, idx, dm_energy_demand_feedstock_bycarr

    # return
    return

def emissions(cdm_const_emission_factor_process, cdm_const_emission_factor, 
              dm_energy_demand_bytechcarr, dm_material_production_bytech):
    
    # get emission factors
    cdm_temp1 = cdm_const_emission_factor_process
    cdm_temp2 = cdm_const_emission_factor

    # emissions = energy demand * emission factor

    # combustion
    dm_emissions_combustion = dm_energy_demand_bytechcarr.copy()
    dm_emissions_combustion.rename_col('energy-demand', "emissions", "Variables")
    dm_emissions_combustion.units["emissions"] = "Mt"
    names = dm_emissions_combustion.col_labels["Categories1"]
    for i in names:
        dm_emissions_combustion.rename_col(i, "CH4_" + i, "Categories1")
    dm_emissions_combustion.deepen("_", based_on = "Categories1")
    idx = dm_emissions_combustion.idx
    arr_temp = dm_emissions_combustion.array[:,:,:,idx["CH4"],:,:]
    dm_emissions_combustion.add(arr_temp[:,:,:,np.newaxis,:,:], "Categories1", col_label = "CO2")
    dm_emissions_combustion.add(arr_temp[:,:,:,np.newaxis,:,:], "Categories1", col_label = "N2O")
    dm_emissions_combustion.array = dm_emissions_combustion.array * \
        cdm_temp2.array[np.newaxis,np.newaxis,:,:,:,np.newaxis]

    # biogenic total
    bio = ['gas-bio','liquid-bio','solid-bio']
    dm_emissions_combustion_bio = dm_emissions_combustion.filter({"Categories2" : bio}, inplace = False)
    dm_emissions_combustion_bio = dm_emissions_combustion_bio.filter({"Categories1" : ["CO2"]}, inplace = False)
    dm_emissions_combustion_bio.group_all("Categories2")
    dm_emissions_combustion_bio.rename_col("emissions", "emissions-biogenic", dim = "Variables")

    # process
    dm_emissions_process = dm_material_production_bytech.filter_w_regex({"Categories1" : "^((?!timber-tech).)*$"})
    dm_emissions_process.change_unit('material-production', factor=1e-3, old_unit='kt', new_unit='Mt')
    dm_emissions_process.rename_col('material-production', "emissions-process_CH4", "Variables")
    dm_emissions_process.deepen("_", based_on = "Variables")
    dm_emissions_process.switch_categories_order("Categories1", "Categories2")
    idx = dm_emissions_process.idx
    arr_temp = dm_emissions_process.array[:,:,:,idx["CH4"],:]
    dm_emissions_process.add(arr_temp[:,:,:,np.newaxis,:], "Categories1", col_label = "CO2")
    dm_emissions_process.add(arr_temp[:,:,:,np.newaxis,:], "Categories1", col_label = "N2O")
    dm_emissions_process.array = dm_emissions_process.array * cdm_temp1.array[np.newaxis,np.newaxis,...]

    # total emissions per technology
    dm_emissions_bygastech = dm_emissions_combustion.group_all("Categories2", inplace = False)
    dm_emissions_bygastech.append(dm_emissions_process, dim = "Variables")
    dm_emissions_bygastech.add(np.nansum(dm_emissions_bygastech.array, -3, keepdims=True), 
                           dim = "Variables", col_label = "emissions-total", unit = "Mt")
    dm_emissions_bygastech.drop("Variables", ['emissions', 'emissions-process'])
    dm_emissions_bygastech.rename_col("emissions-total","emissions", "Variables")

    # put in dict
    DM_emissions = {"bygastech" : dm_emissions_bygastech,
                    "combustion_bio" : dm_emissions_combustion_bio,
                    "bygastech_beforecc" : dm_emissions_bygastech}

    # clean
    del cdm_temp1, cdm_temp2, arr_temp, i, idx, names, bio, \
        dm_emissions_bygastech, dm_emissions_combustion_bio, dm_emissions_process, \
        dm_emissions_combustion
    
    # return
    return DM_emissions

def carbon_capture(dm_ots_fts_cc, dm_emissions_bygastech, dm_emissions_combustion_bio, DM_emissions):
    
    # get carbon capture
    dm_temp = dm_ots_fts_cc.copy()

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
            'steel-hydrog-DRI', 'steel-scrap-EAF-precons', 'steel-sec-postcons']
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
                'steel_hydrog-DRI', 'steel_scrap-EAF-precons','steel_sec-postcons']
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

    # store
    DM_emissions["combustion_bio_capt_w_cc_neg_bymat"] = dm_emissions_combustion_bio_capt_w_cc_neg_bymat
    DM_emissions["capt_w_cc_bytech"] = dm_emissions_capt_w_cc_bytech
    
    # store also bygas (which is used in calibration if it's done)
    DM_emissions["bygas"] = dm_emissions_bygastech.group_all("Categories2", inplace = False)
    
    # emissions with different techs
    DM_emissions["bygasmat"] = sum_over_techs(dm = dm_emissions_bygastech, category_with_techs = "Categories2")
    DM_emissions["bygasmat"].rename_col("tra","tra-equip","Categories2")

    # clean
    del arr_temp, dm_emissions_combustion_bio_capt_w_cc, \
        dm_temp, dm_temp1, i, idx, keep, keep_new, dm_emissions_combustion_bio_capt_w_cc_neg_bymat, \
        dm_emissions_capt_w_cc_bytech
        
    # return
    return

def calibration_emissions(dm_cal, dm_emissions_bygas, dm_emissions_bygastech, DM_emissions):
    
    # get calibration series
    dm_cal_sub = dm_cal.copy()
    dm_cal_sub.filter({"Variables" : ['cal_ind_emissions_CH4', 'cal_ind_emissions_CO2', 'cal_ind_emissions_N2O']}, inplace = True)
    dm_cal_sub.deepen()

    # get calibration rates
    DM_emissions["calib_rates_bygas"] = calibration_rates(dm = dm_emissions_bygas, dm_cal = dm_cal_sub)

    # do calibration
    dm_emissions_bygas.array = dm_emissions_bygas.array * DM_emissions["calib_rates_bygas"].array

    # do calibration for each technology (by applying aggregate calibration rates)
    dm_emissions_bygastech.array = dm_emissions_bygastech.array * DM_emissions["calib_rates_bygas"].array[:,:,:,:,np.newaxis]

    # clean
    del dm_cal_sub
    
    return

# TODO: bring the function material_flows() into minerals (or somewhere external, probably together with the
# cost curves ... i.e. it could be in the tpe) and finalize it
def material_flows(dm_transport_stock, dm_material_towaste, dm_material_recovered, cdm_matdec_veh,
                   dm_emissions_bygasmat):
    
    # do material decomposition of stock
    arr_temp = dm_transport_stock.array[...,np.newaxis] * cdm_matdec_veh.array[np.newaxis,np.newaxis,:,:,:]
    dm_transport_stock_bymat = DataMatrix.based_on(arr_temp, dm_transport_stock, {'Categories2': cdm_matdec_veh.col_labels["Categories2"]}, 
                                                   units = dm_transport_stock.units)
    dm_transport_stock_bymat.units["tra_product-stock"] = "t"
    
    # sum across sectors
    dm_stock_bymat = dm_transport_stock_bymat.group_all("Categories1", inplace = False)
    dm_stock_bymat.rename_col('tra_product-stock','product-stock',"Variables")
    
    return

def compute_costs(dm_fxa_cost_matprod, dm_fxa_cost_cc, dm_material_production_bytech,
                  dm_emissions_capt_w_cc_bytech):

    ###############################
    ##### MATERIAL PRODUCTION #####
    ###############################

    # subset costs
    dm_cost_sub = dm_fxa_cost_matprod

    # get material production by technology
    variables = dm_material_production_bytech.col_labels["Categories1"]
    keep = np.array(variables)[[i in dm_cost_sub.col_labels["Categories1"] for i in variables]].tolist()
    dm_material_techshare_sub = dm_material_production_bytech.filter({"Categories1" : keep})
    dm_cost_sub.change_unit("capex-baseyear", factor=1e3, old_unit='EUR/t', new_unit='EUR/kt')
    dm_cost_sub.change_unit("capex-d-factor", factor=1e3, old_unit='num', new_unit='num')

    # get costs
    dm_material_techshare_sub_capex = cost(dm_activity = dm_material_techshare_sub, dm_cost = dm_cost_sub, cost_type = "capex")
    
    ######################################
    ##### EMISSIONS CAPTURED WITH CC #####
    ######################################

    # subset cdm
    dm_cost_sub = dm_fxa_cost_cc

    # get emissions captured with carbon capture
    variables = dm_emissions_capt_w_cc_bytech.col_labels["Categories1"]
    keep = np.array(variables)[[i in dm_cost_sub.col_labels["Categories1"] for i in variables]].tolist()
    dm_emissions_capt_w_cc_sub = dm_emissions_capt_w_cc_bytech.filter({"Categories1" : keep})
    dm_emissions_capt_w_cc_sub.change_unit("CO2-capt-w-cc", factor=1e6, old_unit='Mt', new_unit='t')

    # get costs
    dm_emissions_capt_w_cc_sub_capex = cost(dm_activity = dm_emissions_capt_w_cc_sub, dm_cost = dm_cost_sub, cost_type = "capex")

    ########################
    ##### PUT TOGETHER #####
    ########################

    DM_cost = {"material-production_capex" : dm_material_techshare_sub_capex,
               "CO2-capt-w-cc_capex" : dm_emissions_capt_w_cc_sub_capex}
    
    # fix
    for key in DM_cost.keys(): 
        cost_type = re.split("_", key)[1]
        activity_type = re.split("_", key)[0]
        DM_cost[key].filter({"Variables" : ["unit-cost",cost_type]}, inplace = True)
        DM_cost[key].rename_col("unit-cost", activity_type + "_" + cost_type + "-unit","Variables")
        DM_cost[key].rename_col(cost_type, activity_type + "_" + cost_type,"Variables")
    
    # sum capex and opex by material
    keys = list(DM_cost)
    for key in keys:
        
        # constants
        cost_type = re.split("_", key)[1]
        activity_type = re.split("_", key)[0]
        
        # subset dm for varibles that have more than one tech per material
        dm_temp = DM_cost[key].copy()
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
        dm_temp1_capex = dm_temp1.filter({"Variables" : [activity_type + "_" + cost_type]}).group_all("Categories2", inplace = False)
        dm_temp1_capex_unit = dm_temp1.filter({"Variables" : [activity_type + "_" + cost_type+"-unit"]}).group_all("Categories2", inplace = False, aggregation = "mean")
        dm_temp1 = dm_temp1_capex.copy()
        dm_temp1.append(dm_temp1_capex_unit, "Variables")
        
        # put values before 2015 as nas
        idx = dm_temp1.idx
        years_na = np.array(range(1990,2015,1))
        dm_temp1.array[:,[idx[y] for y in years_na],...] = np.nan
        
        # append the other variables (with just 1 category)
        variables = dm_temp.col_labels["Categories1"]
        variables = np.array(variables)[[i not in keep for i in variables]].tolist()
        variables_new = [re.split("-", i)[0] for i in variables]
        dm_temp2 = dm_temp.filter({"Categories1" : variables})
        for i in range(len(variables)):
            dm_temp2.rename_col(variables[i], variables_new[i], "Categories1")
        dm_temp1.append(dm_temp2, "Categories1")
        dm_temp1.sort("Categories1")
        
        # write over
        DM_cost[key + "_bymat"] = dm_temp1

    # return
    return DM_cost

def variables_for_tpe(dm_cost_material_production_capex, dm_cost_CO2_capt_w_cc_capex,
                      dm_emissions_bygas, 
                      dm_material_production_bytech, dm_material_production_bymat,
                      dm_energy_demand_bymat, dm_energy_demand_bymatcarr, 
                      dm_energy_demand_bioener):
    
    # adjust variables' names
    dm_cost_material_production_capex.rename_col_regex("material-production_capex", "investment", "Variables")
    dm_cost_CO2_capt_w_cc_capex.rename_col_regex("CO2-capt-w-cc_capex", "investment_CC", "Variables")
    dm_emissions_bygas = dm_emissions_bygas.flatten()
    dm_emissions_bygas.rename_col_regex("_","-","Variables")
    variables = dm_material_production_bytech.col_labels["Categories1"]
    variables_new = [rename_tech_fordeepen(i) for i in variables]
    for i in range(len(variables)):
        dm_material_production_bytech.rename_col(variables[i], variables_new[i], dim = "Categories1")
        
    # convert kt to mt
    dm_material_production_bytech.change_unit('material-production', factor=1e-3, old_unit='kt', new_unit='Mt')
    dm_material_production_bymat.change_unit('material-production', factor=1e-3, old_unit='kt', new_unit='Mt')

    # material production total (chemicals done in ammonia)
    dm_mat_prod = dm_material_production_bymat.filter({"Categories1" : ["aluminium","cement","copper",
                                                                      "glass","lime","paper","steel"]})
    dm_mat_prod.rename_col('material-production', 'ind_material-production', 'Variables')
    
    # energy demand by material
    dm_energy_by_mat = dm_energy_demand_bymat.copy()
    dm_energy_by_mat.rename_col('energy-demand', 'ind_energy-demand', 'Variables')
    
    # emissions (done in emissions)
    
    # production technologies (aluminium, cement, paper, steel)
    dm_temp = dm_material_production_bytech.copy()
    dm_temp.groupby({'aluminium_sec': 'aluminium_sec.*',
                     'steel_scrap-EAF': 'steel_scrap-EAF-precons.*|teel_sec-postcons'}, 
                    dim='Categories1', regex=True, inplace=True)
    dm_prod_tech = dm_temp.filter({"Categories1" : ['aluminium_prim', 'aluminium_sec',
                                                    'cement_dry-kiln', 'cement_geopolym',
                                                    'cement_wet-kiln','paper_recycled',
                                                    'paper_woodpulp', 'steel_BF-BOF',
                                                    'steel_hisarna', 'steel_hydrog-DRI',
                                                    'steel_scrap-EAF']})
    dm_prod_tech.rename_col('material-production', 'ind_material-production', 'Variables')
    
    # energy demand for steel production (aluminium, cement, chem, glass, lime, paper, steel)
    dm_energy_by_carrier = dm_energy_demand_bymatcarr.filter({"Categories1": ['aluminium', 'cement', 'glass',
                                                                     'lime', 'paper', 'steel']})
    dm_energy_by_carrier.rename_col('energy-demand', 'ind_energy-demand', 'Variables')
    

    # dm_tpe
    dm_tpe = dm_emissions_bygas.copy()
    dm_tpe.append(dm_energy_by_mat.flatten(), "Variables")
    dm_tpe.append(dm_energy_by_carrier.flatten().flatten(), "Variables")
    dm_tpe.append(dm_energy_demand_bioener, "Variables")
    dm_tpe.append(dm_cost_CO2_capt_w_cc_capex.flatten(), "Variables")
    dm_tpe.append(dm_cost_material_production_capex.flatten(), "Variables")
    dm_tpe.append(dm_mat_prod.flatten(), "Variables")
    dm_tpe.append(dm_prod_tech.flatten(), "Variables")
    df = dm_tpe.write_df()

    # return
    return df

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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/industry_module.py"
# database_from_csv_to_datamatrix()
start = time.time()
results_run = local_industry_run()
end = time.time()
print(end-start)






