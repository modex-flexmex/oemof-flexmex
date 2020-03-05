"""
Run this script from the root directory of the datapackage to update
or create meta data.
"""
import logging
import os

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building
from oemoflex.helpers import get_experiment_paths


name = 'FlexMex1_10'

abspath = os.path.abspath(os.path.dirname(__file__))

path_config = os.path.join(abspath, '../../config.yml')

experiment_paths = get_experiment_paths(name, path_config)

logpath = define_logging(
    logpath=experiment_paths['results_postprocessed'],
    logfile='oemoflex.log'
)


def main():
    r"""Infer the metadata of the datapackage"""
    logging.info("Inferring the metadata of the datapackage")
    building.infer_metadata(
        package_name='oemof-tabular-dispatch-example',
        foreign_keys={
            'bus': [
                'wind-onshore',
                'wind-offshore',
                'pv',
                'shortage',
                'curtailment',
                'storage',
                'load',
            ],
            'profile': [
                'wind-onshore',
                'wind-offshore',
                'pv',
                'load',
            ],
            'from_to_bus': ['link'],
        },
        path=experiment_paths['data_preprocessed']
    )


if __name__ == '__main__':
    main()
