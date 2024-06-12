import numpy as np
from model.common.data_matrix_class import DataMatrix
from scipy.interpolate import interp1d, CubicSpline
from model.common.io_database import read_database, update_database_from_db, read_database_w_filter
from model.common.constant_data_matrix_class import ConstantDataMatrix
import pandas as pd
import os
import re
import json
from os import listdir
from os.path import isfile, join
import pickle


def add_all_missing_fts_years(dm, baseyear, lastyear):
    # Given a DataMatrix in the style of EUcalc with years every 5 for fts, it returns a DataMatrix with all years
    # whose values are set to nan
    # Add missing years from 2016 to 2050
    missing_years = list(range(baseyear + 1, lastyear + 1))
    for y in dm.col_labels["Years"]:
        if y in missing_years: missing_years.remove(y)

    cols = {
        'Country': dm.col_labels["Country"],
        'Years': missing_years,
        'Variables': dm.col_labels['Variables']
    }
    dm_fts_missing = DataMatrix(col_labels=cols)
    cols = dm_fts_missing.col_labels
    dm_fts_missing.array = np.nan * np.ones(shape=(len(cols["Country"]), len(cols["Years"]), len(cols["Variables"])))
    dm.append(dm_fts_missing, dim="Years")
    dm.sort(dim="Years")

    return dm


def interpolate_nans(arr, x_values):
    nan_indices = np.isnan(arr)
    # Create an interpolation function with cubic spline
    arr[nan_indices] = np.interp(x_values[nan_indices], x_values[~nan_indices], arr[~nan_indices])
    return arr


def interpolate_nan_cubic(arr, x_values):
    # Create an interpolation function using cubic spline
    interp_func = interp1d(x_values[~np.isnan(arr)], arr[~np.isnan(arr)], kind='cubic', fill_value="extrapolate")
    # Interpolate the NaN values
    arr_interp = np.where(np.isnan(arr), interp_func(x_values), arr)
    return arr_interp


def interpolate_nan_smooth(arr, x_values):
    not_nan_indices = ~np.isnan(arr)

    if np.any(not_nan_indices):
        # Cubic spline interpolation for non-NaN values
        spline = CubicSpline(x_values[not_nan_indices], arr[not_nan_indices], bc_type='clamped')

        # Apply the spline function to the x_values
        arr_interp_spline = spline(x_values)

        # Clip the interpolated values to the range of the non-NaN values
        arr_interp = np.clip(arr_interp_spline, min(arr[not_nan_indices]), max(arr[not_nan_indices]))
    else:
        # If there are no non-NaN values, return the original array
        arr_interp = arr

    return arr_interp


def adjust_trend(dm, baseyear, expected_trend):
    # Takes a DataMatrix containing ots and fts, the baseyear and the expected_trend
    # if the actual trend is not following the expected trend it sets the 2050 value to the same at the 2015 value
    # (actually it sets it to the mean value of the last few years)
    if expected_trend == None:
        return dm
    # perform a mean over the last years
    last_ots_years = slice(dm.idx[baseyear - 5],
                           dm.idx[baseyear + 1])  # last_ots_years = range(dm.idx[baseyear-5], dm.idx[baseyear+1])
    last_ots_values = np.mean(dm.array[:, last_ots_years, ...], axis=1)
    increasing_loc = (dm.array[:, -1, ...] > last_ots_values)
    noise = dm.array[:, 0:dm.idx[baseyear], ...].std(axis=1)
    if expected_trend == "decreasing":
        dm.array[:, -1, ...] = np.where(increasing_loc, last_ots_values - noise, dm.array[:, -1, ...])
    if expected_trend == "increasing":
        dm.array[:, -1, ...] = np.where(~increasing_loc, last_ots_values + noise, dm.array[:, -1, ...])
    return dm


def flatten_curve_edges(dm, baseyear, length):
    idx = dm.idx
    for j in range(length):
        dm.array[:, idx[baseyear] + j, ...] = dm.array[:, idx[baseyear], ...]
        dm.array[:, -1 - j, ...] = dm.array[:, -1, ...]
    return dm


def remove_2015_from_fts_db(filename, lever):
    # Remove year 2015 in fts
    # Read db
    df_db = read_database(filename, lever, db_format=True)
    # Read fts
    df_db_fts = df_db.loc[df_db["level"] != 0]
    df_db_fts = df_db_fts.loc[df_db_fts['timescale'] != 2015]
    # Read ots
    df_db_ots = df_db.loc[df_db["level"] == 0]
    df_db = pd.concat([df_db_ots, df_db_fts], axis=0)
    df_db.sort_values(by=['geoscale', 'timescale'], axis=0, inplace=True)

    # Extract full path to file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    # Write to file
    df_db.to_csv(file, sep=";", index=False)
    return


def merge_ots_fts(df_ots, df_fts, levername):
    df_ots.drop(columns=[levername], inplace=True)
    df_fts.drop(columns=[levername], inplace=True)
    rename_ots = {}
    for col in df_ots.columns:
        rename_ots[col] = col.replace('ots_', '')
    df_ots.rename(columns=rename_ots, inplace=True)
    rename_fts = {}
    for col in df_fts.columns:
        rename_fts[col] = col.replace('fts_', '')
    df_fts.rename(columns=rename_fts, inplace=True)
    df = pd.concat([df_ots, df_fts], axis=0)
    df.sort_values(by=['Country', 'Years'], axis=0, inplace=True)
    return df


def compute_stock(dm, rr_regex, tot_regex, waste_col, new_col):
    # Function to compute stock MFA. It determines the waste and the new input
    # based on the total and the renewal_rate.
    # rr_regex: is a regex pattern to find the renewal rate data in dm 'Variables'
    # tot_regex: is a regex pattern to find the tot stock in dm 'Variables'
    # waste_col and new_col are the column names of the output Variables that will be added to dm
    rr_pattern = re.compile(rr_regex)
    tot_pattern = re.compile(tot_regex)
    for col in dm.col_labels['Variables']:
        if re.match(rr_pattern, col):
            rr_col = col
        elif re.match(tot_pattern, col):
            tot_col = col
    # waste(ti + n) = [ (n-1)/n * tot(ti+n) + 1/n *tot(ti) ] +  [ (n-1)/n * RR(ti+n) + 1/n *RR(ti) ]
    # create tot(ti) and RR(ti)
    dm.lag_variable(tot_pattern, 1, "_tmn")
    dm.lag_variable(rr_pattern, 1, "_tmn")
    # compute n as delta(years)
    years = np.array(dm.col_labels['Years'])
    n = np.diff(years)
    n = np.concatenate((np.array([n[0]]), n))  # add value for first year to have the same size
    idx = dm.index_all()
    # Compute tot and rr at time t-1
    dm.array = np.moveaxis(dm.array, 1, -1)  # moves years dim at the end
    tot_tm1 = ((n - 1) / n * dm.array[:, idx[tot_col], ...] + 1 / n * dm.array[:, idx[tot_col + '_tmn'], ...]).astype(
        int)
    rr_tm1 = (n - 1) / n * dm.array[:, idx[rr_col], ...] + 1 / n * dm.array[:, idx[rr_col + '_tmn'], ...]
    dm.array = np.moveaxis(dm.array, -1, 1)  # moves years back in position
    tot_tm1 = np.moveaxis(tot_tm1, -1, 1)
    rr_tm1 = np.moveaxis(rr_tm1, -1, 1)
    # waste = renewal_rate(t-1) x tot(t-1)
    waste_tmp = (rr_tm1 * tot_tm1).astype(int)
    # tot(t) = tot(t-1) + new(t) - waste(t) -> new(t) = tot(t) - tot(t-1) + waste(t)
    new_tmp = (waste_tmp + dm.array[:, :, idx[tot_col], ...] - tot_tm1).astype(int)
    # Deal with negative values
    # Check for negative values in new_cols
    tot = dm.array[:, :, dm.idx[tot_col], :]
    new_tmp[new_tmp < 0] = 0
    waste_tmp[new_tmp < 0] = (tot_tm1[new_tmp < 0] - tot[new_tmp < 0]).astype(int)
    # Add waste and new to datamatrix
    dm.add(waste_tmp, dim='Variables', col_label=waste_col, unit='number')
    dm.add(new_tmp, dim='Variables', col_label=new_col, unit='number')
    # Remove the lagged columns
    dm.drop(dim='Variables', col_label='.*_tmn')
    return


def dm_lever_dict_from_df(df_fts, levername, num_cat):
    levels = list(set(df_fts[levername]))
    dict_dm = {}
    for i in levels:
        df_fts_i = df_fts.loc[df_fts[levername] == i].copy()
        df_fts_i.drop(columns=[levername], inplace=True)
        rename_fts = {}
        for col in df_fts_i.columns:
            rename_fts[col] = col.replace('fts_', '')
        df_fts_i.rename(columns=rename_fts, inplace=True)
        df_fts_i.sort_values(by=['Country', 'Years'], axis=0, inplace=True)
        dict_dm[i] = DataMatrix.create_from_df(df_fts_i, num_cat=num_cat)
    return dict_dm


def read_database_to_ots_fts_dict(file, lever, num_cat, baseyear, years, dict_ots, dict_fts, df_ots=None, df_fts=None,
                                  filter_dict=None):
    # It reads the database in data/csv with name file and returns the ots and the fts in form
    # of datamatrix accessible by dictionaries:
    # e.g.  dict_ots = {lever: dm_ots}
    #       dict_fts = {lever: {1: dm_fts_level_1, 2: dm_fts_level_2, 3: dm_fts_level_3, 4: dm_fts_level_4}}
    # where file is the name of the file and lever is the levername
    if df_ots is None and df_fts is None:
        if filter_dict is None:
            df_ots, df_fts = read_database(file, lever, level='all')
        else:
            df_ots, df_fts = read_database_w_filter(file, lever, filter_dict)
    # Drop from fts the baseyear and earlier years if any
    df_fts.drop(df_fts[df_fts.Years <= baseyear].index, inplace=True)
    # Keep fts only one every five years
    df_fts = df_fts[df_fts['Years'].isin(years)].copy()
    # Keep only years from 1990
    df_ots.drop(df_ots[df_ots.Years > baseyear].index, inplace=True)
    df_ots = df_ots[df_ots['Years'].isin(years)].copy()
    dict_lever = dm_lever_dict_from_df(df_fts, lever, num_cat)
    # Remove 'ots_' and drop lever
    df_ots.drop(columns=[lever], inplace=True)
    rename_ots = {}
    for col in df_ots.columns:
        rename_ots[col] = col.replace('ots_', '')
    df_ots.rename(columns=rename_ots, inplace=True)
    # Sort by country years
    df_ots.sort_values(by=['Country', 'Years'], axis=0, inplace=True)
    dm_ots = DataMatrix.create_from_df(df_ots, num_cat)
    dict_ots[lever] = dm_ots
    dict_fts[lever] = dict_lever
    return dict_ots, dict_fts


def read_database_to_ots_fts_dict_w_groups(file, lever, num_cat_list, baseyear, years, dict_ots, dict_fts, column: str,
                                           group_list: list):
    # It reads the database in data/csv with name file and returns the ots and the fts in form
    # of datamatrix accessible by dictionaries:
    # e.g.  dict_ots = {lever: {group1: dm_1, group2: dm_2, grou}}
    #       dict_fts = {lever: [dm_fts_a, dm_fts_b, dm_fts_c]}
    # where file is the name of the file and lever is the levername
    dm_ots_groups = {}
    dm_fts_groups = {}
    for (i, group) in enumerate(group_list):
        filter_dict = {column: group}
        num_cat = num_cat_list[i]
        dict_tmp_ots = {}
        dict_tmp_fts = {}
        read_database_to_ots_fts_dict(file, lever, num_cat, baseyear, years, dict_tmp_ots, dict_tmp_fts,
                                      filter_dict=filter_dict)
        group = group.replace('.*', '')
        dm_ots_groups[group] = dict_tmp_ots[lever]
        dm_fts_groups[group] = dict_tmp_fts[lever]

    dict_ots[lever] = dm_ots_groups
    dict_fts[lever] = dm_fts_groups

    return dict_ots, dict_fts


def filter_geoscale(global_vars):
    geo_pattern = global_vars['geoscale']
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    mypath = os.path.join(current_file_directory, '../../_database/data/datamatrix')
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    for file in files:
        if '.pickle' in file:
            with open(join(mypath, file), 'rb') as handle:
                DM_module = pickle.load(handle)

            DM_module_geo = {'fxa': {}, 'fts': {}, 'ots': {}}

            for key in DM_module.keys():
                if key in ['fxa', 'calibration']:
                    if isinstance(DM_module[key], dict):
                        for var_name in DM_module[key].keys():
                            dm = DM_module[key][var_name]
                            dm_geo = dm.filter_w_regex({'Country': geo_pattern})
                            DM_module_geo[key][var_name] = dm_geo
                    else:
                        DM_module_geo[key] = DM_module[key].filter_w_regex({'Country': geo_pattern})
                elif key == 'fts':
                    for lever_name in DM_module[key].keys():
                        DM_module_geo[key][lever_name] = {}
                        # If you have lever_value,
                        if 1 in DM_module[key][lever_name]:
                            for level_val in DM_module[key][lever_name].keys():
                                dm = DM_module[key][lever_name][level_val]
                                dm_geo = dm.filter_w_regex({'Country': geo_pattern})
                                DM_module_geo[key][lever_name][level_val] = dm_geo
                        else:
                            for group in DM_module[key][lever_name].keys():
                                DM_module_geo[key][lever_name][group] = {}
                                for level_val in DM_module[key][lever_name][group].keys():
                                    dm = DM_module[key][lever_name][group][level_val]
                                    dm_geo = dm.filter_w_regex({'Country': geo_pattern})
                                    DM_module_geo[key][lever_name][group][level_val] = dm_geo
                elif key == 'ots':
                    for lever_name in DM_module[key].keys():
                        # if there are groups
                        if isinstance(DM_module[key][lever_name], dict):
                            DM_module_geo[key][lever_name] = {}
                            for group in DM_module[key][lever_name].keys():
                                dm = DM_module[key][lever_name][group]
                                dm_geo = dm.filter_w_regex({'Country': geo_pattern})
                                DM_module_geo[key][lever_name][group] = dm_geo
                        # otherwise if you only have one dataframe
                        else:
                            dm = DM_module[key][lever_name]
                            dm_geo = dm.filter_w_regex({'Country': geo_pattern})
                            DM_module_geo[key][lever_name] = dm_geo
                elif key == 'constant':
                    DM_module_geo[key] = DM_module[key]
                else:
                    raise ValueError(f'pickle can only contain fxa, ots, fts, constant and calibration '
                                     f'as dictionary key, error in file {file}, for key {key}')

            current_file_directory = os.path.dirname(os.path.abspath(__file__))
            path_geo = os.path.join(current_file_directory, '../../_database/data/datamatrix/geoscale/')
            f_geo = join(path_geo, file)
            with open(f_geo, 'wb') as handle:
                pickle.dump(DM_module_geo, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return


def read_level_data(DM, lever_setting):
    # Reads the pickle database for ots and fts for the right lever_setting and returns a dictionary of datamatrix
    DM_ots_fts = {}
    for lever in DM['ots'].keys():
        level_value = lever_setting['lever_' + lever]
        # If there are groups
        if isinstance(DM['ots'][lever], dict):
            DM_ots_fts[lever] = {}
            for group in DM['ots'][lever].keys():
                dm = DM['ots'][lever][group]
                dm_fts = DM['fts'][lever][group][level_value]
                dm.append(dm_fts, dim='Years')
                DM_ots_fts[lever][group] = dm
        else:
            dm = DM['ots'][lever]
            dm_fts = DM['fts'][lever][level_value]
            dm.append(dm_fts, dim='Years')
            DM_ots_fts[lever] = dm

    return DM_ots_fts


#  Update Constant file (overwrite existing & append new data)
def update_interaction_constant_from_file(file_new):
    db_new = read_database(file_new, lever='',db_format=True)
    file_out = 'interactions_constants'
    update_database_from_db(file_out, db_new)
    return

def cdm_to_dm(cdm, countries_list, years_list):
    arr_temp = cdm.array[np.newaxis, np.newaxis, ...]
    arr_temp = np.repeat(arr_temp, len(countries_list), axis=0)
    arr_temp = np.repeat(arr_temp, len(years_list), axis=1)
    cy_cols = {
        'Country': countries_list.copy(),
        'Years': years_list.copy(),
    }
    new_cols = {**cy_cols, **cdm.col_labels}
    dm = DataMatrix(col_labels=new_cols, units=cdm.units)
    dm.array = arr_temp
    return dm

def simulate_input(from_sector, to_sector, num_cat = 0):
    
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    
    # get file
    xls_directory = os.path.join(current_file_directory, "../../_database/data/xls")
    files = np.array(os.listdir(xls_directory))
    file = files[[bool(re.search(from_sector + "-to-" + to_sector + ".xlsx", str(i))) for i in files]].tolist()[0]
    xls_file_directory = xls_directory +  "/" + file
    df = pd.read_excel(xls_file_directory)
    
    # get dm
    dm = DataMatrix.create_from_df(df, num_cat=num_cat)
    return dm


def material_decomposition(dm, cdm):
    
    num_dim = len(dm.dim_labels)
    # raise error
    if num_dim <= 3 or num_dim > 5:
        raise ValueError("This function works only for dm with categories (max 2)")

    # unit
    unit = cdm.units
    key_old = list(unit)[0]
    unit["material-decomposition"] = unit.pop(key_old)
    value_old = list(unit.values())[0]
    unit["material-decomposition"] = value_old.split("/")[0]

    # get col names
    if num_dim == 4:
        # # raise error
        # if dm.col_labels["Categories1"] != cdm.col_labels["Categories1"]:
        #     raise ValueError("Put product in the same category for both dm and cdm")

        arr = dm.array[..., np.newaxis] * cdm.array[np.newaxis, np.newaxis, :, :, :]
        dm_out = DataMatrix.based_on(arr, format=dm, units=unit,
                                     change={'Variables': ['material-decomposition'], 'Categories2': cdm.col_labels['Categories2']})

    if num_dim == 5:
        # # raise error
        # if dm.col_labels["Categories2"] != cdm.col_labels["Categories2"]:
        #     raise ValueError("Put product in the same category for both dm and cdm")

        arr = dm.array[..., np.newaxis] * cdm.array[np.newaxis, np.newaxis, :, :, np.newaxis, :]
        dm_out = DataMatrix.based_on(arr, format=dm, units=unit,
                                     change={'Variables': ['material-decomposition'], 'Categories3': cdm.col_labels['Categories2']})

    return dm_out


def calibration_rates(dm, dm_cal, calibration_start_year = 1990, calibration_end_year = 2015,
                      years_setting=[1990, 2015, 2050, 5]):
    # dm is the datamatrix with data to be calibrated
    # dm_cal is the datamatrix with the reference data
    # the function returns a datamatrix with the calibration rates
    # all datamartix should have the same shape
    
    # if dm and dm_cal do not have the same dimension return an error
    if len(dm.dim_labels) != len(dm_cal.dim_labels):
        raise ValueError('dm and dm_cal must have the same dimensions')
    if len(dm.col_labels['Variables']) > 1:
        raise ValueError('You can only calibrate one variable at the time')

    # subset based on years of calibration
    years_sub = np.array(range(calibration_start_year, calibration_end_year + 1, 1)).tolist()
    dm_sub = dm.filter({"Years" : years_sub})
    dm_cal_sub = dm_cal.filter({"Years" : years_sub})
    
    # get calibration rates = (calib - variable)/variable
    dm_cal_sub.array = (dm_cal_sub.array - dm_sub.array)/dm_sub.array + 1
    dm_cal_sub.col_labels["Variables"] = ['cal_rate']
    dm_cal_sub.units['cal_rate'] = "%"

    # adjust missing years in dm_cal_sub
    
    # get new years post calibration_end_year
    years = dm_cal_sub.col_labels["Years"]
    years_fts = np.array(range(years_setting[1] + years_setting[3], 
                                    years_setting[2] + years_setting[3], 
                                    years_setting[3])).tolist()
    if years_setting[1] in years:
        years_new_post = years_fts
    else:
        years_new_post_temp = np.array(range(years[len(years)-1] + 1, years_setting[1] + 1, 1)).tolist()
        years_new_post = years_new_post_temp + years_fts
    
    # get index of dm_cal_sub
    idx = dm_cal_sub.idx
    
    # for missing years pre calibration_start_year, add them with value 1 (no calibration done)
    # TODO!: in KNIME, for the years pre calibration, the calibration rate is the first calibration rate available (not 1), to be decided 
    if years_setting[0] not in years:
        years_new_pre = np.array(range(years_setting[0], calibration_start_year, 1)).tolist()
        for i in years_new_pre:
            dm_cal_sub.add(1, dim="Years", col_label = [i], dummy = True)
        
    # for missing years post calibration_end_year, add them with value of last available year
    for i in years_new_post:
        dm_cal_sub.add(dm_cal_sub.array[:, idx[calibration_end_year], ...], dim="Years", col_label=[i])
    # sort years
    dm_cal_sub.sort("Years")
    
    # return
    return dm_cal_sub

def cost(dm_activity, dm_price_index, cdm_cost, cost_type, baseyear = 2015, unit_cost=True):

    if len(dm_activity.col_labels["Variables"]) > 1:
        raise ValueError("This function works only for one activity at the time")
    # Check that they have the same categories
    for dim in cdm_cost.dim_labels:
        if "Categories" in dim:
            assert dm_activity.col_labels[dim] == cdm_cost.col_labels[dim]
    
    # filter for selected cost_type
    cdm_cost = cdm_cost.filter_w_regex({"Variables": ".*" + cost_type + ".*|.*evolution-method.*"})
    cdm_cost.rename_col_regex(cost_type + "-", "", dim="Variables")
    cdm_cost.rename_col('baseyear', 'unit-cost-baseyear', "Variables")
    
    # get some constants
    activity_last_cat = dm_activity.dim_labels[-1]
    activity_name = dm_activity.col_labels["Variables"][0]
    activity_unit = dm_activity.units[activity_name]
    cost_unit_denominator = re.split("/", cdm_cost.units["unit-cost-baseyear"])[1]
    years = dm_activity.col_labels["Years"]
    years_na = np.array(years)[[i < baseyear for i in years]].tolist()
    
    # include variables in cdm_cost inside dm_activity
    dm_activity = dm_activity.copy()
    dm_activity.add(1, dim="Variables", col_label="ones", dummy=True)
    variables = cdm_cost.col_labels["Variables"]
    idx = dm_activity.idx
    idx_cdm = cdm_cost.idx
    # !FIXME: adjust keep_LE to work with constant instead of dm_activity
    arr_temp = (cdm_cost.array[idx_cdm['d-factor']] * dm_activity.array[:, :, idx["ones"], ...])
    dm_activity.add(arr_temp[:, :, np.newaxis, ...], dim="Variables", col_label='d-factor')
    idx_temp = dm_activity.idx
    dm_activity.array[:, [idx_temp[y] for y in years_na], idx_temp['d-factor'], ...] = np.nan

    dm_activity.drop(dim="Variables", col_label="ones")
    
    # error if unit is not the same
    if cost_unit_denominator != activity_unit:
        raise ValueError(f"The unit of the activity is {activity_unit} while the denominator of the unit of costs is {cost_unit_denominator}. Make the unit of the activity as {cost_unit_denominator}.")
    
    ######################
    ##### UNIT COSTS #####
    ######################
    
    ##### LEARNING RATE METHODOLOGY #####
    
    # keep only variables that have evolution-method == 2 or 3
    idx = cdm_cost.idx
    keep_LR = ((cdm_cost.array[idx["evolution-method"], :] == 2) | \
               (cdm_cost.array[idx["evolution-method"], :] == 3)).tolist()
        
    if any(keep_LR):
        keep = np.array(dm_activity.col_labels[activity_last_cat])[keep_LR].tolist()
        dm_activity_LR = dm_activity.filter({activity_last_cat: keep})
        cdm_cost_LR = cdm_cost.filter({activity_last_cat: keep})
        idx_a_LR = dm_activity_LR.idx
        idx_c_LR = cdm_cost_LR.idx

        # make activity cumulative
        dm_activity_LR.array[:, :, idx_a_LR[activity_name], ...] = \
            np.cumsum(dm_activity_LR.array[:, :, idx_a_LR[activity_name], ...], axis=1)
        
        # learning = cumulated activity ^ b_factor
        arr_temp = (dm_activity_LR.array[:, :, idx_a_LR[activity_name], ...]\
                   ** cdm_cost_LR.array[np.newaxis, np.newaxis, idx_c_LR["b-factor"], ...])
        dm_activity_LR.add(arr_temp, dim="Variables", col_label="learning", unit=activity_unit)

        # a_factor = unit_cost_baseyear / learning
        arr_temp = cdm_cost_LR.array[np.newaxis, np.newaxis, idx_c_LR["unit-cost-baseyear"], ...] \
                  / dm_activity_LR.array[:, :, idx_a_LR['learning'], ...]
        dm_activity_LR.add(arr_temp, dim="Variables", col_label="a-factor", unit='num/' + activity_unit)
        
        # unit cost = a_factor * learning
        # FIXME!: THIS IS LIKE THE KNIME, BUT NOT SURE THIS ISCORRECT, AS LIKE THIS UNIT COST = UNIT COST BASEYEAR (TBC WHAT TO DO)
        dm_activity_LR.operation("a-factor", "*", "learning", dim="Variables", out_col="unit-cost", unit="EUR/" + activity_unit)
        dm_activity_LR.filter({"Variables": ["unit-cost"]}, inplace=True)
        dm_cost_LR = dm_activity_LR
        del cdm_cost_LR, idx_c_LR, idx_a_LR, arr_temp

    ##### LINEAR EVOLUTION METHODOLOGY #####
    
    # keep only variables that have evolution-method == 1
    idx = cdm_cost.idx
    keep_LE = (cdm_cost.array[idx["evolution-method"], :] == 1).tolist()
    
    if any(keep_LE):
        keep = np.array(dm_activity.col_labels[activity_last_cat])[keep_LE].tolist()
        dm_activity_LE = dm_activity.filter({activity_last_cat: keep})
        cdm_cost_LE = cdm_cost.filter({activity_last_cat: keep})
        idx_a_LE = dm_activity_LE.idx
        idx_c_LE = cdm_cost_LE.idx

        # unit_cost = d_factor * (years - baseyear) + unit_cost_baseyear
        years_diff = np.array(dm_activity.col_labels['Years']) - baseyear
        cdm_cost_LE.array = cdm_cost_LE.array[np.newaxis, np.newaxis, ...]
        dm_activity_LE.array = np.moveaxis(dm_activity_LE.array, 1, -1)  # move years to end
        cdm_cost_LE.array = np.moveaxis(cdm_cost_LE.array, 1, -1)  # move years to end
        arr_temp = dm_activity_LE.array[:, idx_a_LE['d-factor'], ...] * years_diff \
                   + cdm_cost_LE.array[:, idx_c_LE["unit-cost-baseyear"], ...]
        arr_temp = np.moveaxis(arr_temp, -1, 1)
        dm_activity_LE.array = np.moveaxis(dm_activity_LE.array, -1, 1)  # move years to end
        dm_activity_LE.add(arr_temp, dim="Variables", col_label="unit-cost", unit="EUR/" + activity_unit)
        dm_activity_LE.filter({"Variables": ["unit-cost"]}, inplace=True)
        dm_cost_LE = dm_activity_LE
        del arr_temp, cdm_cost_LE, idx_c_LE, idx_a_LE
    
    ##### PUT TOGETHER #####
    
    dm_cost = dm_activity.filter({"Variables": [activity_name]})
    if any(keep_LE) and any(keep_LR):
        dm_cost_LR.append(dm_cost_LE, activity_last_cat)
        dm_cost_LR.sort(activity_last_cat)
        dm_cost.append(dm_cost_LR, dim="Variables")
    if not any(keep_LR):
        dm_cost.append(dm_cost_LE, dim="Variables")
    if not any(keep_LE):
        dm_cost.append(dm_cost_LR, dim="Variables")
    
    #################
    ##### COSTS #####
    #################
    
    # cost = unit cost * activity * price index / 100 / 1000000
    idx = dm_cost.idx
    arr_temp = dm_cost.array[:, :, idx["unit-cost"], ...] * dm_cost.array[:, :, idx[activity_name],...] / 100 / 1000000
    arr_temp = np.moveaxis(arr_temp, 0, -1)
    arr_temp = dm_price_index.array[:, 0, 0] * arr_temp
    arr_temp = np.moveaxis(arr_temp, -1, 0)
    if unit_cost:
        dm_cost.add(arr_temp, dim="Variables", col_label=cost_type, unit="MEUR")
        dm_cost.drop("Variables", activity_name)
        # return
        return dm_cost
    else:
        dm_out = DataMatrix.based_on(arr_temp[:, :, np.newaxis, ...], format=dm_cost,
                                     change={'Variables': [cost_type]}, units={cost_type: 'MEUR'})
        return dm_out

def material_switch(dm, dm_ots_fts, cdm_const, material_in, material_out, product, 
                    switch_percentage_prefix, switch_ratio_prefix, dict_for_output = None):
    
    # this function does a material switch between materials
    # dm contains the data on the products' material decomposition (obtained with the function material_decomposition())
    # dm_ots_fts contains the lever data with the material switch percentages
    # cdm_const constains the constants for the switch ratios
    # material_in is the material that will be switched from
    # material_out is the material that will be swiched to
    # product is the product for which we are doing the material switch
    # switch_percentage_prefix is the prefix for the product in the dm_ots_fts
    # switch_ratio_prefix is the prefix for the material switch ratio in cdm_const
    # dict_for_output is an optional dictionary where the function saves variables that will be used for material switch impact in emissions in industry
    # note that this function overwrites directly into the dm.
    
    if len(dm.dim_labels) == 3 | len(dm.dim_labels) == 6:
        raise ValueError("At the moment this function works only for dms with products in Category1 and materials in Category2")
    
    # get constants
    material_in_to_out = [material_in + "-to-" + i for i in material_out]
    product_category = dm.dim_labels[-2]
    material_category = dm.dim_labels[-1]

    # if one of the materials out is not in data, create it
    idx_matindata = [i in dm.col_labels[material_category] for i in material_out]
    if not all(idx_matindata):
        dm.add(np.nan, dim = material_category, col_label = np.array(material_out)[[not i for i in idx_matindata]].tolist(), dummy = True)
        dm.sort(material_category)
    
    # get material in and material out
    dm_temp = dm.filter({product_category : [product]})
    dm_temp = dm_temp.filter({material_category : [material_in] + material_out})
    
    # get switch percentages
    dm_temp2 = dm_ots_fts.filter({product_category : [switch_percentage_prefix + i for i in material_in_to_out]})
    
    # get switch ratios
    dm_temp3 = cdm_const.filter({"Variables" : [switch_ratio_prefix + i for i in material_in_to_out]})
    
    # get materials out
    idx = dm.idx
    idx_temp = dm_temp.idx
    idx_temp2 = dm_temp2.idx
    idx_temp3 = dm_temp3.idx
    for i in range(len(material_out)):
        
        # get material in-to-out
        arr_temp = dm_temp.array[:,:,:,:,idx_temp[material_in]] * \
            dm_temp2.array[:,:,:,idx_temp2[switch_percentage_prefix + material_in_to_out[i]],np.newaxis]
        dm_temp.add(arr_temp, dim = material_category, col_label = material_in_to_out[i])
        dm_temp.add(arr_temp * -1, dim = material_category, col_label = material_in_to_out[i] + "_minus")
        
        # get material in-to-out-times-switch-ratio
        arr_temp = dm_temp.array[:,:,:,:,idx_temp[material_in_to_out[i]]] * \
            dm_temp3.array[idx_temp3[switch_ratio_prefix + material_in_to_out[i]]]
        dm_temp.add(arr_temp, dim = material_category, col_label = material_in_to_out[i] + "_times_ratio")
        
        # get material out
        if idx_matindata[i]:
            dm_temp4 = dm_temp.filter({material_category : [material_out[i], material_in_to_out[i] + "_times_ratio"]})
            dm.array[:,:,:,idx[product],idx[material_out[i]]] = np.nansum(dm_temp4.array[:,:,0,:,:], axis = -1)
        else:
            dm_temp4 = dm_temp.filter({material_category : [material_in_to_out[i] + "_times_ratio"]})
            dm.array[:,:,:,idx[product],idx[material_out[i]]] = dm_temp4.array[:,:,0,0,:]
        
    # get material in and write
    dm_temp4 = dm_temp.filter({material_category : [material_in] + [i + "_minus" for i in material_in_to_out]})
    dm.array[:,:,:,idx[product],idx[material_in]] = np.nansum(dm_temp4.array[:,:,0,:,:], axis = -1)
    
    # get material in-to-out and write
    if dict_for_output is not None:
        dict_for_output[product + "_" + material_in_to_out[0]] = dm_temp.filter({material_category : material_in_to_out})
        
    return

def energy_switch(dm_energy_demand, dm_energy_carrier_mix, carrier_in, carrier_out, dm_energy_carrier_mix_prefix):
    
    # this function does the energy switch
    # dm_energy_demand is the dm with technologies (cat1) and energy carriers (cat2)
    # dm_energy_carrier_mix is the dm with technologies (cat1) and % for the switches (cat2)
    # carrier_in is the carrier that gets switched
    # carrier_out is the carrier that is switched to
    # dm_energy_carrier_mix_prefix is the prefix for the energy switch in dm_energy_carrier_mix
    
    # get categories
    carriers_category = dm_energy_demand.dim_labels[-1]
    
    # get carriers
    carrier_all = dm_energy_demand.col_labels[carriers_category]
    carrier_in_exclude = np.array(carrier_all)[[i not in carrier_in for i in carrier_all]].tolist()
    
    # for all material-technologies, get energy demand for all carriers but carrier out and excluded ones
    dm_temp1 = dm_energy_demand.filter_w_regex({carriers_category : "^((?!" + "|".join(carrier_in_exclude) + ").)*$"})
    
    # get percentages of energy switched to carrier out for each of material-technology
    dm_temp2 = dm_energy_carrier_mix.filter_w_regex({carriers_category : ".*" + dm_energy_carrier_mix_prefix})
    
    # for all material-technologies, get additional demand for carrier out for each energy carrier
    names = dm_temp1.col_labels[carriers_category]
    for i in names:
        dm_temp1.rename_col(i, i + "_total", carriers_category)
    dm_temp1.deepen()
    dm_temp1.add(dm_temp1.array, dim = dm_temp1.dim_labels[-1], col_label = dm_energy_carrier_mix_prefix)
    idx_temp1 = dm_temp1.idx
    dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] = \
        dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] * dm_temp2.array
    
    # get total carrier out switched
    dm_temp3 = dm_temp1.group_all(dim=carriers_category, inplace = False)
    dm_temp3.drop(carriers_category, "total")
    
    # sum this additional demand for carrier out due to switch to carrier-out demand
    dm_temp3.append(dm_energy_demand.filter({carriers_category : [carrier_out]}), carriers_category)
    idx = dm_energy_demand.idx
    dm_energy_demand.array[:,:,:,:,idx[carrier_out]] = np.nansum(dm_temp3.array, axis = -1)
    
    # for each energy carrier, subtract additional demand for carrier out due to switch
    dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] = \
        dm_temp1.array[...,idx_temp1[dm_energy_carrier_mix_prefix]] * -1 # this is to do minus with np.nansum
    dm_temp1.add(np.nansum(dm_temp1.array, axis = -1, keepdims=True), dim = dm_temp1.dim_labels[-1], col_label = "final")
    dm_temp1.drop(dm_temp1.dim_labels[-1], ['total', dm_energy_carrier_mix_prefix])
    dm_temp1 = dm_temp1.flatten()
    dm_temp1.rename_col_regex(str1 = "_final", str2 = "", dim = carriers_category)
    drops = dm_temp1.col_labels[carriers_category]
    dm_energy_demand.drop(carriers_category, drops)
    dm_energy_demand.append(dm_temp1, carriers_category)
    dm_energy_demand.sort(carriers_category)