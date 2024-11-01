import numpy as np
import pandas as pd
import pickle


from model.common.auxiliary_functions import moving_average, linear_fitting, create_years_list
from model.common.io_database import update_database_from_dm, csv_database_reformat, read_database_to_dm
from _database.pre_processing.api_routines_CH import get_data_api_CH
from model.common.data_matrix_class import DataMatrix

import math
import requests

from _database.pre_processing.WorldBank_data_extract import get_WB_data

import os


def compute_new_area_transformed(dm_floor_area, years_ots, cat_map):

    dm = dm_floor_area.copy()
    # removing 2010 value because it is off
    dm.array[:, 0, ...] = np.nan
    linear_fitting(dm, dm.col_labels['Years'])

    dm.lag_variable('bld_floor-area_stock', shift=1, subfix='_tm1')
    dm.operation('bld_floor-area_stock', '-', 'bld_floor-area_stock_tm1', out_col='bld_floor-area_transformed', unit='m2')

    idx = dm.idx
    dm.array[:, 0, idx['bld_floor-area_transformed'], ...] = np.nan

    # Remove negative values
    dm.array[:, :, idx['bld_floor-area_transformed'], ...] \
        = np.maximum(dm.array[:, :, idx['bld_floor-area_transformed'], ...], 0)

    dm.filter({'Variables': ['bld_floor-area_transformed']}, inplace=True)

    construction_period = ['2016-2020', '2021-2023', '2011-2015']
    idx = dm.idx
    for period in construction_period:
        y0 = dm.col_labels['Years'][0]
        end_yr = int(period.split('-')[1])
        for yr in range(y0, end_yr+1):
            if yr in dm.col_labels['Years']:
                dm.array[:, idx[yr], :, :, idx[period]] = 0

    # Fill in previous years with mean values
    arr_mean = np.nanmean(dm.array[...], axis=1)

    years_missing = list(set(years_ots) - set(dm.col_labels['Years']))
    dm.add(0, col_label=years_missing, dummy=True, dim='Years')
    dm.sort('Years')
    idx = dm.idx
    for yr in years_missing:
        dm.array[:, idx[yr], :, :, :] = arr_mean

    dm.fill_nans(dim_to_interp='Years')

    construction_period = ['2016-2020', '2021-2023', '1991-2000', '2001-2005', '2006-2010', '2011-2015']
    for period in construction_period:
        end_yr = int(period.split('-')[1])
        y0 = dm.col_labels['Years'][0]
        for yr in range(y0, end_yr+3):
            if yr in dm.col_labels['Years']:
                dm.array[:, idx[yr], :, :, idx[period]] = 0

    dm.groupby(cat_map, dim='Categories2', inplace=True)

    return dm


def compute_avg_floor_area(dm_floor_area, years_ots):
    dm_avg_floor_area = dm_floor_area.filter({'Variables': ['bld_avg-floor-area-new']})
    years_to_keep = ['1991-2000', '2001-2005', '2006-2010', '2011-2015', '2016-2020', '2021-2023']
    #years_to_keep = dm_avg_floor_area.col_labels['Categories2'].copy()
    #years_to_keep.remove('Avant 1919')
    dm_avg_floor_area.filter({'Categories2': years_to_keep}, inplace=True)
    # Compute the avg floor area based on construction period
    arr_avg_area = np.nanmean(dm_avg_floor_area.array, axis=1, keepdims=True)
    #years_all = create_years_list(1919, 2023, 1)
    years_missing = list(set(years_ots) - set(dm_avg_floor_area.col_labels['Years']))
    dm_avg_floor_area.add(np.nan, dummy=True, dim='Years', col_label=years_missing)
    dm_avg_floor_area.sort('Years')
    dm = dm_avg_floor_area.copy()
    dm.group_all('Categories2')
    dm.array[...] = np.nan
    idx_out = dm.idx
    idx_in = dm_avg_floor_area.idx
    for interval in dm_avg_floor_area.col_labels['Categories2']:
        y_start = int(interval.split('-')[0])
        y_end = int(interval.split('-')[1])
        y_mean = int((y_start + y_end)/2)
        # Assign categories 2 value to years in the middle of the interval
        dm.array[:, idx_out[y_mean], :, :] = arr_avg_area[:, 0, :, :, idx_in[interval]]
    # Linear interpolation
    dm.fill_nans(dim_to_interp='Years')
    # Moving average to smooth
    window_size = 3  # Change window size to control the smoothing effect
    data_smooth = moving_average(dm.array, window_size, axis=dm.dim_labels.index('Years'))
    dm.array[:, 1:-1, ...] = data_smooth

    return dm


def extrapolate_energy_categories_to_missing_years(dm_floor_area, cat_map):

    dm = dm_floor_area.copy()
    dm.filter({'Variables': ['bld_floor-area_stock']}, inplace=True)
    dm.array[:, 0, ...] = np.nan
    #dm_floor_area.group_all('Categories2')
    years_missing = list(set(years_ots) - set(dm.col_labels['Years']))
    dm.add(np.nan, dummy=True, dim='Years', col_label=years_missing)
    dm.sort('Years')

    # Forecasting
    arr_floor_cap = dm.array / dm_pop.array[..., np.newaxis, np.newaxis]
    dm.add(arr_floor_cap, dim='Variables', col_label='bld_floor-area_stock-cap', unit='m2/cap')
    linear_fitting(dm, dm.col_labels['Years'])
    idx = dm.idx
    dm.array[:, :, idx['bld_floor-area_stock'], ...] = \
        dm.array[:, :, idx['bld_floor-area_stock-cap'], ...] * dm_pop.array[..., np.newaxis]

    dm.filter({'Variables': ['bld_floor-area_stock']}, inplace=True)

    construction_period = ['2016-2020', '2021-2023', '1991-2000', '2001-2005', '2006-2010', '2011-2015']
    for period in construction_period:
        start_yr = int(period.split('-')[0])
        y0 = dm.col_labels['Years'][0]
        for yr in range(y0, start_yr):
            if yr in dm.col_labels['Years']:
                dm.array[:, idx[yr], :, :, idx[period]] = 0

    # put nan during the construction period
    construction_period = ['1991-2000', '2001-2005', '2006-2010']
    for period in construction_period:
        start_yr = int(period.split('-')[0])
        end_yr = int(period.split('-')[1])
        for yr in range(start_yr, end_yr+1):
            if yr in dm.col_labels['Years']:
                dm.array[:, idx[yr], :, :, idx[period]] = np.nan

    dm.fill_nans(dim_to_interp='Years')

    dm.groupby(cat_map, dim='Categories2', inplace=True)
    dm.normalise(dim='Categories2', inplace=True, keep_original=True)
    dm.drop(col_label=['bld_floor-area_stock'], dim='Variables')

    return dm


def extrapolate_floor_area_to_missing_years(dm):
    dm.group_all('Categories2')

    dm.filter({'Variables': ['bld_floor-area_stock']}, inplace=True)
    dm.array[:, 0, ...] = np.nan
    years_missing = list(set(years_ots) - set(dm.col_labels['Years']))
    dm.add(np.nan, dummy=True, dim='Years', col_label=years_missing)
    dm.sort('Years')

    # Forecasting
    arr_floor_cap = dm.array / dm_pop.array[..., np.newaxis]
    dm.add(arr_floor_cap, dim='Variables', col_label='bld_floor-area_stock-cap', unit='m2/cap')
    linear_fitting(dm, dm.col_labels['Years'])
    idx = dm.idx
    dm.array[:, :, idx['bld_floor-area_stock'], ...] = \
        dm.array[:, :, idx['bld_floor-area_stock-cap'], ...] * dm_pop.array[...]

    return dm

def extract_bld_floor_area_stock(table_id, file, dm_pop, years_ots, cat_map):

    try:
        with open(file, 'rb') as handle:
            dm_floor_area = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # Extract buildings floor area
        filter = {'Année': structure['Année'],
                  'Canton (-) / District (>>) / Commune (......)': ['Suisse', '- Vaud'],
                  'Catégorie de bâtiment': structure['Catégorie de bâtiment'],
                  'Surface du logement': structure['Surface du logement'],
                  'Époque de construction': structure['Époque de construction']}
        mapping_dim = {'Country': 'Canton (-) / District (>>) / Commune (......)', 'Years': 'Année',
                       'Variables': 'Surface du logement', 'Categories1': 'Catégorie de bâtiment',
                       'Categories2': 'Époque de construction'}
        unit_all = ['number'] * len(structure['Surface du logement'])
        # Get api data
        dm_floor_area = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                        units=unit_all,
                                        language='fr')
        dm_floor_area.rename_col(['Suisse', '- Vaud'], ['Switzerland', 'Vaud'], dim='Country')

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_floor_area, handle, protocol=pickle.HIGHEST_PROTOCOL)

    dm_floor_area.groupby({'single-family-households': ['Maisons individuelles'],
                           'multi-family-households': ['Maisons à plusieurs logements',
                                                       "Bâtiments d'habitation avec usage annexe",
                                                       "Bâtiments partiellement à usage d'habitation"]},
                          dim='Categories1', inplace=True)

    # There is something weird happening where the number of buildings with less than 30m2 built before
    # 1919 increases over time. Maybe they are re-arranging the internal space?
    # Save number of bld (to compute avg size)
    dm_num_bld = dm_floor_area.groupby({'bld_stock-number-bld': '.*'}, dim='Variables',
                                       regex=True, inplace=False)

    ## Compute total floor space
    # Drop split by size
    dm_floor_area.rename_col_regex(' m2', '', 'Variables')
    # The average size for less than 30 is a guess, as is the average size for 150+,
    # we will use the data from bfs to calibrate
    avg_size = {'<30': 25, '30-49': 39.5, '50-69': 59.5, '70-99': 84.5, '100-149': 124.5, '150+': 175}
    idx = dm_floor_area.idx
    for size in dm_floor_area.col_labels['Variables']:
        dm_floor_area.array[:, :, idx[size], :, :] = avg_size[size] * dm_floor_area.array[:, :, idx[size], :, :]
    dm_floor_area.groupby({'bld_floor-area_stock': '.*'}, dim='Variables', regex=True, inplace=True)
    dm_floor_area.change_unit('bld_floor-area_stock', 1, 'number', 'm2')

    #### Section to look into what happens to old buildings in recent years: i.e. renovation by going from mfh to sfh
    dm_area_transformed = compute_new_area_transformed(dm_floor_area, years_ots, cat_map)

    dm_floor_area.append(dm_num_bld, dim='Variables')
    dm_floor_area.operation('bld_floor-area_stock', '/', 'bld_stock-number-bld',
                            out_col='bld_avg-floor-area-new', unit='m2/bld')

    # Extracting the average new built floor area for sfh and mfh
    # (Basically you want the category construction period to become the year category)
    dm_avg_floor_area = compute_avg_floor_area(dm_floor_area, years_ots)

    # Drop split by construction year for floor-area stock
    # Add missing years
    dm_energy_cat = extrapolate_energy_categories_to_missing_years(dm_floor_area, cat_map)
    dm_energy_cat.append(dm_area_transformed, dim='Variables')

    dm_floor_area = extrapolate_floor_area_to_missing_years(dm_floor_area)

    idx = dm_floor_area.idx
    idx_e = dm_energy_cat.idx
    arr = dm_energy_cat.array[:, :, idx_e['bld_floor-area_stock_share'], :, :]\
          * dm_floor_area.array[:, :, idx['bld_floor-area_stock'], :, np.newaxis]
    dm_energy_cat.add(arr, dim='Variables', col_label='bld_floor-area_stock', unit='m2')

    dm_floor_area.append(dm_avg_floor_area, dim='Variables')


    return dm_floor_area, dm_energy_cat


def extract_bld_new_buildings_1(table_id, file):
    try:
        with open(file, 'rb') as handle:
            dm_new_area = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # Extract buildings floor area
        filter = {'Année': structure['Année'],
                  'Grande région (<<) / Canton (-) / Commune (......)': ['Suisse', '- Canton de Vaud'],
                  'Type de bâtiment': structure['Type de bâtiment']}
        mapping_dim = {'Country': 'Grande région (<<) / Canton (-) / Commune (......)',
                       'Years': 'Année',
                       'Variables': 'Type de bâtiment'}
        unit_all = ['number'] * len(structure['Type de bâtiment'])
        # Get api data
        dm_new_area = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                      units=unit_all, language='fr')
        dm_new_area.rename_col(['Suisse', '- Canton de Vaud'], ['Switzerland', 'Vaud'], dim='Country')
        dm_new_area.groupby({'bld_new-buildings_single-family-households':
                                 ['Maisons individuelles'],
                             'bld_new-buildings_multi-family-households':
                                 ['Maisons à plusieurs logements', "Bâtiments d'habitation avec usage annexe",
                                  "Bâtiments partiellement à usage d'habitation"]}, dim='Variables', inplace=True)

        dm_new_area.filter_w_regex({'Variables': '.*households'}, inplace=True)
        dm_new_area.sort('Years')
        dm_new_area.deepen()

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_new_area, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm_new_area


def extract_bld_new_buildings_2(table_id, file):
    try:
        with open(file, 'rb') as handle:
            dm_new_area = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # Extract buildings floor area
        filter = {'Année': structure['Année'],
                  'Canton (-) / Commune (......)': ['Suisse', '- Canton de Vaud'],
                  'Type de bâtiment': structure['Type de bâtiment']}
        mapping_dim = {'Country': 'Canton (-) / Commune (......)',
                       'Years': 'Année',
                       'Variables': 'Type de bâtiment'}
        unit_all = ['number'] * len(structure['Type de bâtiment'])
        # Get api data
        dm_new_area = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                      units=unit_all, language='fr')
        dm_new_area.rename_col(['Suisse', '- Canton de Vaud'], ['Switzerland', 'Vaud'], dim='Country')
        dm_new_area.groupby({'bld_new-buildings_single-family-households':
                                 ['Maisons individuelles à un logement, isolées',
                                  'Maisons individuelles à un logement, mitoyennes'],
                             'bld_new-buildings_multi-family-households':
                                 ["Maisons à plusieurs logements, à usage exclusif d'habitation",
                                  "Bâtiments à usage mixte, principalement à usage d'habitation",
                                  "Bâtiments partiellement à usage d'habitation"]},
                            dim='Variables', inplace=True)

        dm_new_area.filter_w_regex({'Variables': '.*households'}, inplace=True)
        dm_new_area.sort('Years')
        dm_new_area.deepen()

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_new_area, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm_new_area


def compute_bld_floor_area_new(dm_bld_new_buildings_1, dm_bld_new_buildings_2, dm_bld_area_stock, dm_pop):
    dm_bld_area_new = dm_bld_new_buildings_2.copy()
    dm_bld_area_new.append(dm_bld_new_buildings_1, dim='Years')
    dm_bld_area_new.sort('Years')

    # Extrapolate new buildings to missing years using per capita approach
    years_missing = list(set(years_ots) - set(dm_bld_area_new.col_labels['Years']))
    dm_bld_area_new.add(np.nan, col_label=years_missing, dim='Years', dummy=True)
    arr_bld_cap = dm_bld_area_new.array/dm_pop.array[..., np.newaxis]
    dm_bld_area_new.add(arr_bld_cap, dim='Variables', col_label='bld_new-buildings-cap', unit='bld/cap')
    linear_fitting(dm_bld_area_new, years_ots, based_on=create_years_list(1995, 2002, 1))
    dm_bld_area_new.array[:, -1, ...] = np.nan
    linear_fitting(dm_bld_area_new, years_ots, based_on=create_years_list(2015, 2022, 1))
    idx = dm_bld_area_new.idx
    dm_bld_area_new.array[:, :, idx['bld_new-buildings'], :] = dm_bld_area_new.array[:, :, idx['bld_new-buildings-cap'], :] \
                                                               * dm_pop.array[:, :, 0, np.newaxis]

    dm_bld_area_new.append(dm_bld_area_stock, dim='Variables')
    dm_bld_area_new.operation('bld_new-buildings', '*', 'bld_avg-floor-area-new', out_col='bld_floor-area_new', unit='m2')

    dm_bld_area_new.filter({'Variables': ['bld_floor-area_new']}, inplace=True)
    dm_bld_area_stock.filter({'Variables': ['bld_floor-area_stock']}, inplace=True)

    return dm_bld_area_new


def compute_bld_demolition_rate(dm):

    #window_size = 3  # Change window size to control the smoothing effect
    #data_smooth = moving_average( dm_bld_area_stock.array, window_size, axis= dm_bld_area_stock.dim_labels.index('Years'))
    #dm_bld_area_stock.array[:, 1:-1, ...] = data_smooth

    #dm = dm_bld_area_stock.copy()
    #dm.append(dm_bld_area_new, dim='Variables')

    # w(t) = s(t-1) - s(t) + n(t)
    # dem-rate(t-1) = w(t) / s(t-1)
    dm.lag_variable('bld_floor-area_stock', shift=1, subfix='_tm1')
    dm.operation('bld_floor-area_stock_tm1', '-', 'bld_floor-area_stock',
                                out_col='bld_delta-stock', unit='m2')
    dm.operation('bld_delta-stock', '+', 'bld_floor-area_new',
                                out_col='bld_floor-area_waste', unit='m2')
    dm.operation('bld_floor-area_waste', '/', 'bld_floor-area_stock_tm1',
                                out_col='bld_demolition-rate_tm1', unit='%')
    dm.lag_variable('bld_demolition-rate_tm1', shift=-1, subfix='_tp1')
    dm.rename_col('bld_demolition-rate_tm1_tp1', 'bld_demolition-rate', dim='Variables')

    dm.filter({'Variables': ['bld_demolition-rate']}, inplace=False).flatten().datamatrix_plot()

    # Compute demolition rate
    dm_demolition_rate = dm.filter({'Variables': ['bld_demolition-rate']}, inplace=False)
    # Demolition rate cannot be negative. We impose that it has to be at least 0.1%
    dm_demolition_rate.array = np.maximum(0.001, dm_demolition_rate.array)
    # Smooth the demolition-rate
    window_size = 3  # Change window size to control the smoothing effect
    data_smooth = moving_average(dm_demolition_rate.array, window_size, axis=dm_demolition_rate.dim_labels.index('Years'))
    dm_demolition_rate.array[:, 1:-1, ...] = data_smooth

    # Recompute new fleet so that it matches the demolition rate
    # n(t) = s(t) - s(t-1) + w(t)
    # w(t) = dem-rate(t-1) * s(t-1)
    # n(t) = s(t) - s(t-1) - dem-rate(t-1) * s(t-1)
    dm.filter({'Variables': ['bld_floor-area_stock', 'bld_floor-area_stock_tm1']}, inplace=True)
    dm.append(dm_demolition_rate, dim='Variables')
    dm.operation('bld_floor-area_stock', '-', 'bld_floor-area_stock_tm1', out_col='bld_delta-stock', unit='m2')
    dm.lag_variable('bld_demolition-rate', shift=1, subfix='_tm1')
    dm.operation('bld_demolition-rate_tm1', '*', 'bld_floor-area_stock', out_col='bld_floor-area_waste', unit='m2')
    dm.operation('bld_delta-stock', '+', 'bld_floor-area_waste', out_col='bld_floor-area_new', unit='m2')

    dm.filter({'Variables': ['bld_floor-area_stock', 'bld_floor-area_new', 'bld_demolition-rate']}, inplace=True)
    idx = dm.idx
    dm.array[:, 0, idx['bld_floor-area_new'], ...] = np.nan
    dm.fill_nans(dim_to_interp='Years')

    dm.flatten().datamatrix_plot()

    return dm


def extract_number_of_buildings(table_id, file):
    try:
        with open(file, 'rb') as handle:
            dm_nb_bld = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, 'example', language='fr')
        filter = {
            'Canton (-) / District (>>) / Commune (......)': ['Suisse', '- Vaud'],
            'Catégorie de bâtiment': structure['Catégorie de bâtiment'],
            'Époque de construction': structure['Époque de construction'],
            'Année': structure['Année']
        }
        mapping = {'Country': 'Canton (-) / District (>>) / Commune (......)',
                   'Years': 'Année',
                   'Variables': 'Époque de construction',
                   'Categories1': 'Catégorie de bâtiment'}
        unit = ['number'] * len(structure['Époque de construction'])
        dm_nb_bld = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping, language='fr',
                                    units=unit)
        dm_nb_bld.groupby({'bld_nb-bld': '.*'}, regex=True, inplace=True, dim='Variables')
        dm_nb_bld.groupby({'single-family-households': ['Maisons individuelles'],
                           'multi-family-households': ['Maisons à plusieurs logements',
                                                       "Bâtiments d'habitation avec usage annexe",
                                                       "Bâtiments partiellement à usage d'habitation"]},
                          dim='Categories1', inplace=True)
        dm_nb_bld.rename_col(['Suisse', '- Vaud'], ['Switzerland', 'Vaud'], dim='Country')
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_nb_bld, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm_nb_bld


def compute_renovated_buildings(dm_bld, nb_buildings_renovated, VD_share, share_by_bld):
    dm_bld.add(np.nan, dim='Variables', dummy=True, col_label='bld_nb-bld-renovated', unit='number')
    idx = dm_bld.idx
    for yr in nb_buildings_renovated.keys():
        for cat in ['single-family-households', 'multi-family-households']:
            dm_bld.array[idx['Switzerland'], idx[yr], idx['bld_nb-bld-renovated'], idx[cat]] \
                = nb_buildings_renovated[yr] * share_by_bld[cat]
            dm_bld.array[idx['Vaud'], idx[yr], idx['bld_nb-bld-renovated'], idx[cat]] \
                = nb_buildings_renovated[yr] * VD_share[yr] * share_by_bld[cat]
    return dm_bld


def extract_renovation_1990_2000(table_id, file, share_thermal):
    try:
        with open(file, 'rb') as handle:
            dm_renovation = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')

        for e in structure['Epoque de construction']:
            filter = {'Canton': ['Suisse', 'Vaud'],
                      'Type de bâtiment': structure['Type de bâtiment'],
                      "Nombre d'étages": structure["Nombre d'étages"],
                      'Nombre de logements': structure['Nombre de logements'],
                      'Epoque de construction': e,
                      'Epoque de rénovation': structure['Epoque de rénovation'],
                      'Année': structure['Année']
                      }

            mapping = {'Country': 'Canton',
                       'Years': 'Année',
                       'Variables': 'Epoque de construction',
                       'Categories1': 'Type de bâtiment',
                       'Categories2': 'Epoque de rénovation'}
            unit = ['number']
            dm_renovation_e = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping, units=unit,
                                            language='fr')
            if 'dm_renovation' in locals():
                dm_renovation.array = dm_renovation.array + dm_renovation_e.array
            else:
                dm_renovation = dm_renovation_e.groupby({'bld_nb-bld-renovated': '.*'}, regex=True, inplace=False, dim='Variables')

        dm_renovation.groupby({'single-family-households': ['Maisons individuelles'],
                               'multi-family-households': ['Maisons à plusieurs logements',
                                                           "Bâtiments d'habitation avec usage annexe",
                                                           "Bâtiments partiellement à usage d'habitation"]},
                              dim='Categories1', inplace=True)
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_renovation, handle, protocol=pickle.HIGHEST_PROTOCOL)


    # Renovation here includes all types of renovation
    # According to the Programme Bâtiments, usually 30%-35% of renovation are for insulation
    dm_renovation.array = dm_renovation.array * share_thermal
    map_to_years = {'Rénovés dans les 4 dernières années': [2000, 4],
                    'Rénovés dans les 5 à 9 années précédentes': [1990, 5]}
    # Add missing years
    dm_tot_bld = dm_renovation.group_all('Categories2', inplace=False)
    dm_tot_bld.add(np.nan, dummy=True, dim='Years', col_label=create_years_list(1991, 1999, 1))
    dm_tot_bld.sort('Years')
    dm_tot_bld.rename_col('bld_nb-bld-renovated', 'bld_nb-bld', dim='Variables')

    dm_renovation.add(np.nan, dummy=True, dim='Years', col_label=create_years_list(1991, 1999, 1))
    dm_renovation.sort('Years')

    dm_renovation.add(np.nan, dummy=True, dim='Categories2', col_label='total')
    idx = dm_renovation.idx
    for cat, values in map_to_years.items():
        yr = values[0]
        interval = values[1]
        dm_renovation.array[:, idx[yr], idx['bld_nb-bld-renovated'], :, idx['total']] =\
            dm_renovation.array[:, idx[yr], idx['bld_nb-bld-renovated'], :, idx[cat]] / interval

    dm_renovation.filter({'Categories2': ['total']}, inplace=True)
    #dm_renovation.group_all('Categories2', inplace=True)
    dm_renovation.fill_nans(dim_to_interp='Years')
    dm_renovation.group_all('Categories2', inplace=True)
    dm_tot_bld.fill_nans(dim_to_interp='Years')

    dm_renovation.append(dm_tot_bld, dim='Variables')
    dm_renovation.operation('bld_nb-bld-renovated', '/', 'bld_nb-bld', out_col='bld_renovation-rate', unit='%')

    return dm_renovation


def compute_renovation_rate(dm_renovation, years_ots):

    dm_renovation.operation('bld_nb-bld-renovated', '/', 'bld_nb-bld', out_col='bld_renovation-rate', unit='%')
    years_missing = list(set(years_ots) - set(dm_renovation.col_labels['Years']))
    dm_renovation.add(np.nan, dummy=True, col_label=years_missing, dim='Years')
    dm_renovation.sort('Years')
    dm_renovation.fill_nans(dim_to_interp='Years')
    dm_renovation.filter({'Variables': ['bld_renovation-rate']}, inplace=True)

    return dm_renovation


def extract_heating_demand(table_id, file):

    try:
        with open(file, 'rb') as handle:
            dm_heating = pickle.load(handle)
    except OSError:

        structure, title = get_data_api_CH(table_id, mode='example', language='fr')

        filter = {'Économie et ménages': ['--- Chauffage des ménages'],
                  'Unité de mesure': ['Térajoules'],
                  'Année': structure['Année'],
                  'Agent énergétique': structure['Agent énergétique']}

        mapping = {'Country': 'Unité de mesure',
                   'Years': 'Année',
                   'Variables': 'Économie et ménages',
                   'Categories1': 'Agent énergétique'}

        dm_heating = get_data_api_CH(table_id, mode='extract', mapping_dims=mapping, filter=filter, units=['TJ'], language='fr')

        dm_heating.rename_col('--- Chauffage des ménages', 'bld_heating-demand', dim='Variables')
        dm_heating.rename_col('Térajoules', 'Switzerland', dim='Country')

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_heating, handle, protocol=pickle.HIGHEST_PROTOCOL)

    dm_heating.filter({'Categories1': ['Agent énergétique - total']}, inplace=True)
    dm_heating.group_all('Categories1', inplace=True)

    dm_heating.change_unit('bld_heating-demand', 3600, old_unit='TJ', new_unit='TWh', operator='/')

    return dm_heating


def extract_bld_floor_area_stock_envelope_cat(table_id, file, dm_pop, years_ots, cat_dict):

    try:
        with open(file, 'rb') as handle:
            dm_floor_area = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        # Extract buildings floor area
        filter = {'Année': structure['Année'],
                  'Canton (-) / District (>>) / Commune (......)': ['Suisse', '- Vaud'],
                  'Catégorie de bâtiment': structure['Catégorie de bâtiment'],
                  'Surface du logement': structure['Surface du logement'],
                  'Époque de construction': structure['Époque de construction']}
        mapping_dim = {'Country': 'Canton (-) / District (>>) / Commune (......)', 'Years': 'Année',
                       'Variables': 'Surface du logement', 'Categories1': 'Catégorie de bâtiment',
                       'Categories2': 'Époque de construction'}
        unit_all = ['number'] * len(structure['Surface du logement'])
        # Get api data
        dm_floor_area = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                        units=unit_all,
                                        language='fr')
        dm_floor_area.rename_col(['Suisse', '- Vaud'], ['Switzerland', 'Vaud'], dim='Country')

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_floor_area, handle, protocol=pickle.HIGHEST_PROTOCOL)

    dm_floor_area.groupby({'single-family-households': ['Maisons individuelles'],
                           'multi-family-households': ['Maisons à plusieurs logements',
                                                       "Bâtiments d'habitation avec usage annexe",
                                                       "Bâtiments partiellement à usage d'habitation"]},
                          dim='Categories1', inplace=True)

    # Save number of bld (to compute avg size)
    dm_num_bld = dm_floor_area.groupby({'bld_stock-number-bld': '.*'}, dim='Variables',
                                       regex=True, inplace=False)

    ## Compute total floor space
    # Drop split by size
    dm_floor_area.rename_col_regex(' m2', '', 'Variables')
    # The average size for less than 30 is a guess, as is the average size for 150+,
    # we will use the data from bfs to calibrate
    avg_size = {'<30': 25, '30-49': 39.5, '50-69': 59.5, '70-99': 84.5, '100-149': 124.5, '150+': 175}
    idx = dm_floor_area.idx
    for size in dm_floor_area.col_labels['Variables']:
        dm_floor_area.array[:, :, idx[size], :, :] = avg_size[size] * dm_floor_area.array[:, :, idx[size], :, :]
    dm_floor_area.groupby({'bld_floor-area_stock': '.*'}, dim='Variables', regex=True, inplace=True)
    dm_floor_area.change_unit('bld_floor-area_stock', 1, 'number', 'm2')

    dm_floor_area.append(dm_num_bld, dim='Variables')

    dm_floor_area.groupby(cat_dict, dim='Categories2', inplace=True)

    dm_floor_area.normalise(dim='Categories2', inplace=True, keep_original=True)

    dm_floor_area.filter({'Variables': ['bld_floor-area_stock_share']}, inplace=True)

    return dm_floor_area


def compute_new_area_by_energy_cat(dm_bld_area_new, dm_energy_cat, cat_map):

    dm_energy_cat.add(0, dummy=True, dim='Variables', col_label='bld_floor-area_new', unit='m2')

    idx = dm_energy_cat.idx
    idx_n = dm_bld_area_new.idx
    for cat, period in cat_map.items():
        start_yr = period[0]
        end_yr = period[1]
        period_list = list(range(start_yr, end_yr+1))
        idx_period = [idx[yr] for yr in period_list]
        dm_energy_cat.array[:, idx_period, idx['bld_floor-area_new'], :, idx[cat]] = 1

    dm_energy_cat.array[:, :, idx['bld_floor-area_new'], ...] = \
        dm_energy_cat.array[:, :, idx['bld_floor-area_new'], :, :] \
        * dm_bld_area_new.array[:, :, idx_n['bld_floor-area_new'], :, np.newaxis]

    dm_energy_cat.operation('bld_floor-area_new', '+', 'bld_floor-area_transformed', out_col='bld_floor-area_new_tot', unit='m2')

    return dm_energy_cat


# Stock
years_ots = create_years_list(1990, 2023, 1)

dict_lfs_ots, dict_lfs_fts = read_database_to_dm('lifestyles_population.csv', filter={'geoscale': ['Vaud', 'Switzerland']},
                                                 baseyear=years_ots[-1], num_cat=0, level='all')
dm_pop = dict_lfs_ots['pop'].filter({'Variables': ['lfs_population_total']}, inplace=False)
dm_pop.sort('Country')

construction_period_envelope_cat = {'F': ['Avant 1919', '1919-1945', '1946-1960', '1961-1970'],
                                    'E': ['1971-1980'],
                                    'D': ['1981-1990', '1991-2000'],
                                    'C': ['2001-2005', '2006-2010'],
                                    'B': ['2011-2015', '2016-2020', '2021-2023']}
envelope_cat_new = {'D': (1990, 2000), 'C': (2001, 2010), 'B': (2011, 2023)}

# Floor area stock
# Logements selon les niveaux géographiques institutionnels, la catégorie de bâtiment,
# la surface du logement et l'époque de construction
# https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0902020200_103/-/px-x-0902020200_103.px/
table_id = 'px-x-0902020200_103'
file = 'data/bld_floor-area_stock.pickle'
dm_bld_area_stock, dm_energy_cat = extract_bld_floor_area_stock(table_id, file, dm_pop,
                                                                years_ots, construction_period_envelope_cat)

# New residential buildings by sfh, mfh
# Nouveaux logements selon la grande région, le canton, la commune et le type de bâtiment, depuis 2013
table_id = 'px-x-0904030000_107'
file = 'data/bld_new_buidlings_2013_2023.pickle'
dm_bld_new_buildings_1 = extract_bld_new_buildings_1(table_id, file)

# Nouveaux logements selon le type de bâtiment, 1995-2012
table_id = 'px-x-0904030000_103'
file = 'data/bld_new_buildings_1995_2012.pickle'
dm_bld_new_buildings_2 = extract_bld_new_buildings_2(table_id, file)
# Floor-area new
dm_bld_area_new = compute_bld_floor_area_new(dm_bld_new_buildings_1, dm_bld_new_buildings_2, dm_bld_area_stock, dm_pop)
del dm_bld_new_buildings_2, dm_bld_new_buildings_1


dm_energy_cat = compute_new_area_by_energy_cat(dm_bld_area_new, dm_energy_cat, envelope_cat_new)

dm_energy_cat_old = dm_energy_cat.copy()
dm_energy_cat.group_all('Categories2')
# Check what to do for the demolition rate-not clear where the spikes come from
dm_all = compute_bld_demolition_rate(dm_energy_cat)

df = dm_all.write_df()

dm = dm_energy_cat_old.filter({'Variables': ['bld_floor-area_stock']}, inplace=False)
df_cat = dm.write_df()

del dm_bld_area_new, dm_bld_area_stock

# Empty apartments
# Logements vacants selon la grande région, le canton, la commune, le nombre de pièces d'habitation
# et le type de logement vacant
# https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0902020300_101/-/px-x-0902020300_101.px/



# Number of buildings
# Bâtiments selon les niveaux géographiques institutionnels, la catégorie de bâtiment et l'époque de construction
table_id = 'px-x-0902010000_103'
file = 'data/bld_nb-buildings_2010_2022.pickle'
dm_bld = extract_number_of_buildings(table_id, file)

print('Maybe you should considered the buildings undergoing systemic renovation as well')
# Number of renovated-buildings (thermal insulation)
# https://www.newsd.admin.ch/newsd/message/attachments/82234.pdf
# "Programme bâtiments" rapports annuels 2014-2022, focus sur isolation thérmique
nb_buildings_isolated = {2022: 8148, 2021: 8400, 2020: 8050, 2019: 8500,
                          2018: 7500, 2017: 8100, 2016: 7900, 2014: 8303}
nb_buildings_systemic_renovation \
    = {2022: 2326, 2021: 2320, 2020: 2240, 2019: 1900, 2018: 1200,
       2017: 374, 2016: 0, 2014: 0}
nb_buildings_renovated = dict()
for yr in nb_buildings_isolated.keys():
    nb_buildings_renovated[yr] = nb_buildings_isolated[yr] + nb_buildings_systemic_renovation[yr]

# For 2014 - 2016 we assume VD share = VD share 2017
VD_share = {2014: 0.11, 2015: 0.11, 2016: 0.11, 2017: 0.110, 2018: 0.103,
            2019: 0.154, 2020: 0.16, 2021: 0.193, 2022: 0.15}
share_by_bld = {'single-family-households': 0.55, 'multi-family-households': 0.35, 'other': 0.1}
dm_renovation = compute_renovated_buildings(dm_bld, nb_buildings_renovated, VD_share, share_by_bld)
# Compute renovation-rate
dm_renovation = compute_renovation_rate(dm_renovation, years_ots)

df_renovation = dm_renovation.write_df()

# px-x-0902020100_111 / Structure des bâtiments: bâtiments selon le canton, le type de bâtiment,
# le nombre d'étages et de logements, l'époque de construction et de rénovation, 1990 et 2000
table_id = 'px-x-0902020100_111'
file = 'data/bld_renovation-rate_1990_2000.pickle'
# Only a part of the building is renovated for thermal isolation
# According to the Programme Bâtiments, usually 30%-35% of renovation are for insulation
share_thermal_isolation = 0.33
dm_renovation_old = extract_renovation_1990_2000(table_id, file, share_thermal_isolation)

# 2018: Type of renovation 4% windows, 51% roof, 38% facade, 2% floor, 5% other
# shallow: 11% (windows, floor, other) -> uvalue improvement 15%
# medium; 51% (roof) -> uvalue improvement 41%
# deep: 38% (facade) -> uvalue improvement 66%


# 54% sfh, 35% mfh, 11% other
# 2022: 60% sfh, 32% mfh, 8% other
# 2020: 55% sfh, 35% mfh, 10% other


# Energy demand for heating in building sector
table_id = 'px-x-0204000000_106'
file = 'data/bld_heating-energy-demand.pickle'
dm_heating = extract_heating_demand(table_id, file)

# Compute the average kWh/m2 (~5)
dm_tot_area = dm_all.filter({'Variables': ['bld_floor-area_stock']})
dm_tot_area.group_all(dim='Categories1', inplace=True)
dm_tot_area.filter({'Years': dm_heating.col_labels['Years'], 'Country': ['Switzerland']}, inplace=True)
dm_heating.append(dm_tot_area, dim='Variables')
dm_heating.operation('bld_heating-demand', '/', 'bld_floor-area_stock', out_col='bld_energy-intensity', unit='TWh/m2')
dm_heating.change_unit('bld_energy-intensity', factor=1e9, old_unit='TWh/m2', new_unit='kWh/m2')

df_heating = dm_heating.write_df()

energy_saving_TWh = {2022: 2.2, 2021: 2.2, 2020: 2.2, 2019: 2.6, 2018: 2.5, 2017: 3.0}


# Definition of Building Archetypes Based on the Swiss Energy Performance Certificates Database
# by Alessandro Pongelli et al.
# U-value is computed as the average of the house element u-value (roof, wall, windows, ..) weighted by their area
construction_period_envelope_cat = {'F': ['Avant 1919', '1919-1945', '1946-1960', '1961-1970'],
                                    'E': ['1971-1980'],
                                    'D': ['1981-1990', '1991-2000'],
                                    'C': ['2001-2005', '2006-2010'],
                                    'B': ['2011-2015', '2016-2020', '2021-2023']}
envelope_cat_new = {'D': (1990, 2000), 'C': (2001, 2010), 'B': (2011, 2023)}
# U-value in: W/m^2 K
envelope_cat_u_value = {'F': 0.82, 'E': 0.69, 'D': 0.53, 'C': 0.41, 'B': 0.25}
# Energy heating kWh/m^2
envelope_cat_heating_demand = {'F': 175, 'E': 147, 'D': 92, 'C': 66, 'B': 19}

# if I want to save 2.2 TWh, and the maximum improvement I can do is 150 kWh/m2, I need to renovate 15 million m2.
# The current park is 137 + 337 = 474 million m2
# If I want to fix the renovation at 1%, then you renovate 4.7 million m2, in order to save 2.2 TWh,
# you need to save: 470 kWh/m2

# Floor area stock by construction period / energy / Uvalue category
# Logements selon les niveaux géographiques institutionnels, la catégorie de bâtiment,
# la surface du logement et l'époque de construction
# https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0902020200_103/-/px-x-0902020200_103.px/
table_id = 'px-x-0902020200_103'
file = 'data/bld_floor-area_stock.pickle'
dm_energy_cat = extract_bld_floor_area_stock_envelope_cat(table_id, file, dm_pop, years_ots, construction_period_envelope_cat)



# New buildings energy categories
dm_energy_cat.add(0, dummy=True, dim='Variables',
                      col_label=['bld_floor-area_new_share', 'bld_floor-area_renov_share'], unit=['%', '%'])
years_missing = list(set(years_ots) - set(dm_energy_cat.col_labels['Years']))
dm_energy_cat.add(0, dim='Years', dummy=True, col_label=years_missing)
dm_energy_cat.sort('Years')
idx = dm_energy_cat.idx
for cat, yrs_range in envelope_cat_new.items():
    for yr in range(yrs_range[0], yrs_range[1]):
        dm_energy_cat.array[:, idx[yr], idx['bld_floor-area_new_share'], :, idx[cat]] = 1
        dm_energy_cat.array[:, idx[yr], idx['bld_floor-area_renov_share'], :, idx[cat]] = 0.5
        dm_energy_cat.array[:, idx[yr], idx['bld_floor-area_renov_share'], :, idx['C']] = 0.5
        dm_energy_cat.array[:, idx[yr], idx['bld_floor-area_renov_share'], :, idx['F']] = -0.5
        dm_energy_cat.array[:, idx[yr], idx['bld_floor-area_renov_share'], :, idx['E']] = -0.5


# From share to absolute values:
idx = dm_all.idx
idx_c = dm_energy_cat.idx
idx_r = dm_bld.idx
arr_new = dm_all.array[:, :, idx['bld_floor-area_new'], :, np.newaxis] \
          * dm_energy_cat.array[:, :, idx_c['bld_floor-area_new_share'], :, :]
dm_energy_cat.add(arr_new, dim='Variables', col_label='bld_floor-area_new', unit='m2')
arr_stock = dm_all.array[:, :, idx['bld_floor-area_stock'], :, np.newaxis] \
          * dm_energy_cat.array[:, :, idx_c['bld_floor-area_stock_share'], :, :]
dm_energy_cat.add(arr_stock, dim='Variables', col_label='bld_floor-area_stock', unit='m2')
arr_renov = dm_all.array[:, :, idx['bld_floor-area_stock'], :, np.newaxis] \
            * dm_bld.array[:, :, idx_r['bld_renovation-rate'], :, np.newaxis]\
            * dm_energy_cat.array[:, :, idx_c['bld_floor-area_renov_share'], :, :]
dm_energy_cat.add(arr_renov, dim='Variables', col_label='bld_floor-area_renovated', unit='m2')

dm_energy_cat.lag_variable('bld_floor-area_stock', shift=1, subfix='_tm1')
dm_energy_cat.operation('bld_floor-area_stock_tm1', '-', 'bld_floor-area_stock', out_col='bld_floor-area_deltas', unit='m2')
dm_energy_cat.operation('bld_floor-area_deltas', '+', 'bld_floor-area_new', out_col='bld_floor-area_tmp', unit='m2')
dm_energy_cat.operation('bld_floor-area_tmp', '+', 'bld_floor-area_renovated', out_col='bld_floor-area_waste', unit='m2')

dm_tmp = dm_energy_cat.group_all('Categories2', inplace=False)
dm_tmp.datamatrix_plot({'Variables': 'bld_floor-area_waste'})

print('Hello')

df.to_csv('data/out_floor-area.csv')
df_cat.to_csv('data/out_floor-area_by-cat.csv')
df_heating.to_csv('data/out_heating-demand.csv')
df_renovation.to_csv('data/out_renovation-rate.csv')

df_pop = dm_pop.write_df()
df_pop.to_csv('data/out_pop.csv')