import time
import logging
import pandas as pd
from knime2python.src.api.utils import get_size
import pickle
import zlib
from model.interactions import runner


class Model():
    """Class representing a EUCalc model, that can be configured either with a Knime or a Python model backend
    upon initialization.
    The methods perform as little modifications on the results of the model as possible, leaving any aggregation
    or translations to the API.
    """

    def __init__(self, output_nodes=None, global_vars=None, cube_configuration=None, db=None,
                 suppress_run_logs=False, max_cache_size=10, gtap_metrics=None):
        # Variables for the Python backend
        self.global_vars = global_vars
        self.output_nodes = output_nodes

        # Variables for the Knime backend
        self.suppress_run_logs = suppress_run_logs
        self.db = db

        # Generic variables
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.col_map = {}
        self.max_cache_size = max_cache_size

        # GTAP variables
        self.gtap_metrics = gtap_metrics
        self.gtap_scenario_dict = {}
        self.gtap_scenarios = []

        # Column IDs
        self.column_column = "column"
        id_column = "aggregation_id"
        id_list_column = "list_of_ids_to_aggregate"
        self.id_table = "table_type"

        cube_definition = cube_configuration[[self.column_column, id_column, id_list_column, self.id_table]]

        self.id_table_df = cube_definition[[self.column_column, self.id_table]]

        # Split the calculated metrics from the cube definition
        calculated_metrics = cube_definition.loc[cube_definition[id_list_column].notna(), :] \
            .set_index(self.column_column) \
            .drop(columns=id_column)
        calculated_metrics[id_list_column]=calculated_metrics[id_list_column].astype(str)
        self.logger.debug('The following columns will be calculated: {}'.format(calculated_metrics.index.tolist()))

        non_calculated_metrics = cube_definition.loc[cube_definition[id_list_column].isna(), :] \
            .drop(columns=id_list_column)


        # Pivot IDs in the "list" column to columns
        cm = pd.DataFrame(calculated_metrics[id_list_column].str.split(';').tolist(),
                         columns=range(max(calculated_metrics.apply(lambda x: len(x[id_list_column].split(';')), axis='columns'))),
                          index=calculated_metrics.index)

        # Merge with the non calculated list
        cs = pd.DataFrame(cm.stack().astype(float).astype(int)).reset_index().merge(non_calculated_metrics, how='left', left_on=0,
                                                                 right_on=id_column,
                                                                 suffixes=['_to_aggregate', '_source'])[[self.column_column+'_to_aggregate', self.column_column+'_source']]

        # Create map
        self.calculated_columns_map = {}
        for metric, df in cs.groupby(by=[self.column_column+'_to_aggregate']):
            self.calculated_columns_map[metric] = df[self.column_column+'_source'].tolist()
        self.logger.debug('Calculated column map: {}'.format(self.calculated_columns_map))

    def energy_value_by_sector(self, run_output):
        df_energy = self.cube_transformation(self.gtap_metrics, run_output)["timeseries_1990_2050"]
        df_energy_2050 = df_energy.loc[df_energy["Years"]=="2050",:]
        df_energy_2050_total = df_energy_2050.drop(["Country","Years"], axis=1).sum()
        return df_energy_2050_total

    def energy_value(self, E_scenario_values):
        E_value_sectors = []
        for metric in self.gtap_metrics:
            E_value_sector = E_scenario_values[metric]/sum(E_scenario_values[self.gtap_metrics])-self.E_REF_values[metric]/sum(self.E_REF_values[self.gtap_metrics])
            E_value_sectors.append(E_value_sector)
        E_value = sum([i**2 for i in E_value_sectors])
        return E_value

    def nearest_value(self, E_value):
        init = True
        for scenario in self.gtap_scenarios:
            if init:
                init = False
                value = abs(E_value-self.gtap_scenario_dict[scenario][1])
                name = self.gtap_scenario_dict[scenario][0]
            else:
                value_new = abs(E_value-self.gtap_scenario_dict[scenario][1])
                if value_new < value:
                    value = value_new
                    name = self.gtap_scenario_dict[scenario][0]
        return name

    def save_to_cache(self, lever_position_tuple, run_output, first_run=False, gtap_name=None):
        time_start = time.time()
        lever_position_string = ''.join(str(x) for x in lever_position_tuple)

        if run_output is None and gtap_name is not None:
            # if we restart the model with restarting the db, it may occur that we don't need to re-run all the
            # pre-defined GTAP scenarios as they are in the db. We retrieve them from the db to fill the gtap dict
            run_output = self.get_from_cache(lever_position_tuple)
        else:
            if self.db is not None:
                self.logger.info('Data saving in database. Levers position ID:' + lever_position_string)
                self.db.save_cache_db(lever_position_string, zlib.compress(pickle.dumps(run_output)), first_run)
                self.logger.info('Time for saving in database: {0:.3g} s'.format(time.time() - time_start))
            else:
                self.logger.info('Data saving cache. Levers position ID:' + lever_position_string)
                self.cache[lever_position_tuple] = zlib.compress(pickle.dumps(run_output))
                self.logger.info('Size of cache in memory: {:,} bytes'.format(get_size(self.cache)))
                self.logger.info('Time for saving in cache: {0:.3g} s'.format(time.time() - time_start))

        if gtap_name is not None:
            self.gtap_scenarios.append(lever_position_string)
            if first_run: # FIXME: the first run is considered to be the REF scenario
                self.E_REF_values = self.energy_value_by_sector(run_output)
                self.gtap_scenario_dict[lever_position_string] = [gtap_name, 0]
            else:
                E_scenario_values = self.energy_value_by_sector(run_output)
                E_value = self.energy_value(E_scenario_values)
                self.gtap_scenario_dict[lever_position_string] = [gtap_name,E_value]
        else:
            E_scenario_values = self.energy_value_by_sector(run_output)
            E_value = self.energy_value(E_scenario_values)
            gtap_name = self.nearest_value(E_value)
            self.gtap_scenario_dict[lever_position_string] = [gtap_name, E_value]

    def get_from_cache(self, lever_position_tuple):
        time_start = time.time()
        lever_position_string = ''.join(str(x) for x in lever_position_tuple)
        if self.db is not None:
            results = pickle.loads(zlib.decompress(self.db.query_cache_db(lever_position_string)))

            self.logger.info('Time for retrieving from database: {0:.3g} s'.format(time.time() - time_start))
        else:
            results = pickle.loads(zlib.decompress(self.cache[lever_position_tuple]))
            self.logger.info('Time for retrieving from cache: {0:.3g} s'.format(time.time() - time_start))

        return results

    def exist_in_cache(self, lever_position_tuple):
        if self.db is not None:
            lever_position_string = ''.join(str(x) for x in lever_position_tuple)
            return self.db.scenario_in_db(lever_position_string)
        else:
            return lever_position_tuple in self.cache


    def get_results(self, lever_position, output_columns, lever_position_tuple, lever_positions_type):
        """Public method to get the results from a model. The method decides which model type (Knime or python) to use
        based on the available variables in the instance.

        :param lever_position: dict of lever positions, will be passed to the model without check
        :param output_columns: list of output columns, will be passed to the model without check
        :return: DataFrame with requested columns, in addition to 'Years' and 'Country'

        """
        self.logger.debug('Using Python backend')
        return self._get_results_python(lever_position, output_columns, lever_position_tuple, lever_positions_type)

    def _get_results_python(self, lever_position, output_columns, lever_position_tuple, lever_positions_type):
        """Get results from a Python backend, using a graph object that was passed during object initialization.

        :param lever_position: dict of lever positions to run the model with
        :param output_columns: list of output columns to be extracted from the output data
        :return: DataFrame

        """

        start_time = time.time()

        if self.exist_in_cache(lever_position_tuple):
            ####################################################
            run_output = self.get_from_cache(lever_position_tuple)
            ####################################################
            # output_dict = self.get_from_cache(lever_position_tuple)
            # time_here = time.time()
            ####################################################
            if self.db is None:
                self.logger.info('Data fetched from cache. Number of elements in cache: {}'.format(len(self.cache)))
            else:
                self.logger.info('Data fetched from database.')

        else:
            # Format JSON input to be like flow variables in Knime
            if lever_positions_type == "Default":
                lever_position_knime_style = {d: ('INTEGER', lever_position[d]) for d in lever_position}
            else:
                lever_position_knime_style = {d: ('DICTIONARY', lever_position[d]) for d in lever_position}

            try:
                if self.suppress_run_logs:
                    logging.disable(level=logging.CRITICAL)

                # Pandas generates a warning when we set data on a copy of a dataframe. The objective is to
                # warn the user who would want to modify the original dataframe through the copy.
                # Since this is not a typical practice, we disable the warning, which speeds up the run.
                pd.options.mode.chained_assignment = None

                run_output = runner(lever_position, self.global_vars, self.output_nodes, self.logger)

                if self.suppress_run_logs:
                    logging.disable(level=logging.NOTSET)
            except:
                self.logger.exception('An error occurred while running the model.')
                raise

            # If size of the cache is beyond maximum allowed size.
            if len(self.cache) >= self.max_cache_size:
                # Deletes earlier values in the dict, except predefined scenarios
                # (as of Python 3.6 dicts preserve the order of the elements
                self.logger.info('Cache is full. Deleting older lever position results without removing default scenarios.')
                del self.cache[list(self.cache.keys())[4]] #FIXME: replace 4 by the lenght of existing scenarios
            # Remove un-wanted output of the model
            run_output = {key: run_output[key] for key in self.output_nodes}

            ####################################################
            self.save_to_cache(lever_position_tuple, run_output)
            ####################################################

###################### TEMPORARY SAVE CALCULATED OUTPUT TO CACHE ##################################"

        time_here = time.time()

        output_dict = self.cube_transformation(output_columns, run_output)

        self.logger.debug('Time for output loops: {0:.3g} s'.format(time.time() - time_here))
        self.logger.info('Execution time: {0:.3g} s'.format(time.time() - start_time))

        # FIXME: should return the correct name
        return output_dict, "EUREF"   # self.gtap_scenario_dict[''.join(str(x) for x in lever_position_tuple)][0]

    def cube_transformation(self, output_columns, run_output):
        # Build a map of which dataframe holds which columns
        self.col_map = {}
        # Check for duplicated columns and not existing output nodes
        for node in self.output_nodes:
            output_df = run_output.get(node)
            if output_df is not None:
                for i in list(output_df.columns):
                    if self.col_map.get(i):
                        # If metric already exist in the column map
                        if i not in ['Country', 'Years']:
                            self.logger.error(
                                'Duplicated columns found when merging data output: {col} found in the output of nodes {n1} (kept) and {n2} (dropped)'.format(
                                    col=i, n1=self.col_map[i], n2=node))
                    else:

                        self.col_map[i] = node
            else:
                self.logger.error('Specified node doesn\'t exist in the output of the workflow: {}'.format(node))
        self.logger.debug('Column map: {}'.format(self.col_map))
        output_dict = {}
        for id_df in self.id_table_df[self.id_table].unique():
            # Extracts columns from the list using col_map and joins them in a single DataFrame
            output_df = pd.DataFrame()
            # all the warnings are sent to the TPE while only the metric requested are sent
            if id_df == "warning":
                col_id_table = [col for col in self.id_table_df.loc[
                    self.id_table_df[self.id_table] == id_df, self.column_column].values]
            # the cumulative emissions are sent to the TPE by default
            elif id_df == "singlevalue_2100":
                col_id_table = [col for col in self.id_table_df.loc[
                    self.id_table_df[self.id_table] == id_df, self.column_column].values]
            else:
                col_id_table = [col for col in output_columns if col in self.id_table_df.loc[
                    self.id_table_df[self.id_table] == id_df, self.column_column].values]
            for col in col_id_table:
                if col in self.calculated_columns_map:
                    # First check in calculated columns
                    temp_df = None

                    # Validate the columns to aggregate
                    columns_to_aggregate = self.calculated_columns_map.get(col)
                    self.logger.debug(
                        'Columns to sum to calculate calculated metric "{}": {}'.format(col, columns_to_aggregate))
                    missing_columns = set(columns_to_aggregate) - set(self.col_map)

                    if len(missing_columns) > 0:
                        self.logger.error('Missing columns for summing: {}'.format(missing_columns))
                    else:
                        for c in columns_to_aggregate:
                            # Build the temp_df that holds the requested columns for calculation
                            if c not in self.col_map:
                                # In case one of the columns to aggregate is not found, return error
                                message = 'While calculating column [{}]. the following column was not found in the model output: {}'.format(
                                    col, c)
                                self.logger.error(message)
                                raise Exception(message)
                            else:
                                col_list2 = ['Country', 'Years', c]
                                if temp_df is None:
                                    temp_df = run_output[self.col_map[c]].loc[:, col_list2]
                                else:
                                    temp_df = temp_df.merge(run_output[self.col_map[c]].loc[:, col_list2],
                                                            on=['Country', 'Years'],
                                                            how='outer')
                        # Sums results and add to main df
                        if output_df.empty:
                            output_df = temp_df.set_index(['Country', 'Years']).agg(sum, axis='columns').rename(
                                col).reset_index()
                        else:
                            output_df = output_df.merge(
                                temp_df.set_index(['Country', 'Years']).agg(sum, axis='columns').rename(
                                    col).reset_index(), on=['Country', 'Years'], how='outer')
                else:
                    # If not a calculated metric, try go get it from the output directly
                    node = self.col_map.get(col)
                    if node:
                        # Fixme use index instead of list of cols
                        col_list = ['Country', 'Years', col]

                        if output_df.empty:
                            if id_df == "warning":
                                # if it is a warning, there is no need for the Country and Years column
                                output_df = run_output[node].loc[:, [col]]
                            elif "regions" in id_df:
                                output_df = run_output[node].loc[:, ['Country', 'Years', 'Region', col]]
                            else:
                                output_df = run_output[node].loc[:, col_list]
                        else:
                            if id_df == "warning":
                                output_df = output_df.join(run_output[node].loc[:, [col]])
                            elif "regions" in id_df:
                                output_df = output_df.merge(
                                    run_output[node].loc[:, ['Country', 'Years', 'Region', col]],
                                    on=['Country', 'Years', 'Region'],
                                    how='outer')
                            else:
                                output_df = output_df.merge(run_output[node].loc[:, col_list], on=['Country', 'Years'],
                                                            how='outer')
                    else:
                        self.logger.error('The metric requested was not found: {} '.format(col))
            output_dict[id_df] = output_df

        return output_dict


    @staticmethod
    def _format_results_from_db(data_object):
        """Format results from the database to a pandas DataFrame

        :param data_object: dict with "columns" = list and "data" = list of tuples
        :return: DataFrame without index
        """

        return pd.DataFrame(data_object.get('data'), columns=data_object.get('columns'))


