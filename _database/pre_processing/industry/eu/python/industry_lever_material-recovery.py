
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_material-recovery.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# get data
filepath = os.path.join(current_file_directory, '../data/literature/literature_review_material_recovery.xlsx')
df = pd.read_excel(filepath)

# ['aluminium', 'cement', 'chem', 'copper', 'glass', 'lime', 'other', 'paper', 'steel', 'timber']

material_sub_alu = ["cast-aluminium","wrought-aluminium"]
material_sub_steel = ["cast-iron","iron","steel","galvanized-steel","stainless-steel"]
material_sub_pla = ["plastics-ABS", "plastics-PP", "plastics-PA", "plastics-PBT", "plastics-PE",
                    "plastics-PMMA", "plastics-POM", "plastics-EPMD", "plastics-EPS", "plastics-PS",
                    "plastics-PU", "plastics-PUR", "plastics-PET", "plastics-PVC", 
                    "plastics-carbon-fiber-reinforced", "plastics-glass-fiber-reinforced",
                    "plastics-mixture","plastics-EPDM","plastics-other"]
material_current = ['aluminium', 'ammonia', 'concrete-and-inert', 'plastics-total', 'copper', 'glass', 
                    'lime', 'paper', 'iron_&_steel', 'wood']
material_current_correct_name = ['aluminium', 'ammonia', 'cement', 'chem', 'copper', 'glass', 
                                  'lime', 'paper', 'steel', 'timber']

df.columns

# ELV

# ['cars-EV', 'cars-FCV', 'cars-ICE', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']

techs = ['ELV_shredding-and-dismantling_recycling-best','ELV_shredding-and-dismantling_recovery-network-lowest',
         'ELV_shredding-and-dismantling_recovery-network-highest','ELV_dismantling-mechanical-separation-and-recycling_recycling-best',
         'ELV_dismantling-mechanical-separation-and-recycling_recovery-network-lowest','ELV_dismantling-mechanical-separation-and-recycling_recovery-network-highest']
df_elv = df.loc[:,["material","material-sub"] + techs]

# keep alu aggregate
df_elv = df_elv.loc[~df_elv["material-sub"].isin(material_sub_alu),:]

# take average of steel sub
df_temp = df_elv.loc[df_elv["material-sub"].isin(material_sub_steel),:]
df_temp["material"] = "iron_&_steel"
df_temp = pd.melt(df_temp, id_vars = ["material","material-sub"], var_name='tech')
df_temp = df_temp.groupby(["material","tech"], as_index=False)['value'].agg(np.mean)
df_temp["material-sub"] = np.nan
df_temp = df_temp.pivot(index=["material","material-sub"], columns="tech", values='value').reset_index()
df_elv = df_elv.loc[~df_elv["material"].isin(["iron_&_steel"]),:]
for i in material_sub_steel:
    df_elv = df_elv.loc[df_elv["material-sub"] != i,:]
df_elv = pd.concat([df_elv, df_temp])

# keep plastic average
for i in material_sub_pla:
    df_elv = df_elv.loc[df_elv["material-sub"] != i,:]

# make average across techs
df_elv.drop(columns="material-sub",inplace=True)
df_elv = pd.melt(df_elv, id_vars = ["material"], var_name='tech')
df_elv = df_elv.groupby(["material"], as_index=False)['value'].agg(np.mean)
df_elv.sort_values(["material"], inplace=True)

# keep materials present in calculator (and make mean for others)
df_temp = df_elv.loc[df_elv["material"].isin(material_current),:]
df_temp1 = df_elv.loc[~df_elv["material"].isin(material_current),:]
df_temp1["material"] = "other"
df_temp1 = df_temp1.groupby(["material"], as_index=False)['value'].agg(np.mean)
df_elv = pd.concat([df_temp,df_temp1])
for old, new in zip(material_current, material_current_correct_name):
    df_elv.loc[df_elv["material"] == old,"material"] = new

# create dm
countries = ['Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark',
             'EU27','Estonia','Finland','France','Germany','Greece','Hungary','Ireland','Italy',
             'Latvia','Lithuania','Luxembourg','Malta','Netherlands','Poland','Portugal',
             'Romania','Slovakia','Slovenia','Spain','Sweden','United Kingdom']
years = list(range(1990,2023+1,1))
years = years + list(range(2025, 2050+1, 5))
variabs = list(df_elv["material"])
units = list(np.repeat("%", len(variabs)))
units_dict = dict()
for i in range(0, len(variabs)):
    units_dict[variabs[i]] = units[i]
index_dict = dict()
for i in range(0, len(countries)):
    index_dict[countries[i]] = i
for i in range(0, len(years)):
    index_dict[years[i]] = i
for i in range(0, len(variabs)):
    index_dict[variabs[i]] = i

dm = DataMatrix()
dm.col_labels = {"Country" : countries, "Years" : years, "Variables" : variabs}
dm.units = units_dict
dm.idx = index_dict
dm.array = np.zeros((len(countries), len(years), len(variabs)))
idx = dm.idx
for i in variabs:
    dm.array[:,:,idx[i]] = df_elv.loc[df_elv["material"]==i,"value"]

# make nan for other than EU27 for fts
countries_oth = np.array(countries)[[i not in "EU27" for i in countries]].tolist()
idx = dm.idx
years = list(range(2025, 2050+1, 5))
for c in countries_oth:
    for y in years:
        for v in variabs:
            dm.array[idx[c],idx[y],idx[v]] = np.nan
df = dm.write_df()

# rename
for i in variabs:
    dm.rename_col(i, "waste-material-recovery_elv_" + i, "Variables")
dm.deepen()

# divide everything by 100 (as in industry % is between 0 and 1)
dm.array = dm.array/100

# save
years_ots = list(range(1990,2023+1))
years_fts = list(range(2025,2055,5))
dm_ots = dm.filter({"Years" : years_ots})
dm_fts = dm.filter({"Years" : years_fts})
DM_fts = {1: dm_fts, 2: dm_fts, 3: dm_fts, 4: dm_fts} # for now we set all levels to be the same
DM = {"ots" : dm_ots,
      "fts" : DM_fts}
f = os.path.join(current_file_directory, '../data/datamatrix/lever_material-recovery.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM, handle, protocol=pickle.HIGHEST_PROTOCOL)

# df = dm.write_df()
# df_temp = pd.melt(df, id_vars = ['Country', 'Years'], var_name='variable')
# df_temp = df_temp.loc[df_temp["Country"].isin(["Austria","France"]),:]
# df_temp = df_temp.loc[df_temp["Years"]==1990,:]
# name = "temp.xlsx"
# df_temp.to_excel("~/Desktop/" + name)



