import re
import numpy as np
import copy
from model.common.io_database import read_database
from model.common.auxiliary_functions import constant_filter

# ConstantDataMatrix is a class used to deal with constants in a way that is similar to DataMatrix class.
# The main difference if that ConstantDataMatrix has no Country or Years dimensions.
# ConstantDataMatrix contains:
#       - array: numpy array (can be 1D or more)
#       - dim_labels: list ['Variables', 'Categories1', ..]
#       - col_labels: dict that associates each dimension with the list of column labels
#              e.g.{
#                   'Variables': ['biomass-emission-factor', 'agr_carbon-stock', etc],
#                   'Categories1': ['cropland', 'grassland', 'forest']
#                   }
#       - units: dict that contains the unit corresponding to each Variable e.g. units['agr_carbon-stock'] = 'kt'
#       - idx: dictionary that links every label with the array index position
#                   e.g. idx['biomass-emission-factor'] = 0
#                        idx['grassland'] = 1
#              this is used to access the numpy array e.g. cdm.array[idx['biomass-emission-factor'], idx['grassland']]
#              gives as output the biomass emission factor for grassland.


class ConstantDataMatrix:

    def __init__(self, col_labels={}, units={}):
        self.array = None
        self.dim_labels = ["Variables"]  # list
        self.col_labels = copy.deepcopy(col_labels)  # dictionary with dim_labels[i] as key
        if len(self.col_labels) == 2:
            self.dim_labels = ["Variables", "Categories1"]
        if len(self.col_labels) == 3:
            self.dim_labels = ["Variables", "Categories1", "Categories2"]
        self.units = copy.deepcopy(units)  # dictionary
        if len(col_labels) > 0:
            self.idx = self.index_all()

    def read_data(self, constant, num_cat):
        dims = []

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

        # Iterate over the dataframe columns & extract the string _xxx[ as category and the rest as variable
        for (col_i, col) in enumerate(constant['name']):
            last_bracket_index = col.rfind('[')
            v = col[:last_bracket_index]
            data = constant['value'][col_i]
            c = {}
            for i in range(num_cat):
                last_underscore_index = v.rfind('_')
                c[i] = v[last_underscore_index + 1:]
                v = col[:last_underscore_index]
            if num_cat == 0:
                array[self.idx[v]] = data
            if num_cat == 1:
                array[self.idx[v], self.idx[c[0]]] = data
            if num_cat == 2:
                array[self.idx[v], self.idx[c[1]], self.idx[c[0]]] = data
            if num_cat == 3:
                array[self.idx[v], self.idx[c[2]], self.idx[c[1]], self.idx[c[0]]] = data

        self.array = array
        return

    def extract_structure(self, constant, num_cat=1):
            # It reads a dataframe and it extracts its columns as variables and categories
            # it also extracts the Countries and the Years (sorted)
            # These become elements of the class
            if num_cat > 3:
                raise Exception("You can only set maximum 3 categories")

            # Add categories dimension if not there before
            for i in range(num_cat):
                i = i + 1
                cat_str = "Categories" + str(i)
                if cat_str not in self.dim_labels:
                    self.dim_labels.append(cat_str)

            categories = {}
            variables = []
            units = dict()
            i = 1
            for col in constant['name']:
                unit = re.search(r'\[(.*?)\]', col).group(1)
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

            self.col_labels["Variables"] = sorted(variables)
            for i in range(num_cat):
                i = i + 1
                dim_str = "Categories" + str(num_cat - i + 1)
                self.col_labels[dim_str] = sorted(categories[i])

            self.idx = self.index_all()
            self.units = units

            return

    @classmethod
    def create_from_constant(cls, constant, num_cat):
        dm = cls()
        dm.extract_structure(constant, num_cat)
        dm.read_data(constant, num_cat)
        return dm

    @classmethod
    def extract_constant(cls, const_file, pattern, num_cat):
        # it extract constant from the file const_file (database format) using pattern a filter for 'eucalc-name'.
        # it returns a ConstantDataMatrix with the number of categories set by num_cat
        # it uses the class method 'crate from constant
        db_const = read_database(const_file, lever='none', db_format=True)
        const = {
            'name': list(db_const['eucalc-name']),
            'value': list(db_const['value']),
            'idx': dict(zip(list(db_const['eucalc-name']), range(len(db_const['eucalc-name'])))),
            'units': dict(zip(list(db_const['eucalc-name']), list(db_const['unit'])))
        }
        emission_fact = constant_filter(const, pattern)
        cdm_const = ConstantDataMatrix.create_from_constant(emission_fact, num_cat=num_cat)
        return cdm_const

    def index_all(self):
        idx = {}
        for (di, d) in enumerate(self.dim_labels):
            for (ci, c) in enumerate(self.col_labels[d]):
                idx[c] = ci
        return idx

    def drop(self, dim, col_label):
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

    def single_index(self, var_names, dim):
        idx_dict = {}
        # If var_names is a list of variable names do a for loop
        if isinstance(var_names, list):
            for v in var_names:
                idx_dict[v] = self.col_labels[dim].index(v)
        # else var_names should be just a string containing a single variable name
        else:
            idx_dict[var_names] = self.col_labels[dim].index(var_names)

        return idx_dict

    def sort(self, dim):
        sort_index = np.argsort(np.array(self.col_labels[dim]))
        self.col_labels[dim] = sorted(self.col_labels[dim])  # sort labels
        for (ci, c) in enumerate(self.col_labels[dim]):  # sort indexes
            self.idx[c] = ci
        a = self.dim_labels.index(dim)
        self.array = np.take(self.array, sort_index, axis=a)  # re-orders the array according to sort_index
        return

    def copy(self):
        array = self.array.copy()
        col_labels = self.col_labels.copy()  # dictionary with dim_labels[i] as key
        units = self.units.copy()
        cdm = ConstantDataMatrix(col_labels=col_labels, units=units)
        cdm.array = array
        return cdm

