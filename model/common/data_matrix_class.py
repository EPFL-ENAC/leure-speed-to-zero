import numpy as np
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import itertools
import copy

# DataMatrix is the by-default class used by the calculator.
# DataMatrix contains:
#       - array: numpy array (can be 3D or more)
#       - dim_labels: list ['Country', 'Years', 'Variables', 'Categories1', ..]
#       - col_labels: dict that associates each dimension with the list of column labels
#              e.g.{
#                   'Country': ['Austria', 'Belgium', ..],
#                   'Years': [1990, 1991, ..., 2015, 2020, ..., 2050]
#                   'Variables': ['tra_passenger_modal-share', 'tra_passenger_occupancy', ...],
#                   'Categories1': ['LDV', '2W', 'rail', 'aviation', ...]
#                   }
#       - units: dict that contains the unit corresponding to each Variable
#               e.g. units['tra_passenger_modal-share'] = '%'
#       - idx: dictionary that links every label with the array index position
#                   e.g. idx['Austria'] = 0
#                        idx['Belgium'] = 1
#                        idx[1990] = 0
#              this is used to access the numpy array e.g.
#              dm.array[idx['Austria'], :, idx['tra_passenger_modal-share'], idx['LDV']]
#              gives the share of light duty vehicles (cars) in Austria for all years.


class DataMatrix:

    def __init__(self, col_labels={}, units={}):
        self.array = None
        self.dim_labels = ["Country", "Years", "Variables"]  # list
        self.col_labels = copy.deepcopy(col_labels)  # dictionary with dim_labels[i] as key
        if len(self.col_labels) == 4:
            self.dim_labels = ["Country", "Years", "Variables", "Categories1"]
        if len(self.col_labels) == 5:
            self.dim_labels = ["Country", "Years", "Variables", "Categories1", "Categories2"]
        self.units = copy.deepcopy(units)  # dictionary
        if len(col_labels) > 0:
            self.idx = self.index_all()

    def __repr__(self):
        return f'DataMatrix with shape {self.array.shape} and variables {self.col_labels["Variables"]}'

    def read_data(self, df, num_cat):
        # Function called by the classmethod 'create_from_df' (see below)
        # It is used to transform a dataframe df (table) into a datamatrix by specifying the number of categories
        # ATT: to be run after extract_structure which initialises dim_labels, col_labels and units
        dims = []
        df.sort_values(by=['Country', 'Years'], inplace=True)
        if num_cat > 3:
            raise Exception("You can only set maximum 3 categories")

        # Add categories dimension if not there before
        for i in range(num_cat):
            i = i + 1
            cat_str = "Categories" + str(i)
            if cat_str not in self.dim_labels:
                self.dim_labels.append(cat_str)

        for i in self.dim_labels:
            dims.append(len(self.col_labels[i]))

        array = np.empty(dims)
        array[:] = np.nan
        df.set_index(["Country", "Years"], inplace=True)

        # Iterate over the dataframe columns & extract the string _xxx[ as category and the rest as variable
        for col in df.columns:
            last_bracket_index = col.rfind('[')
            v = col[:last_bracket_index]
            series_data = df[col]
            c = {}
            for i in range(num_cat):
                last_underscore_index = v.rfind('_')
                c[i] = v[last_underscore_index + 1:]
                v = col[:last_underscore_index]
            if num_cat == 0:
                array[:, :, self.idx[v]] = np.reshape(series_data.values, (dims[0], dims[1]))
            if num_cat == 1:
                array[:, :, self.idx[v], self.idx[c[0]]] = np.reshape(series_data.values, (dims[0], dims[1]))
            if num_cat == 2:
                array[:, :, self.idx[v], self.idx[c[1]], self.idx[c[0]]] = np.reshape(series_data.values,
                                                                                      (dims[0], dims[1]))
            if num_cat == 3:
                array[:, :, self.idx[v], self.idx[c[2]], self.idx[c[1]], self.idx[c[0]]] = \
                    np.reshape(series_data.values, (dims[0], dims[1]))

        df.reset_index(inplace=True)
        self.array = array
        return

    def extract_structure(self, df, num_cat=1):
        # It reads a dataframe, and it extracts its columns as variables and categories
        # it also extracts the Countries and the Years (sorted)
        # These become elements of the class

        # checks if cols 'Country' and 'Years' are in the datafram
        def check_columns(dataframe):
            required_columns = ['Years', 'Country']
            missing_columns = [col for col in required_columns if col not in dataframe.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            return

        check_columns(df)

        if num_cat > 3:
            raise Exception("You can only set maximum 3 categories")

        # Add categories dimension if not there before
        for i in range(num_cat):
            i = i + 1
            cat_str = "Categories" + str(i)
            if cat_str not in self.dim_labels:
                self.dim_labels.append(cat_str)

        cols = [col for col in df.columns if col not in ["Country", "Years"]]
        categories = {}
        variables = []
        units = dict()
        i = 1
        for col in cols:
            try:
                unit = re.search(r'\[(.*?)\]', col).group(1)
            except AttributeError:
                raise AttributeError('Error: try to remove the lever column from the dataframe and make sure all variables have units in eucalc-name')
                exit()
            col_tmp = col.replace(f'[{unit}]', '')
            for i in range(num_cat):
                i = i + 1
                last_underscore_index = col_tmp.rfind('_')
                cat = col_tmp[last_underscore_index + 1:]
                if i not in categories.keys():
                    categories[i] = [cat]
                else:
                    if cat not in categories[i]:
                        categories[i].append(cat)
                col_tmp = col_tmp.replace(f'_{cat}', '')
            var = col_tmp
            if var not in variables:
                variables.append(var)
            if var in units.keys():
                if unit != units[var]:
                    print("Variables " + var + " has two different units, change its name")
            else:
                units[var] = unit

        self.col_labels["Country"] = sorted(list(set(df["Country"])))
        self.col_labels["Years"] = sorted(list(set(df["Years"].astype(int))))
        self.col_labels["Variables"] = sorted(variables)
        for i in range(num_cat):
            i = i + 1
            dim_str = "Categories" + str(num_cat - i + 1)
            self.col_labels[dim_str] = sorted(categories[i])

        self.idx = self.index_all()
        self.units = units

        return

    @classmethod
    def create_from_df(cls, df, num_cat):
        # Creates a datamatrix given a dataframe and the number of categories that we want
        # Note that df needs to have columns 'Country' and 'Years'
        # it returns a datamatrix
        dm = cls()
        dm.extract_structure(df, num_cat)
        dm.read_data(df, num_cat)
        return dm

    def read_data_0cat(self, df):
        # use read_data instead
        dims = []
        for i in self.dim_labels:
            dims.append(len(self.col_labels[i]))

        array = np.empty(dims)
        array[:] = np.nan
        df.set_index(["Country", "Years"], inplace=True)

        # Iterate over the dataframe columns
        for col in df.columns:
            last_bracket_index = col.rfind('[')
            v = col[:last_bracket_index]
            series_data = df[col]
            array[:, :, self.idx[v]] = np.reshape(series_data.values, (dims[0], dims[1]))

        self.array = array

    def add(self, new_array, dim, col_label, unit=None, dummy=False):
        # Adds the numpy array new_array to the datamatrix over dimension dim.
        # The label associated with the array is in defined by the string col_label
        # The unit is needed as a string (e.g. 'km') only if dim = 'Variables'
        # It does not return a new datamatrix
        # You can also use to add 'dummy' dimension to a datamatrix,
        # usually before appending it to another that has more categories
        self_shape = self.array.shape
        a = self.dim_labels.index(dim)
        new_shape = list(self_shape)
        if isinstance(col_label, str):
            # if I'm adding only one column
            col_label = [col_label]
            unit = [unit]
        new_shape[a] = len(col_label)
        new_shape = tuple(new_shape)
        # If it is adding a new array of constant value (e.g. nan) to have a dummy dimension:
        if isinstance(new_array, float) and dummy is True:
            new_array = new_array * np.ones(new_shape)
        elif len(col_label) == 1 and new_array.shape != new_shape:
            new_array = new_array[..., np.newaxis]
            new_array = np.moveaxis(new_array, -1, a)
        # Else check that the new array dimension is correct
        if new_array.shape != new_shape and dummy is False:
            raise AttributeError(f'The new_array should have dimension {new_shape} instead of {new_array.shape}, '
                                 f'unless you want to add dummy dimensions, then you should add dummy = True and new_array should be a float')
        for col in col_label:
            self.col_labels[dim].append(col)
            i_v = self.single_index(col, dim)
            if col not in list(self.idx.keys()):
                self.idx[col] = i_v[col]
            else:
                raise ValueError("You are trying to append data under the label " + col_label + " which already exists")
        if dim == 'Variables':
            for i, col in enumerate(col_label):
                self.units[col] = unit[i]
        self.array = np.concatenate((self.array, new_array), axis=a)

    def drop(self, dim, col_label):
        # It removes the column col_label along dimension dim
        # as well as the data in array associated to it
        # It does not return a new datamatrix

        # Get the axis of the dimension
        a = self.dim_labels.index(dim)
        # if col_label it's a string, check for the columns that match the regex pattern
        if isinstance(col_label, str):
            tmp = [c for c in self.col_labels[dim] if re.match(col_label, c)]
            col_label = tmp
        # remove the data from the matrix
        idx = self.single_index(col_label, dim)  # get index of col_label
        i_val = list(idx.values())
        self.array = np.delete(self.array, i_val, axis=a)  # remove array
        # remove the label
        for c in col_label:
            self.col_labels[dim].remove(c)
        # remove the unit
        if dim == "Variables":
            if isinstance(col_label, list):
                for c in col_label:
                    self.units.pop(c)
            else:
                self.units.pop(col_label)
        self.idx = self.index_all()
        return

    def lag_variable(self, pattern, shift, subfix):
        # It lags the columns over the years based on the regex pattern "pattern"
        # (e.g. 'tra_passenger_.*|tra_freight_.*')
        # the dimension is always 'Variables' and it lags by a integer 'shift'
        # new column labels across dimension 'Variables' are added with subfix 'subfix'
        vars = [(vi, v) for (vi, v) in enumerate(self.col_labels["Variables"]) if re.match(pattern, v)]
        dim_label = "Variables"
        for (vi, v) in vars:
            v_sub = v + subfix  # new variable name
            unit = self.units[v]
            new_array = np.roll(self.array[:, :, vi, :], shift, axis=1)  # shift along Years axis
            if shift == 1:
                new_array[:, 0, :] = new_array[:, 1, :]  # copy 1991 value to 1990
            elif shift == -1:
                new_array[:, -1, :] = new_array[:, -2, :]  # copy 2045 value to 2050
            else:
                raise Exception("You can only shift by +1 or -1 in lag_variable func of DataMatrix class")
            self.add(new_array, dim_label, v_sub, unit)  # append new_array to self_array

    def single_index(self, var_names, dim):
        # it extract the positional index of the labels in var_names across dimension dim
        idx_dict = {}
        # If var_names is a list of variable names do a for loop
        if isinstance(var_names, list):
            for v in var_names:
                idx_dict[v] = self.col_labels[dim].index(v)
        # else var_names should be just a string containing a single variable name
        else:
            idx_dict[var_names] = self.col_labels[dim].index(var_names)

        return idx_dict

    def index_all(self):
        # extracts all the indexes and returns the dictionary idx (as well as re-assinging self.idx)
        idx = {}
        for (di, d) in enumerate(self.dim_labels):
            for (ci, c) in enumerate(self.col_labels[d]):
                idx[c] = ci
        self.idx = idx

        return idx

    def overwrite_1cat(self, matrix2):
        country = matrix2.col_labels["Country"]
        years = matrix2.col_labels["Years"]
        variables = matrix2.col_labels["Variables"]
        categories = matrix2.col_labels["Categories1"]
        all_cols = set(country + years + variables + categories)
        idx = self.index_all()
        if all_cols.issubset(set(idx.keys())):
            i_c = [idx[x] for x in country]
            i_y = [idx[x] for x in years]
            i_v = [idx[x] for x in variables]
            i_cat = [idx[x] for x in categories]
            mesh = np.ix_(i_c, i_y, i_v, i_cat)  # Create meshgrid
            self.array[mesh] = matrix2.array
        else:
            raise Exception("You are try to overwrite a DataMatrix with another DataMatrix that isn't a subset")

    def fill_nans(self, dim_to_interp):

        axis_to_interp = self.dim_labels.index(dim_to_interp)
        def interpolate_nans(arr):
            nan_indices = np.isnan(arr)
            if nan_indices.any():
                x_values = np.arange(len(arr))
                if len(x_values[~nan_indices]) > 0:
                    arr[nan_indices] = np.interp(x_values[nan_indices], x_values[~nan_indices], arr[~nan_indices])
            return arr

        # Apply interpolation along the specified axis
        if np.isnan(self.array).any():
            self.array = np.apply_along_axis(interpolate_nans, axis_to_interp, self.array)

        return

    def operation(self, col1, operator, col2, dim="Variables", out_col=None, unit=None, div0="error", type=float):
        # operation allows to perform operation between two columns belonging to the same
        # dimensions in DataMatrix and to append/overwrite the result to the dataframe
        i = self.idx
        a = self.dim_labels.index(dim)  #

        self.array = np.moveaxis(self.array, a, -1)  # Move the axis of array to the end

        def interpolate_nans(arr):
            nan_indices = np.isnan(arr)
            if nan_indices.any():
                x_values = np.arange(len(arr))
                if len(x_values[~nan_indices]) > 0:
                    arr[nan_indices] = np.interp(x_values[nan_indices], x_values[~nan_indices], arr[~nan_indices])
            return arr

        if operator == "/":
            if div0 == "error":
                tmp = self.array[..., i[col1]] / self.array[..., i[col2]]
            if div0 == "interpolate":
                axis_to_interp = 1
                tmp = np.divide(self.array[..., i[col1]], self.array[..., i[col2]],
                                out=np.nan * np.ones_like(self.array[..., i[col1]]),
                                where=self.array[..., i[col2]] != 0)
                # Apply interpolation along the specified axis
                if np.isnan(tmp).any():
                    tmp = np.apply_along_axis(interpolate_nans, axis_to_interp, tmp)

        if operator == "-":
            tmp = self.array[..., i[col1]] - self.array[..., i[col2]]

        if operator == "+":
            tmp = self.array[..., i[col1]] + self.array[..., i[col2]]

        if operator == "*":
            tmp = self.array[..., i[col1]] * self.array[..., i[col2]]

        self.array = np.moveaxis(self.array, -1, a)

        if out_col is not None:
            self.add(tmp.astype(type), dim, out_col, unit)
        else:
            return tmp

        return

    def write_df(self):
        years = self.col_labels["Years"]
        countries = self.col_labels["Country"]
        n_y = len(years)
        n_c = len(countries)
        country_list = [item for item in countries for _ in range(n_y)]
        years_list = years * n_c
        df = pd.DataFrame(data=zip(country_list, years_list), columns=["Country", "Years"])

        num_cat = len(self.dim_labels) - 3

        if num_cat == 3:
            dm_new = self.flatten()
            self.__dict__.update(dm_new.__dict__) # it replaces self with dm_new
            num_cat = len(self.dim_labels) - 3

        if num_cat == 2:
            dm_new = self.flatten()
            self.__dict__.update(dm_new.__dict__)  # it replaces self with dm_new
            num_cat = len(self.dim_labels) - 3

        if num_cat == 0:
            for v in self.col_labels["Variables"]:
                col_name = v + "[" + self.units[v] + "]"
                col_value = self.array[:, :, self.idx[v]].flatten()
                df[col_name] = col_value
        if num_cat == 1:
            for v in self.col_labels["Variables"]:
                for c in self.col_labels["Categories1"]:
                    col_name = v + "_" + c + "[" + self.units[v] + "]"
                    col_value = self.array[:, :, self.idx[v], self.idx[c]].flatten()
                    if not np.isnan(col_value).all():
                        df[col_name] = col_value


        return df

    def rename_col(self, col_in, col_out, dim):
        # Rename col_labels
        if isinstance(col_in, str):
            col_in = [col_in]
            col_out = [col_out]
        for i in range(len(col_in)):
            # Rename column labels
            ci = self.idx[col_in[i]]
            self.col_labels[dim][ci] = col_out[i]
            # Rename key for units
            if dim == "Variables":
                self.units[col_out[i]] = self.units[col_in[i]]
                self.units.pop(col_in[i])
            # Rename idx
            self.idx[col_out[i]] = self.idx[col_in[i]]
            self.idx.pop(col_in[i])

        return

    def filter(self, selected_cols):
        # Sort the subset list based on the order of elements in list1
        sorted_cols = {}
        for d in self.dim_labels:
            if d in selected_cols.keys():
                if selected_cols[d] == "all":
                    sorted_cols[d] = self.col_labels[d].copy()
                else:
                    sorted_cols[d] = sorted(selected_cols[d], key=lambda x: self.col_labels[d].index(x))
            else:
                sorted_cols[d] = self.col_labels[d].copy()
        out = DataMatrix(col_labels=sorted_cols)
        out.dim_labels = self.dim_labels.copy()
        # Extract list of indices
        cols_idx = []
        for d in self.dim_labels:
            cols_idx.append([self.idx[xi] for xi in sorted_cols[d]])
        mesh = np.ix_(*cols_idx)
        out.array = self.array[mesh].copy()
        out.units = {key: self.units[key] for key in sorted_cols["Variables"]}
        if len(sorted_cols) > 3:
            out.idx = out.index_all()
        return out

    def filter_w_regex(self, dict_dim_pattern):
        # Return only a portion of the DataMatrix based on a dict_dim_patter
        # E.g. if we wanted to only keep Austria and France, the dict_dim_pattern would be {'Country':'France|Austria'}
        keep = {}
        for d in self.dim_labels:
            if d in dict_dim_pattern.keys():
                pattern = re.compile(dict_dim_pattern[d])
                keep[d] = [col for col in self.col_labels[d] if re.match(pattern, col)]
            else:
                keep[d] = 'all'
        dm_keep = self.filter(keep)
        return dm_keep

    def rename_col_regex(self, str1, str2, dim):
        # Rename all columns containing str1 with str2
        col_in = [col for col in self.col_labels[dim] if str1 in col]
        col_out = [word.replace(str1, str2) for word in col_in]
        self.rename_col(col_in, col_out, dim=dim)
        return

    def sort(self, dim):
        sort_index = np.argsort(np.array(self.col_labels[dim]))
        self.col_labels[dim] = sorted(self.col_labels[dim])  # sort labels
        for (ci, c) in enumerate(self.col_labels[dim]):  # sort indexes
            self.idx[c] = ci
        a = self.dim_labels.index(dim)
        self.array = np.take(self.array, sort_index, axis=a)  # re-orders the array according to sort_index

    def append(self, data2, dim):
        # appends DataMatrix data2 to self in dimension dim.
        # The pre-requisite is that all other dimensions match
        dim_lab = self.dim_labels.copy()
        dim_lab.remove(dim)
        if 'Variables' in dim_lab:
            dim_lab.remove("Variables")
        for d in dim_lab:
            if self.col_labels[d] != data2.col_labels[d]:
                self.sort(dim=d)
                data2.sort(dim=d)
                assert (self.col_labels[d] == data2.col_labels[d])
        # Check that across the dimension where you want to append the labels are different
        cols1 = set(self.col_labels[dim])
        cols2 = set(data2.col_labels[dim])
        same_col = cols2.intersection(cols1)
        if len(same_col) != 0:
            raise Exception("The DataMatrix that you are trying to append contains the same labels across dimension ", dim)
        # Concatenate the two arrays
        a = self.dim_labels.index(dim)
        self.array = np.concatenate((self.array, data2.array), axis=a)
        # Concatenate the two lists of labels across dimension dim
        self.col_labels[dim] = self.col_labels[dim] + data2.col_labels[dim]
        # Re initialise the indexes
        for (ci, c) in enumerate(self.col_labels[dim]):  # sort indexes
            self.idx[c] = ci
        # Add the units if you are appending over "Variables"
        if dim == "Variables":
            self.units = self.units | data2.units

        return

    def deepen(self, sep="_", based_on=None):
        # Adds a category to the datamatrix based on the "Variables" names
        idx_old = self.index_all()

        # Add one category to the dim_labels list depending on the current structure
        if self.dim_labels[-1] == "Variables":
            new_dim = 'Categories1'
            root_dim = 'Variables'
            self.dim_labels.append(new_dim)
        elif self.dim_labels[-1] == 'Categories1':
            new_dim = 'Categories2'
            root_dim = 'Categories1'
            self.dim_labels.append(new_dim)
        elif self.dim_labels[-1] == 'Categories2':
            new_dim = 'Categories3'
            root_dim = 'Categories2'
            self.dim_labels.append(new_dim)
        else:
            raise Exception('You cannot deepen (aka add a dimension) to a datamatrix with already 3 categories')

        if based_on is not None:
            root_dim = based_on

        # Add col labels the added dimension and rename col labels of existing dimension
        # It also takes care of rename the units dictionary if relevant
        self.col_labels[new_dim] = []
        root_cols = []
        rename_mapping = {}

        for col in self.col_labels[root_dim]:
            last_underscore_index = col.rfind(sep)
            if last_underscore_index == -1:
                raise Exception('No separator _ could be found in the last category')
            new_cat = col[last_underscore_index + 1:]
            root_cat = col[:last_underscore_index]
            rename_mapping[col] = [root_cat, new_cat]
            # crates col_labels list for the new dimension
            if new_cat not in self.col_labels[new_dim]:
                self.col_labels[new_dim].append(new_cat)
            # renames the existing root_cat dimension
            if root_cat not in root_cols:
                root_cols.append(root_cat)
            # renames units dict
            if root_dim == 'Variables':
                if root_cat not in self.units.keys():
                    self.units[root_cat] = self.units[col]
                self.units.pop(col)
        self.col_labels[root_dim] = sorted(root_cols)
        self.col_labels[new_dim] = sorted(self.col_labels[new_dim])

        # Restructure data array
        idx_new = self.index_all()
        array_old = self.array
        dims = []
        for i in self.dim_labels:
            dims.append(len(self.col_labels[i]))
        array_new = np.empty(dims)
        array_new[...] = np.nan
        if based_on is not None:
            a_root = self.dim_labels.index(root_dim)
            array_new = np.moveaxis(array_new, a_root, -2)
            array_old = np.moveaxis(array_old, a_root, -1)
        for col in rename_mapping.keys():
            [root_cat, new_cat] = rename_mapping[col]
            array_new[..., idx_new[root_cat], idx_new[new_cat]] = array_old[..., idx_old[col]]
        if based_on is not None:
            array_new = np.moveaxis(array_new, -2, a_root)
        self.array = array_new
        return

    def deepen_twice(self):
        # Adds two dimensions to the datamatrix based on the last dimension column names
        root_dim = self.dim_labels[-1]
        tmp_cols = []

        for col in self.col_labels[root_dim]:
            last_index = col.rfind("_")
            new_col = col[:last_index] + '?' + col[last_index+1:]
            tmp_cols.append(new_col)
            if root_dim == 'Variables':
                self.units[new_col] = self.units[col]
                self.units.pop(col)
        self.col_labels[root_dim] = tmp_cols

        self.deepen(sep='_')

        tmp_cols = []
        root_dim = self.dim_labels[-1]
        for col in self.col_labels[root_dim]:
            last_index = col.rfind("?")
            new_col = col[:last_index] + '_' + col[last_index+1:]
            tmp_cols.append(new_col)
            if root_dim == 'Variables':
                self.units[new_col] = self.units[col]
                self.units.pop(col)
        self.col_labels[root_dim] = tmp_cols

        self.deepen(sep='_')

        return

    def flatten(self):
        # you can flatten only if you have at least one category
        assert len(self.dim_labels) > 3
        d_2 = self.dim_labels[-1]
        cols_2 = self.col_labels[d_2]
        d_1 = self.dim_labels[-2]
        cols_1 = self.col_labels[d_1]
        new_shape = []
        new_col_labels = {}
        for d in self.dim_labels:
            if d is not d_1 and d is not d_2:
                new_shape.append(len(self.col_labels[d]))
                new_col_labels[d] = self.col_labels[d].copy()
        new_shape.append(1)
        new_shape = tuple(new_shape)
        new_array = np.empty(shape=new_shape)
        new_array[...] = np.nan
        new_cols = []
        new_units = {}
        i = 0
        for c1 in cols_1:
            for c2 in cols_2:
                col_value = self.array[..., self.idx[c1], self.idx[c2], np.newaxis]
                if not np.isnan(col_value).all():
                    new_cols.append(f'{c1}_{c2}')
                    if i == 0:
                        i = i+1
                        new_array = col_value
                    else:
                        new_array = np.concatenate([new_array, col_value], axis=-1)
                    if d_1 == 'Variables':
                        new_units[f'{c1}_{c2}'] = self.units[c1]

        new_col_labels[d_1] = new_cols
        if d_1 == 'Variables':
            dm_new = DataMatrix(col_labels=new_col_labels, units=new_units)
        else:
            dm_new = DataMatrix(col_labels=new_col_labels, units=self.units)
        dm_new.array = new_array
        dm_new.idx = dm_new.index_all()
        return dm_new

    def copy(self):
        array = self.array.copy()
        col_labels = self.col_labels.copy()  # dictionary with dim_labels[i] as key
        units = self.units.copy()
        dm = DataMatrix(col_labels=col_labels, units=units)
        dm.array = array
        return dm

    def datamatrix_plot(self, selected_cols, title):

        dims = len(self.dim_labels)
        if (dims != 3) & (dims != 4):
            raise Exception("plot function has been implemented only for DataMatrix with max one category")

        i = self.idx

        countries_list = selected_cols["Country"]
        if countries_list == "all":
            countries_list = self.col_labels["Country"]
        if isinstance(countries_list, str):  # if 'Country': 'France' -> 'Country': ['France']
            countries_list = [countries_list]
        years_list = selected_cols["Years"]
        if years_list == "all":
            years_list = self.col_labels["Years"]
        if isinstance(years_list, str):  # if 'Years': 2020 -> 'Years': [2020]
            years_list = [years_list]
        years_idx = [i[x] for x in years_list]
        vars_list = selected_cols["Variables"]
        if vars_list == "all":
            vars_list = self.col_labels["Variables"]
        if isinstance(vars_list, str):
            vars_list = [vars_list]

        # Create an empty figure
        fig = px.line(x=years_list, labels={'x': 'Years', 'y': 'Values'}, title=title)
        fig.data[0]['y'] = np.nan*np.ones(shape=np.shape(fig.data[0]['y']))
        if dims == 3:
            for c in countries_list:
                for v in vars_list:
                    y_values = self.array[i[c], years_idx, i[v]]
                    label = c + "_" + v
                    fig.add_scatter(x=years_list, y=y_values, name=label, mode='lines')
        if dims == 4:
            cat_list = selected_cols["Categories1"]
            if cat_list == "all":
                cat_list = self.col_labels["Categories1"]
            for c in countries_list:
                for v in vars_list:
                    for cat in cat_list:
                        y_values = self.array[i[c], years_idx, i[v], i[cat]]
                        label = c + "_" + v + "_" + cat
                        fig.add_scatter(x=years_list, y=y_values, name=label, mode='lines')

        fig.show()


        return




