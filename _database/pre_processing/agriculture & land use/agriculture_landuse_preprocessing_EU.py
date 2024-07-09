import numpy as np
from model.common.auxiliary_functions import interpolate_nans, add_missing_ots_years
#from _database.pre_processing.api_routines_CH import get_data_api_CH
from scipy.stats import linregress
import pandas as pd
import faostat


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
def self_sufficiency_processing():

    # Read data ------------------------------------------------------------------------------------------------------------

    # Common for all
    # List of countries
    list_countries = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark',
                      'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia',
                      'Lithuania', 'Luxembourg', 'Malta', 'Netherlands (Kingdom of the)', 'Poland', 'Portugal',
                      'Romania', 'Slovakia',
                      'Slovenia', 'Spain', 'Sweden', 'Switzerland',
                      'United Kingdom of Great Britain and Northern Ireland']

    # FOOD BALANCE SHEETS (FBS) - For everything except molasses and cakes -------------------------------------------------
    # List of elements
    list_elements = ['Production Quantity', 'Import Quantity', 'Export Quantity']

    list_items = ['Cereals - Excluding Beer + (Total)', 'Fruits - Excluding Wine + (Total)', 'Oilcrops + (Total)',
                  'Pulses + (Total)', 'Rice (Milled Equivalent)',
                  'Starchy Roots + (Total)', 'Stimulants + (Total)', 'Sugar Crops + (Total)', 'Vegetables + (Total)',
                  'Demersal Fish', 'Freshwater Fish',
                  'Aquatic Animals, Others', 'Pelagic Fish', 'Beer', 'Beverages, Alcoholic', 'Beverages, Fermented',
                  'Wine', 'Sugar (Raw Equivalent)', 'Sweeteners, Other', 'Vegetable Oils + (Total)',
                  'Milk - Excluding Butter + (Total)', 'Eggs + (Total)', 'Animal fats + (Total)', 'Offals + (Total)',
                  'Bovine Meat', 'Meat, Other', 'Pigmeat',
                  'Poultry Meat', 'Mutton & Goat Meat', 'Fish, Seafood + (Total)']

    # 1990 - 2013
    ld = faostat.list_datasets()
    code = 'FBSH'
    pars = faostat.list_pars(code)
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002',
                  '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_ssr_1990_2013 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # 2010 - 2022
    # Different list becuse different in item nomination such as rice
    list_items = ['Cereals - Excluding Beer + (Total)', 'Fruits - Excluding Wine + (Total)', 'Oilcrops + (Total)',
                  'Pulses + (Total)', 'Rice and products',
                  'Starchy Roots + (Total)', 'Stimulants + (Total)', 'Sugar Crops + (Total)', 'Vegetables + (Total)',
                  'Demersal Fish', 'Freshwater Fish',
                  'Aquatic Animals, Others', 'Pelagic Fish', 'Beer', 'Beverages, Alcoholic', 'Beverages, Fermented',
                  'Wine', 'Sugar (Raw Equivalent)', 'Sweeteners, Other', 'Vegetable Oils + (Total)',
                  'Milk - Excluding Butter + (Total)', 'Eggs + (Total)', 'Animal fats + (Total)', 'Offals + (Total)',
                  'Bovine Meat', 'Meat, Other', 'Pigmeat',
                  'Poultry Meat', 'Mutton & Goat Meat', 'Fish, Seafood + (Total)']
    code = 'FBS'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_ssr_2010_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # COMMODITY BALANCES (NON-FOOD) (OLD METHODOLOGY) - For molasse and cakes ----------------------------------------------
    # 1990 - 2013
    list_items = ['Copra Cake', 'Cottonseed Cake', 'Groundnut Cake', 'Oilseed Cakes, Other', 'Palmkernel Cake',
                  'Rape and Mustard Cake', 'Sesameseed Cake', 'Soyabean Cake', 'Sunflowerseed Cake']
    code = 'CBH'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002',
                  '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_ssr_1990_2013_cake = faostat.get_data_df(code, pars=my_pars, strval=False)

    # SUPPLY UTILIZATION ACCOUNTS (SCl) - For molasse and cakes ----------------------------------------------------------
    # 2010 - 2022
    list_items = ['Molasses', 'Cake of  linseed', 'Cake of  soya beans', 'Cake of copra', 'Cake of cottonseed',
                  'Cake of groundnuts', 'Cake of hempseed', 'Cake of kapok', 'Cake of maize', 'Cake of mustard seed',
                  'Cake of palm kernel', 'Cake of rapeseed', 'Cake of rice bran', 'Cake of safflowerseed',
                  'Cake of sesame seed', 'Cake of sunflower seed', 'Cake, oilseeds nes', 'Cake, poppy seed',
                  'Cocoa powder and cake']
    code = 'SCL'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_ssr_2010_2021_molasse_cake = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Aggregating cakes
    df_ssr_cake = pd.concat([df_ssr_1990_2013_cake, df_ssr_2010_2021_molasse_cake])
    # Filtering
    filtered_df = df_ssr_cake[df_ssr_cake['Item'].str.contains('cake', case=False)]
    # Groupby Area, Year and Element and sum the Value
    grouped_df = filtered_df.groupby(['Area', 'Element', 'Year'])['Value'].sum().reset_index()
    # Adding a column 'Item' containing 'Cakes' for all row, before the 'Value' column
    grouped_df['Item'] = 'Cakes'
    cols = grouped_df.columns.tolist()
    cols.insert(cols.index('Value'), cols.pop(cols.index('Item')))
    df_ssr_cake = grouped_df[cols]

    # Filtering for molasse
    df_ssr_molasses = df_ssr_2010_2021_molasse_cake[
        df_ssr_2010_2021_molasse_cake['Item'].str.contains('Molasses', case=False)]

    # Concatenating
    df_ssr = pd.concat([df_ssr_1990_2013, df_ssr_2010_2021])
    df_ssr = pd.concat([df_ssr, df_ssr_molasses])
    df_ssr = pd.concat([df_ssr, df_ssr_cake])

    # Filtering to keep wanted columns
    columns_to_filter = ['Area', 'Element', 'Item', 'Year', 'Value']
    df_ssr = df_ssr[columns_to_filter]

    # Compute Self-Sufficiency Ratio (SSR) ---------------------------------------------------------------------------------
    # SSR [%] = (100*Production) / (Production + Imports - Exports)
    # Step 1: Pivot the DataFrame to get 'Production', 'Import Quantity', and 'Export Quantity' in separate columns
    pivot_df = df_ssr.pivot_table(index=['Area', 'Year', 'Item'], columns='Element', values='Value').reset_index()

    # Step 2: Compute the SSR [%]
    pivot_df['SSR[%]'] = (pivot_df['Production']) / (
                pivot_df['Production'] + pivot_df['Import Quantity'] - pivot_df['Export Quantity'])

    # Drop the columns Production, Import Quantity and Export Quantity
    pivot_df = pivot_df.drop(columns=['Production', 'Import Quantity', 'Export Quantity'])

    # Extrapolate for missing data -----------------------------------------------------------------------------------------

    # Extrapolate for 2022 for everything ?

    # 'Molasses' (only 2010-2021)

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Food item name matching with dictionary
    # Read excel file
    df_dict_ssr = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='self-sufficiency')

    # Merge based on 'Item'
    df_ssr_pathwaycalc = pd.merge(df_dict_ssr, pivot_df, on='Item')

    # Drop the 'Item' column
    df_ssr_pathwaycalc = df_ssr_pathwaycalc.drop(columns=['Item'])

    # Renaming existing columns (geoscale, timsecale, value)
    df_ssr_pathwaycalc.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'SSR[%]': 'value'}, inplace=True)

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_ssr_pathwaycalc['module'] = 'agriculture'
    df_ssr_pathwaycalc['lever'] = 'food-net-import'
    df_ssr_pathwaycalc['level'] = 0.0
    df_ssr_pathwaycalc['string-pivot'] = 'none'
    cols = df_ssr_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('value'), cols.pop(cols.index('string-pivot')))
    df_ssr_pathwaycalc = df_ssr_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                            'Netherlands')
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # Vaud, Paris & EU27 ---------------------------------------------------------------------------------------------------

    return df_ssr_pathwaycalc





#years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
#years_ots = create_ots_years_list(years_setting)

# RUNNING PRE-PROCESSING -----------------------------------------------------------------------------------------------

df_ssr_pathwaycalc = self_sufficiency_processing()

print('Hello')


