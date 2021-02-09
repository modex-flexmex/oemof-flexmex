import logging
import sys

from oemof.tools.logger import define_logging

from oemoflex.postprocessing import run_postprocessing
from oemoflex.helpers import setup_experiment_paths, check_if_csv_dirs_equal, load_yaml


if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])

    exp_paths = setup_experiment_paths(scenario_specs['scenario'])

    logpath = define_logging(
        logpath=exp_paths.results_postprocessed,
        logfile='oemoflex.log'
    )

    run_postprocessing(scenario_specs, exp_paths)

    # compare with previous data
    previous_path = exp_paths.results_postprocessed.replace('results', 'defaults')
    new_path = exp_paths.results_postprocessed
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        logging.error(e)
