import numpy as np
from model.common.auxiliary_functions import interpolate_nans, add_missing_ots_years
#from _database.pre_processing.api_routines_CH import get_data_api_CH
from scipy.stats import linregress
import pandas as pd


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


# SELF-SUFFICIENCY CROP & LIVESTOCK ------------------------------------------------------------------------------------


# Read data ------------------------------------------------------------------------------------------------------------
# Before 2013

# 2010-2021
df_ssr_2010_2021 = pd.read_csv("/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/FAOSTAT_data_self-sufficiency_after_2010.csv")


# Concatenating

# Filtering to keep wanted columns
columns_to_filter = ['Area', 'Element', 'Item', 'Year', 'Unit', 'Value']
df_ssr_2010_2021 = df_ssr_2010_2021[columns_to_filter]

# Filtering the country to keep only the relevant countries


# Compute Self-Sufficiency Ratio (SSR) ---------------------------------------------------------------------------------
# SSR [%] = (100*Production) / (Production + Imports - Exports)

# Step 1: Pivot the DataFrame to get 'Production', 'Import Quantity', and 'Export Quantity' in separate columns
pivot_df = df_ssr_2010_2021.pivot_table(index=['Area', 'Year', 'Item'], columns='Element', values='Value').reset_index()

# Step 2: Compute the SSR [%]
pivot_df['SSR'] = (pivot_df['Production']) / (pivot_df['Production'] + pivot_df['Import Quantity'] - pivot_df['Export Quantity'])


# PathwayCalc formatting -----------------------------------------------------------------------------------------------

# Name matching with dictionnary

# Further formatting



# Vaud & Paris ---------------------------------------------------------------------------------------------------------



years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
years_ots = create_ots_years_list(years_setting)

# RUNNING PRE-PROCESSING -----------------------------------------------------------------------------------------------


print('Hello')


