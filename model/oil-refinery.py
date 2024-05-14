#######################################################################################################################
# SECTION: Import Packages, Classes & Functions
#######################################################################################################################

import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)
import pandas as pd

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.auxiliary_functions import read_level_data, filter_geoscale

# ImportFunctions
from model.common.io_database import read_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups,\
    update_interaction_constant_from_file


#######################################################################################################################
# ModelSetting - Oil Refinery
#######################################################################################################################

def database_from_csv_to_datamatrix():
    years_setting = [1990, 2015, 2050, 5]  # Set the timestep for historical years & scenarios
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int))
    # Defines the part of dataset that is historical years
    years_fts = list(
        np.linspace(start=baseyear + step_fts, stop=lastyear, num=int((lastyear - baseyear) / step_fts)).astype(int))
    # Defines the part of dataset that is scenario
    years_all = years_ots + years_fts  # Defines all years

#######################################################################################################################
# DataFixedAssumptions - Oil refinery
#######################################################################################################################

    # Read fixed assumptions to datamatrix
    df = read_database_fxa('oil-refinery_fixed-assumptions')
    dm = DataMatrix.create_from_df(df, num_cat=0)

    # Keep only ots and fts years
    dm = dm.filter(selected_cols={'Years': years_all})

    # Dictionary
    dm_refinery_ratio = dm.filter({'Variables': ['ory_refinery_country-ratio']})

    # ToDo: check the values as 12% for France is very low, so meaning of this ratio?
    # ToDo: add calibration factors

    dict_fxa = {
        'refinery-ratio': dm_refinery_ratio
    }

#######################################################################################################################
# DataConstants - Oil refinery
#######################################################################################################################

    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_refinery.*', num_cat=0)


#######################################################################################################################
# DataMatrices - Oil refinery Data Matrix
#######################################################################################################################

    DM_refinery = {
        'fxa': dict_fxa,
        'constant': cdm_const
    }

#######################################################################################################################
# DataPickle - Oil refinery
#######################################################################################################################

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/oil-refinery.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_refinery, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return DM_refinery

# update_interaction_constant_from_file('interactions_constants_local') # uncomment to update constant
# database_from_csv_to_datamatrix()  # un-comment to update pickle

#######################################################################################################################
# DataSubMatrices - Oil refinery
#######################################################################################################################

#######################################################################################################################
# LocalInterfaces - Power
#######################################################################################################################
def simulate_power_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-power-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_power = DataMatrix.create_from_df(df, num_cat=1)

    return dm_power

#######################################################################################################################
# LocalInterfaces - Buildings
#######################################################################################################################
def simulate_buildings_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-buildings-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_buildings = DataMatrix.create_from_df(df, num_cat=1)

    return dm_buildings

#######################################################################################################################
# LocalInterfaces - Transport
#######################################################################################################################
def simulate_transport_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-transport-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_transport = DataMatrix.create_from_df(df, num_cat=1)

    return dm_transport

#######################################################################################################################
# LocalInterfaces - Industry
#######################################################################################################################
def simulate_industry_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-industry-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_industry = DataMatrix.create_from_df(df, num_cat=1)

    return dm_industry

#######################################################################################################################
# LocalInterfaces - Ammonia
#######################################################################################################################
def simulate_ammonia_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-ammonia-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_ammonia = DataMatrix.create_from_df(df, num_cat=1)

    return dm_ammonia

#######################################################################################################################
# LocalInterfaces - Agriculture
#######################################################################################################################
def simulate_agriculture_to_refinery_input():
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/"
                                             "All-Countries-interface_from-agriculture-to-oil-refinery.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm_agriculture = DataMatrix.create_from_df(df, num_cat=1)

    return dm_agriculture

#######################################################################################################################
# CalculationTree - Module - sub flow
#######################################################################################################################
def yearly_production_workflow(dm_climate, dm_capacity, dm_ccus, cdm_const):

    ######################################
    # CalculationLeafs - Gross electricity production [GWh]
    ######################################
    # Tuto: Tree parallel (array)
    idx_cap = dm_capacity.idx
    idx_clm = dm_climate.idx
    ay_gross_yearly_production = dm_capacity.array[:,:,idx_cap['pow_existing-capacity'],:] \
                                 * dm_climate.array[:,:,idx_clm['clm_capacity-factor'],:]*8760
    dm_capacity.add(ay_gross_yearly_production, dim='Variables', col_label='pow_gross-yearly-production', unit='GWh')

#######################################################################################################################
# CoreModule - Refinery
#######################################################################################################################

def refinery(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    refinery_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/oil-refinery.pickle')
    with open(refinery_data_file, 'rb') as handle:  # read binary (rb)
        DM_refinery= pickle.load(handle)

    results_run = DM_refinery

    return results_run


#######################################################################################################################
# LocalRun - Refinery
#######################################################################################################################

def local_refinery_run():
    # Function to run only transport module without converter and tpe
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]

    global_vars = {'geoscale': 'Switzerland'}
    filter_geoscale(global_vars)

    results_run = refinery(lever_setting, years_setting)

    return results_run


results_run = local_refinery_run()