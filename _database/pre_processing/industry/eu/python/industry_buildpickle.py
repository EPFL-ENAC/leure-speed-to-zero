

# packages
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting, fix_jumps_in_dm
import pandas as pd
import pickle
import os
import numpy as np
import warnings
import eurostat
# from _database.pre_processing.api_routine_Eurostat import get_data_api_eurostat
warnings.simplefilter("ignore")
import plotly.express as px
import plotly.io as pio
import re
pio.renderers.default='browser'

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_material-recovery.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# files
files_directory = os.path.join(current_file_directory, '../data/datamatrix')
files = os.listdir(files_directory)

# create DM_industry
DM_ots = {}
DM_fts = {}
DM_fxa = {}
DM_cal = {}
CDM_const = {}
DM_industry = {}

##################
##### LEVERS #####
##################

# list(np.array(files)[[bool(re.search("lever", i)) for i in files]])
lever_files = ['lever_material-switch.pickle', 'lever_material-efficiency.pickle', 
               'lever_energy-efficiency.pickle', 'lever_carbon-capture.pickle', 
               'lever_technology-share.pickle', 'lever_material-net-import.pickle',
               'lever_product-net-import.pickle', 'lever_energy-switch.pickle',
               'lever_waste-management.pickle', 'lever_material-recovery.pickle']
lever_names = ['material-switch', 'material-efficiency', 
               'technology-development',  'cc', 
               'technology-share', 'material-net-import', 
               'product-net-import', 'energy-carrier-mix', 
               'eol-waste-management', 'eol-material-recovery']

# load dms
for i in range(0, len(lever_files)):
    filepath = os.path.join(current_file_directory, '../data/datamatrix/' + lever_files[i])
    with open(filepath, 'rb') as handle:
        DM = pickle.load(handle)
    DM_ots[lever_names[i]] = DM["ots"]
    DM_fts[lever_names[i]] = DM["fts"]

# drop ammonia
lever_names = ['material-efficiency','material-net-import',
               'eol-material-recovery']
for n in lever_names:
    DM_ots[n].drop("Categories1","ammonia")
    for i in range(1,4+1):
        DM_fts[n][i].drop("Categories1","ammonia")

lever_names = ['technology-development','cc',
               'technology-share','energy-carrier-mix']
for n in lever_names:
    DM_ots[n].drop("Categories1","ammonia-tech")
    for i in range(1,4+1):
        DM_fts[n][i].drop("Categories1","ammonia-tech")

# save
DM_industry["ots"] = DM_ots
DM_industry["fts"] = DM_fts

#############################
##### FIXED ASSUMPTIONS #####
#############################

# files_temp = list(np.array(files)[[bool(re.search("fxa", i)) for i in files]])
# names_temp = [i.split("fxa_")[1].split(".pickle")[0] for i in files_temp]
# ['prod', 'cost-matprod', 'cost-CC']

# costs
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'fxa_costs.pickle')
with open(filepath, 'rb') as handle:
    DM = pickle.load(handle)
DM_fxa["cost-matprod"] = DM["costs"]
DM_fxa["cost-CC"] = DM["costs-cc"]

# material production
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'fxa_material-production.pickle')
with open(filepath, 'rb') as handle:
    DM = pickle.load(handle)
DM_fxa["prod"] = DM

#######################
##### CALIBRATION #####
#######################

files_temp = list(np.array(files)[[bool(re.search("calibration", i)) for i in files]])
names_temp = [i.split("calibration_")[1].split(".pickle")[0] for i in files_temp]

for i in range(0, len(files_temp)):
    filepath = os.path.join(current_file_directory, '../data/datamatrix/' + files_temp[i])
    with open(filepath, 'rb') as handle:
        dm = pickle.load(handle)
    DM_cal[names_temp[i]] = dm

#####################
##### CONSTANTS #####
#####################

# files_temp = list(np.array(files)[[bool(re.search("const", i)) for i in files]])
# names_temp = [i.split("const_")[1].split(".pickle")[0] for i in files_temp]

# material switch ratios
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'const_material-switch-ratios.pickle')
with open(filepath, 'rb') as handle:
    cdm = pickle.load(handle)
CDM_const["material-switch"] = cdm

# material decomposition
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'const_material-decomposition.pickle')
with open(filepath, 'rb') as handle:
    CDM = pickle.load(handle)
CDM_const["material-decomposition_pipe"] = CDM["bld_pipe"]
CDM_const["material-decomposition_floor"] = CDM["bld_floor"]
CDM_const["material-decomposition_domapp"] = CDM["bld_domapp"]
CDM_const["material-decomposition_infra"] = CDM["tra_infra"]
CDM_const["material-decomposition_veh"] = CDM["tra_veh"]
CDM_const["material-decomposition_lfs"] = CDM["lfs"]

# energy demand
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'const_energy-demand.pickle')
with open(filepath, 'rb') as handle:
    CDM = pickle.load(handle)
CDM_const["energy_excl-feedstock"] = CDM["energy-demand-excl-feedstock"]
CDM_const["energy_feedstock"] = CDM["energy-demand-feedstock"]

# emission factors
filepath = os.path.join(current_file_directory, '../data/datamatrix/' + 'const_emissions-factors.pickle')
with open(filepath, 'rb') as handle:
    CDM = pickle.load(handle)
CDM_const["emission-factor"] = CDM["combustion-emissions"]
CDM_const["emission-factor-process"] = CDM["process-emissions"]


########################
##### PUT TOGETHER #####
########################

DM_industry = {
    'fxa': DM_fxa,
    'fts': DM_fts,
    'ots': DM_ots,
    'calibration': DM_cal,
    "constant" : CDM_const
}

################################
##### GENERATE SWITZERLAND #####
################################

for key in ['fxa', 'ots', 'calibration']:
    
    dm_names = list(DM_industry[key])
    for name in dm_names:
        
        dm_temp = DM_industry[key][name]
        if "Switzerland" not in dm_temp.col_labels["Country"]:
            
            idx = dm_temp.idx
            arr_temp = dm_temp.array[idx["Austria"],...]
            dm_temp.add(arr_temp[np.newaxis,...], "Country", "Switzerland")
            dm_temp.sort("Country")


dm_names = list(DM_industry["fts"])
for name in dm_names:
    
    for i in range(1,4+1):
        
        dm_temp = DM_industry["fts"][name][i]
        if "Switzerland" not in dm_temp.col_labels["Country"]:
            
            idx = dm_temp.idx
            arr_temp = dm_temp.array[idx["Austria"],...]
            dm_temp.add(arr_temp[np.newaxis,...], "Country", "Switzerland")
            dm_temp.sort("Country")

################
##### SAVE #####
################

# save
f = os.path.join(current_file_directory, '../../../../data/datamatrix/industry.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM_industry, handle, protocol=pickle.HIGHEST_PROTOCOL)








