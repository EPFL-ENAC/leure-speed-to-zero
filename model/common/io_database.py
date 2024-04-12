import pandas as pd
import os


def read_database(filename, lever, folderpath="default", db_format=False, level='all'):
    # Reads csv file in database/data/csv and extracts it in df format with columns
    # "Country, Years, lever-name, variable-columns"
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    if folderpath == "default":
        folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")

    # Remove duplicates
    len_init = len(df_db)
    df_db = df_db.drop_duplicates(subset=['geoscale', 'timescale', 'level', 'string-pivot', 'eucalc-name'])
    if len(df_db) - len_init < 0:
        print(f"Duplicates found in: {filename}, use .duplicated on dataframe to check which lines are repeated")

    if db_format:
        return df_db
    else:
        df_db_ots = (df_db.loc[(df_db["level"] == 0) & (df_db['lever'] == lever)]).copy()
        if level == 'all':
            df_db_fts = (df_db.loc[(df_db["level"] != 0) & (df_db['lever'] == lever)]).copy()
        else:
            df_db_fts = (df_db.loc[(df_db["level"] == level) & (df_db['lever'] == lever)]).copy()

        if (df_db_ots['string-pivot'] != 'none').any():
            df_ots = df_db_ots.pivot(index=['geoscale', 'timescale', 'level', 'string-pivot'], columns="eucalc-name",
                                     values='value')
        else:
            df_ots = df_db_ots.pivot(index=['geoscale', 'timescale', 'level'], columns="eucalc-name", values='value')
        df_ots.reset_index(inplace=True)
        if (df_db_fts['string-pivot'] != 'none').any():
            df_fts = df_db_fts.pivot(index=['geoscale', 'timescale', 'level', 'string-pivot'], columns="eucalc-name",
                                     values='value')
        else:
            df_fts = df_db_fts.pivot(index=['geoscale', 'timescale', 'level'], columns="eucalc-name", values='value')



        df_fts.reset_index(inplace=True)
        rename_cols = {'geoscale': "Country", 'timescale': 'Years', 'level': lever}
        df_ots.rename(columns=rename_cols, inplace=True)
        df_fts.rename(columns=rename_cols, inplace=True)

    return df_ots, df_fts


def edit_database(filename: str, lever: str, column: str, pattern, mode: str, level=None, filter_dict=None):
    # it edits the database either by renaming or removing strings in the database
    # it requires as input the 'filename' as a string, the 'lever' containing the lever name,
    # 'column' indicating the columns in the database that you want to edit, 'mode' is either 'remove' or 'rename',
    # if 'mode'=='remove', then 'pattern' is a regex pattern and the algorithm will remove the entire row
    # e.g. edit_database('lifestyles_population', 'pop', column='geoscale', pattern='Norway|Vaud', mode='remove')
    # it will remove Norway and Vaud from the country list
    # if 'mode'=='rename', then 'pattern' is a dictionary to replace the substring in key with the substring in value.
    # e.g. edit_database('lifestyles_population', 'pop', column='eucalc-name',
    #                    pattern={'population':'pop', 'lfs:'lifestyles'}, mode='rename')
    # if it find for example 'lfs_urban_population' in 'eucalc-name', this would become 'lifestyle_urban_population'
    # name-filter allows to rename only for a specific set of rows before applying the rename
    assert mode in ('rename', 'remove'), f"Invalid mode: {mode}, mode should be rename or remove"

    filename = filename.replace('.csv', '')  # drop .csv extension
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")
    df_db_lever = (df_db[df_db['lever'] == lever]).copy()
    df_db_other = (df_db[df_db['lever'] != lever]).copy()
    if mode == "rename":
        if column == "eucalc-name":
            col_to_rename = ["eucalc-name", "element", "item", "unit"]
        else:
            col_to_rename = [column]
        df_db_unchanged = pd.DataFrame()
        if filter_dict is not None:
            # allows to only filter a set of row before applying the rename
            filter_col = list(filter_dict.keys())[0]
            filter_pattern = filter_dict[filter_col]
            mask = df_db_lever[filter_col].astype(str).str.contains(filter_pattern)
            df_db_unchanged = df_db_lever.loc[~mask].copy()
            df_db_lever = df_db_lever.loc[mask].copy()
        for str1 in pattern:
            str2 = pattern[str1]
            for col in col_to_rename:
                df_db_lever[col] = df_db_lever[col].str.replace(str1, str2)
        if not df_db_unchanged.empty:
            df_db_lever = pd.concat([df_db_lever, df_db_unchanged], axis=0)
    if mode == "remove":
        if level is None:
            mask = df_db_lever[column].str.contains(pattern)
            df_db_lever = df_db_lever[~mask]
        # Remove line conditioned to level value (used to remove 2015 in fts)
        if level is not None:
            mask = (df_db_lever[column].astype(str).str.contains(pattern)) & (df_db_lever['level'] == level)
            df_db_lever = df_db_lever[~mask]
    df_db_new = pd.concat([df_db_lever, df_db_other], axis=0)
    df_db_new.sort_values(by=['geoscale', 'timescale'], axis=0, inplace=True)
    df_db_new.to_csv(file, sep=";", index=False)
    return


def change_unit_database(filename, target_col_pattern, new_unit):
    # Given the name of the csv file in the database and the pattern for the column (do not use .*),
    # it replaces the units in the unit column
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")
    mask = df_db['eucalc-name'].str.contains(target_col_pattern)
    # Define a regular expression to extract the unit between '[' and ']'
    df_db.loc[mask, 'eucalc-name'] = df_db.loc[mask, 'eucalc-name'].replace(to_replace=r'\[.*\]', value="["+new_unit+"]", regex=True)
    df_db.loc[mask, 'unit'] = new_unit
    df_db.to_csv(file, sep=";", index=False)
    return


def update_database(filename, df_new, lever=None):
    # Update csv file in database/data/csv based on a dataframe with columns
    # "Country, Years, lever-name, (col1, col2, col3)"
    if lever is not None:
        rename_cols = {"Country": 'geoscale', 'Years': 'timescale', lever: 'level'}
    else:
        rename_cols = {"Country": 'geoscale', 'Years': 'timescale'}
        df_new['level'] = 0
    df_new.rename(columns=rename_cols, inplace=True)
    df_new = pd.melt(df_new, id_vars=['geoscale', 'timescale', 'level'], var_name='eucalc-name', value_name='value')
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")

    # Merge DataFrame A with DataFrame B based on common columns
    merged_df = df_db.merge(df_new, how='outer', on=['geoscale', 'timescale', 'level', 'eucalc-name'],
                            suffixes=('_old', '_new'))
    merged_df['value'] = merged_df['value_new']

    # check for NaN values
    mask = pd.isna(merged_df['value'])
    merged_df.loc[mask, 'value'] = merged_df.loc[mask, 'value_old']
    # Copy merged on value_old, delete value and value_new and rename value_old as value
    # (this is to preserve the column order)
    merged_df['value_old'] = merged_df['value']
    merged_df.drop(columns=["value_new", "value"], inplace=True)
    merged_df.rename(columns={'value_old': 'value'}, inplace=True)
    merged_df.sort_values(by=['geoscale', 'timescale'], axis=0, inplace=True)
    merged_df.to_csv(file, sep=";", index=False)

    return


def levers_in_file(filename, folderpath="default"):
    # Returns all the lever names in a file
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    if folderpath == "default":
        folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")
    levers = list(set(df_db['lever']))
    return levers


def read_database_w_filter(filename, lever, filter_dict, folderpath="default", db_format=False, level='all'):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    if folderpath == "default":
        folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")
    for column, pattern in filter_dict.items():
        mask = df_db[column].astype(str).str.contains(pattern)
        df_db = df_db.loc[mask]

    # Remove duplicates
    len_init = len(df_db)
    df_db = df_db.drop_duplicates(subset=['geoscale', 'timescale', 'level', 'string-pivot', 'eucalc-name'])
    if len(df_db) - len_init < 0:
        print(f"Duplicates found in: {filename}, use .duplicated on dataframe to check which lines are repeated")

    if db_format:
        return df_db
    else:
        df_db_ots = (df_db.loc[(df_db["level"] == 0) & (df_db['lever'] == lever)]).copy()
        if level == 'all':
            df_db_fts = (df_db.loc[(df_db["level"] != 0) & (df_db['lever'] == lever)]).copy()
        else:
            df_db_fts = (df_db.loc[(df_db["level"] == level) & (df_db['lever'] == lever)]).copy()
        if (df_db_ots['string-pivot'] != 'none').any():
            df_ots = df_db_ots.pivot(index=['geoscale', 'timescale', 'level', 'string-pivot'], columns="eucalc-name", values='value')
        else:
            df_ots = df_db_ots.pivot(index=['geoscale', 'timescale', 'level'], columns="eucalc-name", values='value')
        df_ots.reset_index(inplace=True)
        if (df_db_fts['string-pivot'] != 'none').any():
            df_fts = df_db_fts.pivot(index=['geoscale', 'timescale', 'level', 'string-pivot'], columns="eucalc-name", values='value')
        else:
            df_fts = df_db_fts.pivot(index=['geoscale', 'timescale', 'level'], columns="eucalc-name", values='value')
        df_fts.reset_index(inplace=True)
        rename_cols = {'geoscale': "Country", 'timescale': 'Years', 'level': lever}
        df_ots.rename(columns=rename_cols, inplace=True)
        df_fts.rename(columns=rename_cols, inplace=True)

        return df_ots, df_fts


def update_database_from_db(filename, db_new, folderpath="default"):
    # Update csv file in database/data/csv based on a database with columns
    # "geoscale, timescale, eucalc-name, level, value"
    if folderpath == "default":
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")

    # Merge DataFrame A with DataFrame B based on common columns
    on_cols = list(df_db.columns.drop(['value']))
    merged_df = df_db.merge(db_new, how='outer', on=on_cols,
                            suffixes=('_old', '_new'))
    merged_df['value'] = merged_df['value_new']

    # check for NaN values
    mask = pd.isna(merged_df['value'])
    merged_df.loc[mask, 'value'] = merged_df.loc[mask, 'value_old']
    # Copy merged on value_old, delete value and value_new and rename value_old as value
    # (this is to preserve the column order)
    merged_df['value_old'] = merged_df['value']
    merged_df.drop(columns=["value_new", "value"], inplace=True)
    merged_df.rename(columns={'value_old': 'value'}, inplace=True)
    merged_df.sort_values(by=['geoscale', 'timescale'], axis=0, inplace=True)
    merged_df.to_csv(file, sep=";", index=False)

    return


def read_database_fxa(filename, folderpath="default", db_format=False, filter_dict=None):

    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    if folderpath == "default":
        folderpath = os.path.join(current_file_directory, "../../_database/data/csv/")
    file = folderpath + filename + '.csv'
    df_db = pd.read_csv(file, sep=";")
    if filter_dict is not None:
        for column, pattern in filter_dict.items():
            mask = df_db[column].astype(str).str.contains(pattern)
            df_db = df_db.loc[mask]
    # Remove duplicates
    len_init = len(df_db)
    df_db = df_db.drop_duplicates(subset=['geoscale', 'timescale', 'level', 'string-pivot', 'eucalc-name'])
    if len(df_db) - len_init < 0:
        print(f"Duplicates found in: {filename}, use .duplicated on dataframe to check which lines are repeated")
    if db_format:
        return df_db
    else:
        if (df_db['string-pivot'] != 'none').any():
            df = df_db.pivot(index=['geoscale', 'timescale', 'string-pivot'], columns="eucalc-name", values='value')
        else:
            df = df_db.pivot(index=['geoscale', 'timescale'], columns="eucalc-name", values='value')
        df.reset_index(inplace=True)
        rename_cols = {'geoscale': "Country", 'timescale': 'Years'}
        df.rename(columns=rename_cols, inplace=True)
        return df

