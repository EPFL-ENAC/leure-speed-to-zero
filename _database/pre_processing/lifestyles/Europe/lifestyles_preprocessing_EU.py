import json
import numpy as np
import eurostat
import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting, linear_forecast_BAU, moving_average, create_years_list
from model.common.auxiliary_functions import eurostat_iso2_dict
from model.common.io_database import update_database_from_dm, csv_database_reformat, read_database_to_dm
from _database.pre_processing.api_routine_Eurostat import get_data_api_eurostat

EU27_cntr_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland',
                  'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
                  'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden']


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


def get_household_nb_people_eustat(dict_iso2):

    ##### Extract number of household with a certain number of people
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys())}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'unit',
                   'Categories1': 'n_person'}
    dm_ppl = get_data_api_eurostat('cens_hndwsize', filter, mapping_dim, 'households', years_ots)


    # There is only one value in GE6 for Cyprus, but Cyprus also has 6 and GE7 data. remove GE6 and Total
    dm_ppl.drop(col_label=['GE6', 'TOTAL'], dim='Categories1')
    # Rename GE7 as 7
    dm_ppl.rename_col('GE7', '7', dim='Categories1')
    ppl_int = np.array([int(ppl) for ppl in dm_ppl.col_labels['Categories1']])
    # Compute total number of households
    arr_hh_tot = np.sum(dm_ppl.array, axis=-1)
    # household-size x nb_household / tot nb households = avg household-size
    arr_ppl_w_hh = np.sum(dm_ppl.array[:, :, :, :] * ppl_int[np.newaxis, np.newaxis, np.newaxis, :], axis=-1)
    # Sum together all houses (since it is a nan sum I will overwrite it with the actual sum)
    dm_ppl.group_all('Categories1')
    # Compute average household size in number of people
    arr_hh_size = arr_ppl_w_hh / arr_hh_tot
    dm_ppl.add(arr_hh_size, dim='Variables', col_label='lfs_household-size', unit='people')
    dm_ppl.rename_col('PER', 'lfs_households', dim='Variables')
    # replace household size with avg household size
    dm_ppl.fill_nans(dim_to_interp='Years')
    # Number of households
    idx = dm_ppl.idx
    dm_ppl.array[:, :, idx['lfs_households']] = arr_hh_tot[:, :, 0]

    return dm_ppl


def get_household_size(eustat_code, dict_iso2):

    ##### Household-size data eurostat
    filter = {'geo\TIME_PERIOD': list(dict_iso2.keys())}
    mapping_dim = {'Country': 'geo\TIME_PERIOD',
                   'Variables': 'unit'}
    dm_hs = get_data_api_eurostat(eustat_code, filter, mapping_dim, unit='people', years=years_ots)
    dm_hs.rename_col('AVG', 'household-size', dim='Variables')

    for i in range(2):
        window_size = 3  # Change window size to control the smoothing effect
        data_smooth = moving_average(dm_hs.array, window_size, axis=dm_hs.dim_labels.index('Years'))
        dm_hs.array[:, 1:-1, ...] = data_smooth

    # Treat Slovakia differently because of specific trend
    # Constant extrapolation instead of linear fitting
    dm_hs_slovakia = dm_hs.filter({'Country': ['Slovakia']})
    dm_hs.drop('Country', 'Slovakia')
    dm_hs_slovakia.fill_nans('Years')
    dm_hs.append(dm_hs_slovakia, dim='Country')

    linear_fitting(dm_hs, years_ots=years_ots)

    dm_hs.sort('Country')

    return dm_hs


def estimate_household_size_fts_from_ots(dm_ots, start_t):

    dm_fts_BAU = linear_forecast_BAU(dm_ots, start_t, years_ots, years_fts)

    # Household-size is actually a fxa, all levels have the same value
    dict_fts = dict()
    for level in range(4):
        level = level + 1
        dict_fts[level] = dm_fts_BAU

    return dict_fts


# Set the timestep for historical years & scenarios
years_ots = create_years_list(start_year=1990, end_year=2023, step=1, astype=int)
years_fts = create_years_list(start_year=2025, end_year=2050, step=5, astype=int)

dict_iso2 = eurostat_iso2_dict()
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

# Update household size
update_household_size = True
if update_household_size:
    # OTS
    dm_household_size = get_household_size('ilc_lvph01', dict_iso2)
    # FTS dict
    dict_hs_fts = estimate_household_size_fts_from_ots(dm_household_size, start_t=2012)
    # Update csv file
    file = 'lifestyles_floor-intensity.csv'
    # csv_database_reformat(file)
    update_database_from_dm(dm_household_size, filename=file, lever='floor-intensity', level=0, module='lifestyles')
    for lev, dm_fts in dict_hs_fts.items():
        update_database_from_dm(dm_fts, filename=file, lever='floor-intensity', level=lev, module='lifestyles')


# Household size is a fixed assumption and not an ots

print('Hello')