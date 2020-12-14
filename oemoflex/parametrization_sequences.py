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


def create_electricity_demand_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating electricity demand profiles")
    raw_load_profile_path = os.path.join(data_raw_path, 'Energy', 'FinalEnergy', 'Electricity')

    load_profile_df = combine_profiles(raw_load_profile_path, 'electricity-demand-profile')

    load_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'electricity-demand_profile.csv')
    )


def create_heat_demand_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating heat demand profiles")
    raw_load_profile_path = os.path.join(data_raw_path, 'Energy', 'FinalEnergy', 'Heat')

    load_profile_df = combine_profiles(raw_load_profile_path, 'heat-demand-profile')

    load_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'heat-demand_profile.csv')
    )


def create_wind_onshore_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating wind-onshore profiles")
    raw_wind_onshore_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Wind', 'Onshore'
    )

    wind_onshore_profile_df = combine_profiles(
        raw_wind_onshore_profile_paths, 'wind-onshore-profile'
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
        raw_wind_offshore_profile_paths, 'wind-offshore-profile'
    )

    wind_offshore_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'wind-offshore_profile.csv')
    )


def create_solar_pv_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating solar pv profiles")

    raw_solar_pv_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Solar', 'PV'
    )

    solar_pv_profile_df = combine_profiles(raw_solar_pv_profile_paths, 'solar-pv-profile')

    solar_pv_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'solar-pv_profile.csv')
    )


def create_hydro_reservoir_profiles(data_raw_path, data_preprocessed_path):
    # TODO: Use this function to generalize the other create_profile functions.
    profile_name = 'hydro-reservoir_profile'
    raw_profile_spec = ['Energy', 'SecondaryEnergy', 'Hydro', 'Reservoir']

    logging.info(f"Creating {profile_name} profile")

    raw_profile_paths = os.path.join(
        data_raw_path, *raw_profile_spec
    )

    profile_df = combine_profiles(raw_profile_paths, profile_name)

    profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', profile_name + '.csv')
    )


def create_electricity_heatpump_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating electricity heatpump profiles")

    raw_profile_paths = os.path.join(
        data_raw_path, 'OtherProfiles', 'COP'
    )

    profile_df = combine_profiles(raw_profile_paths, 'cop-profile')

    profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'efficiency_profile.csv')
    )


def create_electricity_bev_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating electricity bev profiles")

    raw_profile_paths = os.path.join(
        data_raw_path, 'OtherProfiles', 'Transport'
    )

    profiles = {
        'drive_power': 'DrivePower',
        'availability': 'GridArrivalabilityRate',
        'max_storage_level': 'MaxBatteryLevel',
        'min_storage_level': 'MinBatteryLevel'
    }

    for k, v in profiles.items():
        path = os.path.join(raw_profile_paths, v)

        profile_df = combine_profiles(path, k + '-profile')

        if k == 'drive_power':

            yearly_amount = profile_df.sum(axis=0)

            profile_df = profile_df.divide(yearly_amount)

        profile_df.to_csv(
            os.path.join(data_preprocessed_path, 'sequences', k + '_profile.csv')
        )


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
