#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 30 15:55:39 2024

@author: echiarot
"""

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_database_to_ots_fts_dict, read_level_data, simulate_input, get_mindec, calibration_rates, cost, read_database_to_ots_fts_dict_w_groups
import pickle
import json
import os
import numpy as np
import re
import warnings
from scipy import interpolate
warnings.simplefilter("ignore")

def database_from_csv_to_datamatrix():
    
    # Read database
    
    #############################
    ##### FIXED ASSUMPTIONS #####
    #############################

    # # TODO: the code below is to put unpcatured emissions in fixed assumptions (in KNIME they were in calibration), delete at the end
    # # Read calibration
    # df = read_database_fxa('emissions_calibration')
    # dm_cal = DataMatrix.create_from_df(df, num_cat=0)
    # dm_cal = dm_cal.filter({"Variables" : ['cal_clm_emissions-CH4_uncaptured', 
    #                                        'cal_clm_emissions-CO2_uncaptured', 
    #                                        'cal_clm_emissions-N2O_uncaptured']})
    # dm_temp = dm_cal
    # idx = dm_temp.idx
    # arr_temp = dm_temp.array[idx["Germany"],...]
    # dm_temp.add(arr_temp, "Country", "EU27")
    # dm_temp.add(arr_temp, "Country", "Vaud")
    # dm_temp.sort("Country")
    # dm_temp.rename_col_regex(str1 = "cal_clm_", str2 = "ems_", dim = "Variables")
    # df = dm_temp.write_df()
    # import pandas as pd
    # df = pd.melt(df, id_vars=["Country","Years"])
    # df1 = pd.DataFrame({'geoscale' : df["Country"].values,
    #                     "timescale" : df["Years"].values,
    #                     "module" : "emissions",
    #                     "eucalc-name" : df["variable"].values,
    #                     "lever" : "ems_fixed-assumptions",
    #                     "level" : 0,
    #                     "string-pivot" : "none",
    #                     "type-prefix" : "none",
    #                     "module-prefix" : "ems",
    #                     "element" : [re.split("_", i)[1] for i in df["variable"].values],
    #                     "item" : [re.split("_", i)[2] for i in df["variable"].values],
    #                     "unit" : "Mt",
    #                     "value" : df["value"].values,
    #                     "reference-id" : "missing-reference",
    #                     "interaction-file" : "ems_fixed-assumptions"})
    # current_file_directory = os.path.dirname(os.path.abspath(__file__))
    # filepath = os.path.join(current_file_directory, '../_database/data/csv/emissions_fixed-assumptions.csv')
    # df1.to_csv(filepath, sep = ";", index = False)
    
    # Read fixed assumptions to datamatrix
    df = read_database_fxa('emissions_fixed-assumptions') # weird warning as there seems to be no repeated lines
    dm_fxa = DataMatrix.create_from_df(df, num_cat=0)    
    dict_fxa = {"uncaptured-emissions" : dm_fxa}
    
    ##################
    ##### LEVERS #####
    ##################
    
    # TODO: note that ems-after-2050 is used only in the more complex computation of CO2e, which is currently not done
    # here, but it's done in KNIME. We will use it when we'll implement this more complex computation also in python.

    dict_ots = {}
    dict_fts = {}
    
    ##### emissions post 2050 #####
    
    # Set years range
    years_setting = [1990, 2015, 2100, 1]
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int)) # make list with years from 1990 to 2015
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int)) # make list with years from 2020 to 2050 (steps of 5 years)
    years_all = years_ots + years_fts
    
    # get file
    file = 'climate_post-2050-emissions'
    lever = "ems-after-2050"
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear,
                                                        years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)
    
    # add EU27 and Vaud
    dm_temp = dict_ots["ems-after-2050"]
    idx = dm_temp.idx
    arr_temp = dm_temp.array[idx["Germany"],...]
    dm_temp.add(arr_temp, "Country", "EU27")
    dm_temp.add(arr_temp, "Country", "Vaud")
    dm_temp.sort("Country")
    dict_temp = dict_fts["ems-after-2050"]
    for key in dict_temp.keys():
        dm_temp = dict_temp[key]
        idx = dm_temp.idx
        arr_temp = dm_temp.array[idx["Germany"],...]
        dm_temp.add(arr_temp, "Country", "EU27")
        dm_temp.add(arr_temp, "Country", "Vaud")
        dm_temp.sort("Country")
    

    ################
    ##### SAVE #####
    ################

    DM_emissions = {
        'fxa': dict_fxa
        # 'fts': dict_fts,
        # 'ots': dict_ots,
    }

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/emissions.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_emissions, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # clean
    del baseyear, df, dm_fxa, DM_emissions,\
        f, handle, lastyear, startyear,\
        years_all, years_fts, years_ots, years_setting
        
    return

def read_data(data_file, lever_setting):
    
    # load dm
    with open(data_file, 'rb') as handle:
        DM_emissions = pickle.load(handle)
        
    # get fxa
    DM_fxa = DM_emissions['fxa']
        
    # # Get ots fts based on lever_setting (excluded for the moment)
    # DM_ots_fts = read_level_data(DM_emissions, lever_setting)

    # # get calibration
    # dm_cal = DM_emissions['calibration']

    # clean
    del handle, DM_emissions, data_file
    
    # return
    return DM_fxa

def emissions_equivalent(DM_interface, DM_fxa):
    
    # drop variables that are already aggregated
    # TODO: in DM_interface["electricity"] I have dropped "elc_emissions-CO2_fossil_total" to avoid to double counting in the overall sum, to be reported in the known issues
    DM_interface["electricity"].drop("Variables", ['elc_stored-CO2_RES_bio_gas', 'elc_stored-CO2_RES_bio_mass',
                                                   'elc_emissions-CO2_fossil_total'])
    DM_interface["transport"].drop("Variables", ['tra_passenger_CH4-emissions', 'tra_passenger_CO2-emissions', 
                                                 'tra_passenger_N2O-emissions', 'tra_freight_CH4-emissions', 
                                                 'tra_freight_CO2-emissions', 'tra_freight_N2O-emissions',
                                                 'tra_CH4-emissions', 'tra_CO2-emissions', 'tra_N2O-emissions'])
    
    # put together
    dm_ems = DM_interface["buildings"].copy()
    keys = ["district-heating","electricity","land-use","biodiversity",
            "industry", "ammonia", "refinery", "agriculture", "transport"]
    for key in keys:
        dm_ems.append(DM_interface[key], "Variables")
        
    # put in the uncaptured emissions
    dm_ems.append(DM_fxa["uncaptured-emissions"], "Variables")
    
    # linear interpolation for nans
    idx = dm_ems.idx
    countries = dm_ems.col_labels["Country"]
    variables = dm_ems.col_labels["Variables"]
    for c in countries:
        for v in variables:
            arr_temp = dm_ems.array[idx[c],:,idx[v]]
            nan_idx = np.isnan(arr_temp)
            nans_pos = np.where(nan_idx)[0]
            nonnan_pos = np.where(~nan_idx)[0]
            nonnan = arr_temp[nonnan_pos]
            arr_temp[nan_idx] = np.interp(nans_pos, nonnan_pos, nonnan)
    
    # apply eq coefficients
    # NOTE: here in knime they were multiplying by (12 / 44) to go grom MtCO2eq to MtC/year, but as then they convert back to MtCO2eq here I compute directly MtCO2eq (so no multiplication by (12 / 44))
    GWP_N2O = 265
    GWP_CH4 = 28
    GWP_SO2 = -40.0
    dm_ems_co2 = dm_ems.filter_w_regex({"Variables" : ".*CO2.*"})
    # dm_ems_co2.array = dm_ems_co2.array * (12 / 44)
    dm_ems_n2o = dm_ems.filter_w_regex({"Variables" : ".*N2O.*"})
    dm_ems_n2o.array = dm_ems_n2o.array * GWP_N2O
    dm_ems_ch4 = dm_ems.filter_w_regex({"Variables" : ".*CH4.*"})
    dm_ems_ch4.array = dm_ems_ch4.array * GWP_CH4
    so2_any = any([re.search("SO2", i) for i in dm_ems.col_labels["Variables"]])
    if so2_any:
        dm_ems_so2 = dm_ems.filter_w_regex({"Variables" : ".*SO2.*"})
        dm_ems_so2.array = dm_ems_so2.array * GWP_SO2
    dm_ems = dm_ems_co2
    dm_ems.append(dm_ems_n2o, "Variables")
    dm_ems.append(dm_ems_ch4, "Variables")
    if so2_any:
        dm_ems.append(dm_ems_so2, "Variables")
        del dm_ems_so2
        
    # sum to get total CO2e
    dm_ems.add(np.nansum(dm_ems.array, axis = -1, keepdims=True), "Variables", "clm_total_CO2e_ems","Mt")
        
    del arr_temp, c, countries, dm_ems_ch4, dm_ems_co2, dm_ems_n2o, GWP_CH4, GWP_N2O, \
        GWP_SO2, idx, key, keys, nan_idx, nans_pos, nonnan, nonnan_pos, v, variables
        
    return dm_ems

def variables_for_tpe(dm_ems):
    
    # biodiversity
    dm_tpe = dm_ems.filter_w_regex({"Variables" : ".*bdy.*"})
    dm_tpe.deepen()
    dm_tpe.group_all("Categories1")
    dm_tpe.rename_col("bdy", "bdy_emissions-CO2e", "Variables")
    
    # ammonia
    dm_amm = dm_ems.filter_w_regex({"Variables" : ".*amm.*"})
    dm_amm.rename_col_regex("_ammonia", "", "Variables")
    dm_amm.deepen()
    dm_amm.group_all("Categories1")
    dm_amm.rename_col("amm", "amm_emissions-CO2e", "Variables")
    dm_tpe.append(dm_amm, "Variables")
    
    # refinery
    dm_fos = dm_ems.filter_w_regex({"Variables" : ".*fos_emissions.*"})
    dm_fos.rename_col("fos_emissions-CO2","fos_emissions-CO2e","Variables")
    dm_tpe.append(dm_fos, "Variables")
    
    # electricity
    dm_elc = dm_ems.filter_w_regex({"Variables" : ".*elc.*CH4.*|.*elc.*N2O.*"})
    dm_elc.deepen("_emissions")
    dm_elc.group_all("Categories1")
    dm_elc.rename_col("elc", "elc_emissions-CO2e_RES_bio", "Variables")
    dm_tpe.append(dm_elc, "Variables")
    dm_elc = dm_ems.filter({"Variables" : ['elc_emissions-CO2_fossil_coal', 
                                           'elc_emissions-CO2_fossil_natural-gas', 
                                           'elc_emissions-CO2_fossil_oil']})
    dm_elc.rename_col_regex("CO2", "CO2e", "Variables")
    dm_tpe.append(dm_elc, "Variables")
    
    # agriculture
    dm_agr = dm_ems.filter_w_regex({"Variables" : ".*agr_emissions.*"})
    dm_agr.rename_col_regex("_","-","Variables")
    dm_agr.rename_col_regex("agr-emissions-N2O-","agr_emissions-N2O_","Variables")
    dm_agr.rename_col_regex("agr-emissions-CH4-","agr_emissions-CH4_","Variables")
    dm_agr.deepen_twice()
    dm_agr.group_all("Categories1")
    dm_agr = dm_agr.flatten()
    dm_agr.rename_col_regex("agr_", "agr_emissions-CO2e_", "Variables")
    dm_tpe.append(dm_agr, "Variables")
    dm_agr = dm_ems.filter_w_regex({"Variables" : ".*agr_input-use.*"})
    for i in dm_agr.col_labels["Variables"]:
        dm_agr.units[i] = "Mt"
    dm_tpe.append(dm_agr, "Variables")
    
    # # TODO: this code below is an example of what to do with agriculture if we keep variables' names, drop it once interfaces are finalized
    # dm_agr_crop = dm_ems.filter_w_regex({"Variables" : ".*agr.*crop.*"})
    # dm_agr_crop.deepen("_emissions-")
    # dm_agr_crop.deepen(based_on = "Categories1")
    # dm_agr_crop.group_all("Categories1")
    # dm_agr_crop = dm_agr_crop.flatten()
    # dm_agr_crop.rename_col_regex("agr_", "agr_emissions-CO2e_crop_", "Variables")
    # dm_tpe.append(dm_agr_crop, "Variables")
    # dm_agr_liv = dm_ems.filter_w_regex({"Variables" : ".*agr.*liv.*"})
    # dm_agr_liv.deepen()
    # dm_agr_liv.deepen(based_on = "Variables")
    # dm_agr_liv.switch_categories_order("Categories1","Categories2")
    # dm_agr_liv = dm_agr_liv.flatten()
    # dm_agr_liv.deepen("_emissions-",based_on="Variables")
    # dm_agr_liv.deepen()
    # dm_agr_liv.group_all("Categories2")
    
    # land use system
    dm_lus = dm_ems.filter_w_regex({"Variables" : ".*lus_emissions.*"})
    dm_lus.rename_col_regex("CO2", "CO2e", "Variables")
    dm_tpe.append(dm_lus, "Variables")
    
    # industry
    dm_ind = dm_ems.filter_w_regex({"Variables" : ".*ind_emissions.*"})
    dm_ind.deepen()
    dm_temp = dm_ind.filter({"Variables" : ['ind_emissions-CO2_biogenic'], 
                             "Categories1" : ["cement","paper","lime","chem","steel"]})
    dm_ind.drop("Variables", ['ind_emissions-CO2_biogenic'])
    # dm_temp = dm_ind.filter({"Variables" : ['ind_emissions-CO2', 'ind_emissions-CO2_biogenic']})
    # dm_ind.drop(dim = "Variables", col_label = "ind_emissions-CO2_biogenic")
    # idx = dm_ind.idx
    # dm_ind.array[:,:,idx["ind_emissions-CO2"],:] = np.nansum(dm_temp.array, axis = -2)
    dm_ind.deepen(based_on="Variables")
    dm_ind.group_all("Categories2")
    dm_ind.rename_col("ind","ind_emissions-CO2e","Variables")
    dm_ind = dm_ind.flatten()
    dm_tpe.append(dm_ind, "Variables")
    dm_temp.rename_col('ind_emissions-CO2_biogenic', 'ind_emissions-CO2e_biogenic', "Variables")
    dm_temp = dm_temp.flatten()
    dm_tpe.append(dm_temp, "Variables")
    
    # transport
    dm_tra = dm_ems.filter_w_regex({"Variables" : ".*tra_emissions.*"})
    dm_tra.deepen_twice()
    dm_tra.deepen(based_on="Variables")
    dm_tra.group_all("Categories3")
    dm_tra.rename_col("tra", "tra_emissions-CO2e","Variables")
    dm_tra = dm_tra.flatten().flatten()
    dm_tra.drop("Variables", ['tra_emissions-CO2e_freight_2W', 'tra_emissions-CO2e_freight_LDV', 
                              'tra_emissions-CO2e_freight_bus', 'tra_emissions-CO2e_freight_metro-tram',
                              'tra_emissions-CO2e_passenger_HDV', 'tra_emissions-CO2e_passenger_IWW',
                              'tra_emissions-CO2e_passenger_marine'])
    dm_tpe.append(dm_tra, "Variables")
    
    # building
    dm_bld = dm_ems.filter_w_regex({"Variables" : ".*bld_emissions.*"})
    dm_bld.rename_col_regex("CO2", "CO2e", "Variables")
    dm_tpe.append(dm_bld, "Variables")
    dm_bld = dm_ems.filter_w_regex({"Variables" : ".*bld_residential-emissions.*"})
    dm_tpe.append(dm_bld, "Variables")
    
    # district heating
    dm_dhg = dm_ems.filter_w_regex({"Variables" : ".*dhg_emissions.*"})
    dm_dhg.deepen_twice()
    dm_dhg.group_all("Categories1")
    dm_dhg.rename_col("dhg", "dhg_emissions-CO2e","Variables")
    dm_dhg = dm_dhg.flatten()
    dm_tpe.append(dm_dhg, "Variables")
    
    # total
    dm_tot = dm_ems.filter_w_regex({"Variables" : ".*clm_total.*"})
    dm_tpe.append(dm_tot, "Variables")
    
    dm_tpe.sort("Variables")
    
    del dm_agr, dm_amm, dm_bld, dm_dhg, dm_elc, dm_ems, dm_fos, dm_ind, dm_lus, \
        dm_temp, dm_tot, dm_tra, i
        
    return dm_tpe

def emissions(lever_setting, years_setting, interface = Interface(), calibration = False):
    
    # emissions data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    emissions_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/emissions.pickle')
    DM_fxa = read_data(emissions_data_file, lever_setting)
    
    # get / simulate interfaces
    DM_interface = {}
    from_sector = ["buildings","district-heating","electricity","land-use","biodiversity",
                   "industry", "ammonia", "refinery", "agriculture", "transport"]
    for i in from_sector:
        if interface.has_link(from_sector = i, to_sector = 'emissions'):
            DM_interface[i] = interface.get_link(from_sector=i, to_sector='emissions')
        else:
            DM_interface[i] = simulate_input(from_sector=i, to_sector="emissions")
    del from_sector, i
    
    # # sum by gas
    # dm_ems = sum_emissions_by_gas(DM_interface)
    
    # get emissions for gas equivalent
    dm_ems = emissions_equivalent(DM_interface, DM_fxa)
    dm_ems.sort("Variables")
    
    # get variables for tpe
    dm_tpe = variables_for_tpe(dm_ems)
    results_run = dm_tpe.write_df()
    
    # return
    return results_run

def local_emissions_run():
    
    # get years and lever setting
    years_setting = [1990, 2015, 2100, 1]
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
    lever_setting = json.load(f)[0]
    
    # get geoscale
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    # run
    results_run = emissions(lever_setting, years_setting)
    
    # return
    return results_run

# # run local
# __file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/emissions_module.py"
# # database_from_csv_to_datamatrix()
# results_run = local_emissions_run()

