
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

def product_production(dm_demand_bld_pipe, dm_demand_bld_floor, dm_demand_bld_domapp, 
                       dm_demand_tra_infra, dm_demand_tra_veh, 
                       dm_demand_lfs, dm_import):
    
    # production [%] = 1 - net import [%]
    # note: production [%] is production [unit] / demand [unit]
    
    dm_prod = dm_import.copy()
    dm_prod.array = 1 - dm_prod.array
    dm_prod.rename_col(col_in="product-net-import", col_out="product-production", dim="Variables")

    #####################
    ##### BUILDINGS #####
    #####################

    # get production for buildings
    dm_prod_bld_pipe = dm_prod.filter({"Categories1" : ['new-dhg-pipe']})
    dm_prod_bld_floor = dm_prod.filter_w_regex({"Categories1": "floor-area"})
    dm_prod_bld_domapp = dm_prod.filter({"Categories1" : ['computer', 'dishwasher', 'dryer', 
                                                          'freezer', 'fridge', 'phone',
                                                          'tv', 'wmachine']})

    # production (units) = production [%] * demand

    # pipes
    dm_prod_bld_pipe.array = dm_prod_bld_pipe.array * dm_demand_bld_pipe.array
    dm_prod_bld_pipe.units["product-production"] = dm_demand_bld_pipe.units["bld_product-demand"]

    # floor
    dm_prod_bld_floor.array = dm_prod_bld_floor.array * dm_demand_bld_floor.array
    dm_prod_bld_floor.units["product-production"] = dm_demand_bld_floor.units["bld_product-demand"]

    # domestic appliances
    dm_prod_bld_domapp.array = dm_prod_bld_domapp.array * dm_demand_bld_domapp.array
    dm_prod_bld_domapp.units["product-production"] = dm_demand_bld_domapp.units["bld_product-demand"]


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
    dm_prod_tra_infra.units["product-production"] = dm_demand_tra_infra.units["tra_product-demand"]

    # veh
    dm_prod_tra_veh.array = dm_prod_tra_veh.array * dm_demand_tra_veh.array
    dm_prod_tra_veh.units["product-production"] = dm_demand_tra_veh.units["tra_product-demand"]


    ######################
    ##### LIFESTYLES #####
    ######################

    # get production for lifestyles
    dm_prod_lfs = dm_prod.filter({"Categories1": ['aluminium-pack', 'glass-pack', 'paper-pack',
                                                   'paper-print', 'paper-san', 'plastic-pack']})


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
    dm_lfs_matdec = material_decomposition(dm=dm_production_lfs, cdm=cdm_matdec_lfs)

    ########################
    ##### PUT TOGETHER #####
    ########################

    dm_matdec = dm_bld_pipe_matdec.copy()
    dm_matdec.append(dm_bld_floor_matdec, dim="Categories1")
    dm_matdec.append(dm_bld_domapp_matdec, dim="Categories1")
    dm_matdec.append(dm_tra_infra_matdec, dim="Categories1")
    dm_matdec.append(dm_tra_veh_matdec, dim="Categories1")
    dm_matdec.append(dm_lfs_matdec, dim="Categories1")

    # note: we are calling this material demand as this is the demand of materials 
    # that comes from the production sector (e.g. how much material is needed to
    # produce a car)
    DM_material_demand = {"material-demand": dm_matdec}
    DM_material_demand["material-demand"].drop("Categories2", ["other"])
    # TODO: understand if to keep other here and later

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
                    switch_ratio_prefix="material-switch-ratios_")

    material_switch(dm=dm_material_demand, dm_ots_fts=dm_material_switch,
                    cdm_const=cdm_material_switch, material_in="steel", material_out=["chem", "aluminium"],
                    product="trucks-ICE", switch_percentage_prefix="trucks-",
                    switch_ratio_prefix="material-switch-ratios_")

    #####################
    ##### BUILDINGS #####
    #####################

    # new buildings: switch to renewable materials (steel and cement to timber in new residential and non-residential)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "steel", material_out = ["timber"], 
                    product = 'floor-area-new-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "cement", material_out = ["timber"], 
                    product = 'floor-area-new-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "steel", material_out = ["timber"], 
                    product = 'floor-area-new-non-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "cement", material_out = ["timber"], 
                    product = 'floor-area-new-non-residential', switch_percentage_prefix = "build-", 
                    switch_ratio_prefix = "material-switch-ratios_", dict_for_output = DM_input_matswitchimpact)

    # renovated buildings: switch to insulated surfaces (chemicals to paper and natural fibers in renovated residential and non-residential)

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "chem", material_out = ["paper","natfibers"], 
                    product = "floor-area-reno-residential", switch_percentage_prefix = "reno-", 
                    switch_ratio_prefix = "material-switch-ratios_")

    material_switch(dm = dm_material_demand, dm_ots_fts = dm_material_switch, 
                    cdm_const = cdm_material_switch, material_in = "chem", material_out = ["paper","natfibers"], 
                    product = "floor-area-reno-non-residential", switch_percentage_prefix = "reno-", 
                    switch_ratio_prefix = "material-switch-ratios_")
    
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

    # subset aggregate demand for the materials we keep
    materials = ['aluminium', 'cement', 'chem', 'copper', 'glass', 'lime', 'paper', 'steel', 'timber']
    dm_material_production_natfiber = dm_matdec_agg.filter({"Categories1": ["natfibers"]}) # this will be used for interface agriculture
    dm_matdec_agg.filter({"Categories1": materials}, inplace=True)

    ######################
    ##### PRODUCTION #####
    ######################

    # material production [kt] = material demand [kt] * (1 - material net import [%])
    # TODO: add this quantity to the material stock

    # get net import % and make production %
    dm_temp = dm_material_net_import.copy()
    dm_temp.filter({"Categories1" : materials}, inplace = True)
    dm_temp.array = 1 - dm_temp.array

    # get material production
    dm_material_production_bymat = dm_matdec_agg.copy()
    dm_material_production_bymat.array = dm_matdec_agg.array * dm_temp.array
    dm_material_production_bymat.rename_col(col_in = 'material-decomposition', col_out = 'material-production', dim = "Variables")

    # include other industries from fxa
    dm_material_production_bymat.append(data2 = dm_matprod_other_industries, dim = "Categories1")
    dm_material_production_bymat.sort("Categories1")
    
    # put together
    DM_material_production = {"bymat" : dm_material_production_bymat, 
                              "natfiber" : dm_material_production_natfiber}
    
    # clean
    del dm_matdec_agg, dm_temp, materials, dm_material_production_bymat, dm_material_production_natfiber
    
    # return
    return DM_material_production

def calibration_material_production(DM_cal, dm_material_production_bymat, DM_material_production, 
                                    years_setting):
    
    # get calibration series
    dm_cal_sub = DM_cal["material-production"].copy()
    materials = dm_material_production_bymat.col_labels["Categories1"]
    dm_cal_sub.filter({"Categories1" : materials}, inplace = True)

    # get calibration rates
    DM_material_production["calib_rates_bymat"] = calibration_rates(dm = dm_material_production_bymat, dm_cal = dm_cal_sub,
                                                                    calibration_start_year = 1990, calibration_end_year = 2023,
                                                                    years_setting=years_setting)

    # do calibration
    dm_material_production_bymat.array = dm_material_production_bymat.array * DM_material_production["calib_rates_bymat"].array

    # clean
    del dm_cal_sub, materials
    
    return

def end_of_life(dm_transport_waste, dm_waste_management, dm_matrec_veh, 
                cdm_matdec_veh, dm_material_production_bymat):
    
    
    # in general:
    # littered + export + uncolleted + collected = 1
    # recycling + energy recovery + reuse + landfill + incineration = 1
    # note on incineration: transport will not have incineration, while electric waste yes
    
    # TODO: for the moment I am doing waste management only for cars and trucks, this will have to be done
    # for 'planes', 'ships', 'trains', batteries (probably this will be in minerals), 
    # appliances (for which we'll have to update buildings) and
    # buildings (which is already present in buildings, though we need to develop the data on their eol).
    # So far, the split of waste categories should be the same for transport and appliances, with the
    # only difference that incineration will be positive values for appliances. That should be the only
    # difference, so same formulas should apply.
    
    # make waste-collected, waste-uncollected, export, littered
    layer1 = ["export","littered","waste-collected","waste-uncollected"]
    dm_waste_layer1 = dm_waste_management.filter({"Categories1" : layer1})
    arr_temp = dm_transport_waste.array[...,np.newaxis] * dm_waste_layer1.array[:,:,np.newaxis,:,:]
    dm_transport_waste_bywsm_layer1 = DataMatrix.based_on(arr_temp, dm_transport_waste, 
                                                          {'Categories2': layer1}, 
                                                          units = dm_transport_waste.units)
    
    # make recycling, energy recovery, reuse, landfill, incineration
    layer2 = ["energy-recovery","incineration","landfill","recycling","reuse"]
    dm_waste_layer2 = dm_waste_management.filter({"Categories1" : layer2})
    # dm_waste_layer2.rename_col_regex("cars","waste-management_cars","Variables")
    # dm_waste_layer2.rename_col_regex("trucks","waste-management_trucks","Variables")
    # dm_waste_layer2.deepen("_","Variables")
    # dm_waste_layer2.switch_categories_order("Categories1","Categories2")
    dm_waste_collected = dm_transport_waste_bywsm_layer1.filter({"Categories2" : ["waste-collected"]})
    arr_temp = dm_waste_collected.array * dm_waste_layer2.array[:,:,np.newaxis,...]
    dm_transport_waste_bywsm_layer2 = DataMatrix.based_on(arr_temp, dm_waste_collected, 
                                                          {'Categories2': layer2}, 
                                                          units = dm_waste_collected.units)
    
    # do material decomposition for recycling
    dm_transport_waste_bywsm_recy = dm_transport_waste_bywsm_layer2.filter({"Categories2" : ["recycling"]})
    arr_temp = dm_transport_waste_bywsm_recy.array * cdm_matdec_veh.array[np.newaxis,np.newaxis,...]
    dm_transport_waste_bymat = DataMatrix.based_on(arr_temp, dm_transport_waste_bywsm_recy, 
                                                   {'Categories2': cdm_matdec_veh.col_labels["Categories2"]}, 
                                                   units = "t")
    dm_transport_waste_bymat.units["tra_product-waste"] = "t"
    
    # get material recovered post consumer
    dm_transport_waste_bymat
    dm_matrec_veh
    dm_transport_matrecovered_veh = dm_matrec_veh.copy()
    idx = dm_transport_waste_bymat.idx
    dm_transport_matrecovered_veh.array = \
        dm_transport_waste_bymat.array[:,:,idx["tra_product-waste"],...] *\
        dm_transport_matrecovered_veh.array
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

def industry(lever_setting, years_setting, interface = Interface(), calibration = True):

    # industry data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    industry_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/industry.pickle')
    DM_fxa, DM_ots_fts, DM_cal, CDM_const = read_data(industry_data_file, lever_setting)

    cntr_list = DM_ots_fts["product-net-import"].col_labels['Country']

    if interface.has_link(from_sector='transport', to_sector='industry'):
        DM_transport = interface.get_link(from_sector='transport', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing transport to industry interface')
        filepath = os.path.join(current_file_directory, '../_database/data/interface/transport_to_industry.pickle')
        with open(filepath, 'rb') as handle:
            DM_transport = pickle.load(handle)
        for key in DM_transport.keys():
            DM_transport[key].filter({'Country': cntr_list}, inplace=True)

    if interface.has_link(from_sector='lifestyles', to_sector='industry'):
        dm_demand_lfs = interface.get_link(from_sector='lifestyles', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing lifestyles to industry interface')
        filepath = os.path.join(current_file_directory, '../_database/data/interface/lifestyles_to_industry.pickle')
        with open(filepath, 'rb') as handle:
            dm_demand_lfs = pickle.load(handle)
        dm_demand_lfs.filter({'Country': cntr_list}, inplace=True)

    if interface.has_link(from_sector='buildings', to_sector='industry'):
        DM_buildings = interface.get_link(from_sector='buildings', to_sector='industry')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing buildings to industry interface')
        filepath = os.path.join(current_file_directory, '../_database/data/interface/buildings_to_industry.pickle')
        with open(filepath, 'rb') as handle:
            DM_buildings = pickle.load(handle)
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
        calibration_material_production(DM_cal, DM_material_production["bymat"], DM_material_production,
                                        years_setting)
        
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
    years_setting = [1990, 2023, 2050, 5]
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
