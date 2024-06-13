import pandas as pd

from model.common.data_matrix_class import DataMatrix
from model.common.interface_class import Interface
from model.common.constant_data_matrix_class import ConstantDataMatrix
from model.common.io_database import read_database, read_database_fxa
from model.common.auxiliary_functions import compute_stock, read_database_to_ots_fts_dict, filter_geoscale
from model.common.auxiliary_functions import read_level_data
import pickle
import json
import os
import numpy as np
import time


def database_from_csv_to_datamatrix():

    # Read database
    # Set years range
    years_setting = [1990, 2015, 2050, 5]
    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_ots = list(np.linspace(start=startyear, stop=baseyear, num=(baseyear-startyear)+1).astype(int))
    years_fts = list(np.linspace(start=baseyear+step_fts, stop=lastyear, num=int((lastyear-baseyear)/step_fts)).astype(int))
    years_all = years_ots + years_fts

    # Read fixed assumptions to datamatrix
    df = read_database_fxa('transport_fixed-assumptions')
    dm = DataMatrix.create_from_df(df, num_cat=0)

    # Keep only ots and fts years
    dm = dm.filter(selected_cols={'Years': years_all})

    dm_freight_tech = dm.filter_w_regex({'Variables': 'tra_freight_technology-share.*|tra_freight_vehicle-efficiency.*'})
    dm_passenger_tech = dm.filter_w_regex({'Variables': 'tra_passenger_technology-share.*|tra_passenger_veh-efficiency_fleet.*'})
    dm_passenger_mode_road = dm.filter_w_regex({'Variables': 'tra_passenger_vehicle-lifetime.*'})
    # !FIXME: Vaud and Switzerland have renewal-rate at 0 in for some ots
    dm_passenger_mode_other = dm.filter_w_regex({'Variables': 'tra_passenger_avg-pkm-by-veh.*|tra_passenger_renewal-rate.*'})
    dm_freight_mode_other = dm.filter_w_regex({'Variables': 'tra_freight_tkm-by-veh.*|tra_freight_renewal-rate.*'})
    dm_freight_mode_road = dm.filter_w_regex({'Variables': 'tra_freight_lifetime.*'})

    # Add metrotram to passenger_tech
    metrotram_tech = np.ones((dm_passenger_tech.array.shape[0], dm_passenger_tech.array.shape[1]))
    dm_passenger_tech.add(metrotram_tech, dim="Variables", col_label='tra_passenger_technology-share_fleet_metrotram_mt', unit='%')
    dm_passenger_tech.rename_col(col_in='tra_passenger_veh-efficiency_fleet_metrotram',
                                 col_out='tra_passenger_veh-efficiency_fleet_metrotram_mt', dim='Variables')
    # Add dimensions
    dm_freight_tech.deepen_twice()
    dm_passenger_tech.deepen_twice()
    dm_passenger_mode_road.deepen()
    dm_passenger_mode_other.deepen()
    dm_freight_mode_other.deepen()
    dm_freight_mode_road.deepen()

    dict_fxa = {
        'freight_tech': dm_freight_tech,
        'passenger_tech': dm_passenger_tech,
        'passenger_mode_road': dm_passenger_mode_road,
        'passenger_mode_other': dm_passenger_mode_other,
        'freight_mode_other': dm_freight_mode_other,
        'freight_mode_road': dm_freight_mode_road
    }

    dict_ots = {}
    dict_fts = {}
    # Read passenger levers
    file = 'transport_passenger-aviation-pkm'
    lever = 'passenger-aviation-pkm'
    # dm_passenger_aviation
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Read passenger efficiency
    file = 'transport_passenger-efficiency'
    lever = 'passenger_veh-efficiency_new'
    df_ots, df_fts = read_database(file, lever, level='all')
    df_ots.columns = df_ots.columns.str.replace('MJ/pkm', 'MJ/km')
    df_fts.columns = df_fts.columns.str.replace('MJ/pkm', 'MJ/km')
    df_ots.columns = df_ots.columns.str.replace('metrotram', 'metrotram_mt')
    df_fts.columns = df_fts.columns.str.replace('metrotram', 'metrotram_mt')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

    # Read passenger modal split urban rural
    file = 'transport_passenger-modal-split'
    lever = 'passenger_modal-share'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Read passenger occupancy
    file = 'transport_passenger-occupancy'
    lever = 'passenger_occupancy'
    # dm_passenger_occupancy
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Read passenger technology split
    file = 'transport_passenger-technology-split'
    lever = 'passenger_technology-share_new'
    df_ots, df_fts = read_database(file, lever, level='all')
    df_ots['tra_passenger_technology-share_new_metrotram_mt[%]'] = 1
    df_fts['tra_passenger_technology-share_new_metrotram_mt[%]'] = 1
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

    # Read passenger use rate
    file = 'transport_passenger-use-rate'
    lever = 'passenger_utilization-rate'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear,
                                                       years=years_all, dict_ots=dict_ots, dict_fts=dict_fts)

    # Read freight levers
    # Efficiency
    file = 'transport_freight-efficiency'
    lever = 'freight_vehicle-efficiency_new'
    df_ots, df_fts = read_database(file, lever, level='all')
    df_ots.columns = df_ots.columns.str.replace('tkm', 'km')
    df_fts.columns = df_fts.columns.str.replace('tkm', 'km')
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

    # Load factors & utilisation rate
    file = 'transport_freight-load-factor'
    lever_1 = 'freight_load-factor'
    lever = 'freight_utilization-rate'
    # there is a problem with the lever name in the original file
    # !FIXME this should be merged with freight use-rate
    df_ots, df_fts = read_database(file, lever_1, level='all')
    df_ots.rename(columns={lever_1: lever}, inplace=True)
    df_fts.rename(columns={lever_1: lever}, inplace=True)
    df_ots_2, df_fts_2 = read_database('transport_freight-use-rate', lever, level='all')
    df_ots = df_ots.merge(df_ots_2, on=['Country', 'Years', lever])
    df_fts = df_fts.merge(df_fts_2, on=['Country', 'Years', lever])
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

    # Modal split
    file = 'transport_freight-modal-split'
    lever = 'freight_modal-share'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=1, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    # Technology split
    file = 'transport_freight-technology-split'
    lever = 'freight_technology-share_new'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    # Volume
    file = 'transport_freight-volume'
    lever = 'freight_tkm'
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=0, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts)

    # Read fuel mix for efuel and biofuels
    fuels = ['biofuels', 'efuel']
    mode = ['marine', 'road', 'aviation']
    lever = 'fuel-mix'
    i = 0
    for f in fuels:
        for m in mode:
            file = 'transport_fuel-mix-' + m + '-' + f
            if f == 'biofuels':
                f = 'biofuel'
            lever_i = 'fuel-mix_' + f + '-' + m
            df_ots_i, df_fts_i = read_database(file, lever_i, level='all')
            df_ots_i.rename(columns={lever_i: lever}, inplace=True)
            df_fts_i.rename(columns={lever_i: lever}, inplace=True)
            df_ots_i.columns = df_ots_i.columns.str.replace('biofuel-', 'biofuel_')
            df_ots_i.columns = df_ots_i.columns.str.replace('efuel-', 'efuel_')
            df_fts_i.columns = df_fts_i.columns.str.replace('biofuel-', 'biofuel_')
            df_fts_i.columns = df_fts_i.columns.str.replace('efuel-', 'efuel_')
            if i == 0:
                df_ots = df_ots_i
                df_fts = df_fts_i
            else:
                df_ots = df_ots.merge(df_ots_i, on=['Country', 'Years', lever])
                df_fts = df_fts.merge(df_fts_i, on=['Country', 'Years', lever])
            if f == 'biofuel':
                f = 'biofuels'
            i = i + 1
    dict_ots, dict_fts = read_database_to_ots_fts_dict(file, lever, num_cat=2, baseyear=baseyear, years=years_all,
                                                       dict_ots=dict_ots, dict_fts=dict_fts, df_ots=df_ots, df_fts=df_fts)

    # Load constants
    cdm_const = ConstantDataMatrix.extract_constant('interactions_constants', pattern='cp_tra_emission-factor.*', num_cat=2)

    DM_transport = {
        'fxa': dict_fxa,
        'fts': dict_fts,
        'ots': dict_ots,
        'constant': cdm_const
    }

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, '../_database/data/datamatrix/transport.pickle')
    with open(f, 'wb') as handle:
        pickle.dump(DM_transport, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return


def read_data(data_file, lever_setting):

    with open(data_file, 'rb') as handle:
        DM_transport = pickle.load(handle)

    dict_fxa = DM_transport['fxa']
    dm_freight_tech = dict_fxa['freight_tech']
    dm_passenger_tech = dict_fxa['passenger_tech']
    dm_passenger_mode_road = dict_fxa['passenger_mode_road']
    dm_passenger_mode_other = dict_fxa['passenger_mode_other']
    dm_freight_mode_other = dict_fxa['freight_mode_other']
    dm_freight_mode_road = dict_fxa['freight_mode_road']

    # Read fts based on lever_setting
    DM_ots_fts = read_level_data(DM_transport, lever_setting)


    # PASSENGER
    dm_passenger_aviation = DM_ots_fts['passenger-aviation-pkm']
    dm_passenger_tech.append(DM_ots_fts['passenger_veh-efficiency_new'], dim='Variables')
    dm_passenger_tech.append(DM_ots_fts['passenger_technology-share_new'], dim='Variables')
    dm_passenger_modal = DM_ots_fts['passenger_modal-share']
    dm_passenger_mode_road.append(DM_ots_fts['passenger_occupancy'], dim='Variables')
    dm_passenger_mode_road.append(DM_ots_fts['passenger_utilization-rate'], dim='Variables')
    # FREIGHT
    dm_freight_tech.append(DM_ots_fts['freight_vehicle-efficiency_new'], dim='Variables')
    dm_freight_tech.append(DM_ots_fts['freight_technology-share_new'], dim='Variables')
    dm_freight_mode_road.append(DM_ots_fts['freight_utilization-rate'], dim='Variables')
    dm_freight_modal_share = DM_ots_fts['freight_modal-share']
    dm_freight_demand = DM_ots_fts['freight_tkm']
    # OTHER
    dm_fuels = DM_ots_fts['fuel-mix']

    DM_passenger = {
        'passenger_tech': dm_passenger_tech,
        'passenger_mode_other': dm_passenger_mode_other,
        'passenger_aviation': dm_passenger_aviation,
        'passenger_modal_split': dm_passenger_modal,
        'passenger_mode_road': dm_passenger_mode_road
        }

    DM_freight = {
        'freight_tech': dm_freight_tech,
        'freight_mode_other': dm_freight_mode_other,
        'freight_mode_road': dm_freight_mode_road,
        'freight_demand': dm_freight_demand,
        'freight_modal_split': dm_freight_modal_share
    }

    DM_other = {
        'fuels': dm_fuels
    }

    cdm_const = DM_transport['constant']

    return DM_passenger, DM_freight, DM_other, cdm_const


def simulate_lifestyles_input():
    # Read input from lifestyle
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(current_file_directory, "../_database/data/xls/All-Countries-interface_from-lifestyles-to-transport.xlsx")
    df = pd.read_excel(f, sheet_name="default")
    dm = DataMatrix.create_from_df(df, num_cat=0)
    dm_pop = dm.filter_w_regex({'Variables': 'lfs_pop.*'})
    dm_passenger_demand = dm.filter_w_regex({'Variables': 'lfs_passenger-travel-demand.*'})
    dm_passenger_demand.deepen()
    DM = {
        'lfs_pop': dm_pop,
        'lfs_passenger_demand': dm_passenger_demand
    }
    return DM


def compute_pkm_demand(modal_split, urb_nonurb_demand):
    # It take the datamatrix with the modal split for urban and non urban
    # and it multiplies it with the demand from lifestyle to return the demand in pkm
    idx_d = urb_nonurb_demand.idx
    idx_m = modal_split.idx
    tmp_nonurb = urb_nonurb_demand.array[:, :, :, idx_d['non-urban'], np.newaxis] * \
                 modal_split.array[:, :, :, idx_m['nonurban'], :]
    tmp_urb = urb_nonurb_demand.array[:, :, :, idx_d['urban'], np.newaxis] * \
              modal_split.array[:, :, :, idx_m['urban'], :]
    tmp_demand = tmp_nonurb + tmp_urb
    cols = {
        'Country': modal_split.col_labels['Country'].copy(),
        'Years': modal_split.col_labels['Years'].copy(),
        'Variables': ['tra_passenger_transport-demand'],
        'Categories1': modal_split.col_labels['Categories2'].copy()
    }
    demand = DataMatrix(col_labels=cols, units={'tra_passenger_transport-demand': 'pkm'})
    demand.array = tmp_demand
    return demand


def compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting):

    def evaluate_at_tmlife(dm, tmlife_arr, col_name):
        a = [dm.dim_labels.index('Years'), dm.dim_labels.index('Variables')]  # years axis and variables axis
        arr_shape = []
        for ax, i in enumerate(dm.array.shape):
            if ax not in a:
                arr_shape.append(i)
        out = np.empty(tuple(arr_shape))
        out[...] = np.nan
        idx_var = dm.single_index(col_name, 'Variables')[col_name]
        for c in range(arr_shape[0]):
            t_cv = tmlife_arr[c, idx_var]
            i_t_cv = dm.single_index(t_cv, 'Years')[t_cv]
            out[c, ...] = dm.array[c, i_t_cv, idx_var, ...]
        return out

    rr_col = cols['renewal-rate']
    tot_col = cols['tot']
    waste_col = cols['waste']
    tech_tot_col = cols['tech_tot']
    eff_tot_col = cols['eff_tot']
    eff_new_col = cols['eff_new']
    new_col = cols['new']

    startyear = years_setting[0]
    baseyear = years_setting[1]
    lastyear = years_setting[2]
    step_fts = years_setting[3]
    years_fts = list(
        np.linspace(start=baseyear + step_fts, stop=lastyear, num=int((lastyear - baseyear) / step_fts)).astype(int))
    tmn = baseyear
    idx_m = dm_mode.index_all()
    idx_t = dm_tech.index_all()

    for t in years_fts:
        # Interpolate to obtain vehicle fleet at t-1 (e.g. if t = 2020 and tmn = 2015, t-1 = 2019)
        tot_tm1_tmp = (t - tmn - 1) / (t - tmn) * dm_mode.array[:, idx_m[t], idx_m[tot_col], ...]\
                  + 1 / (t - tmn) * dm_mode.array[:, idx_m[tmn], idx_m[tot_col], ...]
        tot_tm1 = tot_tm1_tmp[..., np.newaxis] * dm_tech.array[:, idx_t[tmn], idx_t[tech_tot_col], ...]

        # Compute the year = t - round(1/RR(t-1)) = t - lifetime
        rr_tmn = dm_mode.array[:, idx_m[tmn], idx_m[rr_col], ...]
        tmlife = np.where(rr_tmn > 0, t - (1/rr_tmn).astype(int), startyear)
        tmlife[tmlife < startyear] = startyear  # do not allow years before start year
        # make sure future years fall on correct time spacing
        tmlife[tmlife > baseyear] = np.floor_divide(tmlife[tmlife > baseyear], step_fts) * step_fts
        # The tech share at tmlife corresponds to the tech share of waste at time t
        tech_share_waste_t = evaluate_at_tmlife(dm_tech, tmlife, tech_tot_col)
        eff_waste_t = evaluate_at_tmlife(dm_tech, tmlife, eff_tot_col)

        # Recompute waste by technology type
        waste_t = dm_mode.array[:, idx_m[t], idx_m[waste_col], :, np.newaxis] * tech_share_waste_t
        new_t = dm_tech.array[:, idx_t[t], idx_t[new_col], ...]
        # tot(t) = tot(t-1) + new(t) - waste(t)
        tot_t = tot_tm1 + new_t - waste_t

        # Deal with negative numbers
        mask = tot_t < 0
        tot_t[mask] = 0
        waste_t[mask] = tot_tm1[mask] + new_t[mask]

        # Compute efficiency (eff_tot_t is actually eff_tot_t*tot_t (following lines fix this)
        eff_tot_tmn = dm_tech.array[:, idx_t[tmn], idx_t[eff_tot_col], ...]
        eff_tot_t = (dm_tech.array[:, idx_t[tmn], idx_t[tot_col], ...] * eff_tot_tmn
                     + new_t * dm_tech.array[:, idx_t[t], idx_t[eff_new_col], ...]
                     - waste_t * eff_waste_t)

        mask = (tot_t == 0)
        # Re-compute the actual efficiency shares with the exception of when tot_t=0
        eff_tot_t[~mask] = eff_tot_t[~mask]/tot_t[~mask]
        eff_tot_t[mask] = eff_tot_tmn[mask]
        # Re-compute the actual technology shares at time t with the exception of when sum_tot_t = 0
        sum_tot_t = np.nansum(tot_t, axis=-1, keepdims=True)
        tech_tot_t = np.divide(tot_t, sum_tot_t, out=np.nan * np.ones_like(tot_t), where=sum_tot_t != 0)
        mask_tech = (np.isnan(tech_tot_t))
        tech_tot_tmp = dm_tech.array[:, idx_t[tmn], idx_t[tech_tot_col], ...]
        tech_tot_t[mask_tech] = tech_tot_tmp[mask_tech]
        # Update dm_mode for tot_t and waste_t
        dm_mode.array[:, idx_m[t], idx_m[tot_col], :] = np.nansum(tot_t, axis=-1)
        dm_mode.array[:, idx_m[t], idx_m[waste_col], :] = np.nansum(waste_t, axis=-1)
        # Update dm_tech for tot_t, waste_t, eff_tot_t, tech_tot_t
        dm_tech.array[:, idx_t[t], idx_t[tot_col], ...] = tot_t
        dm_tech.array[:, idx_t[t], idx_t[waste_col], ...] = waste_t
        dm_tech.array[:, idx_t[t], idx_t[eff_tot_col], ...] = eff_tot_t
        dm_tech.array[:, idx_t[t], idx_t[tech_tot_col], ...] = tech_tot_t
    return


def add_biofuel_efuel(dm_energy, dm_fuel_shares, mapping_cat):
    # Compute the biofuel and efuel from the demand of PHEV and ICE
    # and outputs them in a new dataframe together with the energy demand
    dm_energy_ICE_PHEV = dm_energy.filter_w_regex({'Categories2': 'PHEV.*|ICE.*'})
    idx_f = dm_fuel_shares.idx
    iter = 0
    for cat in mapping_cat.keys():
        # Filter categories in dm_all that correspond to the group category in dm_fuel_shares. e.g. road : LDV, 2W, bus etc
        # Biofuel
        dm_cat = dm_energy_ICE_PHEV.filter({'Categories1': mapping_cat[cat]})
        dm_biofuel_cat = dm_cat.copy()
        dm_biofuel_cat.array = dm_cat.array * dm_fuel_shares.array[:, :, 0, idx_f['biofuel'], idx_f[cat], np.newaxis, np.newaxis, np.newaxis]
        dm_biofuel_cat.col_labels['Categories2'] = [c + 'bio' for c in dm_biofuel_cat.col_labels['Categories2']]
        if iter == 0:
            dm_biofuel = dm_biofuel_cat.copy()
        else:
            dm_biofuel.append(dm_biofuel_cat, dim='Categories1')
        # Efuel
        dm_efuel_cat = dm_cat.copy()
        dm_efuel_cat.array = dm_cat.array * dm_fuel_shares.array[:, :, 0, idx_f['efuel'], idx_f[cat], np.newaxis, np.newaxis, np.newaxis]
        dm_efuel_cat.col_labels['Categories2'] = [c + 'efuel' for c in dm_efuel_cat.col_labels['Categories2']]
        if iter == 0:
            dm_efuel = dm_efuel_cat.copy()
        else:
            dm_efuel.append(dm_efuel_cat, dim='Categories1')
        iter = iter + 1

    # Add biofuel and efuel from standard fuel demand to avoid double counting
    dm_energy.append(dm_efuel, dim='Categories2')
    dm_energy.append(dm_biofuel, dim='Categories2')
    # Remove biofuel and efuel from standard fuel demand to avoid double counting
    idx_e = dm_energy.idx
    i = 0
    for c in dm_energy_ICE_PHEV.col_labels['Categories2']:
        dm_energy.array[..., idx_e[c]] = dm_energy.array[..., idx_e[c]] \
                                         - dm_efuel.array[..., i] \
                                         - dm_biofuel.array[..., i]
        i = i + 1


    return


def rename_and_group(dm_new_cat, groups, dict_end, grouped_var='tra_total-energy'):

    # Sum columns using the same fuel
    i = 0
    for fuel in groups:
        fuel_str = '.*' + fuel
        tmp = dm_new_cat.filter_w_regex({'Categories1': fuel_str})
        tmp_cat1 = np.nansum(tmp.array, axis=-1, keepdims=True)
        if i == 0:
            i = i+1
            array = tmp_cat1
        else:
            array = np.concatenate([array, tmp_cat1], axis=-1)
    dm_total_energy = DataMatrix(col_labels={'Country': dm_new_cat.col_labels['Country'],
                                             'Years': dm_new_cat.col_labels['Years'],
                                             'Variables': [grouped_var],
                                             'Categories1': groups},
                                 units={grouped_var: list(dm_new_cat.units.values())[0]})

    dm_total_energy.array = array

    for substring, replacement in dict_end.items():
        dm_new_cat.rename_col_regex(substring, replacement, dim='Categories1')
    for substring, replacement in dict_end.items():
        dm_total_energy.rename_col_regex(substring, replacement, dim='Categories1')

    dm_new_cat.deepen()
    for cat in dm_new_cat.col_labels['Categories2']:
        if '-' not in cat:
            dm_new_cat.rename_col(cat, 'none-'+cat, dim='Categories2')
    dm_new_cat.rename_col_regex('-', '_', dim='Categories2')
    dm_new_cat.deepen()

    return dm_total_energy


def passenger_fleet_energy(DM_passenger, DM_lfs, DM_other, cdm_const, years_setting):
    # Compute pkm demand by mode
    # dm_demand_by_mode [pkm] = modal_shares(urban) * demand_pkm(urban) + modal_shares(non-urban) * demand_pkm(non-urban)
    dm_modal_split = DM_passenger['passenger_modal_split']
    dm_lfs_demand = DM_lfs['lfs_passenger_demand']
    dm_demand_by_mode = compute_pkm_demand(dm_modal_split, dm_lfs_demand)
    del dm_modal_split, dm_lfs_demand
    # Remove walking and biking
    dm_demand_by_mode.drop(dim='Categories1', col_label='walk|bike')

    # Aviation pkm
    # demand_aviation [pkm] = demand aviation [pkm/cap] * pop
    dm_aviation_pkm = DM_passenger['passenger_aviation']
    dm_pop = DM_lfs['lfs_pop']
    tmp_aviation = dm_aviation_pkm.array[..., 0] * dm_pop.array[...]
    dm_demand_by_mode.add(tmp_aviation, dim='Categories1', col_label='aviation')
    del dm_aviation_pkm, tmp_aviation

    # Split between road and other passenger transport data
    dm_demand_road = dm_demand_by_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'LDV|bus|2W'})
    dm_demand_other = dm_demand_by_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'aviation|metrotram|rail'})

    dm_road = DM_passenger['passenger_mode_road']
    dm_road.append(dm_demand_road, dim='Variables')
    del dm_demand_road, dm_demand_by_mode

    # demand [vkm] = demand [pkm] / occupancy [pkm/vkm]
    dm_road.operation('tra_passenger_transport-demand', '/', 'tra_passenger_occupancy',
                      dim="Variables", out_col='tra_passenger_transport-demand-vkm', unit='vkm', div0="error")
    # vehicle-fleet [number] = demand [vkm] / utilisation-rate [vkm/veh/year]
    dm_road.operation('tra_passenger_transport-demand-vkm', '/', 'tra_passenger_utilisation-rate',
                      dim="Variables", out_col='tra_passenger_vehicle-fleet', unit='number', div0="error", type=int)
    # renewal-rate [%] = utilisation-rate [vkm/veh/year] /  vehicle-lifetime [years]
    dm_road.operation('tra_passenger_utilisation-rate', '/', 'tra_passenger_vehicle-lifetime',
                      dim="Variables", out_col='tra_passenger_renewal-rate', unit='%', div0="error")

    dm_other = DM_passenger['passenger_mode_other']
    dm_other.append(dm_demand_other, dim='Variables')
    del dm_demand_other

    # vehicle-fleet[number] = demand [pkm] / avg-pkm-by-veh [pkm/veh]
    dm_other.operation('tra_passenger_transport-demand', '/', 'tra_passenger_avg-pkm-by-veh',
                       dim="Variables", out_col='tra_passenger_vehicle-fleet', unit='number', div0="error", type=int)

    # Compute vehicle waste and new vehicles for both road and other
    dm_other_tmp = dm_other.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
    dm_mode = dm_road.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
    dm_other.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
    dm_road.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')

    dm_mode.append(dm_other_tmp, dim='Categories1')
    del dm_other_tmp

    dm_mode.sort(dim='Categories1')
    compute_stock(dm_mode, 'tra_passenger_renewal-rate', 'tra_passenger_vehicle-fleet',
                  waste_col='tra_passenger_vehicle-waste', new_col='tra_passenger_new-vehicles')

    # Compute fleet by technology type
    dm_tech = DM_passenger['passenger_tech']
    idx_t = dm_tech.index_all()
    idx_m = dm_mode.index_all()
    tmp_1 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_passenger_vehicle-fleet'], :, np.newaxis]
    tmp_2 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_passenger_vehicle-waste'], :, np.newaxis]
    tmp_3 = dm_tech.array[:, :, idx_t['tra_passenger_technology-share_new'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_passenger_new-vehicles'], :, np.newaxis]
    dm_tech.add(tmp_1, col_label='tra_passenger_vehicle-fleet', dim='Variables', unit='number')
    dm_tech.add(tmp_2, col_label='tra_passenger_vehicle-waste', dim='Variables', unit='number')
    dm_tech.add(tmp_3, col_label='tra_passenger_new-vehicles', dim='Variables', unit='number')
    del tmp_1, tmp_2, tmp_3
    #
    cols = {
        'renewal-rate': 'tra_passenger_renewal-rate',
        'tot': 'tra_passenger_vehicle-fleet',
        'waste': 'tra_passenger_vehicle-waste',
        'new': 'tra_passenger_new-vehicles',
        'tech_tot': 'tra_passenger_technology-share_fleet',
        'eff_tot': 'tra_passenger_veh-efficiency_fleet',
        'eff_new': 'tra_passenger_veh-efficiency_new'
    }
    compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting)

    # Extract passenger transport demand vkm for road and pkm for others, join and compute transport demand by technology
    dm_demand_km = dm_road.filter(selected_cols={'Variables': ['tra_passenger_transport-demand-vkm']})
    dm_demand_km_other = dm_other.filter(selected_cols={'Variables': ['tra_passenger_transport-demand']})
    dm_demand_km_other.units['tra_passenger_transport-demand'] = 'km'
    dm_demand_km.units['tra_passenger_transport-demand-vkm'] = 'km'
    dm_demand_km.rename_col('tra_passenger_transport-demand-vkm', 'tra_passenger_transport-demand', dim='Variables')
    dm_demand_km.append(dm_demand_km_other, dim='Categories1')
    dm_demand_km.sort(dim='Categories1')
    idx_t = dm_tech.index_all()
    tmp = dm_demand_km.array[:, :, 0, :, np.newaxis] \
          * dm_tech.array[:, :, idx_t['tra_passenger_technology-share_fleet'], ...]
    dm_tech.add(tmp, dim='Variables', col_label='tra_passenger_transport-demand', unit='km')
    del tmp, dm_demand_km, dm_demand_km_other
    # Compute energy consumption
    dm_tech.operation('tra_passenger_veh-efficiency_fleet', '*', 'tra_passenger_transport-demand',
                      out_col='tra_passenger_energy-demand', unit='MJ')

    # Add e-fuel and bio-fuel to energy consumption
    dm_fuel = DM_other['fuels']
    mapping_cat = {'road': ['LDV', '2W', 'rail', 'metrotram', 'bus'], 'aviation': ['aviation']}
    dm_energy = dm_tech.filter({'Variables': ['tra_passenger_energy-demand']})
    add_biofuel_efuel(dm_energy, dm_fuel, mapping_cat)

    # Deal with PHEV and electricity. For each mode of transport,
    # sum PHEV energy demand and multiply it by 0.1 to obtain a new category, the PHEV_elec
    dm_energy_phev = dm_energy.filter_w_regex({'Variables': 'tra_passenger_energy-demand', 'Categories2': 'PHEV.*'})
    PHEV_elec = 0.1 * np.nansum(dm_energy_phev.array, axis=-1)
    dm_energy.add(PHEV_elec, dim='Categories2', col_label='PHEV-elec')

    dm_energy.array = dm_energy.array*0.277778
    dm_energy.units['tra_passenger_energy-demand'] = 'TWh'

    # Prepare output for energy
    dm_electricity = dm_energy.groupby({'power-demand': ['BEV', 'CEV', 'PHEV-elec', 'mt']}, dim='Categories2')
    dm_electricity.groupby({'road': ['2W', 'bus', 'LDV'], 'rail': ['metrotram', 'rail'], 'other': ['aviation']},
                           dim='Categories1', inplace=True)
    dm_electricity.switch_categories_order()
    dm_electricity.rename_col('tra_passenger_energy-demand', 'tra', dim='Variables')
    dm_electricity = dm_electricity.flatten()
    dm_electricity = dm_electricity.flatten()
    dm_electricity.deepen()

    dm_efuel = dm_energy.groupby({'efuel': '.*efuel'}, dim='Categories2', regex=True)
    dm_efuel.groupby({'power-demand': '.*'}, dim='Categories1', inplace=True, regex=True)
    dm_efuel.rename_col('tra_passenger_energy-demand', 'tra', dim='Variables')
    dm_efuel = dm_efuel.flatten()
    dm_efuel = dm_efuel.flatten()
    dm_efuel.deepen()

    dm_electricity.append(dm_efuel, dim='Categories1')
    dm_electricity.array = dm_electricity.array/1000
    dm_electricity.units['tra_power-demand'] = 'GWh'

    DM_passenger_out = {
        'power': {'electricity': dm_electricity.flatten()},
    }
    # end energy output

    dict1 = {'FCEV': 'FCV-hydrogen', 'BEV': 'BEV-elec', 'CEV': 'CEV-elec', 'metrotram_mt': 'metrotram_elec',
             'aviation_ICEefuel': 'aviation_ejetfuel', 'aviation_ICEbio': 'aviation_biojetfuel',
             'aviation_ICE': 'aviation_kerosene', 'PHEVbio': 'dieselbio', 'PHEVefuel': 'dieselefuel'}

    dm_energy_new_cat = dm_energy.flatten()
    # Rename the columns based on the substring mapping
    for substring, replacement in dict1.items():
        dm_energy_new_cat.rename_col_regex(substring, replacement, dim='Categories1')
    dm_energy_new_cat.rename_col('2W_PHEV', '2W_diesel', dim='Categories1')

    grouping = ['dieselbio', 'gasolinebio', 'gasbio', 'gasoline', 'diesel', 'gas', 'dieselefuel', 'gasolineefuel',
                'gasefuel', 'hydrogen', "elec", 'biojetfuel', 'kerosene', 'ejetfuel']
    dict2 = {'dieselbio': 'biodiesel', 'gasolinebio': 'bioethanol', 'gasbio': 'biogas', 'dieselefuel': 'ediesel',
             'gasolineefuel': 'egasoline', 'gasefuel': 'egas', 'elec': 'electricity'}

    dm_tot_energy = rename_and_group(dm_energy_new_cat, grouping, dict2, grouped_var='tra_passenger_total-energy')

    # Power output
    dm_pow_hydrogen = dm_tot_energy.filter({'Categories1': ['hydrogen']})
    dm_pow_hydrogen.rename_col('tra_passenger_total-energy', 'tra_power-demand', dim='Variables')
    dm_pow_hydrogen.array = dm_pow_hydrogen.array/1000
    dm_pow_hydrogen.units['tra_power-demand'] = 'GWh'
    DM_passenger_out['power']['hydrogen'] = dm_pow_hydrogen.flatten()

    DM_passenger_out['oil-refinery'] = dm_tot_energy.filter({'Categories1': ['gasoline', 'diesel', 'gas', 'kerosene']})

    dm_biogas = dm_tot_energy.filter({'Categories1': ['biogas']})

    # Compute emission by fuel
    # Filter fuels for which we have emissions
    cdm_const.drop(col_label='marinefueloil', dim='Categories2')
    dm_energy_em = dm_tot_energy.filter({'Categories1': cdm_const.col_labels['Categories2']})
    # Sort categories to make sure they match
    dm_energy_em.sort(dim='Categories1')
    cdm_const.sort(dim='Categories2')
    idx_e = dm_energy_em.idx
    idx_c = cdm_const.idx
    # emissions = energy * emission-factor
    tmp = dm_energy_em.array[:, :, idx_e['tra_passenger_total-energy'], np.newaxis, :] \
          * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], :, :]
    tmp = np.moveaxis(tmp, -2, -1)
    # Save emissions by fuel in a datamatrix
    col_labels = dm_energy_em.col_labels.copy()
    col_labels['Variables'] = ['tra_passenger_emissions']
    col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
    unit = {'tra_passenger_emissions': 'Mt'}
    dm_emissions_by_fuel = DataMatrix(col_labels=col_labels, units=unit)
    dm_emissions_by_fuel.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
    del dm_energy_em, tmp, col_labels, unit

    # Compute emissions by mode
    dm_energy_em = dm_energy_new_cat.filter({'Categories3': cdm_const.col_labels['Categories2']})
    dm_energy_em.sort(dim='Categories3')
    cdm_const.sort(dim='Categories2')
    idx_e = dm_energy_em.idx
    idx_c = cdm_const.idx
    tmp_en = np.nansum(dm_energy_em.array, axis=-2)  # remove technology split
    tmp = tmp_en[:, :, idx_e['tra_passenger_energy-demand'], :, np.newaxis, :] \
          * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], np.newaxis, :, :]
    tmp = np.nansum(tmp, axis=-1)  # Remove split by fuel
    col_labels = dm_energy_em.col_labels.copy()
    col_labels.pop('Categories3')
    col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
    col_labels['Variables'] = ['tra_passenger_emissions']
    unit = {'tra_passenger_emissions': 'Mt'}
    dm_emissions_by_mode = DataMatrix(col_labels=col_labels, units=unit)
    dm_emissions_by_mode.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
    del tmp, unit, col_labels, idx_e, idx_c, tmp_en, dm_energy_em

    # Group emissions by GHG gas
    tmp = np.nansum(dm_emissions_by_mode.array, axis=-2)
    col_labels = dm_emissions_by_mode.col_labels.copy()
    col_labels['Categories1'] = col_labels['Categories2'].copy()
    col_labels.pop('Categories2')
    unit = dm_emissions_by_mode.units
    dm_emissions_by_GHG = DataMatrix(col_labels=col_labels, units=unit)
    dm_emissions_by_GHG.array = tmp[:, :, np.newaxis, :]
    del tmp, unit, col_labels

    tmp = np.nansum(dm_energy.array, axis=(-1,-2))
    col_labels = dm_energy.col_labels.copy()
    col_labels.pop('Categories1')
    col_labels.pop('Categories2')
    dm_no_cat = DataMatrix(col_labels=col_labels, units=dm_energy.units.copy())
    dm_no_cat.array = tmp[:, :, np.newaxis]

    dm_tech.rename_col('tra_passenger_technology-share_fleet', 'tra_passenger_technology-share-fleet', dim='Variables')

    idx = dm_tech.idx
    tmp = np.nansum(dm_tech.array[:, :, idx['tra_passenger_transport-demand'], :, :], axis=-1)
    dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_transport-demand-by-mode', unit='pkm')

    # Compute passenger demand by mode
    idx = dm_energy.idx
    tmp = np.nansum(dm_energy.array[:, :, idx['tra_passenger_energy-demand'], :, :], axis=-1)
    dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_energy-demand-by-mode', unit='TWh')

    # Compute CO2 emissions by mode
    idx = dm_emissions_by_mode.idx
    tmp = dm_emissions_by_mode.array[:, :, idx['tra_passenger_emissions'], :, idx['CO2']]
    dm_mode.add(tmp, dim='Variables', col_label='tra_passenger_emissions-by-mode_CO2', unit='Mt')

    dm_tot_energy.rename_col(col_in='tra_passenger_total-energy', col_out='tra_passenger_energy-demand-by-fuel', dim='Variables')

    DM_passenger_out['mode'] = dm_mode
    DM_passenger_out['tech'] = dm_tech
    DM_passenger_out['fuel'] = dm_fuel
    DM_passenger_out['agriculture'] = dm_biogas
    DM_passenger_out['emissions'] = dm_emissions_by_mode

    return DM_passenger_out


def freight_fleet_energy(DM_freight, DM_other, cdm_const, years_setting):
    # FREIGHT
    dm_tkm = DM_freight['freight_demand']
    dm_mode = DM_freight['freight_modal_split']
    # From bn tkm to tkm by mode of transport
    tmp = dm_tkm.array[:, :, 0, np.newaxis] * 1e9 * dm_mode.array[:, :, 0, :]
    dm_mode.add(tmp, dim='Variables', col_label='tra_freight_transport-demand', unit='tkm')

    dm_mode_road = DM_freight['freight_mode_road']
    dm_mode_road.append(dm_mode.filter_w_regex(dict_dim_pattern={'Categories1': 'HDV.*'}), dim='Variables')
    dm_mode_road.operation('tra_freight_transport-demand', '/', 'tra_freight_load-factor',
                           out_col='tra_freight_transport-demand-vkm', unit='vkm')
    dm_mode_road.operation('tra_freight_transport-demand-vkm', '/', 'tra_freight_utilisation-rate',
                           out_col='tra_freight_vehicle-fleet', unit='number')
    dm_mode_road.operation('tra_freight_utilisation-rate', '/', 'tra_freight_lifetime',
                           out_col='tra_freight_renewal-rate', unit='%')

    dm_mode_other = DM_freight['freight_mode_other']
    dm_mode_other.append(dm_mode.filter({'Categories1': ['IWW', 'marine', 'aviation', 'rail']}), dim='Variables')
    dm_mode_other.operation('tra_freight_transport-demand', '/', 'tra_freight_tkm-by-veh',
                            out_col='tra_freight_vehicle-fleet', unit='number')

    # Compute vehicle waste and new vehicles for both road and other
    dm_other_tmp = dm_mode_other.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
    dm_road_tmp = dm_mode_road.filter_w_regex(dict_dim_pattern={'Variables': '.*vehicle-fleet|.*renewal-rate'})
    dm_mode_other.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
    dm_mode_road.drop(dim='Variables', col_label='.*vehicle-fleet|.*renewal-rate')
    dm_road_tmp.append(dm_other_tmp, dim='Categories1')
    dm_mode.append(dm_road_tmp, dim='Variables')
    del dm_road_tmp, dm_other_tmp

    compute_stock(dm_mode, rr_regex='tra_freight_renewal-rate', tot_regex='tra_freight_vehicle-fleet',
                  waste_col='tra_freight_vehicle-waste', new_col='tra_freight_new-vehicles')

    # Compute fleet by technology type
    dm_tech = DM_freight['freight_tech']
    idx_t = dm_tech.index_all()
    idx_m = dm_mode.index_all()
    tmp_1 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_freight_vehicle-fleet'], :, np.newaxis]
    tmp_2 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_freight_vehicle-waste'], :, np.newaxis]
    tmp_3 = dm_tech.array[:, :, idx_t['tra_freight_technology-share_new'], :, :] \
            * dm_mode.array[:, :, idx_m['tra_freight_new-vehicles'], :, np.newaxis]
    dm_tech.add(tmp_1, col_label='tra_freight_vehicle-fleet', dim='Variables', unit='number')
    dm_tech.add(tmp_2, col_label='tra_freight_vehicle-waste', dim='Variables', unit='number')
    dm_tech.add(tmp_3, col_label='tra_freight_new-vehicles', dim='Variables', unit='number')
    del tmp_1, tmp_2, tmp_3
    #
    cols = {
        'renewal-rate': 'tra_freight_renewal-rate',
        'tot': 'tra_freight_vehicle-fleet',
        'waste': 'tra_freight_vehicle-waste',
        'new': 'tra_freight_new-vehicles',
        'tech_tot': 'tra_freight_technology-share_fleet',
        'eff_tot': 'tra_freight_vehicle-efficiency_fleet',
        'eff_new': 'tra_freight_vehicle-efficiency_new'
    }
    compute_fts_tech_split(dm_mode, dm_tech, cols, years_setting)

    # Extract freight transport demand vkm for road and tkm for others, join and compute transport demand by technology
    dm_demand_km = dm_mode_road.filter(selected_cols={'Variables': ['tra_freight_transport-demand-vkm']})
    dm_demand_km_other = dm_mode_other.filter(selected_cols={'Variables': ['tra_freight_transport-demand']})
    dm_demand_km_other.units['tra_freight_transport-demand'] = 'km'
    dm_demand_km.units['tra_freight_transport-demand-vkm'] = 'km'
    dm_demand_km.rename_col('tra_freight_transport-demand-vkm', 'tra_freight_transport-demand', dim='Variables')
    dm_demand_km.append(dm_demand_km_other, dim='Categories1')
    dm_demand_km.sort(dim='Categories1')
    idx_t = dm_tech.index_all()
    tmp = dm_demand_km.array[:, :, 0, :, np.newaxis] \
          * dm_tech.array[:, :, idx_t['tra_freight_technology-share_fleet'], ...]
    dm_tech.add(tmp, dim='Variables', col_label='tra_freight_transport-demand', unit='km')
    del tmp, dm_demand_km, dm_demand_km_other
    # Compute energy consumption
    dm_tech.operation('tra_freight_vehicle-efficiency_fleet', '*', 'tra_freight_transport-demand',
                      out_col='tra_freight_energy-demand', unit='MJ')

    # Compute biofuel and efuel and extract energy as standalone dm
    dm_fuel = DM_other['fuels']
    mapping_cat = {
        'road': ['HDVH', 'HDVM', 'HDVL'],
        'aviation': ['aviation'],
        'rail': ['rail'],
        'marine': ['IWW', 'marine']
    }
    dm_energy = dm_tech.filter({'Variables': ['tra_freight_energy-demand']})
    add_biofuel_efuel(dm_energy, dm_fuel, mapping_cat)

    # Deal with PHEV and electricity. For each mode of transport,
    # sum PHEV energy demand and multiply it by 0.1 to obtain a new category, the PHEV_elec
    dm_energy_phev = dm_energy.filter_w_regex({'Variables': 'tra_freight_energy-demand', 'Categories2': 'PHEV.*'})
    PHEV_elec = 0.1 * np.nansum(dm_energy_phev.array, axis=-1)
    dm_energy.add(PHEV_elec, dim='Categories2', col_label='PHEV-elec')

    dm_energy.array = dm_energy.array*0.277778
    dm_energy.units['tra_freight_energy-demand'] = 'TWh'

    # Prepare output for energy
    dm_electricity = dm_energy.groupby({'power-demand': ['BEV', 'CEV', 'PHEV-elec']}, dim='Categories2')
    dm_electricity.groupby({'road': ['HDVH', 'HDVL', 'HDVM'], 'rail': ['rail'], 'other': ['aviation', 'marine', 'IWW']},
                           dim='Categories1', inplace=True)
    dm_electricity.switch_categories_order()
    dm_electricity.rename_col('tra_freight_energy-demand', 'tra', dim='Variables')
    dm_electricity = dm_electricity.flatten()
    dm_electricity = dm_electricity.flatten()
    dm_electricity.deepen()

    dm_efuel = dm_energy.groupby({'efuel': '.*efuel'}, dim='Categories2', regex=True)
    dm_efuel.groupby({'power-demand': '.*'}, dim='Categories1', inplace=True, regex=True)
    dm_efuel.rename_col('tra_freight_energy-demand', 'tra', dim='Variables')
    dm_efuel = dm_efuel.flatten()
    dm_efuel = dm_efuel.flatten()
    dm_efuel.deepen()

    dm_electricity.append(dm_efuel, dim='Categories1')
    dm_electricity.array = dm_electricity.array/1000
    dm_electricity.units['tra_power-demand'] = 'GWh'

    DM_freight_out = {
        'power': {'electricity': dm_electricity.flatten()},
    }
    ## end

    dict1 = {'FCEV': 'FCV-hydrogen', 'BEV': 'BEV-elec', 'CEV': 'CEV-elec',
             'aviation_ICEefuel': 'aviation_ejetfuel', 'aviation_ICEbio': 'aviation_biojetfuel',
             'aviation_ICE': 'aviation_kerosene'}

    dm_energy_new_cat = dm_energy.flatten()
    # Rename the columns based on the substring mapping
    for substring, replacement in dict1.items():
        dm_energy_new_cat.rename_col_regex(substring, replacement, dim='Categories1')

    grouping = ['dieselbio', 'gasolinebio', 'gasbio', 'gasoline', 'diesel', 'gas', 'dieselefuel', 'gasolineefuel',
                'gasefuel', 'hydrogen', "elec", "ICEbio", "ICEefuel", "ICE", 'biojetfuel', 'kerosene', 'ejetfuel']

    dict2 = {'dieselbio': 'biodiesel', 'gasolinebio': 'bioethanol', 'gasbio': 'biogas',
             'dieselefuel': 'ediesel', 'gasolineefuel': 'egasoline', 'gasefuel': 'egas', 'elec': 'electricity',
             'ICEbio': 'biomarinefueloil', 'ICEefuel': 'emarinefueloil', 'IWW_ICE': 'IWW_marinefueloil',
             'marine_ICE': 'marine_marinefueloil'}

    dm_total_energy = rename_and_group(dm_energy_new_cat, grouping, dict2, grouped_var='tra_freight_total-energy')
    dm_total_energy.rename_col('ICE', 'marinefueloil', dim='Categories1')

    # Output to power:
    dm_pow_hydrogen = dm_total_energy.filter({'Categories1': ['hydrogen']})
    dm_pow_hydrogen.rename_col('tra_freight_total-energy', 'tra_power-demand', dim='Variables')
    dm_pow_hydrogen.array = dm_pow_hydrogen.array/1000
    dm_pow_hydrogen.units['tra_power-demand'] = 'GWh'
    DM_freight_out['power']['hydrogen'] = dm_pow_hydrogen.flatten()

    # Prepare output to refinery:
    DM_freight_out['oil-refinery'] = dm_total_energy.filter({'Categories1': ['gasoline', 'diesel', 'marinefueloil', 'gas', 'kerosene']})

    dm_biogas = dm_total_energy.filter({'Categories1': ['biogas']})

    # Compute emission by fuel
    # Filter fuels for which we have emissions
    dm_energy_em = dm_total_energy.filter({'Categories1': cdm_const.col_labels['Categories2']})
    # Sort categories to make sure they match
    dm_energy_em.sort(dim='Categories1')
    cdm_const.sort(dim='Categories2')
    idx_e = dm_energy_em.idx
    idx_c = cdm_const.idx
    # emissions = energy * emission-factor
    tmp = dm_energy_em.array[:, :, idx_e['tra_freight_total-energy'], np.newaxis, :] \
          * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], :, :]
    tmp = np.moveaxis(tmp, -2, -1)
    # Save emissions by fuel in a datamatrix
    col_labels = dm_energy_em.col_labels.copy()
    col_labels['Variables'] = ['tra_freight_emissions']
    col_labels['Categories2'] = cdm_const.col_labels['Categories1'].copy()  # GHG category
    unit = {'tra_freight_emissions': 'Mt'}
    dm_emissions_by_fuel = DataMatrix(col_labels=col_labels, units=unit)
    dm_emissions_by_fuel.array = tmp[:, :, np.newaxis, :, :]  # The variable dimension was lost when doing nansum
    del dm_energy_em, tmp, col_labels, unit

    # Compute emissions by mode
    dm_energy_em = dm_energy_new_cat.filter({'Categories3': cdm_const.col_labels['Categories2']})
    dm_energy_em.sort(dim='Categories3')
    cdm_const.sort(dim='Categories2')
    idx_e = dm_energy_em.idx
    idx_c = cdm_const.idx
    tmp_en = np.nansum(dm_energy_em.array, axis=-2)  # remove technology split
    tmp = tmp_en[:, :, idx_e['tra_freight_energy-demand'], :, np.newaxis, :] \
          * cdm_const.array[np.newaxis, np.newaxis, idx_c['cp_tra_emission-factor'], np.newaxis, :, :]
    tmp = np.nansum(tmp, axis=-1)  # Remove split by fuel
    tmp = tmp[:, :, np.newaxis, :, :]
    dm_emissions_by_mode = DataMatrix.based_on(tmp, format=dm_energy_em,
                                               change={'Variables': ['tra_freight_emissions'],
                                                       'Categories2': cdm_const.col_labels['Categories1'],
                                                       'Categories3': None}, units={'tra_freight_emissions': 'Mt'})
    del tmp, idx_e, idx_c, tmp_en, dm_energy_em

    tmp = np.nansum(dm_emissions_by_mode.array, axis=-2)
    col_labels = dm_emissions_by_mode.col_labels.copy()
    col_labels['Categories1'] = col_labels['Categories2'].copy()
    col_labels.pop('Categories2')
    unit = dm_emissions_by_mode.units
    dm_emissions_by_GHG = DataMatrix(col_labels=col_labels, units=unit)
    dm_emissions_by_GHG.array = tmp[:, :, np.newaxis, :]
    del tmp, unit, col_labels

    tmp = np.nansum(dm_energy.array, axis=(-1, -2))
    col_labels = dm_energy.col_labels.copy()
    col_labels.pop('Categories1')
    col_labels.pop('Categories2')
    dm_no_cat = DataMatrix(col_labels=col_labels, units=dm_energy.units.copy())
    dm_no_cat.array = tmp[:, :, np.newaxis]

    dm_tech.rename_col('tra_freight_technology-share_fleet', 'tra_freight_techology-share-fleet', dim='Variables')

    DM_freight_out['mode'] = dm_mode
    DM_freight_out['tech'] = dm_tech
    DM_freight_out['energy'] = dm_energy
    DM_freight_out['agriculture'] = dm_biogas
    DM_freight_out['emissions'] = dm_emissions_by_mode

    return DM_freight_out


def tra_industry_interface(dm_freight_new_veh, dm_passenger_new_veh, dm_infrastructure):
    # Filter cars only and rename technology as ICE, FCV and EV
    dm_cars = dm_passenger_new_veh.filter({'Categories1': ['LDV']})
    dm_cars.group_all(dim='Categories1', inplace=True)
    dm_cars.groupby({'cars-ICE': 'ICE.*|PHEV.*', 'cars-FCV': 'FCEV', 'cars-EV': 'BEV'}, dim='Categories1', regex=True, inplace=True)
    dm_cars.drop(dim='Categories1', col_label=['CEV', 'mt'])   # these are 0 for cars empty
    dm_cars.rename_col('tra_passenger_new-vehicles', 'tra_product-demand', dim='Variables')

    # Filter trucks only and rename technologies as ICE, FCV, EV
    dm_trucks = dm_freight_new_veh.filter({'Categories1': ['HDVH', 'HDVL', 'HDVM']})
    dm_trucks.group_all(dim='Categories1')
    dm_trucks.groupby({'trucks-ICE': 'ICE.*|PHEV.*', 'trucks-FCV': 'FCEV', 'trucks-EV': 'BEV|CEV'}, dim='Categories1', regex=True, inplace=True)
    dm_trucks.rename_col('tra_freight_new-vehicles', 'tra_product-demand', dim='Variables')

    # Compute new-vehicles for aviation, marine, rail
    dm_freight_new_veh.group_all(dim='Categories2')  # drop fuel split
    dm_passenger_new_veh.group_all(dim='Categories2')  # drop fuel split
    dm_passenger_new_veh.add(0, dim='Categories1', col_label=['marine'], dummy=True)  # add dummy 'marine' to passenger
    dm_freight_new_veh.filter({'Categories1': ['aviation', 'marine', 'rail']}, inplace=True)  # keep only rail, aviation, marine
    dm_passenger_new_veh.filter({'Categories1': ['aviation', 'marine', 'rail']}, inplace=True)  # keep only rail, aviation, marine
    dm_product_demand = dm_passenger_new_veh
    dm_product_demand.append(dm_freight_new_veh, dim='Variables')  # merge passenger and freight
    dm_product_demand.groupby({'tra_product-demand': '.*'}, dim='Variables', regex=True, inplace=True)
    # Rename aviation, marine, rail to planes, ships, trains
    dm_product_demand.rename_col(['aviation', 'marine', 'rail'], ['planes', 'ships', 'trains'], dim='Categories1')


    # Append cars and trucks
    dm_product_demand.append(dm_cars, dim='Categories1')
    dm_product_demand.append(dm_trucks, dim='Categories1')

    dm_product_demand.sort(dim='Categories1')

    dm_infra_ind = dm_infrastructure.copy()
    dm_infra_ind.rename_col_regex('infra-', '', dim='Categories1')
    dm_infra_ind.rename_col('tra_new_infrastructure', 'tra_product-demand', dim='Variables')

    # ! FIXME add infrastructure in km
    DM_industry = {
        'tra-veh': dm_product_demand,
        'tra-infra': dm_infra_ind
    }
    return DM_industry


def tra_minerals_interface(dm_freight_new_veh, dm_passenger_new_veh, DM_industry, dm_infrastructure, write_xls=False):

    # Group technologies as PHEV, ICE, EV and FCEV
    dm_freight_new_veh.groupby({'PHEV': 'PHEV.*', 'ICE': 'ICE.*', 'EV': 'BEV|CEV'}, regex=True, inplace=True, dim='Categories2')
    # note that mt is later dropped
    dm_passenger_new_veh.groupby({'PHEV': 'PHEV.*', 'ICE': 'ICE.*', 'EV': 'BEV|CEV|mt'}, regex=True, inplace=True, dim='Categories2')
    # keep only certain vehicles
    keep_veh = 'HDV.*|2W|LDV|bus'
    dm_keep_new_veh = dm_passenger_new_veh.filter_w_regex({'Categories1': keep_veh})
    dm_keep_new_veh.rename_col('tra_passenger_new-vehicles', 'tra_product-demand', dim='Variables')
    dm_keep_freight_new_veh = dm_freight_new_veh.filter_w_regex({'Categories1': keep_veh})
    dm_keep_freight_new_veh.rename_col('tra_freight_new-vehicles', 'tra_product-demand', dim='Variables')
    # join passenger and freight
    dm_keep_new_veh.append(dm_keep_freight_new_veh, dim='Categories1')
    # flatten to obtain e.g. LDV-EV or HDVL-FCEV
    dm_keep_new_veh = dm_keep_new_veh.flatten()
    dm_keep_new_veh.rename_col_regex('_', '-', 'Categories1')

    dm_other = DM_industry['tra-veh'].filter({'Categories1': ['planes', 'ships', 'trains']})
    dm_other.groupby({'other-planes': ['planes'], 'other-ships': ['ships'], 'other-trains': ['trains']}, dim='Categories1', inplace=True)

    dm_keep_new_veh.append(dm_other, dim='Categories1')
    dm_keep_new_veh.rename_col('tra_product-demand', 'product-demand', dim='Variables')

    DM_minerals = {
        'tra_veh': dm_keep_new_veh,
        'tra_infra': dm_infrastructure
    }

    if write_xls:
        df1 = DM_minerals['tra_veh'].write_df()
        df2 = DM_minerals['tra_infra'].write_df()
        df = pd.concat([df1, df2.drop(columns=['Country', 'Years'])], axis=1)
        df.to_excel('../_database/data/xls/All-Countries-interface_from-transport-to-minerals.xlsx', index=False)

    return DM_minerals

def tra_oilrefinery_interface(dm_pass_energy, dm_freight_energy):

    dm_pass_energy.add(0, dummy=True, col_label='marinefueloil', dim='Categories1')
    dm_pass_energy.append(dm_freight_energy, dim='Variables')
    dm_tot_energy = dm_pass_energy.groupby({'tra_energy-demand': '.*'}, dim='Variables', inplace=False, regex=True)
    dict_rename = {'diesel': 'liquid-ff-diesel', 'marinefueloil': 'liquid-ff-fuel-oil', 'gasoline': 'liquid-ff-gasoline',
                   'gas': 'gas-ff-natural', 'kerosene': 'liquid-ff-kerosene'}
    for str_old, str_new in dict_rename.items():
        dm_tot_energy.rename_col(str_old, str_new, dim='Categories1')

    return dm_tot_energy


def prepare_TPE_output(DM_passenger_out, DM_freight_out):

    dm_keep_mode = DM_passenger_out['mode'].filter({'Variables': ['tra_passenger_transport-demand-by-mode',
                                                                  'tra_passenger_energy-demand-by-mode',
                                                                  'tra_passenger_emissions-by-mode_CO2']})

    dm_keep_tech = DM_passenger_out['tech'].filter({'Variables': ['tra_passenger_technology-share-fleet']})

    dm_keep_fuel = DM_passenger_out['fuel']

    # Turn datamatrix to dataframe (because converter and TPE work with dataframes)
    df = dm_keep_mode.write_df()
    df2 = dm_keep_tech.write_df()
    df = pd.concat([df, df2.drop(columns=['Country', 'Years'])], axis=1)
    df3 = dm_keep_fuel.write_df()
    df = pd.concat([df, df3.drop(columns=['Country', 'Years'])], axis=1)

    # Dummy variable
    dm_energy_tot = DM_passenger_out['mode'].filter({'Variables': ['tra_passenger_energy-demand-by-mode']})
    dm_energy_tot.group_all(dim='Categories1')
    dm_energy_freight = DM_freight_out['energy'].copy()
    dm_energy_freight.group_all(dim='Categories2')
    dm_energy_freight.group_all(dim='Categories1')
    dm_energy_tot.append(dm_energy_freight, dim='Variables')
    dm_energy_tot.operation('tra_passenger_energy-demand-by-mode', '+', 'tra_freight_energy-demand',
                            out_col='tra_energy-demand_total', unit='TWh')
    dm_energy_tot.filter({'Variables': ['tra_energy-demand_total']}, inplace=True)
    df4 = dm_energy_tot.write_df()
    df = pd.concat([df, df4.drop(columns=['Country', 'Years'])], axis=1)

    return df


# !FIXME: infrastructure dummy not OK, find real tot infrastructure data and real renewal-rates or new-infrastructure
def dummy_tra_infrastructure_workflow(dm_pop):

    # Industry and Minerals need the new infrastructure in km for rails, roads, and trolley-cables
    # In order to compute the new infrastructure we need the tot infrastructure and a renewal-rate
    # tot_infrastructure = Looking at Swiss data it looks like there are around 10 m of road per capita
    # (Longueurs des routes nationales, cantonales et des autres routes ouvertes aux véhicules à moteur selon le canton)
    # and 0.6 m of rail per capita and 0.0017 of trolley-bus, I'm using this approximation for all countries
    # for the renewal rate eucalc was using 5%, which correspond to a resurfacing every 20 years. I use this for road
    # for rails I use 2.5% (40 years lifetime). For the wires I have no idea,
    # I'm going with 25 that seem to be the rewiring span of electrical cables (rr = 4%)
    # I'm using the stock function to compute the new km and the 'waste' km

    ay_infra_road = dm_pop.array * 10 / 1000  # road infrastructure in km
    ay_infra_rail = dm_pop.array * 0.6 / 1000  # rail infrastructure in km
    ay_infra_trolleybus = dm_pop.array * 0.0017 / 1000  # rail infrastructure in km

    ay_tot = np.concatenate((ay_infra_rail, ay_infra_road, ay_infra_trolleybus), axis=-1)

    dm_infra = DataMatrix.based_on(ay_tot[:, :, np.newaxis, :], format=dm_pop,
                                   change={'Variables': ['tra_tot-infrastructure'],
                                           'Categories1': ['infra-rail', 'infra-road', 'infra-trolley-cables']},
                                   units={'tra_tot-infrastructure': 'km'})
    # Add dummy renewal rates
    dm_infra.add(0, dummy=True, dim='Variables', col_label='tra_renewal-rate', unit='%')
    idx = dm_infra.idx
    dm_infra.array[:, :, idx['tra_renewal-rate'], idx['infra-road']] = 0.05
    dm_infra.array[:, :, idx['tra_renewal-rate'], idx['infra-rail']] = 0.025
    dm_infra.array[:, :, idx['tra_renewal-rate'], idx['infra-trolley-cables']] = 0.04

    compute_stock(dm_infra, 'tra_renewal-rate', 'tra_tot-infrastructure',
                  waste_col='tra_infrastructure_waste', new_col='tra_new_infrastructure')

    return dm_infra.filter({'Variables': ['tra_new_infrastructure']})


def tra_emissions_interface(dm_pass_emissions, dm_freight_emissions, write_xls=False):

    dm_pass_emissions.rename_col('tra_passenger_emissions', 'tra_emissions_passenger', dim='Variables')
    dm_pass_emissions = dm_pass_emissions.flatten().flatten()
    dm_freight_emissions.rename_col('tra_freight_emissions', 'tra_emissions_freight', dim='Variables')
    dm_freight_emissions = dm_freight_emissions.flatten().flatten()

    dm_pass_emissions.append(dm_freight_emissions, dim='Variables')

    if write_xls:
        df = dm_pass_emissions.write_df()
        df.to_excel('../_database/data/xls/All-Countries-interface_from-transport-to-emissions.xlsx', index=False)

    return dm_pass_emissions


def transport(lever_setting, years_setting, interface=Interface()):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    transport_data_file = os.path.join(current_file_directory, '../_database/data/datamatrix/geoscale/transport.pickle')
    DM_passenger, DM_freight, DM_other, cdm_const = read_data(transport_data_file, lever_setting)

    cntr_list = DM_passenger['passenger_modal_split'].col_labels['Country']

    # If the input from lifestyles are available in the interface, read them, else read from xls
    if interface.has_link(from_sector='lifestyles', to_sector='transport'):
        DM_lfs = interface.get_link(from_sector='lifestyles', to_sector='transport')
    else:
        if len(interface.list_link()) != 0:
            print('You are missing lifestyles to oil-refinery interface')
        DM_lfs = simulate_lifestyles_input()
        for key in DM_lfs.keys():
            DM_lfs[key] = DM_lfs[key].filter({'Country': cntr_list})

    # PASSENGER
    cdm_const_passenger = cdm_const.copy()
    DM_passenger_out = passenger_fleet_energy(DM_passenger, DM_lfs, DM_other, cdm_const_passenger, years_setting)
    # FREIGHT
    cdm_const_freight = cdm_const.copy()
    DM_freight_out = freight_fleet_energy(DM_freight, DM_other, cdm_const_freight, years_setting)

    results_run = prepare_TPE_output(DM_passenger_out, DM_freight_out)

    # Power-module
    DM_power = DM_passenger_out['power']
    DM_power['hydrogen'].array = DM_power['hydrogen'].array + DM_freight_out['power']['hydrogen'].array
    DM_power['electricity'].array = DM_power['electricity'].array + DM_freight_out['power']['electricity'].array
    interface.add_link(from_sector='transport', to_sector='power', dm=DM_power)
    # df = dm_power.write_df()
    # df.to_excel('transport-to-power.xlsx', index=False)

    # Storage-module
    dm_oil_refinery = tra_oilrefinery_interface(DM_passenger_out['oil-refinery'], DM_freight_out['oil-refinery'])
    interface.add_link(from_sector='transport', to_sector='oil-refinery', dm=dm_oil_refinery)

    # Agriculture-module
    # !FIXME: of all of the bio-energy demand, only the biogas one is accounted for in Agriculture
    dm_agriculture = DM_freight_out['agriculture']
    dm_agriculture.array = dm_agriculture.array + DM_passenger_out['agriculture'].array
    dm_agriculture.rename_col('tra_freight_total-energy', 'tra_bioenergy', dim='Variables')
    dm_agriculture.rename_col('biogas', 'gas', dim='Categories1')
    interface.add_link(from_sector='transport', to_sector='agriculture', dm=dm_agriculture)

    # Minerals and Industry
    dm_freight_new_veh = DM_freight_out['tech'].filter({'Variables': ['tra_freight_new-vehicles']})
    dm_passenger_new_veh = DM_passenger_out['tech'].filter({'Variables': ['tra_passenger_new-vehicles']})
    dm_infrastructure = dummy_tra_infrastructure_workflow(DM_lfs['lfs_pop'])
    DM_industry = tra_industry_interface(dm_freight_new_veh.copy(), dm_passenger_new_veh.copy(), dm_infrastructure)
    DM_minerals = tra_minerals_interface(dm_freight_new_veh, dm_passenger_new_veh, DM_industry, dm_infrastructure, write_xls=False)
    # !FIXME: add km infrastructure data, using compute_stock with tot_km and renovation rate as input.
    #  data for ch ok, data for eu, backcalculation? dummy based on swiss pop?
    interface.add_link(from_sector='transport', to_sector='industry', dm=DM_industry)
    interface.add_link(from_sector='transport', to_sector='minerals', dm=DM_minerals)

    # Emissions
    dm_emissions = tra_emissions_interface(DM_passenger_out['emissions'], DM_freight_out['emissions'], write_xls=False)
    interface.add_link(from_sector='transport', to_sector='emissions', dm=dm_emissions)
    return results_run


def local_transport_run():
    # Function to run only transport module without converter and tpe
    years_setting = [1990, 2015, 2050, 5]
    f = open('../config/lever_position.json')
    lever_setting = json.load(f)[0]

    global_vars = {'geoscale': '.*'}
    filter_geoscale(global_vars)

    results_run = transport(lever_setting, years_setting)

    return results_run

# database_from_csv_to_datamatrix()
# results_run = local_transport_run()
