import requests
import numpy as np
from model.common.data_matrix_class import DataMatrix

def json_to_dm(data_json, mapping_dims, mapping_vars, units):
    # Number of dimensions in the key
    num_dimensions = len(data_json['data'][0]['key'])
    # Initialize a list of sets to store unique elements for each dimension
    dimension_sets = [set() for _ in range(num_dimensions)]

    # Iterate through each dictionary in the JSON data
    for entry in data_json['data']:
        key = entry['key']
        # Update each dimension's set with the current key's elements
        for i in range(num_dimensions):
            dimension_sets[i].add(key[i])
    del entry, key, i, num_dimensions

    # Convert sets to lists for the final output
    dimension_lists = [sorted(list(dimension_set)) for dimension_set in dimension_sets]
    del dimension_sets
    arr_shape = [len(l) for l in dimension_lists]
    arr_shape = tuple(arr_shape)
    arr = np.empty(arr_shape)
    for elem in data_json['data']:
        keys = elem['key']
        value = elem['values'][0]
        idx = []
        for dim in range(len(dimension_lists)):
            idx.append(dimension_lists[dim].index(keys[dim]))
        arr[tuple(idx)] = value
    del arr_shape, keys, value, elem, idx, dim

    map_tmp = {}
    for i, vars_json in enumerate(dimension_lists):
        dim_json = data_json['columns'][i]['text']
        vars_dm = [mapping_vars[dim_json][var] for var in vars_json]
        map_tmp[dim_json] = {'cols': vars_dm, 'axis': i}
    del vars_dm, dim_json, mapping_vars, i, vars_json, data_json, dimension_lists

    col_labels = {}
    dim_axis = {}
    for dim_dm, dim_json in mapping_dims.items():
        col_labels[dim_dm] = map_tmp[dim_json]['cols']
        dim_axis[dim_dm] = map_tmp[dim_json]['axis']
    del dim_dm, dim_json, mapping_dims, map_tmp

    unit_vars = {}
    for i, var in enumerate(col_labels['Variables']):
        unit_vars[var] = units[i]

    # Turn years to int
    col_labels['Years'] = [int(y) for y in col_labels['Years']]
    dm = DataMatrix(col_labels, unit_vars)
    del col_labels, unit_vars, var, i, units

    # Re-order the axis of the numpy array
    new_order = list(range(len(arr.shape)))
    arr_shape = []
    for axis, dim in enumerate(dm.dim_labels):
        axis_json = dim_axis[dim]
        new_order[axis_json] = axis
        if axis != len(dm.dim_labels)-1:
            new_order[axis] = axis_json
        arr_shape.append(len(dm.col_labels[dim]))

    arr = np.transpose(arr, axes=new_order)
    arr = arr.reshape(tuple(arr_shape))

    dm.array = arr

    return dm


def get_data_api_CH(table_id, mode='example', filter=dict(), mapping_dims=dict(), units=[], language='en'):
    # Define the base URL and the specific table_id for the API endpoint
    base_url = "https://www.pxweb.bfs.admin.ch/api/v1"
    base_url_lan = f"{base_url}/{language}"
    url = f"{base_url_lan}/{table_id}/{table_id}.px"
    response_structure = requests.get(url)
    data_structure = response_structure.json()

    # Give as output the structure
    if mode == 'example':
        structure = {}
        for elem in data_structure['variables']:
            structure[elem['text']] = elem['valueTexts']
        title = data_structure['title']
        return structure, title
    # Extract data
    if mode == 'extract':
        if len(filter) == 0:
            raise ValueError(
                'You need to provide the parameters you want to extract as a dictionary based on the structure')
        query = []  # List of  dictionaries
        mapping = {}
        for elem in data_structure['variables']:
            extract = {}  # Dictionary with key 'code' and 'selection'
            extract['code'] = elem['code']  # Extract code name
            key = elem['text']  # Match element with input filter dictionary
            valuetext = filter[key]
            if isinstance(valuetext, str):
                index = elem['valueTexts'].index(valuetext)
                value = [elem['values'][index]]
            else:
                index = [elem['valueTexts'].index(val) for val in valuetext]
                value = [elem['values'][i] for i in index]
            mapping[elem['text']] = {v: vt for v, vt in
                                     zip(value, valuetext if isinstance(valuetext, list) else [valuetext])}
            extract['selection'] = {'filter': 'item', 'values': value}
            query.append(extract)
        payload = {
            "query": query,
            "response": {"format": "json"}
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            # Parse and print the JSON response
            data = response.json()
            dm = json_to_dm(data, mapping_dims, mapping_vars=mapping, units=units)
            return dm
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            print(response.text)
            return
