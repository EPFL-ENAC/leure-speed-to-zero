import numpy as np
from model.common.auxiliary_functions import interpolate_nans, add_missing_ots_years
#from _database.pre_processing.api_routines_CH import get_data_api_CH
from scipy.stats import linregress
import pandas as pd
import faostat
import os
import eurostat
from model.common.io_database import database_to_dm


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


# CalculationLeaf SELF-SUFFICIENCY CROP & LIVESTOCK ------------------------------------------------------------------------------
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
    list_elements = ['Production Quantity', 'Import Quantity', 'Export Quantity', 'Feed']

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
    # Renaming the elements
    df_ssr_1990_2013.loc[df_ssr_1990_2013['Element'].str.contains('Production Quantity', case=False, na=False), 'Element'] = 'Production'
    df_ssr_1990_2013.loc[
        df_ssr_1990_2013['Element'].str.contains('Import Quantity', case=False, na=False), 'Element'] = 'Import'
    df_ssr_1990_2013.loc[
        df_ssr_1990_2013['Element'].str.contains('Export Quantity', case=False, na=False), 'Element'] = 'Export'

    # 2010 - 2022
    list_elements = ['Production Quantity', 'Import quantity', 'Export quantity', 'Feed']
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

    # Renaming the elements
    df_ssr_2010_2021.loc[
        df_ssr_2010_2021['Element'].str.contains('Production Quantity', case=False, na=False), 'Element'] = 'Production'
    df_ssr_2010_2021.loc[
        df_ssr_2010_2021['Element'].str.contains('Import quantity', case=False, na=False), 'Element'] = 'Import'
    df_ssr_2010_2021.loc[
        df_ssr_2010_2021['Element'].str.contains('Export quantity', case=False, na=False), 'Element'] = 'Export'

    # COMMODITY BALANCES (NON-FOOD) (OLD METHODOLOGY) - For molasse and cakes ----------------------------------------------
    # 1990 - 2013
    list_elements = ['Production Quantity', 'Import Quantity', 'Export Quantity', 'Feed']
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
    # Renaming the elements
    df_ssr_1990_2013_cake.loc[
        df_ssr_1990_2013_cake['Element'].str.contains('Production Quantity', case=False, na=False), 'Element'] = 'Production'
    df_ssr_1990_2013_cake.loc[
        df_ssr_1990_2013_cake['Element'].str.contains('Import Quantity', case=False, na=False), 'Element'] = 'Import'
    df_ssr_1990_2013_cake.loc[
        df_ssr_1990_2013_cake['Element'].str.contains('Export Quantity', case=False, na=False), 'Element'] = 'Export'

    # SUPPLY UTILIZATION ACCOUNTS (SCl) - For molasse and cakes ----------------------------------------------------------
    # 2010 - 2022
    list_elements = ['Production Quantity', 'Import quantity', 'Export quantity', 'Feed']
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

    # Renaming the elements
    df_ssr_2010_2021_molasse_cake.loc[
        df_ssr_2010_2021_molasse_cake['Element'].str.contains('Production Quantity', case=False, na=False), 'Element'] = 'Production'
    df_ssr_2010_2021_molasse_cake.loc[
        df_ssr_2010_2021_molasse_cake['Element'].str.contains('Import quantity', case=False, na=False), 'Element'] = 'Import'
    df_ssr_2010_2021_molasse_cake.loc[
        df_ssr_2010_2021_molasse_cake['Element'].str.contains('Export quantity', case=False, na=False), 'Element'] = 'Export'

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

    # Create a copy for feed pre-processing and drop irrelevant columns
    df_csl_feed = pivot_df.copy()
    df_csl_feed = df_csl_feed.drop(columns=['Production', 'Import', 'Export'])

    # Step 2: Compute the SSR [%]
    pivot_df['SSR[%]'] = (pivot_df['Production']) / (
                pivot_df['Production'] + pivot_df['Import'] - pivot_df['Export'])

    # Drop the columns Production, Import Quantity and Export Quantity
    pivot_df = pivot_df.drop(columns=['Production', 'Import', 'Export', 'Feed'])

    # Extrapolate for missing data -----------------------------------------------------------------------------------------

    # Extrapolate for 2022 for everything ?

    # 'Molasses' (only 2010-2021), extrapolate for

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
    df_ssr_pathwaycalc['level'] = 0
    cols = df_ssr_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_ssr_pathwaycalc = df_ssr_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                            'Netherlands')
    df_ssr_pathwaycalc['geoscale'] = df_ssr_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # Vaud, Paris & EU27 ---------------------------------------------------------------------------------------------------

    return df_ssr_pathwaycalc, df_csl_feed

# CalculationLeaf CLIMATE SMART CROP ---------------------------------------------------------------------------------------------
def climate_smart_crop_processing():

    # Common for all
    # List of countries
    list_countries = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark',
                      'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia',
                      'Lithuania', 'Luxembourg', 'Malta', 'Netherlands (Kingdom of the)', 'Poland', 'Portugal',
                      'Romania', 'Slovakia',
                      'Slovenia', 'Spain', 'Sweden', 'Switzerland',
                      'United Kingdom of Great Britain and Northern Ireland']



    # ENERGY DEMAND --------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # INPUT USE ------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # NITROGEN, PHOSPHATE, POTASH ------------------------------------------------------------------------------------------

    # List of elements
    list_elements = ['Use per area of cropland']

    list_items = ['Nutrient nitrogen N (total)', 'Nutrient phosphate P2O5 (total)', 'Nutrient potash K2O (total)']

    # 1990 - 2021
    ld = faostat.list_datasets()
    code = 'RFN'
    pars = faostat.list_pars(code)
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_input_nitrogen_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # PESTICIDES -----------------------------------------------------------------------------------------------------------

    # List of elements
    list_elements = ['Use per area of cropland']

    list_items = ['Pesticides (total) + (Total)']

    # 1990 - 2021
    code = 'RP'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_input_pesticides_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # LIMING, UREA ---------------------------------------------------------------------------------------------------------
    # List of elements
    list_elements = ['Agricultural Use']

    list_items = ['Urea', 'Calcium ammonium nitrate (CAN) and other mixtures with calcium carbonate']

    # Input Liming Urea 2002 - 2021
    code = 'RFB'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_input_liming_urea_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Area Harvested 2002 - 2021

    # List of elements
    list_elements = ['Area harvested']
    list_items = ['Cereals, primary + (Total)', 'Fibre Crops, Fibre Equivalent + (Total)', 'Fruit Primary + (Total)',
                  'Oilcrops, Oil Equivalent + (Total)', 'Pulses, Total + (Total)', 'Rice',
                  'Roots and Tubers, Total + (Total)',
                  'Sugar Crops Primary + (Total)', 'Vegetables Primary + (Total)']
    code = 'QCL'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_area_2022_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Conversion from [t] in [t/ha]-----------------------------------------------------------------------------------------
    # Summming Area harvested per country and year (and element)
    df_area_total_2022_2021 = df_area_2022_2021.groupby(['Area', 'Element', 'Year'])['Value'].sum().reset_index()

    # UREA
    # Filtering and dropping columns
    df_input_urea_1990_2021 = df_input_liming_urea_1990_2021[df_input_liming_urea_1990_2021['Item'] == 'Urea']
    df_input_urea_1990_2021 = df_input_urea_1990_2021.drop(
        columns=['Domain Code', 'Domain', 'Area Code', 'Element Code',
                 'Item Code', 'Year Code', 'Unit', 'Item'])
    # Concatenate
    df_urea_area = pd.concat([df_area_total_2022_2021, df_input_urea_1990_2021])
    # Step 1: Pivot the DataFrame
    pivot_df = df_urea_area.pivot_table(index=['Area', 'Year'], columns='Element', values='Value').reset_index()
    # Step 2: Compute the input [t/ha]
    pivot_df['Input[t/ha]'] = pivot_df['Agricultural Use'] / pivot_df['Area harvested']
    # Drop the columns Yield
    pivot_df = pivot_df.drop(columns=['Agricultural Use', 'Area harvested'])
    # Adding a column Item
    pivot_df['Item'] = 'Urea'
    cols = pivot_df.columns.tolist()
    cols.insert(cols.index('Input[t/ha]'), cols.pop(cols.index('Item')))
    pivot_df = pivot_df[cols]
    pivot_df_urea = pivot_df.copy()

    # LIMING
    # Filtering and dropping columns
    df_input_liming_1990_2021 = df_input_liming_urea_1990_2021[df_input_liming_urea_1990_2021[
                                                                   'Item'] == 'Calcium ammonium nitrate (CAN) and other mixtures with calcium carbonate']
    df_input_liming_1990_2021 = df_input_liming_1990_2021.drop(
        columns=['Domain Code', 'Domain', 'Area Code', 'Element Code',
                 'Item Code', 'Year Code', 'Unit', 'Item'])
    # Concatenate
    df_liming_area = pd.concat([df_area_total_2022_2021, df_input_liming_1990_2021])
    # Step 1: Pivot the DataFrame
    pivot_df = df_liming_area.pivot_table(index=['Area', 'Year'], columns='Element', values='Value').reset_index()
    # Step 2: Compute the input [t/ha]
    pivot_df['Input[t/ha]'] = pivot_df['Agricultural Use'] / pivot_df['Area harvested']
    # Drop the columns
    pivot_df = pivot_df.drop(columns=['Agricultural Use', 'Area harvested'])
    # Adding a column Item
    pivot_df['Item'] = 'Calcium ammonium nitrate (CAN) and other mixtures with calcium carbonate'
    cols = pivot_df.columns.tolist()
    cols.insert(cols.index('Input[t/ha]'), cols.pop(cols.index('Item')))
    pivot_df = pivot_df[cols]
    pivot_df_liming = pivot_df.copy()

    # Conversion from [kg/ha] in [t/ha]-------------------------------------------------------------------------------------

    # Concatenating
    df_input_pesticides_nitrogen = pd.concat([df_input_pesticides_1990_2021, df_input_nitrogen_1990_2021])
    # Step 1: Pivot the DataFrame
    pivot_df = df_input_pesticides_nitrogen.pivot_table(index=['Area', 'Year', 'Item'], columns='Element',
                                                        values='Value').reset_index()
    # Step 2: Compute the Input [t/ha]
    pivot_df['Input[t/ha]'] = pivot_df['Use per area of cropland'] * 0.001
    # Drop the columns
    pivot_df_pesticides_nitrogen = pivot_df.drop(columns=['Use per area of cropland'])

    # Extrapolating RFB for 1990 to 2001 and other missing values ----------------------------------------------------------

    # Extrapolating everything for 2022

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Concatenating
    pivot_df_input = pd.concat([pivot_df_urea, pivot_df_liming], axis=0)
    pivot_df_input = pd.concat([pivot_df_input, pivot_df_pesticides_nitrogen], axis=0)

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csc = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-crops')

    # Merge based on 'Item'
    df_input_pathwaycalc = pd.merge(df_dict_csc, pivot_df_input, on='Item')

    # Drop the 'Item' column
    df_input_pathwaycalc = df_input_pathwaycalc.drop(columns=['Item'])

    # Renaming existing columns (geoscale, timsecale, value)
    df_input_pathwaycalc.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Input[t/ha]': 'value'}, inplace=True)

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_input_pathwaycalc['module'] = 'agriculture'
    df_input_pathwaycalc['lever'] = 'climate-smart-crop'
    df_input_pathwaycalc['level'] = 0
    cols = df_input_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_input_pathwaycalc = df_input_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_input_pathwaycalc['geoscale'] = df_input_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_input_pathwaycalc['geoscale'] = df_input_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                'Netherlands')
    df_input_pathwaycalc['geoscale'] = df_input_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # EF AGROFORESTRY ------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    # Is equal to 0 for all ots for all countries

    # Use pivot_df_input as a structural basis
    agroforestry_crop = pivot_df_input.copy()

    # Drop the column Item
    agroforestry_crop = agroforestry_crop.drop(columns=['Item', 'Input[t/ha]'])

    # Rename the column in geoscale and timescale
    agroforestry_crop.rename(columns={'Area': 'geoscale', 'Year': 'timescale'}, inplace=True)

    # Changing data type to numeric (except for the geoscale column)
    agroforestry_crop.loc[:, agroforestry_crop.columns != 'geoscale'] = agroforestry_crop.loc[:,
                                                                        agroforestry_crop.columns != 'geoscale'].apply(
        pd.to_numeric, errors='coerce')

    # Add rows to have 1990-2022
    # Generate a DataFrame with all combinations of geoscale and timescale
    geoscale_values = agroforestry_crop['geoscale'].unique()
    timescale_values = pd.Series(range(1990, 2023))

    # Create a DataFrame for the cartesian product
    cartesian_product = pd.MultiIndex.from_product([geoscale_values, timescale_values],
                                                   names=['geoscale', 'timescale']).to_frame(index=False)



    # Merge the original DataFrame with the cartesian product to include all combinations
    agroforestry_crop = pd.merge(cartesian_product, agroforestry_crop, on=['geoscale', 'timescale'], how='left')

    # Add the variables with a value of 0
    agroforestry_crop['agr_climate-smart-crop_ef_agroforestry_cover-crop[tC/ha]'] = 0
    agroforestry_crop['agr_climate-smart-crop_ef_agroforestry_cropland[tC/ha]'] = 0
    agroforestry_crop['agr_climate-smart-crop_ef_agroforestry_hedges[tC/ha]'] = 0
    agroforestry_crop['agr_climate-smart-crop_ef_agroforestry_no-till[tC/ha]'] = 0

    # Melt the df
    agroforestry_crop_pathwaycalc = pd.melt(agroforestry_crop, id_vars=['timescale', 'geoscale'],
                                           value_vars=['agr_climate-smart-crop_ef_agroforestry_cover-crop[tC/ha]',
                                                       'agr_climate-smart-crop_ef_agroforestry_cropland[tC/ha]',
                                                       'agr_climate-smart-crop_ef_agroforestry_hedges[tC/ha]',
                                                       'agr_climate-smart-crop_ef_agroforestry_no-till[tC/ha]'],
                                           var_name='variables', value_name='value')

    # PathwayCalc formatting
    agroforestry_crop_pathwaycalc['module'] = 'agriculture'
    agroforestry_crop_pathwaycalc['lever'] = 'climate-smart-crop'
    agroforestry_crop_pathwaycalc['level'] = 0
    cols = agroforestry_crop_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('timescale'), cols.pop(cols.index('variables')))
    agroforestry_crop_pathwaycalc = agroforestry_crop_pathwaycalc[cols]


    # ----------------------------------------------------------------------------------------------------------------------
    # LOSSES ---------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # FOOD BALANCE SHEETS (FBS) - For everything  -------------------------------------------------
    # List of elements
    list_elements = ['Losses', 'Production Quantity']

    list_items = ['Cereals - Excluding Beer + (Total)', 'Fruits - Excluding Wine + (Total)', 'Oilcrops + (Total)',
                  'Pulses + (Total)', 'Rice (Milled Equivalent)', 'Starchy Roots + (Total)', 'Sugar Crops + (Total)',
                  'Vegetables + (Total)', ]

    # 1990 - 2013
    code = 'FBSH'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_losses_1990_2013 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # 2010 - 2022
    # Different list because different in item nomination such as rice
    list_items = ['Cereals - Excluding Beer + (Total)', 'Fruits - Excluding Wine + (Total)', 'Oilcrops + (Total)',
                  'Pulses + (Total)', 'Rice and products', 'Starchy Roots + (Total)', 'Sugar Crops + (Total)',
                  'Vegetables + (Total)', ]
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
    df_losses_2010_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Concatenating
    df_losses = pd.concat([df_losses_1990_2013, df_losses_2010_2021])

    # Compute losses ([%] of production) -----------------------------------------------------------------------------------
    # Losses [%] = 1 / (1 - Losses [1000t] / Production [1000t]) (pre processing for multiplicating the workflow)

    # Step 1: Pivot the DataFrame
    pivot_df = df_losses.pivot_table(index=['Area', 'Year', 'Item'], columns='Element', values='Value').reset_index()

    # Step 2: Compute the Losses [%] (really it's unit less)
    pivot_df['Losses[%]'] = 1 / (1 - pivot_df['Losses'] / pivot_df['Production'])

    # Drop the columns Production, Import Quantity and Export Quantity
    pivot_df = pivot_df.drop(columns=['Production', 'Losses'])

    # Extrapolating for 2022 -----------------------------------------------------------------------------------------------

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csc = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-crops')

    # Merge based on 'Item'
    df_losses_pathwaycalc = pd.merge(df_dict_csc, pivot_df, on='Item')

    # Drop the 'Item' column
    df_losses_pathwaycalc = df_losses_pathwaycalc.drop(columns=['Item'])

    # Renaming existing columns (geoscale, timsecale, value)
    df_losses_pathwaycalc.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Losses[%]': 'value'}, inplace=True)

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_losses_pathwaycalc['module'] = 'agriculture'
    df_losses_pathwaycalc['lever'] = 'climate-smart-crop'
    df_losses_pathwaycalc['level'] = 0
    cols = df_losses_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_losses_pathwaycalc = df_losses_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_losses_pathwaycalc['geoscale'] = df_losses_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_losses_pathwaycalc['geoscale'] = df_losses_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                  'Netherlands')
    df_losses_pathwaycalc['geoscale'] = df_losses_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # RESIDUE SHARE --------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # YIELD ----------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # CROPS AND LIVESTOCK PRODUCTS (QCL) (for everything except lgn-energycrop, gas-energycrop, algae and insect)
    # List of elements
    list_elements = ['Yield']

    list_items = ['Cereals, primary + (Total)', 'Fibre Crops, Fibre Equivalent + (Total)', 'Fruit Primary + (Total)',
                  'Oilcrops, Oil Equivalent + (Total)', 'Pulses, Total + (Total)', 'Rice',
                  'Roots and Tubers, Total + (Total)',
                  'Sugar Crops Primary + (Total)', 'Vegetables Primary + (Total)']

    # 1990 - 2022
    code = 'QCL'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_yield_1990_2022 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Unit conversion from [100g/ha] to [t/ha]  ----------------------------------------------------------------------------

    # Step 1: Pivot the DataFrame
    pivot_df = df_yield_1990_2022.pivot_table(index=['Area', 'Year', 'Item'], columns='Element',
                                              values='Value').reset_index()

    # Step 2: Compute the Yield [t/ha]
    pivot_df['Yield[t/ha]'] = pivot_df['Yield'] * 0.0001

    # Drop the columns Yield
    pivot_df = pivot_df.drop(columns=['Yield'])

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csc = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-crops')

    # Merge based on 'Item'
    df_yield_pathwaycalc = pd.merge(df_dict_csc, pivot_df, on='Item')

    # Drop the 'Item' column
    df_yield_pathwaycalc = df_yield_pathwaycalc.drop(columns=['Item'])

    # Renaming existing columns (geoscale, timsecale, value)
    df_yield_pathwaycalc.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Yield[t/ha]': 'value'}, inplace=True)

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_yield_pathwaycalc['module'] = 'agriculture'
    df_yield_pathwaycalc['lever'] = 'climate-smart-crop'
    df_yield_pathwaycalc['level'] = 0
    cols = df_yield_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_yield_pathwaycalc = df_yield_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_yield_pathwaycalc['geoscale'] = df_yield_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_yield_pathwaycalc['geoscale'] = df_yield_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                'Netherlands')
    df_yield_pathwaycalc['geoscale'] = df_yield_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ------------------------------------------------------------------------------------------------------------------
    # YIELD ALGAE & INSECT ---------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # Is constant for all ots for all countries

    # Use (agroforestry_crop) as a structural basis
    yield_aps = agroforestry_crop[['timescale', 'geoscale']].copy()

    # Add the variables with a value of 0
    yield_aps['agr_climate-smart-crop_yield_algae[kcal/ha]'] = 119866666.666667
    yield_aps['agr_climate-smart-crop_yield_insect[kcal/ha]'] = 675000000.0

    # Melt the df
    yield_aps_pathwaycalc = pd.melt(yield_aps, id_vars=['timescale', 'geoscale'],
                                           value_vars=['agr_climate-smart-crop_yield_algae[kcal/ha]',
                                                       'agr_climate-smart-crop_yield_insect[kcal/ha]'],
                                           var_name='variables', value_name='value')

    # PathwayCalc formatting --------------------------------------------------------------------------------------------
    yield_aps_pathwaycalc['module'] = 'agriculture'
    yield_aps_pathwaycalc['lever'] = 'climate-smart-crop'
    yield_aps_pathwaycalc['level'] = 0
    cols = yield_aps_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('timescale'), cols.pop(cols.index('variables')))
    yield_aps_pathwaycalc = yield_aps_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    yield_aps_pathwaycalc['geoscale'] = yield_aps_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    yield_aps_pathwaycalc['geoscale'] = yield_aps_pathwaycalc['geoscale'].replace(
        'Netherlands (Kingdom of the)',
        'Netherlands')
    yield_aps_pathwaycalc['geoscale'] = yield_aps_pathwaycalc['geoscale'].replace('Czechia',
                                                                                                'Czech Republic')

    # FINAL RESULT ---------------------------------------------------------------------------------------------------------
    df_climate_smart_crop = pd.concat([df_input_pathwaycalc, df_losses_pathwaycalc])
    df_climate_smart_crop = pd.concat([df_climate_smart_crop, df_yield_pathwaycalc])
    df_climate_smart_crop = pd.concat([df_climate_smart_crop, agroforestry_crop_pathwaycalc])
    df_climate_smart_crop = pd.concat([df_climate_smart_crop, yield_aps_pathwaycalc])

    return df_climate_smart_crop

# CalculationLeaf CLIMATE SMART LIVESTOCK ------------------------------------------------------------------------------
def climate_smart_livestock_processing(df_csl_feed):

    # Common for all
    # List of countries
    list_countries = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark',
                      'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia',
                      'Lithuania', 'Luxembourg', 'Malta', 'Netherlands (Kingdom of the)', 'Poland', 'Portugal',
                      'Romania', 'Slovakia',
                      'Slovenia', 'Spain', 'Sweden', 'Switzerland',
                      'United Kingdom of Great Britain and Northern Ireland']

    # ----------------------------------------------------------------------------------------------------------------------
    # LIVESTOCK DENSITY & GRAZING INTENSITY ---------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    list_elements = ['Livestock units per agricultural land area', 'Share in total livestock']

    list_items = ['Major livestock types > (List)']

    # 1990 - 2021
    code = 'EK'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_density_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Renaming item as the same animal (for meat and live/producing/slaugthered animals)
    # Commenting only to consider grazing animals (cattle, buffalo, sheep, goat, horse)
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Pig', case=False, na=False), 'Item'] = 'Pig'
    df_density_1990_2021.loc[
        df_density_1990_2021['Item'].str.contains('Cattle', case=False, na=False), 'Item'] = 'Cattle'
    df_density_1990_2021.loc[
        df_density_1990_2021['Item'].str.contains('Buffalo', case=False, na=False), 'Item'] = 'Cattle'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Camel', case=False, na=False), 'Item'] = 'Other non-specified'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Rodent', case=False, na=False), 'Item'] = 'Other non-specified'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Chicken', case=False, na=False), 'Item'] = 'Chicken'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Duck', case=False, na=False), 'Item'] = 'Duck'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Geese', case=False, na=False), 'Item'] = 'Goose'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Pigeon', case=False, na=False), 'Item'] = 'Pigeon'
    df_density_1990_2021.loc[
        df_density_1990_2021['Item'].str.contains('Horses', case=False, na=False), 'Item'] = 'Horse'
    df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Sheep', case=False, na=False), 'Item'] = 'Sheep'
    df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Goat', case=False, na=False), 'Item'] = 'Goat'
    # df_density_1990_2021.loc[df_density_1990_2021['Item'].str.contains('Rabbits and hares', case=False, na=False), 'Item'] = 'Rabbit'

    # Aggregating
    # Reading excel lsu equivalent (for aggregatop,
    df_lsu = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/lsu_equivalent.xlsx',
        sheet_name='lsu_equivalent')
    # Merging
    df_density_1990_2021 = pd.merge(df_density_1990_2021, df_lsu, on='Item')

    # Aggregating
    df_density_1990_2021 = \
    df_density_1990_2021.groupby(['Aggregation', 'Area', 'Year', 'Element', 'Unit'], as_index=False)['Value'].sum()

    # Pivot the df
    pivot_df = df_density_1990_2021.pivot_table(index=['Area', 'Year', 'Aggregation'], columns='Element',
                                                values='Value').reset_index()

    # Normalize the share of ruminants
    pivot_df['Total ruminant share [%]'] = pivot_df.groupby(['Area', 'Year'])['Share in total livestock'].transform(
        'sum')
    pivot_df['Normalized ruminant share [%]'] = pivot_df['Share in total livestock'] / pivot_df[
        'Total ruminant share [%]']

    # Multiply Livestock per ha per type [lsu/ha] with the normalized ratio
    pivot_df['Livestock area per type per share [lsu/ha]'] = pivot_df['Livestock units per agricultural land area'] * \
                                                             pivot_df['Normalized ruminant share [%]']

    # Sum
    # Livestock density [lsu/ha] = sum per year & country (Livestock area per type per share [lsu/ha])
    pivot_df['Livestock density [lsu/ha]'] = pivot_df.groupby(['Area', 'Year'])[
        'Livestock area per type per share [lsu/ha]'].transform('sum')

    # Grouping for one value per country & year
    grouped_df = pivot_df.groupby(['Year', 'Area', 'Livestock density [lsu/ha]']).size().reset_index(name='Count')
    # Drop other columns by selecting only the desired columns
    grouped_df = grouped_df[['Year', 'Area', 'Livestock density [lsu/ha]']]

    # Adding an Item column for name
    grouped_df['Item'] = 'Density'

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Renaming into 'Value'
    grouped_df.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Livestock density [lsu/ha]': 'value'},
                      inplace=True)

    # Read excel file
    df_dict_csl = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock')

    # Merge based on 'Item'
    df_csl_density_pathwaycalc = pd.merge(df_dict_csl, grouped_df, on='Item')

    # Drop the 'Item' column
    df_csl_density_pathwaycalc = df_csl_density_pathwaycalc.drop(columns=['Item'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_csl_density_pathwaycalc['module'] = 'agriculture'
    df_csl_density_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_csl_density_pathwaycalc['level'] = 0
    cols = df_csl_density_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_csl_density_pathwaycalc = df_csl_density_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_csl_density_pathwaycalc['geoscale'] = df_csl_density_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_csl_density_pathwaycalc['geoscale'] = df_csl_density_pathwaycalc['geoscale'].replace(
        'Netherlands (Kingdom of the)',
        'Netherlands')
    df_csl_density_pathwaycalc['geoscale'] = df_csl_density_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # AGROFORESTRY (GRASSLAND & HEDGES) ------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    # Is equal to 0 for all ots for all countries

    # Use density (grouped_df) as a structural basis
    agroforestry_liv = grouped_df.copy()

    # Drop the column Item
    agroforestry_liv = agroforestry_liv.drop(columns=['Item', 'value'])

    # Rename the column in geoscale and timescale
    agroforestry_liv.rename(columns={'Area': 'geoscale', 'Year': 'timescale'}, inplace=True)

    # Changing data type to numeric (except for the geoscale column)
    agroforestry_liv.loc[:, agroforestry_liv.columns != 'geoscale'] = agroforestry_liv.loc[:,
                                                                        agroforestry_liv.columns != 'geoscale'].apply(
        pd.to_numeric, errors='coerce')

    # Add rows to have 1990-2022
    # Generate a DataFrame with all combinations of geoscale and timescale
    geoscale_values = agroforestry_liv['geoscale'].unique()
    timescale_values = pd.Series(range(1990, 2023))

    # Create a DataFrame for the cartesian product
    cartesian_product = pd.MultiIndex.from_product([geoscale_values, timescale_values],
                                                   names=['geoscale', 'timescale']).to_frame(index=False)

    # Merge the original DataFrame with the cartesian product to include all combinations
    agroforestry_liv = pd.merge(cartesian_product, agroforestry_liv, on=['geoscale', 'timescale'], how='left')

    # Add the variables with a value of 0
    agroforestry_liv['agr_climate-smart-livestock_ef_agroforestry_grassland[tC/ha]'] = 0
    agroforestry_liv['agr_climate-smart-livestock_ef_agroforestry_hedges[tC/ha]'] = 0

    # Melt the df
    agroforestry_liv_pathwaycalc = pd.melt(agroforestry_liv, id_vars=['timescale', 'geoscale'],
                    value_vars=['agr_climate-smart-livestock_ef_agroforestry_grassland[tC/ha]', 'agr_climate-smart-livestock_ef_agroforestry_hedges[tC/ha]'],
                    var_name='variables', value_name='value')

    # PathwayCalc formatting --------------------------------------------------------------------------------------------
    agroforestry_liv_pathwaycalc['module'] = 'agriculture'
    agroforestry_liv_pathwaycalc['lever'] = 'climate-smart-crop'
    agroforestry_liv_pathwaycalc['level'] = 0
    cols = agroforestry_liv_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('timescale'), cols.pop(cols.index('variables')))
    agroforestry_liv_pathwaycalc = agroforestry_liv_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    agroforestry_liv_pathwaycalc['geoscale'] = agroforestry_liv_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    agroforestry_liv_pathwaycalc['geoscale'] = agroforestry_liv_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                  'Netherlands')
    agroforestry_liv_pathwaycalc['geoscale'] = agroforestry_liv_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # ENTERIC EMISSIONS ----------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    list_elements = ['Enteric fermentation (Emissions CH4)', 'Stocks']

    list_items = ['All Animals > (List)']

    # 1990 - 2021
    code = 'GLE'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_enteric_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Renaming item as the same animal (for meat and live/producing/slaugthered animals)
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Cattle, dairy', case=False, na=False), 'Item'] = 'Dairy cows'
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Cattle, non-dairy', case=False, na=False), 'Item'] = 'Cattle'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Goat', case=False, na=False), 'Item'] = 'Goat'
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Chickens, broilers', case=False, na=False), 'Item'] = 'Chicken'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Chickens, layers', case=False,
                                                                       na=False), 'Item'] = 'Chicken laying hens'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Duck', case=False, na=False), 'Item'] = 'Duck'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Horse', case=False, na=False), 'Item'] = 'Horse'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Sheep', case=False, na=False), 'Item'] = 'Sheep'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Swine', case=False, na=False), 'Item'] = 'Pig'
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Turkey', case=False, na=False), 'Item'] = 'Turkey'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Asse', case=False, na=False), 'Item'] = 'Asse'
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Buffalo', case=False, na=False), 'Item'] = 'Buffalo'
    df_enteric_1990_2021.loc[df_enteric_1990_2021['Item'].str.contains('Mule', case=False, na=False), 'Item'] = 'Mule'
    df_enteric_1990_2021.loc[
        df_enteric_1990_2021['Item'].str.contains('Camel', case=False, na=False), 'Item'] = 'Other non-specified'

    # Reading excel lsu equivalent
    df_lsu = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/lsu_equivalent.xlsx',
        sheet_name='lsu_equivalent')
    # Merging
    df_enteric_1990_2021 = pd.merge(df_enteric_1990_2021, df_lsu, on='Item')

    # Converting Animals to lsu
    condition = df_enteric_1990_2021['Unit'] == 'An'
    df_enteric_1990_2021.loc[condition, 'Value'] *= df_enteric_1990_2021['lsu']

    # Aggregating
    df_enteric_1990_2021_grouped = \
    df_enteric_1990_2021.groupby(['Aggregation', 'Area', 'Year', 'Element', 'Unit'], as_index=False)['Value'].sum()

    # Pivot the df
    pivot_df = df_enteric_1990_2021_grouped.pivot_table(index=['Area', 'Year', 'Aggregation'], columns='Element',
                                                        values='Value').reset_index()

    # Enteric emissions CH4 [t/lsu] = 1000 * 'Enteric fermentation (Emissions CH4) [kt]'/ 'Stocks [lsu]'
    pivot_df['Enteric emissions CH4 [t/lsu]'] = 1000 * pivot_df['Enteric fermentation (Emissions CH4)'] / pivot_df[
        'Stocks']

    # Drop the columns 'Enteric fermentation (Emissions CH4)' 'Stocks'
    pivot_df = pivot_df.drop(columns=['Enteric fermentation (Emissions CH4)', 'Stocks'])

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Renaming into 'Value'
    pivot_df.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Enteric emissions CH4 [t/lsu]': 'value'},
                    inplace=True)

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csl_enteric = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock_enteric')

    # Merge based on 'Item' & 'Aggregation'
    df_enteric_pathwaycalc = pd.merge(df_dict_csl_enteric, pivot_df, left_on='Item', right_on='Aggregation')

    # Drop the 'Item' column
    df_enteric_pathwaycalc = df_enteric_pathwaycalc.drop(columns=['Item', 'Aggregation'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_enteric_pathwaycalc['module'] = 'agriculture'
    df_enteric_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_enteric_pathwaycalc['level'] = 0
    cols = df_enteric_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_enteric_pathwaycalc = df_enteric_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_enteric_pathwaycalc['geoscale'] = df_enteric_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_enteric_pathwaycalc['geoscale'] = df_enteric_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                    'Netherlands')
    df_enteric_pathwaycalc['geoscale'] = df_enteric_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # MANURE EMISSIONS (APPLIED, PASTURE & TREATED) ------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    list_elements = ['Amount excreted in manure (N content)', 'Manure left on pasture (N content)',
                     'Manure applied to soils (N content)', 'Losses from manure treated (N content)']

    list_items = ['All Animals > (List)']

    # 1990 - 2021
    code = 'EMN'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_manure_1990_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Renaming item as the same animal
    df_manure_1990_2021.loc[
        df_manure_1990_2021['Item'].str.contains('Cattle, dairy', case=False, na=False), 'Item'] = 'Dairy cows'
    df_manure_1990_2021.loc[
        df_manure_1990_2021['Item'].str.contains('Cattle, non-dairy', case=False, na=False), 'Item'] = 'Cattle'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Goat', case=False, na=False), 'Item'] = 'Goat'
    df_manure_1990_2021.loc[
        df_manure_1990_2021['Item'].str.contains('Chickens, broilers', case=False, na=False), 'Item'] = 'Chicken'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Chickens, layers', case=False,
                                                                     na=False), 'Item'] = 'Chicken laying hens'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Duck', case=False, na=False), 'Item'] = 'Duck'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Horse', case=False, na=False), 'Item'] = 'Horse'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Sheep', case=False, na=False), 'Item'] = 'Sheep'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Swine', case=False, na=False), 'Item'] = 'Pig'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Turkey', case=False, na=False), 'Item'] = 'Turkey'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Asse', case=False, na=False), 'Item'] = 'Asse'
    df_manure_1990_2021.loc[
        df_manure_1990_2021['Item'].str.contains('Buffalo', case=False, na=False), 'Item'] = 'Buffalo'
    df_manure_1990_2021.loc[df_manure_1990_2021['Item'].str.contains('Mule', case=False, na=False), 'Item'] = 'Mule'
    df_manure_1990_2021.loc[
        df_manure_1990_2021['Item'].str.contains('Camel', case=False, na=False), 'Item'] = 'Other non-specified'

    # Reading excel lsu equivalent (for aggregatop,
    df_lsu = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/lsu_equivalent.xlsx',
        sheet_name='lsu_equivalent')
    # Merging
    df_manure_1990_2021 = pd.merge(df_manure_1990_2021, df_lsu, on='Item')

    # Aggregating
    df_manure_1990_2021 = \
    df_manure_1990_2021.groupby(['Aggregation', 'Area', 'Year', 'Element', 'Unit'], as_index=False)['Value'].sum()

    # Pivot the df
    pivot_df = df_manure_1990_2021.pivot_table(index=['Area', 'Year', 'Aggregation'], columns='Element',
                                               values='Value').reset_index()

    # Manure applied/treated/pasture [%] = Manure applied to soil/treated/left on pasture (N content) [kg] / Amount excreted (N content) [kg]

    pivot_df['Manure applied [%]'] = pivot_df['Manure applied to soils (N content)'] / pivot_df[
        'Amount excreted in manure (N content)']
    pivot_df['Manure treated [%]'] = pivot_df['Losses from manure treated (N content)'] / pivot_df[
        'Amount excreted in manure (N content)']
    pivot_df['Manure pasture [%]'] = pivot_df['Manure left on pasture (N content)'] / pivot_df[
        'Amount excreted in manure (N content)']

    # Drop the columns
    pivot_df = pivot_df.drop(columns=['Manure applied to soils (N content)', 'Losses from manure treated (N content)',
                                      'Manure left on pasture (N content)', 'Amount excreted in manure (N content)'])

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Melt the DataFrame
    df_melted = pd.melt(pivot_df, id_vars=['Area', 'Year', 'Aggregation'],
                        value_vars=['Manure applied [%]', 'Manure treated [%]', 'Manure pasture [%]'],
                        var_name='Item', value_name='value')

    # Concatenate the aggregation column with the manure column names
    df_melted['Item'] = df_melted['Aggregation'] + ' ' + df_melted['Item']

    # Drop the aggregation column as it's now part of the item column
    df_melted = df_melted.drop(columns=['Aggregation'])

    # Renaming
    df_melted.rename(columns={'Area': 'geoscale', 'Year': 'timescale'}, inplace=True)

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csl = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock')

    # Merge based on 'Item' & 'Aggregation'
    df_manure_pathwaycalc = pd.merge(df_dict_csl, df_melted, on='Item')

    # Drop the 'Item' column
    df_manure_pathwaycalc = df_manure_pathwaycalc.drop(columns=['Item'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_manure_pathwaycalc['module'] = 'agriculture'
    df_manure_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_manure_pathwaycalc['level'] = 0
    cols = df_manure_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_manure_pathwaycalc = df_manure_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_manure_pathwaycalc['geoscale'] = df_manure_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_manure_pathwaycalc['geoscale'] = df_manure_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                  'Netherlands')
    df_manure_pathwaycalc['geoscale'] = df_manure_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # LOSSES ---------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # FOOD BALANCE SHEETS (FBS) - For everything  -------------------------------------------------
    # List of elements
    list_elements = ['Losses', 'Production Quantity']

    list_items = ['Animal Products > (List)']

    # 1990 - 2013
    code = 'FBSH'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_losses_csl_1990_2013 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Renaming Elements
    df_losses_csl_1990_2013.loc[df_losses_csl_1990_2013['Element'].str.contains('Production Quantity',
                                                                                case=False,
                                                                                na=False), 'Element'] = 'Production'

    # 2010 - 2022
    # Different list because different in item nomination such as rice
    list_elements = ['Losses', 'Production Quantity']
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
    df_losses_csl_2010_2021 = faostat.get_data_df(code, pars=my_pars, strval=False)
    # Renaming Elements
    df_losses_csl_2010_2021.loc[df_losses_csl_2010_2021['Element'].str.contains('Production Quantity',
                                                                                case=False,
                                                                                na=False), 'Element'] = 'Production'

    # Concatenating
    df_losses_csl = pd.concat([df_losses_csl_1990_2013, df_losses_csl_2010_2021])

    # Compute losses ([%] of production) -----------------------------------------------------------------------------------
    # Losses [%] = 1 / (1 - Losses [1000t] / Production [1000t]) (pre processing for multiplicating the workflow)

    # Step 1: Pivot the DataFrame
    pivot_df = df_losses_csl.pivot_table(index=['Area', 'Year', 'Item'], columns='Element',
                                         values='Value').reset_index()

    # Step 2: Compute the Losses [%] (really it's unit less)
    pivot_df['Losses[%]'] = 1 / (1 - pivot_df['Losses'] / pivot_df['Production'])

    # Drop the columns Production, Import Quantity and Export Quantity
    pivot_df = pivot_df.drop(columns=['Production', 'Losses'])

    # Extrapolating for 2022 -----------------------------------------------------------------------------------------------

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csl_losses = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock_losses')

    # Merge based on 'Item'
    df_losses_csl_pathwaycalc = pd.merge(df_dict_csl_losses, pivot_df, on='Item')

    # Drop the 'Item' column
    df_losses_csl_pathwaycalc = df_losses_csl_pathwaycalc.drop(columns=['Item'])

    # Renaming existing columns (geoscale, timsecale, value)
    df_losses_csl_pathwaycalc.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Losses[%]': 'value'},
                                     inplace=True)

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_losses_csl_pathwaycalc['module'] = 'agriculture'
    df_losses_csl_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_losses_csl_pathwaycalc['level'] = 0
    cols = df_losses_csl_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_losses_csl_pathwaycalc = df_losses_csl_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_losses_csl_pathwaycalc['geoscale'] = df_losses_csl_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_losses_csl_pathwaycalc['geoscale'] = df_losses_csl_pathwaycalc['geoscale'].replace(
        'Netherlands (Kingdom of the)',
        'Netherlands')
    df_losses_csl_pathwaycalc['geoscale'] = df_losses_csl_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # FEED RATION ----------------------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------------------------------
    # Fill nan with zeros
    df_csl_feed['Feed'].fillna(0, inplace=True)

    # Add a column with the total feed (per country and year)
    df_csl_feed['Total feed'] = df_csl_feed.groupby(['Area', 'Year'])['Feed'].transform('sum')

    # Feed ration [%] = Feed from item i / Total feed
    df_csl_feed['Feed ratio'] = df_csl_feed['Feed'] / df_csl_feed['Total feed']

    # Drop columns
    df_csl_feed = df_csl_feed.drop(columns=['Feed', 'Total feed'])

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Renaming into 'Value'
    df_csl_feed.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Feed ratio': 'value'}, inplace=True)

    # Read excel file
    df_dict_csl = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock')

    # Merge based on 'Item'
    df_csl_feed_pathwaycalc = pd.merge(df_dict_csl, df_csl_feed, on='Item')

    # Drop the 'Item' column
    df_csl_feed_pathwaycalc = df_csl_feed_pathwaycalc.drop(columns=['Item'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_csl_feed_pathwaycalc['module'] = 'agriculture'
    df_csl_feed_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_csl_feed_pathwaycalc['level'] = 0
    cols = df_csl_feed_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_csl_feed_pathwaycalc = df_csl_feed_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_csl_feed_pathwaycalc['geoscale'] = df_csl_feed_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_csl_feed_pathwaycalc['geoscale'] = df_csl_feed_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                      'Netherlands')
    df_csl_feed_pathwaycalc['geoscale'] = df_csl_feed_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # SLAUGHTERED LIVESTOCK  & YIELD (DAIRY & EGGS) ------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    list_elements = ['Producing Animals/Slaughtered', 'Production Quantity']

    list_items = ['Milk, Total > (List)', 'Eggs Primary > (List)']

    # 1990 - 2022
    code = 'QCL'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_producing_animals_1990_2022 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Drop the rows where Production is not in Nb of Eggs
    df_producing_animals_1990_2022 = df_producing_animals_1990_2022[df_producing_animals_1990_2022['Unit'] != '1000 No']

    # Renaming item as the same animal (for meat and live/producing/slaugthered animals)
    df_producing_animals_1990_2022.loc[
        df_producing_animals_1990_2022['Item'].str.contains('Cattle', case=False, na=False), 'Item'] = 'Dairy cows'
    df_producing_animals_1990_2022.loc[
        df_producing_animals_1990_2022['Item'].str.contains('Sheep', case=False, na=False), 'Item'] = 'Dairy sheep'
    df_producing_animals_1990_2022.loc[
        df_producing_animals_1990_2022['Item'].str.contains('Goat', case=False, na=False), 'Item'] = 'Dairy goat'
    df_producing_animals_1990_2022.loc[
        df_producing_animals_1990_2022['Item'].str.contains('Buffalo', case=False, na=False), 'Item'] = 'Dairy buffalo'
    df_producing_animals_1990_2022.loc[df_producing_animals_1990_2022['Item'].str.contains('Hen eggs', case=False,
                                                                                           na=False), 'Item'] = 'Chicken laying hens'
    df_producing_animals_1990_2022.loc[
        df_producing_animals_1990_2022['Item'].str.contains('Eggs from other birds', case=False,
                                                            na=False), 'Item'] = 'Other laying hens'

    # Unit conversion Poultry : [1000 An] => [An]
    df_producing_animals_1990_2022.loc[df_producing_animals_1990_2022['Unit'] == '1000 An', 'Value'] *= 1000

    # Reading excel lsu equivalent
    df_lsu = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/lsu_equivalent.xlsx',
        sheet_name='lsu_equivalent')
    # Merging
    df_producing_animals_1990_2022 = pd.merge(df_producing_animals_1990_2022, df_lsu, on='Item')

    # Converting Animals to lsu
    condition = (df_producing_animals_1990_2022['Unit'] == 'An') | (df_producing_animals_1990_2022['Unit'] == '1000 An')
    df_producing_animals_1990_2022.loc[condition, 'Value'] *= df_producing_animals_1990_2022['lsu']

    # Aggregating
    grouped_df = \
    df_producing_animals_1990_2022.groupby(['Aggregation', 'Area', 'Year', 'Element', 'Unit'], as_index=False)[
        'Value'].sum()

    # Pivot the df
    pivot_df = grouped_df.pivot_table(index=['Area', 'Year', 'Aggregation'], columns='Element',
                                      values='Value').reset_index()

    # "Merging" the columns 'Laying' and 'Milk Animals' into 'Producing Animals'
    # Replace NaN with 0
    pivot_df['Laying'].fillna(0, inplace=True)
    pivot_df['Milk Animals'].fillna(0, inplace=True)

    # Sum the columns to create the 'Producing Animals' column
    pivot_df['Producing Animals'] = pivot_df['Laying'] + pivot_df['Milk Animals']

    # Yield [t/lsu] = Production quantity / Producing animals/Slaugthered
    pivot_df['Yield [t/lsu]'] = pivot_df['Production'] / pivot_df['Producing Animals']

    # Drop the columns Yield
    pivot_df = pivot_df.drop(columns=['Laying', 'Milk Animals', 'Production', 'Producing Animals'])

    # ----------------------------------------------------------------------------------------------------------------------
    # SLAUGHTERED LIVESTOCK  & YIELD (MEAT) --------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    list_elements = ['Producing Animals/Slaughtered', 'Stocks', 'Production Quantity']

    list_items = ['Meat, Total > (List)', 'Live Animals > (List)']

    # 1990 - 2022
    code = 'QCL'
    my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
    my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
    my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
    list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
                  '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
                  '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
    my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

    my_pars = {
        'area': my_countries,
        'element': my_elements,
        'item': my_items,
        'year': my_years
    }
    df_slaughtered_1990_2022 = faostat.get_data_df(code, pars=my_pars, strval=False)

    # Dropping 'Bees'
    df_slaughtered_1990_2022 = df_slaughtered_1990_2022[df_slaughtered_1990_2022['Item'] != 'Bees']

    # Renaming item as the same animal (for meat and live/producing/slaugthered animals)
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Pig', case=False, na=False), 'Item'] = 'Pig'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Cattle', case=False, na=False), 'Item'] = 'Cattle'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Buffalo', case=False, na=False), 'Item'] = 'Cattle'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Camel', case=False, na=False), 'Item'] = 'Other non-specified'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Rodent', case=False, na=False), 'Item'] = 'Other non-specified'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Chicken', case=False, na=False), 'Item'] = 'Chicken'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Duck', case=False, na=False), 'Item'] = 'Duck'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Geese', case=False, na=False), 'Item'] = 'Goose'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Pigeon', case=False, na=False), 'Item'] = 'Pigeon'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Horses', case=False, na=False), 'Item'] = 'Horse'
    df_slaughtered_1990_2022.loc[
        df_slaughtered_1990_2022['Item'].str.contains('Rabbits and hares', case=False, na=False), 'Item'] = 'Rabbit'

    # Unit conversion Poultry : [1000 An] => [An]
    df_slaughtered_1990_2022.loc[df_slaughtered_1990_2022['Unit'] == '1000 An', 'Value'] *= 1000

    # Reading excel lsu equivalent
    df_lsu = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/lsu_equivalent.xlsx',
        sheet_name='lsu_equivalent')
    # Merging
    df_slaughtered_1990_2022 = pd.merge(df_slaughtered_1990_2022, df_lsu, on='Item')

    # Converting Animals to lsu
    condition = (df_slaughtered_1990_2022['Unit'] == 'An') | (df_slaughtered_1990_2022['Unit'] == '1000 An')
    df_slaughtered_1990_2022.loc[condition, 'Value'] *= df_slaughtered_1990_2022['lsu']

    # Aggregating
    grouped_df = df_slaughtered_1990_2022.groupby(['Aggregation', 'Area', 'Year', 'Element', 'Unit'], as_index=False)[
        'Value'].sum()

    # Pivot the df
    pivot_df_slau = grouped_df.pivot_table(index=['Area', 'Year', 'Aggregation'], columns='Element',
                                           values='Value').reset_index()

    # Replace NaN with 0
    pivot_df_slau['Producing Animals/Slaughtered'].fillna(0, inplace=True)
    pivot_df_slau['Production'].fillna(0, inplace=True)

    # Slaughtered animals [%] = 'Producing Animals/Slaughtered' / 'Stocks'
    pivot_df_slau['Slaughtered animals [%]'] = pivot_df_slau['Producing Animals/Slaughtered'] / pivot_df_slau['Stocks']

    # Yield [t/lsu] = Production quantity / Producing animals/Slaugthered
    pivot_df_slau['Yield [t/lsu]'] = pivot_df_slau['Production'] / pivot_df_slau['Producing Animals/Slaughtered']

    # Drop the columns
    pivot_df_slau = pivot_df_slau.drop(columns=['Producing Animals/Slaughtered', 'Stocks', 'Production'])

    # Replace NaN with 0
    pivot_df_slau['Yield [t/lsu]'].fillna(0, inplace=True)
    pivot_df_slau['Slaughtered animals [%]'].fillna(0, inplace=True)

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------

    # Separating between slaugthered animals and yield (for meat)
    df_yield_meat = pivot_df_slau[['Area', 'Year', 'Aggregation', 'Yield [t/lsu]']]
    df_slau_meat = pivot_df_slau[['Area', 'Year', 'Aggregation', 'Slaughtered animals [%]']]

    # Creating copies
    df_yield_meat = df_yield_meat.copy()
    df_slau_meat = df_slau_meat.copy()

    # Renaming into 'Value'
    df_yield_meat.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Yield [t/lsu]': 'value'}, inplace=True)
    pivot_df.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Yield [t/lsu]': 'value'}, inplace=True)
    df_slau_meat.rename(columns={'Area': 'geoscale', 'Year': 'timescale', 'Slaughtered animals [%]': 'value'},
                        inplace=True)

    # Concatenating yield (meat, milk & eggs)
    df_yield_liv = pd.concat([df_yield_meat, pivot_df])

    # Food item name matching with dictionary
    # Read excel file
    df_dict_csl_yield = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock_yield')
    df_dict_csl_slau = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-livestock_slau')

    # Merge based on 'Item'
    df_yield_liv_pathwaycalc = pd.merge(df_dict_csl_yield, df_yield_liv, left_on='Item', right_on='Aggregation')
    df_slau_liv_pathwaycalc = pd.merge(df_dict_csl_slau, df_slau_meat, left_on='Item', right_on='Aggregation')

    # Drop the 'Item' column
    df_yield_liv_pathwaycalc = df_yield_liv_pathwaycalc.drop(columns=['Item', 'Aggregation'])
    df_slau_liv_pathwaycalc = df_slau_liv_pathwaycalc.drop(columns=['Item', 'Aggregation'])

    # Concatenating yield and slau
    df_yield_slau_liv_pathwaycalc = pd.concat([df_yield_liv_pathwaycalc, df_slau_liv_pathwaycalc])

    # Adding the columns module, lever, level and string-pivot at the correct places
    df_yield_slau_liv_pathwaycalc['module'] = 'agriculture'
    df_yield_slau_liv_pathwaycalc['lever'] = 'climate-smart-livestock'
    df_yield_slau_liv_pathwaycalc['level'] = 0
    cols = df_yield_slau_liv_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    df_yield_pathwaycalc = df_yield_slau_liv_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_yield_slau_liv_pathwaycalc['geoscale'] = df_yield_slau_liv_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_yield_slau_liv_pathwaycalc['geoscale'] = df_yield_slau_liv_pathwaycalc['geoscale'].replace(
        'Netherlands (Kingdom of the)',
        'Netherlands')
    df_yield_slau_liv_pathwaycalc['geoscale'] = df_yield_slau_liv_pathwaycalc['geoscale'].replace('Czechia',
                                                                                                  'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # FINAL RESULTS --------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    df_csl = pd.concat([df_csl_density_pathwaycalc, df_enteric_pathwaycalc])
    df_csl = pd.concat([df_csl, df_manure_pathwaycalc])
    df_csl = pd.concat([df_csl, df_losses_csl_pathwaycalc])
    df_csl = pd.concat([df_csl, df_csl_feed_pathwaycalc])
    df_csl = pd.concat([df_csl, df_yield_slau_liv_pathwaycalc])
    df_csl = pd.concat([df_csl, agroforestry_liv_pathwaycalc])

    return df_csl

# CalculationLeaf CLIMATE SMART FORESTRY -------------------------------------------------------------------------------
def climate_smart_forestry_processing():

    # ----------------------------------------------------------------------------------------------------------------------
    # INCREMENTAL GROWTH [m3/ha] -------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # Read csv
    df_g_inc = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='annual_ginc_per_area_m3ha')

    # Read and format forest area for later
    df_area = pd.read_csv(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/fra-extentOfForest.csv')
    df_area.columns = df_area.iloc[0]
    df_area = df_area[1:]
    # Rename column name 'geoscale'
    df_area.rename(columns={df_area.columns[0]: 'geoscale'}, inplace=True)

    # Format correctly
    # Melting the dfs to have the relevant format (geoscale, year, value)
    df_g_inc = pd.melt(df_g_inc, id_vars=['geoscale'], var_name='timescale', value_name='value')
    df_area = pd.melt(df_area, id_vars=['geoscale'], var_name='timescale', value_name='forest area [ha]')
    # Changing data type to numeric (except for the geoscale column)
    df_g_inc.loc[:, df_g_inc.columns != 'geoscale'] = df_g_inc.loc[:, df_g_inc.columns != 'geoscale'].apply(
        pd.to_numeric, errors='coerce')
    # Merge the dfs (growing stock and area) to filter the relevant countries
    df_g_inc_area = pd.merge(df_g_inc, df_area, on=['geoscale', 'timescale'])
    # Only keep the columns geoscale, timescale and value
    df_g_inc_area = df_g_inc_area[['geoscale', 'timescale', 'value']]
    df_g_inc_area_pathwaycalc = df_g_inc_area.copy()

    # DEPRECIATED Compute the incremental difference -----------------------------------------------------------------------------------
    # Ensure the DataFrame is sorted by geoscale and timescale
    # df_g_inc.sort_values(by=['geoscale', 'timescale'], inplace=True)

    # Compute the incremental growing stock for each country : incremental growing stock [m3] = growing stock y(i) - growing stock y(i-1)
    # df_g_inc['incremental growing stock [m3/ha]'] = df_g_inc.groupby('geoscale')['growing stock [m3/ha]'].diff()

    # Calculate the number of years between each period
    # df_g_inc['years_diff'] = df_g_inc.groupby('geoscale')['timescale'].diff()

    # Calculate the annual increment by dividing the incremental growing stock by the number of years
    # df_g_inc['annual increment [m3/ha/yr]'] = df_g_inc['incremental growing stock [m3/ha]'] / df_g_inc['years_diff']

    # Drop the rows that are not countries (they both contain 2024)
    # df_g_inc_area = df_g_inc_area[~df_g_inc_area['geoscale'].str.contains('2024', na=False)]

    # Incremental growing stock [m3/ha] = Incremental growing stock [m3] / forest area [ha]
    # df_g_inc_area['Incremental growing stock [m3/ha]'] = df_g_inc_area['incremental growing stock [m3]'] / df_g_inc_area['forest area [ha]']

    # Incremental growing stock [m3/ha] = Incremental growing stock [m3] / forest area [ha]
    # df_g_inc_area['value'] = df_g_inc_area['annual increment [m3/yr]'] / df_g_inc_area['forest area [ha]']

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------
    # Adding the columns module, lever, level and string-pivot at the correct places
    df_g_inc_area_pathwaycalc['module'] = 'land-use'
    df_g_inc_area_pathwaycalc['lever'] = 'climate-smart-forestry'
    df_g_inc_area_pathwaycalc['level'] = 0
    df_g_inc_area_pathwaycalc['variables'] = 'agr_climate-smart-forestry_g-inc[m3/ha]'
    cols = df_g_inc_area_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('geoscale'), cols.pop(cols.index('variables')))
    df_g_inc_area_pathwaycalc = df_g_inc_area_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    df_g_inc_area_pathwaycalc['geoscale'] = df_g_inc_area_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    df_g_inc_area_pathwaycalc['geoscale'] = df_g_inc_area_pathwaycalc['geoscale'].replace(
        'Netherlands (Kingdom of the)',
        'Netherlands')
    df_g_inc_area_pathwaycalc['geoscale'] = df_g_inc_area_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # CSF MANAGED ----------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # Is equal to 0 for all ots for all countries

    # Use df_g_inc_area_pathwaycalc as a structural basis
    csf_managed = df_g_inc_area_pathwaycalc.copy()

    # Add rows to have 1990-2022
    # Generate a DataFrame with all combinations of geoscale and timescale
    geoscale_values = csf_managed['geoscale'].unique()
    timescale_values = pd.Series(range(1990, 2023))

    # Create a DataFrame for the cartesian product
    cartesian_product = pd.MultiIndex.from_product([geoscale_values, timescale_values],
                                                   names=['geoscale', 'timescale']).to_frame(index=False)

    # Merge the original DataFrame with the cartesian product to include all combinations
    csf_managed = pd.merge(cartesian_product, csf_managed, on=['geoscale', 'timescale'], how='left')

    # Replace the variable with ots_agr_climate-smart-forestry_csf-man[m3/ha]
    csf_managed['variables'] = 'agr_climate-smart-forestry_csf-man[m3/ha]'

    # Replace the value with 0
    csf_managed['value'] = 0

    # PathwayCalc formatting
    csf_managed['module'] = 'land-use'
    csf_managed['lever'] = 'climate-smart-forestry'
    csf_managed['level'] = 0
    cols = csf_managed.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    csf_managed = csf_managed[cols]

    # ----------------------------------------------------------------------------------------------------------------------
    # FAWS SHARE & GSTOCK (FAWS & NON FAWS)  -------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # Read files (growing stock available fo wood supply and not)
    gstock_total = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='gstock_total_Mm3')
    gstock_faws = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='gstock_faws_Mm3')
    area_faws = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='forest_area_faws_1000ha')

    # Format correctly
    # Melting the dfs to have the relevant format (geoscale, year, value)
    gstock_faws = pd.melt(gstock_faws, id_vars=['geoscale'], var_name='timescale',
                          value_name='growing stock faws [Mm3]')
    area_faws = pd.melt(area_faws, id_vars=['geoscale'], var_name='timescale', value_name='area faws [1000ha]')
    gstock_total = pd.melt(gstock_total, id_vars=['geoscale'], var_name='timescale',
                           value_name='growing stock total [Mm3]')
    # Convert 'year' to integer type (optional, for better numerical handling)
    gstock_faws['timescale'] = gstock_faws['timescale'].astype(int)
    area_faws['timescale'] = area_faws['timescale'].astype(int)
    gstock_total['timescale'] = gstock_total['timescale'].astype(int)

    # Merge together and  with forest area (df_area) (also filters the relevant countries)
    gstock = pd.merge(gstock_faws, gstock_total, on=['geoscale', 'timescale'])
    gstock = pd.merge(gstock, area_faws, on=['geoscale', 'timescale'])
    gstock = pd.merge(gstock, df_area, on=['geoscale', 'timescale'])

    # Changing data type to numeric (except for the geoscale column)
    gstock.loc[:, gstock.columns != 'geoscale'] = gstock.loc[:, gstock.columns != 'geoscale'].apply(pd.to_numeric,
                                                                                                    errors='coerce')

    # Growing stock not faws [m3] = Growing stock total [m3] - Growing stock faws [m3]
    gstock['growing stock non faws [Mm3]'] = gstock['growing stock total [Mm3]'] - gstock['growing stock faws [Mm3]']

    # Forest area not for wood supply [ha] = total forest area [ha] - forest available for wood supply [ha]
    gstock['area non faws [ha]'] = gstock['forest area [ha]'] - 1000 * gstock['area faws [1000ha]']

    # Growing stock faws [m3/ha] = 10**6 * Growing stock faws [Mm3] / forest available for wood supply [ha]
    gstock['Growing stock faws [m3/ha]'] = (10 ** 6 * gstock['growing stock faws [Mm3]']) / (
                1000 * gstock['area faws [1000ha]'])

    # Growing stock non faws [m3/ha] = 10**6 * Growing stock non faws [Mm3] / forest non faws [ha]
    gstock['Growing stock non faws [m3/ha]'] = (10 ** 6 * gstock['growing stock non faws [Mm3]']) / gstock[
        'area non faws [ha]']

    # Share faws [%] = total forest area [ha] - forest available for wood supply [ha]
    gstock['Share faws [%]'] = 1000 * gstock['area faws [1000ha]'] / gstock['forest area [ha]']

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------
    # Melt the DataFrame
    gstock_pathwaycalc = pd.melt(gstock, id_vars=['geoscale', 'timescale'],
                                 value_vars=['Growing stock faws [m3/ha]', 'Growing stock non faws [m3/ha]',
                                             'Share faws [%]'],
                                 var_name='Item', value_name='value')

    # Read excel file
    df_dict_forestry = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-forestry')

    # Merge based on 'Item'
    gstock_pathwaycalc = pd.merge(df_dict_forestry, gstock_pathwaycalc, on='Item')

    # Drop the 'Item' column
    gstock_pathwaycalc = gstock_pathwaycalc.drop(columns=['Item'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    gstock_pathwaycalc['module'] = 'land-use'
    gstock_pathwaycalc['lever'] = 'climate-smart-forestry'
    gstock_pathwaycalc['level'] = 0
    cols = gstock_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    gstock_pathwaycalc = gstock_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    gstock_pathwaycalc['geoscale'] = gstock_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    gstock_pathwaycalc['geoscale'] = gstock_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                            'Netherlands')
    gstock_pathwaycalc['geoscale'] = gstock_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # HARVESTING RATE -------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    # Read files (growing stock available fo wood supply and not)
    h_rate = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='h-rate')

    # Format correctly
    # Melting the dfs to have the relevant format (geoscale, year, value)
    h_rate = pd.melt(h_rate, id_vars=['geoscale'], var_name='timescale', value_name='value')
    # Convert 'year' to integer type (optional, for better numerical handling)
    h_rate['timescale'] = h_rate['timescale'].astype(int)

    # Merge with forest area (df_area) (to filter the relevant countries) then filter out
    h_rate = pd.merge(h_rate, df_area, on=['geoscale', 'timescale'])
    h_rate = h_rate[['geoscale', 'timescale', 'value']]

    # Create copy
    h_rate_pathwaycalc = h_rate.copy()

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------
    # Adding the columns module, lever, level and string-pivot at the correct places
    h_rate_pathwaycalc['module'] = 'land-use'
    h_rate_pathwaycalc['lever'] = 'climate-smart-forestry'
    h_rate_pathwaycalc['level'] = 0
    h_rate_pathwaycalc['variables'] = 'agr_climate-smart-forestry_h-rate[%]'
    cols = h_rate_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    cols.insert(cols.index('geoscale'), cols.pop(cols.index('variables')))
    h_rate_pathwaycalc = h_rate_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    h_rate_pathwaycalc['geoscale'] = h_rate_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    h_rate_pathwaycalc['geoscale'] = h_rate_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                            'Netherlands')
    h_rate_pathwaycalc['geoscale'] = h_rate_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # NATURAL LOSSES -------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # Read file
    nat_losses = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_forestry.xlsx',
        sheet_name='nat-losses_1000ha')

    # Format correctly
    # Melt the DataFrame to long format
    df_melted = pd.melt(nat_losses, id_vars=['geoscale'], var_name='variable', value_name='Losses [1000ha]')

    # Extract 'item' and 'year' from the 'variable' column
    df_melted['Item'] = df_melted['variable'].str.extract(r'^(.*?)\s\d{4}$')[0]
    df_melted['timescale'] = df_melted['variable'].str.extract(r'(\d{4})$')[0]

    # Drop the original 'variable' column
    df_melted = df_melted.drop(columns=['variable'])

    # Rearrange the columns
    nat_losses = df_melted[['geoscale', 'timescale', 'Item', 'Losses [1000ha]']]

    # Change type to numeric for timescale to merge
    nat_losses['timescale'] = nat_losses['timescale'].apply(pd.to_numeric, errors='coerce')

    # Adding forest area and total growing stock
    nat_losses = pd.merge(nat_losses, df_area, on=['geoscale', 'timescale'])
    nat_losses = pd.merge(nat_losses, gstock_total, on=['geoscale', 'timescale'])

    # Change type to numeric
    numeric_cols = nat_losses.columns[3:]  # Get all columns except the first three
    nat_losses[numeric_cols] = nat_losses[numeric_cols].apply(pd.to_numeric,
                                                              errors='coerce')  # Convert to numeric, if not already

    # Ratio of losses area compared to total forest area
    nat_losses['Ratio of losses'] = 1000 * nat_losses['Losses [1000ha]'] / nat_losses['forest area [ha]']

    # Growing stock total [m3/ha] = Growing stock [Mm3] / forest area [ha]
    nat_losses['Growing stock total [m3/ha]'] = 10 ** 6 * nat_losses['growing stock total [Mm3]'] / nat_losses[
        'forest area [ha]']

    # Losses [m3/ha] = Ratio of losses [%] * Growing stock total [m3/ha]
    nat_losses['value'] = nat_losses['Ratio of losses'] * nat_losses['Growing stock total [m3/ha]']

    # Filtering
    nat_losses_pathwaycalc = nat_losses.copy()
    nat_losses_pathwaycalc = nat_losses_pathwaycalc[['Item', 'geoscale', 'timescale', 'value']]

    # PathwayCalc formatting -----------------------------------------------------------------------------------------------
    # Read excel file
    df_dict_forestry = pd.read_excel(
        '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
        sheet_name='climate-smart-forestry')

    # Merge based on 'Item'
    nat_losses_pathwaycalc = pd.merge(df_dict_forestry, nat_losses_pathwaycalc, on='Item')

    # Drop the 'Item' column
    nat_losses_pathwaycalc = nat_losses_pathwaycalc.drop(columns=['Item'])

    # Adding the columns module, lever, level and string-pivot at the correct places
    nat_losses_pathwaycalc['module'] = 'land-use'
    nat_losses_pathwaycalc['lever'] = 'climate-smart-forestry'
    nat_losses_pathwaycalc['level'] = 0
    cols = nat_losses_pathwaycalc.columns.tolist()
    cols.insert(cols.index('value'), cols.pop(cols.index('module')))
    cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
    cols.insert(cols.index('value'), cols.pop(cols.index('level')))
    nat_losses_pathwaycalc = nat_losses_pathwaycalc[cols]

    # Rename countries to Pathaywcalc name
    nat_losses_pathwaycalc['geoscale'] = nat_losses_pathwaycalc['geoscale'].replace(
        'United Kingdom of Great Britain and Northern Ireland', 'United Kingdom')
    nat_losses_pathwaycalc['geoscale'] = nat_losses_pathwaycalc['geoscale'].replace('Netherlands (Kingdom of the)',
                                                                                    'Netherlands')
    nat_losses_pathwaycalc['geoscale'] = nat_losses_pathwaycalc['geoscale'].replace('Czechia', 'Czech Republic')

    # ----------------------------------------------------------------------------------------------------------------------
    # FINAL RESULT ---------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # Concat all dfs together
    df_csf = pd.concat([df_g_inc_area_pathwaycalc, csf_managed])
    df_csf = pd.concat([df_csf, gstock_pathwaycalc])
    df_csf = pd.concat([df_csf, h_rate_pathwaycalc])
    df_csf = pd.concat([df_csf, nat_losses_pathwaycalc])
    return df_csf, csf_managed

#years_setting = [1990, 2022, 2050, 5]  # Set the timestep for historical years & scenarios
#years_ots = create_ots_years_list(years_setting)

# CalculationTree RUNNING PRE-PROCESSING -----------------------------------------------------------------------------------------------

#df_ssr_pathwaycalc, df_csl_feed = self_sufficiency_processing()
#df_climate_smart_crop = climate_smart_crop_processing()
#df_climate_smart_livestock = climate_smart_livestock_processing(df_csl_feed)
df_csf, csf_managed = climate_smart_forestry_processing()

#df_climate_smart_livestock.to_csv('climate-smart-livestock_29-07-24.csv', index=False)


# CalculationLeaf LAND MANAGEMENT --------------------------------------------------------------------------------------

# Importing UNFCCC excel files and reading them with a loop (only for Switzerland)

# ----------------------------------------------------------------------------------------------------------------------
# LAND MATRIX & LAND MAN USE----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# 1990 to 2020 , to update !

# Importing UNFCCC excel files and reading them with a loop (only for Switzerland) Table 4.1 ---------------------------
# Putting in a df in 3 dimensions (from, to, year)
# Define the path where the Excel files are located
folder_path = '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/data/data_unfccc'

# List all files in the folder
files = os.listdir(folder_path)

# Filter and sort files by the year (1990 to 2020)
sorted_files = sorted([f for f in files if f.startswith('CHE_2022_') and int(f.split('_')[2]) in range(1990, 2021)],
                      key=lambda x: int(x.split('_')[2]))

# Initialize a list to store DataFrames
data_frames = []

# Loop through sorted files, read the required rows, and append to the list
for file in sorted_files:
    # Extract the year from the filename
    year = int(file.split('_')[2])

    # Full path to the file
    file_path = os.path.join(folder_path, file)

    # Read the specific rows and sheet from the Excel file
    df = pd.read_excel(file_path, sheet_name='Table4.1', skiprows=4, nrows=14, header=None)

    # Add a column for the year to the DataFrame
    df['Year'] = year

    # Append to the list of DataFrames
    data_frames.append(df)

# Combine all DataFrames into a single DataFrame with a multi-index
combined_df = pd.concat(data_frames, axis=0).set_index(['Year'])

# Create a 3D array
values_3d = np.array([df.values for df in data_frames])

# Convert array in string
data = values_3d.astype(str)

# Create a row mask where the first column of each 14x13 slice doesn't contain 'unmanaged' -----------------------------
row_mask = np.all(np.core.defchararray.find(data[:, :, 0], 'unmanaged') == -1, axis=0)

# Create a column mask where the first row of each 14x13 slice doesn't contain 'unmanaged'
col_mask = np.all(np.core.defchararray.find(data[:, 0, :], 'unmanaged') == -1, axis=0)

# Apply the row mask to keep rows in each slice that do not contain 'unmanaged' in the first column
filtered_data = data[:, row_mask, :]

# Apply the column mask to keep columns in each slice that do not contain 'unmanaged' in the first row
filtered_data = filtered_data[:, :, col_mask]

# Creating a copy due to mask issue in the following steps
filtered_data = filtered_data.copy()

# Dropping the row that contain 'FROM' (index 1) ---------------------------------------------------------------------------------
# Function to drop the second row (index 1) in a 14x13 slice
def drop_second_row(slice_2d):
    # Create a mask for all rows except the one to drop (row index 1)
    row_mask = np.arange(slice_2d.shape[0]) != 1

    # Keep only the rows that are not the second row
    filtered_slice = slice_2d[row_mask, :]

    return filtered_slice

# Apply the function to each 14x13 slice
filtered_data_2 = np.array([drop_second_row(filtered_data[i]) for i in range(filtered_data.shape[0])])

# Create a copy for potential issues due to mask
filtered_data_2 = filtered_data_2.copy()

# LAND MATRIX -------------------------------------------------------------------------------------------------------------

# Create a copy
array_land_matrix = filtered_data_2.copy()

# Drop the unwanted row and column to only keep the land to and from (not final)
# Function to drop the second row (index 1) in a 14x13 slice
def drop_rows_and_columns(slice_2d, rows_to_drop=None, cols_to_drop=None):
    """
    Drop specific rows and columns from a 2D NumPy array.

    Parameters:
    slice_2d (np.ndarray): The 2D NumPy array from which rows and columns will be dropped.
    rows_to_drop (list or None): List of row indices to be dropped. If None, no rows are dropped.
    cols_to_drop (list or None): List of column indices to be dropped. If None, no columns are dropped.

    Returns:
    np.ndarray: The modified 2D NumPy array with specified rows and columns removed.
    """
    # If rows_to_drop is None or empty, don't drop any rows
    if rows_to_drop is None:
        rows_to_drop = []
    # If cols_to_drop is None or empty, don't drop any columns
    if cols_to_drop is None:
        cols_to_drop = []

    # Create a mask for rows to keep (not in rows_to_drop)
    if rows_to_drop:
        row_mask = np.ones(slice_2d.shape[0], dtype=bool)
        row_mask[rows_to_drop] = False
    else:
        row_mask = np.ones(slice_2d.shape[0], dtype=bool)

    # Create a mask for columns to keep (not in cols_to_drop)
    if cols_to_drop:
        col_mask = np.ones(slice_2d.shape[1], dtype=bool)
        col_mask[cols_to_drop] = False
    else:
        col_mask = np.ones(slice_2d.shape[1], dtype=bool)

    # Apply the masks to keep only the rows and columns that are not in the drop lists
    filtered_slice = slice_2d[row_mask, :][:, col_mask]

    return filtered_slice

# Apply the function to each 14x13 slice
array_land_matrix = np.array([drop_rows_and_columns(array_land_matrix[i], rows_to_drop=[7,8], cols_to_drop=None) for i in range(array_land_matrix.shape[0])])

# Transform in a df
# Reshape array
array_2d = array_land_matrix.reshape(-1, array_land_matrix.shape[2])
# Convert the 2D array to a DataFrame
df_land_matrix = pd.DataFrame(array_2d)

# Set the first row as index
df_land_matrix.columns = df_land_matrix.iloc[0]  # Set the first row as the new column headers
df_land_matrix = df_land_matrix[1:]  # Remove the first row from the DataFrame
df_land_matrix = df_land_matrix.reset_index(drop=True)  # Reset the index after removing the first row

# Drop the rows that contain TO:
df_land_matrix = df_land_matrix[~df_land_matrix.apply(lambda row: row.astype(str).str.contains('TO:').any(), axis=1)]

# Rename cols 1990 into timescale
df_land_matrix.rename(columns={'1990': 'timescale'}, inplace=True)

# Change type to numeric
numeric_cols = df_land_matrix.columns[1:]  # Get all columns except the first three
df_land_matrix[numeric_cols] = df_land_matrix[numeric_cols].apply(pd.to_numeric,
                                                             errors='coerce')  # Convert to numeric, if not already


# Divide each column by the initial area to convert from [ha] to [%]
df_land_matrix['Forest land (managed)'] = df_land_matrix['Forest land (managed)'] / df_land_matrix['Initial area']
df_land_matrix['Cropland '] = df_land_matrix['Cropland '] / df_land_matrix['Initial area']
df_land_matrix['Grassland (managed)'] = df_land_matrix['Grassland (managed)'] / df_land_matrix['Initial area']
df_land_matrix['Wetlands (managed)'] = df_land_matrix['Wetlands (managed)'] / df_land_matrix['Initial area']
df_land_matrix['Settlements'] = df_land_matrix['Settlements'] / df_land_matrix['Initial area']
df_land_matrix['Other land'] = df_land_matrix['Other land'] / df_land_matrix['Initial area']

# Drop the column 'Initial area'
df_land_matrix = df_land_matrix.drop(columns=['Initial area'])

# Melt to have year, values, land-to and land-from
df_land_matrix = pd.melt(df_land_matrix, id_vars=['TO:', 'timescale'],
                    value_vars=['Forest land (managed)', 'Cropland ', 'Grassland (managed)', 'Wetlands (managed)',
                                'Settlements', 'Other land'],
                    var_name='FROM:', value_name='value')

# Combine 'TO:' and 'FROM:' columns into a single 'item' column
df_land_matrix['Item'] = df_land_matrix['FROM:'] + ' to '+ df_land_matrix['TO:']

# Drop the original 'TO:' and 'FROM:' columns if no longer needed
df_land_matrix = df_land_matrix.drop(columns=['TO:', 'FROM:'])

# PathwayCalc formatting -----------------------------------------------------------------------------------------------
# Match with dictionary for correct names
# Read excel file
df_dict_land_man = pd.read_excel(
    '/Users/crosnier/Documents/PathwayCalc/_database/pre_processing/agriculture & land use/dictionaries/dictionnary_agriculture_landuse.xlsx',
    sheet_name='land-management')

# Merge based on 'Item'
df_land_matrix_pathwaycalc = pd.merge(df_dict_land_man, df_land_matrix, on='Item')

# Drop the 'Item' column
df_land_matrix_pathwaycalc = df_land_matrix_pathwaycalc.drop(columns=['Item'])

# Adding the columns module, lever, level and string-pivot at the correct places
df_land_matrix_pathwaycalc['module'] = 'land-use'
df_land_matrix_pathwaycalc['lever'] = 'land-man'
df_land_matrix_pathwaycalc['level'] = 0
df_land_matrix_pathwaycalc['geoscale'] = 'Switzerland'
cols = df_land_matrix_pathwaycalc.columns.tolist()
cols.insert(cols.index('value'), cols.pop(cols.index('module')))
cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
cols.insert(cols.index('value'), cols.pop(cols.index('level')))
cols.insert(cols.index('timescale'), cols.pop(cols.index('geoscale')))
df_land_matrix_pathwaycalc = df_land_matrix_pathwaycalc[cols]

# LAND USE -------------------------------------------------------------------------------------------------------------
# Use the row 'Final area' for 'land-man_use' forest, other, settlement and wetland ------------------------------------
def keep_final_use_row(slice_2d):
    # Create a mask for all rows except the one to drop (row index 1)
    row_mask = np.arange(slice_2d.shape[0]) == 7

    # Keep only the rows that are not the second row
    filtered_slice = slice_2d[row_mask, :]

    return filtered_slice


# Apply the function to each 14x13 slice
filtered_data_land_use = np.array([keep_final_use_row(filtered_data_2[i]) for i in range(filtered_data_2.shape[0])])

# Transform  array in df
# Remove the extra dimension
reshaped_array = filtered_data_land_use.reshape(31, 9)
# Create a DataFrame from the reshaped array
df_land_use = pd.DataFrame(reshaped_array)

# Change the correct indices for columns
new_column_names = ['element', 'agr_land-man_use_forest[ha]', 'agr_land-man_use_cropland[ha]',
                    'agr_land-man_use_grassland[ha]', 'agr_land-man_use_wetland[ha]', 'agr_land-man_use_settlement[ha]',
                    'agr_land-man_use_other[ha]', 'initial area', 'timescale']

# Assign the new column names to the DataFrame
df_land_use.columns = new_column_names

# Dropping the columns 'element' and 'initial area'
df_land_use = df_land_use.drop(columns=['element', 'initial area'])
df_land_use_filtered = df_land_use.drop(columns=['agr_land-man_use_cropland[ha]', 'agr_land-man_use_grassland[ha]'])

# Melting the dfs to have the relevant format (geoscale, year, value)
df_land_use_pathwaycalc = pd.melt(df_land_use_filtered, id_vars=['timescale'], var_name='variables', value_name='value')

# Convert the 'value' column from string to numeric
df_land_use_pathwaycalc['value'] = pd.to_numeric(df_land_use_pathwaycalc['value'], errors='coerce')

# Unit conversion [kha] => [ha]
df_land_use_pathwaycalc['value'] = df_land_use_pathwaycalc['value'] * 1000

# PathwayCalc formatting -----------------------------------------------------------------------------------------------
# Adding the columns module, lever, level and string-pivot at the correct places
df_land_use_pathwaycalc['module'] = 'land-use'
df_land_use_pathwaycalc['lever'] = 'land-man'
df_land_use_pathwaycalc['level'] = 0
df_land_use_pathwaycalc['geoscale'] = 'Switzerland'
cols = df_land_use_pathwaycalc.columns.tolist()
cols.insert(cols.index('value'), cols.pop(cols.index('module')))
cols.insert(cols.index('value'), cols.pop(cols.index('lever')))
cols.insert(cols.index('value'), cols.pop(cols.index('level')))
cols.insert(cols.index('timescale'), cols.pop(cols.index('geoscale')))
df_land_use_pathwaycalc = df_land_use_pathwaycalc[cols]

# ----------------------------------------------------------------------------------------------------------------------
# LAND DYN -------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# 1 for forest, 0 for grassland and unmanaged for all ots

# Using csf_managed as a structural basis
df_land_dyn_forest = csf_managed.copy()
df_land_dyn_grass = csf_managed.copy()
df_land_dyn_unmanaged = csf_managed.copy()

# Changing values and variable name
df_land_dyn_forest['variables'] = 'agr_land-man_dyn_forest[%]'
df_land_dyn_forest['value'] = 1
df_land_dyn_grass['variables'] = 'agr_land-man_dyn_grassland[%]'
df_land_dyn_grass['value'] = 0
df_land_dyn_unmanaged['variables'] = 'agr_land-man_dyn_unmanaged[%]'
df_land_dyn_unmanaged['value'] = 0

# Concatenating
df_land_dyn = pd.concat([df_land_dyn_forest, df_land_dyn_grass])
df_land_dyn = pd.concat([df_land_dyn, df_land_dyn_unmanaged])

# PathwayCalc formatting
df_land_dyn['lever'] = 'land-man'

# ----------------------------------------------------------------------------------------------------------------------
# LAND GAP -------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# Difference in values between FAO and UNFCCC

# Read FAO Values (for Switzerland) --------------------------------------------------------------------------------------------
# List of countries
list_countries = ['Switzerland']

# List of elements
list_elements = ['Area']

list_items = ['-- Cropland', '-- Permanent meadows and pastures', 'Forest land']

# 1990 - 2022
ld = faostat.list_datasets()
code = 'RL'
pars = faostat.list_pars(code)
my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
              '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
              '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

my_pars = {
    'area': my_countries,
    'element': my_elements,
    'item': my_items,
    'year': my_years
}
df_land_use_fao = faostat.get_data_df(code, pars=my_pars, strval=False)

# Drop columns
df_land_use_fao = df_land_use_fao.drop(
    columns=['Domain Code', 'Domain', 'Area Code', 'Element Code',
             'Item Code', 'Year Code', 'Unit', 'Element', 'Area'])

# Reshape
df = df_land_use_fao.copy()
# Reshape the DataFrame using pivot
reshaped_df = df.pivot(index='Year', columns='Item', values='Value')
# Reset the index if you want a flat DataFrame with 'item' as a column
reshaped_df = reshaped_df.reset_index()

# Read UNFCCC values (for Switzerland)
# done in previous steps, result is df_land_use

# Merged based on timescale
df_land_gap = pd.merge(reshaped_df, df_land_use, left_on='Year', right_on='timescale')

# Change type to numeric
numeric_cols = df_land_gap.columns[1:]  # Get all columns except the first three
df_land_gap[numeric_cols] = df_land_gap[numeric_cols].apply(pd.to_numeric,
                                                          errors='coerce')

# Computing the difference
df_land_gap['agr_land-man_gap_cropland[ha]'] = df_land_gap['agr_land-man_use_cropland[ha]'] - df_land_gap['Cropland']
df_land_gap['agr_land-man_gap_forest[ha]'] = df_land_gap['agr_land-man_use_forest[ha]'] - df_land_gap['Forest land']
df_land_gap['agr_land-man_gap_grassland[ha]'] = df_land_gap['agr_land-man_use_grassland[ha]'] - df_land_gap['Permanent meadows and pastures']
#df_land_gap['agr_land-man_gap_other[ha]'] = df_land_gap[''] - df_land_gap['']
#df_land_gap['agr_land-man_gap_settlement[ha]'] = df_land_gap[''] - df_land_gap['']
#df_land_gap['agr_land-man_gap_wetland[ha]'] = df_land_gap[''] - df_land_gap['']

# Keep only the useful columns
df_land_gap = df_land_gap[['timescale', 'agr_land-man_gap_cropland[ha]', 'agr_land-man_gap_forest[ha]',
                                         'agr_land-man_gap_grassland[ha]']]

# Melt the df


# Unit conversion [kha] => [ha]

# PathwayCalc formatting

# ----------------------------------------------------------------------------------------------------------------------
# FINAL RESULTS --------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# Concatenating all dfs


# CalculationLeaf BIOMASS HIERARCHY ------------------------------------------------------------------------------------

# Common for all
# List of countries
list_countries = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark',
                  'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia',
                  'Lithuania', 'Luxembourg', 'Malta', 'Netherlands (Kingdom of the)', 'Poland', 'Portugal',
                  'Romania', 'Slovakia',
                  'Slovenia', 'Spain', 'Sweden', 'Switzerland',
                  'United Kingdom of Great Britain and Northern Ireland']

list_test = ['Switzerland']

# ----------------------------------------------------------------------------------------------------------------------
# BIOMASS MIX ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# API EUROSTAT (DOES NOT CORK FOR CH)
#code_eurostat = 'nrg_cb_rw'
#list_test = ['LI']
#list_countries_eurostat = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE',
#                           'EL', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT',
#                           'RO', 'SK', 'SI', 'ES', 'SE', 'UK']
#my_filter_pars = {'startPeriod': 1990,'endPeriod': 2022, 'geo': list_test}
#data = eurostat.get_data_df(code_eurostat, filter_pars=my_filter_pars)


# Drop the irrelevant columns


list_elements = ['Energy production']

list_items = ['Total Bioenergy > (List)']

# 1990 - 2022
code = 'BE'
my_countries = [faostat.get_par(code, 'area')[c] for c in list_countries]
my_elements = [faostat.get_par(code, 'elements')[e] for e in list_elements]
my_items = [faostat.get_par(code, 'item')[i] for i in list_items]
list_years = ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
              '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
              '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
my_years = [faostat.get_par(code, 'year')[y] for y in list_years]

my_pars = {
    'area': my_countries,
    'element': my_elements,
    'item': my_items,
    'year': my_years
}
df_bioenergy_mix_1990_2022 = faostat.get_data_df(code, pars=my_pars, strval=False)

# ----------------------------------------------------------------------------------------------------------------------
# INTERACTIONS CONSTANTS
# ----------------------------------------------------------------------------------------------------------------------

# Goal is to add the add the constants from the agriculture module to the interactions_constants file common
# to all modules

# Read csv
constants_agr = pd.read_csv('/Users/crosnier/Documents/PathwayCalc/_database/data/csv/interactions_constants_pathwaycalc.csv', sep=';')
constants_all = pd.read_csv('/Users/crosnier/Documents/PathwayCalc/_database/data/csv/interactions_constants_back-up.csv', sep=';')

# Identify the columns to check for duplicates
common_columns = constants_all.columns.tolist()

# Filter out rows in df2 that are already in df1 based on common columns
constants_agr_unique = constants_agr[~constants_agr.apply(tuple, axis=1).isin(constants_all.apply(tuple, axis=1))]

# Concatenate df1 with the filtered df2
result = pd.concat([constants_all, constants_agr_unique])

# Export to csv
#result.to_csv('interactions_constants_30-07.csv', index=False, sep=';')




years_setting = [1990, 2022, 2050, 5]
startyear = years_setting[0]
baseyear = years_setting[1]
lastyear = years_setting[2]
step_fts = years_setting[3]
years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int))
years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int))
years_all = years_ots + years_fts
#num_cat = 33

#dict_ots, dict_fts = database_to_dm(df_ssr_pathwaycalc, 'food-net-import', num_cat, baseyear, years_all, level='all')


print('Hello')


