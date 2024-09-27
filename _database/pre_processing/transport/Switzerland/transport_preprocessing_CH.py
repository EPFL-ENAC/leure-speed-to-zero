import numpy as np
import pandas as pd
import numpy as np
from _database.pre_processing.api_routines_CH import get_data_api_CH
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import create_years_list, linear_fitting, add_missing_ots_years, moving_average
import pickle
import os
import requests


def compute_passenger_new_fleet(table_id_new_veh, file_new_veh_ots1, file_new_veh_ots2):

    #### New fleet Switzerland + Vaud: 2005 - now
    def get_new_fleet_by_tech_raw(table_id, file):
        # New fleet data are heavy, download them only once
        try:
            with open(file, 'rb') as handle:
                dm_new_fleet = pickle.load(handle)
        except OSError:
            structure, title = get_data_api_CH(table_id, mode='example')
            i = 0
            for month in structure['Month']:
                i = i + 1
                filtering = {'Year': structure['Year'],
                          'Month': [month],
                          'Vehicle group / type': structure['Vehicle group / type'],
                          'Canton': ['Switzerland', 'Vaud'],
                          'Fuel': structure['Fuel']}

                mapping_dim = {'Country': 'Canton',
                               'Years': 'Year',
                               'Variables': 'Month',
                               'Categories1': 'Vehicle group / type',
                               'Categories2': 'Fuel'}

                # Extract new fleet
                dm_new_fleet_month = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                                    units=['number'])
                if dm_new_fleet_month is None:
                    raise ValueError(f'API returned None for {month}')
                if i == 1:
                    dm_new_fleet = dm_new_fleet_month.copy()
                else:
                    dm_new_fleet.append(dm_new_fleet_month, dim='Variables')

                current_file_directory = os.path.dirname(os.path.abspath(__file__))
                f = os.path.join(current_file_directory, file)
                with open(f, 'wb') as handle:
                    pickle.dump(dm_new_fleet, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return dm_new_fleet


    ### Passenger new fleet Switzerland + Vaud: 2005 - new
    def extract_passenger_new_fleet_by_tech(dm_new_fleet):
        # Sum all months
        dm_new_fleet.groupby({'tra_passenger_new-vehicles': '.*'}, dim='Variables', regex=True, inplace=True)

        # Keep only passenger car main categories
        main_cat = [cat for cat in dm_new_fleet.col_labels['Categories1'] if '>' in cat]
        passenger_cat = [cat for cat in main_cat if 'Passenger' in cat or 'Motorcycles' in cat]

        # Filter for Passenger vehicles
        dm_pass_new_fleet = dm_new_fleet.filter({'Categories1': passenger_cat}, inplace=False)
        dm_pass_new_fleet.groupby({'LDV': '.*Passenger.*'}, dim='Categories1', regex=True, inplace=True)
        dm_pass_new_fleet.groupby({'2W': '.*Motorcycles.*'}, dim='Categories1', regex=True, inplace=True)

        # Filter new technologies
        # (this is needed to later allocate the vehicle fleet "Other" category to the new technologies)
        new_technologies = ['Hydrogen', 'Diesel-electricity: conventional hybrid',
                            'Petrol-electricity: conventional hybrid',
                            'Petrol-electricity: plug-in hybrid', 'Diesel-electricity: plug-in hybrid',
                            'Gas (monovalent and bivalent)']
        dm_new_tech = dm_pass_new_fleet.filter({'Categories2': new_technologies})

        # Map fuel technology to transport module category
        dict_tech = {'FCEV': ['Hydrogen'], 'BEV': ['Electricity'],
                     'ICE-diesel': ['Diesel', 'Diesel-electricity: conventional hybrid'],
                     'ICE-gasoline': ['Petrol', 'Petrol-electricity: conventional hybrid'],
                     'PHEV-diesel': ['Diesel-electricity: plug-in hybrid'],
                     'PHEV-gesoline': ['Petrol-electricity: plug-in hybrid'],
                     'ICE-gas': ['Gas (monovalent and bivalent)']}
        dm_pass_new_fleet.groupby(dict_tech, dim='Categories2', regex=False, inplace=True)
        dm_pass_new_fleet.drop(col_label='Without motor', dim='Categories2')
        # Check that other categories are only a small contribution
        dm_tmp = dm_pass_new_fleet.normalise(dim='Categories2', inplace=False)
        dm_tmp.filter({'Categories2': ['Other']}, inplace=True)
        # If Other and Without motor are more than 0.1% you should account for it
        if (dm_tmp.array > 0.01).any():
            raise ValueError('"Other" category is greater than 1% of the fleet, it cannot be discarded')

        dm_pass_new_fleet.drop(col_label='Other', dim='Categories2')


        return dm_pass_new_fleet, dm_new_tech


    ### New fleet Switzerland: 1990 - now
    # New registration of road model vehicles
    # download csv file FSO number gr-e-11.03.02.02.01a
    # https://www.bfs.admin.ch/asset/en/30305446
    def get_new_fleet(file, first_year):
        df = pd.read_csv(file)
        for col in df.columns:
            df.rename(columns={col: col + '[number]'}, inplace=True)
        df.rename(columns={'X.1[number]': 'Years'}, inplace=True)
        df['Country'] = 'Switzerland'
        dm_new_fleet_CH = DataMatrix.create_from_df(df, num_cat=0)
        dm_pass_new_fleet_CH = dm_new_fleet_CH.groupby({'tra_passenger_new-vehicles_LDV': 'passenger.*',
                                                        'tra_passenger_new-vehicles_2W': 'motorcycles'},
                                                       dim='Variables', regex=True, inplace=False)
        dm_pass_new_fleet_CH.deepen()

        # Keep only years before 2005
        old_yrs_series = [yr for yr in dm_pass_new_fleet_CH.col_labels['Years'] if yr < first_year]
        dm_pass_new_fleet_CH.filter({'Years': old_yrs_series}, inplace=True)

        return dm_pass_new_fleet_CH


    ### Add new fleet Vaud 1990 - 2004
    def compute_new_fleet_vaud(dm_CH, dm_tech):
        # Extract the cantonal % of the swiss new vehicles in 2005 and uses it to determine Vaud fleet in 1990-2004
        dm_tmp = dm_tech.group_all(dim='Categories2', inplace=False)
        idx = dm_tmp.idx
        arr_shares = dm_tmp.array[idx['Vaud'], 0, :, :] / dm_tmp.array[idx['Switzerland'], 0, :, :]
        idx_ch = dm_CH.idx
        arr_VD = dm_CH.array[idx_ch['Switzerland'], :, :, :] * arr_shares[np.newaxis, :, :]
        dm = dm_CH.copy()
        dm.add(arr_VD, dim='Country', col_label='Vaud')
        return dm


    ### New Passenger fleet for Switzerland and Vaud from 1990-2023
    def compute_new_fleet_tech_all_ots(dm_new_fleet_tech_ots1, dm_pass_new_fleet_ots2):
        # Applied 2005 share by technology to 1990-2005 period
        dm_new_fleet_tech_ots1.normalise(dim='Categories2', inplace=True, keep_original=True)

        if dm_new_fleet_tech_ots1.col_labels['Categories1'] != dm_pass_new_fleet_ots2.col_labels['Categories1']:
            raise ValueError('Make sure categories match')
        if dm_new_fleet_tech_ots1.col_labels['Country'] != dm_pass_new_fleet_ots2.col_labels['Country']:
            raise ValueError('Make sure Country match')
        # Multiply historical data on new fleet by 2005 technology share to obtain fleet by techology
        idx_n = dm_pass_new_fleet_ots2.idx
        idx_s = dm_new_fleet_tech_ots1.idx
        arr = dm_pass_new_fleet_ots2.array[:, :, idx_n['tra_passenger_new-vehicles'], :, np.newaxis] \
              * dm_new_fleet_tech_ots1.array[:, idx_s[first_year], np.newaxis, idx_s['tra_passenger_new-vehicles_share'], :, :]
        arr = arr[:, :, np.newaxis, :, :]

        dm_new_fleet_tech_ots1.drop(dim='Variables', col_label='tra_passenger_new-vehicles_share')
        dm_new_fleet_tech = dm_new_fleet_tech_ots1.copy()
        dm_new_fleet_tech.add(arr, dim='Years', col_label=dm_pass_new_fleet_ots2.col_labels['Years'])
        dm_new_fleet_tech.sort('Years')

        return dm_new_fleet_tech

    # New fleet Switzerland + Vaud: 2005 - now (by technology)
    dm_new_fleet_tech_ots1 = get_new_fleet_by_tech_raw(table_id_new_veh, file_new_veh_ots1)
    # Passenger new fleet Switzerland + Vaud: 2005 - new (by technology)
    dm_pass_new_fleet_tech_ots1, dm_new_tech = extract_passenger_new_fleet_by_tech(dm_new_fleet_tech_ots1)
    first_year = dm_pass_new_fleet_tech_ots1.col_labels['Years'][0]
    # New fleet Switzerland 1990 - 2004

    dm_pass_new_fleet_CH_ots2 = get_new_fleet(file_new_veh_ots2, first_year)
    # Add new fleet Vaud 1990 - 2004
    dm_pass_new_fleet_ots2 = compute_new_fleet_vaud(dm_pass_new_fleet_CH_ots2, dm_pass_new_fleet_tech_ots1)
    # Compute technology shares 1990 - 2004
    dm_new_fleet_tech = compute_new_fleet_tech_all_ots(dm_pass_new_fleet_tech_ots1, dm_pass_new_fleet_ots2)

    return dm_new_fleet_tech, dm_new_tech


def get_passenger_stock_fleet_by_tech_raw(table_id, file):
    # New fleet data are heavy, download them only once
    try:
        with open(file, 'rb') as handle:
            dm_fleet = pickle.load(handle)
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example')
        # Keep only passenger car main categories
        main_cat = [cat for cat in structure['Vehicle group / type'] if '>' in cat]
        passenger_cat = [cat for cat in main_cat if 'Passenger' in cat or 'Motorcycles' in cat]

        filtering = {'Year': structure['Year'],
                     'Year of first registration': structure['Year of first registration'],
                     'Vehicle group / type': passenger_cat,
                     'Canton': ['Switzerland', 'Vaud'],
                     'Fuel': structure['Fuel']}

        mapping_dim = {'Country': 'Canton',
                       'Years': 'Year',
                       'Variables': 'Year of first registration',
                       'Categories1': 'Vehicle group / type',
                       'Categories2': 'Fuel'}

        # Extract new fleet
        dm_fleet = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                            units=['number']*len(structure['Year of first registration']))

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_fleet, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # Group all vehicles independently of immatriculation data
    dm_fleet.groupby({'tra_passenger_vehicle-fleet': '.*'}, dim='Variables', regex=True, inplace=True)
    # Group passenger vehicles as LDV and motorcycles as 2W
    dm_fleet.groupby({'LDV': '.*Passenger.*', '2W': '.*Motorcycles'}, dim='Categories1', regex=True, inplace=True)
    # Map fuel technology to transport module category. Other category cannot be removed as it is above 1%
    dict_tech = {'BEV': ['Electricity'],
                 'ICE-diesel': ['Diesel'],
                 'ICE-gasoline': ['Petrol']}
    dm_fleet.groupby(dict_tech, dim='Categories2', regex=False, inplace=True)
    dm_fleet.drop(dim='Categories2', col_label='Without motor')

    return dm_fleet


def allocate_other_to_new_technologies(dm_fleet, dm_new_tech):

    dm_fleet_other = dm_fleet.filter({'Categories2': ['Other']})
    #dm_fleet_other.group_all('Categories2')
    dm_fleet_other.filter({'Years': dm_new_tech.col_labels['Years']}, inplace=True)
    dm_fleet.drop(dim='Categories2', col_label='Other')

    # Assuming none of the vehicles from 2005 has gone to waste (simplification),
    # the fleet at year Y will be the sum of new_fleet for years <= Y
    # The results are then normalised and the shares are used to allocate other
    dm_new_tech_cumul = dm_new_tech.copy()
    dm_new_tech_cumul.array = np.cumsum(dm_new_tech.array, axis=1)
    dm_new_tech_cumul.normalise(dim='Categories2', inplace=True, keep_original=False)
    # The normalisation returns nan if all values are 0. Then replace with 0
    np.nan_to_num(dm_new_tech_cumul.array, nan=0.0, copy=False)

    # Allocate
    idx = dm_fleet_other.idx
    arr = dm_fleet_other.array[:, :, :, :, idx['Other'], np.newaxis]*dm_new_tech_cumul.array
    dm_fleet_other.add(arr, dim='Categories2', col_label=dm_new_tech_cumul.col_labels['Categories2'])
    dm_fleet_other.drop(dim='Categories2', col_label='Other')

    # Map fuel technology to transport module category
    dict_tech = {'FCEV': ['Hydrogen'],
                 'ICE-diesel': ['Diesel-electricity: conventional hybrid'],
                 'ICE-gasoline': ['Petrol-electricity: conventional hybrid'],
                 'PHEV-diesel': ['Diesel-electricity: plug-in hybrid'],
                 'PHEV-gesoline': ['Petrol-electricity: plug-in hybrid'],
                 'ICE-gas': ['Gas (monovalent and bivalent)']}
    dm_fleet_other.groupby(dict_tech, dim='Categories2', regex=False, inplace=True)

    dm_fleet_new = dm_fleet.filter({'Years': dm_fleet_other.col_labels['Years']}, inplace=False)
    dm_fleet.drop(dim='Years', col_label=dm_fleet_other.col_labels['Years'])

    idx_f = dm_fleet.idx
    idx_o = dm_fleet_other.idx
    # Diesel
    dm_fleet_new.array[:, :, :, :, idx_f['ICE-diesel']] = \
        dm_fleet_new.array[:, :, :, :, idx_f['ICE-diesel']] \
        + dm_fleet_other.array[:, :, :, :, idx_o['ICE-diesel']]
    # Petrol
    dm_fleet_new.array[:, :, :, :, idx_f['ICE-gasoline']] = \
        dm_fleet_new.array[:, :, :, :, idx_f['ICE-gasoline']] \
        + dm_fleet_other.array[:, :, :, :, idx_o['ICE-gasoline']]
    dm_fleet_other.drop(dim='Categories2', col_label=['ICE-gasoline', 'ICE-diesel'])

    dm_fleet_new.append(dm_fleet_other, dim='Categories2')

    dm_fleet.add(0.0, dummy=True, dim='Categories2', col_label=dm_fleet_other.col_labels['Categories2'])
    dm_fleet.append(dm_fleet_new, dim='Years')

    return dm_fleet


def get_passenger_transport_demand(file_url, local_filename, years_ots):
    response = requests.get(file_url, stream=True)
    if not os.path.exists(local_filename):
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

    df = pd.read_csv(local_filename)
    df.columns = df.columns.str.replace(' (Bpkm)', '')
    df_T = pd.melt(df, id_vars=['Scenario', 'Mode'], var_name='Years', value_name='tra_passenger_demand')
    df_T['Country'] = 'Switzerland'
    # Pivot the dataframe
    df_pivot = df_T.pivot_table(index=['Country', 'Years'], columns=['Scenario', 'Mode'], values='tra_passenger_demand',
                                aggfunc='sum')  # Use 'sum' or 'first', depending on how you want to aggregate

    # Flatten the multi-level columns
    df_pivot.columns = [f'tra_passenger_transport-demand_{sce}_{mod}[Bpkm]' for sce, mod in df_pivot.columns]

    df_pivot.reset_index(inplace=True)
    dm_demand = DataMatrix.create_from_df(df_pivot, num_cat=2)
    dm_demand.switch_categories_order()

    # Rename categories to match calculator's
    map_cat = {'bike': ['Bikes', 'Mopeds and fast e-bikes'], '2W': ['Motorcycles'], 'walk': ['On foot'],
               'bus': ['Buses', 'Trolleybuses'], 'rail': ['Passenger rail'], 'LDV': ['Personal cars'],
               'metrotram': ['Trams']}
    dm_demand.groupby(map_cat, dim='Categories1', inplace=True)
    dm_demand.drop(col_label='Other private', dim='Categories1')

    # Extract ots years
    years_tmp = [y for y in dm_demand.col_labels['Years'] if y < 2025]
    dm_demand_ots = dm_demand.filter({'Years': years_tmp}, inplace=False)
    dm_demand_ots.filter({'Categories2': ['Reference']}, inplace=True)
    dm_demand_ots.group_all('Categories2')

    # Extract fts scenarios
    dm_demand_fts = dm_demand
    dm_demand_fts.drop(dim='Years', col_label=dm_demand_ots.col_labels['Years'])
    dm_demand_fts.operation('Low', '+', 'Reference', out_col='Medium-Low', dim='Categories2')
    idx = dm_demand_fts.idx
    dm_demand_fts.array[:, :, :, :, idx['Medium-Low']] = dm_demand_fts.array[:, :, :, :, idx['Medium-Low']]/2

    dict_demand_fts = dict()
    dict_demand_fts[1] = dm_demand_fts.filter({'Categories2': ['Reference']}, inplace=False)
    dict_demand_fts[1].group_all('Categories2')
    dict_demand_fts[2] = dm_demand_fts.filter({'Categories2': ['High']}, inplace=False)
    dict_demand_fts[2].group_all('Categories2')
    dict_demand_fts[4] = dm_demand_fts.filter({'Categories2': ['Low']}, inplace=False)
    dict_demand_fts[4].group_all('Categories2')

    dm_demand_ots.change_unit('tra_passenger_transport-demand', 1e9, old_unit='Bpkm', new_unit='pkm')

    # Extrapolate years before 2000, but skip 2020 (because of Covid)
    dm_demand_ots_2020 = dm_demand_ots.filter({'Years': [2020]})
    dm_demand_ots.drop(dim='Years', col_label=2020)
    linear_fitting(dm_demand_ots, years_ots)
    dm_demand_ots.drop(dim='Years', col_label=2020)
    dm_demand_ots.append(dm_demand_ots_2020, dim='Years')
    dm_demand_ots.sort('Years')

    return dm_demand_ots, dict_demand_fts


def get_public_transport_data(file_url, local_filename, years_ots):

    def get_excel_file_sheets(file_url, local_filename):
        response = requests.get(file_url, stream=True)
        if not os.path.exists(local_filename):
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
        # The excel file contains multiple sheets
        # load index sheet
        df_index = pd.read_excel(local_filename)
        df_index.drop(columns=['Unnamed: 0', 'Unnamed: 3', 'Unnamed: 5'], inplace=True)
        df_index.dropna(how='any', inplace=True)
        # Change colummns header
        df_index.rename(columns={'Unnamed: 1': 'Sheet', 'Unnamed: 2': 'Theme'}, inplace=True)
        df_index = df_index[1:]  # take the data less the header row
        sheet_fleet = list(df_index.loc[df_index['Theme'] == 'Moyens de transport: véhicules '].Sheet)[0]
        sheet_passenger = list(df_index.loc[df_index['Theme'] == 'Voyageurs transportés'].Sheet)[0]
        sheet_pkm = list(df_index.loc[df_index['Theme'] == 'Voyageurs-kilomètres'].Sheet)[0]
        sheet_vkm = list(df_index.loc[df_index['Theme']== 'Utilisation du système: prestations kilométriques, ponctualité et indices des prix'].Sheet)[0]

        df_fleet = pd.read_excel(local_filename, sheet_name=sheet_fleet.replace('.', '_'))
        df_nb_passenger = pd.read_excel(local_filename, sheet_name=sheet_passenger.replace('.', '_'))
        df_pkm = pd.read_excel(local_filename, sheet_name=sheet_pkm.replace('.', '_'))
        df_vkm = pd.read_excel(local_filename, sheet_name=sheet_vkm.replace('.', '_'))

        DF_dict = {'Passenger fleet': df_fleet,
                   'Passenger transported': df_nb_passenger,
                   'Passenger pkm': df_pkm,
                   'Passenger vkm': df_vkm}

        return DF_dict

    def extract_public_passenger_fleet(df, years_ots):
        # Change headers
        new_header = df.iloc[2]
        new_header.values[0] = 'Variables'
        df.columns = new_header
        df = df[3:].copy()
        # Remove nans and empty columns/rows
        df.drop(columns=np.nan, inplace=True)
        df.set_index('Variables', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        # Filter rows that contain at least one number (integer or float)
        df = df[df.applymap(pd.api.types.is_number).any(axis=1)]
        df = df.loc[:, df.applymap(pd.api.types.is_number).any(axis=0)].copy()
        # Extract only the data we are interested in:
        vehicles_vars = ['Voitures voyageurs (voitures de commande isolées, automotrices et éléments de rames automotrices inclus)',
                         'Trolleybus', 'Tram', 'Autobus', 'Total - nombre de véhicules motorisés']
        df_pass_public_veh = df.loc[vehicles_vars].copy()
        df_pass_public_veh = df_pass_public_veh.applymap(lambda x: pd.to_numeric(x, errors='coerce'))
        df_pass_public_veh.reset_index(inplace=True)
        df_pass_public_veh['Variables'] = df_pass_public_veh['Variables'].str[:10]
        df_pass_public_veh = df_pass_public_veh.groupby(['Variables']).sum()
        df_pass_public_veh.reset_index(inplace=True)

        # Pivot the dataframe
        df_pass_public_veh['Country'] = 'Switzerland'
        df_T = pd.melt(df_pass_public_veh, id_vars=['Variables', 'Country'], var_name='Years', value_name='values')
        df_pivot = df_T.pivot_table(index=['Country', 'Years'], columns=['Variables'], values='values', aggfunc='sum')
        df_pivot = df_pivot.add_suffix('[number]')
        df_pivot = df_pivot.add_prefix('tra_passenger_vehicle-fleet_')
        df_pivot.reset_index(inplace=True)

        dm_fleet = DataMatrix.create_from_df(df_pivot, num_cat=1)
        map_cat = {'bus': ['Autobus', 'Trolleybus'], 'metrotram': ['Tram'], 'rail': ['Total - no', 'Voitures v']}
        dm_fleet.groupby(map_cat, dim='Categories1', inplace=True)
        mask = dm_fleet.array == 0
        dm_fleet.array[mask] = np.nan
        add_missing_ots_years(dm_fleet, startyear=dm_fleet.col_labels['Years'][0], baseyear=dm_fleet.col_labels['Years'][-1])
        dm_fleet.fill_nans(dim_to_interp='Years')
        # Extrapolate based on 2010 values onwards
        years_init = [y for y in dm_fleet.col_labels['Years'] if y >= 2010]
        dm_tmp = dm_fleet.filter({'Years': years_init})
        years_extract = [y for y in years_ots if y >= 2010]
        linear_fitting(dm_tmp, years_extract)
        # Join historical values with extrapolated ones
        dm_fleet.drop(dim='Years', col_label=years_init)
        dm_fleet.append(dm_tmp, dim='Years')

        return dm_fleet

    def extract_public_passenger_pkm(df, years_ots):
        # Change headers
        new_header = df.iloc[2]
        new_header.values[0] = 'Variables'
        df.columns = new_header
        df = df[3:].copy()
        # Remove nans and empty columns/rows
        df.drop(columns=np.nan, inplace=True)
        df.set_index('Variables', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        # Filter rows that contain at least one number (integer or float)
        df = df[df.applymap(pd.api.types.is_number).any(axis=1)]
        df = df.loc[:, df.applymap(pd.api.types.is_number).any(axis=0)].copy()
        # Vars to keep
        vars_to_keep = ['Chemins de fer', 'Chemins de fer à crémaillère', 'Tram', 'Trolleybus', 'Autobus']
        df_pkm = df.loc[vars_to_keep]
        # Convert ... to numerics
        df_pkm = df_pkm.applymap(lambda x: pd.to_numeric(x, errors='coerce'))
        df_pkm.reset_index(inplace=True)

        # Pivot the dataframe
        df_pkm['Country'] = 'Switzerland'
        df_T = pd.melt(df_pkm, id_vars=['Variables', 'Country'], var_name='Years', value_name='values')
        df_pivot = df_T.pivot_table(index=['Country', 'Years'], columns=['Variables'], values='values', aggfunc='sum')
        df_pivot = df_pivot.add_suffix('[Mpkm]')
        df_pivot = df_pivot.add_prefix('tra_passenger_transport-demand_')
        df_pivot.reset_index(inplace=True)

        # Create datamatrix
        dm = DataMatrix.create_from_df(df_pivot, num_cat=1)
        # Convert 0 to np.nan
        cat_map = {'bus': ['Autobus', 'Trolleybus'], 'metrotram': ['Tram'],
                   'rail': ['Chemins de fer', 'Chemins de fer à crémaillère']}
        dm.groupby(cat_map, dim='Categories1', inplace=True)
        mask = dm.array == 0
        dm.array[mask] = np.nan

        # Extrapolate based on 2020 values onwards
        years_init = [y for y in dm.col_labels['Years'] if y >= 2020]
        dm_tmp = dm.filter({'Years': years_init})
        years_extract = [y for y in years_ots if y >= 2020]
        linear_fitting(dm_tmp, years_extract)
        # Join historical values with extrapolated ones
        dm.drop(dim='Years', col_label=years_init)
        dm.append(dm_tmp, dim='Years')
        # Back-extrapolate (use data until 2019 - Covid-19)
        years_tmp = [y for y in dm.col_labels['Years'] if y <= 2019]
        dm_tmp = dm.filter({'Years': years_tmp})
        years_extract = [y for y in years_ots if y <= 2019]
        linear_fitting(dm_tmp, years_extract)
        dm.drop(dim='Years', col_label=years_tmp)
        dm.append(dm_tmp, dim='Years')
        dm.sort('Years')
        dm.change_unit('tra_passenger_transport-demand', 1e6, old_unit='Mpkm', new_unit='pkm')

        return dm

    def extract_public_passenger_vkm(df, years_ots):
        # Change headers
        new_header = df.iloc[2]
        new_header.values[0] = 'Variables'
        df.columns = new_header
        df = df[3:].copy()
        # Remove nans and empty columns/rows
        df.drop(columns=np.nan, inplace=True)
        df.set_index('Variables', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        # Filter rows that contain at least one number (integer or float)
        df = df[df.applymap(pd.api.types.is_number).any(axis=1)]
        df = df.loc[:, df.applymap(pd.api.types.is_number).any(axis=0)]
        # Vars to keep
        vars_to_keep = ['Chemins de fer', 'Chemins de fer à crémaillère', 'Tram', 'Trolleybus', 'Autobus']
        df_vkm = df.loc[vars_to_keep].copy()
        # Convert ... to numerics
        df_vkm = df_vkm.applymap(lambda x: pd.to_numeric(x, errors='coerce'))
        df_vkm.reset_index(inplace=True)

        # Pivot the dataframe
        df_vkm['Country'] = 'Switzerland'
        df_T = pd.melt(df_vkm, id_vars=['Variables', 'Country'], var_name='Years', value_name='values')
        df_pivot = df_T.pivot_table(index=['Country', 'Years'], columns=['Variables'], values='values', aggfunc='sum')
        df_pivot = df_pivot.add_suffix('[1000vkm]')
        df_pivot = df_pivot.add_prefix('tra_passenger_transport-demand-vkm_')
        df_pivot.reset_index(inplace=True)

        # Create datamatrix
        dm = DataMatrix.create_from_df(df_pivot, num_cat=1)

        # Convert 0 to np.nan
        cat_map = {'bus': ['Autobus', 'Trolleybus'], 'metrotram': ['Tram'],
                   'rail': ['Chemins de fer', 'Chemins de fer à crémaillère']}
        dm.groupby(cat_map, dim='Categories1', inplace=True)
        mask = dm.array == 0
        dm.array[mask] = np.nan

        # Extrapolate based on 2010 values onwards
        years_init = [y for y in dm.col_labels['Years'] if y >= 2015 and y != 2020]
        dm_tmp = dm.filter({'Years': years_init})
        years_extract = [y for y in years_ots if y >= 2015]
        linear_fitting(dm_tmp, years_extract)
        dm_tmp.drop(dim='Years', col_label=2020)
        # Join historical values with extrapolated ones
        dm.drop(dim='Years', col_label=years_init)
        dm.append(dm_tmp, dim='Years')
        dm.sort('Years')
        linear_fitting(dm, years_ots)
        dm.change_unit('tra_passenger_transport-demand-vkm', 1000, old_unit='1000vkm', new_unit='vkm')

        return dm

    DF_dict = get_excel_file_sheets(file_url, local_filename)
    dm_public_fleet = extract_public_passenger_fleet(DF_dict['Passenger fleet'], years_ots)
    dm_public_demand_pkm = extract_public_passenger_pkm(DF_dict['Passenger pkm'], years_ots)
    dm_public_demand_vkm = extract_public_passenger_vkm(DF_dict['Passenger vkm'], years_ots)

    DM_public = {'public_fleet': dm_public_fleet, 'public_demand-pkm': dm_public_demand_pkm,
                 'public_demand-vkm': dm_public_demand_vkm}

    return DM_public


def get_vehicle_efficiency(table_id, file, years_ots, var_name, overwrite_VD_PHEV_FCEV=False):
    # New fleet data are heavy, download them only once
    try:
        with open(file, 'rb') as handle:
            dm_veh_eff = pickle.load(handle)
            print(f'The vehicle efficienty is read from file {file}. Delete it if you want to update data from api.')
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        i = 0
        # The table is too big to be downloaded at once
        for eu_class in structure["Classe d'émission selon l'UE"]:
            for part in structure['Filtre à particules']:
                i = i + 1
                filtering = {'Année': structure['Année'],
                             'Carburant': structure['Carburant'],
                             'Puissance': structure['Puissance'],
                             'Canton': ['Suisse', 'Vaud'],
                             "Classe d'émission selon l'UE": eu_class,
                             'Émissions de CO2 par km (NEDC)': structure['Émissions de CO2 par km (NEDC)'],
                             'Filtre à particules': part}

                mapping_dim = {'Country': 'Canton',
                               'Years': 'Année',
                               'Variables': 'Puissance',
                               'Categories1': 'Carburant',
                               'Categories2': 'Émissions de CO2 par km (NEDC)'}

                # Extract new fleet
                dm_veh_eff_cl = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                                units=['gCO2/km']*len(structure['Puissance']), language='fr')
                dm_veh_eff_cl.array = np.nan_to_num(dm_veh_eff_cl.array)

                if dm_veh_eff_cl is None:
                    raise ValueError(f'API returned None for {eu_class}')
                if i == 1:
                    dm_veh_eff = dm_veh_eff_cl.copy()
                else:
                    dm_veh_eff.array = dm_veh_eff.array + dm_veh_eff_cl.array

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_veh_eff, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Distribute Inconnu on other categories based on their share
    cat_other = [cat for cat in dm_veh_eff.col_labels['Categories2'] if cat != 'Inconnu']
    dm_other = dm_veh_eff.filter({'Categories2': cat_other}, inplace=False)
    dm_other.normalise(dim='Categories2', inplace=True)
    idx = dm_veh_eff.idx
    arr_inc = dm_veh_eff.array[:, :, :, :, idx['Inconnu'], np.newaxis] * dm_other.array
    dm_veh_eff.drop(dim='Categories2', col_label='Inconnu')
    dm_veh_eff.array = dm_veh_eff.array + arr_inc

    # Remove fuel type "Autre" (there are only very few car in this category)
    dm_veh_eff.drop(dim='Categories1', col_label='Autre')

    # Assign Vaud Hydrogen and hybrid-rechargeable to Swiss values
    if overwrite_VD_PHEV_FCEV:
        idx = dm_veh_eff.idx
        cats = ['Hydrogène', 'Essence-électrique: hybride rechargeable', 'Diesel-électrique: hybride rechargeable']
        for cat in cats:
            dm_veh_eff.array[idx['Vaud'], :, :, idx[cat]] = dm_veh_eff.array[idx['Suisse'], :, :, idx[cat]]

    # Group categories1 according to model
    map_cat = {'ICE-diesel': ['Diesel', 'Diesel-électrique: hybride normal'],
               'ICE-gasoline': ['Essence', 'Essence-électrique: hybride normal'],
               'ICE-gas': ['Gaz (monovalent et bivalent)'],
               'BEV': ['Électrique'],
               'FCEV': ['Hydrogène'],
               'PHEV-diesel': ['Diesel-électrique: hybride rechargeable'],
               'PHEV-gasoline': ['Essence-électrique: hybride rechargeable']
               }
    dm_veh_eff.groupby(map_cat, dim='Categories1', inplace=True)

    # Do this to have realistic curves
    mask = dm_veh_eff.array == 0
    dm_veh_eff.array[mask] = np.nan

    # Flat extrapolation
    years_to_add = [year for year in years_ots if year not in dm_veh_eff.col_labels['Years']]
    dm_veh_eff.add(np.nan, dummy=True, col_label=years_to_add, dim='Years')
    dm_veh_eff.sort(dim='Years')
    dm_veh_eff.fill_nans(dim_to_interp='Years')

    dm_veh_eff.groupby({var_name: '.*'}, dim='Variables', regex=True, inplace=True)

    # Clean grams CO2 category and perform weighted average
    # cols are e.g '0 - 50 g' -> '0-50' -> 25
    dm_veh_eff.rename_col_regex(' g', '', dim='Categories2')
    dm_veh_eff.rename_col_regex(' ', '', dim='Categories2')
    dm_veh_eff.rename_col('Plusde300', '300-350', dim='Categories2')
    cat2_list_old = dm_veh_eff.col_labels['Categories2']
    co2_km = []
    for i in range(len(cat2_list_old)):
        old_cat = cat2_list_old[i]
        new_cat = float(old_cat.split('-')[0]) + float(old_cat.split('-')[1])/2
        co2_km.append(new_cat)
    co2_arr = np.array(co2_km)
    dm_veh_eff.normalise(dim='Categories2', inplace=True)
    dm_veh_eff.array = dm_veh_eff.array*co2_arr[np.newaxis, np.newaxis, np.newaxis, np.newaxis, :]
    dm_veh_eff.group_all(dim='Categories2')

    dm_veh_eff.change_unit(var_name, 1, old_unit='%', new_unit='gCO2/km')


    for i in range(2):
        window_size = 3  # Change window size to control the smoothing effect
        data_smooth = moving_average(dm_veh_eff.array, window_size, axis=dm_veh_eff.dim_labels.index('Years'))
        dm_veh_eff.array[:, 1:-1, ...] = data_smooth

    # Add LDV
    dm_veh_eff_LDV = DataMatrix.based_on(dm_veh_eff.array[..., np.newaxis], dm_veh_eff, change={'Categories2': ['LDV']},
                                         units=dm_veh_eff.units)
    dm_veh_eff_LDV.switch_categories_order()

    return dm_veh_eff_LDV


def get_new_vehicle_efficiency(table_id, file, years_ots, var_name):
    # New fleet data are heavy, download them only once
    try:
        with open(file, 'rb') as handle:
            dm_veh_eff = pickle.load(handle)
            print(f'The vehicle efficienty is read from file {file}. Delete it if you want to update data from api.')
    except OSError:
        structure, title = get_data_api_CH(table_id, mode='example', language='fr')
        i = 0
        # The table is too big to be downloaded at once
        for eu_class in structure["Classe d'émission selon l'UE"]:
            i = i + 1
            filtering = {'Année': structure['Année'],
                         'Carburant': structure['Carburant'],
                         'Puissance': structure['Puissance'],
                         'Canton': ['Suisse', 'Vaud'],
                         "Classe d'émission selon l'UE": eu_class,
                         'Émissions de CO2 par km (NEDC/WLTP)': structure['Émissions de CO2 par km (NEDC/WLTP)']}

            mapping_dim = {'Country': 'Canton',
                           'Years': 'Année',
                           'Variables': 'Puissance',
                           'Categories1': 'Carburant',
                           'Categories2': 'Émissions de CO2 par km (NEDC/WLTP)'}

            # Extract new fleet
            dm_veh_eff_cl = get_data_api_CH(table_id, mode='extract', filter=filtering, mapping_dims=mapping_dim,
                                            units=['gCO2/km']*len(structure['Puissance']), language='fr')
            dm_veh_eff_cl.array = np.nan_to_num(dm_veh_eff_cl.array)

            if dm_veh_eff_cl is None:
                raise ValueError(f'API returned None for {eu_class}')
            if i == 1:
                dm_veh_eff = dm_veh_eff_cl.copy()
            else:
                dm_veh_eff.array = dm_veh_eff.array + dm_veh_eff_cl.array

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        f = os.path.join(current_file_directory, file)
        with open(f, 'wb') as handle:
            pickle.dump(dm_veh_eff, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Do this to have realistic curves
    mask = dm_veh_eff.array == 0
    dm_veh_eff.array[mask] = np.nan

    # Flat extrapolation
    years_to_add = [year for year in years_ots if year not in dm_veh_eff.col_labels['Years']]
    dm_veh_eff.add(np.nan, dummy=True, col_label=years_to_add, dim='Years')
    dm_veh_eff.sort(dim='Years')
    dm_veh_eff.fill_nans(dim_to_interp='Years')

    # Explore Inconnu category
    # -> The data seem to be good only from 2016 to 2020, still the "Inconnu" share is big
    dm_norm = dm_veh_eff.normalise(dim='Categories2', inplace=False)
    idx = dm_norm.idx
    for country in dm_veh_eff.col_labels['Country']:
        for year in dm_veh_eff.col_labels['Years']:
            for cat in dm_veh_eff.col_labels['Categories1']:
                # If "Inconnu" is more than 20% remove the data points
                if dm_norm.array[idx[country], idx[year], 0, idx[cat], idx['Inconnu']] > 0.2:
                    dm_veh_eff.array[idx[country], idx[year], 0, idx[cat], :] = np.nan

    for i in range(2):
        window_size = 3  # Change window size to control the smoothing effect
        data_smooth = moving_average(dm_veh_eff.array, window_size, axis=dm_veh_eff.dim_labels.index('Years'))
        dm_veh_eff.array[:, 1:-1, ...] = data_smooth

    # Distribute Inconnu on other categories based on their share
    cat_other = [cat for cat in dm_veh_eff.col_labels['Categories2'] if cat != 'Inconnu']
    dm_other = dm_veh_eff.filter({'Categories2': cat_other}, inplace=False)
    dm_other.normalise(dim='Categories2', inplace=True)
    dm_other.array = np.nan_to_num(dm_other.array)
    idx = dm_veh_eff.idx
    arr_inc = np.nan_to_num(dm_veh_eff.array[:, :, :, :, idx['Inconnu'], np.newaxis]) * dm_other.array
    dm_veh_eff.drop(dim='Categories2', col_label='Inconnu')
    dm_veh_eff.array = dm_veh_eff.array + arr_inc

    # Remove fuel type "Autre" (there are only very few car in this category)
    dm_veh_eff.drop(dim='Categories1', col_label='Autre')

    # Group categories1 according to model
    map_cat = {'ICE-diesel': ['Diesel', 'Diesel-électrique: hybride normal'],
               'ICE-gasoline': ['Essence', 'Essence-électrique: hybride normal'],
               'ICE-gas': ['Gaz (monovalent et bivalent)'],
               'BEV': ['Électrique'],
               'FCEV': ['Hydrogène'],
               'PHEV-diesel': ['Diesel-électrique: hybride rechargeable'],
               'PHEV-gasoline': ['Essence-électrique: hybride rechargeable']
               }
    dm_veh_eff.groupby(map_cat, dim='Categories1', inplace=True)

    dm_veh_eff.groupby({var_name: '.*'}, dim='Variables', regex=True, inplace=True)

    # Clean grams CO2 category and perform weighted average
    # cols are e.g '0 - 50 g' -> '0-50' -> 25
    dm_veh_eff.rename_col_regex(' g', '', dim='Categories2')
    dm_veh_eff.rename_col_regex(' ', '', dim='Categories2')
    dm_veh_eff.rename_col('Plusde300', '300-350', dim='Categories2')
    cat2_list_old = dm_veh_eff.col_labels['Categories2']
    co2_km = []
    for i in range(len(cat2_list_old)):
        old_cat = cat2_list_old[i]
        new_cat = float(old_cat.split('-')[0]) + float(old_cat.split('-')[1])/2
        co2_km.append(new_cat)
    dm_veh_eff.normalise(dim='Categories2', inplace=True)
    dm_veh_eff.array = dm_veh_eff.array*np.array(co2_km)
    dm_veh_eff.group_all(dim='Categories2')
    dm_veh_eff.change_unit(var_name, 1, old_unit='%', new_unit='gCO2/km')

    # Add LDV
    dm_veh_eff_LDV = DataMatrix.based_on(dm_veh_eff.array[..., np.newaxis], dm_veh_eff, change={'Categories2': ['LDV']},
                                         units=dm_veh_eff.units)
    dm_veh_eff_LDV.switch_categories_order()

    return dm_veh_eff_LDV


years_ots = create_years_list(start_year=1990, end_year=2023, step=1, astype=int)

#### New passenger fleet by technology LDV, 2W
table_id_new_veh = 'px-x-1103020200_120'
# file is created if it doesn't exist
file_new_veh_ots1 = 'data/tra_new_fleet.pickle'
# download this from https://www.bfs.admin.ch/asset/en/30305446, download csv file FSO number gr-e-11.03.02.02.01a
file_new_veh_ots2 = 'data/tra_new-vehicles_CH_1990-2023.csv'
# dm_new_tech is the number of new vehicles for new technologies (used to allocate "Other" category in dm_pass_fleet
dm_pass_new_fleet, dm_new_tech = compute_passenger_new_fleet(table_id_new_veh, file_new_veh_ots1, file_new_veh_ots2)
del table_id_new_veh, file_new_veh_ots1, file_new_veh_ots2

#### Passenger fleet by technology (stock) LDV, 2W
table_id_tot_veh = 'px-x-1103020100_101'
file_tot_veh = 'data/tra_tot_fleet.pickle'
dm_pass_fleet_raw = get_passenger_stock_fleet_by_tech_raw(table_id_tot_veh, file_tot_veh)
# Allocate "Other" category to new technologies
dm_pass_fleet = allocate_other_to_new_technologies(dm_pass_fleet_raw, dm_new_tech)
del table_id_tot_veh, file_tot_veh, dm_pass_fleet_raw, dm_new_tech

#### Passenger transport demand - Switzerland only
# Data source: Sweet CROSS
file_url = 'https://sweet-cross.ethz.ch/data/end-use-energy-demand-cross/2022-09-30/passenger-transport-demand-2000-2050.csv'
local_filename = 'data/SweetCROSS_passenger-transport-energy-demand.csv'  # Created by the routine if it doesn't exist
dm_pass_demand_ots, dict_pass_demand_fts = get_passenger_transport_demand(file_url, local_filename, years_ots)
del file_url, local_filename

#### Public transport - Switzerland only
# Note that this data are better for ots than Sweet CROSS data
file_url = 'https://dam-api.bfs.admin.ch/hub/api/dam/assets/32253175/master'
# Transports publics (trafic marchandises rail inclus) - séries chronologiques détaillées
local_filename = 'data/tra_public_transport.xlsx'
DM_public = get_public_transport_data(file_url, local_filename, years_ots)
del file_url, local_filename

#### Vehicle efficiency - LDV - CO2/km
# FCEV (Hydrogen) data are off - BEV too
# !!! Attention: The data are bad before 2016 and after 2020, backcasting to 1990 from 2016 done with linear fitting.
table_id_veh_eff = 'px-x-1103020100_106'
local_filename_veh = 'data/tra_veh_efficiency.pickle'  # The file is created if it doesn't exist
overwrite_VD_PHEV_FCEV = False
dm_veh_eff_LDV = get_vehicle_efficiency(table_id_veh_eff, local_filename_veh,
                                        var_name='tra_passenger_veh-efficiency_fleet', years_ots=years_ots)
del table_id_veh_eff, local_filename_veh, overwrite_VD_PHEV_FCEV

#### Vehicle efficiency new - LDV - CO2/km
# FCEV data are off, BEV = 25 gCO2/km independently of car power
table_id_new_eff = 'px-x-1103020200_201'
local_filename_new = 'data/tra_new-veh_efficiency.pickle'  # The file is created if it doesn't exist3#
dm_veh_new_eff_LDV = get_new_vehicle_efficiency(table_id_new_eff, local_filename_new,
                                                var_name='tra_passenger_veh-efficiency_new', years_ots=years_ots)
del table_id_new_eff, local_filename_new


print('Hello')