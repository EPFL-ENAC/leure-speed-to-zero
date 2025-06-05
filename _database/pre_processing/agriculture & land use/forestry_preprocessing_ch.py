import pandas as pd
import numpy as np
from _database.pre_processing.api_routines_CH import get_data_api_CH
import pickle
import os
import requests
import deepl
import faostat
from model.common.data_matrix_class import DataMatrix
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.auxiliary_functions import create_years_list, linear_fitting, my_pickle_dump

# Initialize the Deepl Translator
deepl_api_key = '9ecffb3f-5386-4254-a099-8bfc47167661:fx'
translator = deepl.Translator(deepl_api_key)

def translate_text(text):
    if isinstance(text, str):
        translation = translator.translate_text(text, target_lang='EN-GB')
        out = translation.text
    else:
        out = text
    return out

##########################################################################################################
# Download of files from URL
##########################################################################################################
def save_url_to_file(file_url, local_filename):
    # Loop for URL
    if not os.path.exists(local_filename):
        response = requests.get(file_url, stream=True)
        # Check if the request was successful
        if response.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"File downloaded successfully as {local_filename}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    else:
        print(f'File {local_filename} already exists. If you want to download again delete the file')

    return

##########################################################################################################
# Wood production in CH and Cantons
##########################################################################################################
def get_wood_production(table_id, file):
    try:
        # Try to look for the pickle
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)

    # No pickle available
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example')

        filtering = {'Year': structure['Year'],
                     'Forest zone': ['Switzerland'],
                     'Canton': ['Switzerland', 'Vaud'],
                     'Type of owner': ['Type of owners - total'],
                     'Wood species': structure['Wood species'],
                     'Observation unit': structure['Observation unit']}

        mapping_dim = {'Country': 'Canton',
                       'Years': 'Year',
                       'Variables': 'Observation unit',
                       'Categories1': 'Wood species'}

        # Extract new fleet
        dm = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                   units=['m3'] * len(structure['Observation unit']))
        dm.sort('Years')

        #Write the pickle
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm

##########################################################################################################
# Wood production in CH and Cantons
##########################################################################################################

def get_wood_energy_by_sector(file_url, local_filename):
    ### Creates the file
    save_url_to_file(file_url, local_filename)
    ### Read the file
    df = pd.read_excel(local_filename, sheet_name='M')
    #filter lines
    df = df.iloc[0:9]
    #filter column:
    df = df.drop(df.columns[0], axis=1)

    # header change
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    # Nan remove
    df = df.dropna(how='all')
    df.columns = [str(int(col)) if isinstance(col, float) else str(col) for col in df.columns]
    ### translate
    new_names=['Years']
    for i in range(1):
        # Use deepl to translate variables from de to en
        variables_de = list(set(df[df.columns[i]]))
        variables_en = [translate_text(var) for var in variables_de]
        var_dict = dict(zip(variables_de, variables_en))
        df[new_names[i]] = df[df.columns[i]].map(var_dict)

    df.drop([df.columns[0]], axis=1, inplace=True)

    # change the column position
    df = df[[df.columns[-1]] + list(df.columns[:-1])]

    ##Transpose
    #df = df.T
    df = df.T
    df = df.reset_index()
    df = df.rename(columns={'index': 'year'})
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    #Country
    df.insert(0, "Country", "Switzerland")

    # New names
    df = df.rename(columns={
        'Households': 'fst_wood-energy-demand_households[TJ]',
        'Agriculture / Forestry': 'fst_wood-energy-demand_agriculture-forestry[TJ]',
        'District heating':'fst_wood-energy-demand_district-heating[TJ]',
        'services': 'fst_wood-energy-demand_services[TJ]',
        'Industry / Trade':'fst_wood-energy-demand_industry[TJ]',
        'All system categories (Cat. 1 - 20)':'fst_wood-energy-demand_total[TJ]',
        'Electricity':'fst_wood-energy-demand_electricity[TJ]'
    })
    # Convert to DM
    dm_wood_demand_energy = DataMatrix.create_from_df(df, num_cat=1)

    # Conversion from TJ to GWh:
    dm_wood_demand_energy.change_unit('fst_wood-energy-demand', factor=0.27778, old_unit='TJ', new_unit='GWh')
    #dm_wood_demand_energy.datamatrix_plot()
    return dm_wood_demand_energy

##########################################################################################################
# Wood consumption in CH and Cantons
##########################################################################################################

def get_wood_energy_by_use(file_url, local_filename):
    ### Creates the file
    save_url_to_file(file_url, local_filename)
    ### Read the file
    df_raw = pd.read_excel(local_filename, sheet_name='R')

    # Filtering the matrix for wood use in m3 (TJ to follow)
    df = df_raw
    df = df.iloc[0:11]

    # header change
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    # Nan remove
    df = df.dropna(how='all')
    df.columns = [str(int(col)) if isinstance(col, float) else str(col) for col in df.columns]
    ### translate
    new_names=['Years']
    for i in range(1):
        # Use deepl to translate variables from de to en
        variables_de = list(set(df[df.columns[i]]))
        variables_en = [translate_text(var) for var in variables_de]
        var_dict = dict(zip(variables_de, variables_en))
        df[new_names[i]] = df[df.columns[i]].map(var_dict)

    df.drop([df.columns[0]], axis=1, inplace=True)

    # change the column position
    df = df[[df.columns[-1]] + list(df.columns[:-1])]

    ##Transpose
    #df = df.T
    df = df.T
    df = df.reset_index()
    df = df.rename(columns={'index': 'year'})
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    #Country
    df.insert(0, "Country", "Switzerland")

    # New names
    df = df.rename(columns={
        'Total incl. KVA (Cat 1-20)': 'fst_wood-energy-use_total[m3]',
        'Waste wood without MSWI (without cat. 20)': 'fst_wood-energy-use_waste-without-incineration[m3]',
        'Waste wood in MSWI (only cat. 20)':'fst_wood-energy-use_waste-incineration[m3]',
        'Residual wood from wood processing plants': 'fst_wood-energy-use_wood-byproducts[m3]',
        'Wood pellets *)':'fst_wood-energy-use_pellets[m3]',
        'Natural logs':'fst_wood-energy-use_natural-logs[m3]',
        'Natural non-chunky wood':'fst_wood-energy-use_natural-non-chunky-wood[m3]',
        'Total without KVA (Cat 1-19)': 'fst_wood-energy-use_total-without-incineration[m3]'
    })
    # Convert to DM
    dm_wood_energy_use_m3 = DataMatrix.create_from_df(df, num_cat=1)

    # Filtering the matrix for wood use in TJ
    df = df_raw
    df = df.iloc[14:25]

    # header change
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    # Nan remove
    df = df.dropna(how='all')
    df.columns = [str(int(col)) if isinstance(col, float) else str(col) for col in df.columns]
    ### translate
    new_names = ['Years']
    for i in range(1):
        # Use deepl to translate variables from de to en
        variables_de = list(set(df[df.columns[i]]))
        variables_en = [translate_text(var) for var in variables_de]
        var_dict = dict(zip(variables_de, variables_en))
        df[new_names[i]] = df[df.columns[i]].map(var_dict)

    df.drop([df.columns[0]], axis=1, inplace=True)

    # change the column position
    df = df[[df.columns[-1]] + list(df.columns[:-1])]

    ##Transpose
    # df = df.T
    df = df.T
    df = df.reset_index()
    df = df.rename(columns={'index': 'year'})
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    # Country
    df.insert(0, "Country", "Switzerland")

    # New names
    df = df.rename(columns={
        'Total incl. KVA (Cat 1-20)': 'fst_wood-energy-use_total[TJ]',
        'Waste wood without MSWI (without cat. 20)': 'fst_wood-energy-use_waste-without-incineration[TJ]',
        'Waste wood in MSWI (only cat. 20)': 'fst_wood-energy-use_waste-incineration[TJ]',
        'Residual wood from wood processing plants': 'fst_wood-energy-use_wood-byproducts[TJ]',
        'Wood pellets *)': 'fst_wood-energy-use_pellets[TJ]',
        'Natural logs': 'fst_wood-energy-use_natural-logs[TJ]',
        'Natural non-chunky wood': 'fst_wood-energy-use_natural-non-chunky-wood[TJ]',
        'Total without KVA (Cat 1-19)': 'fst_wood-energy-use_total-without-incineration[TJ]'
    })
    # Convert to DM
    dm_wood_energy_use_gwh = DataMatrix.create_from_df(df, num_cat=1)

    # Conversion from TJ to GWh:
    dm_wood_energy_use_gwh.change_unit('fst_wood-energy-use', factor=0.27778, old_unit='TJ', new_unit='GWh')
    dm_wood_energy_use_gwh.rename_col("fst_wood-energy-use","fst_wood-energy-use-gwh","Variables")
    dm_wood_energy_use_m3.rename_col("fst_wood-energy-use", "fst_wood-energy-use-m3", "Variables")
    #dm_wood_demand_energy.datamatrix_plot()

    dm_wood_energy_use=dm_wood_energy_use_gwh
    dm_wood_energy_use.append(dm_wood_energy_use_m3, dim='Variables')
    dm_wood_energy_use.operation('fst_wood-energy-use-gwh', '/', 'fst_wood-energy-use-m3', out_col='fst_energy-density', unit='gwh/m3')
    dm_wood_energy_use.datamatrix_plot({'Variables': ['fst_energy-density']})

    return dm_wood_energy_use

##########################################################################################################
# Wood production in CH and Cantons
##########################################################################################################
def get_forest_area(table_id, file):
    try:
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example')

        filtering = {'Year': structure['Year'],
                     'Forest zone': ['Switzerland'],
                     'Canton': ['Switzerland', 'Vaud'],
                     'Type of owner':['Type of owners - total'],
                     'Observation unit':['Total forest area', 'Productive forest area']}

        mapping_dim = {'Country': 'Canton',
                       'Years': 'Year',
                       'Variables': 'Observation unit',
                       'Categories1': 'Type of owner'}

        # Extract new fleet
        dm = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                   units=['ha'] * len(structure['Observation unit']))
        dm= dm.flatten()
        df = dm.write_df()
        dm.sort('Years')

        with open(file, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm

def get_wood_trade_balance(file):
    try:
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
    except OSError:
        # My PARSE -------------------------------------------------
        code = 'FO'

        # Metadata
        list_data = faostat.list_datasets()
        list_data
        list_items = faostat.get_par(code, 'items')
        list_items
        list_itemsagg = faostat.get_par(code, 'itemsagg')
        list_itemsagg
        list_area = faostat.get_par(code, 'area')
        list_area
        list_pars = faostat.list_pars(code)
        list_pars

        # My selection
        areas = ['Switzerland']
        years = [str(y) for y in range(1990, 2024)]
        elements = ['Export quantity','Import quantity','Production Quantity']
        itemsagg = ['Roundwood + (Total)','Roundwood > (List)',
                    'Roundwood, coniferous > (List)',
                    'Roundwood, non-coniferous > (List)']

        my_areas = [faostat.get_par(code, 'area')[c] for c in areas]
        my_elements = [faostat.get_par(code, 'elements')[e] for e in elements]
        my_itemsagg = [faostat.get_par(code, 'itemsagg')[i] for i in itemsagg]
        my_years = [faostat.get_par(code, 'year')[y] for y in years]

        my_pars = {
            'area': my_areas,
            'element': my_elements,
            'year':my_years,
            'itemsagg':my_itemsagg
        }
        dm = faostat.get_data_df(code, pars=my_pars, strval=False)

        # Filter out FAOSTAT columns
        dm = dm[['Area', 'Year', 'Value', 'Element', 'Item', 'Unit']]

        # Shaping to turn into DM
        dm = dm.rename(columns={'Year': 'Years', 'Area': 'Country'})

        dm['Variable'] = dm.apply(
            lambda row: f"{row['Item'].lower()}_{row['Element'].lower()}[{row['Unit'].lower()}]", axis=1)
        dm = dm.drop(columns=['Item', 'Element', 'Unit'])
        dm = dm.pivot(index=['Country', 'Years'], columns='Variable', values='Value').reset_index()
        dm = DataMatrix.create_from_df(dm, num_cat=1)
        dm = dm.filter_w_regex({'Variables': 'industrial roundwood|industrial roundwood, coniferous|industrial roundwood, non-coniferous|\
        other industrial roundwood|pulp for paper|\
        roundwood|roundwood, coniferous|roundwood, non-coniferous|\
        sawlogs and veneer logs|sawlogs and veneer logs, coniferous|\
        sawlogs and veneer logs, non-coniferous|\
        wood fuel|wood fuel, coniferous|wood fuel, non-coniferous'})

        with open(file, 'wb') as handle:
            pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dm

################################################################
# Simulate Industry Interface as a Pickle
################################################################
def simulate_industry_input(write_pickle= True):
    if write_pickle is True:
        # Path for the input from industry
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, "../../data/xls/fake_ind-to-fst.xlsx")
        # Read the file:
        df = pd.read_excel(f, sheet_name="ind-to-fst")
        # Build DataMatrix
        dm = DataMatrix.create_from_df(df, num_cat=1)
        DM_industry_to_forestry = dm
        # Write Pickle
        f = os.path.join(current_file_directory, '../../data/interface/industry_to_forestry.pickle')
        my_pickle_dump(DM_new=DM_industry_to_forestry, local_pickle_file=f)

    return

simulate_industry_input()

######################################################################
######################################################################
# DATA
######################################################################
######################################################################
years_ots = create_years_list(1990, 2023, 1)
years_fts = create_years_list(2025, 2050, 5)

################################################################
# Trade Wood - FAOSTAT (Switzerland)
################################################################

file = 'data/forestry-trade.pickle'
dm = get_wood_trade_balance(file)
dm_roundwood_export = dm.filter_w_regex({'Variables':'roundwood'})
dm_roundwood_export = dm.filter_w_regex({'Categories1':'export quantity'})
df = dm_roundwood_export.write_df()
#dm_roundwood_export.datamatrix_plot({'Categories1': ['export quantity']})

################################################################
# Calibration: Energy demand per sector (Switzerland)
################################################################

file_url = 'https://www.bfe.admin.ch/bfe/en/home/versorgung/statistik-und-geodaten/energiestatistiken/teilstatistiken.exturl.html/aHR0cHM6Ly9wdWJkYi5iZmUuYWRtaW4uY2gvZGUvcHVibGljYX/Rpb24vZG93bmxvYWQvMTE0NDA=.html'
local_filename = 'data/Swiss-wood-energy-statistics.xlsx'
dm_wood_energy_calibration = get_wood_energy_by_sector(file_url, local_filename)

################################################################
# Wood production in CH and Cantons
################################################################

# Create the data matrix out of the SwissSTAT Tab
file = "data/wood_production_ch.pickle"
table_id = "px-x-0703010000_102"
dm = get_wood_production(table_id, file)

# Renaming
dm.rename_col(
    ['Wood harvest - total', ' Sawlogs and veneer logs',' Industrial roundwood',' Wood fuel - total',' >> Chopped wood',' >> Wood chips',' Other types of wood'],
    ['total', 'sawlogs','industrial-wood','woodfuel','chopped-wood','wood-chips','any-other-wood'],
    dim='Variables')

dm.rename_col(
    ['Species - total', 'Softwood (conifers)', 'Hardwood (deciduous)'],
    ['overall','coniferous','non-coniferous'],
    dim='Categories1')

# Merge the category to match FAOSTAT classification

# Filter out the column that we do not use
dm.drop(dim='Variables', col_label='chopped-wood|wood-chips')
dm.drop(dim='Categories1', col_label='overall')

#dm.datamatrix_plot()

# Compute coniferous, non-coniferous share

dm.normalise('Categories1',  keep_original=True)
dm_wood_production=dm
dm_wood_type = dm.filter_w_regex({'Variables': '.*_share'})

#checks
df = dm.write_df()
#dm.datamatrix_plot({'Variables': 'total_share'}, stacked=True)
#dm.datamatrix_plot()

################################################################
# Forest area per Canton
################################################################

# Create the data matrix out of the SwissSTAT Tab
file = "data/forest_area_ch.pickle"
table_id = "px-x-0703010000_101"
dm = get_forest_area(table_id, file)

# Renaming
dm.rename_col(
    ['Total forest area_Type of owners - total', 'Productive forest area_Type of owners - total'],
    ['total-forest-area', 'productive-forest-area'],
    dim='Variables')

dm.operation('productive-forest-area', '/', 'total-forest-area', out_col='productive-share', unit='%')
dm.operation('total-forest-area', '-', 'productive-forest-area', out_col='unproductive-forest-area', unit='ha')
dm.operation('unproductive-forest-area', '/', 'total-forest-area', out_col='unproductive-share', unit='%')

dm_forest_area=dm
#dm_forest_area.datamatrix_plot()
#dm_forest_area.datamatrix_plot({'Variables': ['productive-share','unproductive-share']}, stacked=True)

################################################################
# Harvest rate
################################################################

ay_harvest_rate = dm_wood_production[:, :, 'total', :] \
                             / dm_forest_area[:, :,'productive-forest-area', np.newaxis]
dm_wood_production.add(ay_harvest_rate,col_label='harvest-rate',dim='Variables',unit='m3/ha')

#dm_wood_production.datamatrix_plot({'Variables': ['harvest-rate']})

#dm_forest_area.datamatrix_plot()

################################################################
# FXA: Wood fuel demand per use (Switzerland)
################################################################

file_url = 'https://www.bfe.admin.ch/bfe/en/home/versorgung/statistik-und-geodaten/energiestatistiken/teilstatistiken.exturl.html/aHR0cHM6Ly9wdWJkYi5iZmUuYWRtaW4uY2gvZGUvcHVibGljYX/Rpb24vZG93bmxvYWQvMTE0NDA=.html'
local_filename = 'data/Swiss-wood-energy-statistics.xlsx'
dm_wood_energy_use = get_wood_energy_by_use(file_url, local_filename)

################################################################
# DM pre-processing Forestry
################################################################

DM_preprocessing_forestry = {'calibration': dm_wood_energy_calibration,
                             'production': dm_wood_production,
                             'wood-energy-use': dm_wood_energy_use,
                             'forest-area': dm_forest_area,
                             'wood-trade':dm_roundwood_export}

DM_preprocessing_forestry

################################################################
################################################################
# Constants
################################################################
################################################################

################################################################
# Constants - Wood density
################################################################

forestry_wood_density = {'pulp-to-softwood': 1.4,
                         'pulp-to-hardwood': 1.25,
                         'timber-to-softwood': 1.82,
                         'timber-to-hardwood': 1.43,
                         'industrial-to-softwood': 1.43,
                         'industrial-to-hardwood': 1.25,
                         'woodfuel-to-softwood': 1.43,
                         'woodfuel-to-hardwood': 1.25,
                         }
cdm_wood_density = ConstantDataMatrix(col_labels={'Variables': ['fst_wood-density'],
                                              'Categories1': ['pulp-to-softwood',
                                                              'pulp-to-hardwood',
                                                              'timber-to-softwood',
                                                              'timber-to-hardwood',
                                                              'industrial-to-softwood',
                                                              'industrial-to-hardwood',
                                                              'woodfuel-to-softwood',
                                                              'woodfuel-to-hardwood']},
                                  units={'fst_wood-density': 'm3/t'})

cdm_wood_density.array = np.zeros((len(cdm_wood_density.col_labels['Variables']),
                                    len(cdm_wood_density.col_labels['Categories1'])))
idx = cdm_wood_density.idx
for key, value in forestry_wood_density.items():
    cdm_wood_density.array[0, idx[key]] = value

cdm_wood_density.sort('Categories1')

################################################################
# Constants - Wood energy density
################################################################

forestry_energy_density = {'woodfuel-average': 0.002326,
                         'woodfuel-hardwood': 0.0026749,
                         'woodfuel-softwood': 0.00250045
                         }
cdm_energy_density = ConstantDataMatrix(col_labels={'Variables': ['fst_energy-density'],
                                                    'Categories1': ['woodfuel-average',
                                                                    'woodfuel-hardwood',
                                                                    'woodfuel-softwood']},
                                        units={'fst_energy-density': 'GWh/m3'})

cdm_energy_density.array = np.zeros((len(cdm_energy_density.col_labels['Variables']),
                                    len(cdm_energy_density.col_labels['Categories1'])))
idx = cdm_energy_density.idx
for key, value in forestry_energy_density.items():
    cdm_energy_density.array[0, idx[key]] = value

cdm_energy_density.sort('Categories1')

################################################################
# Constants - Wood energy density
################################################################

forestry_industry_loop = {'wood-fuel-byproducts': 0.002326}

cdm_industry_loop = ConstantDataMatrix(col_labels={'Variables': ['fst_industry-byproducts'],
                                                    'Categories1': ['wood-fuel-byproducts']},
                                        units={'fst_industry-byproducts': '%'})

cdm_industry_loop.array = np.zeros((len(cdm_industry_loop.col_labels['Variables']),
                                    len(cdm_industry_loop.col_labels['Categories1'])))
idx = cdm_industry_loop.idx
for key, value in forestry_industry_loop.items():
    cdm_energy_density.array[0, idx[key]] = value

cdm_energy_density.sort('Categories1')

################################################################
# Missing Values - Wood type share - Any other industrial wood
################################################################

linear_fitting(dm_wood_type,dm_wood_type.col_labels['Years'],based_on=create_years_list(2004,2023,1))

################################################################
# FXA - Wood type
################################################################

# Extract OTS & Add FTS
dm_wood_type.filter({'Years': years_ots}, inplace=True)
dm_wood_type.add(np.nan, col_label=years_fts, dim='Years', dummy=True)
# Linear extrapolation on future years
linear_fitting(dm_wood_type, years_fts)

################################################################
# Create fts example
################################################################

# Extract harvest-rate
dm_harvest = dm_wood_production.filter({'Variables': ['harvest-rate']})
dm_harvest.filter({'Years': years_ots}, inplace=True)
dm_harvest_clean = dm_harvest.copy()
# Remove anomalies for extrapolation
dm_harvest_clean[:, 2000, ...] = np.nan
dm_harvest_clean[:, 1990, ...] = np.nan
dm_harvest_clean.add(np.nan, col_label=years_fts, dim='Years', dummy=True)
# Linear extrapolation on future years
linear_fitting(dm_harvest_clean, years_fts)
#dm_harvest_clean.array = np.maximum(1, dm_harvest_clean.array)  # Example if you want to have at least 1 as harvest-rate
# Keep only fts years
dm_harvest_clean.filter({'Years': years_fts}, inplace=True)
# Append to original data
dm_harvest.append(dm_harvest_clean, dim='Years')



################################################################
# Pickle for Forestry
################################################################

DM_forestry = {'ots': dict(), 'fts': dict(), 'fxa': dict(), 'constant': dict()}
DM_forestry['constant']['energy-density'] = cdm_energy_density
DM_forestry['constant']['wood-density'] = cdm_wood_density
DM_forestry['constant']['industry-byproducts'] = cdm_industry_loop
DM_forestry['fxa']['coniferous-share'] = dm_wood_type
DM_forestry

### Final DM is ots:, fts:, fxa:, (keys of ots must be lever name)

DM_forestry['ots']['harvest-rate'] = dm_harvest.filter({'Years': years_ots})
DM_forestry['fts']['harvest-rate'] = dict()
for lev in range(4):
    DM_forestry['fts']['harvest-rate'][lev+1] = dm_harvest.filter({'Years': years_fts})

# Fake Industry to Forestry interface

# save

f = '../../data/datamatrix/forestry.pickle'
with open(f, 'wb') as handle:
    pickle.dump(DM_forestry, handle, protocol=pickle.HIGHEST_PROTOCOL)
