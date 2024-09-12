import json
import numpy as np
import eurostat
import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting
from model.common.io_database import update_database_from_dm
from _database.pre_processing.api_routine_Eurostat import get_data_api_eurostat

EU27_cntr_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland',
                  'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
                  'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden']


def moving_average(data, window_size, axis):
    # Apply moving average along the first axis (rows)
    smoothed_data = np.apply_along_axis(lambda x: np.convolve(x, np.ones(window_size) / window_size, mode='valid'),
                                        axis=axis, arr=data)
    return smoothed_data

def create_fts_years_list():
    years_fts = list(
        np.linspace(start=2025, stop=2050, num=6).astype(int))
    return years_fts


def create_ots_years_list(years_setting, astype):
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int).astype(astype))
    return years_ots


def get_pop_eurostat(code_pop, EU27_cntr_list, dict_iso2, years_ots):
    ################################
    ### Extract total population ###
    ################################
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys()),
              'age': 'TOTAL',
              'sex': 'T'}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'age'}
    dm_pop_tot = get_data_api_eurostat(code_pop, filter, mapping_dim, 'inhabitants')

    # Keep only years_ots
    dm_pop_tot.filter({'Years': years_ots}, inplace=True)
    # Replace Germany 1990 value with Nan (Berlin wall jump)
    idx = dm_pop_tot.idx
    dm_pop_tot.array[idx['Germany'], idx[1990], ...] = np.nan

    # Rename, change unit, interpolate
    dm_pop_tot.rename_col('TOTAL', 'lfs_population_total', dim='Variables')
    dm_pop_tot.fill_nans(dim_to_interp='Years')

    # Population data
    dm_pop_tot.drop(dim='Country', col_label='EU27')
    dm_EU27_tot = dm_pop_tot.groupby({'EU27': EU27_cntr_list}, dim='Country')
    dm_pop_tot.append(dm_EU27_tot, dim='Country')

    #######################################
    ### Extract population by age group ###
    #######################################
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys()),
              'sex': ['F', 'M']}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'freq',
                   'Categories1': 'sex',
                   'Categories2': 'age'}
    dm_pop_age = get_data_api_eurostat(code_pop, filter, mapping_dim, 'inhabitants')


    # Keep only years_ots
    dm_pop_age.filter({'Years': years_ots}, inplace=True)
    # Replace Germany 1990 value with Nan (Berlin wall jump)
    idx = dm_pop_age.idx
    dm_pop_age.array[idx['Germany'], idx[1990], ...] = np.nan
    # Fill Nans
    dm_pop_age.fill_nans(dim_to_interp='Years')

    # Group single years in year groups
    dm_pop_age.drop(dim='Categories2', col_label='TOTAL')
    dm_pop_age.rename_col_regex('Y', '', dim='Categories2')
    group_dict = {
        'below19': ['LT1'],
        'age20-29': [],
        'age30-54': [],
        'age55-64': [],
        'above65': ['OPEN'],
    }
    dm_pop_age.drop(dim='Categories2', col_label='UNK')
    for age in dm_pop_age.col_labels['Categories2']:
        try:
            int_age = int(age)
            if int_age <= 19:
                group_dict['below19'].append(age)
            if (int_age >= 20) and (int_age <= 29):
                group_dict['age20-29'].append(age)
            if (int_age >= 30) and (int_age <= 54):
                group_dict['age30-54'].append(age)
            if (int_age >= 55) and (int_age <= 64):
                group_dict['age55-64'].append(age)
            if int_age >= 65:
                group_dict['above65'].append(age)
        except ValueError:
            pass
    dm_pop_age.groupby(group_dict, inplace=True, dim='Categories2')
    dm_pop_age.rename_col('A', 'lfs_demography', dim='Variables')
    dm_pop_age.rename_col(['M', 'F'], ['male', 'female'], dim='Categories1')
    dm_pop_age = dm_pop_age.flatten()

    dm_pop_age.drop(dim='Country', col_label='EU27')
    dm_EU27_age = dm_pop_age.groupby({'EU27': EU27_cntr_list}, dim='Country')
    dm_pop_age.append(dm_EU27_age, dim='Country')

    # Make sure sum over ages matches with total age
    dm_pop_age.sort(dim='Country')
    dm_pop_tot.sort(dim='Country')
    dm_pop_age.array = dm_pop_age.array/np.sum(dm_pop_age.array, axis=-1, keepdims=True)*dm_pop_tot.array[..., np.newaxis]

    # Check for nans
    if np.isnan(dm_pop_age.array).any():
        raise ValueError('dm_pop_age contains nan, it should be fixed')
    if np.isnan(dm_pop_tot.array).any():
        raise ValueError('dm_pop_tot contains nan, it should be fixed')

    return dm_pop_age, dm_pop_tot


def get_pop_eurostat_fts(code_pop_fts, EU27_cntr_list, years_fts, dict_iso2):

    # Scenarios
    # 1- Baseline, 2- Lower mortality, 3-Lower migration, 4-Lower fertility
    # Assign levers
    level_dict = {1: 'BSL', 2: 'LMRT', 3: 'LMIGR', 4: 'LFRT'}

    ##### Extract total pop forecasting
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys()),
              'age': 'TOTAL',
              'sex': 'T',
              'projection': list(level_dict.values())}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'projection'}
    dm_pop_tot = get_data_api_eurostat(code_pop_fts, filter, mapping_dim, 'inhabitants')

    # Keep only years_fts
    dm_pop_tot.filter({'Years': years_fts}, inplace=True)

    ##### Extract total pop by age forecasting
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys()),
              'sex': ['F', 'M'],
              'projection': list(level_dict.values())}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'projection',
                   'Categories1': 'sex',
                   'Categories2': 'age'}
    dm_pop_age = get_data_api_eurostat(code_pop_fts, filter, mapping_dim, 'inhabitants')

    # Keep only years_fts
    dm_pop_age.filter({'Years': years_fts}, inplace=True)

    dm_pop_age.drop(dim='Categories2',
                    col_label=['TOTAL', 'Y15-64', 'Y15-74', 'Y20-64', 'YGE75', 'YGE65', 'YGE80', 'YLT15', 'YLT20'])
    dm_pop_age.rename_col_regex('Y', '', dim='Categories2')
    group_dict = {
        'below19': ['LT1'],
        'age20-29': [],
        'age30-54': [],
        'age55-64': [],
        'above65': ['GE100'],
    }

    for age in dm_pop_age.col_labels['Categories2']:
        try:
            int_age = int(age)
            if int_age <= 19:
                group_dict['below19'].append(age)
            if (int_age >= 20) and (int_age <= 29):
                group_dict['age20-29'].append(age)
            if (int_age >= 30) and (int_age <= 54):
                group_dict['age30-54'].append(age)
            if (int_age >= 55) and (int_age <= 64):
                group_dict['age55-64'].append(age)
            if int_age >= 65:
                group_dict['above65'].append(age)
        except ValueError:
            pass

    dm_pop_age.groupby(group_dict, inplace=True, dim='Categories2')
    dm_pop_age.rename_col(['M', 'F'], ['male', 'female'], dim='Categories1')
    dm_pop_age = dm_pop_age.flatten()

    dm_pop_tot.drop(dim='Country', col_label='EU27')
    dm_EU27_tot = dm_pop_tot.groupby({'EU27': EU27_cntr_list}, dim='Country')
    dm_pop_tot.append(dm_EU27_tot, dim='Country')

    dm_pop_age.drop(dim='Country', col_label='EU27')
    dm_EU27_age = dm_pop_age.groupby({'EU27': EU27_cntr_list}, dim='Country')
    dm_pop_age.append(dm_EU27_age, dim='Country')

    # Make sure sum over ages matches with total age
    dm_pop_age.sort(dim='Country')
    dm_pop_tot.sort(dim='Country')
    dm_pop_age.array = dm_pop_age.array / np.sum(dm_pop_age.array, axis=-1, keepdims=True) * dm_pop_tot.array[
        ..., np.newaxis]

    # Check for nans
    if np.isnan(dm_pop_age.array).any():
        raise ValueError('dm_pop_age contains nan, it should be fixed')
    if np.isnan(dm_pop_tot.array).any():
        raise ValueError('dm_pop_tot contains nan, it should be fixed')

    dict_dm_pop_fts = dict()
    dict_dm_pop_fts_tot = dict()
    for k, v in level_dict.items():
        dict_dm_pop_fts[k] = dm_pop_age.filter({'Variables': [v]})
        dict_dm_pop_fts[k].rename_col(v, 'lfs_demography', dim='Variables')

        dict_dm_pop_fts_tot[k] = dm_pop_tot.filter({'Variables': [v]})
        dict_dm_pop_fts_tot[k].rename_col(v, 'lfs_population_total', dim='Variables')

    return dict_dm_pop_fts, dict_dm_pop_fts_tot


years_setting = [1990, 2023, 2050, 5]  # Set the timestep for historical years & scenarios
years_ots = create_ots_years_list(years_setting, astype=int)
years_fts = create_fts_years_list()

f = open('../../country_codes_iso2.json')
dict_iso2 = json.load(f)
dict_iso2.pop('CH')  # Remove Switzerland

# Use following line to explore EUROSTAT database
#toc = eurostat.get_toc_df(agency='EUROSTAT', lang='en')
#toc_pop = eurostat.subset_toc_df(toc, 'house')
update_pop = False
if update_pop:
    # Get population total and by age group (ots)
    dm_pop_age, dm_pop_tot = get_pop_eurostat('demo_pjan', EU27_cntr_list, dict_iso2, years_ots)
    # Get raw fts pop data (fts)
    dict_dm_pop_fts, dict_dm_pop_fts_tot = get_pop_eurostat_fts('proj_23np', EU27_cntr_list, years_fts, dict_iso2)
    dm_pop_age.drop(dim='Years', col_label=[2023])
    dm_pop_tot.drop(dim='Years', col_label=[2023])
    # Update lifestyles_population.csv data
    file = 'lifestyles_population.csv'
    update_database_from_dm(dm_pop_tot, filename=file, lever='pop', level=0, module='lifestyles')
    update_database_from_dm(dm_pop_age, filename=file, lever='pop', level=0, module='lifestyles')
    for lev, dm_fts in dict_dm_pop_fts.items():
        update_database_from_dm(dm_fts, filename=file, lever='pop', level=lev, module='lifestyles')
    for lev, dm_fts in dict_dm_pop_fts_tot.items():
        update_database_from_dm(dm_fts, filename=file, lever='pop', level=lev, module='lifestyles')

# Update household size (see buildings_preprocessing_EU.py)
