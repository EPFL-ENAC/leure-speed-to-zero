import dm as dm
import pandas as pd
import numpy as np
from _database.pre_processing.api_routines_CH import get_data_api_CH
import pickle
import os
import requests
import deepl
from model.common.data_matrix_class import DataMatrix

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
        with open(file, 'rb') as handle:
            dm = pickle.load(handle)
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

######################################################################
######################################################################
# DATA
######################################################################
######################################################################

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
    ['Softwood (conifers)', 'Hardwood (deciduous)'],
    ['coniferous','non-coniferous'],
    dim='Categories1')

# Merge the category to match FAOSTAT classification
dm.groupby( {'industrial-wood': ['industrial-wood','sawlogs']}, dim='Variables', inplace=True)

# Filter out the column that we do not use
dm.drop(dim='Variables', col_label='chopped-wood|wood-chips')
dm.drop(dim='Categories1', col_label='Species - total')

#dm.datamatrix_plot()

# Compute coniferous, non-coniferous share
dm.normalise('Categories1',  keep_original=True)
dm_wood_production=dm

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
dm_forest_area.datamatrix_plot({'Variables': ['productive-share','unproductive-share']}, stacked=True)

################################################################
# Harvest rate
################################################################

ay_harvest_rate = dm_wood_production.array[:, :, 'productive-forest-area', :] \
                             / dm_forest_area[:, :, 'total', np.newaxis]

dm_forest_area.datamatrix_plot()