
from model.common.data_matrix_class import DataMatrix
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_level_data
from model.common.auxiliary_functions import calibration_rates, cost
from model.common.auxiliary_functions import material_switch, energy_switch
import pickle
import json
import os
import numpy as np
import re
import warnings
import time
warnings.simplefilter("ignore")

def read_data(data_file, lever_setting):
    
    # load dm
    with open(data_file, 'rb') as handle:
        DM_minerals = pickle.load(handle)

    # # get fxa
    # DM_fxa = DM_minerals['fxa']

    # Get ots fts based on lever_setting
    DM_ots_fts = read_level_data(DM_minerals, lever_setting)

    # # get calibration
    # dm_cal = DM_minerals['calibration']

    # get constants
    CMD_const = DM_minerals['constant']

    # clean
    del handle, DM_minerals, data_file, lever_setting
    
    # return
    return DM_ots_fts, CMD_const

def minerals(lever_setting, years_setting, interface = Interface(), calibration = False):
    
    # minerals data file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    minerals_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/minerals_new.pickle')
    DM_ots_fts, CDM_const = read_data(minerals_data_file, lever_setting)
    
    return

def local_minerals_run():
    
    # get years and lever setting
    years_setting = [1990, 2023, 2025, 2050, 5]
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(current_file_directory, '../config/lever_position.json'))
    lever_setting = json.load(f)[0]
    # lever_setting["lever_energy-carrier-mix"] = 3
    # lever_setting["lever_cc"] = 3
    # lever_setting["lever_material-switch"] = 3
    # lever_setting["lever_technology-share"] = 4
    
    # get geoscale
    global_vars = {'geoscale': 'EU27|Switzerland|Vaud'}
    filter_geoscale(global_vars)

    # run
    results_run = minerals(lever_setting, years_setting)
    
    # return
    return results_run

# # run local
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/model/minerals_module_new.py"
# start = time.time()
results_run = local_minerals_run()
# end = time.time()
# print(end-start)


