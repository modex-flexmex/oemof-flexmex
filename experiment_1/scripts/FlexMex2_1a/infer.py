"""
Run this script from the root directory of the datapackage to update
or create meta data.
"""
import logging

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building
from oemoflex.helpers import setup_experiment_paths


name = 'FlexMex2_1a'

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
                'heat-shortage',
                'heat-excess',
                'heat-demand',
                'heat-storage-large',
                'heat-storage-small',
                'wind-onshore',
                'wind-offshore',
                'solar-pv',
                'electricity-shortage',
                'electricity-curtailment',
                'electricity-demand',
                'electricity-h2_cavern',
                'electricity-liion_battery',
                'hydro-reservoir',
                'electricity-bev',
            ],
            'profile': [
                'wind-onshore',
                'wind-offshore',
                'solar-pv',
                'electricity-demand',
                'hydro-reservoir',
                'heat-demand',
            ],
            'from_to_bus': [
                'electricity-transmission',
                'ch4-gt',
                'uranium-nuclear-st',
                'ch4-boiler-small',
                'ch4-boiler-large',
                'electricity-pth',
                'electricity-heatpump-small',
                'electricity-heatpump-large',
            ],
            'chp': [
                'ch4-bpchp',
                'ch4-extchp',
            ],
            'efficiency': [
                'electricity-heatpump-large',
                'electricity-heatpump-small',
            ],
            'availability': ['electricity-bev'],
            'drive_power': ['electricity-bev'],
            'min_storage_level': ['electricity-bev'],
            'max_storage_level': ['electricity-bev'],
        },
        path=exp_paths.data_preprocessed
    )


if __name__ == '__main__':
    main()
