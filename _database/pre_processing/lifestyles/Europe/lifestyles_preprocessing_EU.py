import json
import numpy as np
import eurostat
import pandas as pd
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting

EU27_cntr_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland',
                  'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
                  'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden']

def create_ots_years_list(years_setting):
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int).astype(str))
    return years_ots


def get_pop_eurostat(code_pop, EU27_cntr_list):

    df_pop = eurostat.get_data_df(code_pop)

    # Step 1: Melt the dataframe to long format
    df_pop['age'] = df_pop['age'].str.replace('_', '', regex=False)
    df_pop['age_sex'] = 'lfs_' + df_pop['age'] + '_' + df_pop['sex'] + '[nb]'

    df_pop.drop(['freq', 'unit', 'age', 'sex'], axis=1, inplace=True)
    df_pop.rename(columns={'geo\TIME_PERIOD': 'Country'}, inplace=True)
    df_melted = pd.melt(df_pop, id_vars=['Country', 'age_sex'], var_name='Years', value_name='Population')

    # Step 2: Pivot the dataframe to have a column for each age group
    df_pivoted = df_melted.pivot_table(index=['Country', 'Years'], columns='age_sex', values='Population').reset_index()
    df_pivoted.sort_values(['Country', 'Years'], inplace=True)
    df_pivoted['Years'] = df_pivoted['Years'].astype(int)
    df_pivoted = df_pivoted.loc[df_pivoted['Years'] >= 1990].copy()

    # Get iso for EU countries
    f = open('../../country_codes_iso2.json')
    dict_iso2 = json.load(f)
    countries_to_keep = list(dict_iso2.keys())
    df_pivoted = df_pivoted[df_pivoted['Country'].isin(countries_to_keep)]
    df_pivoted['Country'] = df_pivoted['Country'].replace(dict_iso2)
    # Add France 1990 that is missing by using nans
    df_pivoted = df_pivoted.set_index(['Country', 'Years'])
    new_index = pd.MultiIndex.from_tuples([('France', 1990)], names=['Country', 'Years'])
    nan_row = pd.DataFrame(index=new_index, columns=df_pivoted.columns)
    df_pivoted = pd.concat([df_pivoted, nan_row])
    df_pivoted = df_pivoted.reset_index()

    # Create datamatrix
    dm = DataMatrix.create_from_df(df_pivoted, num_cat=2)

    # Set Germany to 1990 to np.nan
    idx = dm.idx
    dm.array[idx['Germany'], idx[1990], :, :] = np.nan
    # Drop Switzerland and EU27
    dm.drop(dim='Country', col_label=['Switzerland', 'EU27'])

    dm_pop_tot = dm.filter({'Categories1': ['TOTAL'], 'Categories2': ['T']}, inplace=False)
    dm_pop_tot = dm_pop_tot.flatten()
    dm_pop_tot.rename_col('TOTAL_T', 'population_total', dim='Categories1')
    dm_pop_tot = dm_pop_tot.flatten()
    dm_pop_tot.change_unit('lfs_population_total', 1, old_unit='nb', new_unit='inhabitants')
    cntr_to_interp = ['France', 'Germany']
    for c in cntr_to_interp:
        dm_cntr_tot = dm_pop_tot.filter({'Country': [c]})
        dm_cntr_tot.fill_nans(dim_to_interp='Years')
        dm_pop_tot.drop(col_label=c, dim='Country')
        dm_pop_tot.append(dm_cntr_tot, dim='Country')

    dm_pop_age = dm.copy()
    dm_pop_age.drop(dim='Categories1', col_label='TOTAL')
    dm_pop_age.drop(dim='Categories2', col_label='T')
    dm_pop_age.rename_col_regex('Y', '', dim='Categories1')
    group_dict = {
        'below19': ['LT1'],
        'age20-29': [],
        'age30-54': [],
        'age55-64': [],
        'above65': ['OPEN'],
    }
    dm_pop_age.drop(dim='Categories1', col_label='UNK')

    cntr_to_interp = ['France', 'Germany', 'Croatia']
    for c in cntr_to_interp:
        dm_cntr_age = dm_pop_age.filter({'Country': [c]})
        dm_cntr_age.fill_nans(dim_to_interp='Years')
        dm_pop_age.drop(col_label=c, dim='Country')
        dm_pop_age.append(dm_cntr_age, dim='Country')

    for age in dm_pop_age.col_labels['Categories1']:
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

    dm_pop_age.groupby(group_dict, inplace=True, dim='Categories1')
    dm_pop_age.rename_col('lfs', 'lfs_demography', dim='Variables')
    dm_pop_age.rename_col(['M', 'F'], ['male', 'female'], dim='Categories2')
    dm_pop_age.switch_categories_order('Categories1', 'Categories2')
    dm_pop_age = dm_pop_age.flatten()

    dm_EU27_tot = dm_pop_tot.groupby({'EU27': EU27_cntr_list}, dim='Country')
    dm_pop_tot.append(dm_EU27_tot, dim='Country')

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


#years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
#years_ots = create_ots_years_list(years_setting)

# Use following line to explore EUROSTAT database
#toc = eurostat.get_toc_df(agency='EUROSTAT', lang='en')
#toc_pop = eurostat.subset_toc_df(toc, 'population on 1 January by age')

# Code
dm_pop_age, dm_pop_tot = get_pop_eurostat('demo_pjan', EU27_cntr_list)


print('Hello')