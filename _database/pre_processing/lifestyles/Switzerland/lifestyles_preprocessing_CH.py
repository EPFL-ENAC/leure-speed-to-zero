import numpy as np
from model.common.auxiliary_functions import interpolate_nans, add_missing_ots_years
from _database.pre_processing.api_routines_CH import get_data_api_CH
from scipy.stats import linregress


def linear_fitting(dm, years_ots):

    # Define a function to apply linear regression and extrapolate
    def extrapolate_to_year(arr, years, target_year):
        slope, intercept, _, _, _ = linregress(years, arr)
        extrapolated_value = intercept + slope * target_year

        return extrapolated_value

    start_year = int(years_ots[0])
    base_year = int(years_ots[-1])
    # Apply the function along the last axis (years axis)
    array_reshaped = np.moveaxis(dm.array, 1, -1)
    extrapolated_data = np.apply_along_axis(extrapolate_to_year, axis=-1, arr=array_reshaped, years=dm.col_labels['Years'],
                                            target_year=start_year)
    dm.add(extrapolated_data, dim='Years', col_label=[start_year])

    # Add missing ots years as nan
    dm = add_missing_ots_years(dm, startyear=start_year, baseyear=base_year)

    # Fill nan
    dm.fill_nans(dim_to_interp='Years')

    return


def create_ots_years_list(years_setting):
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int).astype(str))
    return years_ots


###############################
### POPULATION - deprecated ###
###############################
def deprecated_extract_lfs_population_total(years_ots):
    # !FIXME: you should rather download the resident population and not the citizens
    # Demographic balance by institutional units
    table_id = "px-x-0102020000_201"
    structure = get_data_api_CH(table_id, mode='example')

    filter = {'Year': years_ots,
              'Canton (-) / District (>>) / Commune (......)': ['Switzerland', '- Vaud'],
              'Citizenship (category)': 'Citizenship (category) - total',
              'Sex': 'Sex - total',
              'Demographic component': 'Population on 1 January'}

    mapping_dim = {'Country': 'Canton (-) / District (>>) / Commune (......)',
                   'Years': 'Year',
                   'Variables': 'Demographic component'}


    dm_lfs_pop = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim, units=['inhabitants'])

    dm_lfs_pop.rename_col('- Vaud', 'Vaud', dim='Country')
    dm_lfs_pop.rename_col('Population on 1 January', 'lfs_population_total', dim='Variables')

    return dm_lfs_pop


######################################
### POPULATION by age - deprecated ###
######################################
def deprecated_extract_lfs_demography_age():
    # ! FIXME: this database is missing many years, find another one model the missing years
    table_id = 'px-x-0102010000_103'
    structure = get_data_api_CH(table_id, mode='example')

    # Extract all age classes
    filter = {'Year': structure['Year'],
              'Canton (-) / District (>>) / Commune (......)': ['Switzerland', '- Vaud'],
              'Population type': ['Permanent resident population', 'Non permanent resident population'],
              'Sex': ['Male', 'Female'],
              'Marital status': 'Marital status - total',
              'Age class': structure['Age class']}

    mapping_dim = {'Country': 'Canton (-) / District (>>) / Commune (......)',
                   'Years': 'Year',
                   'Variables': 'Population type',
                   'Categories1': 'Sex',
                   'Categories2': 'Age class'}
    # Extract population by age group data
    dm_lfs_pop_age = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                     units=['inhabitants', 'inhabitants'])
    # Group age categories
    dm_lfs_pop_age.groupby({'below19': ['0-4 years', '5-9 years', '10-14 years', '15-19 years'],
                            'age20-29': ['20-24 years', '25-29 years'],
                            'age30-54': ['30-34 years', '35-39 years', '40-44 years', '45-49 years', '50-54 years'],
                            'age55-64': ['55-59 years', '60-64 years'],
                            'above65': ['65-69 years', '70-74 years', '75-79 years', '80-84 years', '85-89 years',
                                        '90-94 years', '95-99 years', '100 years or older']},
                            dim='Categories2', inplace=True, regex=False)
    # Rename sex
    dm_lfs_pop_age.rename_col('Male', 'male', dim='Categories1')
    dm_lfs_pop_age.rename_col('Female', 'female', dim='Categories1')
    # Rename Vaud
    dm_lfs_pop_age.rename_col('- Vaud', 'Vaud', 'Country')
    # Group permanent and non-permanent (permis C / citizenship and other)
    dm_lfs_pop_age.groupby({'lfs_demography': ['Permanent resident population', 'Non permanent resident population']},
                           dim='Variables', inplace=True, regex=False)
    # Extract age class total to compare with tot population data
    dm_tot_resident_pop = dm_lfs_pop_age.filter({'Categories2': ['Age class - total']}, inplace=False)
    dm_lfs_pop_age.drop('Categories2', 'Age class - total')
    # Join sex and age group
    dm_lfs_pop_age = dm_lfs_pop_age.flatten(sep='-')

    # Drop sex
    dm_tot_resident_pop.group_all('Categories1', inplace=True)

    return dm_lfs_pop_age


########################
###    POPULATION    ###
### tot & by age new ###
########################
def extract_lfs_pop(years_ots):
    # Demographic balance by age and canton
    table_id = 'px-x-0102020000_104'
    structure, title = get_data_api_CH(table_id, mode='example')

    # Extract all age classes
    filter = {'Year': years_ots,
              'Canton': ['Switzerland', 'Vaud'],
              'Citizenship (category)': 'Citizenship (category) - total',  # Swiss and non-Swiss resident
              'Sex': ['Male', 'Female'],
              'Age': structure['Age'],
              'Demographic component': 'Population on 1 January'}

    mapping_dim = {'Country': 'Canton',
                   'Years': 'Year',
                   'Variables': 'Demographic component',
                   'Categories1': 'Sex',
                   'Categories2': 'Age'}
    # Extract population by age group data
    dm_lfs_pop_age = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                     units=['inhabitants'])

    dm_lfs_pop_tot = dm_lfs_pop_age.filter({'Categories2': ['Age - total']})
    dm_lfs_pop_age.drop(dim='Categories2', col_label='Age - total')
    dm_lfs_pop_age.rename_col_regex(' years', '', dim='Categories2')
    dm_lfs_pop_age.rename_col_regex(' year', '', dim='Categories2')
    dm_lfs_pop_age.rename_col('99 or older', '99', dim='Categories2')
    dm_lfs_pop_age.drop(dim='Categories2', col_label='No indication')

    # Group ages by category
    group_dict = {
        'below19': [],
        'age20-29': [],
        'age30-54': [],
        'age55-64': [],
        'above65': [],
    }
    for age in dm_lfs_pop_age.col_labels['Categories2']:
        if int(age) <= 19:
            group_dict['below19'].append(age)
        elif (int(age) >= 20) and (int(age) <= 29):
            group_dict['age20-29'].append(age)
        elif (int(age) >= 30) and (int(age) <= 54):
            group_dict['age30-54'].append(age)
        elif (int(age) >= 55) and (int(age) <= 64):
            group_dict['age55-64'].append(age)
        elif int(age) >= 65:
            group_dict['above65'].append(age)

    dm_lfs_pop_age.groupby(group_dict, 'Categories2', inplace=True, regex=False)
    # Rename sex
    dm_lfs_pop_age.rename_col('Male', 'male', dim='Categories1')
    dm_lfs_pop_age.rename_col('Female', 'female', dim='Categories1')
    dm_lfs_pop_age.rename_col('Population on 1 January', 'lfs_demography', dim='Variables')
    dm_lfs_pop_age = dm_lfs_pop_age.flatten(sep='-')

    dm_lfs_pop_tot.group_all('Categories2')
    dm_lfs_pop_tot.group_all('Categories1')
    dm_lfs_pop_tot.rename_col('Population on 1 January', 'lfs_population_total', dim='Variables')
    return dm_lfs_pop_age, dm_lfs_pop_tot


########################
### URBAN POPULATION ###
########################
def extract_lfs_urban_share(years_ots):
    # Suisse urbaine: sélection de variables selon la typologie urbain-rural
    table_id = 'px-x-2105000000_404'
    structure, title = get_data_api_CH(table_id, mode='example', language='fr')

    # Extract all age classes
    filter = {'Année': structure['Année'],
              'Résultat': 'Valeur',
              'Variable': 'Population résidante permanente, total',  # Swiss and non-Swiss resident
              'Typologie urbain-rural': structure['Typologie urbain-rural']}

    mapping_dim = {'Country': 'Résultat',
                   'Years': 'Année',
                   'Variables': 'Typologie urbain-rural'}

    # Extract urban / rural pop
    dm_lfs_urban = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim,
                                   units=['inhabitants', 'inhabitants', 'inhabitants'], language='fr')
    dm_lfs_urban.rename_col('Valeur', 'Switzerland', dim='Country')
    dm_lfs_urban.groupby({'non-urban': ['Intermédiaire (périurbain dense et centres ruraux)', 'Rural'],
                          'urban': ['Urbain']}, dim='Variables', inplace=True, regex=False)

    # Perform linear extrapolation all the way back to 1990
    linear_fitting(dm_lfs_urban, years_ots)

    # Compute urban share of total population
    dm_lfs_urban.operation('urban', '+', 'non-urban', out_col='total', unit='inhabitants', dim='Variables')
    dm_lfs_urban.operation('urban', '/', 'total', out_col='lfs_demography_urban-population', unit='%', dim='Variables',
                           div0='error')
    dm_lfs_urban.filter({'Variables': ['lfs_demography_urban-population']}, inplace=True)

    # Vaud urban pop rate as CH
    dm_lfs_urban_VD = dm_lfs_urban.copy()
    dm_lfs_urban_VD.rename_col('Switzerland', 'Vaud', 'Country')

    dm_lfs_urban.append(dm_lfs_urban_VD, dim='Country')

    return dm_lfs_urban


########################
####   FLOOR-AREA   ####
########################
def extract_lfs_floor_space(years_ots, dm_lfs_tot_pop):
    table_id = 'px-x-0902020200_103'
    structure, title = get_data_api_CH(table_id, mode='example', language='fr')

    # Extract buildings floor area
    filter = {'Année': structure['Année'],
              'Canton (-) / District (>>) / Commune (......)': ['Suisse', ' - Vaud'],
              'Catégorie de bâtiment': structure['Catégorie de bâtiment'],
              'Surface du logement': structure['Surface du logement'],
              'Epoque de construction': structure['Epoque de construction']}
    mapping_dim = {'Country': 'Canton (-) / District (>>) / Commune (......)', 'Years': 'Année',
                   'Variables': 'Catégorie de bâtiment', 'Categories1': 'Surface du logement',
                   'Categories2': 'Epoque de construction'}
    unit_all = ['number'] * len(structure['Catégorie de bâtiment'])
    # Get api data
    dm_floor_area = get_data_api_CH(table_id, mode='extract', filter=filter, mapping_dims=mapping_dim, units=unit_all,
                                    language='fr')

    # Pre-processing

    ## Rename & Group
    dm_floor_area.rename_col(['Suisse', ' - Vaud'], ['Switzerland', 'Vaud'], dim='Country')
    dm_floor_area.group_all('Categories2')
    dm_floor_area.groupby({'lfs_dwellings': '.*'}, dim='Variables', regex=True, inplace=True)
    # !FIXME you are here, you should find the total floor area. Alternatively dowload the per capita floor area data
    dm_num_bld = dm_floor_area.group_all('Categories1', inplace=False)

    ## Compute total floor space
    dm_floor_area.rename_col_regex(' m2', '', 'Categories1')
    # The average size for less than 30 is a guess, as is the average size for 150+,
    # we will use the data from bfs to calibrate
    avg_size = {'<30': 25, '30-49': 39.5, '50-69': 59.5, '70-99': 84.5, '100-149': 124.5, '150+': 175}
    idx = dm_floor_area.idx
    for size in dm_floor_area.col_labels['Categories1']:
        dm_floor_area.array[:, :, :, idx[size]] = avg_size[size] * dm_floor_area.array[:, :, :, idx[size]]
    dm_floor_area.rename_col('lfs_dwellings', 'lfs_floor-area', 'Variables')
    dm_floor_area.units['lfs_floor-area'] = 'm2'
    dm_floor_area.group_all('Categories1')

    ## Calibrate
    # From https://www.bfs.admin.ch/bfs/en/home/statistics/construction-housing/dwellings/size.html#accordion1719560162958
    # In 2022 the average floor space per dwelling was 99m2. The relative stability observed since 2000 (97m2)
    # can be explained by the fact that dwellings built prior to 1981 (60% of the housing stock) have an average floor space
    # of less than 100m2. The size of more recent dwellings, however, is larger, and dwellings built between 2001 and 2005
    # have an average floor space of 131m2.
    # Compute average size of dwelling
    avg_floor_space_CH_2022_m2 = 99
    dm_floor_area.append(dm_num_bld, dim='Variables')
    dm_floor_area.operation('lfs_floor-area', '/', 'lfs_dwellings', dim='Variables', out_col='lfs_avg-floor-size',
                            unit='m2')
    cal_factor = avg_floor_space_CH_2022_m2 / dm_floor_area.array[
        idx['Switzerland'], idx[2022], idx['lfs_avg-floor-size']]
    dm_floor_area.filter({'Variables': ['lfs_avg-floor-size']}, inplace=True)
    dm_floor_area.array = dm_floor_area.array * cal_factor

    # Linear fitting
    linear_fitting(dm_floor_area, years_ots)
    linear_fitting(dm_num_bld, years_ots)

    # Recompute total floor-area = avg-floor-size * nb_dwellings
    dm_floor_area.append(dm_num_bld, dim='Variables')
    dm_floor_area.operation('lfs_avg-floor-size', '*', 'lfs_dwellings', out_col='lfs_floor-area', unit='m2')

    # Compute floor-area per capita
    dm_floor_area.append(dm_lfs_tot_pop, dim='Variables')
    dm_floor_area.operation('lfs_floor-area', '/', 'lfs_population_total', out_col='lfs_floor-intensity_space-cap',
                            unit='m2/cap')

    dm_floor_area.filter({'Variables': ['lfs_floor-intensity_space-cap']}, inplace=True)

    return dm_floor_area


years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
years_ots = create_ots_years_list(years_setting)

# Get population total and by age group (ots)
dm_lfs_age, dm_lfs_tot_pop = extract_lfs_pop(years_ots)
# Get urban share (ots)
# dm_lfs_urban_pop = extract_lfs_urban_share(years_ots)
# Get floor area (ots)
dm_lfs_floor_area = extract_lfs_floor_space(years_ots, dm_lfs_tot_pop)
print('Hello')


