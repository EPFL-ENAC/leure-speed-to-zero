import argparse
import os.path
import warnings

import yaml
from knime2python.src.api.app import build_app

# This script allows to initialize the database and start the API for EUCalc.

if __name__ == '__main__':
    warnings.filterwarnings("ignore")

    # Extract command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configuration", help="location of configuration file (defaults to config/config_eu.yml",
                        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'config','config_eu.yml'))

    parser.add_argument("--no-extra-scenarios", help="does not run extra scenarios, just the first one", action="store_true")

    run_args = parser.parse_args()
    run_args_dict = vars(run_args)

    # Load configuration, to get parameters to run the API
    with open(run_args_dict['configuration'], 'r') as f:
        cfg = yaml.full_load(f)

    # Run the API
    app = build_app(run_args_dict['configuration'], extra_scenarios = not run_args.no_extra_scenarios)

    app.run(port=cfg['api']['port'], threaded=False, host='0.0.0.0')  # For production

