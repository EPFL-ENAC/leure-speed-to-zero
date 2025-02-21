
import pandas as pd
import numpy as np
import re
import os
from model.common.data_matrix_class import DataMatrix

def get_jrc_data(dict_extract, country, current_file_directory, years = list(range(2000,2021+1)), 
                 levels_to_industry_preproc = "../../../Industry"):

    def my_search(search, x):
        if x is np.nan:
            return False
        else:
            return bool(re.search(search, x, re.IGNORECASE))
    
    filepath_jrc = os.path.join(current_file_directory, levels_to_industry_preproc + '/eu/data/JRC-IDEES-2021/EU27/JRC-IDEES-2021_Transport_' + country + '.xlsx')
    
    # get data
    key = "Transport"
    df = pd.read_excel(filepath_jrc, key)
    id_var = df.columns[0]
    df.rename(columns={id_var : "variable"},inplace=True)
    
    # subset data
    def get_indexes(vector, string):
        variable = re.sub(r"([\(\)])", r"\\\1", string) # this is to accept parentheses in the string
        bool_temp = [bool(my_search(variable, x)) for x in vector]
        idx_temp = [i for i, x in enumerate(bool_temp) if x][0]
        return idx_temp
    strings = dict_extract[key]["variable"] + dict_extract[key]["end_database_at"]
    indexes = [get_indexes(df.loc[:,"variable"], string) for string in strings]
    df_temp = df.iloc[range(indexes[0],indexes[1]+1),:]
    df_temp = df_temp.loc[df_temp["variable"].isin(dict_extract[key]["sub_variables"]),:]
    df_temp = df_temp.loc[:,["variable"] + years]
    
    # add unit to variables names
    unit = dict_extract[key]["variable"][0].split("(")[1].split(")")[0]
    df_temp["variable"] = [re.sub(r"$", "[" + unit + "]", text) for text in df_temp["variable"]]
    
    # reshape data
    df_temp = pd.melt(df_temp, id_vars = "variable", var_name='Years')
    df_temp["Country"] = country
    df_temp = df_temp.pivot(index=["Country","Years"], columns="variable", values='value').reset_index()
    
    # make data matrix
    dm = DataMatrix.create_from_df(df_temp, 0)
    
    # return
    return dm

