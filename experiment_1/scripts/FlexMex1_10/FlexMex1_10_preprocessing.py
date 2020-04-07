import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.preprocessing import (
    datetimeindex, create_default_elements, update_shortage, update_load,
    update_link, update_wind_onshore, update_wind_offshore, update_solar_pv)
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


def combine_profiles(raw_profile_path, column_name):
    profile_file_list = sorted(os.listdir(raw_profile_path))

    profile_list = []
    for file in profile_file_list:
        region = file.split('_')[1]

        raw_load_profile = pd.read_csv(os.path.join(raw_profile_path, file), index_col=0)

        load_profile = raw_load_profile.iloc[:, 0]

        load_profile.name = region + '-' + column_name

        profile_list.append(load_profile)

    profile_df = pd.concat(profile_list, axis=1, sort=True)

    profile_df = profile_df.set_index(datetimeindex, drop=True)

    profile_df.index.name = 'timeindex'

    return profile_df


def create_load_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating load profiles")
    raw_load_profile_path = os.path.join(data_raw_path, 'Energy', 'FinalEnergy', 'Electricity')

    load_profile_df = combine_profiles(raw_load_profile_path, 'el-load-profile')

    load_profile_df.to_csv(os.path.join(data_preprocessed_path, 'sequences', 'load_profile.csv'))


def create_wind_onshore_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating wind-onshore profiles")
    raw_wind_onshore_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Wind', 'Onshore'
    )

    wind_onshore_profile_df = combine_profiles(
        raw_wind_onshore_profile_paths, 'el-wind-onshore-profile'
    )

    wind_onshore_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'wind-onshore_profile.csv')
    )


def create_wind_offshore_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating wind-offshore profiles")

    raw_wind_offshore_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Wind', 'Offshore'
    )

    wind_offshore_profile_df = combine_profiles(
        raw_wind_offshore_profile_paths, 'el-wind-offshore-profile'
    )

    wind_offshore_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'wind-offshore_profile.csv')
    )


def create_solar_pv_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating solar pv profiles")

    raw_solar_pv_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Solar', 'PV'
    )

    solar_pv_profile_df = combine_profiles(raw_solar_pv_profile_paths, 'el-solar-pv-profile')

    solar_pv_profile_df.to_csv(os.path.join(data_preprocessed_path, 'sequences', 'pv_profile.csv'))


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
