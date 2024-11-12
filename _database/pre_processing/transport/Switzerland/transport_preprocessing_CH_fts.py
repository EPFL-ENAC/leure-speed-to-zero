import pickle
import numpy as np
import pandas as pd
from model.common.auxiliary_functions import linear_fitting
#from IPython.display import display

data_file = r"C:\\Users\\simon\Documents\\projet_MA3\\PathwayCalc\\_database\\data\\datamatrix\transport_CH_VD.pickle"
with open(data_file, 'rb') as handle:
    DM_transport = pickle.load(handle)

# ======================  MODAL_SHARE  ========================================================

dm_modal_share_2 = DM_transport['fts']['passenger_modal-share'][2].copy()
dm_modal_share_ots = DM_transport['ots']['passenger_modal-share']

#Scénario 1: BAU
#dm_modal_share_trend_bau = dm_modal_share_ots.copy()
#dm_modal_share_trend_bau.append(dm_modal_share_1, dim ='Years')
#dm_modal_share_trend.flatten().datamatrix_plot()

#Scénario 2: PCV
idx = dm_modal_share_ots.idx
#Calcul coefficient 2050 selon OTS
CITEC_prop_TP = 0.38 #(Source: vision 2050)
CITEC_prop_TIM = 0.55 #(Source: vision 2050)
CITEC_prop_MA = 0.07 #(Source: vision 2050)
prop_2W_LDV = (( dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['2W']] ) /
               (dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['LDV']] +
                dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['2W']] ))
modal_share_2050_LDV = (1-prop_2W_LDV)*CITEC_prop_TIM
modal_share_2050_2W = (prop_2W_LDV)*CITEC_prop_TIM

prop_walk_bike = (( dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['walk']] ) /
                  (dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['walk']] +
                   dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['bike']] ))
modal_share_2050_bike = (1-prop_walk_bike)*CITEC_prop_MA
modal_share_2050_walk = (prop_walk_bike)*CITEC_prop_MA

denominator_TP = (dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['rail']] +
                 dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['metrotram']] +
                 dm_modal_share_ots.array[idx['Vaud'], idx[2015], idx['tra_passenger_modal-share'], idx['bus']])
prop_rail_TP = ( dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['rail']] ) / denominator_TP
prop_bus_TP = ( dm_modal_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_modal-share'], idx['bus']] ) / denominator_TP
modal_share_2050_rail = (prop_rail_TP)*CITEC_prop_TP
modal_share_2050_metrotram = (1 - prop_rail_TP - prop_bus_TP)*CITEC_prop_TP
modal_share_2050_bus = (prop_bus_TP)*CITEC_prop_TP

idx = dm_modal_share_2.idx
values_2050 = {'rail': modal_share_2050_rail, 'metrotram': modal_share_2050_metrotram, 'bus': modal_share_2050_bus, 'walk': modal_share_2050_walk, 'bike': modal_share_2050_bike, 'LDV': modal_share_2050_LDV, '2W': modal_share_2050_2W}
for key,values in values_2050.items():
    dm_modal_share_2.array[idx['Vaud'], idx[2050], idx['tra_passenger_modal-share'], idx[key]] = values

values_2030 = {'rail': 0.25, 'metrotram': 0.02, 'bus':0.03, 'walk': 0.05, 'bike': 0.03, 'LDV': 0.6, '2W':0.03} #Source: PCV
for key,values in values_2030.items():
    dm_modal_share_2.array[idx['Vaud'], idx[2030], idx['tra_passenger_modal-share'], idx[key]] = values

#choisir entre linear_fitting et fill_nans
#dm_modal_share_2.fill_nans(dim_to_interp='Years')
linear_fitting(dm_modal_share_2, dm_modal_share_2.col_labels['Years'])
dm_modal_share_2.normalise(dim='Categories1', inplace=True)

dm_modal_share_PCV = dm_modal_share_ots.copy()
dm_modal_share_PCV.append(dm_modal_share_2, dim ='Years')
#dm_modal_share_PCV.flatten().datamatrix_plot()

DM_transport['fts']['passenger_modal-share'][2] = dm_modal_share_2

# ======================  OCCUPANCY  ========================================================
dm_occupancy_2 = DM_transport['fts']['passenger_occupancy'][2].copy()
dm_occupancy_ots = DM_transport['ots']['passenger_occupancy']

#BAU
#dm_occupancy_1 = DM_transport['fts']['passenger_occupancy'][1]
#dm_occupancy_trend = dm_occupancy_ots.copy()
#dm_occupancy_trend.append(dm_occupancy_1, dim ='Years')
#dm_occupancy_trend.flatten().datamatrix_plot()

#Scénario PCV:
idx = dm_occupancy_2.idx
dm_occupancy_2.array[idx['Vaud'], idx[2030]:, idx['tra_passenger_occupancy'], :] = np.nan
array_PCV_occupancy = dm_occupancy_2.array

dm_occupancy_2.array[idx['Vaud'], idx[2030], idx['tra_passenger_occupancy'], idx['LDV']] = 1.9

dm_occupancy_2.fill_nans(dim_to_interp='Years')
dm_occupancy_trend_PCV = dm_occupancy_ots.copy()
dm_occupancy_trend_PCV.append(dm_occupancy_2, dim ='Years')
#dm_occupancy_trend_PCV.flatten().datamatrix_plot()

DM_transport['fts']['passenger_occupancy'][2] = dm_occupancy_2

# ======================  NEW FUEL EFF  ========================================================

dm_new_eff_2 = DM_transport['fts']['passenger_veh-efficiency_new'][2]
dm_new_eff_ots = DM_transport['ots']['passenger_veh-efficiency_new']
dm_new_eff_trend = dm_new_eff_ots.copy()

#BAU
#dm_new_eff_1 = DM_transport['fts']['passenger_veh-efficiency_new'][1]
#dm_new_eff_trend.append(dm_new_eff_1, dim ='Years')
#dm_new_eff_trend.flatten().datamatrix_plot()

idx = dm_new_eff_ots.idx
efficiency_LDV_2023_BEV = dm_new_eff_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['BEV']]
efficiency_LDV_2023_diesel = dm_new_eff_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['ICE-diesel']]
efficiency_LDV_2023_gasoline = dm_new_eff_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['ICE-gasoline']]
efficiency_LDV_2023_PHEV_diesel = dm_new_eff_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['PHEV-diesel']]
efficiency_LDV_2023_PHEV_gasoline = dm_new_eff_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['PHEV-gasoline']]

#efficiency_LDV_2023 = dm_new_eff_ots.array[idx['Vaud'], idx[2022], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], :]
print(efficiency_LDV_2023_BEV, efficiency_LDV_2023_diesel, efficiency_LDV_2023_gasoline, efficiency_LDV_2023_PHEV_diesel, efficiency_LDV_2023_PHEV_gasoline)
reduction_2035_thermique = (2035-2022)/(2050-2022)*0.39
reduction_2035_electrique = (2035-2022)/(2050-2022)*0.13

efficiency_LDV_2035_BEV_modèle = reduction_2035_electrique*efficiency_LDV_2023_BEV
efficiency_LDV_2035_diesel_modèle = reduction_2035_thermique * efficiency_LDV_2023_diesel
efficiency_LDV_2035_gasoline_modèle = reduction_2035_thermique * efficiency_LDV_2023_gasoline
efficiency_LDV_2035_PHEV_diesel_modèle = reduction_2035_thermique * efficiency_LDV_2023_PHEV_diesel
efficiency_LDV_2035_PHEV_gasoline_modèle = reduction_2035_thermique * efficiency_LDV_2023_PHEV_gasoline

efficiency_LDV_2021_BEV = dm_new_eff_ots.array[idx['Vaud'], idx[2021], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['BEV']]
efficiency_LDV_2021_diesel = dm_new_eff_ots.array[idx['Vaud'], idx[2021], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['ICE-diesel']]
efficiency_LDV_2021_gasoline = dm_new_eff_ots.array[idx['Vaud'], idx[2021], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['ICE-gasoline']]
efficiency_LDV_2021_PHEV_diesel = dm_new_eff_ots.array[idx['Vaud'], idx[2021], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['PHEV-diesel']]
efficiency_LDV_2021_PHEV_gasoline = dm_new_eff_ots.array[idx['Vaud'], idx[2021], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], idx['PHEV-gasoline']]

#PCV
dm_new_eff_2.filter({'Categories1': ['LDV']}, inplace = True)
array_PCV_new_eff = dm_new_eff_2.array
idx = dm_new_eff_2.idx

#values_2030_new_eff = {'BEV': 0,47, 'CEV': nan, 'FCEV': 1.8, 'ICE':nan, 'ICE-diesel': 0.74, 'ICE-gas': nan, 'ICE-gasoline': 0.87, 'PHEV': nan, 'PHEV-diesel': nan, 'PHEV-gasoline':nan, 'mt':nan}

#for key,values in values_2030_new_eff.items():
#    dm_new_eff_2.array[idx['Vaud'], idx[2030], idx['tra_passenger_occupancy'], idx[key]] = values

# écraser DM_transport['fts']['passenger_veh-efficiency_new'][2]

# ======================  NEW SALES VEHICLES  ========================================================    #dm_new_tech_share_2.filter({'Categories1': ['LDV']}, inplace = True)
dm_new_tech_share_1 = DM_transport['fts']['passenger_technology-share_new'][1]
dm_new_tech_share_2 = DM_transport['fts']['passenger_technology-share_new'][2].copy()
dm_new_tech_share_ots = DM_transport['ots']['passenger_technology-share_new']
dm_new_tech_share_trend = dm_new_tech_share_ots.copy()
dm_new_tech_share_trend.append(dm_new_tech_share_1, dim ='Years')
#dm_new_tech_share_trend.flatten().datamatrix_plot()

array_PCV_new_tech_share = dm_new_tech_share_2.array
idx = dm_new_tech_share_ots.idx

prop_EV_PHEV_2035_PCV = 0.5
prop_FCEV_2035_PCV = 0.00
prop_ICE_2035_PCV = 0.5

denominator_EV_PHEV = ( dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['BEV']] +
                      dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['PHEV-gasoline']] +
                      dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['PHEV-diesel']] )
prop_BEV_EV_2023 = dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['BEV']] / denominator_EV_PHEV
prop_PHEV_diesel_EV_2023 = dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['PHEV-diesel']] / denominator_EV_PHEV
prop_PHEV_gasoline_EV_2023 = dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['PHEV-gasoline']] / denominator_EV_PHEV
print(( dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['PHEV-gasoline']] ) )
prop_gasoline_ICE_2023 = ( dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['ICE-gasoline']]  /
                          ( dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['ICE-gasoline']] +
                            dm_new_tech_share_ots.array[idx['Vaud'], idx[2023], idx['tra_passenger_technology-share_new'], idx['LDV'], idx['ICE-diesel']] ) )
prop_diesel_ICE_2023 = 1 - prop_gasoline_ICE_2023

idx = dm_new_tech_share_2.idx
dm_new_tech_share_2.array[idx['Vaud'], :, idx['tra_passenger_technology-share_new'], :] = np.nan

prop_BEV_2035_PCV = prop_EV_PHEV_2035_PCV*prop_BEV_EV_2023
prop_PHEV_diesel_2035_PCV = prop_EV_PHEV_2035_PCV * prop_PHEV_diesel_EV_2023
prop_PHEV_gasoline_2035_PCV = prop_EV_PHEV_2035_PCV * prop_PHEV_gasoline_EV_2023
prop_diesel_ICE_2035_PCV = prop_ICE_2035_PCV * prop_diesel_ICE_2023
prop_gasoline_ICE_2035_PCV = prop_ICE_2035_PCV * prop_gasoline_ICE_2023
values_2035_new_tech_share = {'BEV': prop_BEV_2035_PCV, 'ICE-diesel': prop_diesel_ICE_2035_PCV, 'ICE-gasoline': prop_gasoline_ICE_2035_PCV, 'PHEV-diesel': prop_PHEV_diesel_2035_PCV, 'PHEV-gasoline': prop_PHEV_gasoline_2035_PCV}

for key,values in values_2035_new_tech_share.items():
    dm_new_tech_share_2.array[idx['Vaud'], idx[2035], idx['tra_passenger_technology-share_new'], idx['LDV'], idx[key]] = values

dm_new_tech_share_trend_PCV = dm_new_tech_share_ots.copy()
linear_fitting(dm_new_tech_share_2, dm_new_tech_share_2.col_labels['Years'])
dm_new_tech_share_2.normalise(dim='Categories2', inplace=True)
dm_new_tech_share_trend_PCV.append(dm_new_tech_share_2, dim = 'Years')
#dm_new_tech_share_trend_PCV.fill_nans(dim_to_interp='Years')
dm_new_tech_share_trend_PCV.normalise(dim='Categories2', inplace=True)
dm_new_tech_share_trend_PCV.flatten().datamatrix_plot()

DM_transport['fts']['passenger_technology-share_new'][2] = dm_new_tech_share_2

# # ======================  MESURE 5  ======================================================== (CALCULER LES EMISSIONS MOYENNES DU NOUVEAU PARC EN 2021)
categories_transport =['BEV', 'CEV', 'FCEV', 'ICE-diesel', 'ICE-gas', 'ICE-gasoline', 'PHEV-diesel', 'PHEV-gasoline', 'mt']
df_emissions_moyennes_2035 = pd.DataFrame(index= categories_transport)

idx = dm_new_eff_ots.idx
facteurs_emission_2018 = dm_new_eff_ots.array[idx['Vaud'], idx[2018], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], :]
df_emissions_moyennes_2035['facteurs 2018'] = facteurs_emission_2018

idx = dm_new_tech_share_ots.idx
market_shares_2018 = dm_new_tech_share_ots.array[idx['Vaud'], idx[2018], idx['tra_passenger_technology-share_new'], idx['LDV'], :]
df_emissions_moyennes_2035['part de marché 2018'] = market_shares_2018

idx = dm_new_eff_2.idx
facteurs_emission_2035 = dm_new_eff_2.array[idx['Vaud'], idx[2035], idx['tra_passenger_veh-efficiency_new'], idx['LDV'], :]
df_emissions_moyennes_2035['facteurs 2035'] = facteurs_emission_2035

idx = dm_new_tech_share_2.idx
market_shares_2035 = dm_new_tech_share_2.array[idx['Vaud'], idx[2035], idx['tra_passenger_technology-share_new'], idx['LDV'], :]
df_emissions_moyennes_2035['part de marché 2035'] = market_shares_2035
pd.set_option('display.max_columns', 10)
df_emissions_moyennes_2035.drop('ICE-gas', inplace = True)
df_emissions_moyennes_2035.drop('FCEV', inplace = True)
df_emissions_moyennes_2035.drop('CEV', inplace = True)
df_emissions_moyennes_2035.drop('mt', inplace = True)

emissions_moyennes_2018 = (df_emissions_moyennes_2035['facteurs 2018']*df_emissions_moyennes_2035['part de marché 2018']).sum()
emissions_moyennes_2035 = (df_emissions_moyennes_2035['facteurs 2035']*df_emissions_moyennes_2035['part de marché 2035']).sum()

#Prendre en compte l'amélioration de l'efficacité:
df_emissions_moyennes_2035['facteurs 2035_efficacité'] = np.nan
facteur_amelioration_BEV_2035 = 1 - 0.13*(2035-2022)/(2050-2022)
facteur_amelioration_ICE_2035 = 1 - 0.39*(2035-2022)/(2050-2022)
df_emissions_moyennes_2035.at['BEV', 'facteurs 2035_efficacité'] = facteur_amelioration_BEV_2035 * df_emissions_moyennes_2035.at['BEV', 'facteurs 2018']
df_emissions_moyennes_2035.at['ICE-diesel', 'facteurs 2035_efficacité'] = facteur_amelioration_BEV_2035 * df_emissions_moyennes_2035.at['ICE-diesel', 'facteurs 2018']
df_emissions_moyennes_2035.at['PHEV-diesel', 'facteurs 2035_efficacité'] = facteur_amelioration_BEV_2035 * df_emissions_moyennes_2035.at['PHEV-diesel', 'facteurs 2018']
df_emissions_moyennes_2035.at['ICE-gasoline', 'facteurs 2035_efficacité'] = facteur_amelioration_BEV_2035 * df_emissions_moyennes_2035.at['ICE-gasoline', 'facteurs 2018']
df_emissions_moyennes_2035.at['PHEV-gasoline', 'facteurs 2035_efficacité'] = facteur_amelioration_BEV_2035 * df_emissions_moyennes_2035.at['PHEV-gasoline', 'facteurs 2018']
print(df_emissions_moyennes_2035)

ratio_2021_2035 = emissions_moyennes_2035/ emissions_moyennes_2018
if ratio_2021_2035 > 0.6:
    print("le ratio est de: " + str(round(ratio_2021_2035, 2)) + " la mesure 5 n'est pas remplie")
else:
    print("le ratio est de: " + str(round(ratio_2021_2035, 2)) + " la mesure 5 est remplie")

emissions_moyennes_2035_effiacité = (df_emissions_moyennes_2035['facteurs 2035_efficacité']*df_emissions_moyennes_2035['part de marché 2035']).sum()
ratio_2021_2035_efficacite = emissions_moyennes_2035_effiacité / emissions_moyennes_2018
if ratio_2021_2035_efficacite > 0.6:
    print("le ratio efficacité est de: " + str(round(ratio_2021_2035_efficacite, 2)) + " la mesure 5 n'est pas remplie")
else:
    print("le ratio efficacité est de: " + str(round(ratio_2021_2035_efficacite, 2)) + " la mesure 5 est remplie")

print("fin du code")