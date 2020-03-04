import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.model_structure import (
    bus_list, datetimeindex, create_default_elements_files)
from oemoflex.helpers import get_experiment_paths, check_if_csv_dirs_equal


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

scalars = pd.read_csv(os.path.join(experiment_paths['data_raw'], 'Scalars.csv'), header=0)

create_default_elements_files(os.path.join(data_preprocessed_path, 'elements'))


def update_shortage_file():
    logging.info("Updating shortage file")

    shortage = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'shortage.csv'))

    shortage['marginal_cost'] = 5000

    shortage.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'shortage.csv'), index=False,
    )


def update_load_file():
    logging.info("Updating load file")

    load = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'load.csv'))

    scalars_load = scalars.loc[scalars['Parameter'] == 'Energy_FinalEnergy_Electricity']

    load['amount'] = scalars_load['Value'].values * 1e6  # TWh to MWh

    load['profile'] = ['{}-el-load-profile'.format(bus.split('-')[0]) for bus in bus_list]

    load.to_csv(os.path.join(data_preprocessed_path, 'elements', 'load.csv'), index=False)


def update_link_file():
    logging.info("Updating link file")

    link = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'link.csv'))

    transmission_loss_per_100km = scalars.loc[
        scalars['Parameter'] == 'Transmission_Losses_Electricity_Grid'
    ]

    transmission_length = scalars.loc[
        scalars['Parameter'] == 'Transmission_Length_Electricity_Grid'
    ]

    transmission_capacity = scalars.loc[
        scalars['Parameter'] == 'Transmission_Capacity_Electricity_Grid'
    ]

    link['capacity'] = transmission_capacity['Value'].values

    link['loss'] = (
        transmission_length['Value'].values
        * 0.01
        * transmission_loss_per_100km['Value'].values
        / transmission_capacity['Value'].values
    )

    link.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'link.csv'), index=False,
    )


def update_wind_onshore():
    wind_onshore = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv'))

    scalars_wind_onshore = scalars.loc[
        scalars['Parameter'] == 'EnergyConversion_Capacity_Electricity_Wind_Onshore'
    ]

    wind_onshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-onshore']) for bus in bus_list]

    wind_onshore['carrier'] = 'wind'

    wind_onshore['tech'] = 'onshore'

    wind_onshore['capacity'] = scalars_wind_onshore['Value'].values

    wind_onshore['bus'] = bus_list

    wind_onshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-onshore-profile']) for bus in bus_list
    ]

    wind_onshore.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv'), index=False,
    )


def update_wind_offshore():
    wind_offshore = pd.read_csv(
        os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')
    )

    scalars_wind_offshore = scalars.loc[
        scalars['Parameter'] == 'EnergyConversion_Capacity_Electricity_Wind_Offshore'
    ]

    wind_offshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-offshore']) for bus in bus_list]

    wind_offshore['carrier'] = 'wind'

    wind_offshore['tech'] = 'offshore'

    wind_offshore['capacity'] = scalars_wind_offshore['Value'].values

    wind_offshore['bus'] = bus_list

    wind_offshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-offshore-profile']) for bus in bus_list
    ]

    wind_offshore.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv'), index=False,
    )


def update_solar_pv():
    solarpv = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'pv.csv'))

    scalars_solarpv = scalars.loc[
        scalars['Parameter'] == 'EnergyConversion_Capacity_Electricity_Solar_PV'
    ]

    solarpv['name'] = ['-'.join(bus.split('-')[:2] + ['solarpv']) for bus in bus_list]

    solarpv['carrier'] = 'solar'

    solarpv['tech'] = 'pv'

    solarpv['capacity'] = scalars_solarpv['Value'].values

    solarpv['bus'] = bus_list

    solarpv['profile'] = ['-'.join(bus.split('-')[:2] + ['solar-pv-profile']) for bus in bus_list]

    solarpv.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'pv.csv'), index=False,
    )


def combine_volatile_file():
    wind_onshore = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv'))

    wind_offshore = pd.read_csv(
        os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')
    )

    solarpv = pd.read_csv(os.path.join(data_preprocessed_path, 'elements', 'pv.csv'))

    volatile = pd.concat([wind_onshore, wind_offshore, solarpv], axis=0)

    volatile['type'] = 'volatile'

    volatile['marginal_cost'] = 0

    volatile['output_parameters'] = '{}'

    volatile.to_csv(
        os.path.join(data_preprocessed_path, 'elements', 'volatile.csv'), index=False,
    )


def combine_profiles(raw_profile_path, column_name):
    profile_file_list = sorted(os.listdir(raw_profile_path))

    profile_list = []
    for file in profile_file_list:
        region = file.split('_')[1]

        logging.info("Preprocessing the load profile for region {}".format(region))
        # TODO: This is not only used for load profiles

        raw_load_profile = pd.read_csv(os.path.join(raw_profile_path, file), index_col=0)

        load_profile = raw_load_profile.iloc[:, 0]

        load_profile.name = region + '-' + column_name

        profile_list.append(load_profile)

    profile_df = pd.concat(profile_list, axis=1, sort=True)

    profile_df = profile_df.set_index(datetimeindex, drop=True)

    profile_df.index.name = 'timeindex'

    return profile_df


def create_load_profiles():
    raw_load_profile_path = os.path.join(data_raw_path, 'Energy', 'FinalEnergy', 'Electricity')

    load_profile_df = combine_profiles(raw_load_profile_path, 'el-load-profile')

    load_profile_df.to_csv(os.path.join(data_preprocessed_path, 'sequences', 'load_profile.csv'))


def create_volatile_profiles():
    logging.info("Creating volatile file")
    raw_wind_onshore_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Wind', 'Onshore'
    )

    wind_onshore_profile_df = combine_profiles(
        raw_wind_onshore_profile_paths, 'el-wind-onshore-profile'
    )

    raw_wind_offshore_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Wind', 'Offshore'
    )

    wind_offshore_profile_df = combine_profiles(
        raw_wind_offshore_profile_paths, 'el-wind-offshore-profile'
    )

    raw_solar_pv_profile_paths = os.path.join(
        data_raw_path, 'Energy', 'SecondaryEnergy', 'Solar', 'PV'
    )

    solar_pv_profile_df = combine_profiles(raw_solar_pv_profile_paths, 'el-solar-pv-profile')

    wind_onshore_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'wind-onshore_profile.csv')
    )
    wind_offshore_profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'wind-offshore_profile.csv')
    )
    solar_pv_profile_df.to_csv(os.path.join(data_preprocessed_path, 'sequences', 'pv_profile.csv'))


def main():
    update_shortage_file()
    update_load_file()
    update_wind_onshore()
    update_wind_offshore()
    update_solar_pv()
    update_link_file()

    create_load_profiles()
    create_volatile_profiles()

    previous_path = experiment_paths['data_preprocessed'] + '_default'
    new_path = experiment_paths['data_preprocessed']

    check_if_csv_dirs_equal(new_path, previous_path, ignore=['log', 'json'])


if __name__ == '__main__':
    main()
