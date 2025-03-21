
# DataMatrix with shape (32, 33, 1, 16), variables ['ind_material-efficiency'] and categories1 ['aluminium', 'ammonia', 'cement', 'chem', 'copper', 'fbt', 'glass', 'lime', 'mae', 'ois', 'paper', 'steel', 'textiles', 'timber', 'tra-equip', 'wwp']

# packages
from model.common.data_matrix_class import DataMatrix
from model.common.auxiliary_functions import linear_fitting
import pickle
import os
import numpy as np
import warnings
warnings.simplefilter("ignore")

# file
__file__ = "/Users/echiarot/Documents/GitHub/2050-Calculators/PathwayCalc/_database/pre_processing/industry/eu/python/industry_lever_material-efficiency.py"

# directories
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# create dm
countries = ['Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark',
             'EU27','Estonia','Finland','France','Germany','Greece','Hungary','Ireland','Italy',
             'Latvia','Lithuania','Luxembourg','Malta','Netherlands','Poland','Portugal',
             'Romania','Slovakia','Slovenia','Spain','Sweden','United Kingdom']
years = list(range(1990,2023+1,1))
years = years + list(range(2025, 2050+1, 5))
variabs = ['aluminium', 'ammonia', 'cement', 'chem', 'copper', 'fbt', 'glass', 'lime', 
           'mae', 'ois', 'other', 'paper', 'steel', 'textiles', 'timber', 'tra-equip', 'wwp']
variabs = ["material-efficiency_" + i for i in variabs]
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

# make nan for other than EU27, as for EU for the moment we keep BAU which is 0
countries_oth = np.array(countries)[[i not in "EU27" for i in countries]].tolist()
idx = dm.idx
years = list(range(2025, 2050+1, 5))
for c in countries_oth:
    for y in years:
        for v in variabs:
            dm.array[idx[c],idx[y],idx[v]] = np.nan
df = dm.write_df()

# deepen
dm.deepen()

# set years
years_ots = list(range(1990,2023+1))
years_fts = list(range(2025,2055,5))

###############
##### OTS #####
###############

dm_ots = dm.filter({"Years" : years_ots})

#######################
##### FTS LEVEL 1 #####
#######################

# level 1: continuing as is
dm_fts_level1 = dm.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 2 #####
#######################

# TODO: level 2 to do, for the moment we set it continuing as is
dm_fts_level2 = dm.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 3 #####
#######################

# TODO: level 3 to do, for the moment we set it continuing as is
dm_fts_level3 = dm.filter({"Years" : years_fts})

#######################
##### FTS LEVEL 4 #####
#######################

# we take levels for 2050 from eucalc, and do a linear trend for 2025-2050
dm_level4 = dm.copy()
idx = dm_level4.idx
years_fts = list(range(2025,2055,5))
for y in years_fts:
    dm_level4.array[idx["EU27"],idx[y],:,:] = np.nan
dm_level4.array[idx["EU27"],idx[2050],:,idx["steel"]] = 0.33
dm_level4.array[idx["EU27"],idx[2050],:,idx["cement"]] = 0.20
dm_level4.array[idx["EU27"],idx[2050],:,idx["ammonia"]] = 0.10
dm_level4.array[idx["EU27"],idx[2050],:,idx["chem"]] = 0.30
dm_level4.array[idx["EU27"],idx[2050],:,idx["paper"]] = 0.10
dm_level4.array[idx["EU27"],idx[2050],:,idx["aluminium"]] = 0.14
dm_level4.array[idx["EU27"],idx[2050],:,idx["glass"]] = 0.12
dm_level4.array[idx["EU27"],idx[2050],:,idx["lime"]] = 0.14
dm_level4.array[idx["EU27"],idx[2050],:,idx["copper"]] = 0.14
dm_level4 = linear_fitting(dm_level4, years_fts)
# dm_level4.filter({"Country" : ["EU27"]}).flatten().datamatrix_plot()
dm_fts_level4 = dm_level4.filter({"Years" : years_fts})
# dm_fts_level4.filter({"Country" : ["EU27"]}).flatten().datamatrix_plot()

################
##### SAVE #####
################

DM_fts = {1: dm_fts_level1.copy(), 2: dm_fts_level2.copy(), 3: dm_fts_level3.copy(), 4: dm_fts_level4.copy()}
DM = {"ots" : dm_ots,
      "fts" : DM_fts}
f = os.path.join(current_file_directory, '../data/datamatrix/lever_material-efficiency.pickle')
with open(f, 'wb') as handle:
    pickle.dump(DM, handle, protocol=pickle.HIGHEST_PROTOCOL)


