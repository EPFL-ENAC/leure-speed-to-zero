
# packages
from model.common.constant_data_matrix_class import ConstantDataMatrix
import pandas as pd
import pickle
import os
import warnings
import numpy as np
warnings.simplefilter("ignore")

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_const_material-decomposition.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

#############################################
##### NEW CONSTANTS FROM LIT REV BY E4S #####
#############################################

# get data
filepath = os.path.join(current_file_directory, '../data/Literature/literature_review_material_decomposition.xlsx')
df = pd.read_excel(filepath)

# name first 2 columns
df.rename(columns={"Unnamed: 0": "material", "Unnamed: 1" : "material-sub"}, inplace=True)

# melt
indexes = ["material","material-sub"]
df = pd.melt(df, id_vars = indexes, var_name='variable')

# save materials lists
material_sub_alu = ["cast-aluminium","wrought-aluminium"]
material_sub_steel = ["cast-iron","iron","steel","galvanized-steel","stainless-steel"]
material_sub_pla = ["plastics-ABS", "plastics-PP", "plastics-PA", "plastics-PBT", "plastics-PE",
                    "plastics-PMMA", "plastics-POM", "plastics-EPMD", "plastics-EPS", "plastics-PS",
                    "plastics-PU", "plastics-PUR", "plastics-PET", "plastics-PVC", 
                    "plastics-carbon-fiber-reinforced", "plastics-glass-fiber-reinforced",
                    "plastics-mixture","plastics-other"]
material_current = ['Aluminium', 'ammonia', 'concrete-and-inert', 'plastics-total', 'copper', 'glass', 
                    'lime', 'paper', 'iron_&_steel', 'wood']
material_current_correct_name = ['aluminium', 'ammonia', 'cement', 'chem', 'copper', 'glass', 
                                  'lime', 'paper', 'steel', 'timber']

def aggregate_materials(df, variable, material_current, material_current_correct_name):
    
    # get df for one variable
    df_temp = df.loc[df["variable"] == variable,:]

    # drop na in value
    df_temp = df_temp.dropna(subset=['value'])

    # rename missing material with sub material and drop sub material
    df_temp.loc[df_temp["material"].isnull(),"material"] = df_temp.loc[df_temp["material"].isnull(),"material-sub"]
    df_temp = df_temp.loc[:,["material","variable","value"]]

    # aggregate sub materials if any
    df_temp.loc[df_temp["material"].isin(material_sub_pla),"material"] = "plastics-total"
    df_temp.loc[df_temp["material"].isin(material_sub_alu),"material"] = "Aluminium"
    df_temp.loc[df_temp["material"].isin(material_sub_steel),"material"] = "iron_&_steel"
    df_temp = df_temp.groupby(["material","variable"], as_index=False)['value'].agg(sum)

    # get df with materials of current model and change their names
    df_temp1 = df_temp.loc[df_temp["material"].isin(material_current),:]
    for i in range(0, len(material_current)):
        df_temp1.loc[df_temp1["material"] == material_current[i],"material"] = material_current_correct_name[i]
    
    # get other materials, sum them and concat with others
    df_temp2 = df_temp.loc[~df_temp["material"].isin(material_current),:]
    df_temp2 = df_temp2.groupby(["variable"], as_index=False)['value'].agg(sum)
    df_temp2["material"] = "other"
    df_temp = pd.concat([df_temp1, df_temp2])
    
    # return
    return df_temp

variabs = df["variable"].unique()
df_agg = pd.concat([aggregate_materials(df, variable, 
                                        material_current = material_current, 
                                        material_current_correct_name = material_current_correct_name) 
                    for variable in variabs])

# check
df_check = df_agg.groupby(["variable"], as_index=False)['value'].agg(sum)

# map to products we have in the calc (by taking the mean across products)
dict_map = {"cars-ICE[kg/num]": ["LDV_ICE-gasoline[kg/unit]","LDV_ICE-diesel[kg/unit]","LDV_HEV[kg/unit]"],
            "cars-EV[kg/num]" : ["LDV_BEV[kg/unit]"],
            "cars-FCV[kg/num]" : ["LDV_FCEV[kg/unit]"],
            "trucks-ICE[kg/num]": ["HDVH_ICE-Class-8-day-cab-truck[kg/unit]",
                                    "HDVH_HEV-Class-8-day-cab-truck[kg/unit]",
                                    "HDVH_ICE-Class-8-sleeper-cab-truck[kg/unit]",
                                    "HDVH_HEV-Class-8-sleeper-cab-truck[kg/unit]",
                                    "HDVM_ICE-Class-6-PnD-truck[kg/unit]",
                                    "HDVM_HEV-Class-6-PnD-truck[kg/unit]"],
            "trucks-EV[kg/num]" : ["HDVH_BEV-Class-8-day-cab-truck[kg/unit]",
                                    "HDVH_BEV-Class-8-sleeper-cab-truck[kg/unit]",
                                    "HDVM_EV-Class-6-PnD-truck[kg/unit]"],
            "trucks-FCV[kg/num]" : ["HDVH_FCEV-Class-8-day-cab-truck[kg/unit]",
                                    "HDVH_FCV-Class-8-sleeper-cab-truck[kg/unit]",
                                    "HDVM_FCV-Class-6-PnD-truck[kg/unit]"],
            "computer[kg/num]" : ["electronics_PC[kg/unit]"],
            "dryer[kg/num]" : ["larger-appliances_dryer[kg/unit]"],
            "tv[kg/num]" : ["electronics_TV[kg/unit]"],
            "phone[kg/num]" : ["electronics_phones[kg/unit]"],
            "fridge[kg/num]" : ["larger-appliances_fridge[kg/unit]"],
            "dishwasher[kg/num]" : ["larger-appliances_dishwasher[kg/unit]"],
            "wmachine[kg/num]" : ["larger-appliances_washing-machine[kg/num]"], 
            "freezer[kg/num]" : ["larger-appliances_freezer[kg/num]"], 
            "floor-area-new-residential[kg/m2]" : ["floor-area-new-residential[kg/m2]"],
            "floor-area-new-non-residential[kg/m2]" : ["floor-area-new-non-residential[kg/m2]"], 
            "floor-area-reno-residential[t/m2]" : ["floor-area-reno-residential[t/m2]"], 
            "floor-area-reno-non-residential[t/m2]" : [],	
            "new-dhg-pipe[t/km]" : ["District heating pipes [t/km]"],	
            "ships[t/num]" : ["Ships [t/num]"], 
            "trains[t/num]" : ["Trains [t/num]"],
            "planes[t/num]" : ["Planes [t/num]"],
            "road[t/km]" : ["Road [t/km]"], 
            "rail[t/km]" : ["Rail [t/km]"], 	
            "trolley-cables[t/km]" : ["Trolley-cables [t/km]"],
            "fertilizer[t/t]" : ["Fertilizer [t/t]"],
            "plastic-pack[t/t]" : ["Plastic packaging [t/t]"],
            "paper-pack[t/t]" : ["Paper packaging [t/t]"],
            "aluminium-pack[t/t]" : ["Aluminium packaging [t/t]"],
            "glass-pack[t/t]" : ["Glass packaging [t/t]"],
            "paper-print[t/t]" : ["Paper printing and graphic [t/t]"],
            "paper-san[t/t]" : ["Paper sanitary and household [t/t]"]}

for key in dict_map.keys():
    df_agg.loc[df_agg["variable"].isin(dict_map[key]),"variable"] = key
df_agg = df_agg.groupby(["variable","material"], as_index=False)['value'].agg(np.mean)

# check
df_check = df_agg.groupby(["variable"], as_index=False)['value'].agg(sum)

# fix units
df_agg.loc[df_agg["variable"] == "floor-area-new-residential[kg/m2]","value"] = \
    df_agg.loc[df_agg["variable"] == "floor-area-new-residential[kg/m2]","value"] / 1000
df_agg.loc[df_agg["variable"] == "floor-area-new-non-residential[kg/m2]","value"] = \
    df_agg.loc[df_agg["variable"] == "floor-area-new-non-residential[kg/m2]","value"] / 1000
df_agg.loc[df_agg["variable"] == "floor-area-new-residential[kg/m2]","variable"] = "floor-area-new-residential[t/m2]"
df_agg.loc[df_agg["variable"] == "floor-area-new-non-residential[kg/m2]","variable"] = "floor-area-new-non-residential[t/m2]"
ls_temp = ["fridge[kg/num]", "dishwasher[kg/num]", "wmachine[kg/num]", 
            "freezer[kg/num]", "dryer[kg/num]", "tv[kg/num]", "phone[kg/num]", 
            "computer[kg/num]",
            "cars-ICE[kg/num]", "trucks-ICE[kg/num]", "cars-FCV[kg/num]",
            "trucks-FCV[kg/num]", "cars-EV[kg/num]", "trucks-EV[kg/num]"]
ls_temp1 = ["fridge[t/num]", "dishwasher[t/num]", "wmachine[t/num]", 
            "freezer[t/num]", "dryer[t/num]", "tv[t/num]", "phone[t/num]", 
            "computer[t/num]",
            "cars-ICE[t/num]", "trucks-ICE[t/num]", "cars-FCV[t/num]",
            "trucks-FCV[t/num]", "cars-EV[t/num]", "trucks-EV[t/num]"]
for i in range(0, len(ls_temp)):
    df_agg.loc[df_agg["variable"] == ls_temp[i],"value"] = \
        df_agg.loc[df_agg["variable"] == ls_temp[i],"value"] / 1000
    df_agg.loc[df_agg["variable"] == ls_temp[i],"variable"] = ls_temp1[i]
# df_agg["variable"].unique()

# # fix units
# import re
# variables = np.array(df["variable"].unique())
# variables = variables[[bool(re.search("kg/",v)) for v in variables]]
# for v in variables:
#     df_agg.loc[df["variable"] == v,"value"] = df_agg.loc[df["variable"] == v,"value"]/1000
#     df_agg.loc[df["variable"] == v,"variable"] = v.replace("kg","t")

# make datamatrixes
def create_constant(df, variables):
    
    df_temp = df.loc[df["variable"].isin(variables),:]

    # rename variables
    df_temp["variable"] = [v.split("[")[0] + "_" + m + "[" + v.split("[")[1] for v, m in zip(df_temp["variable"],df_temp["material"])]
    df_temp.drop(["material"], axis=1, inplace=True)
    
    # put unit
    df_temp["unit"] = [i.split("[")[1].split("]")[0] for i in df_temp["variable"]]
    
    const = {
        'name': list(df_temp['variable']),
        'value': list(df_temp['value']),
        'idx': dict(zip(list(df_temp['variable']), range(len(df_temp['variable'])))),
        'units': dict(zip(list(df_temp['variable']), list(df_temp['unit'])))
    }
    
    # return
    return const

# cdm_bld_floor
tmp = create_constant(df_agg, ["floor-area-new-residential[t/m2]", "floor-area-new-non-residential[t/m2]",
                               "floor-area-reno-residential[t/m2]", "floor-area-reno-non-residential[t/m2]"])
cdm_bld_floor = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_bld_floor.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_bld_pipe
tmp = create_constant(df_agg, ["new-dhg-pipe[t/km]"])
cdm_bld_pipe = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_bld_pipe.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_domapp
tmp = create_constant(df_agg, ["fridge[t/num]", "dishwasher[t/num]","wmachine[t/num]", 
                               "freezer[t/num]", "dryer[t/num]", "tv[t/num]", 
                               "phone[t/num]", "computer[t/num]"])
cdm_domapp = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_domapp.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_tra_veh
tmp = create_constant(df_agg, ["cars-ICE[t/num]", "trucks-ICE[t/num]", "cars-FCV[t/num]",
                               "ships[t/num]", "trains[t/num]", "planes[t/num]",
                               "trucks-FCV[t/num]", "cars-EV[t/num]", "trucks-EV[t/num]"])
cdm_tra_veh = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_tra_veh.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_tra_infra
tmp = create_constant(df_agg, ["road[t/km]", "rail[t/km]", "trolley-cables[t/km]"])
cdm_tra_infra = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_tra_infra.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_fert
tmp = create_constant(df_agg, ["fertilizer[t/t]"])
cdm_fert = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_fert.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# cdm_pack
tmp = create_constant(df_agg, ["plastic-pack[t/t]", "paper-pack[t/t]", "aluminium-pack[t/t]",
                            "glass-pack[t/t]", "paper-print[t/t]", "paper-san[t/t]"])
cdm_pack = ConstantDataMatrix.create_from_constant(tmp, 1)
cdm_check = cdm_pack.group_all("Categories1",inplace=False)
df_check = cdm_check.write_df()

# put together
CDM_matdec = {
    "pack" : cdm_pack,
    "tra_veh" : cdm_tra_veh,
    "tra_infra" : cdm_tra_infra,
    "bld_floor" : cdm_bld_floor,
    "bld_pipe" : cdm_bld_pipe,
    "bld_domapp" : cdm_domapp,
    "fertilizer" : cdm_fert
    }

# rename
for key in CDM_matdec.keys():
    variabs = CDM_matdec[key].col_labels["Variables"]
    for v in variabs:
        CDM_matdec[key].rename_col(v, "material-decomp_" + v, "Variables")
    CDM_matdec[key] = CDM_matdec[key].flatten()
    CDM_matdec[key].deepen_twice()

# drop other
# note: in general we drop other as we do not have a general technology for other materials
# we could keep "other" and use it in industry module until the technology part, though we would need to adjust
# net import to add other raw materials ... we'll do it only if we decide
# to add a general tech for other at some point.
for key in CDM_matdec.keys():
    CDM_matdec[key].drop("Categories2","other")

# save
f = os.path.join(current_file_directory, '../data/datamatrix/const_material-decomposition.pickle')
with open(f, 'wb') as handle:
    pickle.dump(CDM_matdec, handle, protocol=pickle.HIGHEST_PROTOCOL)

# cdm_temp = CDM_matdec["bld_domapp"].copy()
# idx = cdm_temp.idx
# cdm_temp.array[cdm_temp.array == 0] = np.nan
# cdm_temp.write_df().columns



# =============================================================================
# ##################
# ##### EUCALC #####
# ##################
# 
# # get data
# filepath = os.path.join(current_file_directory, '../data/EUCalc/products_material_composition.xlsx')
# df = pd.read_excel(filepath)
# 
# # fix product names
# df.loc[:,"product"]
# name_old = ["Residential buildings [kg/m2 floor]", "Non-residential buildings [kg/m2 floor]",
#             "Insulation residential buildings [t/m2 wall]", "Insulation non- residential buildings [t/m2 wall]",
#             "District heating pipes [t/km]","Fridges [kg/num]", "Dishwashers [kg/num]",
#             "Washing machines [kg/num]", "Freezers [kg/num]", "Dryer [kg/num]",
#             "TV [kg/num]", "Smartphone [kg/num]", "Computer [kg/num]",
#             "ICE cars [t/num]", "ICE trucks [t/num]", "FCV cars [t/num]",
#             "FCV trucks [t/num]", "EV cars [t/num]", "EV trucks [t/num]",
#             "Ships [t/num]", "Trains [t/num]", "Planes [t/num]", "Road [t/km]",
#             "Rail [t/km]", "Trolley-cables [t/km]", "Fertilizer [t/t]",
#             "Plastic packaging [t/t]", "Paper packaging [t/t]", "Aluminium packaging [t/t]",
#             "Glass packaging [t/t]", "Paper printing and graphic [t/t]", 
#             "Paper sanitary and household [t/t]"]
# name_new = ["floor-area-new-residential[kg/m2]", "floor-area-new-non-residential[kg/m2]",
#             "floor-area-reno-residential[t/m2]", "floor-area-reno-non-residential[t/m2]",
#             "new-dhg-pipe[t/km]", "fridge[kg/num]", "dishwasher[kg/num]",
#             "wmachine[kg/num]", "freezer[kg/num]", "dryer[kg/num]",
#             "tv[kg/num]", "phone[kg/num]", "computer[kg/num]",
#             "cars-ICE[t/num]", "trucks-ICE[t/num]", "cars-FCV[t/num]",
#             "trucks-FCV[t/num]", "cars-EV[t/num]", "trucks-EV[t/num]",
#             "ships[t/num]", "trains[t/num]", "planes[t/num]", "road[t/km]",
#             "rail[t/km]", "trolly-cables[t/km]", "fertilizer[t/t]",
#             "plastic-pack[t/t]", "paper-pack[t/t]","aluminium-pack[t/t]",
#             "glass-pack[t/t]", "paper-print[t/t]", 
#             "paper-san[t/t]"]
# for i in range(0,len(name_old)):
#     df.loc[df["product"] == name_old[i],"product"] = name_new[i]
# 
# # fix columns
# df.rename(columns={"other chemicals" : "chem", "product" : "variable"}, inplace=True)
# 
# # melt
# indexes = ["variable"]
# df = pd.melt(df, id_vars = indexes, var_name='material')
# 
# # fix units
# df.loc[df["variable"] == "floor-area-new-residential[kg/m2]","value"] = \
#     df.loc[df["variable"] == "floor-area-new-residential[kg/m2]","value"] / 1000
# df.loc[df["variable"] == "floor-area-new-non-residential[kg/m2]","value"] = \
#     df.loc[df["variable"] == "floor-area-new-non-residential[kg/m2]","value"] / 1000
# df.loc[df["variable"] == "floor-area-new-residential[kg/m2]","variable"] = "floor-area-new-residential[t/m2]"
# df.loc[df["variable"] == "floor-area-new-non-residential[kg/m2]","variable"] = "floor-area-new-non-residential[t/m2]"
# ls_temp = ["fridge[kg/num]", "dishwasher[kg/num]", "wmachine[kg/num]", 
#            "freezer[kg/num]", "dryer[kg/num]", "tv[kg/num]", "phone[kg/num]", 
#            "computer[kg/num]"]
# ls_temp1 = ["fridge[t/num]", "dishwasher[t/num]", "wmachine[t/num]", 
#            "freezer[t/num]", "dryer[t/num]", "tv[t/num]", "phone[t/num]", 
#            "computer[t/num]"]
# for i in range(0, len(ls_temp)):
#     df.loc[df["variable"] == ls_temp[i],"value"] = \
#         df.loc[df["variable"] == ls_temp[i],"value"] / 1000
#     df.loc[df["variable"] == ls_temp[i],"variable"] = ls_temp1[i]
#     
# # drop other
# # note: in general we drop other as we do not have a general technology for other materials
# # we could keep "other" and use it in industry module until the technology part, though we would need to adjust
# # net import to add other raw materials ... we'll do it only if we decide
# # to add a general tech for other at some point.
# df = df.loc[df["material"] != "other",:]
# 
# # create dms
# def create_constant(df, variables):
#     
#     df_temp = df.loc[df["variable"].isin(variables),:]
# 
#     # rename variables
#     df_temp["variable"] = [v.split("[")[0] + "_" + m + "[" + v.split("[")[1] for v, m in zip(df_temp["variable"],df_temp["material"])]
#     df_temp.drop(["material"], axis=1, inplace=True)
#     
#     # put unit
#     df_temp["unit"] = [i.split("[")[1].split("]")[0] for i in df_temp["variable"]]
#     
#     const = {
#         'name': list(df_temp['variable']),
#         'value': list(df_temp['value']),
#         'idx': dict(zip(list(df_temp['variable']), range(len(df_temp['variable'])))),
#         'units': dict(zip(list(df_temp['variable']), list(df_temp['unit'])))
#     }
#     
#     # return
#     return const
# 
# # cdm_bld_floor
# tmp = create_constant(df, ["floor-area-new-residential[t/m2]", "floor-area-new-non-residential[t/m2]",
#                            "floor-area-reno-residential[t/m2]", "floor-area-reno-non-residential[t/m2]"])
# cdm_bld_floor = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_bld_pipe
# tmp = create_constant(df, ["new-dhg-pipe[t/km]"])
# cdm_bld_pipe = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_domapp
# tmp = create_constant(df, ["fridge[t/num]", "dishwasher[t/num]","wmachine[t/num]", 
#                            "freezer[t/num]", "dryer[t/num]", "tv[t/num]", 
#                            "phone[t/num]", "computer[t/num]"])
# cdm_domapp = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_tra_veh
# tmp = create_constant(df, ["cars-ICE[t/num]", "trucks-ICE[t/num]", "cars-FCV[t/num]",
#                            "ships[t/num]", "trains[t/num]", "planes[t/num]",
#                            "trucks-FCV[t/num]", "cars-EV[t/num]", "trucks-EV[t/num]"])
# cdm_tra_veh = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_tra_infra
# tmp = create_constant(df, ["road[t/km]", "rail[t/km]", "trolly-cables[t/km]"])
# cdm_tra_infra = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_fert
# tmp = create_constant(df, ["fertilizer[t/t]"])
# cdm_fert = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # cdm_lfs
# tmp = create_constant(df, ["plastic-pack[t/t]", "paper-pack[t/t]", "aluminium-pack[t/t]",
#                            "glass-pack[t/t]", "paper-print[t/t]", "paper-san[t/t]"])
# cdm_lfs = ConstantDataMatrix.create_from_constant(tmp, 1)
# 
# # put together
# CDM_matdec = {
#     "lfs" : cdm_lfs,
#     "tra_veh" : cdm_tra_veh,
#     "tra_infra" : cdm_tra_infra,
#     "bld_floor" : cdm_bld_floor,
#     "bld_pipe" : cdm_bld_pipe,
#     "bld_domapp" : cdm_domapp,
#     "fertilizer" : cdm_fert
#     }
# 
# # rename
# for key in CDM_matdec.keys():
#     variabs = CDM_matdec[key].col_labels["Variables"]
#     for v in variabs:
#         CDM_matdec[key].rename_col(v, "material-decomp_" + v, "Variables")
#     CDM_matdec[key] = CDM_matdec[key].flatten()
#     CDM_matdec[key].deepen_twice()
# 
# # save
# f = os.path.join(current_file_directory, '../data/datamatrix/const_material-decomposition.pickle')
# with open(f, 'wb') as handle:
#     pickle.dump(CDM_matdec, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# # cdm_temp = CDM_matdec["bld_domapp"].copy()
# # idx = cdm_temp.idx
# # cdm_temp.array[cdm_temp.array == 0] = np.nan
# # cdm_temp.write_df().columns
# =============================================================================