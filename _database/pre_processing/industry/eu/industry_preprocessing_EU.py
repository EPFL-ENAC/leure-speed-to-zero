
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa, update_database_from_db
from model.common.interface_class import Interface
from model.common.auxiliary_functions import filter_geoscale, cdm_to_dm, read_database_to_ots_fts_dict, read_level_data, simulate_input, calibration_rates, cost
import pandas as pd
import pickle
import json
import os
import numpy as np
import re
import warnings
warnings.simplefilter("ignore")

__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/EU/industry_preprocessing_EU.py"

########################################################
#################### PRE PROCESSING ####################
########################################################

#############################
##### FIXED ASSUMPTIONS #####
#############################

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))
xls_directory = os.path.join(current_file_directory, "data")

# costs
file = "costs.xlsx"
xls_file_directory = xls_directory +  "/" + file
df_costs = pd.read_excel(xls_file_directory)

# price index
file = "costs_priceindex.xlsx"
xls_file_directory = xls_directory +  "/" + file
df_price = pd.read_excel(xls_file_directory)

# add extra countries in price index
df_price_extra = pd.DataFrame({"Country" : ["EU27", "EU28","Paris", "Vaud"], 
                               "Years" : [2015,2015,2015,2015], 
                               "ots_tec_price-indices_pli[%]" : [100,100, 107.6, 154.0]})
df_price = pd.concat([df_price, df_price_extra]).reset_index(level=0, drop=True)
df_price = df_price.sort_values("Country")

# add other countries to costs
countries = df_price["Country"].tolist()
countries.remove("EU28")
df_costs_new = df_costs.copy()
for c in countries:
    df_temp = df_costs.copy()
    df_temp["Country"] = c
    df_costs_new = pd.concat([df_costs_new, df_temp]).reset_index(level=0, drop=True)

# merge with price data
df_costs_new = pd.merge(df_costs_new, df_price, how="left", on=["Country","Years"])

# get new capex and opex 2050 and baseyear by weighting for price index
variabs = ["capex_2050","capex_baseyear","opex_2050","opex_baseyear"]
for v in variabs:
    df_costs_new[v] = df_costs_new[v] * df_costs_new["ots_tec_price-indices_pli[%]"] / 100

# b factor = log(1 - linear rate)/log(2)
df_costs_new["capex_b_factor"] = np.log(1 - df_costs_new["capex_lr"]) / np.log(2)
df_costs_new["opex_b_factor"] = np.log(1 - df_costs_new["opex_lr"]) / np.log(2)

# d factor = (cost 2050 - cost 2015) / 2050 - 2015
df_costs_new["capex_d_factor"] = (df_costs_new["capex_2050"] - df_costs_new["capex_baseyear"]) / (2050 - 2015)
df_costs_new["opex_d_factor"] = (df_costs_new["opex_2050"] - df_costs_new["opex_baseyear"]) / (2050 - 2015)

# long format
df = df_costs_new.copy()
df1 = df.loc[df["Country"] != "EU28",:]
indexes = ["Country","Years", "sector", "technology_code","capex_unit","opex_unit"]
variabs = ['capex_b_factor', 'capex_baseyear', 'capex_d_factor', 'opex_b_factor',
           'opex_baseyear', 'opex_d_factor','evolution_method']
df1 = df1.loc[:,indexes + variabs]
df1 = pd.melt(df1, id_vars = indexes)

# drop na
df1 = df1.dropna(subset=["value"])

# make variables
df1 = df1.rename(columns={"Country": "geoscale", "Years": "timescale"})
df1["module"] = "cost"
df1["element"] = df1["variable"]
df1["element"] = [i.replace("_", "-") for i in df1["element"].values.tolist()]
df1["item"] = df1["technology_code"]
df1["unit"] = "num"
df1.loc[df1["element"] == "capex-baseyear","unit"] = "EUR/" + df1.loc[df1["element"] == "capex-baseyear","capex_unit"]
df1.loc[df1["element"] == "opex-baseyear","unit"] = "EUR/" + df1.loc[df1["element"] == "opex-baseyear","opex_unit"]
df1["eucalc-name"] = df1["sector"] + "_" + df1["element"] + "_" + df1["item"] + "[" + df1["unit"] + "]"
df1["lever"] = "none"
df1["level"] = 0
df1["string-pivot"] = "none"
df1["type-prefix"] = "none"
df1["module-prefix"] = "cost-" + df1["sector"]
df1["reference-id"] = "missing-reference"
df1["interaction-file"] = "cost_fixed-assumptions"

# drop extra variables
df1 = df1.drop(['sector','technology_code','capex_unit','opex_unit','variable'], axis = 1)

# order and sort
df1 = df1.loc[:,['geoscale', "timescale", "module", "eucalc-name", "lever", "level", "string-pivot",
                  "type-prefix", "module-prefix", "element", "item", "unit", "value", "reference-id", 
                  "interaction-file"]]
df1 = df1.sort_values(by=['geoscale', "timescale", "module", "eucalc-name"])

# save
filepath = os.path.join(current_file_directory, '../../../data/csv/costs_fixed-assumptions.csv')
df1.to_csv(filepath, sep = ";", index = False)

