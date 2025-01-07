
# packages
from model.common.data_matrix_class import DataMatrix
import pickle
import os
import numpy as np
import warnings
warnings.simplefilter("ignore")

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_material-switch.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# create dm
countries = ['Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark',
             'EU27','Estonia','Finland','France','Germany','Greece','Hungary','Ireland','Italy',
             'Latvia','Lithuania','Luxembourg','Malta','Netherlands','Poland','Portugal',
             'Romania','Slovakia','Slovenia','Spain','Sweden','United Kingdom']
years = list(range(1990,2023+1,1))
years = years + list(range(2025, 2050+1, 5))
variabs = ['build-cement-to-timber', 'build-steel-to-timber', 'cars-steel-to-aluminium', 'cars-steel-to-chem', 'reno-chem-to-natfibers', 'reno-chem-to-paper', 'trucks-steel-to-aluminium', 'trucks-steel-to-chem']
units = list(np.repeat("%", len(variabs)))
units_dict = dict()
for i in range(0, len(variabs)):
    units_dict[variabs[i]] = units[i]
index_dict = dict()
for i in range(0, len(countries)):
    index_dict[countries[i]] = i
for i in range(0, len(years)):
    index_dict[years[i]] = i
for i in range(0, len(variabs)):
    index_dict[variabs[i]] = i

dm = DataMatrix()
dm.col_labels = {"Country" : countries, "Years" : years, "Variables" : variabs}
dm.units = units_dict
dm.idx = index_dict
dm.array = np.zeros((len(countries), len(years), len(variabs)))
# note that this is all zeroes as from page 27 Table 4 of https://www.european-calculator.eu/wp-content/uploads/2020/04/D3.1-Raw-materials-module-and-manufacturing.pdf

# make nan for other than EU27
countries_oth = np.array(countries)[[i not in "EU27" for i in countries]].tolist()
idx = dm.idx
years = list(range(2025, 2050+1, 5))
for c in countries_oth:
    for y in years:
        for v in variabs:
            dm.array[idx[c],idx[y],idx[v]] = np.nan
df = dm.write_df()

# save
f = os.path.join(current_file_directory, '../data/datamatrix/lever_material-switch.pickle')
with open(f, 'wb') as handle:
    pickle.dump(dm, handle, protocol=pickle.HIGHEST_PROTOCOL)


