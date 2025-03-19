import numpy as np

import pandas as pd
import faostat
import os
import re
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from _database.pre_processing.api_routines_CH import get_data_api_CH
from model.common.auxiliary_functions import create_years_list, linear_fitting, filter_DM

import pickle
import json
import os
import numpy as np


def get_livestock_all(table_id, file, years_ots):
    try:
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
            print(f'The livestock units are read from file {file}. Delete it if you want to update data from api.')
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        i = 0
        # The table is too big to be downloaded at once
        filtering = {"Unité d'observation": ['Cheptel - Bovins', 'Cheptel - Equidés', 'Cheptel - Moutons',
                                             'Cheptel - Chèvres', 'Cheptel - Porcs', 'Cheptel - Volailles',
                                             'Cheptel - Autres animaux'],
                     'Canton': ['Vaud'],
                     'Zone de production agricole' : ['Zone de production agricole - total'],
                     'Classe de taille': ['Classe de taille - total'],
                     "Système d'exploitation": ["Système d'exploitation - total"],
                     "Forme d'exploitation": ["Forme d'exploitation - total"],
                     'Année': structure['Année']}

        mapping_dim = {'Country': 'Canton',
                       'Years': 'Année',
                       'Variables': 'Zone de production agricole',
                       'Categories1': "Unité d'observation"}

        # Extract new fleet
        dm = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                             units=['lsu'], language='fr')
        dm.rename_col('Zone de production agricole - total', 'agr_livestock', 'Variables')
        dm.rename_col_regex('Cheptel - ', '', dim='Categories1')
        dict_cat = {'bovine': ['Bovins'], 'sheep': ['Moutons'], 'pig': ['Porcs'],
                    'poultry': ['Volailles'], 'oth-animals': ['Equidés', 'Chèvres', 'Autres animaux']}
        dm.groupby(dict_cat, dim='Categories1', inplace=True)
        dm.sort('Years')
        dm.filter({'Years': years_ots}, inplace=True)

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    dm = linear_fitting(dm, years_ots)
    return dm


def get_livestock_dairy_egg(table_id, file, years_ots):
    try:
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
            print(f'The livestock units are read from file {file}. Delete it if you want to update data from api.')
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # The table is too big to be downloaded at once
        filtering = {"Unité d'observation": ['Cheptel - Vaches laitières', 'Cheptel - Brebis laitières',
                                             'Cheptel - Chèvres laitières', "Cheptel - Poules de ponte et d'élevage"],
                     'Canton': ['Vaud'],
                     'Zone de production agricole': ['Zone de production agricole - total'],
                     "Système d'exploitation": ["Système d'exploitation - total"],
                     "Forme d'exploitation": ["Forme d'exploitation - total"],
                     'Année': structure['Année']}

        mapping_dim = {'Country': 'Canton',
                       'Years': 'Année',
                       'Variables': 'Zone de production agricole',
                       'Categories1': "Unité d'observation"}

        # Extract new fleet
        dm = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                             units=['lsu'], language='fr')
        dm.rename_col('Zone de production agricole - total', 'agr_livestock-dairy-egg', 'Variables')
        dm.rename_col_regex('Cheptel - ', '', dim='Categories1')
        dict_cat = {'bovine': ['Vaches laitières'], 'sheep': ['Brebis laitières'], 'oth-animals': ['Chèvres laitières'],
                    'poultry': ["Poules de ponte et d'élevage"]}
        dm.groupby(dict_cat, dim='Categories1', inplace=True)
        dm.sort('Years')
        dm.filter({'Years': years_ots}, inplace=True)

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    dm.array[dm.array == 0] = np.nan
    dm = linear_fitting(dm, years_ots)
    return dm


def compute_livestock(dm_all, dm_dairy_egg):
    missing_cat = list(set(dm_all.col_labels['Categories1']) - set(dm_dairy_egg.col_labels['Categories1']))

    dm_meat = dm_all.filter({'Categories1': dm_dairy_egg.col_labels['Categories1']})
    dm_meat.append(dm_dairy_egg, dim='Variables')
    dm_meat.operation('agr_livestock', '-', 'agr_livestock-dairy-egg', out_col='agr_livestock-meat', unit='lsu')
    dm_meat.filter({'Variables': ['agr_livestock-meat']}, inplace=True)

    dm_meat_other = dm_all.filter({'Categories1': missing_cat})
    dm_meat_other.rename_col('agr_livestock', 'agr_livestock-meat', dim='Variables')

    dm_meat.append(dm_meat_other, dim='Categories1')
    dm_meat.sort('Categories1')

    # add 'meat-' to categories
    for cat in dm_meat.col_labels['Categories1']:
        dm_meat.rename_col(cat, 'meat-'+cat, dim='Categories1')

    dm_meat.rename_col('agr_livestock-meat', 'agr_livestock', dim='Variables')

    dm_dairy_egg.groupby({'abp-dairy-milk': ['bovine', 'oth-animals', 'sheep'], 'abp-hens-egg': ['poultry']},
                         dim='Categories1', inplace=True)
    dm_dairy_egg.rename_col('agr_livestock-dairy-egg', 'agr_livestock', 'Variables')
    dm_lsu = dm_meat
    dm_lsu.append(dm_dairy_egg, dim='Categories1')
    dm_lsu.sort('Categories1')

    return dm_lsu


def get_crop_prod(table_id, file, years_ots):
    try:
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
            print(f'The livestock units are read from file {file}. Delete it if you want to update data from api.')
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # The table is too big to be downloaded at once
        filtering = {"Unité d'observation": structure["Unité d'observation"],
                     'Canton': ['Vaud'],
                     'Zone de production agricole': ['Zone de production agricole - total'],
                     "Système d'exploitation": ["Système d'exploitation - total"],
                     "Forme d'exploitation": ["Forme d'exploitation - total"],
                     'Année': structure['Année']}
        mapping_dim = {'Country': 'Canton',
                       'Years': 'Année',
                       'Variables': 'Zone de production agricole',
                       'Categories1': "Unité d'observation"}
        dm = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                             units=['ha'], language='fr')
        dm.drop(dim='Categories1', col_label=['Exploitations', 'SAU - Total (en ha)'])
        dm.rename_col_regex('SAU - ', '', dim='Categories1')
        dm.rename_col_regex(' (en ha)', '', dim='Categories1')

        cat_map = {
            "crop-cereal": ["Blé", "Orge", "Avoine", "Seigle", "Triticale", "Epeautre", 'Céréales en général',
                            "Méteil et autres céréales panifiables", "Maïs grain", 'Autres céréales', "Maïs d'ensilage et maïs vert"],
            "crop-fruit": ["Baies annuelles", "Cultures de baies sous abri", 'Cultures fruitières en général', 'Pommes',
                           'Poires', 'Fruits à noyaux', 'Baies pluriannuelles'],
            "crop-oilcrop": ["Colza pour matière première renouvelable", "Tournesol pour matière première renouvelable",
                             "Lin", "Chanvre", 'Colza pour huile comestible', 'Tournesol pour huile comestible',
                             'Courge à huile'],
            "crop-pulse": ['Pois protéagineux', 'Féveroles', 'Légumineuses en général', 'Lupin fourrager', "Soja"],
            "crop-starch": ["Pommes de terre"],
            "crop-sugarcrop": ["Betteraves sucrières"],
            "crop-veg": ["Cultures maraîchères de plein champ", "Cultures maraîchères sous abri", "Asperges",
                         "Rhubarbe"],
            "pro-bev-beer": ["Houblon"],
            "pro-bev-wine": ["Vigne"],
            "remove": ["Plantes aromatiques et médicinales annuelles", "Plantes aromatiques et médicinales pluriannuelles",
                       "Arbrisseaux ornementaux", "Sapins de Noël", "Pépinières forestières hors forêt sur SAU",
                       "Autres pépinières", "Prairies artificielles", "Pâturages", "Prairies extensives", "Prairies peu intensives",
                        "Prairies dans la région d'estivage", "Autres prairies permanentes",
                       "Surfaces à litières", "Haies, bosquets champêtres et berges boisées", "Betteraves fourragères",
                       "Matières premières renouvelables annuelles", "Matières premières renouvelables pluriannuelles",
                       "Autres SAU", "Tabac", "Jachère", "Autres terres ouvertes", 'Méteil et autres céréales fourragères'],
            "other": ["Cultures horticoles de plein champ annuelles",
                      "Cultures horticoles sous abri", "Autres cultures pérennes",
                      "Autres cultures sous abri", "Cultures sous abri en général"]
        }
        # FIXME: Where should bettreve fourrageres go ?
        dm.groupby(cat_map, dim='Categories1', inplace=True)
        dm.drop(dim='Categories1', col_label=['remove'])
        dm.rename_col('Zone de production agricole - total', 'agr_land-use', dim='Variables')

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    linear_fitting(dm, years_ots)
    dm.filter({'Years': years_ots}, inplace=True)
    return dm


def compute_wine_production(dm_crop_wine, wine_hl, conversion_hl_to_kcal):
    years_wine = list(wine_hl.keys())
    years_wine.sort()
    arr_wine = [wine_hl[yr] for yr in years_wine]
    arr_wine = np.array(arr_wine)
    dm_wine = DataMatrix(col_labels={'Country': ['Vaud'], 'Years': years_wine, 'Variables': ['agr_production'],
                                     'Categories1': ['pro-bev-wine']}, units={'agr_production': 'hl'})
    dm_shape = tuple([len(dm_wine.col_labels[dim]) for dim in dm_wine.dim_labels])
    dm_wine.array = np.zeros(shape=dm_shape)
    dm_wine.array[0, :, 0, 0] = arr_wine
    missing_years = list(set(years_ots) - set(dm_wine.col_labels['Years']))
    dm_wine.add(np.nan, dummy=True, dim='Years', col_label=missing_years)

    dm_crop_wine.append(dm_wine, dim='Variables')
    dm_crop_wine.operation('agr_production', '/', 'agr_land-use', out_col='agr_climate-smart-crop_yield', unit='hl/ha')
    dm_crop_wine.drop(col_label='agr_production', dim='Variables')
    dm_crop_wine.fill_nans('Years')
    dm_crop_wine.operation('agr_land-use', '*', 'agr_climate-smart-crop_yield', out_col='agr_production', unit='hl')
    # Wine calories
    # https://www.calories.info/food/wine ( avg 80 Calories/100 gr = 80 kcal/100 gr = 800 kcal/l -> 80'000 kcal/hl )
    # FIXME you are here
    dm_crop_wine.change_unit('agr_production_adj', old_unit='hl', new_unit='kcal', factor=conversion_hl_to_kcal)

    return dm_crop_wine


years_ots = create_years_list(1990, 2023, 1)
years_fts = create_years_list(2025, 2050, 5)


# Population
data_file = '../../data/datamatrix/lifestyles.pickle'
with open(data_file, 'rb') as handle:
    DM_lfs = pickle.load(handle)
dm_pop = DM_lfs['ots']['pop']['lfs_population_']

# Load Agriculture pickle to read Switzerland data
data_file = '../../data/datamatrix/agriculture.pickle'
with open(data_file, 'rb') as handle:
    DM_agriculture = pickle.load(handle)
filter_DM(DM_agriculture, {'Country': ['Switzerland']})

#dm_kcal = DM_agriculture['ots']['kcal-req']
#linear_fitting(dm_kcal, years_ots)
#linear_fitting(dm_kcal, years_fts)

# Section: Production - Animals
# All livestock
table_id = 'px-x-0702000000_101'
file = 'data/agr_livestock_all.pickle'
dm_lsu_meat = get_livestock_all(table_id, file, years_ots)
# Dairy livestock
table_id = 'px-x-0702000000_108'
file = 'data/agr_livestock_dairy_egg.pickle'
dm_lsu_dairy_egg = get_livestock_dairy_egg(table_id, file, years_ots)
# All livestock (meat, dairy, egg)
dm_lsu = compute_livestock(dm_lsu_meat, dm_lsu_dairy_egg)

# Multiply dm_lsu by yield to obtain total kcal produced
dm_yield = DM_agriculture['ots']['climate-smart-livestock']['climate-smart-livestock_yield'].filter({'Country': ['Switzerland']})
dm_yield.rename_col('Switzerland', 'Vaud', 'Country')
if 'meat-oth-animals' not in dm_yield.col_labels['Categories1']:
    idx = dm_yield.idx
    arr_poultry = dm_yield.array[:, :, :, idx['meat-poultry']]
    dm_yield.add(arr_poultry, dim='Categories1', col_label=['meat-oth-animals'])
linear_fitting(dm_yield, years_ots)

# Production
dm_lsu.append(dm_yield, dim='Variables')
dm_lsu.operation('agr_livestock', '*', 'agr_climate-smart-livestock_yield', out_col='agr_production', unit='kcal')

# Section: Production - Crop & Co
table_id = 'px-x-0702000000_106'
file = 'data/agr_crop_prod.pickle'
# Production in ha
dm_crop_prod = get_crop_prod(table_id, file, years_ots)
# Production in kcal = Production in ha x yield in kcal/ha
dm_yield = DM_agriculture['ots']['climate-smart-crop']['climate-smart-crop_yield'].filter({'Country': ['Switzerland']})
dm_yield.rename_col('Switzerland', 'Vaud', dim='Country')
linear_fitting(dm_yield, years_ots)
dm_crop_only = dm_crop_prod.filter_w_regex({'Categories1': 'crop-.*'}, inplace=False)
dm_crop_only.rename_col_regex('crop-', '', dim='Categories1')
dm_crop_only.drop(col_label='stm', dim='Categories1')
dm_yield_crop = dm_yield.filter({'Categories1': dm_crop_only.col_labels['Categories1']}, inplace=False)
dm_crop_only.append(dm_yield_crop, dim='Variables')
dm_crop_only.operation('agr_land-use', '*', 'agr_climate-smart-crop_yield', out_col='agr_production', unit='kcal')

# Wine production
# The Federal Office of Agriculture, report the hl of wine produced and the ha of land dedicated to vineyards.
# https://www.blw.admin.ch/fr/vin
# the reports are available for every year, and every canton, in pdf format. The values from 2021 to 2024
wine_hl_VD = {2015: 218026, 2019: 278474,  2020: 237740, 2021: 191463, 2022: 273762, 2023: 287379} #2024: 230916}
conversion_hl_to_kcal = 80000  # one hl of wine is 80'000 kcal
dm_crop_wine = dm_crop_prod.filter({'Categories1': ['pro-bev-wine']}, inplace=False)
dm_crop_wine = compute_wine_production(dm_crop_wine, wine_hl_VD, conversion_hl_to_kcal)

# Beer production
# Since the cultivation of hop is small in Vaud and no data could be found on beer production we use crop-cereal
dm_crop_beer = dm_crop_prod.filter({'Categories1': ['pro-bev-beer']}, inplace=False)
dm_yield_beer = dm_yield.filter({'Categories1': ['cereal']}, inplace=False)
dm_yield_beer.rename_col('cereal', 'pro-bev-beer', 'Catego')
# Section: Supply
# Compute supply = Demand + Waste
# Demand = append( Consumer-diet,  )
# Consumer-diet-other = ( kcal-req - sum(Consumer-diet) )*Share
# Share
dm_share = DM_agriculture['ots']['diet']['share'].normalise('Categories1', inplace=False)
linear_fitting(dm_share, years_ots)
# Consumer-diet
dm_diet = DM_agriculture['ots']['diet']['lfs_consumers-diet']
linear_fitting(dm_diet, years_ots)
# kcal-req
dm_kcal_req = DM_agriculture['ots']['kcal-req'].groupby({'lfs_kcal-req': '.*'}, regex=True, inplace=False, dim='Variables')
linear_fitting(dm_kcal_req, years_ots)

#  Consumer-diet-other = ( kcal-req - sum(Consumer-diet) )*Share
dm_tot_diet = dm_diet.group_all('Categories1', inplace=False)
arr_kcal_other = (dm_kcal_req.array[:, :, :, np.newaxis] - dm_tot_diet.array[:, :, :, np.newaxis])*dm_share.array[:, :, :, :]
dm_share.add(arr_kcal_other, dim='Variables', col_label=['lfs_consumers-diet'], unit=['kcal/cap/day'])
dm_diet_other = dm_share.filter({'Variables': ['lfs_consumers-diet']})

# Demand = append( Consumer-diet, Consumer-diet-other )
dm_diet.append(dm_diet_other, 'Categories1')

# Supply = Waste + Demand
dm_waste = DM_agriculture['ots']['fwaste']
linear_fitting(dm_waste, years_ots)
dm_supply = dm_waste
dm_supply.append(dm_diet, dim='Variables')
dm_supply.operation('lfs_consumers-food-wastes', '+', 'lfs_consumers-diet', out_col='lfs_supply', unit='kcal/cap/day')

# Net-import = Production/Suppy ( = production/(production + import - export))
dm_supply.change_unit('lfs_supply', old_unit='kcal/cap/day', new_unit='kcal/cap', factor=365)


print('Hello')
