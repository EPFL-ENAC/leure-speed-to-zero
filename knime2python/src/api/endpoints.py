import pandas as pd
from flask_restful import Resource
from flask import request
import logging
import numpy as np

class Levers(Resource):
    """Provide information on the levers implemented.

    """

    def __init__(self, **kwargs):
        """
        Create the Lever endpoint.

        :param config_levers: dataframe holding lever information
        """

        self.levers = kwargs['config_levers']

    def get(self):
        """
        Return information for all levers available.

        :return: All data columns present in the config_levers argument, in the format::

        ::

            [
                {'code': 'code', 'title': '', 'group': '', 'headline': '', },
                …
            ]
        """

        lever_code = request.args.get('code')
        if lever_code is not None:
            return self.levers[self.levers['code']==lever_code].to_dict('records')
        else:
            return self.levers.to_dict('records')

class Lever_details(Resource):
    """
    Provide information on a specific lever.
    """

    def __init__(self, **kwargs):
        """
        Create the Lever_details endpoint.

        :param config_levers: dataframe holding lever information
        """

        self.levers = kwargs['config_levers']

    def get(self):
        """
        Return detailed information about a specific lever

        :param code: HTTP request argument: lever code as defined in the configuration.
        :return: All data columns present in the config_levers argument, in the format:

        ::

            [
                {name:value, name: value, ... },
                …
            ]
        """

        lever_code = request.args.get('code')
        if lever_code is not None:
            return self.levers[self.levers['code']==lever_code].to_dict('records')
        else:
            return self.levers.to_dict('records')

class Outputs(Resource):
    """
    Provide the list of output variables available from the model or as calculated variables.
    """
    def __init__(self, **kwargs):
        """
        Create the Outputs endpoint.

        :param output_df: dataframe holding information about outputs
        """
        self.output_df = kwargs['output_df']

    def get(self):
        """
        Return information about output variables as defined in the configuration.

        :return: All data columns present in the output_df argument, in the format::

        ::

            [
                {'column': 'column', 'title': 'title},
                …
            ]
        """

        return self.output_df[['column', 'display_name']].to_dict('records')


class Results(Resource):
    """
    Provide results using a backend model provided at initialization time.
    """

    def __init__(self, **kwargs):
        """
        Create the Results endpoint.

        :param config_levers: list of lever codes
        :param model: initialised model
        :param country_code_conversion: dict of country codes like { country -> code }
        :param output_list: dict of output variables like { variable_code -> display_name }
        """

        self.levers = kwargs['config_levers']
        self.model = kwargs['model']
        self.country_code_conversion = kwargs['country_code_conversion']
        self.output_list = kwargs['output_list']
        self.logger = logging.getLogger(__name__)


    def post(self):
        """
        Trigger a model run.

        :param JSON request data:

        ::

            {
            "levers": {
                "default": [1,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
                "exceptions": {
                    "DE": [4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4]
                }
            },
            "outputs": [
                {
                    "id": "bld_residential-energy-demand_oil[TWh]"
                },
                {
                    "id": "ref_demand_fuel-oil_total[TWh]",
                    "allCountries": true
                },
                ]
            }

        :return: list of output variables like:

        ::

            [
                {'id': "metric,
                 'title': 'title',
                 "timeAxis": [1990, 1991, ...],
                 "data": {
                    "EU": [value, value, ...]
                    }
                }
            ]

        :raise:
            500 error returned to browser if:
                - lever JSON can't be decoded
                - if number of levers don't correspond to configuration
            Errors in the logs if:
                - A variable requested is not found in the model's output.

        """

        # Process request arguments
        json_data = request.get_json()
        # Decode lever position
        self.logger.debug('Incoming request JSON: {}'.format(json_data))

        try:
            lever_positions_default = json_data.get('levers').get('default')
            lever_positions_exceptions = json_data.get('levers').get('exceptions')
        except:
            err_message = 'Request JSON for lever positions could not be parsed.'
            self.logger.error(err_message)
            return {'message': err_message,
                    'json': json_data,
                    }, 500

        self.logger.info('Request parsed with default levers positions: {}'.format(lever_positions_default))
        self.logger.warning('Request parsed with exceptions to levers positions: {}'.format(
            lever_positions_exceptions))

        # Check levers for errors
        if len(self.levers) > len(lever_positions_default):
            err_message = 'Request levers do not include levers specified in configuration.'
            self.logger.error(err_message)
            return {'message': err_message,
                    'levers': lever_positions_default,
                    'configuration': list(self.levers)
                    }, 500
        elif len(self.levers) < len(lever_positions_default):
            self.logger.error('Too many levers provided compared to configuration.')

        # Combines internal list of levers with positions
        lever_positions_temp = {i: j for i, j in zip(self.levers, lever_positions_default)}
        lever_position_tuple = tuple(lever_positions_default)

        if lever_positions_exceptions is None or lever_positions_exceptions == {}:
            lever_positions_type = "Default"
            lever_positions = lever_positions_temp
        else:
            lever_positions_type = "Exception"
            country_table = pd.DataFrame(list(self.country_code_conversion.items()),
                                         columns=['Country', 'Country_code'])
            lever_positions = {i:{'default':j} for i,j in lever_positions_temp.items()}
            for country, levers in lever_positions_exceptions.items():
                #lever_positions_country = {}
                #lever_positions_country = {i:{country:j} for i, j in zip(self.levers, levers)}
                lever_positions_country = {i:{country_table.loc[country_table['Country_code']==country,"Country"].values[0]:j} for i, j in zip(self.levers, levers)}
                lever_position_tuple = lever_position_tuple +tuple(country)+ tuple(levers)
                for k in lever_positions:
                    if lever_positions_country[k][country_table.loc[country_table['Country_code']==country,"Country"].values[0]] != lever_positions[k]['default']:
                        lever_positions[k].update(lever_positions_country.get(k, {}))  # dict1.get(k).update(dict2.get(k, {}))

            # for i in range(len(self.levers)):
            #     country_table_temp = country_table.copy()
            #     value_default = lever_positions_default[i]
            #     key = self.levers[i]
            #     country_table_temp["levers"] = value_default
            #     for key_exception, value_exception in lever_positions_exceptions.items():
            #         country_table_temp.loc[country_table_temp["Country_code"] == key_exception, "levers"] = value_exception[i]
            #
            #     lever_positions[key] = country_table_temp
            #     lever_position_tuple = tuple(
            #         ''.join(str(e) for e in lever_positions_default) + list(lever_positions_exceptions.keys())[
            #             0] + ''.join(
            #             str(e) for e in lever_positions_exceptions[list(lever_positions_exceptions.keys())[0]]))

        # Decode outputs
        output_metrics = [m.get('id') for m in json_data.get('outputs')]
        output_metrics_not_aggregated = [m.get('id') for m in json_data.get('outputs') if m.get('allCountries') == True]
        self.logger.debug('Output metrics identified: {}'.format(output_metrics))

        # Get results
        try:
            results_dict, gtap_scenario = self.model.get_results(lever_positions, output_metrics,
                                                                 lever_position_tuple, lever_positions_type)
        except Exception as err:
            self.logger.exception('An error occurred when trying to get model results.')
            result = []
            raise
        else:
            if len(results_dict) == 0:
                self.logger.warning('The model returned an empty dataset.')
                result = []
            else:
                results_columns = [col for list_col in [results_dict[key].columns for key in results_dict] for col in list_col]
                # Check if some metrics were not found
                missing_metrics = set(output_metrics) - set(results_columns)

                if len(missing_metrics) > 0:
                    self.logger.warning('Some metrics were not found: {}'.format(missing_metrics))
                    output_metrics_not_aggregated = list(set(output_metrics_not_aggregated) - missing_metrics)
                result_output = []
                result_warning = []
                for key in results_dict:
                    results = results_dict[key]
                    try:
                        if len(results) != 0:
                            if key == "warning":
                                for column in results.columns:
                                    result_warning.append(
                                        {'id': column,
                                         "level": float(results.loc[0,column])
                                         }
                                    )
                            elif key == "singlevalue_2050minus2015_regions":
                                results.loc[:, 'Years'] = results['Years'].astype('int')
                                results.loc[:, 'Country'] = results.loc[:, 'Country'].map(self.country_code_conversion) + '_' + results.loc[:, 'Region']
                                results.drop(['Region'], axis='columns', inplace=True)
                                # Set Country and Years as index
                                results = results.set_index(['Country', 'Years'])
                                results = results.astype('float')
                                results = results.unstack(level='Country')
                                for metric, df in results.groupby(axis=1, level=0):
                                    frame = df[metric].reset_index().replace({np.nan:None}).to_dict(orient='list')
                                    result_output.append(
                                        {'id': metric,
                                         'title': self.output_list.get(metric, ''),
                                         "timeAxis": frame.pop('Years'),
                                         "data": frame
                                         }
                                    )
                            elif "singlevalue" in key:
                                results.loc[:, 'Years'] = results['Years'].astype('int')
                                results.loc[:, 'Country'] = results.loc[:, 'Country'].map(self.country_code_conversion)
                                # Set Country and Years as index
                                results = results.set_index(['Country', 'Years'])
                                results = results.astype('float')
                                results = results.unstack(level='Country')
                                for metric, df in results.groupby(axis=1, level=0):
                                    frame = df[metric].reset_index().replace({np.nan:None}).to_dict(orient='list')
                                    result_output.append(
                                        {'id': metric,
                                         'title': self.output_list.get(metric, ''),
                                         "timeAxis": frame.pop('Years'),
                                         "data": frame
                                         }
                                    )
                            elif key == "timeseries_1990_2050_regions":
                                #results.loc[:, 'Years'] = results.loc[:, 'Years'] + '_S' + results.loc[:, 'Semester'].astype('str')
                                #results.loc[:, 'Semester'] = results.loc[:, 'Semester'].astype('str')
                                results.loc[:, 'Country'] = results.loc[:, 'Country'].map(self.country_code_conversion) + '_' + results.loc[:, 'Region']
                                results.loc[:, 'Years'] = results['Years'].astype('int')
                                results.drop(['Region'], axis='columns', inplace=True)
                                # Set Country and Years as index
                                results = results.set_index(['Country', 'Years'])
                                results = results.astype('float')
                                #results = results.unstack(level='Semester')
                                #results.columns = ['_S'.join(col).strip() for col in results.columns.values]
                                results = results.unstack(level='Country')
                                for metric, df in results.groupby(axis=1, level=0):
                                    frame = df[metric].reset_index().replace({np.nan:None}).to_dict(orient='list')
                                    result_output.append(
                                        {'id': metric,
                                         'title': self.output_list.get(metric, ''),
                                         "timeAxis": frame.pop('Years'),
                                         "data": frame
                                         }
                                    )

                            else:
                                # Converts Years to integer
                                results.loc[:, 'Years'] = results['Years'].astype('int')
                                if key == "timeseries_2020_2050":
                                    results = results.loc[results.loc[:,'Years'] >= 2020,:]

                                # Convert country codes ##FIXME: why do we convert the names ?
                                results.loc[:, 'Country'] = results.loc[:, 'Country'].map(self.country_code_conversion)

                                # Set Country and Years as index
                                results = results.set_index(['Country', 'Years'])
                                results = results.astype('float')

                                output_metrics_not_aggregated_temp = [col for col in output_metrics_not_aggregated if col in results.columns]

                                # Separate columns to be aggregated over Country (default case)
                                results_non_aggregated = results[output_metrics_not_aggregated_temp].copy()
                                results_to_aggregate = results.drop(columns=output_metrics_not_aggregated_temp)

                                # Aggregates over Country
                                results_aggregated = results_to_aggregate.groupby(by='Years').sum()
                                results_non_aggregated_eu = results_non_aggregated.groupby(by='Years').sum()

                                # Keep data of exceptions countries
                                try:
                                    country_exceptions = list(lever_positions_exceptions.keys())
                                except Exception as e:
                                    self.logger.warning(e)
                                    country_exceptions = []


                                if country_exceptions == []:
                                    results_country_exceptions = results_to_aggregate.loc[:, :]
                                    results_country_exceptions = results_country_exceptions.unstack(level='Country')
                                else:
                                    try:
                                        results_country_exceptions = results_to_aggregate.loc[country_exceptions, :]
                                    except Exception:
                                        results_country_exceptions = results_to_aggregate.loc[:, :]
                                    results_country_exceptions = results_country_exceptions.unstack(level='Country')


                                # Pivot non-aggregated data on Country, the result is a multi column index (metric, country)
                                results_non_aggregated = results_non_aggregated.unstack(level='Country')

                                # Output of Non Aggregated Metrics
                                # Loop over the first level of the column index, the metrics
                                for metric, df in results_non_aggregated.groupby(axis=1, level=0):
                                    # This formats the DataFrame as a dict of countries, each holding a list of values, plus a Years item
                                    # We also replace NaN by None, so that it gives "null" in JSON.

                                    frame = df[metric].reset_index().replace({np.nan:None}).to_dict(orient='list')
                                    frame_eu = results_non_aggregated_eu.loc[:, metric].reset_index().to_dict(orient='list')
                                    frame["EU"] = frame_eu[metric]

                                    result_output.append(
                                        {'id': metric,
                                         'title': self.output_list.get(metric, ''),
                                         "timeAxis": frame.pop('Years'),
                                         "data": frame
                                         }
                                    )

                                # Output of Aggregated metrics
                                if country_exceptions != []:
                                    # Loop over the aggregated columns
                                    for metric, df in results_country_exceptions.groupby(axis=1, level=0):
                                        # This formats the DataFrame as a dict of countries, each holding a list of values, plus a Years item
                                        # Here we don't need to replace NaN since the sum is doing it by default.

                                        frame = df[metric].reset_index().replace({np.nan: None}).to_dict(orient='list')
                                        frame_eu = results_aggregated.loc[:, metric].reset_index().to_dict(orient='list')
                                        frame["EU"] = frame_eu[metric]

                                        result_output.append(
                                            {'id': metric,
                                             'title': self.output_list.get(metric, ''),
                                             "timeAxis": frame.pop('Years'),
                                             "data": frame
                                             }
                                        )
                                else:
                                    for metric in results_aggregated.columns:
                                        # This formats the DataFrame as a dict of countries, each holding a list of values, plus a Years item
                                        # Here we don't need to replace NaN since the sum is doing it by default.

                                        frame = results_aggregated.loc[:, metric].reset_index().to_dict(orient='list')

                                        result_output.append(
                                            {'id': metric,
                                             'title': self.output_list.get(metric, ''),
                                             "timeAxis": frame.pop('Years'),
                                             "data": {
                                                 # Aggregated metrics are labeled EU
                                                 "EU": frame[metric]
                                             }
                                             }
                                        )
                    except Exception as e:
                        self.logger.error("Error with the following metric: " + results.columns)
                result = {"outputs": result_output, "warnings":result_warning, "gtap_scenario":gtap_scenario}
        finally:
            # We need to always return a response even on server error
            return result
