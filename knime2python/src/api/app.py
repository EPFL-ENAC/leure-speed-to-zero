import warnings

from flask_restful import Api
from flask import Flask
from knime2python.src.api.endpoints import Levers, Results, Outputs, Lever_details
from model.interactions import runner
from model.common.auxiliary_functions import filter_geoscale

from knime2python.src.api.model import Model
import os
import coloredlogs
import logging
import sys
import pandas as pd
import yaml
from knime2python.src.api.database import Database
import numpy as np
import pickle
from knime2python.src.api.utils import get_size
import json


def build_api(levers_df, levers_list, model, output_df, country_codes, output_list):
    """
    Build the EUCalc API structure with all endpoints

    :param levers_df:
    :param levers_list:
    :param model:
    :param country_codes:
    :return:
    """
    app = Flask(__name__)
    api = Api(app)

    # Endpoint to get list of levers
    api.add_resource(Levers, '/api/v1.0/levers', resource_class_kwargs={'config_levers': levers_df[['code', 'title', 'group', 'headline']]})

    # Endpoint to get a single lever with all data
    api.add_resource(Lever_details, '/api/v1.0/lever_details', resource_class_kwargs={'config_levers': levers_df.replace({'Nan':None, np.nan:None}) })

    # Endpoint for model queries
    api.add_resource(Results, '/api/v1.0/results',
                     resource_class_kwargs={'config_levers': levers_list,
                                            'model': model,
                                            'country_code_conversion': country_codes,
                                            'output_list': output_list})

    # Endpoint to get the list of output metrics
    api.add_resource(Outputs, '/api/v1.0/outputs', resource_class_kwargs={'output_df': output_df})

    return app


def build_model(initial_scenario, levers_list, global_vars, output_nodes, suppress_run_logs, max_cache_size, cube_df, additional_scenarios=None, db=None, gtap_metrics=None):
    """
    Return a model that has been built and run one time. The run result is stored in the cache
    :param initial_scenario:
    :param levers_list:
    :param output_nodes:
    :param suppress_run_logs:
    :param max_cache_size:
    :param cube_df:
    :return:
    """
    logger = logging.getLogger(__name__)

    # Build the model
    logger.info('Python model build finished.')

    # Run the model with an initial scenario
    default_lever_position = {n: ('INTEGER', initial_scenario[d]) for d, n in enumerate(levers_list)}

    m = Model(output_nodes=output_nodes, global_vars=global_vars, cube_configuration=cube_df,
              suppress_run_logs=suppress_run_logs, max_cache_size=max_cache_size, db=db, gtap_metrics=gtap_metrics)

    if db is None:
        logger.info('Size of Python model in memory: {:,} bytes'.format(get_size(m)))

    logger.info('Run default scenarios')

    lever_positions = {i: j for i, j in zip(levers_list,
                                            initial_scenario)}  # converting the scenario into a dictionnary of lever_position allow to remove the duplicates values in the lever list

    filter_geoscale(global_vars)

    first_run = runner(lever_positions, m.global_vars, m.output_nodes, m.logger)

    # Keep only selected output_nodes from the run
    first_run = {key: first_run[key] for key in output_nodes}

    # FIXME: replace REF by the name of the scenario from the configuration file
    m.save_to_cache(tuple(lever_positions.values()), first_run, first_run=True, gtap_name="EUREF")
    if db is None:
        logger.info('Size of Python model after firs run in memory: {:,} bytes'.format(get_size(m)))
    logger.info('Initial scenario run finished.')

    # Add rest of the default scenarios to the model
    if additional_scenarios is not None:
        for key, value in additional_scenarios.items():
            lever_positions = {i: j for i, j in zip(levers_list, value)} # converting the scenario into a dictionnary of lever_position allow to remove the duplicates values in the lever list
            lever_position_string = ''.join(str(x) for x in tuple(lever_positions.values()))
            if not m.exist_in_cache(tuple(lever_positions.values())):
                logger.info("Extra scenario run with following levers position: " + lever_position_string)
                run_output = runner(lever_positions, m.global_vars, m.output_nodes, m.logger)
                # Keep only selected output_nodes from the run
                run_output = {key: run_output[key] for key in output_nodes}
                m.save_to_cache(tuple(lever_positions.values()), run_output, gtap_name=key)
            else:
                # if the scenario is already saved in the cache then we don't run the model
                logger.info("Extra scenario already exists in cache: "+lever_position_string)
                m.save_to_cache(tuple(lever_positions.values()), None, gtap_name=key)

    logger.info('End of default scenarios run.')

    return m


def build_app(cfg_file, bypass_model = False, extra_scenarios=True):
    warnings.filterwarnings("ignore")
    # Load configuration
    with open(cfg_file, 'r') as f:
        cfg = yaml.full_load(f)

    try:
        log_level = cfg['log']['level']
    except:
        log_level = 'NOTSET'

    log_format = '%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.install(level=log_level, stream=sys.stdout, fmt=log_format)
    logger = logging.getLogger(__name__)

    logger.info('Configuration loaded: {}'.format(cfg))

    try:
        suppress_run_logs = cfg['log']['suppress_run_logs']
    except KeyError:
        suppress_run_logs = False

    try:
        log_file = cfg['log']['file']
    except:
        pass
    else:
        fh = logging.FileHandler(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', log_file), encoding='UTF-8')
        fh.setFormatter(logging.Formatter(log_format))
        logging.root.addHandler(fh)

    if logger.level == logging.DEBUG:
        logger.warning('Debug level set to {}, this will generate massive logs.'.format(logger.level))

    # Create database connection object
    if cfg["model"]["db_caching"]:
        db = Database(**cfg['database'])
        if cfg["model"]["reset_db"]:
            db.recreate_db()
    else:
        db = None
        if bypass_model:
            logger.exception("A DB connection is mandatory to run the api_db.")

    # Load lever definition from Excel file
    levers_df = pd.read_excel(io=cfg.get('model').get('interfaces').get('file'),
                              sheet_name=cfg.get('model').get('interfaces').get('levers_sheet'),
                              header=0,
                              ).dropna(subset=['code']) #[['code', 'title', 'group', 'headline']]

    levers_list = list(levers_df['code'])

    logger.info('Levers configuration loaded ({} levers): {}'.format(len(levers_list), levers_list))

    # Load output variable definition from Excel file
    output_df = pd.read_excel(io=cfg.get('model').get('interfaces').get('file'),
                              sheet_name=cfg.get('model').get('interfaces').get('cube_sheet'),
                              header=0,
                              ).dropna(subset=['column'])

    output_df['display_name'].fillna(value='', inplace=True)

    logger.info('Cube configuration loaded ({} metrics)'.format(len(output_df)))

    # Create simplified list to use in Results endpoint
    output_list = output_df[['column', 'display_name']].set_index('column').to_dict('index')
    output_list = {k:v['display_name'] for k, v in output_list.items()}

    output_nodes = cfg['model']['prod']['output_nodes']
    max_cache_size = cfg['model']['max_cache_size']
    gtap_metrics = cfg['model']['GTAP']['metrics']
    gtap_scenarios = cfg['model']['GTAP']['scenarios']
    gtap_scenarios_withoutREF = {key: value for key, value in gtap_scenarios.items() if key not in ["EUREF"]}
    global_vars = {}
    global_vars['years_setting'] = cfg['model']['years']
    global_vars['geoscale'] = cfg['model']['geoscale']

    if extra_scenarios:
        m = build_model(gtap_scenarios['EUREF'], levers_list, global_vars, output_nodes, suppress_run_logs,
                      max_cache_size, output_df, additional_scenarios=gtap_scenarios_withoutREF, db=db, gtap_metrics=gtap_metrics)
    else:
        m = build_model(gtap_scenarios['EUREF'], levers_list, global_vars, output_nodes, suppress_run_logs,
                      max_cache_size, output_df, db=db, gtap_metrics=gtap_metrics)

    if db is None:
        logger.info('Size of Python model in memory: {:,} bytes'.format(get_size(m)))

    country_codes = cfg['api']['country_codes']

    # Build the API
    return build_api(levers_df, levers_list, m, output_df, country_codes, output_list)
