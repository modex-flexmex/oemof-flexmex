"""
"""
import os

from oemof.tools.logger import define_logging

from oemoflex.helpers import setup_experiment_paths
from oemoflex.optimization import optimize


name = 'FlexMex1_7b'

exp_paths = setup_experiment_paths(name)

logpath = define_logging(
    logpath=exp_paths.results_postprocessed,
    logfile='oemoflex.log'
)


def main():
    optimize(exp_paths.data_preprocessed, exp_paths.results_optimization)


if __name__ == '__main__':
    main()
