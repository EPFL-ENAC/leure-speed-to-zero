import pandas as pd
from model.common.data_matrix_class import DataMatrix
import numpy as np
from model.common.auxiliary_functions import linear_fitting

def get_CDD_data():
    # The datasource for the CDD is Eurostat, base temperature is 21, threshold is 24.
    file = 'Eurostat_CDD.xlsx'
    data_path = 'data/'
    rows_to_skip = list(range(8)) + [9] + [39, 40, 41]
    df_cdd = pd.read_excel(data_path+file, sheet_name='Sheet 1', skiprows=rows_to_skip)
    df_cdd.rename({'TIME': 'Country'}, axis=1, inplace=True)
    # It melts a short format to a long format, var_name is all of the columns except the one specified in id_vars
    df_melted = pd.melt(df_cdd, id_vars=['Country'], var_name='Years', value_name='clm_CDD[daysK]')
    dm_cdd = DataMatrix.create_from_df(df_melted, num_cat=0)
    dm_cdd.rename_col('European Union - 27 countries (from 2020)', 'EU27', dim='Country')
    return dm_cdd


def get_HDD_data():
    file = 'Eurostat_HDD.xlsx'
    data_path = 'data/'
    rows_to_skip = list(range(8)) + [9] + [39, 40, 41]
    df_hdd = pd.read_excel(data_path+file, sheet_name='Sheet 1', skiprows=rows_to_skip)
    df_hdd.rename({'TIME': 'Country'}, axis=1, inplace=True)
    # It melts a short format to a long format, var_name is all of the columns except the one specified in id_vars
    df_melted = pd.melt(df_hdd, id_vars=['Country'], var_name='Years', value_name='clm_HDD[daysK]')
    dm_hdd = DataMatrix.create_from_df(df_melted, num_cat=0)
    dm_hdd.rename_col('European Union - 27 countries (from 2020)', 'EU27', dim='Country')
    return dm_hdd


def get_new_building():
    file = 'Floor-area_new_built.xlsx'
    data_path = 'data/'
    rows_to_skip = [0, 506, 507]
    df_new = pd.read_excel(data_path+file, sheet_name='Export', skiprows=rows_to_skip)
    df_new.rename({'Year': 'Years', 'Value': 'bld_floor-area_new_residential[m2]',
                   'Value.1': 'bld_floor-area_new_non-residential[m2]'}, axis=1, inplace=True)
    dm_new = DataMatrix.create_from_df(df_new, num_cat=1)

    return dm_new


def get_renovation_rate():
    file = 'renovation_rates.xlsx'
    data_path = 'data/'
    df_rr_res = pd.read_excel(data_path + file, sheet_name='Renovation_rates_residential')
    df_rr_nonres = pd.read_excel(data_path + file, sheet_name='Renovation_rates_non_residentia')
    df_rr_res.rename({'Energy related: “Light” ': 'bld_ren-rate_sha_residential[%]',
                      'Energy related: “Medium” ': 'bld_ren-rate_med_residential[%]',
                      'Energy related: “Deep” ': 'bld_ren-rate_dep_residential[%]'}, axis=1, inplace=True)
    df_rr_nonres.rename({'Energy related: “Light” ': 'bld_ren-rate_sha_non-residential[%]',
                         'Energy related: “Medium” ': 'bld_ren-rate_med_non-residential[%]',
                         'Energy related: “Deep” ': 'bld_ren-rate_dep_non-residential[%]'}, axis=1, inplace=True)
    # Drop useless cols
    df_rr_res.drop(['Energy related: “Total” ', 'Energy related: “below Threshold” '], axis=1, inplace=True)
    df_rr_nonres.drop(['Energy related: “Total” ', 'Energy related: “below Threshold” '], axis=1, inplace=True)
    # Remove space in Country col
    df_rr_res['Country'] = df_rr_res['Country'].str.strip()
    df_rr_nonres['Country'] = df_rr_nonres['Country'].str.strip()
    # These data are the average between 2012 - 2016
    df_rr_res['Years'] = 2014
    df_rr_nonres['Years'] = 2014
    df_rr = pd.merge(df_rr_res, df_rr_nonres, on=['Country', 'Years'], how='inner')
    dm_rr = DataMatrix.create_from_df(df_rr, num_cat=2)
    # Duplicate 2014 values for all years
    for y in list(range(1990, 2022)):
        if y != 2014:
            # Take first year value
            new_array = dm_rr.array[:, 0, ...]
            dm_rr.add(new_array, dim='Years', col_label=[y], unit='%')
    dm_rr.sort(dim='Country')

    return dm_rr


def sub_routine_get_uvalue_by_element():
    # Load u-values by element, construction-period, building type
    file = 'U_value_Europe.xlsx'
    data_path = 'data/'
    rows_to_skip = [1, 191, 192]
    df_u_wall = pd.read_excel(data_path + file, sheet_name='U-value - wall', skiprows=rows_to_skip)
    df_u_window = pd.read_excel(data_path + file, sheet_name='U-value - window', skiprows=rows_to_skip)
    df_u_roof = pd.read_excel(data_path + file, sheet_name='U-value - roof', skiprows=rows_to_skip)
    df_u_ground = pd.read_excel(data_path + file, sheet_name='U-value - ground floor', skiprows=rows_to_skip)
    # Rename dictionary
    dict_ren = {'Building use': 'Country', 'Unnamed: 1': 'Construction period'}
    df_u_wall.rename(dict_ren, axis=1, inplace=True)
    df_u_window.rename(dict_ren, axis=1, inplace=True)
    df_u_roof.rename(dict_ren, axis=1, inplace=True)
    df_u_ground.rename(dict_ren, axis=1, inplace=True)
    # Remove useless cols
    drop_cols = ['All uses']
    df_u_wall.drop(drop_cols, axis=1, inplace=True)
    df_u_window.drop(drop_cols, axis=1, inplace=True)
    df_u_roof.drop(drop_cols, axis=1, inplace=True)
    df_u_ground.drop(drop_cols, axis=1, inplace=True)
    return df_u_wall, df_u_window, df_u_roof, df_u_ground


def compute_weighted_u_value(df_u_wall, df_u_window, df_u_roof, df_u_ground):
    # Load u-values by element, construction-period, building type
    file_weight = 'Uvalues_literature.xlsx'
    data_path = 'data/'
    df_u_weight = pd.read_excel(data_path + file_weight, sheet_name='weight_element')
    df_u_weight.set_index('Element', inplace=True)

    # Weight u-values by area of element for single-family-households
    w_sfh = df_u_weight['bld_area_weight_sfh[%]']
    sfh_col = 'Single-family buildings'
    df_u_wall[sfh_col] = w_sfh['Facade'] * df_u_wall[sfh_col]
    df_u_roof[sfh_col] = w_sfh['Roof'] * df_u_roof[sfh_col]
    df_u_window[sfh_col] = w_sfh['Windows'] * df_u_roof[sfh_col]
    df_u_ground[sfh_col] = w_sfh['Cellar'] * df_u_ground[sfh_col]

    # Weight u-values by area of element for other buildings
    # We apply the multi-family house area weight to all buildings except sfh
    others_col = [col for col in df_u_wall.columns if col not in
                  ['Country', 'Construction period', 'Single-family buildings']]
    w_mfh = df_u_weight['bld_area_weight_mfh[%]']
    for col in others_col:
        df_u_wall[col] = w_mfh['Facade'] * df_u_wall[col]
        df_u_roof[col] = w_mfh['Roof'] * df_u_roof[sfh_col]
        df_u_window[col] = w_mfh['Windows'] * df_u_roof[sfh_col]
        df_u_ground[col] = w_mfh['Cellar'] * df_u_ground[sfh_col]

    # Compute uvalue as weighted average of element u-value
    df_uvalue = df_u_wall
    u_cols = [col for col in df_u_wall.columns if col not in ['Country', 'Construction period']]
    for col in u_cols:
        df_uvalue[col] = df_uvalue[col] + df_u_roof[col] + df_u_window[col] + df_u_ground[col]
    return df_uvalue


def extract_u_value(df_uvalue):

    # To obtain the u-value of new buildings replace the construction period with the middle year
    df_uvalue[['start_y', 'end_y']] = df_uvalue['Construction period'].str.split('-', expand=True)
    # Replace now with 2020
    df_uvalue['end_y'] = df_uvalue['end_y'].str.replace('now', '2020')
    df_uvalue[['start_y', 'end_y']] = df_uvalue[['start_y', 'end_y']].astype(int)
    df_uvalue['Years'] = ((df_uvalue['end_y'] + df_uvalue['start_y'])/2).astype(int)
    df_uvalue.drop(['start_y', 'end_y'], axis=1, inplace=True)

    # df_uvalue
    df_uvalue.drop(['Construction period'], axis=1, inplace=True)
    # add unit
    df_uvalue = df_uvalue.add_suffix('[W/(m2K)]')
    df_uvalue = df_uvalue.add_prefix('bld_uvalue_')
    df_uvalue.rename({'bld_uvalue_Country[W/(m2K)]': 'Country',
                      'bld_uvalue_Years[W/(m2K)]': 'Years'}, axis=1, inplace=True)

    return df_uvalue


def extract_floor_area_stock():
    file = 'BSO_floor_area_2020.xlsx'
    data_path = 'data/'
    rows_to_skip = [1, 198, 199]
    df_area = pd.read_excel(data_path + file, sheet_name='Export', skiprows=rows_to_skip)
    dict_ren = {'Building use': 'Construction period', 'Unnamed: 1': 'Country'}
    df_area.rename(dict_ren, axis=1, inplace=True)
    # To obtain the u-value of new buildings replace the construction period with the middle year
    df_area[['start_y', 'end_y']] = df_area['Construction period'].str.split('-', expand=True)
    # Replace now with 2020
    df_area['end_y'] = df_area['end_y'].str.replace('now', '2020')
    df_area[['start_y', 'end_y']] = df_area[['start_y', 'end_y']].astype(int)
    df_area['Years'] = ((df_area['end_y'] + df_area['start_y'])/2).astype(int)
    df_area_new = df_area.loc[df_area['Years']>=1990].copy()
    df_area.drop(['start_y', 'end_y'], axis=1, inplace=True)

    # Keep only buildings after 1990
    df_area.drop(['Construction period'], axis=1, inplace=True)
    # add unit
    df_area = df_area.add_suffix('[m2]')
    df_area = df_area.add_prefix('bld_floor-area_')
    df_area.rename({'bld_floor-area_Country[m2]': 'Country',
                        'bld_floor-area_Years[m2]': 'Years'}, axis=1, inplace=True)
    dm_area = DataMatrix.create_from_df(df_area, num_cat=1)

    # Compute the average yearly new floor-area constructed as the floor-area/construction period lenght
    df_area_new['period_length'] = df_area_new['end_y'] - df_area_new['start_y']
    df_area_new.drop(['start_y', 'end_y', 'Construction period'], axis=1, inplace=True)
    value_cols = set(df_area_new.columns) - {'Country', 'Years', 'period_length'}
    for col in value_cols:
        df_area_new[col] = df_area_new[col]/df_area_new['period_length']
    df_area_new.drop(['period_length'], axis=1, inplace=True)
    # add unit
    df_area_new = df_area_new.add_suffix('[m2]')
    df_area_new = df_area_new.add_prefix('bld_floor-area_new_')
    df_area_new.rename({'bld_floor-area_new_Country[m2]': 'Country',
                        'bld_floor-area_new_Years[m2]': 'Years'}, axis=1, inplace=True)
    dm_area_new = DataMatrix.create_from_df(df_area_new, num_cat=1)

    return dm_area, dm_area_new


def create_ots_years_list(years_setting):
    startyear: int = years_setting[0]  # Start year is argument [0], i.e., 1990
    baseyear: int = years_setting[1]  # Base/Reference year is argument [1], i.e., 2015
    lastyear: int = years_setting[2]  # End/Last year is argument [2], i.e., 2050
    step_fts = years_setting[3]  # Timestep for scenario is argument [3], i.e., 5 years
    years_ots = list(
        np.linspace(start=startyear, stop=baseyear, num=(baseyear - startyear) + 1).astype(int).astype(str))
    return years_ots


def get_uvalue_new_stock0(years_ots):
    # Gets the u-value for the new buildings, as well as the u-value of the building stock at t=baseyear
    # Load u-values by element, construction-period, building type
    df_u_wall, df_u_window, df_u_roof, df_u_ground = sub_routine_get_uvalue_by_element()
    # Weight u-values of element by area of element
    df_uvalue = compute_weighted_u_value(df_u_wall, df_u_window, df_u_roof, df_u_ground)
    # From df_uvalue keep only new built for construction period > 1990
    df_uvalue = extract_u_value(df_uvalue)
    # From df to dm
    dm_uvalue = DataMatrix.create_from_df(df_uvalue, num_cat=1)
    # Extract floor-area of building stock
    dm_area, dm_area_new = extract_floor_area_stock()
    dm_area.drop(dim='Country', col_label = 'EU27')
    # Get multi-family household value as weighted average of 'Apartment buildings', 'Multi-family buildings'
    dm_uvalue.append(dm_area, dim='Variables')
    dm_uvalue.operation('bld_uvalue', '*', 'bld_floor-area', out_col='bld_uxarea', unit='m2')
    dm_uvalue.groupby({'multi-family-households': ['Apartment buildings', 'Multi-family buildings']}, dim='Categories1', inplace=True)
    idx = dm_uvalue.idx
    dm_uvalue.array[:, :, idx['bld_uvalue'], idx['multi-family-households']] = \
        dm_uvalue.array[:, :, idx['bld_uxarea'], idx['multi-family-households']] /\
        dm_uvalue.array[:, :, idx['bld_floor-area'], idx['multi-family-households']]
    # Rename using Calculator names:
    cols_in = ['Educational buildings', 'Health buildings', 'Hotels and Restaurants', 'Offices',
               'Other non-residential buildings', 'Trade buildings', 'Single-family buildings']
    cols_out = ['education', 'health', 'hotels', 'offices', 'other', 'trade', 'single-family-households']
    dm_uvalue.rename_col(cols_in, cols_out, dim='Categories1')

    # Get right categories for new floor area
    dm_area_new.groupby({'multi-family-households': ['Apartment buildings', 'Multi-family buildings']},
                        dim='Categories1', inplace=True)
    dm_area_new.rename_col(cols_in, cols_out, dim='Categories1')

    # Compute dm_uvalue for initial stock
    dm_uvalue_stock0 = dm_uvalue.filter({'Years': [972, 1957, 1974, 1984]})
    dm_uvalue_stock0.groupby({1990: '.*'}, dim='Years', regex=True, inplace=True)
    dm_uvalue_stock0.array[:, :, idx['bld_uvalue'], :] = dm_uvalue_stock0.array[:, :, idx['bld_uxarea'], :]\
                                                         / dm_uvalue_stock0.array[:, :, idx['bld_floor-area'], :]
    dm_uvalue_stock0.filter({'Variables': ['bld_uvalue']}, inplace=True)

    # Extract dm_uvalue new
    dm_uvalue_new = dm_uvalue.filter({'Years': [1994, 2005, 2015]})
    dm_uvalue_new.filter({'Variables': ['bld_uvalue']}, inplace=True)
    dm_uvalue_new.rename_col('bld_uvalue', 'bld_uvalue_new', dim='Variables')
    # Linear fitting for missing years
    idx = dm_uvalue_stock0.idx
    max_start = dm_uvalue_stock0.array[:, 0, idx['bld_uvalue'], np.newaxis, :]
    min_end = np.min(dm_uvalue_new.array)*np.ones(shape=max_start.shape)
    linear_fitting(dm_uvalue_new, years_ots, max_t0=max_start, min_tb=min_end)

    # Compute share of floor area by building type, to determine floor-area stock for non-residential buildings
    dm_area_2020 = dm_uvalue.filter({'Variables': ['bld_floor-area']}, inplace=False)
    dm_area_2020.groupby({2020: '.*'}, dim='Years', regex=True, inplace=True)
    idx = dm_area_2020.idx
    arr_share = dm_area_2020.array[:, :, idx['bld_floor-area'], :] \
                / np.nansum(dm_area_2020.array[:, :, idx['bld_floor-area'], :], axis=-1, keepdims=True)
    dm_area_2020.add(arr_share, dim='Variables', col_label='bld_floor-area_share', unit='%')
    dm_area_2020.filter({'Variables': ['bld_floor-area_share']}, inplace=True)
    return dm_uvalue_new, dm_area_2020, dm_uvalue_stock0, dm_area_new


def estimate_floor_area(dm_new_group, dm_new_type, years_ots):
    # Compute share for sfh and mfh
    dm_new_res_type = dm_new_type.filter({'Categories1': ['single-family-households', 'multi-family-households']}, inplace=False)
    arr_res_share = dm_new_res_type.array / np.nansum(dm_new_res_type.array, axis=-1, keepdims=True)
    dm_new_res_type.add(arr_res_share, dim='Variables', col_label='bld_floor-area_share', unit='%')
    # Compute shares for non residential (commercial)
    dm_new_comm_type = dm_new_type.filter({'Categories1': ['education', 'health', 'hotels', 'offices', 'other', 'trade']}, inplace=False)
    arr_comm_share = dm_new_comm_type.array / np.nansum(dm_new_comm_type.array, axis=-1, keepdims=True)
    dm_new_comm_type.add(arr_comm_share, dim='Variables', col_label='bld_floor-area_share', unit='%')
    # Extrapolate to all the years available in dm_new_group
    years_tmp = dm_new_group.col_labels['Years']
    linear_fitting(dm_new_comm_type, years_tmp)
    linear_fitting(dm_new_res_type, years_tmp)
    # Multiply new floor-area group by the shares
    idx_g = dm_new_group.idx
    idx_c = dm_new_comm_type.idx
    dm_new_comm_type.array[:, 1:, idx_c['bld_floor-area_new'], :] \
        = dm_new_comm_type.array[:, 1:, idx_c['bld_floor-area_share'], :] \
          * dm_new_group.array[:, :, idx_g['bld_floor-area_new'], idx_g['non-residential'], np.newaxis]
    idx_r = dm_new_res_type.idx
    dm_new_res_type.array[:, 1:, idx_r['bld_floor-area_new'], :] \
        = dm_new_res_type.array[:, 1:, idx_r['bld_floor-area_share'], :] \
          * dm_new_group.array[:, :, idx_g['bld_floor-area_new'], idx_g['non-residential'], np.newaxis]
    # Join residential and commercial new floor area and apply linear extrapolation
    dm_new_res_type.append(dm_new_comm_type, dim='Categories1')
    dm_new_res_type.drop(dim='Variables', col_label='bld_floor-area_share')
    linear_fitting(dm_new_res_type, years_ots, min_t0=0, min_tb=0)

    return dm_new_res_type

years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
years_ots = create_ots_years_list(years_setting)

# Load CDD
dm_cdd = get_CDD_data()
# Load HDD
dm_hdd = get_HDD_data()
# Load renovation rates
dm_rr = get_renovation_rate()
# Load U-value for new buildings()
dm_uvalue_new, dm_area_2020, dm_uvalue_stock0, dm_new_2 = get_uvalue_new_stock0(years_ots)
# Load new building floor area
dm_new_1 = get_new_building()
# Reconcile two new build area estimates
dm_area_new = estimate_floor_area(dm_new_1, dm_new_2, years_ots)
del dm_new_1, dm_new_2

# I currently have u_new(t), u_stock(t0), stock(2020), new(t), ren-rate(t), cdd(t), hdd(t)
# Problem 1: I'm missing some countries: Switzerland, Vaud, Paris, (Norway), (EU27)
# Problem 2: what I actually need as input is demolition-rate(t), [stock(t) from Lifestyle for resident
# + I can use stock(2020) to determine floor-area for non-residential], ren-rate(t)
# (this is to obtain new(t), waste/demolition(t), renovated(t), unrenovated(t)).
# Problem 3: But to determine the u_stock(t) I also need: u_decrease per renovation type, and alpha
# (the share of renovation-rate per each renovation type) per renovation type.
# Problem 4: For calibration I could use stock(2020), but we also need the energy demand per building type.
# Problem 5: We need the number of days with temperatures above 24 and below 15
# + to create a variable for T_int_h and T_int_c and set it to 20 for all countries for ots,
# and explore different T_int for fts
# Problem 6: determine fts for all

# Let us load historical data for population and average m2/cap to compute the the demolition-rate.





print('Hello')