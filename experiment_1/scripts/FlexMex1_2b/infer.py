"""
Run this script from the root directory of the datapackage to update
or create meta data.
"""
import logging

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building
from oemoflex.helpers import setup_experiment_paths


name = 'FlexMex1_2b'

exp_paths = setup_experiment_paths(name)

logpath = define_logging(
    logpath=exp_paths.results_postprocessed,
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
                'solar-pv',
                'electricity-shortage',
                'electricity-curtailment',
                'electricity-demand',
                'electricity-h2_cavern',
                'electricity-liion_battery',
            ],
            'profile': [
                'wind-onshore',
                'wind-offshore',
                'solar-pv',
                'electricity-demand',
            ],
            'from_to_bus': [
                'ch4-gt'
            ],
        },
        path=exp_paths.data_preprocessed
    )


if __name__ == '__main__':
    main()
