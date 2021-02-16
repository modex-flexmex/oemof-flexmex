import logging
import os

import pandas as pd

from oemoflex.helpers import load_yaml


# Path definitions
module_path = os.path.dirname(os.path.abspath(__file__))

MODEL_CONFIG = 'model_config'

PATH_MAPPINGS_REL = '../flexmex_config'

path_oemof_tabular_settings = os.path.join(
    module_path, MODEL_CONFIG, 'oemof-tabular-settings.yml')

path_mappings = os.path.abspath(os.path.join(module_path, PATH_MAPPINGS_REL))

path_mapping_input_timeseries = os.path.join(path_mappings, 'mapping-input-timeseries.yml')

# Load configs
oemof_tabular_settings = load_yaml(path_oemof_tabular_settings)

# Define time index and regions
datetimeindex = pd.date_range(start='2019-01-01', freq='H', periods=8760)

mapping = load_yaml(path_mapping_input_timeseries)


def combine_profiles(raw_profile_path, column_name):
    profile_file_list = sorted(os.listdir(raw_profile_path))

    profile_file_list = [file for file in profile_file_list if file.endswith('csv')]

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


def create_profiles(exp_path, select_components):

    def normalize_year(timeseries):
        r"""Normalizes the DataFrame 'timeseries' to values that add up to 1.0."""
        yearly_amount = timeseries.sum(axis=0)
        timeseries = timeseries.divide(yearly_amount)
        return timeseries

    recalculation_functions = {
        'normalize_year': normalize_year
    }

    sequences_dir = oemof_tabular_settings['sequences-dir']
    profile_file_suffix = oemof_tabular_settings['profile-file-suffix']
    profile_name_suffix = oemof_tabular_settings['profile-name-suffix']

    for component in select_components:

        try:
            profiles = mapping[component]['profiles']
        except KeyError:
            logging.info(f"No timeseries information found for '{component}'.")
        else:
            for profile_name, profile in profiles.items():
                logging.info(f"Creating '{profile_name}' timeseries for '{component}'.")

                profile_paths = os.path.join(exp_path.data_raw, profile['input-path'])

                profile_df = combine_profiles(profile_paths, profile_name + profile_name_suffix)

                if 'apply-function' in profile:
                    function_name = profile['apply-function']
                    recalc = recalculation_functions[function_name]
                    profile_df = recalc(profile_df)

                try:
                    output_filename_base = profile['output-name']
                except KeyError:
                    output_filename_base = profile_name

                profile_df.to_csv(
                    os.path.join(
                        exp_path.data_preprocessed,
                        sequences_dir,
                        output_filename_base + profile_file_suffix + '.csv')
                )
