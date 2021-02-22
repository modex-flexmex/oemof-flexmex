import sys

from oemof.tools.logger import define_logging

from oemoflex.helpers import load_yaml
from oemoflex.helpers import setup_experiment_paths
from oemoflex.optimization import optimize


if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])
    data_preprocessed = sys.argv[2]
    results_optimization = sys.argv[3]
    logging_path = sys.argv[4]

    logpath = define_logging(
        logpath=logging_path,
        logfile='oemoflex.log'
    )

    optimize(data_preprocessed, results_optimization)
