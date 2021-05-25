import os
import sys

from oemof_flexmex.helpers import load_yaml, setup_logging
from oemof_flexmex.optimization import optimize

if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])
    data_preprocessed = sys.argv[2]
    results_optimization = sys.argv[3]
    logging_path = sys.argv[4]

    setup_logging(logging_path)

    if not os.path.exists(results_optimization):
        os.makedirs(results_optimization)

    optimize(data_preprocessed, results_optimization)
