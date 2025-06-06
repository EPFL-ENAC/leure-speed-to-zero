import pandas as pd

from model.common.data_matrix_class import DataMatrix
from model.common.interface_class import Interface
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, read_database_to_ots_fts_dict
from model.common.auxiliary_functions import compute_stock, filter_geoscale
from model.common.auxiliary_functions import read_level_data, create_years_list, linear_fitting
import pickle
import json
import os
import numpy as np
import time


def read_data(data_file, lever_setting):

    with open(data_file, 'rb') as handle:
        DM_forestry = pickle.load(handle)

    dict_const = DM_forestry['constant']
    dict_fxa = DM_forestry['fxa']

    # Read fts based on lever_setting
    #DM_ots_fts = read_level_data(DM_forestry, lever_setting)

    DM_forestry = {'fxa': dict_fxa,
        'constant': dict_const}

    return DM_forestry

#####################################################################################################################
#####################################################################################################################
# Calculation Tree - Forestry:
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
# Calculation Tree - Wood demand in m3:
#####################################################################################################################
def wood_demand_m3 (dm_wood_demand, DM_forestry):
    # Wood demand in tonnes
    dm_wood_demand_industry = dm_wood_demand
    dm_wood_demand

    return dm_wood_demand


def forestry(lever_setting, years_setting, interface=Interface()):

    ##############################################################
    # Load the datamatrix of Forestry: the following is computed in the pre-processing, and includes ots, fts, fxa, cp
    ##############################################################

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    forestry_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/forestry.pickle')
    # Read forestry pickle data based on lever setting and return data in a structured DM
    DM_forestry = read_data(forestry_data_file, lever_setting)
    #cntr_list = DM['key'].col_labels['Country']
    cntr_list = ['Switzerland']

    ###################################################################
    # Interface - Energy to Forestry: If the input from Power/Energy are available in the interface, read them, else read from pickle
    ###################################################################

    if interface.has_link(from_sector='energy', to_sector='forestry'):
        dm_fuelwood_demand = interface.get_link(from_sector='energy', to_sector='forestry')
    else:
        if len(interface.list_link()) != 0:
            print("You are missing " + 'energy' + " to " + 'forestry' + " interface")
        lfs_interface_data_file = os.path.join(current_file_directory,
                                               '../_database/data/interface/energy_to_forestry.pickle')
        with open(lfs_interface_data_file, 'rb') as handle:
            dm_fuelwood_demand = pickle.load(handle)
        dm_fuelwood_demand.filter({'Country': cntr_list}, inplace=True)
    ####################################################################################################################
    # Interface - Industry to Forestry:
    ####################################################################################################################

    if interface.has_link(from_sector='industry', to_sector='forestry'):
        dm_wood_demand = interface.get_link(from_sector='industry', to_sector='forestry')
    else:
        if len(interface.list_link()) != 0:
            print("You are missing " + 'industry' + " to " + 'forestry' + " interface")
        lfs_interface_data_file = os.path.join(current_file_directory,
                                               '../_database/data/interface/industry_to_forestry.pickle')
        with open(lfs_interface_data_file, 'rb') as handle:
            dm_wood_demand = pickle.load(handle)
        dm_wood_demand.filter({'Country': cntr_list}, inplace=True)

    ####################################################################################################################
    # Functions - Wood demand in m3
    ####################################################################################################################

    dm_wood_demand_m3 = wood_demand_m3(dm_wood_demand, DM_forestry)

    ####################################################################################################################
    # Interface - Forestry to TPE :
    ####################################################################################################################

    #results_run = forestry_to_tpe(DM_, DM_)


    return # results_run


def local_forestry_run():
    # Function to run only transport module without converter and tpe
    years_setting = [1990, 2023, 2025, 2050, 5]
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
    lever_setting = json.load(f)[0]

    global_vars = {'geoscale': 'Switzerland'}
    filter_geoscale(global_vars)

    results_run = forestry(lever_setting, years_setting)

    return results_run


local_forestry_run()