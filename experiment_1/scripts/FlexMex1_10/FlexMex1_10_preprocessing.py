import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.preprocessing import (
    create_default_elements, update_shortage, update_load,
    update_link, update_wind_onshore, update_wind_offshore, update_solar_pv, create_load_profiles,
    create_wind_onshore_profiles, create_wind_offshore_profiles, create_solar_pv_profiles)
from oemoflex.helpers import get_experiment_paths, get_dir_diff


name = 'FlexMex1_10'

# Get paths
abspath = os.path.abspath(os.path.dirname(__file__))

path_config = os.path.join(abspath, '../../config.yml')

experiment_paths = get_experiment_paths(name, path_config)

data_raw_path = experiment_paths['data_raw']

data_preprocessed_path = os.path.join(experiment_paths['data_preprocessed'], 'data')

logpath = define_logging(
    logpath=experiment_paths['results_postprocessed'],
    logfile='oemoflex.log'
)

if not os.path.exists(data_preprocessed_path):
    for subdir in ['elements', 'sequences']:
        os.makedirs(os.path.join(data_preprocessed_path, subdir))


def main():
    # Load common input parameters
    scalars = pd.read_csv(os.path.join(experiment_paths['data_raw'], 'Scalars.csv'), header=0)

    # Prepare oemof.tabular input CSV files
    create_default_elements(os.path.join(data_preprocessed_path, 'elements'))

    # update elements
    update_shortage(data_preprocessed_path)
    update_load(data_preprocessed_path, scalars)
    update_wind_onshore(data_preprocessed_path, scalars)
    update_wind_offshore(data_preprocessed_path, scalars)
    update_solar_pv(data_preprocessed_path, scalars)
    update_link(data_preprocessed_path, scalars)

    # create sequences
    create_load_profiles(data_raw_path, data_preprocessed_path)
    create_wind_onshore_profiles(data_raw_path, data_preprocessed_path)
    create_wind_offshore_profiles(data_raw_path, data_preprocessed_path)
    create_solar_pv_profiles(data_raw_path, data_preprocessed_path)

    # compare with previous data
    previous_path = experiment_paths['data_preprocessed'] + '_default'
    new_path = experiment_paths['data_preprocessed']
    diff_output = get_dir_diff(new_path, previous_path, ignore_list=['*.log', '*.json'])
    logging.info(
        "Diff-checking the preprocessed data against '_default' directory:\n{}"
        .format(diff_output)
    )
    # check_if_csv_dirs_equal(new_path, previous_path, ignore=['log', 'json'])


if __name__ == '__main__':
    main()
