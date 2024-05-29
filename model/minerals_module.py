#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  9 16:29:51 2024

@author: echiarot
"""

from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database_fxa
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, simulate_input, get_mindec, calibration_rates
import pandas as pd
import pickle
import os
import numpy as np
import re
import warnings
warnings.simplefilter("ignore")

def relative_reserve(minerals, dm, reserve_starting_year, mineral_type, range_max):

    prefix_1 = "min_reserve_"
    if mineral_type == "fossil_fuel":
        prefix_2 = "min_energy_"
    if mineral_type == "mineral":
        prefix_2 = "min_extraction_"
    warning_name = "min_" + mineral_type + "_warning"
    
    
    # create empty array for warning
    index_warning = np.empty(0)
    
    # create dictionary where to save things
    variabs_relresleft = ["min_relative_reserves_left_" + i + "[%]" for i in minerals]
    output = dict.fromkeys(variabs_relresleft, None)
    output[warning_name] = None
    output["Country"] = "Europe"
    output["Years"] = 2050
    
    for k in range(len(minerals)):
        
        # get names of reserves and mineral variables
        variabs_reserve = [prefix_1 + i for i in minerals]
        variabs_mineral = [prefix_2 + i for i in minerals]
        
        # get indexes
        idx = dm.idx
        
        # get last year of considered reserves
        reserve_starting = dm.array[:,idx[reserve_starting_year],idx[variabs_reserve[k]]]
        
        # get indexes for years after start reserves
        years = dm.col_labels["Years"]
        years = np.array(years)[[i > reserve_starting_year for i in years]].tolist()
        idx_years = [idx[i] for i in years]
        
        # make cumulative use of minerals
        mineral_yearly = dm.array[:,idx_years,idx[variabs_mineral[k]]] * 5
        mineral_cum = np.cumsum(mineral_yearly)
        
        # compute series for reserves left
        reserve_left = np.append(reserve_starting, reserve_starting - mineral_cum) 
        
        # get warning if there is no more reserves left in 2050 
        relative_reserve_left = (reserve_left[len(reserve_left)-1]/reserve_left[0] - 1)*-100
        output[variabs_relresleft[k]] = relative_reserve_left
        
        if 100 <= relative_reserve_left <= range_max:
            index_warning = np.append(index_warning, 1)
    
    # count how many warnings for minerals
    index_warning = np.count_nonzero(index_warning)
    if index_warning == 0:
        index_warning = 0
    if index_warning == 1:
        index_warning = 1
    if index_warning >= 2:
        index_warning = 2
    
    # store warnings
    output[warning_name] = index_warning
    
    return output

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

    #####################
    # FIXED ASSUMPTIONS #
    #####################

    # Read fixed assumptions to datamatrix
    df = read_database_fxa('minerals_fixed-assumptions')
    dm = DataMatrix.create_from_df(df, num_cat=0)
    
    # Keep only ots and fts years
    dm = dm.filter(selected_cols={'Years': years_all})
    dm.col_labels

    # make data matrixes with specific data using regular expression (regex)
    dm_elec_new = dm.filter_w_regex({'Variables': 'elc_new_RES.*|elc_new.*|.*solar.*'})
    dm_elec_new.col_labels
    dm_min_other = dm.filter_w_regex({'Variables': 'min_other.*'})
    dm_min_proportion = dm.filter_w_regex({'Variables': 'min_proportion.*'})

    # save
    dict_fxa = {
        'elec_new': dm_elec_new,
        'min_other': dm_min_other,
        'min_proportion': dm_min_proportion
    }
    
    ###############
    # CALIBRATION #
    ###############
    
    # Read calibration
    df = read_database_fxa('minerals_calibration')
    dm_cal = DataMatrix.create_from_df(df, num_cat=0)

    #############
    # CONSTANTS #
    #############

    # Load constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_ind_material-efficiency.*|cp_min.*', num_cat=0)

    ########
    # SAVE #
    ########

    DM_minerals = {
        'fxa': dict_fxa,
        'calibration': dm_cal,
        'constant': cdm_const
    }
    
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/minerals.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_minerals, handle, protocol=pickle.HIGHEST_PROTOCOL)
        

    del baseyear, cdm_const, df, dict_fxa, dm, dm_elec_new, dm_min_other, dm_min_proportion, DM_minerals, f, handle, lastyear,\
        startyear, step_fts, years_all, years_fts, years_ots, years_setting
        
    return

def read_data(data_file):
    
    # load datamatrixes
    with open(data_file, 'rb') as handle:
        DM_minerals = pickle.load(handle)
        
    # get constants
    cdm_constants = DM_minerals["constant"].copy()
    cdm_constants.rename_col_regex(str1 = "cp_",str2 = "",dim = "Variables")
        
    # return
    return DM_minerals, cdm_constants

def rename_interfaces(DM_interface):

    # files' names
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
        
    # rename interfaces
    filepath = os.path.join(current_file_directory, '../_database/data/csv/minerals_variables-names.csv')
    df_names = pd.read_csv(filepath, sep=",")

    for key in DM_interface.keys():
        
        if key in df_names["module_input"].values:
            
            dm_temp = DM_interface[key] # puntator
            idx_temp = df_names["old_name"].isin(dm_temp.col_labels["Variables"])
            old_name = df_names.loc[idx_temp,"old_name"].values.tolist()
            new_name = df_names.loc[idx_temp,"new_name"].values.tolist()
            
            if len(old_name)>0:
                for i in range(len(old_name)):
                    dm_temp.rename_col(col_in = old_name[i], col_out = new_name[i], dim = "Variables")
                    
    # return
    return DM_interface
    
def product_demand(DM_minerals, DM_interface, cdm_constants):

    # get fxa
    DM_fxa = DM_minerals['fxa']

    # get datamatrixes
    dm_tra = DM_interface["transport"]
    dm_bld = DM_interface["buildings"]
    dm_str = DM_interface["storage"]
    
    #####################
    ##### TRANSPORT #####
    #####################

    # make 2020 as mean of before and after for subways, planes, ships, trains
    idx = dm_tra.idx
    variabs = ["tra_other-subways","tra_other-planes","tra_other-ships","tra_other-trains"]
    for i in variabs:
        dm_tra.array[:,idx[2020],idx[i]] = (dm_tra.array[:,idx[2015],idx[i]] + \
                                            dm_tra.array[:,idx[2025],idx[i]])/2
    del idx, variabs

    # demand for vehicles [num]
    tra_veh = ['HDVH-EV','HDVH-FCEV','HDVH-ICE','HDVH-PHEV','HDVL-EV','HDVL-FCEV',
               'HDVL-ICE','HDVL-PHEV','HDVM-EV','HDVM-FCEV','HDVM-ICE','HDVM-PHEV','LDV-EV','LDV-FCEV','LDV-ICE','LDV-PHEV',
               '2W-EV','2W-FCEV','2W-ICE','2W-PHEV','bus-EV','bus-FCEV','bus-ICE','bus-PHEV',
               'other-planes', 'other-ships', 'other-subways', 'other-trains']

    find = ["tra_" + i for i in tra_veh]
    dm_tra_veh = dm_tra.filter(selected_cols = {"Variables":find})
    dm_tra_veh.deepen()
    dm_tra_veh.rename_col(col_in = "tra", col_out = "product-demand", dim="Variables")
    # note that in dm_tra_veh.idx now product-demand appears as last, but this is fine as the order of idx is not important, what's important
    # is the value of the key


    #######################
    ##### ELECTRONICS #####
    #######################

    # filter
    electr = ['electronics-computer','electronics-phone', 'electronics-tv']
    find = ["bld_" + i for i in electr]
    dm_electr = dm_bld.filter(selected_cols = {"Variables":find})

    # deepen
    dm_electr.deepen()
    dm_electr.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")


    #####################
    ##### BATTERIES #####
    #####################

    # this is demand for installed capacity of batteries, expressed in kWh

    # get demand for batteries from energy sector
    dm_battery = dm_str.filter_w_regex({"Variables": ".*battery.*"})
        
    # convert from GW to kWh
    dm_battery.array = dm_battery.array * 1000000
    dm_battery.units['str_energy-battery'] = "kWh"

    # deepen
    dm_battery.deepen()
    dm_battery.rename_col(col_in = "str", col_out = "product-demand", dim="Variables")

    # get demand for batteries from transport and electronics

    # get kWh from constants
    cdm_temp = cdm_constants.filter_w_regex({"Variables": ".*batveh.*"})
    cdm_temp.deepen()

    # get transport and electronics variables which correspond to the constants

    cdm_variabs = cdm_temp.col_labels["Categories1"]
    dm_tra_veh_variabs = dm_tra_veh.col_labels["Categories1"]
    dm_electr_variabs = dm_electr.col_labels["Categories1"]

    dm_tra_veh_variabs = np.array(dm_tra_veh_variabs)[[i in cdm_variabs for i in dm_tra_veh_variabs]].tolist()
    dm_electr_variabs = np.array(dm_electr_variabs)[[i in cdm_variabs for i in dm_electr_variabs]].tolist()

    # put them together
    dm_temp = dm_tra_veh.filter({"Categories1":dm_tra_veh_variabs})
    dm_temp2 = dm_electr.filter({"Categories1":dm_electr_variabs})

    dm_temp.append(dm_temp2, dim = "Categories1")

    # sort
    dm_temp.sort(dim = "Categories1")
    cdm_temp.sort(dim = "Categories1")

    # multiply demand of product (item) and kWh
    arr_temp = dm_temp.array * cdm_temp.array[np.newaxis,np.newaxis,...]
    dm_temp.add(arr_temp, dim = "Variables", col_label = "battery_demand", unit="kWh")

    # split between transport and electronics
    dm_temp_tra = dm_temp.filter({"Categories1":dm_tra_veh_variabs})
    dm_temp_tra = dm_temp_tra.filter({"Variables":["battery_demand"]})

    dm_temp_electr = dm_temp.filter({"Categories1":dm_electr_variabs})
    dm_temp_electr = dm_temp_electr.filter({"Variables":["battery_demand"]})

    # sum and put in dm_battery
    arr_temp = np.nansum(dm_temp_tra.array, axis=-1, keepdims = True)
    dm_battery.add(arr_temp, dim = "Categories1", col_label = "transport-battery")

    arr_temp = np.nansum(dm_temp_electr.array, axis=-1, keepdims = True)
    dm_battery.add(arr_temp, dim = "Categories1", col_label = "electronics-battery")

    # sort
    dm_battery.sort(dim = "Categories1")

    # clean
    del arr_temp, cdm_temp, cdm_variabs, dm_electr_variabs, dm_temp, dm_temp2, dm_temp_electr, dm_temp_tra,\
        dm_tra_veh_variabs, i

    ##########################
    ##### INFRASTRUCTURE #####
    ##########################

    # demand for infrastructure [km]
    tra_inf = ['infra-rail', 'infra-road', 'infra-trolley-cables']
    find = ["tra_" + i for i in tra_inf]
    dm_infra = dm_tra.filter(selected_cols = {"Variables":find})

    # get infra in bld
    bld_infra = ['infra-pipe']
    find = ["bld_" + i for i in bld_infra]
    dm_infra_temp = dm_bld.filter({"Variables": find})
    dm_infra_temp.rename_col_regex(str1 = "bld", str2 = "tra", dim="Variables")

    # append
    dm_infra.append(dm_infra_temp, dim = "Variables")

    # deepen
    dm_infra.deepen()
    dm_infra.rename_col(col_in = "tra", col_out = "product-demand", dim="Variables")

    del dm_infra_temp

    ##############################
    ##### DOMESTIC APPLIANCE #####
    ##############################

    # get domestic appliances in bld
    domapp = ['dom-appliance-dishwasher','dom-appliance-dryer','dom-appliance-freezer',
              'dom-appliance-fridge','dom-appliance-wmachine',]
    find = ["bld_" + i for i in domapp]
    dm_domapp = dm_bld.filter({"Variables": find})

    # deepen
    dm_domapp.deepen()
    dm_domapp.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")

    ########################
    ##### CONSTRUCTION #####
    ########################

    # get floor area
    constr = ['floor-area-new-non-residential', 'floor-area-new-residential', 
             'floor-area-reno-non-residential', 'floor-area-reno-residential']
    find = ["bld_" + i for i in constr]
    dm_constr = dm_bld.filter({"Variables": find})

    # deepen
    dm_constr.deepen()
    dm_constr.rename_col(col_in = "bld", col_out = "product-demand", dim="Variables")

    ##################
    ##### ENERGY #####
    ##################

    # this is the demand for energy that comes from different energy sources, expressed in GW (power)

    # get fts, which are in dm_str

    energy = ['energy-coal', 'energy-csp', 'energy-gas', 'energy-geo', 'energy-hydro', 
              'energy-marine', 'energy-nuclear', 'energy-off-wind', 'energy-oil', 
              'energy-on-wind','energy-pvroof','energy-pvutility']
    find = ["elc_" + i for i in energy]
    dm_energy_fts = dm_str.filter({"Variables": find})

    # add pvroof and pvutility
    dm_energy_fts.operation('elc_energy-pvroof', "+", 'elc_energy-pvutility', dim = "Variables", out_col="elc_pv", unit="GW", div0="error")
    dm_energy_fts.drop(dim = "Variables", col_label = ['elc_energy-pvroof','elc_energy-pvutility'])

    # new variables
    energy = ['energy-coal', 'energy-csp', 'energy-gas', 'energy-geo', 'energy-hydro', 
              'energy-marine', 'energy-nuclear', 'energy-off-wind', 'energy-oil', 
              'energy-on-wind','energy-pv']

    # deepen
    dm_energy_fts.deepen()

    # get ots, which are in fxa

    dm_energy_ots = DM_fxa["elec_new"].copy()
    dm_energy_ots.rename_col_regex("_tech", "", dim = "Variables")
    dm_energy_ots.rename_col_regex("_new_RES", "", dim = "Variables")
    dm_energy_ots.rename_col_regex("_new_fossil", "", dim = "Variables")
    dm_energy_ots.rename_col_regex("elc_", "elc_energy-", dim = "Variables")
    # !FIXME: at the moment we do not have ots for oil and coal

    # make all zeroes for oil and coal ots for the moment
    c , y = len(dm_energy_ots.col_labels["Country"]), len(dm_energy_ots.col_labels["Years"])
    arr_temp = np.zeros((c, y))
    dm_energy_ots.add(arr_temp, dim = "Variables", col_label = "elc_energy-coal", unit="GW")
    dm_energy_ots.add(arr_temp, dim = "Variables", col_label = "elc_energy-oil", unit="GW")

    # deepen
    dm_energy_ots.deepen()

    # sort
    dm_energy_fts.sort(dim = "Categories1")
    dm_energy_ots.sort(dim = "Categories1")

    # add and save in dm_energy
    arr_temp = dm_energy_ots.array + dm_energy_fts.array
    dm_energy = dm_energy_ots.copy()
    dm_energy.add(arr_temp, dim = "Variables", col_label = "product-demand", unit="GW")
    dm_energy.drop(dim = "Variables", col_label = ['elc'])

    # clean
    del arr_temp, c, dm_energy_fts, dm_energy_ots, find, y

    ########################
    ##### PUT TOGETHER #####
    ########################

    DM_demand = {"vehicles" : dm_tra_veh,
                 "electronics" : dm_electr, 
                  "batteries" : dm_battery, 
                  "infrastructure" : dm_infra, 
                  "dom-appliance" : dm_domapp, 
                  "construction" : dm_constr, 
                  "energy" : dm_energy}

    # clean
    del dm_tra_veh, dm_electr, dm_battery, dm_infra, dm_domapp, dm_constr, dm_energy
    
    # return
    return DM_demand
    
def product_import(DM_interface):
    
    # get datamatrixes
    dm_ind = DM_interface["industry"]
    
    # get imports and rename
    dm_import = dm_ind.filter_w_regex({"Variables":".*import.*"})
    dm_import.rename_col_regex(str1 = "_product-net-import", str2 = "", dim = "Variables")

    # add net imports for categories of vehicles we do not have
    variabs = ["LDV-ICE", "HDVL-ICE", "other-trains", "LDV-ICE","LDV-ICE","LDV-ICE","LDV-ICE","HDVL-ICE","HDVL-ICE",
               "HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE","HDVL-ICE"]
    variabs = ["ind_" + i for i in variabs]
    variabs_new = ["LDV-PHEV","HDVL-PHEV","other-subways","2W-EV","2W-ICE","2W-FCEV","2W-PHEV","bus-EV","bus-ICE",
                   "bus-FCEV","bus-PHEV","HDVM-EV","HDVM-ICE","HDVM-FCEV","HDVM-PHEV","HDVH-EV","HDVH-ICE","HDVH-FCEV","HDVH-PHEV"]
    variabs_new = ["ind_" + i for i in variabs_new]

    idx = dm_import.idx
    for i in range(len(variabs)):
        dm_import.add(dm_import.array[:,:,idx[variabs[i]]], dim="Variables", col_label=variabs_new[i], unit="%")
        
    # sort
    dm_import.sort(dim = "Variables")
        
    # clean
    del i, idx, variabs, variabs_new
    
    # return
    return dm_import

def product_demand_split(DM_demand, dm_import, cdm_constants):
    
    ###################################
    ##### SHARE OF PRODUCT DEMAND #####
    ###################################
    
    # demand split
    dm_demand_split_share = dm_import.copy()

    # product indirect demand
    name_old = dm_demand_split_share.col_labels["Variables"]
    name_new = [i + "_indir" for i in name_old]
    for i in range(len(name_old)):
        dm_demand_split_share.rename_col(col_in = name_old[i], col_out = name_new[i], dim = "Variables")

    # deepen
    dm_demand_split_share.deepen_twice()
    dm_demand_split_share.rename_col(col_in = "ind", col_out = "product-demand-split-share", dim = "Variables")

    # product net export
    arr_temp = -dm_demand_split_share.array
    dm_demand_split_share.add(arr_temp, dim = "Categories2", col_label = "exp", unit = "%")

    # product direct demand
    idx = dm_demand_split_share.idx
    arr_temp = dm_demand_split_share.array[:,:,:,:,idx["indir"]]-dm_demand_split_share.array[:,:,:,:,idx["indir"]]+1
    dm_demand_split_share.add(arr_temp, dim = "Categories2", col_label = "dir", unit = "%")

    # add to dm_trade the share for other products from constants
    countries_list = dm_demand_split_share.col_labels["Country"]
    years_list = dm_demand_split_share.col_labels["Years"]
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*trade*"})
    cdm_temp = cdm_to_dm(cdm_temp, countries_list, years_list)

    # deepen
    cdm_temp.deepen_twice()
    cdm_temp.rename_col(col_in = "min_trade", col_out = "product-demand-split-share", dim = "Variables")

    # append
    dm_demand_split_share.append(cdm_temp, dim = "Categories1")

    # sort
    dm_demand_split_share.sort(dim = "Categories1")
    # note: careful that here sorts first the variables with cap letters

    # clean
    del arr_temp, cdm_temp, i, idx, name_new, name_old
    
    #################
    ##### UNITS #####
    #################

    # create empty dictionary without constructions (they are assumed not to be traded)
    DM_demand_split = dict.fromkeys(["vehicles","electronics", "batteries", 
                                     "infrastructure", "dom-appliance", "energy"])

    for key in DM_demand_split.keys():

        # get demand
        dm_demand_temp = DM_demand[key]
        
        # get corresponding split share
        dm_demand_split_temp = dm_demand_split_share.filter({"Categories1": dm_demand_temp.col_labels["Categories1"]})
        arr_temp = dm_demand_temp.array[...,np.newaxis] * dm_demand_split_temp.array
        
        # add split in unit as a variable
        dm_demand_split_temp.add(arr_temp, dim = "Variables", 
                                 col_label = "product-demand-split-unit", unit=dm_demand_temp.units["product-demand"])
        
        # drop product demand split share
        dm_demand_split_temp.drop(dim = "Variables", col_label = ["product-demand-split-share"])
        
        # put dm in dictionary
        DM_demand_split[key] = dm_demand_split_temp

    # clean
    del key, dm_demand_temp, dm_demand_split_temp, arr_temp
    
    # return
    return DM_demand_split

def mineral_demand_split(DM_minerals, DM_interface, DM_demand, DM_demand_split, cdm_constants):
    
    # name of minerals
    minerals = ['aluminium','copper','graphite','lead','lithium','manganese','nickel','steel']
    
    # get data
    DM_fxa = DM_minerals['fxa']
    dm_ind = DM_interface["industry"]
    dm_str = DM_interface["storage"]

    #####################
    ##### BATTERIES #####
    #####################

    # get product demand split unit
    dm_temp = DM_demand_split["batteries"]

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*battery*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|energytech).)*$"})
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_battery_mindec = get_mindec(dm_temp, cdm_temp)

    # clean
    del dm_temp, cdm_temp

    ######################
    ##### CARS (LDV) #####
    ######################

    # get names
    tra_veh = ['HDVH-EV','HDVH-FCEV','HDVH-ICE','HDVH-PHEV','HDVL-EV','HDVL-FCEV',
               'HDVL-ICE','HDVL-PHEV','HDVM-EV','HDVM-FCEV','HDVM-ICE','HDVM-PHEV','LDV-EV','LDV-FCEV','LDV-ICE','LDV-PHEV',
               '2W-EV','2W-FCEV','2W-ICE','2W-PHEV','bus-EV','bus-FCEV','bus-ICE','bus-PHEV',
               'other-planes', 'other-ships', 'other-subways', 'other-trains']
    tra_ldv = np.array(tra_veh)[[bool(re.search("LDV", str(i), flags=re.IGNORECASE)) for i in tra_veh]].tolist()

    # get product demand split unit
    dm_temp = DM_demand_split["vehicles"]
    dm_temp = dm_temp.filter_w_regex({"Categories1":".*LDV*"})

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*LDV*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_veh_ldv_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across vehicles
    arr_temp = np.nansum(dm_veh_ldv_mindec.array, axis=-3, keepdims = True)
    dm_veh_ldv_mindec.add(arr_temp, dim = "Categories1", col_label = "LDV")
    dm_veh_ldv_mindec.drop(dim = "Categories1", col_label = tra_ldv)

    # get mineral switch parameter
    dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-cars*"})

    # set variables with mineral that is switched
    mineral_in = "steel"
    mineral_out = "other"

    mineral_in_unadj = mineral_in + "-unadj"
    mineral_switched = mineral_in + "-switched-to-" + mineral_out

    dm_veh_ldv_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")

    # for mineral that is switched, get how much is switched and add it as new variable
    idx = dm_veh_ldv_mindec.idx
    arr_temp = dm_veh_ldv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
    arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
    dm_veh_ldv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

    # do mineral unadjusted - mineral switched
    dm_veh_ldv_mindec.operation(col1 = mineral_in_unadj, operator = "-", col2 = mineral_switched, dim = "Categories3",
                            out_col = mineral_in)

    # for indir, substitute back the unadjusted one (adjustment is only done on exp and dir)
    dm_veh_ldv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_veh_ldv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]

    # drop
    dm_veh_ldv_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_switched])

    # clean
    del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_switched, mineral_in_unadj, idx, arr_temp


    ########################
    ##### TRUCKS (HDV) #####
    ########################

    # get names
    tra_hdv = np.array(tra_veh)[[bool(re.search("HDV", str(i), flags=re.IGNORECASE)) for i in tra_veh]].tolist()

    # get product demand split unit
    dm_temp = DM_demand_split["vehicles"]
    dm_temp = dm_temp.filter_w_regex({"Categories1":".*HDV*"})

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*HDV*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_veh_hdv_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across vehicles
    arr_temp = np.nansum(dm_veh_hdv_mindec.array, axis=-3, keepdims = True)
    dm_veh_hdv_mindec.add(arr_temp, dim = "Categories1", col_label = "HDV")
    dm_veh_hdv_mindec.drop(dim = "Categories1", col_label = tra_hdv)

    # do the switch steel to other and steel to aluminium

    # get mineral switch parameter
    dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-trucks-steel-other*"})
    dm_temp_alu = dm_ind.filter_w_regex({"Variables":".*switch-trucks-steel-aluminium*"})

    # set variables with mineral that is switched
    mineral_in = "steel"
    mineral_out = "other"
    mineral_out2 = "aluminium"

    mineral_in_unadj = mineral_in + "-unadj"
    mineral_out2_unadj = mineral_out2 + "-unadj"

    mineral_switched = mineral_in + "-switched-to-" + mineral_out
    mineral_switched2 = mineral_in + "-switched-to-" + mineral_out2

    dm_veh_hdv_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")
    dm_veh_hdv_mindec.rename_col(col_in = mineral_out2, col_out = mineral_out2_unadj, dim = "Categories3")

    # for mineral that is switched, get how much is switched and add it as new variable
    idx = dm_veh_hdv_mindec.idx

    arr_temp = dm_veh_hdv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
    arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
    dm_veh_hdv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

    arr_temp = dm_veh_hdv_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
    arr_temp = arr_temp[...,np.newaxis] * dm_temp_alu.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
    dm_veh_hdv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched2)

    # do mineral unadjusted - mineral switched
    idx = dm_veh_hdv_mindec.idx
    arr_temp = dm_veh_hdv_mindec.array[...,idx[mineral_in_unadj]] - \
        dm_veh_hdv_mindec.array[...,idx[mineral_switched]] - \
            dm_veh_hdv_mindec.array[...,idx[mineral_switched2]]
    dm_veh_hdv_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_in)

    # do aluminium + steel-switched-to-aluminium
    dm_veh_hdv_mindec.operation(col1 = mineral_out2_unadj, operator = "+", col2 = mineral_switched2, dim = "Categories3",
                            out_col = mineral_out2)

    # for indir, substitute back the unadjusted ones (adjustment is only done on exp and dir)
    dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]
    dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_out2]] = dm_veh_hdv_mindec.array[:,:,:,:,idx["indir"],idx[mineral_out2_unadj]]

    # drop
    dm_veh_hdv_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_out2_unadj, mineral_switched, mineral_switched2])

    # sort
    dm_veh_hdv_mindec.sort("Categories3")

    # clean
    del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_out2, mineral_switched, \
        mineral_switched2, mineral_in_unadj, mineral_out2_unadj, idx, arr_temp, dm_temp_alu

    ##########################
    ##### OTHER VEHICLES #####
    ##########################

    # get other vehicles
    tra_oth = ['2W-EV','2W-FCEV','2W-ICE','2W-PHEV','bus-EV','bus-FCEV','bus-ICE','bus-PHEV',
               'other-planes', 'other-ships', 'other-subways', 'other-trains']

    # get product demand split unit
    dm_temp = DM_demand_split["vehicles"]
    dm_temp = dm_temp.filter({"Categories1":tra_oth})

    # get constants for mineral decomposition
    find = [".*" + i + ".*" for i in tra_oth]
    cdm_temp = cdm_constants.filter_w_regex({"Variables": "|".join(find)})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!batveh).)*$"})
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_veh_oth_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across vehicles
    arr_temp = np.nansum(dm_veh_oth_mindec.array, axis=-3, keepdims = True)
    dm_veh_oth_mindec.add(arr_temp, dim = "Categories1", col_label = "other")
    dm_veh_oth_mindec.drop(dim = "Categories1", col_label = tra_oth)

    # clean
    del dm_temp, cdm_temp, arr_temp, find


    ###########################
    ##### TRANSPORT TOTAL #####
    ###########################

    # get batteries for transport
    dm_veh_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['transport-battery']})

    # add missing minerals to the dms
    DM_temp = {"ldv": dm_veh_ldv_mindec, 
               "hdv": dm_veh_hdv_mindec, 
               "oth": dm_veh_oth_mindec, 
               "batt" : dm_veh_batt_mindec}


    for key in DM_temp.keys():
        
        variables = DM_temp[key].col_labels["Categories3"]
        variables_missing = np.array(minerals)[[i not in variables for i in minerals]].tolist()
        
        for variable in variables_missing:
            DM_temp[key].add(np.nan, dim = "Categories3", col_label = variable, dummy = True)

    # sum across vehicles and batteries
    dm_veh_mindec = dm_veh_ldv_mindec.copy()
    dm_veh_mindec.append(dm_veh_hdv_mindec, dim = "Categories1")
    dm_veh_mindec.append(dm_veh_oth_mindec, dim = "Categories1")
    dm_veh_mindec.append(dm_veh_batt_mindec, dim = "Categories1")
    arr_temp = np.nansum(dm_veh_mindec.array, axis=-3, keepdims = True)
    dm_veh_mindec.add(arr_temp, dim = "Categories1", col_label = "transport")
    dm_veh_mindec.drop(dim = "Categories1", col_label = ['LDV', 'HDV', 'other', 'transport-battery'])

    del dm_veh_ldv_mindec, dm_veh_hdv_mindec, dm_veh_oth_mindec, arr_temp, DM_temp, variable, variables, variables_missing


    ##########################
    ##### INFRASTRUCTURE #####
    ##########################
    
    # names for infra
    tra_inf = ['infra-rail', 'infra-road', 'infra-trolley-cables']
    bld_infra = ['infra-pipe']
    infra = tra_inf + bld_infra

    # get product demand split unit
    dm_temp = DM_demand_split["infrastructure"]

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*infra*"})
    cdm_temp.rename_col_regex(str1 = "infra_", str2 = "infra-", dim = "Variables")
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_infra_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across infra
    arr_temp = np.nansum(dm_infra_mindec.array, axis=-3, keepdims = True)
    dm_infra_mindec.add(arr_temp, dim = "Categories1", col_label = "infra")
    dm_infra_mindec.drop(dim = "Categories1", col_label = infra)

    # clean
    del dm_temp, cdm_temp, arr_temp


    ##############################
    ##### DOMESTIC APPLIANCE #####
    ##############################
    
    # names for domapp
    domapp = ['dom-appliance-dishwasher','dom-appliance-dryer','dom-appliance-freezer',
              'dom-appliance-fridge','dom-appliance-wmachine']

    # get product demand split unit
    dm_temp = DM_demand_split["dom-appliance"]

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*appliance*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!min_other).)*$"})
    cdm_temp.rename_col_regex(str1 = "appliance", str2 = "dom-appliance", dim = "Variables")
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_domapp_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across dom appliance
    arr_temp = np.nansum(dm_domapp_mindec.array, axis=-3, keepdims = True)
    dm_domapp_mindec.add(arr_temp, dim = "Categories1", col_label = "dom-appliance")
    dm_domapp_mindec.drop(dim = "Categories1", col_label = domapp)

    # get factor for materials coming from unaccounted appliances
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*min_other_dom*"})
    cdm_temp.rename_col_regex(str1 = "other_dom-appliances", str2 = "other-dom-appliance", dim = "Variables")
    cdm_temp.deepen_twice()
    cdm_temp.sort("Categories2")

    # divide mineral split by this factor (to get mineral + extra mineral from unaccounted sectors)
    dm_domapp_mindec.array = dm_domapp_mindec.array / cdm_temp.array[np.newaxis,np.newaxis,np.newaxis,...]

    # get aluminium packages (t) and add it to aluminium from dom appliance (only for dir)
    dm_temp = dm_ind.filter({"Variables":["ind_product_aluminium-pack"]})
    dm_temp.array = dm_temp.array * 1000 # make kg
    idx = dm_domapp_mindec.idx
    dm_domapp_mindec.array[:,:,:,:,idx["dir"],idx["aluminium"]] = dm_domapp_mindec.array[:,:,:,:,idx["dir"],idx["aluminium"]] + \
        dm_temp.array[...,np.newaxis]

    # clean
    del dm_temp, cdm_temp, arr_temp, idx


    #######################
    ##### ELECTRONICS #####
    #######################
    
    # names of electronics
    electr = ['electronics-computer','electronics-phone', 'electronics-tv']

    # get product demand split unit
    dm_temp = DM_demand_split["electronics"]

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*electr*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|batveh|battery).)*$"})
    cdm_temp.rename_col_regex(str1 = "electronics_", str2 = "electronics-", dim = "Variables")
    cdm_temp.deepen_twice()

    # get minderal decomposition
    dm_electr_cotvph_mindec = get_mindec(dm_temp, cdm_temp)

    # get batteries for electronics
    dm_electr_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['electronics-battery']})

    # add missing minerals to the dms
    DM_temp = {"electr": dm_electr_cotvph_mindec, 
               "batt": dm_electr_batt_mindec}

    for key in DM_temp.keys():
        
        variables = DM_temp[key].col_labels["Categories3"]
        variables_missing = np.array(minerals)[[i not in variables for i in minerals]].tolist()
        
        for variable in variables_missing:
            DM_temp[key].add(np.nan, dim = "Categories3", col_label = variable, dummy = True)
        
    # append
    dm_electr_cotvph_mindec.append(dm_electr_batt_mindec, dim = "Categories1")

    # get sum across electr
    arr_temp = np.nansum(dm_electr_cotvph_mindec.array, axis=-3, keepdims = True)
    dm_electr_cotvph_mindec.add(arr_temp, dim = "Categories1", col_label = "electronics")
    electr = electr + ["electronics-battery"]
    dm_electr_cotvph_mindec.drop(dim = "Categories1", col_label = electr)

    # copy
    dm_electr_mindec = dm_electr_cotvph_mindec.copy()

    # clean
    del dm_electr_cotvph_mindec, dm_electr_batt_mindec, dm_temp, cdm_temp, arr_temp, DM_temp, key


    ########################
    ##### CONSTRUCTION #####
    ########################
    
    # names of construction
    constr = ['floor-area-new-non-residential', 'floor-area-new-residential', 
              'floor-area-reno-non-residential', 'floor-area-reno-residential']

    # get product demand split unit
    dm_temp = DM_demand["construction"].copy()

    # convert Mm2 to m2
    dm_temp.array = dm_temp.array * 1000000
    dm_temp.units["product-demand"] = "m2"

    # expand of 1 dimension
    dm_temp.array = dm_temp.array[...,np.newaxis]
    dm_temp.col_labels["Categories2"] = ["dir"]
    dm_temp.dim_labels = dm_temp.dim_labels + ["Categories2"]
    dm_temp.idx["Categories2"] = 0

    # add exp and indir as nan 
    variables_missing = ["exp", "indir"]
    for variable in variables_missing:
        dm_temp.add(np.nan, dim = "Categories2", col_label = variable, dummy = True)

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*building*"})
    cdm_temp.rename_col_regex(str1 = "building_", str2 = "building-", dim = "Variables")
    cdm_temp.rename_col_regex(str1 = "new_", str2 = "new-", dim = "Variables")
    cdm_temp.rename_col_regex(str1 = "reno_", str2 = "reno-", dim = "Variables")
    cdm_temp.deepen_twice()

    # get mineral decomposition
    dm_constr_mindec = get_mindec(dm_temp, cdm_temp)

    # get sum across buildings
    arr_temp = np.nansum(dm_constr_mindec.array, axis=-3, keepdims = True)
    dm_constr_mindec.add(arr_temp, dim = "Categories1", col_label = "construction")
    dm_constr_mindec.drop(dim = "Categories1", col_label = constr)

    # get mineral switch parameter
    dm_temp = dm_ind.filter_w_regex({"Variables":".*switch-build*"})

    # set variables with mineral that is switched
    mineral_in = "steel"
    mineral_out = "timber"

    mineral_in_unadj = mineral_in + "-unadj"
    mineral_switched = mineral_in + "-switched-to-" + mineral_out

    dm_constr_mindec.rename_col(col_in = mineral_in, col_out = mineral_in_unadj, dim = "Categories3")

    # for mineral that is switched, get how much is switched and add it as new variable
    idx = dm_constr_mindec.idx
    arr_temp = dm_constr_mindec.array[:,:,:,:,:,idx[mineral_in_unadj]]
    arr_temp = arr_temp[...,np.newaxis] * dm_temp.array[:,:,np.newaxis,np.newaxis,np.newaxis,:]
    dm_constr_mindec.add(arr_temp, dim = "Categories3", col_label = mineral_switched)

    # do mineral unadjusted - mineral switched
    dm_constr_mindec.operation(col1 = mineral_in_unadj, operator = "-", col2 = mineral_switched, dim = "Categories3",
                            out_col = mineral_in)

    # for indir and exp, substitute back the unadjusted one (adjustment is only done on exp and dir)
    dm_constr_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in]] = dm_constr_mindec.array[:,:,:,:,idx["indir"],idx[mineral_in_unadj]]
    dm_constr_mindec.array[:,:,:,:,idx["exp"],idx[mineral_in]] = dm_constr_mindec.array[:,:,:,:,idx["exp"],idx[mineral_in_unadj]]

    # drop
    dm_constr_mindec.drop(dim = "Categories3", col_label = [mineral_in_unadj, mineral_switched])

    # clean
    del dm_temp, cdm_temp, mineral_in, mineral_out, mineral_switched, mineral_in_unadj, idx, arr_temp, variables, variable,\
        variables_missing


    ##################
    ##### ENERGY #####
    ##################
    
    # names for energy
    energy = ['energy-coal', 'energy-csp', 'energy-gas', 'energy-geo', 'energy-hydro', 
              'energy-marine', 'energy-nuclear', 'energy-off-wind', 'energy-oil', 
              'energy-on-wind','energy-pv']

    # get product demand split unit
    dm_temp = DM_demand_split["energy"].copy()

    # get constants for mineral decomposition
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*energy*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!trade|battery).)*$"})
    cdm_temp.deepen_twice()

    # get constants for thin film
    cdm_temp2 = cdm_constants.filter_w_regex({"Variables":".*min_share_pv_*"})
    cdm_temp2.rename_col_regex(str1 = "pv_", str2 = "pv-", dim = "Variables")

    # get indir, exp and dir for energy-pv-csi (by multipilication with the thin film and csi factors)
    idx = dm_temp.idx
    idx2 = cdm_temp2.idx

    arr_temp = dm_temp.array[:,:,:,idx["energy-pv"],:] * cdm_temp2.array[idx2["min_share_pv-csi"]]
    dm_temp.add(arr_temp, dim = "Categories1", col_label = "energy-pv-csi")

    arr_temp = dm_temp.array[:,:,:,idx["energy-pv"],:] * cdm_temp2.array[idx2["min_share_pv-thinfilm"]]
    dm_temp.add(arr_temp, dim = "Categories1", col_label = "energy-pv-thinfilm")

    dm_temp.drop(dim = "Categories1", col_label = ["energy-pv"])
    energy = energy[0:-1]
    energy = energy + ['energy-pv-csi','energy-pv-thinfilm']

    # get mineral decomposition
    dm_energy_tech_mindec = get_mindec(dm_temp, cdm_temp)

    # get batteries for energy
    dm_energy_batt_mindec = dm_battery_mindec.filter({"Categories1" : ['energy-battery']})

    # add missing minerals to the dms
    DM_temp = {"energy": dm_energy_tech_mindec, 
               "batt": dm_energy_batt_mindec}

    for key in DM_temp.keys():
        
        variables = DM_temp[key].col_labels["Categories3"]
        variables_missing = np.array(minerals)[[i not in variables for i in minerals]].tolist()
        
        for variable in variables_missing:
            DM_temp[key].add(np.nan, dim = "Categories3", col_label = variable, dummy = True)
        
    # append
    dm_energy_tech_mindec.append(dm_energy_batt_mindec, dim = "Categories1")
    dm_energy_mindec = dm_energy_tech_mindec.copy()

    # get sum across energy
    arr_temp = np.nansum(dm_energy_mindec.array, axis=-3, keepdims = True)
    dm_energy_mindec.add(arr_temp, dim = "Categories1", col_label = "energy")
    energy = energy + ["energy-battery"]
    dm_energy_mindec.drop(dim = "Categories1", col_label = energy)
    # not that here for example Austria 2020 for dir_energy_aluminium differs slightly from KNIME, supposedly for rounding differences (numbers are generally fine)

    # get electricity demand total (GWh) and constant for amount of copper in wires (kg/GWh)
    dm_temp = dm_str.filter({"Variables":["elc_electricity-demand_total"]})
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*wire_copper*"})

    # multiply direct demand times amount of copper in wires to get amount of copper in wires (kg)
    arr_temp = dm_temp.array * cdm_temp.array
    dm_temp = dm_energy_mindec.filter({"Categories2" : ["dir"]})
    dm_temp = dm_temp.filter({"Categories3" : ["copper"]})
    dm_temp.add(arr_temp[...,np.newaxis,np.newaxis,np.newaxis], col_label = "copper-wire", dim = "Categories3")

    # add amount of coppers in wires to copper from energy
    idx = dm_temp.idx
    dm_temp.array[...,idx["copper"]] = np.nansum(dm_temp.array, axis = -1)
    dm_temp.drop(dim = "Categories3", col_label = ["copper-wire"])

    idx1 = dm_energy_mindec.idx
    idx2 = dm_temp.idx
    dm_energy_mindec.array[:,:,:,:,idx1["dir"],idx1["copper"]] = dm_temp.array[:,:,:,:,idx2["dir"],idx2["copper"]]

    # clean
    del dm_energy_tech_mindec, dm_energy_batt_mindec, dm_temp, cdm_temp, arr_temp, cdm_temp2, idx, idx2, \
        DM_temp, key, variable, variables, variables_missing, idx1


    ########################
    ##### ALL MINERALS #####
    ########################


    # add minerals as nans for those dms which do not have all minerals

    DM_mindec = {"transport": dm_veh_mindec, 
                 "infra": dm_infra_mindec,
                 "dom-appliance": dm_domapp_mindec,
                 "electronics": dm_electr_mindec, 
                 "construction": dm_constr_mindec, 
                 "energy" : dm_energy_mindec}

    for key in DM_mindec.keys():
        
        variables = DM_mindec[key].col_labels["Categories3"]
        variables_missing = np.array(minerals)[[i not in variables for i in minerals]].tolist()
        
        for variable in variables_missing:
            DM_mindec[key].add(np.nan, dim = "Categories3", col_label = variable, dummy = True)
            

    # sum minerals across all sectors
    dm_mindec = dm_veh_mindec.copy()
    mylist = ['infra', 'dom-appliance', 'electronics', 'construction', 'energy']
    for key in mylist:
        dm_mindec.append(DM_mindec[key], dim = "Categories1")
    arr_temp = np.nansum(dm_mindec.array, axis=-3, keepdims = True)
    drop = list(DM_mindec)
    dm_mindec.add(arr_temp, dim = "Categories1", col_label = "all-sectors")
    dm_mindec.drop(dim = "Categories1", col_label = drop)

    # clean
    del key, arr_temp, variables, variable, variables_missing, mylist

    #######################################
    ##### OTHER (UNACCOUNTED) SECTORS #####
    #######################################

    minerals_sub1 = ["aluminium","copper","lead","steel"]

    # create dm for other minerals
    dm_other_mindec = dm_mindec.filter({"Categories3" : minerals_sub1})
    dm_other_mindec = dm_other_mindec.filter({"Categories2" : ["dir"]})

    # get constants
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*other*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!vehicle|appliance).)*$"})
    cdm_temp.deepen_twice()
    cdm_temp = cdm_temp.filter({"Categories2" : minerals_sub1})

    # expand constants
    dm_temp = cdm_to_dm(cdm_temp, countries_list = dm_other_mindec.col_labels["Country"], 
                        years_list = dm_other_mindec.col_labels["Years"])

    # multiply total times factors and add them to dm_other_mindec
    arr_temp = dm_other_mindec.array * dm_temp.array[...,np.newaxis,:]
    dm_other_mindec.add(arr_temp, dim = "Categories1", col_label = "other")
    dm_other_mindec.drop(dim = "Categories1", col_label = "all-sectors")

    # clean
    del cdm_temp, dm_temp, arr_temp

    ####################
    ##### INDUSTRY #####
    ####################

    # Note: this is done only for direct demand, so industries in foreign countries are not considered

    minerals_sub2 = ["graphite","lithium","manganese","nickel"]

    # add other aluminium and steel temporarely to total (this is just for computing industry, you'll redo the addition of everything at the end)
    dm_mindec_temp = dm_mindec.filter({"Categories3" : ["aluminium","steel"], "Categories2" : ["dir"]})
    dm_other_mindec_temp = dm_other_mindec.filter({"Categories3" : ["aluminium","steel"], "Categories2" : ["dir"]})
    dm_mindec_temp.append(dm_other_mindec_temp, "Categories1")
    arr_temp = np.nansum(dm_mindec_temp.array, axis = -3, keepdims=True)
    dm_mindec_temp.drop(dim = "Categories1", col_label = "all-sectors")
    dm_mindec_temp.add(arr_temp, dim = "Categories1", col_label = "all-sectors")
    dm_mindec_temp.drop(dim = "Categories1", col_label = "other")

    # create dm for industry: take direct demand for steel and aluminium and convert from kg to mt
    dm_industry_mindec = dm_mindec_temp.copy()
    dm_industry_mindec.array = dm_industry_mindec.array * 0.000000001
    dm_industry_mindec.units['mineral-decomposition'] = "Mt"

    # take glass
    dm_temp2 = dm_ind.filter({"Variables" : ["ind_material-production_glass"]})
    dm_industry_mindec.add(dm_temp2.array[:,:,np.newaxis,np.newaxis,np.newaxis,:], dim = "Categories3", col_label = "glass")

    # get constants for switches
    conversions_old = ["min_industry_aluminium_lithium", "min_industry_steel_nickel", "min_industry_steel_manganese",
                       "min_industry_steel_graphite","min_industry_glass_lithium", "min_industry_aluminium_manganese"]
    cdm_temp = cdm_constants.filter({"Variables":conversions_old})
    conversions = ["min_aluminium-lithium", "min_steel-nickel", "min_steel-manganese",
                   "min_steel-graphite","min_glass-lithium", "min_aluminium-manganese"]
    for i in range(len(conversions)):
        cdm_temp.rename_col(col_in = conversions_old[i], col_out = conversions[i], dim = "Variables")
    cdm_temp.deepen()

    # multiply direct demand by these switch factors
    idx_dm = dm_industry_mindec.idx
    idx_cdm = cdm_temp.idx
    col1 = ["aluminium","aluminium","steel","steel","steel","glass"]
    col2 = ["aluminium-lithium", "aluminium-manganese", "steel-nickel", "steel-manganese","steel-graphite", "glass-lithium"]
    for i in range(len(col1)):
        arr_temp = dm_industry_mindec.array[...,idx_dm[col1[i]]] * cdm_temp.array[...,idx_cdm[col2[i]]]
        dm_industry_mindec.add(arr_temp, dim = "Categories3", col_label = col2[i])

    # drop starting point minerals
    dm_industry_mindec.drop(dim = "Categories3", col_label = ["aluminium","glass","steel"])

    # transform in kg
    dm_industry_mindec.array = dm_industry_mindec.array * 1000000000
    dm_industry_mindec.units['mineral-decomposition'] = "kg"

    # sum over end point minerals
    dm_temp = dm_industry_mindec.filter({"Categories3" : ["aluminium-lithium", "glass-lithium"]})
    arr_temp = np.nansum(dm_temp.array, axis = -1, keepdims=True)
    dm_industry_mindec.add(arr_temp, dim = "Categories3", col_label = "lithium")
    dm_industry_mindec.drop(dim = "Categories3", col_label = ["aluminium-lithium","glass-lithium"])

    dm_temp2 = dm_industry_mindec.filter({"Categories3" : ["aluminium-manganese", "steel-manganese"]})
    arr_temp = np.nansum(dm_temp2.array, axis = -1, keepdims=True)
    dm_industry_mindec.add(arr_temp, dim = "Categories3", col_label = "manganese")
    dm_industry_mindec.drop(dim = "Categories3", col_label = ["aluminium-manganese","steel-manganese"])

    dm_industry_mindec.rename_col(col_in = 'steel-nickel', col_out = "nickel", dim = "Categories3")
    dm_industry_mindec.rename_col(col_in = 'steel-graphite', col_out = "graphite", dim = "Categories3")

    # adjust graphite for how much graphite is used in electric arc furnace to make steel
    dm_temp = DM_fxa["min_proportion"].filter({"Variables":["min_proportion_eu_steel_EAF"]})
    idx = dm_industry_mindec.idx
    dm_industry_mindec.array[...,idx["graphite"]] = dm_industry_mindec.array[...,idx["graphite"]] * dm_temp.array[:,:,np.newaxis,np.newaxis,:]

    # sort and rename
    dm_industry_mindec.sort("Categories3")
    dm_industry_mindec.rename_col(col_in = "all-sectors", col_out = "industry", dim = "Categories1")

    # add industry graphite, lithium, manganese and nickel temporarely to total to compute other graphite, lithium, manganese and nickel
    dm_mindec_temp = dm_mindec.filter({"Categories3":minerals_sub2})
    dm_mindec_temp = dm_mindec_temp.filter({"Categories2":["dir"]})
    dm_mindec_temp.add(dm_industry_mindec.array, col_label = "industry", dim = "Categories1")
    arr_temp = np.nansum(dm_mindec_temp.array, axis = -3, keepdims=True)
    dm_mindec_temp.drop(dim = "Categories1", col_label = "all-sectors")
    dm_mindec_temp.add(arr_temp, dim = "Categories1", col_label = "all-sectors")
    dm_mindec_temp.drop(dim = "Categories1", col_label = "industry")

    # multiply these total with factors for other unaccounted sectos 

    # get constants
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*other*"})
    cdm_temp = cdm_temp.filter_w_regex({"Variables":"^((?!vehicle|appliance).)*$"})
    cdm_temp.deepen_twice()
    cdm_temp = cdm_temp.filter({"Categories2" : minerals_sub2})
    dm_temp = cdm_to_dm(cdm_temp, countries_list = dm_other_mindec.col_labels["Country"], 
                        years_list = dm_other_mindec.col_labels["Years"])

    # multiply total from dm_mindec_temp times factors and add them to dm_mindec_temp
    arr_temp = dm_mindec_temp.array * dm_temp.array[...,np.newaxis,:]
    dm_mindec_temp.add(arr_temp, dim = "Categories1", col_label = "other")

    # add other to dm_other_mindec
    dm_temp = dm_mindec_temp.filter({"Categories1":["other"]})
    dm_other_mindec.append(dm_temp, dim = "Categories3")
    dm_other_mindec.sort("Categories3")

    # add exp and indir to other
    dm_other_mindec.add(np.nan, dim = "Categories2", col_label = "exp", dummy = True)
    dm_other_mindec.add(np.nan, dim = "Categories2", col_label = "indir", dummy = True)

    # add exp and indir, and other materials, to industry
    dm_industry_mindec.add(np.nan, dim = "Categories2", col_label = "exp", dummy = True)
    dm_industry_mindec.add(np.nan, dim = "Categories2", col_label = "indir", dummy = True)
    for i in minerals_sub1:
        dm_industry_mindec.add(np.nan, dim = "Categories3", col_label = i, dummy = True)
    dm_industry_mindec.sort(dim = "Categories3")

    # sum industry and other to total
    dm_mindec.append(dm_other_mindec, dim = "Categories1")
    dm_mindec.append(dm_industry_mindec, dim = "Categories1")
    arr_temp = np.nansum(dm_mindec.array, axis = -3, keepdims=True)
    dm_mindec.drop(dim = "Categories1", col_label = "all-sectors")
    dm_mindec.add(arr_temp, dim = "Categories1", col_label = "all-sectors")
    dm_mindec.drop(dim = "Categories1", col_label = "industry")
    dm_mindec.drop(dim = "Categories1", col_label = "other")

    # clean
    del cdm_temp, dm_temp, arr_temp, col1, col2, conversions, conversions_old, dm_temp2, drop, i, idx,\
        idx_cdm, idx_dm, minerals_sub1, minerals_sub2, dm_mindec_temp
    
    ########################
    ##### PUT TOGETHER #####
    ########################
        
    # put dms together
    DM_mindec = {"transport": dm_veh_mindec, 
                  "infrastructure": dm_infra_mindec,
                  "domestic-appliance": dm_domapp_mindec,
                  "electronics": dm_electr_mindec, 
                  "construction": dm_constr_mindec, 
                  "energy" : dm_energy_mindec,
                  "industry" : dm_industry_mindec,
                  "other" : dm_other_mindec}

    # put sectors in one dm
    dm_mindec_sect = DM_mindec["transport"].copy()
    mykey = list(DM_mindec)[1:]
    for i in mykey:
        dm_mindec_sect.append(DM_mindec[i], dim = "Categories1")

    #################################
    ##### SECTORIAL PERCENTAGES #####
    #################################

    # make percentages
    # note: I have to to this here as these percenteges are done on dm_mindec before computing effifiency (not clear why)
    dm_mindec_sect.array = dm_mindec_sect.array / dm_mindec.array
    dm_mindec_sect.units['mineral-decomposition'] = "%"

    # make nan for indir (as at the moment percentages are not done for indir)
    idx = dm_mindec_sect.idx
    dm_mindec_sect.array[:,:,idx["mineral-decomposition"],:,idx["indir"],:] = np.nan

    # clean
    del idx, mykey

    ################################################
    ##### EFFICIENCY FOR MINERAL DIRECT DEMAND #####
    ################################################

    # get material-efficiency from constant and industry
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*eff*"})
    dm_temp = dm_ind.filter_w_regex({"Variables":".*eff*"})

    # expand constants and add
    dm_temp2 = cdm_to_dm(cdm_temp, countries_list = dm_temp.col_labels["Country"], years_list = dm_temp.col_labels["Years"])
    dm_temp.append(dm_temp2, dim = "Variables")
    dm_temp.deepen()

    # do 1 - ind efficiency and substitute back in
    dm_temp.array = 1 - dm_temp.array

    # mutltiply total times ind efficiency and substitute back in
    dm_temp2 = dm_mindec.filter({"Categories2" : ["dir"]})
    idx = dm_mindec.idx
    idx2 = dm_temp2.idx
    dm_mindec.array[:,:,:,:,idx["dir"],:] = dm_temp2.array[...,idx2["dir"],:] * dm_temp.array[:,:,np.newaxis,:]

    # clean
    del cdm_temp, dm_temp, dm_temp2, idx, idx2
    
    # return
    return dm_mindec, dm_mindec_sect

def mineral_demand_calibration(DM_minerals, dm_mindec):
    
    # get calibration series for direct demand
    dm_cal = DM_minerals["calibration"]
    dm_cal.deepen_twice()
    dm_cal.rename_col("min", "mineral-decomposition-calib", "Variables")
    dm_cal.rename_col("calib", "all-sectors", "Categories1")

    # get only direct demand
    dm_temp = dm_mindec.filter({"Categories2" : ["dir"]})
    dm_temp = dm_temp.flatten()
    dm_temp.rename_col_regex(str1 = "dir_", str2 = "", dim = "Categories2")

    # obtain calibration rates
    dm_mindec_dir_calib_rates = calibration_rates(dm = dm_temp, dm_cal = dm_cal)

    # use the same calibration rates on indirect demand, net exports and direct demand
    dm_mindec.array = dm_mindec.array * dm_mindec_dir_calib_rates.array[:,:,:,:,np.newaxis,:]
    
    # clean
    del dm_cal, dm_temp
    
    # return
    return dm_mindec, dm_mindec_dir_calib_rates
    
def mineral_extraction(DM_minerals, DM_interface, dm_mindec, cdm_constants):
    
    # name of minerals
    minerals = ['aluminium','copper','graphite','lead','lithium','manganese','nickel','steel']
    
    # get data
    DM_fxa = DM_minerals['fxa']
    dm_ind = DM_interface["industry"]
    
    ###################################
    ##### MINERAL PRODUCTION (KG) #####
    ###################################

    # !FIXME: in the knime this is dir - exp.

    # mineral production at home
    dm_production = dm_mindec.copy()
    idx = dm_production.idx
    dm_production.array[...,idx["exp"]] = np.nan_to_num(dm_production.array[...,idx["exp"]])
    dm_production.operation('dir', "-", 'exp', dim = "Categories2", out_col="mineral-production-home", div0="error")

    # mineral production abroad
    idx = dm_mindec.idx
    arr_temp = dm_production.array[...,idx["indir"],:]
    dm_production.add(arr_temp[...,np.newaxis,:,:], dim = "Categories2", col_label = "mineral-production-abroad")
    # note: in theory mineral demand = mineral produced at home + mineral produced abroad

    # clean
    dm_production.drop(dim = "Categories2", col_label = ["dir","exp","indir"])
    del idx, arr_temp


    ################################################
    ##### SCRAP USE IN MINERAL PRODUCTION (KG) #####
    ################################################

    # get variables
    dm_proportion = DM_fxa["min_proportion"].copy()
    dm_temp = dm_ind.filter_w_regex({"Variables":".*technology.*"})
    dm_temp.rename_col_regex(str1 = "technology-development", str2 = "proportion", dim = "Variables")
    dm_temp.rename_col_regex(str1 = "copper_tech", str2 = "copper_secondary", dim = "Variables")
    dm_temp.rename_col_regex(str1 = "_prim", str2 = "_primary", dim = "Variables")
    dm_temp.rename_col_regex(str1 = "aluminium_sec", str2 = "aluminium_secondary", dim = "Variables")

    # adjust steel eaf for scraps
    idx1 = dm_proportion.idx
    idx2 = dm_temp.idx

    dm_proportion.array[:,:,idx1["min_proportion_eu_steel_EAF"]] = dm_proportion.array[:,:,idx1["min_proportion_eu_steel_EAF"]] + \
                                                             dm_temp.array[:,:,idx2['ind_proportion_steel_scrap-EAF']] - \
                                                             dm_temp.array[:,:,idx2['ind_proportion_steel_hydrog-DRI']] - \
                                                             (dm_temp.array[:,:,idx2['ind_proportion_steel_hisarna']]/2) - \
                                                             dm_temp.array[:,:,idx2['ind_proportion_steel_BF-BOF']]

    # adjust steel bof for scraps
    dm_proportion.array[:,:,idx1["min_proportion_eu_steel_BOF"]] = dm_proportion.array[:,:,idx1["min_proportion_eu_steel_BOF"]] + \
                                                             dm_temp.array[:,:,idx2['ind_proportion_steel_BF-BOF']] - \
                                                             (dm_temp.array[:,:,idx2['ind_proportion_steel_hisarna']]/2) - \
                                                             dm_temp.array[:,:,idx2['ind_proportion_steel_scrap-EAF']]

    # make proportion of primary copper in industry
    dm_temp.add(dm_temp.array[:,:,idx2["ind_proportion_copper_secondary"]], 
                 dim = "Variables", col_label = "ind_proportion_copper_primary")

    # adjust proportions of aluminium and copper
    dm_proportion.array[:,:,idx1["min_proportion_eu_aluminium_primary"]] = \
        dm_proportion.array[:,:,idx1["min_proportion_eu_aluminium_primary"]] -  dm_temp.array[:,:,idx2['ind_proportion_aluminium_primary']]
    dm_proportion.array[:,:,idx1["min_proportion_eu_copper_primary"]] = \
        dm_proportion.array[:,:,idx1["min_proportion_eu_copper_primary"]] -  dm_temp.array[:,:,idx2['ind_proportion_copper_primary']]
    dm_proportion.array[:,:,idx1["min_proportion_eu_aluminium_secondary"]] = \
        dm_proportion.array[:,:,idx1["min_proportion_eu_aluminium_secondary"]] -  dm_temp.array[:,:,idx2['ind_proportion_aluminium_secondary']]
    dm_proportion.array[:,:,idx1["min_proportion_eu_copper_secondary"]] = \
        dm_proportion.array[:,:,idx1["min_proportion_eu_copper_secondary"]] -  dm_temp.array[:,:,idx2['ind_proportion_copper_secondary']]
        
    # get proportions for hisarna and dri from temp into dm_proportion
    dm_proportion.add(dm_temp.array[:,:,idx2["ind_proportion_steel_hisarna"]], dim = "Variables", col_label = "min_proportion_eu_steel_hisarna")
    dm_proportion.add(dm_temp.array[:,:,idx2["ind_proportion_steel_hydrog-DRI"]], dim = "Variables", col_label = "min_proportion_eu_steel_DRI")

    # fix dimensions of dm_production
    dm_production = dm_production.flatten()
    dm_production = dm_production.flatten()
    dm_production = dm_production.flatten()
    dm_production.rename_col_regex(str1 = "mineral-decomposition_all-sectors_mineral-production-", str2 = "", dim = "Variables")
    dm_production.deepen()

    # fix dimensions of dm_proportion
    dm_proportion.deepen_twice()
    dm_proportion.rename_col(col_in = "min_proportion_eu", col_out = "home", dim = "Variables")
    dm_proportion.rename_col(col_in = "min_proportion_row", col_out = "abroad", dim = "Variables")
    dm_proportion.sort("Variables")
    dm_proportion.drop(dim = "Categories1", col_label = ['cobalt'])

    # clean
    del idx1, idx2

    ###################################
    ##### MINERAL EXTRACTION (KG) #####
    ###################################

    # multiply production with proportion
    dm_primsec = dm_proportion.copy()
    dm_primsec.array = dm_production.array[...,np.newaxis] * dm_proportion.array
    dm_primsec.units["home"] = "kg"
    dm_primsec.units["abroad"] = "kg"

    # get factor to keep only primary
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*recy*"})
    cdm_temp.sort("Variables")

    # apply factor to keep only primary
    dm_extraction = dm_primsec.copy()
    dm_extraction.array = dm_extraction.array * cdm_temp.array[np.newaxis,np.newaxis,np.newaxis,np.newaxis,:]

    # sum over prim and sec, and home and abroad
    dm_extraction.add(np.nansum(dm_extraction.array, axis = -1, keepdims=True), dim = "Categories2", col_label = "total-sub")
    drops = ['BOF', 'DRI', 'EAF', 'hisarna', 'primary', 'secondary']
    dm_extraction.drop(dim = "Categories2", col_label = drops)
    dm_extraction.add(np.nansum(dm_extraction.array, axis = -3, keepdims=True), dim = "Variables", col_label = "total")
    drops = ['abroad', 'home']
    dm_extraction.drop(dim = "Variables", col_label = drops)

    # reshape
    dm_extraction = dm_extraction.flatten()
    dm_extraction = dm_extraction.flatten()
    dm_extraction.rename_col_regex(str1 = "total_", str2 = "", dim = "Variables")
    dm_extraction.rename_col_regex(str1 = "_total-sub", str2 = "", dim = "Variables")
    for i in minerals:
        dm_extraction.units[i] = "kg"

    # multiply by extraction parameters
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*param*"})
    dm_extraction.array = dm_extraction.array * cdm_temp.array[np.newaxis,np.newaxis,:]

    # rename aluminium to bauxite and steel to iron
    dm_extraction.rename_col("aluminium", "bauxite", "Variables")
    dm_extraction.rename_col("steel", "iron", "Variables")
    dm_extraction.sort("Variables")
    minerals = ['bauxite', 'copper', 'graphite', "iron", 'lead', 'lithium', 'manganese', 'nickel', 'phosphate', 'potash']

    # convert to mt
    dm_extraction.array = dm_extraction.array * 0.000000001
    for i in minerals:
        dm_extraction.units[i] = "Mt"

    # clean
    del cdm_temp, dm_proportion, dm_temp, drops, i
    
    # return
    return dm_extraction
    
def mineral_reserves(DM_minerals, DM_interface, dm_mindec, dm_mindec_sect, dm_extraction, cdm_constants):
    
    # name of minerals
    minerals = ['bauxite', 'copper', 'graphite', "iron", 'lead', 'lithium', 'manganese', 'nickel', 'phosphate', 'potash']
    
    # get data
    DM_fxa = DM_minerals['fxa']
    
    ###############################################################
    #################### MINERAL RESERVES (Mt) ####################
    ###############################################################

    # get reserves
    cdm_reserves = cdm_constants.filter_w_regex({"Variables" : ".*reserve.*"})
    dm_reserves = cdm_to_dm(cdm_reserves, countries_list = dm_extraction.col_labels["Country"], 
                            years_list = dm_extraction.col_labels["Years"])

    # scale reserves by population share to make it country level
    dm_lfs = DM_interface["lifestyles"].copy()
    idx_lfs = dm_lfs.idx
    arr_temp = dm_lfs.array[...,idx_lfs['lfs_pop_population']] / dm_lfs.array[...,idx_lfs['lfs_macro-scenarii_iiasa-ssp2']]
    dm_reserves.array = dm_reserves.array * arr_temp[...,np.newaxis]

    # clean
    del idx_lfs, arr_temp, dm_lfs, cdm_reserves


    ########################
    ##### FOSSIL FUELS #####
    ########################

    # demand for oil, gas and coal
    dm_fossil = DM_interface["oil-refinery"].copy()
    dm_fossil.rename_col_regex(str1 = "fos_primary-demand_", str2 = "min_energy_", dim = "Variables")
    idx = dm_fossil.idx
    dm_fossil.array[...,idx["min_energy_coal"]] = dm_fossil.array[...,idx["min_energy_coal"]] * 0.123
    dm_fossil.array[...,idx["min_energy_gas"]] = dm_fossil.array[...,idx["min_energy_gas"]] * 0.076
    dm_fossil.array[...,idx["min_energy_oil"]] = dm_fossil.array[...,idx["min_energy_oil"]] * 0.086
    fossils = ["coal","gas","oil"]
    variables = ["min_energy_" + i for i in fossils]
    for i in variables:
        dm_fossil.units[i] = "Mt"
        
    # adjust min_energy_gas for ccus_gas
    dm_gas = dm_fossil.filter({"Variables":["min_energy_gas"]})
    dm_ccus = DM_interface["ccus"].copy()
    dm_ccus.array[dm_gas.array < 0] = dm_ccus.array[dm_gas.array < 0] + dm_gas.array[dm_gas.array < 0] # in the ambitious pathway, the supply of ccus (which include biogas) is more than the demand for gaz leading to gas demand being negative. The following operation serves to correct this difference by substracting the negative gas demand by the over supply of ccus.
    idx = dm_fossil.idx
    dm_fossil.array[:,:,idx["min_energy_gas"], np.newaxis] = dm_fossil.array[:,:,idx["min_energy_gas"], np.newaxis] + dm_ccus.array

    # relative reserves for fossil fuels 
    variables = ["min_reserve_" + i for i in fossils]
    dm_relres_fossil = dm_reserves.filter({"Variables":variables})
    dm_relres_fossil.append(dm_fossil, dim = "Variables")

    # get yearly (sum across countries)
    dm_relres_fossil.add(np.nansum(dm_relres_fossil.array, axis = -3, keepdims=True), dim = "Country", col_label = "total")
    drops = dm_fossil.col_labels["Country"]
    dm_relres_fossil.drop(dim = "Country", col_label = drops)

    # make relative reserves
    dict_relres_fossil = relative_reserve(minerals = ["coal","gas","oil"], dm = dm_relres_fossil.copy(), 
                                          reserve_starting_year = 2015, mineral_type = "fossil_fuel",
                                          range_max = 200)

    # clean
    del idx, fossils, variables, drops

    ####################
    ##### MINERALS #####
    ####################

    # add phosphate and potash extraction
    dm_min_other = DM_fxa["min_other"].copy()
    dm_agr = DM_interface["agriculture"].copy()

    dm_temp = dm_agr.filter_w_regex({"Variables" : ".*phosphate.*"})
    dm_temp.append(dm_min_other.filter_w_regex({"Variables" : ".*phosphate.*"}), dim = "Variables")
    dm_temp.add(np.nansum(dm_temp.array, axis=-1, keepdims=True), dim = "Variables", col_label = "phosphate", unit = "Mt")
    dm_extraction.append(dm_temp.filter({"Variables" : ["phosphate"]}), dim = "Variables")

    dm_temp = dm_agr.filter_w_regex({"Variables" : ".*potash.*"})
    dm_temp.append(dm_min_other.filter_w_regex({"Variables" : ".*potash.*"}), dim = "Variables")
    dm_temp.add(np.nansum(dm_temp.array, axis=-1, keepdims=True), dim = "Variables", col_label = "potash", unit = "Mt")
    dm_extraction.append(dm_temp.filter({"Variables" : ["potash"]}), dim = "Variables")

    # relative reserves for minerals
    variables = ["min_reserve_" + i for i in minerals]
    dm_relres_mineral = dm_reserves.filter({"Variables":variables})
    dm_temp = dm_extraction.copy()
    for i in minerals:
        dm_temp.rename_col(col_in = i, col_out = "min_extraction_" + i, dim="Variables")
    dm_relres_mineral.append(dm_temp, dim = "Variables")

    # get yearly (sum across countries)
    dm_relres_mineral.add(np.nansum(dm_relres_mineral.array, axis = -3, keepdims=True), dim = "Country", col_label = "total")
    drops = dm_extraction.col_labels["Country"]
    dm_relres_mineral.drop(dim = "Country", col_label = drops)

    # make relative reserves
    dict_relres_minerals = relative_reserve(minerals = ["bauxite","copper","graphite", "iron","lead","lithium","manganese","nickel","phosphate","potash"], 
                                            dm = dm_relres_mineral.copy(), reserve_starting_year = 2015, 
                                            mineral_type = "mineral", range_max = 300)

    # clean
    del dm_temp, variables, drops
    
    # return
    return dict_relres_fossil, dict_relres_minerals, dm_fossil

def mineral_production_bysector(dm_mindec, dm_mindec_sect, cdm_constants):
    
    # apply extraction parameter to total indir, exp and dir
    # note: not clear why this is applied now directly here, as before we applied after all the modifications in industry, etc ...
    cdm_temp = cdm_constants.filter_w_regex({"Variables":".*param*"})
    dm_mindec.array = dm_mindec.array * cdm_temp.array
    # note: here we apply the parameter to dm_mindec directly as for tpe we need the indir after multiplication

    # multiply exp and dir by sectoral percentages to get sectoral exp and dir (indir will be nan)
    dm_mindec_sect.array = dm_mindec.array * dm_mindec_sect.array
    dm_mindec_sect.units['mineral-decomposition'] = "kg"

    # !FIXME: in the knime this is dir - exp.

    # mineral production by sector
    dm_production_sect = dm_mindec_sect.copy()
    idx = dm_production_sect.idx

    dm_production_sect.array[:,:,:,:,idx["exp"],:] = np.nan_to_num(dm_production_sect.array[:,:,:,:,idx["exp"],:])
    dm_production_sect.operation('dir', "-", 'exp', dim = "Categories2", out_col="mineral-production", div0="error")
    dm_production_sect.drop(dim = "Categories2", col_label = ['dir', 'exp', 'indir'])
    dm_production_sect.rename_col(col_in = "aluminium", col_out = "bauxite", dim = "Categories3")
    dm_production_sect.rename_col(col_in = "steel", col_out = "iron", dim = "Categories3")
    dm_production_sect.sort("Categories3")

    # clean
    del idx, cdm_temp
    
    # return
    return dm_production_sect

def variables_for_tpe(DM_interface, DM_minerals, dm_production_sect, dm_fossil, dm_mindec, dm_extraction, 
                      dict_relres_fossil, dict_relres_minerals):
    
    # get data
    DM_fxa = DM_minerals['fxa']
    dm_min_other = DM_fxa["min_other"]
    dm_agr = DM_interface["agriculture"]
    dm_ccus = DM_interface["ccus"]
    dm_ind = DM_interface["industry"]
    
    ###########################
    ##### EXTRA MATERIALS #####
    ###########################

    # bioenergy wood
    dm_temp = dm_agr.filter({"Variables":['agr_bioenergy_biomass-demand_liquid_btl_fuelwood-and-res', 
                                          'agr_bioenergy_biomass-demand_solid_fuelwood-and-res']})
    dm_temp.add(np.nansum(dm_temp.array, axis=-1, keepdims=True), dim = "Variables", col_label="bioenergy_wood", unit = "Mt")
    dm_extramaterials = dm_temp.filter({"Variables":['bioenergy_wood']})

    # from industry
    dm_temp = dm_ind.filter({"Variables":["ind_material-production_glass", 'ind_timber', 
                                           'ind_material-production_cement', 'ind_material-production_paper_woodpulp']})
    idx = dm_temp.idx

    # glass sand
    dm_temp.array[...,idx["ind_material-production_glass"]] = dm_temp.array[...,idx["ind_material-production_glass"]] * 1.9/2.4
    dm_temp.rename_col(col_in = "ind_material-production_glass", col_out = "glass_sand", dim = "Variables")

    # timber
    dm_temp.array[...,idx["ind_timber"]] = dm_temp.array[...,idx["ind_timber"]] * 0.001
    dm_temp.units["ind_timber"] = "Mt"
    dm_temp.rename_col(col_in = "ind_timber", col_out = "construction_wood", dim = "Variables")

    # cement sand
    dm_temp.array[...,idx["ind_material-production_cement"]] = dm_temp.array[...,idx["ind_material-production_cement"]] * 90/50
    dm_temp.rename_col(col_in = "ind_material-production_cement", col_out = "cement_sand", dim = "Variables")

    # paper wood
    dm_temp.array[...,idx["ind_material-production_paper_woodpulp"]] = dm_temp.array[...,idx["ind_material-production_paper_woodpulp"]] * 2.5
    dm_temp.rename_col(col_in = "ind_material-production_paper_woodpulp", col_out = "paper_wood", dim = "Variables")

    dm_extramaterials.append(dm_temp, dim = "Variables")

    # gas ccus
    dm_temp = dm_ccus.copy()
    dm_temp.rename_col(col_in = "ccu_ccus_gas-ff-natural", col_out = "ccus_gas", dim = "Variables")
    dm_extramaterials.append(dm_temp, dim = "Variables")

    # rename
    for i in dm_extramaterials.col_labels["Variables"]:
        dm_extramaterials.rename_col(col_in = i, col_out = "min_" + i, dim = "Variables")

    # clean
    del dm_temp, idx, i

    ##################################
    ##### PUT VARIABLES TOGETHER #####
    ##################################

    # extra materials
    dm_tpe = dm_extramaterials.copy()

    # mineral production by mineral and sector

    # potash and phosphate from other and agriculture
    dm_temp = dm_agr.filter({"Variables" : ['agr_demand_phosphate', 'agr_demand_potash']})
    dm_temp.rename_col_regex(str1 = "agr_demand", str2 = "min_agr", dim = "Variables")
    dm_tpe.append(dm_temp, dim = "Variables")
    dm_temp = dm_min_other.filter({"Variables" : ['min_other_phosphate', 'min_other_potash']})
    dm_tpe.append(dm_temp, dim = "Variables")

    # minerals from all sectors
    dm_temp = dm_production_sect.copy()
    dm_temp.rename_col(col_in = 'mineral-decomposition', col_out = "min", dim = "Variables")
    dm_temp.rename_col(col_in = 'construction', col_out = "building", dim = "Categories1")
    dm_temp = dm_temp.flatten()
    dm_temp = dm_temp.flatten()
    dm_temp = dm_temp.flatten()
    dm_temp.rename_col_regex(str1 = "mineral-production_", str2 = "", dim = "Variables")
    dm_temp.array = dm_temp.array * 0.000000001
    for key in dm_temp.units.keys():
        dm_temp.units[key] = "Mt"
    dm_tpe.append(dm_temp, dim = "Variables")

    # fossil fuels
    dm_tpe.append(dm_fossil, dim = "Variables")

    # indirect demand by mineral
    dm_temp = dm_mindec.filter({"Categories2":["indir"]})
    dm_temp.rename_col(col_in = 'aluminium', col_out = "bauxite", dim = "Categories3")
    dm_temp.rename_col(col_in = 'steel', col_out = "iron", dim = "Categories3")
    dm_temp.sort("Categories3")
    dm_temp.rename_col(col_in = 'mineral-decomposition', col_out = "min", dim = "Variables")
    dm_temp.rename_col(col_in = 'indir', col_out = "indirect", dim = "Categories2")
    dm_temp.array = dm_temp.array * 0.000000001
    dm_temp.units["min"] = "Mt"
    dm_temp = dm_temp.flatten()
    dm_temp = dm_temp.flatten()
    dm_temp = dm_temp.flatten()
    dm_temp.rename_col_regex(str1 = "all-sectors_", str2 = "", dim = "Variables")
    dm_tpe.append(dm_temp, dim = "Variables")

    # extraction
    dm_temp = dm_extraction.copy()
    for i in dm_temp.col_labels["Variables"]:
        dm_temp.rename_col(col_in = i, col_out = "min_extraction_" + i, dim = "Variables")
    dm_tpe.append(dm_temp, dim = "Variables")

    # sort
    dm_tpe.sort("Variables")

    # get as df
    df_tpe = dm_tpe.copy().write_df()

    # get relative reserves
    df_relres_fossil = pd.DataFrame(dict_relres_fossil, index=[0])
    df_relres_minerals = pd.DataFrame(dict_relres_minerals, index=[0])
    df_tpe_relres = pd.merge(df_relres_fossil, df_relres_minerals, how="left", on=["Country","Years"])
    indexes = ["Country","Years"]
    variables = df_tpe_relres.columns.tolist()
    variables = np.array(variables)[[i not in indexes for i in variables]].tolist()
    df_tpe_relres = df_tpe_relres.loc[:,indexes + variables]
    
    # clean
    del dm_temp, key, i, indexes, variables
    
    # return
    return df_tpe, df_tpe_relres

def minerals(years_setting, interface=Interface(), calibration = False):
    
    # directories
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    minerals_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/minerals.pickle')
    # minerals_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/minerals.pickle') # for local run
    
    # get data
    DM_minerals, cdm_constants = read_data(minerals_data_file)
    
    # get countries
    cntr_list = DM_minerals["fxa"]["elec_new"].col_labels['Country']
    
    # get interfaces
    DM_interface = {}
    
    if interface.has_link(from_sector='lifestyles', to_sector='minerals'):
        DM_interface["lifestyles"] = interface.get_link(from_sector='lifestyles', to_sector='minerals')
    else:
        DM_interface["lifestyles"] = simulate_input(from_sector="lifestyles", to_sector="minerals")
        
    if interface.has_link(from_sector='transport', to_sector='minerals'):
        DM_interface["transport"] = interface.get_link(from_sector='transport', to_sector='minerals')
    else:
        DM_interface["transport"] = simulate_input(from_sector="transport", to_sector="minerals")
        
    if interface.has_link(from_sector='agriculture', to_sector='minerals'):
        DM_interface["agriculture"] = interface.get_link(from_sector='agriculture', to_sector='minerals')
    else:
        DM_interface["agriculture"] = simulate_input(from_sector="agriculture", to_sector="minerals")
        
    if interface.has_link(from_sector='industry', to_sector='minerals'):
        DM_interface["industry"] = interface.get_link(from_sector='industry', to_sector='minerals')
    else:
        DM_interface["industry"] = simulate_input(from_sector="industry", to_sector="minerals")
    
    if interface.has_link(from_sector='storage', to_sector='minerals'):
        DM_interface["storage"] = interface.get_link(from_sector='storage', to_sector='minerals')
    else:
        DM_interface["storage"] = simulate_input(from_sector="storage", to_sector="minerals")
        
    if interface.has_link(from_sector='buildings', to_sector='minerals'):
        DM_interface["buildings"] = interface.get_link(from_sector='buildings', to_sector='minerals')
    else:
        DM_interface["buildings"] = simulate_input(from_sector="buildings", to_sector="minerals")
        
    if interface.has_link(from_sector='oil-refinery', to_sector='minerals'):
        DM_interface["oil-refinery"] = interface.get_link(from_sector='oil-refinery', to_sector='minerals')
    else:
        DM_interface["oil-refinery"] = simulate_input(from_sector="oil-refinery", to_sector="minerals")
    
    if interface.has_link(from_sector='ccus', to_sector='minerals'):
        DM_interface["ccus"] = interface.get_link(from_sector='ccus', to_sector='minerals')
    else:
        DM_interface["ccus"] = simulate_input(from_sector="ccus", to_sector="minerals")
    
    # rename interfaces
    DM_interface = rename_interfaces(DM_interface)
    
    # keep only the countries in cntr_list
    for i in DM_interface.keys():
        DM_interface[i] = DM_interface[i].filter({'Country': cntr_list})
        
    # get product demand
    DM_demand = product_demand(DM_minerals, DM_interface, cdm_constants)
    
    # get product import
    dm_import = product_import(DM_interface)
    
    # get product demand split
    DM_demand_split = product_demand_split(DM_demand, dm_import, cdm_constants)
    
    # get mineral demand split
    dm_mindec, dm_mindec_sect = mineral_demand_split(DM_minerals, DM_interface, DM_demand, DM_demand_split, cdm_constants)
    
    # calibration
    if calibration is True:
        dm_mindec, dm_mindec_calib_rates = mineral_demand_calibration(DM_minerals, dm_mindec)

    # get mineral extraction
    dm_extraction = mineral_extraction(DM_minerals, DM_interface, dm_mindec, cdm_constants)
    
    # get mineral reserves
    dict_relres_fossil, dict_relres_minerals, dm_fossil = mineral_reserves(DM_minerals, DM_interface, dm_mindec, 
                                                                           dm_mindec_sect, dm_extraction, cdm_constants)
    
    # get mineral production by sector
    dm_production_sect = mineral_production_bysector(dm_mindec, dm_mindec_sect, cdm_constants)
    
    # get variables for TPE
    df_tpe, df_tpe_relres = variables_for_tpe(DM_interface, DM_minerals, dm_production_sect, dm_fossil, dm_mindec, dm_extraction, 
                                              dict_relres_fossil, dict_relres_minerals)


    # return
    #results_run = {"out1": df_tpe, "out2": "calibration_tbd", "out3" : df_tpe_relres}
    results_run = df_tpe
    return results_run

def local_minerals_run():
    
    # set years
    years_setting = [1990, 2015, 2050, 5]
    
    # geoscale
    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)
    
    # run
    results_run = minerals(years_setting)
    
    # return
    return results_run


# # run local
# __file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/minerals_module.py"
# database_from_csv_to_datamatrix()
# results_run = local_minerals_run()
