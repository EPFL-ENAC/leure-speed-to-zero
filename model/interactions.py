
from model.transport_module import transport
from model.lifestyles_module import lifestyles
from model.buildings_module import buildings
from model.minerals_module import minerals
from model.common.interface_class import Interface

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

    TPE = {}
    interface = Interface()

    #TPE['lifestyles'] = lifestyles(lever_setting, years_setting, interface)
    TPE['transport'] = transport(lever_setting, years_setting, interface)
    TPE['buildings'] = buildings(lever_setting, years_setting, interface)
    TPE['minerals'] = minerals(lever_setting, years_setting, interface)

    logger.info('Execution time: {0:.3g} s'.format(time.time() - start_time))

    return TPE

