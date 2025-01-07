
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
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_product-net-import.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

#########################################
##### GET CLEAN DATAFRAME WITH DATA #####
#########################################

# get data
# df = eurostat.get_data_df("ds-056120")
filepath = os.path.join(current_file_directory, '../data/eurostat/ds-056120.csv')
# df.to_csv(filepath, index = False)
df = pd.read_csv(filepath)

# NOTE: as ds-056120 is on sold production, then we assume sold production = demand
# import and export should be always on "sold", as a country exports what's demanded
# and it imports what it demands.

# explore data
df.columns
product_code = "29102100"
variabs = ["PRODVAL","PRODQNT","EXPVAL","EXPQNT","IMPVAL","IMPQNT"]
df_sub = df.loc[df["prccode"].isin([product_code]),:]
df_sub = df_sub.loc[df_sub["indicators\TIME_PERIOD"].isin(variabs),:]
len(df_sub["decl"].unique())
df_sub = df_sub.loc[df_sub["decl"].isin([4,2027])] # get germnay and EU27_2020
# it seems values are generally there for all variables
# I will do: 
# product-net-import[%] = (IMPQNT - EXPQNT) / PRODQNT
# For now I will do the adjustments (nan filling, jumps, predictions) on the variables 
# EXPQNT, IMPQNT and PRODQNT, and then I will make the variable product-net-import[%] at the end.
# The alternative would be to make product-net-import[%] from the
# beginning, and do all the adjustments on that variable. TBC.

# get "PRODQNT", "EXPQNT", "IMPQNT", "QNTUNIT"
variabs = ["PRODQNT", "EXPQNT", "IMPQNT", "QNTUNIT"]
df = df.loc[df["indicators\TIME_PERIOD"].isin(variabs),:]

# keep only things in mapping for industry
filepath = os.path.join(current_file_directory, '../data/eurostat/PRODCOM2024_PRODCOM2023_Table.csv')
df_map = pd.read_csv(filepath)
df_map = df_map.loc[:,['PRODCOM2024_KEY','calc_industry_product']]
df_map = df_map.rename(columns= {"PRODCOM2024_KEY" : "prccode"})
df_map = df_map.dropna()
df = pd.merge(df, df_map, how="left", on=["prccode"])
df_sub = df.loc[~df["calc_industry_product"].isnull(),:]
df_sub = df_sub.loc[~df_sub["calc_industry_product"].isin(["battery"]),:] # drop battery for now

# fix countries
# sources:
# DECL drop down menu: https://ec.europa.eu/eurostat/databrowser/view/DS-056120/legacyMultiFreq/table?lang=en  
# https://ec.europa.eu/eurostat/documents/120432/0/Quick+guide+on+accessing+PRODCOM+data+DS-056120.pdf/484b8bbf-e371-49f3-6fa7-6a2514ebfcc9?t=1696602916356
decl_mapping = {1: "France", 3: "Netherlands", 4: "Germany", 5: "Italy", 6: "United Kingdom",
                7: "Ireland", 8: "Denmark", 9: "Greece", 10: "Portugal", 11: "Spain",
                17: "Belgium", 18: "Luxembourg", 24: "Iceland", 28: "Norway", 30: "Sweden",
                32: "Finland", 38: "Austria", 46: "Malta", 52: "Turkiye", 53: "Estonia",
                54: "Latvia", 55: "Lithuania", 60: "Poland", 61: "Czech Republic", 
                63: "Slovakia", 64: "Hungary", 66: "Romania", 68: "Bulgaria",
                70: "Albania", 91: "Slovenia", 92: "Croatia", 93: "Bosnia and Herzegovina",
                96: "North Macedonia", 97: "Montenegro", 98: "Serbia", 600: "Cyprus",
                1110: "EU15", 1111: "EU25", 1112: "EU27_2007", 2027: "EU27_2020", 2028: "EU28"}
df_sub["country"] = np.nan
for key in decl_mapping.keys():
    df_sub.loc[df_sub["decl"] == key,"country"] = decl_mapping[key]
    
# make long format
df_sub.rename(columns={"indicators\TIME_PERIOD":"variable"}, inplace = True)
df_sub_unit = df_sub.loc[df_sub["variable"].isin(["QNTUNIT"]),:]
df_sub = df_sub.loc[~df_sub["variable"].isin(["QNTUNIT"]),:]
drops = ['freq', 'decl']
df_sub.drop(drops,axis=1, inplace = True)
indexes = ['prccode', 'variable', 'country', 'calc_industry_product']
df_sub = pd.melt(df_sub, id_vars = indexes, var_name='year')

# make unit as column
drops = ['freq', 'decl']
df_sub_unit.drop(drops,axis=1, inplace = True)
indexes = ['prccode', 'variable', 'country', 'calc_industry_product']
df_sub_unit = pd.melt(df_sub_unit, id_vars = indexes, var_name='year')
df_sub_unit.rename(columns={"value":"unit"}, inplace = True)
keep = ['prccode', 'country', 'calc_industry_product','year','unit']
indexes = ['prccode', 'country', 'calc_industry_product','year']
df_sub = pd.merge(df_sub, df_sub_unit.loc[:,keep], how="left", on=indexes)

# fix unit
df_sub["unit"].unique()
old_unit = [np.nan, 'kg ', 'm2 ', 'kg N ', 'kg P2O5 ', 'kg K2O ', 'kg effect ', 'p/st ', 'ct/l ', 'CGT ', 'NA ']
new_unit = [np.nan, 'kg', 'm2', 'kg N', 'kg P2O5', 'kg K2O', 'kg effect', 'p/st', 'ct/l', 'CGT', 'NA']
for i in range(0, len(old_unit)):
    df_sub.loc[df_sub["unit"] == old_unit[i],"unit"] = new_unit[i]
df_sub["unit"].unique()

# fix value
df_sub["value"] = [float(i) for i in df_sub["value"]]

# order and sort
indexes = ['country', 'variable', 'prccode', 'calc_industry_product', 'year']
variabs = ['value', 'unit']
df_sub = df_sub.loc[:,indexes + variabs]
df_sub = df_sub.sort_values(by=indexes)

# check
df_check = df_sub.loc[df_sub["prccode"] == "29102100",:]
df_check = df_check.loc[df_sub["country"].isin(["Germany","EU27_2020"])]
# ok

# aggregate by calc_industry_product
df_sub = df_sub.reset_index()
indexes = ['country', 'variable', 'calc_industry_product', 'year','unit']
df_sub = df_sub.groupby(indexes, as_index=False)['value'].agg(sum)

# keep right units
df_sub["calc_industry_product"].unique()
df_sub["unit"].unique()
df_sub.loc[df_sub["calc_industry_product"].isin(["glass-pack"]),"unit"].unique()
df_sub.loc[df_sub["calc_industry_product"].isin(["aluminium-pack"]),"unit"].unique()
["aluminium-pack","glass-pack", "paper-pack", "paper-print", "paper-san", "plastic-pack"]
product_check = ["paper-pack"]
df_check = df_sub.loc[df_sub["calc_industry_product"].isin(product_check),:]
df_check = df_check.loc[df_check["country"].isin(["EU27_2020"]),:]
units_dict = {'aluminium-pack' : ['p/st'], 'cars-EV' : ['p/st'], 'cars-ICE' : ['p/st'],
              'computer' : ['p/st'], 'dishwasher' : ['p/st'],
              'fertilizer' : ['kg', 'kg K2O', 'kg N', 'kg P2O5', 'kg effect'],
              'freezer' : ['p/st'], 'fridge' : ['p/st'], 'glass-pack' : ['p/st'],
              'paper-pack' : ['kg'], 'paper-print' : ['kg'], 'paper-san' : ['kg'],
              'phone' : ['p/st'], 'planes' : ['p/st'], 'plastic-pack' : ['p/st'],
              'ships' : ['p/st'], 'trains' : ['p/st'], 'trucks-EV' : ['p/st'],
              'trucks-ICE' : ['p/st'], 'tv' : ['p/st'], 'wmachine' : ['p/st']}
df_sub = pd.concat([df_sub.loc[(df_sub["calc_industry_product"] == key) & \
                               (df_sub["unit"].isin(units_dict[key])),:] \
                    for key in units_dict.keys()])
df_sub.loc[df_sub["unit"] == 'p/st',"unit"] = "num"

# groupby for fertilizer
df_fert = df_sub.loc[df_sub["calc_industry_product"] == "fertilizer",:]
indexes = ['country', 'variable', 'calc_industry_product', 'year']
df_fert = df_fert.groupby(indexes, as_index=False)['value'].agg(sum)
df_fert["unit"] = "kg"
df_sub = df_sub.loc[~df_sub["calc_industry_product"].isin(["fertilizer"]),:]
df_sub = pd.concat([df_sub, df_fert])

# fix countries
countries_calc = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 
                  'Czech Republic', 'Denmark', 'EU27', 'Estonia', 'Finland', 
                  'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 
                  'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 
                  'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 
                  'Slovenia', 'Spain', 'Sweden', 'United Kingdom']
df_sub["country"].unique()
drops = ['Albania','Bosnia and Herzegovina','EU15','EU28','Iceland','Montenegro',
         'North Macedonia', 'Norway', 'Serbia', 'Turkiye']
df_sub = df_sub.loc[~df_sub["country"].isin(drops),:]
countries = df_sub["country"].unique()

# I assume that trade extra eu is from the data EU27_2020
df_sub = df_sub.loc[~df_sub["country"].isin(['EU27_2007']),:]
df_sub.loc[df_sub["country"] == 'EU27_2020',"country"] = "EU27"
df_temp = df_sub.loc[df_sub["country"] == "EU27",:]
countries = df_sub["country"].unique()

##################################
##### CONVERT TO DATA MATRIX #####
##################################

# make df ready for conversion to dm
df_sub.loc[df_sub["variable"] == "IMPQNT","variable"] = "product-import"
df_sub.loc[df_sub["variable"] == "EXPQNT","variable"] = "product-export"
df_sub.loc[df_sub["variable"] == "PRODQNT","variable"] = "product-demand"
df_sub["variable"] = df_sub["variable"] + "_" + df_sub["calc_industry_product"] + "[" + df_sub["unit"] + "]"
df_sub = df_sub.rename(columns={"country": "Country", "year" : "Years"})
drops = ["calc_industry_product","unit"]
df_sub.drop(drops,axis=1, inplace = True)
countries = df_sub["Country"].unique()
years = df_sub["Years"].unique()
variables = df_sub["variable"].unique()
panel_countries = np.repeat(countries, len(variables) * len(years))
panel_years = np.tile(np.tile(years, len(variables)), len(countries))
panel_variables = np.tile(np.repeat(variables, len(years)), len(countries))
df_temp = pd.DataFrame({"Country" : panel_countries, 
                        "Years" : panel_years, 
                        "variable" : panel_variables})
df_sub = pd.merge(df_temp, df_sub, how="left", on=["Country","Years","variable"])

# put nan where is 0
df_sub.loc[df_sub["value"] == 0,"value"] = np.nan

# split in dms
df_sub["selection"] = [i.split("_")[1].split("[")[0] for i in df_sub["variable"]]

# dm_bld_domapp
df_temp = df_sub.loc[df_sub["selection"].isin(['computer', 'dishwasher', 'freezer', 'fridge',
                                               'phone', 'tv', 'wmachine']),["Country","Years","variable","value"]]
df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
dm_bld_domapp = DataMatrix.create_from_df(df_temp, 1)

# dm_tra_veh
df_temp = df_sub.loc[df_sub["selection"].isin(['cars-EV', 'cars-ICE','planes', 'ships', 'trains',
                                               'trucks-EV', 'trucks-ICE']),["Country","Years","variable","value"]]
df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
dm_tra_veh = DataMatrix.create_from_df(df_temp, 1)

# dm_lfs
df_temp = df_sub.loc[df_sub["selection"].isin(['paper-pack', 'paper-print', 'paper-san']),["Country","Years","variable","value"]]
df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
dm_lfs_kg = DataMatrix.create_from_df(df_temp, 1)
df_temp = df_sub.loc[df_sub["selection"].isin(['aluminium-pack', 'glass-pack', 'plastic-pack']),
                     ["Country","Years","variable","value"]]
df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
dm_lfs_unit = DataMatrix.create_from_df(df_temp, 1)

# put together
DM_trade = {"domapp" : dm_bld_domapp,
            "tra-veh" : dm_tra_veh,
            "lfs_paper" : dm_lfs_kg,
            "lfs_other" : dm_lfs_unit}

# # plot
# DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["tra-veh"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["lfs_kg"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["lfs_unit"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # all data starts in 2003
# # phone data starts in 2022, i will put a zero in 2003 and then compute the linear trend for missing 

###################
##### FIX OTS #####
###################

# Set years range
years_setting = [1990, 2023, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(range(startyear, baseyear+1, 1))
years_fts = list(range(baseyear+2, lastyear+1, step_fts))
years_all = years_ots + years_fts

# put zero for phone and planes in 2003
idx = DM_trade["domapp"].idx
DM_trade["domapp"].array[:,idx[2003],:,idx["phone"]] = 0
idx = DM_trade["tra-veh"].idx
DM_trade["tra-veh"].array[:,idx[2003],:,idx["planes"]] = 0

# fill in missing values with linear fitting
for key in DM_trade.keys():
    years_fitting = DM_trade[key].col_labels["Years"]
    DM_trade[key] = linear_fitting(DM_trade[key], years_fitting, min_t0=0)
    DM_trade[key].array = np.round(DM_trade[key].array,0)

# # plot
# DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["tra-veh"].filter({"Country" : ["EU27"], "Categories1" : ["trucks-ICE"]}).datamatrix_plot()
# DM_trade["lfs_kg"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["lfs_unit"].filter({"Country" : ["EU27"]}).datamatrix_plot()

# fix jumps
for key in DM_trade.keys(): DM_trade[key] = fix_jumps_in_dm(DM_trade[key])

# # plot
# DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["tra-veh"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# DM_trade["lfs"].filter({"Country" : ["EU27"]}).datamatrix_plot()

# add missing years ots
for key in DM_trade.keys():
    years_missing = list(set(years_ots) - set(DM_trade[key].col_labels['Years']))
    DM_trade[key].add(np.nan, col_label=years_missing, dummy=True, dim='Years')
    DM_trade[key].sort('Years')

# fill in missing years ots with linear fitting
for key in DM_trade.keys():
    DM_trade[key] = linear_fitting(DM_trade[key], years_missing, min_t0=0)
    DM_trade[key].array = np.round(DM_trade[key].array,0)

# # check
# df_check = DM_trade["domapp"].write_df()
# DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()

#############################################
##### GENERATE VARIABLES WE DO NOT HAVE #####
#############################################

# note: for the variables that we do not have, in general import and export will be set
# to zero, and demand will be set to nan

# generate cars-FCV and trucks-FCV
# we assume that imports remain zero throughout
idx = DM_trade["tra-veh"].idx
DM_trade["tra-veh"].add(0, "Categories1", "cars-FCV", unit="num", dummy=True)
DM_trade["tra-veh"].array[:,:,idx["product-demand"],idx["cars-FCV"]] = np.nan
DM_trade["tra-veh"].add(0, "Categories1", "trucks-FCV", unit="num", dummy=True)
DM_trade["tra-veh"].array[:,:,idx["product-demand"],idx["trucks-FCV"]] = np.nan
DM_trade["tra-veh"].sort("Categories1")

# generate new-dhg-pipe, rail, road, trolley-cables, floor-area-new-non-residential, 
# floor-area-new-residential, floor-area-reno-non-residential, floor-area-reno-residential
# we assume imports of these are all zero
DM_trade["domapp"].add(0, "Categories1", "new-dhg-pipe", unit="num", dummy=True)
dm_bld_pipe = DM_trade["domapp"].filter({"Categories1" : ["new-dhg-pipe"]})
dm_bld_pipe.units['product-export'] = "km"
dm_bld_pipe.units['product-import'] = "km"
dm_bld_pipe.units['product-demand'] = "km"
idx = dm_bld_pipe.idx
dm_bld_pipe.array[:,:,idx["product-demand"],idx["new-dhg-pipe"]] = np.nan
DM_trade["domapp"].drop("Categories1", ["new-dhg-pipe"])
DM_trade["pipe"] = dm_bld_pipe

DM_trade["tra-veh"].add(0, "Categories1", "rail", unit="num", dummy=True)
DM_trade["tra-veh"].add(0, "Categories1", "road", unit="num", dummy=True)
DM_trade["tra-veh"].add(0, "Categories1", "trolley-cables", unit="num", dummy=True)
dm_tra_infra = DM_trade["tra-veh"].filter({"Categories1" : ["rail","road","trolley-cables"]})
dm_tra_infra.units['product-export'] = "km"
dm_tra_infra.units['product-import'] = "km"
dm_tra_infra.units['product-demand'] = "km"
idx = dm_tra_infra.idx
dm_tra_infra.array[:,:,idx["product-demand"],:] = np.nan
DM_trade["tra-veh"].drop("Categories1", ["rail","road","trolley-cables"])
dm_tra_infra.sort("Categories1")
DM_trade["tra-infra"] = dm_tra_infra

DM_trade["domapp"].add(0, "Categories1", "floor-area-new-non-residential", unit="m2", dummy=True)
DM_trade["domapp"].add(0, "Categories1", "floor-area-new-residential", unit="m2", dummy=True)
DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-non-residential", unit="m2", dummy=True)
DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-residential", unit="m2", dummy=True)
dm_bld_floor = DM_trade["domapp"].filter({"Categories1" : ["floor-area-new-non-residential","floor-area-new-residential", 
                                                           "floor-area-reno-non-residential", "floor-area-reno-residential"]})
dm_bld_floor.units['product-export'] = "m2"
dm_bld_floor.units['product-import'] = "m2"
dm_bld_floor.units['product-demand'] = "m2"
idx = dm_bld_floor.idx
dm_bld_floor.array[:,:,idx["product-demand"],:] = np.nan
DM_trade["domapp"].drop("Categories1", ["floor-area-new-non-residential","floor-area-new-residential", 
                                        "floor-area-reno-non-residential", "floor-area-reno-residential"])
dm_bld_floor.sort("Categories1")
DM_trade["bld-floor"] = dm_bld_floor

# dryer
# I assume dryers are 1% of exports and imports (check excel file in WITS folder called "percentage_dryers_export_EU")
idx = DM_trade["domapp"].idx
arr_temp = DM_trade["domapp"].array[...,idx["wmachine"]] * 0.01
DM_trade["domapp"].add(arr_temp, col_label="dryer", dim='Categories1', unit = "num")
DM_trade["domapp"].sort("Categories1")

# ships
# I assume that imports and exports of ships are zero (rather than missing)
idx = DM_trade["tra-veh"].idx
DM_trade["tra-veh"].array[:,:,idx["product-export"],idx["ships"]] = 0
DM_trade["tra-veh"].array[:,:,idx["product-import"],idx["ships"]] = 0

# check
# ['aluminium-pack', 'glass-pack', 'paper-pack', 'paper-print', 'paper-san', 'plastic-pack']
# ['cars-EV', 'cars-FCV', 'cars-ICE', 'planes', 'ships', 'trains', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']
# ['computer', 'dishwasher', 'dryer', 'freezer', 'fridge', 'phone', 'tv', 'wmachine']
# product = 'ships'
# DM_trade["tra-veh"].datamatrix_plot(selected_cols={"Country" : ["EU27"], 
#                                                   "Variables" : ["product-export","product-import"],
#                                                   "Categories1" : [product]})
# DM_trade["tra-veh"].datamatrix_plot(selected_cols={"Country" : ["EU27"], 
#                                                   "Variables" : ["product-demand"],
#                                                   "Categories1" : [product]})


####################
##### MAKE FTS #####
####################

# make function to fill in missing years fts for EU27 with linear fitting
def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
             min_t0=0, min_tb=0, years_fts = years_fts): # I put minimum to 1 so it does not go to zero
    dm = dm.copy()
    idx = dm.idx
    based_on_yars = list(range(year_start, year_end + 1, 1))
    dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
                             years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
    idx_temp = dm_temp.idx
    if dim == "Variables":
        dm.array[idx[country],:,idx[variable],...] = \
            np.round(dm_temp.array[idx_temp[country],:,idx_temp[variable],...],0)
    if dim == "Categories1":
        dm.array[idx[country],:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,idx_temp[variable]], 0)
    if dim == "Categories2":
        dm.array[idx[country],:,:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]], 0)
    if dim == "Categories3":
        dm.array[idx[country],:,:,:,:,idx[variable]] = \
            np.round(dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]], 0)
    
    return dm

# add missing years fts
for key in DM_trade.keys():
    DM_trade[key].add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# set default time window for linear trend
# assumption: best is taking longer trend possible to make predictions to 2050 (even if earlier data is generated)
baseyear_start = 1990
baseyear_end = 2019

# domestic appliances
DM_trade["lfs_other"] = make_fts(DM_trade["lfs_other"], "aluminium-pack", baseyear_start, baseyear_end)
DM_trade["lfs_other"] = make_fts(DM_trade["lfs_other"], "glass-pack", 2012, baseyear_end) # here upwatd trend in import and demand starts in 2012
DM_trade["lfs_other"] = make_fts(DM_trade["lfs_other"], "plastic-pack", baseyear_start, baseyear_end)
DM_trade["lfs_paper"] = make_fts(DM_trade["lfs_paper"], "paper-pack", baseyear_start, baseyear_end)
DM_trade["lfs_paper"] = make_fts(DM_trade["lfs_paper"], "paper-print", baseyear_start, baseyear_end)
DM_trade["lfs_paper"] = make_fts(DM_trade["lfs_paper"], "paper-san", baseyear_start, baseyear_end)
# product = "paper-san"
# (make_fts(DM_trade["lfs_paper"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-import","product-export"],
#                                 "Categories1" : [product]}))
# (make_fts(DM_trade["lfs_paper"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-demand"],
#                                 "Categories1" : [product]}))

# transport vehicles
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-EV", 2021, 2022) # assuming they will have upward trend (these dates allow max upward trend with technique of linear trend)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-FCV", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-ICE", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "planes", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "ships", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trains", 2012, baseyear_end) # there is upward trend from 2012
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-EV", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-FCV", baseyear_start, baseyear_end)
DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-ICE", baseyear_start, baseyear_end)
# product = "ships"
# (make_fts(DM_trade["tra-veh"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-import","product-export"],
#                                 "Categories1" : [product]}))
# (make_fts(DM_trade["tra-veh"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-demand"],
#                                 "Categories1" : [product]}))

# transport infra
DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "rail", baseyear_start, baseyear_end)
DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "road", baseyear_start, baseyear_end)
DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "trolley-cables", baseyear_start, baseyear_end)

# buildings
DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-new-non-residential", baseyear_start, baseyear_end)
DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-new-residential", baseyear_start, baseyear_end)
DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-reno-non-residential", baseyear_start, baseyear_end)
DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-reno-residential", baseyear_start, baseyear_end)

# domestic appliances
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "computer", baseyear_start, baseyear_end)
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "dishwasher", baseyear_start, baseyear_end)
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "dryer", 2000, 2007) # here I assume there is some problem with the data after 2008
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "freezer", baseyear_start, baseyear_end)
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "fridge", baseyear_start, baseyear_end)
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "phone", baseyear_start, baseyear_end)
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "tv", 2012, baseyear_end) # downward trend in demand since 2012
DM_trade["domapp"] = make_fts(DM_trade["domapp"], "wmachine", 2000, 2007) # here I assume there is some problem with the data after 2008
# product = "tv"
# (make_fts(DM_trade["domapp"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-import","product-export"],
#                                 "Categories1" : [product]}))
# (make_fts(DM_trade["domapp"], product, baseyear_start, baseyear_end).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-demand"],
#                                 "Categories1" : [product]}))

# pipes
DM_trade["pipe"] = make_fts(DM_trade["pipe"], "new-dhg-pipe", baseyear_start, baseyear_end)

###################################
##### MAKE PRODUCT NET IMPORT #####
###################################

# product-net-import[%] = (product-import - product-export)/product-demand
DM_trade_net_share = {}
keys = ['domapp', 'tra-veh', 'lfs_paper', 'lfs_other', 'pipe', 'tra-infra', 'bld-floor']
for key in keys:
    dm_temp = DM_trade[key].copy() 
    
    # # when demand is zero put it equal to 1 unit (so then the division does not give infinite)
    # dm_temp1 = dm_temp.filter({"Variables" : ["product-demand"]})
    # idx1 = dm_temp1.idx
    # dm_temp1.array[dm_temp1.array == 0] = 1
    
    # make product-net-import[%] = (product-import - product-export)/product-demand
    idx = dm_temp.idx
    arr_temp = dm_temp.array
    arr_net = (arr_temp[:,:,idx["product-import"],:] - arr_temp[:,:,idx["product-export"],:]) / arr_temp[:,:,idx["product-demand"],:]
    
    # when both import and export are zero, assign a zero
    arr_net[(arr_temp[:,:,idx["product-import"],:] == 0) & (arr_temp[:,:,idx["product-export"],:] == 0)] = 0
    dm_temp.add(arr_net[:,:,np.newaxis,:], "Variables", "product-net-import", unit="%")
    
    # drop
    dm_temp.drop("Variables", ["product-import","product-export","product-demand"])
    
    # store
    DM_trade_net_share[key] = dm_temp
dm_trade_netshare = DM_trade_net_share["domapp"]
keys = ['tra-veh', 'lfs_paper', 'lfs_other', 'pipe', 'tra-infra', 'bld-floor']
for key in keys:
    dm_trade_netshare.append(DM_trade_net_share[key], "Categories1")
dm_trade_netshare.sort("Categories1")

# fill in missing values for product-net-import (coming from dividing by zero)
idx = dm_trade_netshare.idx
dm_trade_netshare.array[dm_trade_netshare.array == np.inf] = np.nan
years_fitting = dm_trade_netshare.col_labels["Years"]
dm_trade_netshare = linear_fitting(dm_trade_netshare, years_fitting)

# for the variables that we generated as all zero, re-put zeroes
variabs = ["cars-FCV", "trucks-FCV", "aluminium-pack", "new-dhg-pipe", "rail",
            "road", "trolley-cables", "floor-area-new-non-residential", 
            "floor-area-new-residential", "floor-area-reno-non-residential", 
            "floor-area-reno-residential", "ships"]
idx = dm_trade_netshare.idx
for v in variabs:
    dm_trade_netshare.array[:,:,:,idx[v]] = 0
    
# fix jumps in product-net-import
dm_trade_netshare = fix_jumps_in_dm(dm_trade_netshare)

# check
# ['aluminium-pack', 'glass-pack', 'paper-pack', 'paper-print', 'paper-san', 'plastic-pack']
# ['cars-EV', 'cars-FCV', 'cars-ICE', 'planes', 'ships', 'trains', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']
# ['computer', 'dishwasher', 'dryer', 'freezer', 'fridge', 'phone', 'tv', 'wmachine']
# product = 'ships'
# DM_trade["tra-veh"].datamatrix_plot(selected_cols={"Country" : ["EU27"], 
#                                                   "Variables" : ["product-export","product-import"],
#                                                   "Categories1" : [product]})
# DM_trade["tra-veh"].datamatrix_plot(selected_cols={"Country" : ["EU27"], 
#                                                   "Variables" : ["product-demand"],
#                                                   "Categories1" : [product]})
# dm_trade_netshare.datamatrix_plot(selected_cols={"Country" : ["EU27"], 
#                                                   "Variables" : ["product-net-import"],
#                                                   "Categories1" : [product]})
# idx = DM_trade["domapp"].idx
# ((DM_trade["domapp"].array[idx["EU27"],idx[1990],idx["product-import"],idx["phone"]]-
#   DM_trade["domapp"].array[idx["EU27"],idx[1990],idx["product-export"],idx["phone"]])/
#   DM_trade["domapp"].array[idx["EU27"],idx[1990],idx["product-demand"],idx["phone"]])

################
##### SAVE #####
################

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_product-net-import.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm_trade_netshare, handle, protocol=pickle.HIGHEST_PROTOCOL)













# #########################################################################################
# ######################## VERSION WITH PRODUCT NET IMPORT AS CORE ########################
# #########################################################################################

# # note: in this version, product-net-import is computed at the beginning and fts are made
# # directly on it

# ###################################
# ##### MAKE PRODUCT NET IMPORT #####
# ###################################

# # product-net-import[%] = (product-import - product-export)/product-demand
# DM_trade_net_share = {}
# keys = ["lfs", "tra-veh", "domapp"]
# for key in keys:
#     dm_temp = DM_trade[key].copy() 
    
#     # # when demand is zero put it equal to 1 unit (so then the division does not give infinite)
#     # dm_temp1 = dm_temp.filter({"Variables" : ["product-demand"]})
#     # idx1 = dm_temp1.idx
#     # dm_temp1.array[dm_temp1.array == 0] = 1
    
#     # make product-net-import[%] = (product-import - product-export)/product-demand
#     idx = dm_temp.idx
#     arr_temp = (dm_temp.array[:,:,idx["product-import"],:] -\
#                 dm_temp.array[:,:,idx["product-export"],:])/\
#         dm_temp.array[:,:,idx["product-demand"],:]
#     dm_temp.add(arr_temp, "Variables", "product-net-import", unit="%")
#     dm_temp.drop("Variables", ["product-import","product-export","product-demand"])
#     DM_trade_net_share[key] = dm_temp
# dm_trade_netshare = DM_trade_net_share["lfs"]
# keys = ["tra-veh", "domapp"]
# for key in keys:
#     dm_trade_netshare.append(DM_trade_net_share[key], "Categories1")
# dm_trade_netshare.sort("Categories1")

# # fill in missing values for product-net-import
# idx = dm_trade_netshare.idx
# dm_trade_netshare.array[dm_trade_netshare.array == np.inf] = np.nan
# years_fitting = dm_trade_netshare.col_labels["Years"]
# dm_trade_netshare = linear_fitting(dm_trade_netshare, years_fitting)

# # fix jumps in product-net-import
# dm_trade_netshare = fix_jumps_in_dm(dm_trade_netshare)

# #############################################
# ##### GENERATE VARIABLES WE DO NOT HAVE #####
# #############################################

# # generate cars-FCV and trucks-FCV
# # we assume that imports remain zero throughout
# DM_trade["tra-veh"].add(0, "Categories1", "cars-FCV", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "trucks-FCV", unit="num", dummy=True)
# DM_trade["tra-veh"].sort("Categories1")
# dm_trade_netshare.add(0, "Categories1", "cars-FCV", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "trucks-FCV", unit="%", dummy=True)
# dm_trade_netshare.sort("Categories1")

# # generate aluminium-pack
# # for the moment we assume that imports remain zero throughout
# DM_trade["lfs"].add(0, "Categories1", "aluminium-pack", unit="kg", dummy=True)
# DM_trade["lfs"].sort("Categories1")
# dm_trade_netshare.add(0, "Categories1", "aluminium-pack", unit="%", dummy=True)
# dm_trade_netshare.sort("Categories1")

# # generate new-dhg-pipe, rail, road, trolley-cables, floor-area-new-non-residential, 
# # floor-area-new-residential, floor-area-reno-non-residential, floor-area-reno-residential
# # we assume imports of these are all zero
# DM_trade["domapp"].add(0, "Categories1", "new-dhg-pipe", unit="num", dummy=True)
# dm_bld_pipe = DM_trade["domapp"].filter({"Categories1" : ["new-dhg-pipe"]})
# dm_bld_pipe.units['product-export'] = "km"
# dm_bld_pipe.units['product-import'] = "km"
# dm_bld_pipe.units['product-demand'] = "km"
# DM_trade["domapp"].drop("Categories1", ["new-dhg-pipe"])
# DM_trade["pipe"] = dm_bld_pipe
# dm_trade_netshare.add(0, "Categories1", "new-dhg-pipe", unit="%", dummy=True)
# dm_trade_netshare.sort("Categories1")

# DM_trade["tra-veh"].add(0, "Categories1", "rail", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "road", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "trolley-cables", unit="num", dummy=True)
# dm_tra_infra = DM_trade["tra-veh"].filter({"Categories1" : ["rail","road","trolley-cables"]})
# dm_tra_infra.units['product-export'] = "km"
# dm_tra_infra.units['product-import'] = "km"
# dm_tra_infra.units['product-demand'] = "km"
# DM_trade["tra-veh"].drop("Categories1", ["rail","road","trolley-cables"])
# dm_tra_infra.sort("Categories1")
# DM_trade["tra-infra"] = dm_tra_infra
# dm_trade_netshare.add(0, "Categories1", "rail", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "road", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "trolley-cables", unit="%", dummy=True)
# dm_trade_netshare.sort("Categories1")

# DM_trade["domapp"].add(0, "Categories1", "floor-area-new-non-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-new-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-non-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-residential", unit="m2", dummy=True)
# dm_bld_floor = DM_trade["domapp"].filter({"Categories1" : ["floor-area-new-non-residential","floor-area-new-residential", 
#                                                            "floor-area-reno-non-residential", "floor-area-reno-residential"]})
# dm_bld_floor.units['product-export'] = "m2"
# dm_bld_floor.units['product-import'] = "m2"
# dm_bld_floor.units['product-demand'] = "m2"
# DM_trade["domapp"].drop("Categories1", ["floor-area-new-non-residential","floor-area-new-residential", 
#                                         "floor-area-reno-non-residential", "floor-area-reno-residential"])
# dm_bld_floor.sort("Categories1")
# DM_trade["bld-floor"] = dm_bld_floor
# dm_trade_netshare.add(0, "Categories1", "floor-area-new-non-residential", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "floor-area-new-residential", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "floor-area-reno-non-residential", unit="%", dummy=True)
# dm_trade_netshare.add(0, "Categories1", "floor-area-reno-residential", unit="%", dummy=True)
# dm_trade_netshare.sort("Categories1")

# # dryer
# # I assume dryers are 1% of exports and imports (check excel file in WITS folder called "percentage_dryers_export_EU")
# idx = DM_trade["domapp"].idx
# arr_temp = DM_trade["domapp"].array[...,idx["wmachine"]] * 0.01
# DM_trade["domapp"].add(arr_temp, col_label="dryer", dim='Categories1', unit = "num")
# DM_trade["domapp"].sort("Categories1")
# idx = DM_trade["domapp"].idx
# arr_temp = (DM_trade["domapp"].array[:,:,idx["product-import"],idx["dryer"]]-\
#     DM_trade["domapp"].array[:,:,idx["product-export"],idx["dryer"]])/\
#     DM_trade["domapp"].array[:,:,idx["product-demand"],idx["dryer"]]
# dm_trade_netshare.add(arr_temp[:,:,np.newaxis,np.newaxis], "Categories1", "dryer", unit="%")
# dm_trade_netshare.sort("Categories1")

# # # # check
# # # ['aluminium-pack', 'glass-pack', 'paper-pack', 'paper-print', 'paper-san', 'plastic-pack']
# # # ['cars-EV', 'cars-FCV', 'cars-ICE', 'planes', 'ships', 'trains', 'trucks-EV', 'trucks-FCV', 'trucks-ICE']
# # # ['computer', 'dishwasher', 'dryer', 'freezer', 'fridge', 'phone', 'tv', 'wmachine']
# # product = 'wmachine'
# # DM_trade["domapp"].datamatrix_plot(selected_cols={"Country" : ["EU27"], 
# #                                                   "Variables" : ["product-export","product-import","product-demand"],
# #                                                   "Categories1" : [product]})
# # dm_trade_netshare.datamatrix_plot(selected_cols={"Country" : ["EU27"], 
# #                                                   "Variables" : ["product-net-import"],
# #                                                   "Categories1" : [product]})

# ###########################################
# ##### MAKE FTS FOR PRODUCT NET IMPORT #####
# ###########################################

# # NOTE: in case we will split imports and exports, we will do OTS and FTS on those, and
# # then compute product net import

# # make function to fill in missing years fts for EU27 with linear fitting
# def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
#              min_t0=None, min_tb=None, years_fts = years_fts):
#     dm = dm.copy()
#     idx = dm.idx
#     based_on_yars = list(range(year_start, year_end + 1, 1))
#     dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
#                              years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
#     idx_temp = dm_temp.idx
#     if dim == "Variables":
#         dm.array[idx[country],:,idx[variable],...] = \
#             dm_temp.array[idx_temp[country],:,idx_temp[variable],...]
#     if dim == "Categories1":
#         dm.array[idx[country],:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,idx_temp[variable]]
#     if dim == "Categories2":
#         dm.array[idx[country],:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]]
#     if dim == "Categories3":
#         dm.array[idx[country],:,:,:,:,idx[variable]] = \
#             dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]]
    
#     return dm

# # add missing years fts
# dm_trade_netshare.add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# # make fts
# baseyear_start = 2006 # I pick 2006 as in general it's after a dip in the data in 2005 (and data before 2002 is often generated)
# baseyear_end = 2019

# # domestic appliances
# dm_trade_netshare = make_fts(dm_trade_netshare, "aluminium-pack", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "glass-pack", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "plastic-pack", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "paper-pack", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "paper-print", 2012, baseyear_end) # here there is upward trend starting after 2012
# dm_trade_netshare = make_fts(dm_trade_netshare, "paper-san", 2010, baseyear_end) # here there is upward trend starting after 2010
# # product = "paper-san"
# # (make_fts(dm_trade_netshare, product, 2010, baseyear_end).
# #   datamatrix_plot(selected_cols={"Country" : ["EU27"],
# #                                 "Variables" : ["product-net-import"],
# #                                 "Categories1" : [product]}))

# # transport vehicles
# dm_trade_netshare = make_fts(dm_trade_netshare, "cars-EV", 2017, baseyear_end) # here I assume that net import of EVs will increase a lot (on trend with 2017-2020)
# dm_trade_netshare = make_fts(dm_trade_netshare, "cars-FCV", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "cars-ICE", 2019, 2023) # here I assume that net import of cars will stay approximately consant (on trend with 2019-2023)
# dm_trade_netshare = make_fts(dm_trade_netshare, "planes", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "ships", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "trains", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "trucks-EV", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "trucks-FCV", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "trucks-ICE", 1995, baseyear_end)
# product = "cars-ICE"
# (make_fts(dm_trade_netshare, product, 2019, 2023).
#   datamatrix_plot(selected_cols={"Country" : ["EU27"],
#                                 "Variables" : ["product-net-import"],
#                                 "Categories1" : [product]}))

# # transport infra
# dm_trade_netshare = make_fts(dm_trade_netshare, "rail", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "road", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "trolley-cables", baseyear_start, baseyear_end)

# # buildings
# dm_trade_netshare = make_fts(dm_trade_netshare, "floor-area-new-non-residential", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "floor-area-new-residential", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "floor-area-reno-non-residential", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "floor-area-reno-residential", baseyear_start, baseyear_end)

# # domestic appliances
# dm_trade_netshare = make_fts(dm_trade_netshare, "computer", 2010, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "dishwasher", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "dryer", 2000, 2007) # here I assume there is some problem with the data after 2008
# dm_trade_netshare = make_fts(dm_trade_netshare, "freezer", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "fridge", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "phone", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "tv", baseyear_start, baseyear_end)
# dm_trade_netshare = make_fts(dm_trade_netshare, "wmachine", 2000, 2007) # here I assume there is some problem with the data after 2008
# # product = "wmachine"
# # (make_fts(dm_trade_netshare, product, 2000, 2007).
# #   datamatrix_plot(selected_cols={"Country" : ["EU27"],
# #                                 "Variables" : "Variables" : ["product-net-import"],
# #                                 "Categories1" : [product]}))

# # pipes
# dm_trade_netshare = make_fts(dm_trade_netshare, "new-dhg-pipe", baseyear_start, baseyear_end)




# #####################################################
# ######################## OLD ########################
# #####################################################

# # get codes descriptions
# filepath = os.path.join(current_file_directory, '../data/eurostat/PRODCOM2024_PRODCOM2023_Table.csv')
# df_codes = pd.read_csv(filepath)
# df_codes = df_codes.loc[:,['PRODCOM2024_KEY', 'PRODCOM2024_NAME']]
# df_codes = df_codes.rename(columns={"PRODCOM2024_KEY": "prccode"})

# # get codes mapping with pathway calc
# filepath = os.path.join(current_file_directory, '../data/eurostat/PRODCOM2024_products_mapping.csv')
# df_map = pd.read_csv(filepath)

# # # get pickles
# # transport_data_file = "/Users/echiarot/Downloads/transport_CH_VD.pickle"
# # with open(transport_data_file, 'rb') as handle:
# #     dm_tradensport = pickle.load(handle)
# # list(dm_tradensport)
# # list(dm_tradensport["ots"])
# # list(dm_tradensport["fxa"])
# # df_cars = dm_tradensport["ots"]["passenger_technology-share_new"].write_df()
# # df_cars.columns

# # explore
# df.columns
# df["indicators\TIME_PERIOD"].unique()
# df1 = df.loc[df["indicators\TIME_PERIOD"] == "QNTUNIT",:]
# len(df["prccode"].unique())
# df["decl"].unique()

# # decl mapping
# # sources:
# # DECL drop down menu: https://ec.europa.eu/eurostat/databrowser/view/DS-056120/legacyMultiFreq/table?lang=en  
# # https://ec.europa.eu/eurostat/documents/120432/0/Quick+guide+on+accessing+PRODCOM+data+DS-056120.pdf/484b8bbf-e371-49f3-6fa7-6a2514ebfcc9?t=1696602916356
# decl_mapping = {1: "France",
#                 3: "Netherlands",
#                 4: "Germany",
#                 5: "Italy",
#                 6: "United Kingdom",
#                 7: "Ireland",
#                 8: "Denmark",
#                 9: "Greece",
#                 10: "Portugal",
#                 11: "Spain",
#                 17: "Belgium",
#                 18: "Luxembourg",
#                 24: "Iceland",
#                 28: "Norway",
#                 30: "Sweden",
#                 32: "Finland",
#                 38: "Austria",
#                 46: "Malta",
#                 52: "Turkiye",
#                 53: "Estonia",
#                 54: "Latvia",
#                 55: "Lithuania",
#                 60: "Poland",
#                 61: "Czech Republic",
#                 63: "Slovakia",
#                 64: "Hungary",
#                 66: "Romania",
#                 68: "Bulgaria",
#                 70: "Albania",
#                 91: "Slovenia",
#                 92: "Croatia",
#                 93: "Bosnia and Herzegovina",
#                 96: "North Macedonia",
#                 97: "Montenegro",
#                 98: "Serbia",
#                 600: "Cyprus",
#                 1110: "EU15",
#                 1111: "EU25",
#                 1112: "EU27_2007",
#                 2027: "EU27_2020",
#                 2028: "EU28"}
# np.array(list(decl_mapping))[[i not in df["decl"].unique() for i in list(decl_mapping)]] # EU25 is missing from data

# # insert country names
# df["country"] = np.nan
# for key in decl_mapping.keys():
#     df.loc[df["decl"] == key,"country"] = decl_mapping[key]

# # insert mapping with calc
# df_map = df_map.rename(columns= {"PRODCOM2024_KEY" : "prccode"})
# for i in range(0,len(df_map)):
#     if not np.isnan(df_map.loc[i,"prccode"]):
#         df_map.loc[i,"prccode"] = str(int(df_map.loc[i,"prccode"]))
# df_map_sub = df_map.filter(items=['prccode', 'calc_industry_product'])
# df_map_sub = df_map_sub.dropna()
# df = pd.merge(df, df_map_sub, how="left", on=["prccode"])

# # keep only products with reference to calc
# df_sub = df.loc[~df["calc_industry_product"].isnull(),:]

# # keep only import and export
# df_sub.rename(columns={"indicators\TIME_PERIOD":"variable"}, inplace = True)
# keep = ["IMPQNT","EXPQNT","PRODQNT"]
# # next week: check "IMPVAL","EXPVAL","PRODVAL" and if it's worth to do value over value (as prodqnt has lots of missing data)
# df_sub_unit = df_sub.loc[df_sub["variable"].isin(["QNTUNIT"]),:]
# df_sub = df_sub.loc[df_sub["variable"].isin(keep),:]

# # make long format
# drops = ['freq', 'decl']
# df_sub.drop(drops,1, inplace = True)
# indexes = ['prccode', 'variable', 'country', 'calc_industry_product']
# df_sub = pd.melt(df_sub, id_vars = indexes, var_name='year')

# # make unit as column
# drops = ['freq', 'decl']
# df_sub_unit.drop(drops,1, inplace = True)
# indexes = ['prccode', 'variable', 'country', 'calc_industry_product']
# df_sub_unit = pd.melt(df_sub_unit, id_vars = indexes, var_name='year')
# df_sub_unit.rename(columns={"value":"unit"}, inplace = True)
# keep = ['prccode', 'country', 'calc_industry_product','year','unit']
# indexes = ['prccode', 'country', 'calc_industry_product','year']
# df_sub = pd.merge(df_sub, df_sub_unit.loc[:,keep], how="left", on=indexes)
# # df_sub_unit = df_sub_unit.loc[~df_sub_unit["unit"].isnull(),:]
# df_sub["unit"].unique()
# # p/st = number of items
# # kg = kilograms
# # ct/l = Carrying capacity in tonnes
# # Compensated Gross Tonne

# # fix unit
# df_sub = df_sub.reset_index()
# for i in range(0, len(df_sub["unit"])):
#     if type(df_sub.loc[i,"unit"]) == str:
#         df_sub.loc[i,"unit"] = df_sub.loc[i,"unit"].strip()
# # df_fix = df_sub.loc[~df_sub["unit"].isnull(),:]
# # indexes = ['prccode', 'calc_industry_product']
# # def myfun(x):
# #     return(pd.unique(x)[0])
# # df_fix = df_fix.groupby(indexes, as_index=False)['unit'].agg(myfun)
# # codes = df_sub["prccode"].unique()
# # for c in codes:
# #     df_sub.loc[df_sub["prccode"] == c,"unit"] = df_fix.loc[df_fix["prccode"] == c,"unit"].values[0]
# df_sub["unit"].unique()

# # fix value
# df_sub["value"] = [float(i) for i in df_sub["value"]]

# # order and sort
# indexes = ['country', 'variable', 'prccode', 'calc_industry_product', 'year']
# variabs = ['value', 'unit']
# df_sub = df_sub.loc[:,indexes + variabs]
# df_sub = df_sub.sort_values(by=indexes)

# # check the units
# df_check = df_sub.loc[~df_sub["unit"].isnull(),:]
# df_check = df_check.loc[df_check["unit"] != "p/st",:]
# A = df_map.loc[df_map["prccode"].isin(df_check["prccode"]),:]

# # aggregate by calc_industry_product
# df_sub = df_sub.reset_index()
# indexes = ['country', 'variable', 'calc_industry_product', 'year','unit']
# df_sub = df_sub.groupby(indexes, as_index=False)['value'].agg(sum)

# # keep right units
# df_sub["calc_industry_product"].unique()
# df_sub["unit"].unique()
# df_sub.loc[df_sub["calc_industry_product"].isin(["plastic-pack"]),"unit"].unique()
# units_dict = {'aluminium-pack' : ['p/st'],
#               'cars-EV' : ['p/st'],
#               'cars-ICE' : ['p/st'],
#               'computer' : ['p/st'],
#               'dishwasher' : ['p/st'],
#               'fertilizer' : ['kg', 'kg K2O', 'kg N', 'kg P2O5', 'kg effect'],
#               'freezer' : ['p/st'],
#               'fridge' : ['p/st'],
#               'glass-pack' : ['kg'],
#               'paper-pack' : ['kg'],
#               'paper-print' : ['kg'],
#               'paper-san' : ['kg'],
#               'phone' : ['p/st'],
#               'planes' : ['p/st'],
#               'plastic-pack' : ['kg'],
#               'ships' : ['p/st'],
#               'trains' : ['p/st'],
#               'trucks-EV' : ['p/st'],
#               'trucks-ICE' : ['p/st'],
#               'tv' : ['p/st'],
#               'wmachine' : ['p/st']}
# df_sub = pd.concat([df_sub.loc[(df_sub["calc_industry_product"] == key) & \
#                                (df_sub["unit"].isin(units_dict[key])),:] \
#                     for key in units_dict.keys()])
# df_sub.loc[df_sub["unit"] == 'p/st',"unit"] = "num"

# # groupby for fertilizer
# df_fert = df_sub.loc[df_sub["calc_industry_product"] == "fertilizer",:]
# indexes = ['country', 'variable', 'calc_industry_product', 'year']
# df_fert = df_fert.groupby(indexes, as_index=False)['value'].agg(sum)
# df_fert["unit"] = "kg"
# df_sub = df_sub.loc[~df_sub["calc_industry_product"].isin(["fertilizer"]),:]
# df_sub = pd.concat([df_sub, df_fert])

# # fix countries
# countries_calc = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 
#                   'Czech Republic', 'Denmark', 'EU27', 'Estonia', 'Finland', 
#                   'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 
#                   'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 
#                   'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 
#                   'Slovenia', 'Spain', 'Sweden', 'United Kingdom']
# df_sub["country"].unique()
# drops = ['Albania','Bosnia and Herzegovina','EU15','EU28','Iceland','Montenegro',
#          'North Macedonia', 'Norway', 'Serbia', 'Turkiye']
# df_sub = df_sub.loc[~df_sub["country"].isin(drops),:]
# countries = df_sub["country"].unique()

# # EU27
# check = ['EU27_2007','EU27_2020']
# df_check = df_sub.loc[df_sub["country"].isin(check),:]
# df_check = df_check.loc[df_check["calc_industry_product"] == "cars-ICE",:]

# drops = ['EU27_2007','EU27_2020', 'United Kingdom']
# df_check2 = df_sub.loc[~df_sub["country"].isin(drops),:]
# # df_temp1 = df_check2.loc[df_check2["calc_industry_product"] == "cars-ICE",:]
# df_temp1 = df_check2.copy()
# indexes = ['variable', 'calc_industry_product', 'year', 'unit']
# df_temp2 = df_temp1.groupby(indexes, as_index=False)['value'].agg(sum)
# fig = px.line(df_temp2, x='year', y='value', color="variable", line_group="variable",
#               facet_col="calc_industry_product", facet_col_wrap=2)
# fig.update_yaxes(matches=None)
# # fig.show()

# # I assume that trade extra eu is from the data EU27_2020
# df_sub = df_sub.loc[~df_sub["country"].isin(['EU27_2007']),:]
# df_sub.loc[df_sub["country"] == 'EU27_2020',"country"] = "EU27"
# df_temp = df_sub.loc[df_sub["country"] == "EU27",:]
# # fig = px.line(df_temp, x='year', y='value', color="variable", line_group="variable",
# #               facet_col="calc_industry_product", facet_col_wrap=2)
# # fig.update_yaxes(matches=None)
# # fig.show()

# # make df ready for conversion to dm
# df_sub.loc[df_sub["variable"] == "IMPQNT","variable"] = "product-import"
# df_sub.loc[df_sub["variable"] == "EXPQNT","variable"] = "product-export"
# df_sub.loc[df_sub["variable"] == "PRODQNT","variable"] = "product-demand"
# df_sub["variable"] = df_sub["variable"] + "_" + df_sub["calc_industry_product"] + "[" + df_sub["unit"] + "]"
# df_sub = df_sub.rename(columns={"country": "Country", "year" : "Years"})
# drops = ["calc_industry_product","unit"]
# df_sub.drop(drops,1, inplace = True)
# countries = df_sub["Country"].unique()
# years = df_sub["Years"].unique()
# variables = df_sub["variable"].unique()
# panel_countries = np.repeat(countries, len(variables) * len(years))
# panel_years = np.tile(np.tile(years, len(variables)), len(countries))
# panel_variables = np.tile(np.repeat(variables, len(years)), len(countries))
# df_temp = pd.DataFrame({"Country" : panel_countries, 
#                         "Years" : panel_years, 
#                         "variable" : panel_variables})
# df_sub = pd.merge(df_temp, df_sub, how="left", on=["Country","Years","variable"])

# # split in dms
# df_sub["selection"] = [i.split("_")[1].split("[")[0] for i in df_sub["variable"]]

# # dm_bld_domapp
# df_temp = df_sub.loc[df_sub["selection"].isin(['computer', 'dishwasher', 'freezer', 'fridge',
#                                                'phone', 'tv', 'wmachine']),["Country","Years","variable","value"]]
# df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
# dm_bld_domapp = DataMatrix.create_from_df(df_temp, 1)

# # dm_tra_veh
# df_temp = df_sub.loc[df_sub["selection"].isin(['cars-EV', 'cars-ICE','planes', 'ships', 'trains',
#                                                'trucks-EV', 'trucks-ICE']),["Country","Years","variable","value"]]
# df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
# dm_tra_veh = DataMatrix.create_from_df(df_temp, 1)

# # dm_lfs
# df_temp = df_sub.loc[df_sub["selection"].isin(['glass-pack', 'paper-pack', 'paper-print',
#                                                'paper-san', 'plastic-pack']),["Country","Years","variable","value"]]
# df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
# dm_lfs = DataMatrix.create_from_df(df_temp, 1)
# # TODO: I currently do not have aluminium pack in kg, for the moment i create it equal to zero

# # put together
# DM_trade = {"domapp" : dm_bld_domapp,
#             "tra-veh" : dm_tra_veh,
#             "lfs" : dm_lfs}

# # # plot
# # DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["tra-veh"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["lfs"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # # phone data starts in 2022, i will put a zero in 2003 and then compute the linear trend for missing 

# # Set years range
# years_setting = [1990, 2023, 2050, 5]
# startyear = years_setting[0]
# baseyear = years_setting[1]
# lastyear = years_setting[2]
# step_fts = years_setting[3]
# years_ots = list(range(startyear, baseyear+1, 1))
# years_fts = list(range(baseyear+2, lastyear+1, step_fts))
# years_all = years_ots + years_fts

# # put zero for phone and planes in 2003
# idx = DM_trade["domapp"].idx
# DM_trade["domapp"].array[:,idx[2003],:,idx["phone"]] = 0
# idx = DM_trade["tra-veh"].idx
# DM_trade["tra-veh"].array[:,idx[2003],:,idx["planes"]] = 0

# # fill in missing values with linear fitting
# for key in DM_trade.keys():
#     years_fitting = DM_trade[key].col_labels["Years"]
#     DM_trade[key] = linear_fitting(DM_trade[key], years_fitting, min_t0=0)
#     DM_trade[key].array = np.round(DM_trade[key].array,0)

# # # plot
# # DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["tra-veh"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["lfs"].filter({"Country" : ["EU27"]}).datamatrix_plot()

# # fix jumps
# for key in DM_trade.keys(): DM_trade[key] = fix_jumps_in_dm(DM_trade[key])

# # # plot
# # DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["tra-veh"].filter({"Country" : ["EU27"]}).datamatrix_plot()
# # DM_trade["lfs"].filter({"Country" : ["EU27"]}).datamatrix_plot()

# # add missing years ots
# for key in DM_trade.keys():
#     years_missing = list(set(years_ots) - set(DM_trade[key].col_labels['Years']))
#     DM_trade[key].add(np.nan, col_label=years_missing, dummy=True, dim='Years')
#     DM_trade[key].sort('Years')

# # fill in missing years ots with linear fitting
# for key in DM_trade.keys():
#     DM_trade[key] = linear_fitting(DM_trade[key], years_missing, min_t0=0)
#     DM_trade[key].array = np.round(DM_trade[key].array,0)

# # # check
# # df_check = DM_trade["domapp"].write_df()
# # DM_trade["domapp"].filter({"Country" : ["EU27"]}).datamatrix_plot()

# # generate cars-FCV and trucks-FCV
# # we assume that imports remain zero throughout
# DM_trade["tra-veh"].add(0, "Categories1", "cars-FCV", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "trucks-FCV", unit="num", dummy=True)
# DM_trade["tra-veh"].sort("Categories1")

# # generate aluminium-pack
# # for the moment we assume that imports remain zero throughout
# DM_trade["lfs"].add(0, "Categories1", "aluminium-pack", unit="kg", dummy=True)
# DM_trade["lfs"].sort("Categories1")

# # generate new-dhg-pipe, rail, road, trolley-cables, floor-area-new-non-residential, 
# # floor-area-new-residential, floor-area-reno-non-residential, floor-area-reno-residential
# # we assume imports of these are all zero
# DM_trade["domapp"].add(0, "Categories1", "new-dhg-pipe", unit="num", dummy=True)
# dm_bld_pipe = DM_trade["domapp"].filter({"Categories1" : ["new-dhg-pipe"]})
# dm_bld_pipe.units['product-export'] = "km"
# dm_bld_pipe.units['product-import'] = "km"
# DM_trade["domapp"].drop("Categories1", ["new-dhg-pipe"])
# DM_trade["pipe"] = dm_bld_pipe

# DM_trade["tra-veh"].add(0, "Categories1", "rail", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "road", unit="num", dummy=True)
# DM_trade["tra-veh"].add(0, "Categories1", "trolley-cables", unit="num", dummy=True)
# dm_tra_infra = DM_trade["tra-veh"].filter({"Categories1" : ["rail","road","trolley-cables"]})
# dm_tra_infra.units['product-export'] = "km"
# dm_tra_infra.units['product-import'] = "km"
# DM_trade["tra-veh"].drop("Categories1", ["rail","road","trolley-cables"])
# dm_tra_infra.sort("Categories1")
# DM_trade["tra-infra"] = dm_tra_infra

# DM_trade["domapp"].add(0, "Categories1", "floor-area-new-non-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-new-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-non-residential", unit="m2", dummy=True)
# DM_trade["domapp"].add(0, "Categories1", "floor-area-reno-residential", unit="m2", dummy=True)
# dm_bld_floor = DM_trade["domapp"].filter({"Categories1" : ["floor-area-new-non-residential","floor-area-new-residential", 
#                                                            "floor-area-reno-non-residential", "floor-area-reno-residential"]})
# dm_bld_floor.units['product-export'] = "m2"
# dm_bld_floor.units['product-import'] = "m2"
# DM_trade["domapp"].drop("Categories1", ["floor-area-new-non-residential","floor-area-new-residential", 
#                                         "floor-area-reno-non-residential", "floor-area-reno-residential"])
# dm_bld_floor.sort("Categories1")
# DM_trade["bld-floor"] = dm_bld_floor

# # dryer
# # I assume dryers are 1% of exports and imports (check excel file in WITS folder called "percentage_dryers_export_EU")
# idx = DM_trade["domapp"].idx
# arr_temp = DM_trade["domapp"].array[...,idx["wmachine"]] * 0.01
# DM_trade["domapp"].add(arr_temp, col_label="dryer", dim='Categories1', unit = "num")
# DM_trade["domapp"].sort("Categories1")

# # add missing years fts
# for key in DM_trade.keys():
#     DM_trade[key].add(np.nan, col_label=years_fts, dummy=True, dim='Years')

# # fill in missing years fts for EU27 with linear fitting
# def make_fts(dm, variable, year_start, year_end, country = "EU27", dim = "Categories1", 
#              min_t0=0, min_tb=0, years_fts = years_fts):
#     dm = dm.copy()
#     idx = dm.idx
#     based_on_yars = list(range(year_start, year_end + 1, 1))
#     dm_temp = linear_fitting(dm.filter({"Country" : [country], dim : [variable]}), 
#                              years_ots = years_fts, min_t0=min_t0, min_tb=min_tb, based_on = based_on_yars)
#     idx_temp = dm_temp.idx
#     if dim == "Variables":
#         dm.array[idx[country],:,idx[variable],...] = \
#             np.round(dm_temp.array[idx_temp[country],:,idx_temp[variable],...],0)
#     if dim == "Categories1":
#         dm.array[idx[country],:,:,idx[variable]] = \
#             np.round(dm_temp.array[idx_temp[country],:,:,idx_temp[variable]],0)
#     if dim == "Categories2":
#         dm.array[idx[country],:,:,:,idx[variable]] = \
#             np.round(dm_temp.array[idx_temp[country],:,:,:,idx_temp[variable]],0)
#     if dim == "Categories3":
#         dm.array[idx[country],:,:,:,:,idx[variable]] = \
#             np.round(dm_temp.array[idx_temp[country],:,:,:,:,idx_temp[variable]],0)
    
#     return dm

# baseyear_start = 2006
# baseyear_end = 2019

# # domestic appliances
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "aluminium-pack", baseyear_start, baseyear_end)
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "glass-pack", baseyear_start, baseyear_end)
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "plastic-pack", baseyear_start, baseyear_end)
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "paper-pack", baseyear_start, baseyear_end)
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "paper-print", baseyear_start, baseyear_end)
# DM_trade["lfs"] = make_fts(DM_trade["lfs"], "paper-san", baseyear_start, baseyear_end)

# # transport vehicles
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-EV", 2021, 2022)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-FCV", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "cars-ICE", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "planes", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "ships", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trains", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-EV", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-FCV", baseyear_start, baseyear_end)
# DM_trade["tra-veh"] = make_fts(DM_trade["tra-veh"], "trucks-ICE", 1995, baseyear_end)

# # transport infra
# DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "rail", baseyear_start, baseyear_end)
# DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "road", baseyear_start, baseyear_end)
# DM_trade["tra-infra"] = make_fts(DM_trade["tra-infra"], "trolley-cables", baseyear_start, baseyear_end)

# # buildings
# DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-new-non-residential", baseyear_start, baseyear_end)
# DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-new-residential", baseyear_start, baseyear_end)
# DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-reno-non-residential", baseyear_start, baseyear_end)
# DM_trade["bld-floor"] = make_fts(DM_trade["bld-floor"], "floor-area-reno-residential", baseyear_start, baseyear_end)

# # domestic appliances
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "computer", 2010, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "dishwasher", baseyear_start, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "dryer", 2000, 2007) # here I assume there is some problem with the data after 2008
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "freezer", baseyear_start, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "fridge", baseyear_start, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "phone", baseyear_start, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "tv", baseyear_start, baseyear_end)
# DM_trade["domapp"] = make_fts(DM_trade["domapp"], "wmachine", 2000, 2007) # here I assume there is some problem with the data after 2008

# # pipes
# DM_trade["pipe"] = make_fts(DM_trade["pipe"], "new-dhg-pipe", baseyear_start, baseyear_end)

# # product-net-import = product-import - product-export
# DM_trade["lfs"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="num")
# DM_trade["tra-veh"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="num")
# DM_trade["tra-infra"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="km")
# DM_trade["bld-floor"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="m2")
# DM_trade["pipe"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="km")
# DM_trade["domapp"].operation("product-import", "-", "product-export", dim="Variables", out_col="product-net-import", unit="num")

# # # check
# # make_fts(dm_bld_domapp, "phone", 2021, 2023).datamatrix_plot(selected_cols={"Country" : ["EU27"], 
# #                                                                             "Variables" : ["product-import","product-export"],
# #                                                                             "Categories1" : ["phone"]})
# # df_temp = dm_bld_domapp.write_df()
# # df_temp.columns
# # dm_bld_domapp.datamatrix_plot(selected_cols={"Country" : ["EU27"], "Variables" : ["product-import","product-export"]})

# # save
# DM_trade_goods = {
#     "lfs" : dm_lfs,
#     "tra_veh" : dm_tra_veh,
#     "tra_infra" : dm_tra_infra,
#     "bld_floor" : dm_bld_floor,
#     "bld_pipe" : dm_bld_pipe,
#     "bld_domapp" : dm_bld_domapp
#     }
# f = os.path.join(current_file_directory, '../data/datamatrix/lever_product-net-import.pickle')
# with open(f, 'wb') as handle:
#     pickle.dump(DM_trade_goods, handle, protocol=pickle.HIGHEST_PROTOCOL)
