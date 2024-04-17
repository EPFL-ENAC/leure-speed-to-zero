# Import the Packages

import pandas as pd
import numpy as np
import pickle  # read/write the data in pickle
import json  # read the lever setting
import os  # operating system (e.g., look for workspace)

# Import Class
from model.common.data_matrix_class import DataMatrix  # Class for the model inputs
from model.common.constant_data_matrix_class import ConstantDataMatrix  # Class for the constant inputs
from model.common.auxiliary_functions import read_level_data

# ImportFunctions
from model.common.io_database import read_database, read_database_fxa  # read functions for levers & fixed assumptions
from model.common.auxiliary_functions import read_database_to_ots_fts_dict, read_database_to_ots_fts_dict_w_groups


# filtering the constants & read csv and prepares it for the pickle format

# Lever setting for local purpose


def init_years_lever():
    # function that can be used when running the module as standalone to initialise years and levers
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]
    return years_setting, lever_setting


# Setting up the database in the module
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

    # Initiate the dictionary for ots & fts
    dict_ots = {}
    dict_fts = {}

    # Data - Lever - Climate temperature
    file = 'climate_temperature'  # File name to read
    lever = 'temp'  # Lever name to match the JSON?

    # Creates the datamatrix for lifestyles population
    dict_ots, dict_fts = read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list=[1, 0, 1, 0], baseyear=baseyear,
                                                                years=years_all, dict_ots=dict_ots, dict_fts=dict_fts,
                                                                column='eucalc-name', group_list=[
                                                                            'clm_climate-impact-space',
                                                                            'clm_climate-impact_average',
                                                                            'clm_capacity-factor',
                                                                            'clm_temp_global'
                                                                            ])

    #  Create the data matrix for lifestyles
    DM_climate = {
        'fts': dict_fts,
        'ots': dict_ots
    }

    # Pickle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))  # creates local path variable
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/climate.pickle')
    # creates path variable for the pickle
    with open(f, 'wb') as handle:  # 'wb': writing binary / standard protocol for pickle
        pickle.dump(DM_climate, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return

# Update/Create the Pickle
# database_from_csv_to_datamatrix()  # un-comment to update

    #  Reading the Pickle
def read_data(data_file, lever_setting):
    with open(data_file, 'rb') as handle:  # read binary (rb)
        DM_climate = pickle.load(handle)

    DM_ots_fts = read_level_data(DM_climate,
                                 lever_setting)  # creates the datamatrix according to the lever setting?

    # Extract sub-data-matrices according to the flow (parallel)
    # TPE sub-matrix (global temperature)
    dm_temperature_global = DM_ots_fts['temp']['clm_temp_global']
    dm_temperature_average = DM_ots_fts['temp']['clm_climate-impact_average']
    #dm_space_heating = DM_ots_fts['temp']['clm_climate-impact-space-heating']
    #dm_space_cooling = DM_ots_fts['temp']['clm_climate-impact-space-cooling']
    # FIXME: split heating and colling or send all as dm_building
    dm_space_buildings = DM_ots_fts['temp']['clm_climate-impact-space']
    dm_energy = DM_ots_fts['temp']['clm_capacity-factor']

    # Aggregated Data Matrix - Appliances

    DM_climate_impact = {
        'global-temp': dm_temperature_global,
        'climate-impact': dm_temperature_average,
        'heating-cooling': dm_space_buildings,
        'capacity-factor': dm_energy
    }

    return DM_climate_impact

def climate_workflow(DM_climate_impact):

    # Global temperature
    dm_temperature_global = DM_climate_impact['global-temp']
    dm_temperature_average = DM_climate_impact['climate-impact']
    dm_space_buildings = DM_climate_impact['heating-cooling']
    dm_energy = DM_climate_impact[ 'capacity-factor']

    return dm_temperature_global, dm_temperature_average, dm_space_buildings, dm_energy

# CORE module
def climate(lever_setting, years_setting):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    climate_data_file = os.path.join(current_file_directory,
                                        '../_database/data/datamatrix/geoscale/climate.pickle')
    DM_climate_impact = read_data(climate_data_file, lever_setting)

    # To send to TPE (result run)
    dm_temperature_global = climate_workflow(DM_climate_impact)

    # To send to buildings (result run)
    dm_space_buildings = climate_workflow(DM_climate_impact)

    # To send to energy (result run)
    dm_energy = climate_workflow(DM_climate_impact)

    # TODO: To send to water when water will be done

    # concatenate all results to df

    results_run = dm_temperature_global
    return results_run


# Local run of lifestyles
def local_climate_run():
    # Initiate the year & lever setting
    years_setting, lever_setting = init_years_lever()
    climate(lever_setting, years_setting)

    return

local_climate_run()  # to un-comment to run in local