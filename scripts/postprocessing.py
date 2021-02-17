import logging
import sys

from addict import Dict

from oemof.tools.logger import define_logging

from oemoflex.postprocessing import run_postprocessing
from oemoflex.helpers import setup_experiment_paths, check_if_csv_dirs_equal, load_yaml


if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])

    paths = Dict()
    paths.data_raw = sys.argv[2]
    paths.data_preprocessed = sys.argv[3]
    paths.results_optimization = sys.argv[4]
    paths.results_template = sys.argv[5]
    paths.results_postprocessed = sys.argv[6]

    exp_paths = setup_experiment_paths(scenario_specs['scenario'])

    logpath = define_logging(
        logpath=exp_paths.results_postprocessed,
        logfile='oemoflex.log'
    )

    run_postprocessing(scenario_specs, paths)

    # compare with previous data
    previous_path = paths.results_postprocessed.replace('results', 'defaults')
    new_path = paths.results_postprocessed
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        logging.warning(e)
