import numpy as np

import pandas as pd
import faostat
import os
import re
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from _database.pre_processing.api_routines_CH import get_data_api_CH
from model.common.auxiliary_functions import create_years_list, linear_fitting

import pickle
import json
import os
import numpy as np


def get_livestock_all(table_id, file, years_ots):
    # New fleet data are heavy, download them only once
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
    # New fleet data are heavy, download them only once
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


years_ots = create_years_list(1990, 2023, 1)
years_fts = create_years_list(2025, 2050, 5)

data_file = '../../data/datamatrix/agriculture.pickle'
with open(data_file, 'rb') as handle:
    DM_agriculture = pickle.load(handle)

# Section: Food Net-Import (=prod/demand) - Animals
# All livestock
table_id = 'px-x-0702000000_101'
file = 'data/agr_livestock_all.pickle'
dm_lsu_all = get_livestock_all(table_id, file, years_ots)
# Dairy livestock
table_id = 'px-x-0702000000_108'
file = 'data/agr_livestock_dairy_egg.pickle'
dm_lsu_dairy_egg = get_livestock_dairy_egg(table_id, file, years_ots)
# Meat livestock
dm_lsu = compute_livestock(dm_lsu_all, dm_lsu_dairy_egg)

# Multiply dm_lsu by yield to obtain total kcal produced
dm_yield = DM_agriculture['ots']['climate-smart-livestock']['climate-smart-livestock_yield'].filter({'Country': ['Switzerland']})

dm_lsu.append(dm_yield, dim='Variables')
dm_lsu.operation('agr_livestock', '*', 'agr_climate-smart-livestock_yield', out_col='agr_production', unit='kcal')


print('Hello')
