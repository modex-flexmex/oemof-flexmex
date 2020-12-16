import sys

from oemof.tools.logger import define_logging

from oemoflex.helpers import load_yaml
from oemoflex.helpers import setup_experiment_paths
from oemoflex.optimization import optimize


if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])

    exp_paths = setup_experiment_paths(scenario_specs['name'])

    logpath = define_logging(
        logpath=exp_paths.results_postprocessed,
        logfile='oemoflex.log'
    )

    optimize(exp_paths.data_preprocessed, exp_paths.results_optimization)
