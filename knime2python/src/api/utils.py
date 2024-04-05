import sys

import numpy as np
import pandas as pd


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def reduce_mem_usage(props):
    NAlist = []  # Keeps track of columns that have missing values filled in.
    for col in props.columns:
        if props[col].dtype != object:  # Exclude strings

            # make variables for Int, max and min
            IsInt = False
            mx = props[col].max()
            mn = props[col].min()

            # Integer does not support NA, therefore, NA needs to be filled
            if not np.isfinite(props[col]).all():
                NAlist.append(col)
                IsInt = False
            else:
                # test if column can be converted to an integer
                asint = props[col].fillna(0).astype(np.int64)
                result = (props[col] - asint)
                result = result.sum()
                if result > -0.01 and result < 0.01:
                    IsInt = True

            # Make Integer/unsigned Integer datatypes
            if IsInt:
                ###############################################################################
                # Disactivated: 487 MB => 460 MB in memory (with compression) but slowing down the converter
                ###############################################################################
                if mn >= 0:
                    pass
                    #props[col] = pd.to_numeric(props[col], downcast='signed')
                else:
                    pass
                    #props[col] = pd.to_numeric(props[col], downcast='unsigned')

            # Downcast floats
            else:
                ###############################################################################
                # THE DOWNCAST of FLOAT is causing issues in the results of Power and Buildings
                ###############################################################################

                #props[col] = pd.to_numeric(props[col], downcast='float')
                pass
                #props[col] = props[col].astype(np.float32)

            # Print new column type
            #print("dtype after: ", props[col].dtype)
            #print("******************************")

        # if object, convert to categories
        else:
            ###############################################################################
            # Disactivated: 487 MB => 400 MB in memory (with compression) but creating issues in 'missing_value_node' and 'pivoting_node' because the category dtype does not exist in np.dtypes
            ###############################################################################

            pass
            # num_unique_values = len(props[col].unique())
            # num_total_values = len(props[col])
            # if num_unique_values / num_total_values < 0.5:
            #     props.loc[:, col] = props[col].astype('category')
            # else:
            #     props.loc[:, col] = props[col]

    return props, NAlist
