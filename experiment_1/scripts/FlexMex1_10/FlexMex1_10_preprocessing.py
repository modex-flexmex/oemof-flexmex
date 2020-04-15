import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.preprocessing import (
    create_default_elements, update_shortage, update_load,
    update_link, update_wind_onshore, update_wind_offshore, update_solar_pv, create_load_profiles,
    create_wind_onshore_profiles, create_wind_offshore_profiles, create_solar_pv_profiles)
from oemoflex.helpers import setup_experiment_paths, get_dir_diff


name = 'FlexMex1_10'

# Get paths
basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
exp_paths = setup_experiment_paths(name, basepath)

exp_paths.data_preprocessed = os.path.join(exp_paths.data_preprocessed, 'data')

logpath = define_logging(
    logpath=exp_paths['results_postprocessed'],
    logfile='oemoflex.log'
)

if not os.path.exists(exp_paths.data_preprocessed):
    for subdir in ['elements', 'sequences']:
        os.makedirs(os.path.join(exp_paths.data_preprocessed, subdir))


def main():
    # Load common input parameters
    scalars = pd.read_csv(os.path.join(exp_paths['data_raw'], 'Scalars.csv'), header=0)

    # Prepare oemof.tabular input CSV files
    create_default_elements(os.path.join(exp_paths.data_preprocessed, 'elements'))

    # update elements
    update_shortage(exp_paths.data_preprocessed)
    update_load(exp_paths.data_preprocessed, scalars)
    update_wind_onshore(exp_paths.data_preprocessed, scalars)
    update_wind_offshore(exp_paths.data_preprocessed, scalars)
    update_solar_pv(exp_paths.data_preprocessed, scalars)
    update_link(exp_paths.data_preprocessed, scalars)

    # create sequences
    create_load_profiles(exp_paths.data_raw, exp_paths.data_preprocessed)
    create_wind_onshore_profiles(exp_paths.data_raw, exp_paths.data_preprocessed)
    create_wind_offshore_profiles(exp_paths.data_raw, exp_paths.data_preprocessed)
    create_solar_pv_profiles(exp_paths.data_raw, exp_paths.data_preprocessed)

    # compare with previous data
    previous_path = exp_paths['data_preprocessed'] + '_default'
    new_path = exp_paths['data_preprocessed']
    diff_output = get_dir_diff(new_path, previous_path, ignore_list=['*.log', '*.json'])
    logging.info(
        "Diff-checking the preprocessed data against '_default' directory:\n{}"
        .format(diff_output)
    )
    # check_if_csv_dirs_equal(new_path, previous_path, ignore=['log', 'json'])


if __name__ == '__main__':
    main()
