
from model.transport_module import transport
from model.lifestyles_module import lifestyles

import math
import time
import os
import json


def runner(lever_setting, global_vars, output_nodes, logger):
    # get years setting from global variables
    years_setting = global_vars['years_setting']
    # lever setting dictionary convert float to integer
    lever_setting = {key: math.floor(value) for key, value in lever_setting.items()}
    # Transport module
    start_time = time.time()

    results_run = {}

    results_run['lifestyles'] = lifestyles(lever_setting, years_setting)
    results_run['transport'] = transport(lever_setting, years_setting)

    logger.info('Execution time TRANSPORT module: {0:.3g} s'.format(time.time() - start_time))

    return results_run

