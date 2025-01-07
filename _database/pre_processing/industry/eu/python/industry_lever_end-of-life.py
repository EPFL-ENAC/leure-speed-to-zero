
# dm_waste_management
# DataMatrix with shape (32, 33, 6, 10), variables ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE'] and categories1 ['energy-recovery', 'export', 'incineration', 'landfill', 'littered', 'recovery', 'recycling', 'reuse', 'waste-collected', 'waste-uncollected']
# dm_matrec_veh
# DataMatrix with shape (32, 33, 6, 27), variables ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE'] and categories1 ['abs', 'aluminium', 'brass', 'chromium', 'cobalt', 'copper', 'epdm', 'eps', 'ferrous', 'lithium', 'mangnesium', 'neodymium', 'pa', 'pbt', 'pcb', 'pe', 'pmma', 'pom', 'pp', 'ps', 'pur', 'pvc', 'silver', 'steel', 'tin', 'tungsten', 'zinc']

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
pio.renderers.default='browser'

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_end-of-life.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# Eurostat databases:
# env_waselv for vehicles
# env_waselee for larger appliances, pc and electronics, tv and pc
# env_waspac for packaging waste

###############################################
##### GET DATA ON END OF LIFE OF VEHICLES #####
###############################################

# get data
# df = eurostat.get_data_df("env_waselv")
filepath = os.path.join(current_file_directory, '../data/eurostat/env_waselv.csv')
# df.to_csv(filepath, index = False)
df = pd.read_csv(filepath)

# in general:
# total = littered + exported + collected + uncollected
# collected = recycling + energy recovery + reuse + landfill + incineration

# get geo column
geo_column = 'geo\\TIME_PERIOD'

# filter for unit of measure: Tonne
df = df.loc[df['unit'] == 'T',:]

# filter based on different combinations of 'waste' and 'wst_oper'
df.columns
df['wst_oper'].unique() # array(['DSP', 'GEN', 'RCV', 'RCV_E', 'RCY', 'REU'], dtype=object)
df['waste'].unique() # array(['DMDP', 'EXP', 'LIQ', 'W160103', 'W160107', 'W160119', 'W160120', 'W1601A', 'W1601B', 'W1601C', 'W1606', 'W1608', 'W1910', 'W191001', 'W191002', 'W1910A', 'W1910B', 'ELV'], dtype=object)
# abbreviations: disposed (DSP), generated (GEN), recovered (RCV), energy recovery (RCV-E), recycled (RCY), 
# reused (REU), dismantling and de-pollution (DMDP), exported (EXP), liquids (LIQ), end of life vehicles (ELV).
# 2.1 Select from 'Waste arising only from end-of-life vehicles of type passenger cars (M1), 
# light commercial vehicles (N1) and three wheeled moped vehicles (ELV)', the 'Waste generated (GEN)' & 'Recycling (RCY)'
df_elv_1 = df.loc[(df['waste'] == 'ELV') & (df['wst_oper'].isin(['GEN', 'RCY', 'RCV', 'REU'])),:]
# 2.2 Select from 'End-of-life vehicles exported (EXP)', 'Waste generated (GEN)' & 'Disposal (DSP)'
df_elv_2 = df.loc[(df['waste'] == 'EXP') & (df['wst_oper'].isin(['GEN', 'DSP'])),:]
# 2.3 Select from 'Waste from dismantling and de-pollution of end-of-life-vehicles 
# (LIQ+W1601A+W1601B+W1601C+LoW:160103+160107+160119+160120+1606+1608) (DMDP)' & 
# 'Waste arising from shredding of end-of-life vehicles (W191001+W191002+W1910A+W1910B)', 
# 'Recovery - energy recovery (R1)' & 'Disposal (DSP)' & 'Recovery (RCV)'
df_elv_3 = df.loc[(df['waste'].isin(['DMDP', 'W1910'])) & (df['wst_oper'].isin(['RCV_E', 'DSP', 'RCV'])),:]
# Combine all filtered DataFrames into one
df_elv = pd.concat([df_elv_1, df_elv_2, df_elv_3])

# renaming specific (waste, wst_oper) combinations, EU27, and geoscale
combination_replace_dict = {
    ('ELV', 'GEN'): 'GEN', # Waste generated
    ('ELV', 'RCY'): 'RCY', # Recycling
    ('EXP', 'GEN'): 'EXP-GEN', # Exported
    ('DMDP', 'RCV_E'): 'R1_DMDP', # Energy recovery of waste from dismantling and de-pollution
    ('W1910', 'RCV_E'): 'R1_W1910', # Energy recovery of waste from shredding
    ('DMDP', 'DSP'): 'DSP-DMDP', # Disposal of waste from dismantling and de-pollution
    ('W1910', 'DSP'): 'DSP-W1910', # Disposal of waste from shredding
    ('EXP', 'DSP'): 'DSP-EXP', # Disposal of exported vehicles
    ('ELV', 'RCV'): 'recovery', # recovery
    ('ELV','REU'): 'reuse', # reuse
    ('DMDP', 'RCV'): 'RCV_DMDP', # placeholder
    ('W1910', 'RCV'): 'RCV_W1910' # placeholder
}
# Function to replace based on the combination of 'waste' and 'wst_oper'
def translate_waste_oper(row):
    return combination_replace_dict.get((row['waste'], row['wst_oper']), None)
# Apply the replacement
df_elv['translated'] = df_elv.apply(translate_waste_oper, axis=1)

# Rename the 'geo\\TIME_PERIOD' column to 'geoscale' and replace 'EU27_2020' with 'EU27'
df_elv.rename(columns={'geo\\TIME_PERIOD': 'geoscale'}, inplace=True)
df_elv['geoscale'] = df_elv['geoscale'].replace({'EU27_2020': 'EU27'})

# fix country names
country_list = {'AT' : "Austria", 'BE' : "Belgium", 'BG': "Bulgaria", 'CY' : "Cyprus", 
                'CZ' : "Czech Republic", 'DE' : "Germany", 'DK' : "Denmark", 'EE' : "Estonia", 
                'EL' : "Greece", 'ES' : "Spain",'FI' : "Finland", 'FR' : "France", 
                'HR' : "Croatia", 'HU' : "Hungary", 'IE' : "Ireland", 'IS' : "Iceland", 
                'IT' : "Italy", 'LI' : "Liechtenstein", 'LT' : "Lithuania", 'LU' : "Luxembourg", 
                'LV' : "Latvia", 'MT' : "Malta", 'NL' : "Netherlands", 'NO' : "Norway", 
                'PL' : "Poland", 'PT' : "Portugal", 'RO' : "Romania", 'SE' : "Sweden", 
                'SI' : "Slovenia", 'SK' : "Slovakia"}
for c in country_list.keys():
    df_elv.loc[df_elv["geoscale"] == c,"geoscale"] = country_list[c]
drops = ["Liechtenstein"]
df_elv = df_elv.loc[~df_elv["geoscale"].isin(drops),:]
len(df_elv["geoscale"].unique()) # note that we are missing UK, to do at the end

# aggregate by new "translated" category
df_elv = df_elv.drop(columns=['freq', 'unit'])
df_elv = df_elv.melt(id_vars=['geoscale', 'waste', 'wst_oper', 'translated'], var_name='timescale',value_name='value')
df_elv = df_elv.pivot_table(index=['geoscale', 'timescale'], columns='translated', 
                            values='value', aggfunc='sum').reset_index()

####################################
##### GET MUNICIPAL WASTE DATA #####
####################################

# get data
# df = eurostat.get_data_df("env_wasmun")
filepath = os.path.join(current_file_directory, '../data/eurostat/env_wasmun.csv')
# df.to_csv(filepath, index = False)
df = pd.read_csv(filepath)

# Filter for unit of measure: Thousand tonnes
df_mun = df.loc[df['unit'] == 'THS_T',:]

# get only incineration (DSP_I) and landfill (DSP_L_OTH)
waste_management = ['DSP_L_OTH', 'DSP_I']  # landfill, incineration
df_mun = df_mun.loc[df_mun['wst_oper'].isin(waste_management),:]

# rename the specified values using the correct column names
replace_dict = {
    'geo\\TIME_PERIOD': {'EU27_2020': 'EU27'},
    'wst_oper': {
        'DSP_L_OTH': 'landfill-mun',
        'DSP_I': 'incineration-mun'
    }
}
df_mun = df_mun.replace(replace_dict)

# fix country names
for c in country_list.keys():
    df_mun.loc[df_mun["geo\\TIME_PERIOD"] == c,"geo\\TIME_PERIOD"] = country_list[c]
df_mun["geo\\TIME_PERIOD"].unique()
drops = ['AL', 'BA', 'CH', 'ME', 'MK', 'RS', 'TR', 'XK']
df_mun = df_mun.loc[~df_mun["geo\\TIME_PERIOD"].isin(drops),:]

# reshape
long_df = df_mun.melt(id_vars=['geo\\TIME_PERIOD', 'wst_oper'], 
                      value_vars=[str(year) for year in range(2007, 2019)], 
                      var_name="timescale", value_name="value")
long_df.rename(columns={'geo\\TIME_PERIOD': 'geoscale'}, inplace=True)
long_df['wst_oper'] = long_df['wst_oper'] + '[t]'
pivot_index = ['geoscale', 'timescale']
df_mun = long_df.pivot_table(index=pivot_index, columns="wst_oper", 
                              values="value", aggfunc='sum').reset_index()
df_mun = df_mun.sort_values(by=['geoscale', "timescale"])

#####################
##### SOMETHING #####
#####################

# merging df_elv and df_mun based on geoscale and timescale
merged_df = pd.merge(df_mun, df_elv, on=['geoscale', 'timescale'], how='outer')

# move EU27 to the top
merged_df['sort_order'] = merged_df['geoscale'].apply(lambda x: 0 if x == 'EU27' else 1)
merged_df = merged_df.sort_values(by=['sort_order', 'geoscale', 'timescale'], ascending=[True, True, True])
merged_df = merged_df.drop(columns='sort_order')
merged_df.reset_index(drop=True, inplace=True)

# linearly regress waste-collected, landfill, and incineration over time (2007-2018)
df = merged_df.copy()
excluded_years = ["2005", "2006", "2007", "2008", "2009", "2010"]
included_years = [year for year in df['timescale'].unique() if year not in excluded_years]
df = df[df['timescale'].isin(included_years)]
df['timescale'] = pd.to_numeric(df['timescale'])
eu27_data = df[df['geoscale'] == 'EU27']
included_countries = df['geoscale'].unique()
included_countries = list(included_countries[[i not in "EU27" for i in included_countries]])
for year in eu27_data['timescale'].unique(): # if EU27 value for GEN is missing, create it by aggregating with other countries
    if pd.isna(eu27_data.loc[eu27_data['timescale'] == year, 'GEN']).any():
        aggregate_value = df[(df['timescale'] == year) & (df['geoscale'].isin(included_countries))]['GEN'].sum()
        df.loc[(df['geoscale'] == 'EU27') & (df['timescale'] == year), 'GEN'] = aggregate_value

# note: in theory this chunk is useless as we have GEN for all countries
# # perform regression for GEN column for each country in included_countries
# for country in included_countries:
#     country_data = df[df['geoscale'] == country].copy()
#     if country_data.empty:
#         continue
#     X_country = country_data['timescale'].values.reshape(-1, 1)
#     y = country_data['GEN'].values
#     missing_indices = np.where(pd.isna(y))[0]
#     if missing_indices.size > 0 and len(y) - len(missing_indices) > 1:
#         slope, intercept = np.polyfit(X_country[~pd.isna(y)].flatten(), y[~pd.isna(y)], 1)
#         y_pred = slope * X_country[missing_indices].flatten() + intercept
#         country_data.iloc[missing_indices, country_data.columns.get_loc('GEN')] = np.maximum(0, y_pred)
#         df.update(country_data)

# note: in theory, also this chunk of code is useless, as we already have all data (at least for the countries in EUCalc)
# columns_to_regress = ['RCY', 'DSP-W1910', 'DSP-DMDP', 'DSP-EXP', 'EXP-GEN', 'R1_DMDP', 'R1_W1910', 'recovery', 'reuse']
# for country in df['geoscale'].unique():
#     country_data = df[df['geoscale'] == country].copy()
#     if country != 'EU27':  # Skip 'EU27' to avoid double-counting
#         X_country = country_data['GEN'].values.reshape(-1, 1)  # Use 'GEN' column as the independent variable for regression
#         for column in columns_to_regress:
#             y = country_data[column].values
#             valid_indices = ~pd.isna(y)  # Boolean array of valid data points
#             missing_indices = np.where(pd.isna(y))[0]  # Indices where data is missing
#             # Ensure there are enough valid data points for regression
#             if missing_indices.size > 0 and valid_indices.sum() > 1:
#                 try:
#                     # Perform linear regression using numpy's polyfit
#                     slope, intercept = np.polyfit(X_country[valid_indices].flatten(), y[valid_indices], 1)
#                     y_pred = slope * X_country[missing_indices].flatten() + intercept
#                     # Fill the missing values in the original dataframe
#                     country_data.loc[country_data.index[missing_indices], column] = np.maximum(0, y_pred)
#                 except np.linalg.LinAlgError:
#                     df.update(country_data)

# next time: re-start from same point in elv.py and finish up the cleaning, then continue with the other products










