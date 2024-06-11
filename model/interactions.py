
from model.transport_module import transport
from model.lifestyles_module import lifestyles
from model.buildings_module import buildings
from model.minerals_module import minerals
from model.common.interface_class import Interface
from model.district_heating_module import district_heating
from model.agriculture_module import agriculture
from model.emissions_module import emissions
from model.climate_module import climate
from model.ammonia_module import ammonia
from model.industry_module import industry

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

    init_time = time.time()
    TPE = {}
    interface = Interface()
    start_time = time.time()
    TPE['climate'] = climate(lever_setting, years_setting, interface)
    logger.info('Execution time Climate: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['lifestyles'] = lifestyles(lever_setting, years_setting, interface)
    logger.info('Execution time Lifestyles: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['transport'] = transport(lever_setting, years_setting, interface)
    logger.info('Execution time Transport: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['buildings'] = buildings(lever_setting, years_setting, interface)
    logger.info('Execution time Buildings: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['industry'] = industry(lever_setting, years_setting, interface)
    logger.info('Execution time Industry: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['agriculture'] = agriculture(lever_setting, years_setting, interface)
    logger.info('Execution time Agriculture: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['ammonia'] = ammonia(lever_setting, years_setting, interface)
    logger.info('Execution time Ammonia: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['district-heating'] = district_heating(lever_setting, years_setting, interface)
    logger.info('Execution time District-Heating: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['minerals'] = minerals(interface)
    logger.info('Execution time Minerals: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()
    TPE['emissions'] = emissions(lever_setting, years_setting, interface)
    logger.info('Execution time Emissions: {0:.3g} s'.format(time.time() - start_time))
    start_time = time.time()

    logger.info('Execution time: {0:.3g} s'.format(time.time() - init_time))

    return TPE

