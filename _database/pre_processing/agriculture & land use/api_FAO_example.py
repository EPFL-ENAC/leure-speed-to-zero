import faostat
# README on how to use faostat available at
# Step 1. Install faostat package
# https://pypi.org/project/faostat/
ld = faostat.list_datasets()
code = 'FBS'
pars = faostat.list_pars(code)
my_pars = {
    'area': faostat.get_par(code, 'area')['Switzerland'],
    'element': faostat.get_par(code, 'elements')['Production Quantity'],
    'item': faostat.get_par(code, 'item')['Wheat and products']
}

df = faostat.get_data_df(code, pars=my_pars, strval=False)

print(df.head())