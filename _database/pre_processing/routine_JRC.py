
import pandas as pd
import numpy as np
import re
import os
from model.common.data_matrix_class import DataMatrix

def get_jrc_data(dict_extract, dict_countries, current_file_directory, years = list(range(2000,2021+1)), 
                 levels_to_industry_preproc = "../../../Industry"):
    
    # get dataframe by country

    def get_dataframe(dict_extract, country):
        
        # store things
        database = dict_extract["database"]
        sheet = dict_extract["sheet"]
        variable = dict_extract["variable"]
        sheet_last_row = dict_extract["sheet_last_row"]
        sub_variables = dict_extract["sub_variables"]
        
        # define function to search
        def my_search(search, x):
            if x is np.nan:
                return False
            else:
                return bool(re.search(search, x, re.IGNORECASE))
        
        # get data
        filepath_jrc = os.path.join(current_file_directory, levels_to_industry_preproc + '/eu/data/JRC-IDEES-2021/' + country + '/JRC-IDEES-2021_' + database + '_' + country + '.xlsx')
        df = pd.read_excel(filepath_jrc, sheet)
        id_var = df.columns[0]
        df.rename(columns={id_var : "variable"},inplace=True)
        
        # subset data
        def get_indexes(vector, string):
            variable = re.sub(r"([\(\)])", r"\\\1", string) # this is to accept parentheses in the string
            bool_temp = [bool(my_search(variable, x)) for x in vector]
            idx_temp = [i for i, x in enumerate(bool_temp) if x][0]
            return idx_temp
        strings = [variable] + [sheet_last_row]
        indexes = [get_indexes(df.loc[:,"variable"], string) for string in strings]
        df_temp = df.iloc[range(indexes[0],indexes[1]+1),:]
        df_temp = df_temp.loc[df_temp["variable"].isin(sub_variables),:]
        df_temp = df_temp.loc[:,["variable"] + years]
        
        # add unit to variables names
        unit = variable.split("(")[1].split(")")[0]
        df_temp["variable"] = [re.sub(r"$", "[" + unit + "]", text) for text in df_temp["variable"]]
        
        # reshape data
        df_temp = pd.melt(df_temp, id_vars = "variable", var_name='Years')
        df_temp["Country"] = country
        df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
        
        return df_temp
    
    df_all = pd.concat([get_dataframe(dict_extract, country) for country in dict_countries.keys()])
    
    # make data matrix
    dm = DataMatrix.create_from_df(df_all, 0)
    
    # change country names
    for key in dict_countries.keys():
        dm.rename_col(key, dict_countries[key], "Country")
    
    # return
    return dm

