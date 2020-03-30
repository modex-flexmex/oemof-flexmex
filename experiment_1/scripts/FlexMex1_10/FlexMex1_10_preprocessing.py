import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.model_structure import (
    bus_list, datetimeindex, create_default_elements_files)
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

scalars = pd.read_csv(os.path.join(experiment_paths['data_raw'], 'Scalars.csv'), header=0)

# Prepare oemof.tabular input CSV files
create_default_elements_files(os.path.join(data_preprocessed_path, 'elements'))


def get_parameter_values(parameter_name):
    r"""
    Selects rows from common input file "Scalars.csv" by column=='parameter_name'

    Parameters
    ----------
    parameter_name : str
    Specifies the rows to select by the name in column "Parameter"

    Returns
    -------
    The parameter's values (column 'Value') as numpy.ndarray
    """
    # Select corresponding rows from the common input file "Scalars.csv"
    # TODO Assure that both data sets perfectly fit, i.e. element 'AT-el-load'
    #  gets the value of AT in 'Scalars.csv' (only assumed at the moment!)
    parameter_dataframe = scalars.loc[scalars['Parameter'] == parameter_name]

    return parameter_dataframe['Value'].values


def update_shortage_file(data_preprocessed_path):
    logging.info("Updating shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file)

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = 5000

    # Write back to the CSV file
    shortage.to_csv(shortage_file, index=False)


def update_load_file(data_preprocessed_path):
    logging.info("Updating load file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'load.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file)

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values('Energy_FinalEnergy_Electricity') * 1e6  # TWh to MWh

    # Put in a reference to the corresponding time series
    load['profile'] = ['{}-el-load-profile'.format(bus.split('-')[0]) for bus in bus_list]

    # Write back to the CSV file
    load.to_csv(load_file, index=False)


def update_link_file(data_preprocessed_path):
    logging.info("Updating link file")

    link_file = os.path.join(data_preprocessed_path, 'elements', 'link.csv')

    link = pd.read_csv(link_file)

    transmission_loss_per_100km = get_parameter_values('Transmission_Losses_Electricity_Grid')

    transmission_length = get_parameter_values('Transmission_Length_Electricity_Grid')

    transmission_capacity = get_parameter_values('Transmission_Capacity_Electricity_Grid')

    link['capacity'] = transmission_capacity

    link['loss'] = (
        transmission_length
        * 0.01
        * transmission_loss_per_100km
        / transmission_capacity
    )

    link.to_csv(link_file, index=False)


def update_wind_onshore(data_preprocessed_path):
    wind_onshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv')

    wind_onshore = pd.read_csv(wind_onshore_file)

    scalars_wind_onshore = get_parameter_values('EnergyConversion_Capacity_Electricity_Wind_Onshore')

    wind_onshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-onshore']) for bus in bus_list]

    wind_onshore['carrier'] = 'wind'

    wind_onshore['tech'] = 'onshore'

    wind_onshore['capacity'] = scalars_wind_onshore

    wind_onshore['bus'] = bus_list

    wind_onshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-onshore-profile']) for bus in bus_list
    ]

    wind_onshore.to_csv(wind_onshore_file, index=False)


def update_wind_offshore(data_preprocessed_path):
    wind_offshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')

    wind_offshore = pd.read_csv(wind_offshore_file)

    scalars_wind_offshore = get_parameter_values('EnergyConversion_Capacity_Electricity_Wind_Offshore')

    wind_offshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-offshore']) for bus in bus_list]

    wind_offshore['carrier'] = 'wind'

    wind_offshore['tech'] = 'offshore'

    wind_offshore['capacity'] = scalars_wind_offshore

    wind_offshore['bus'] = bus_list

    wind_offshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-offshore-profile']) for bus in bus_list
    ]

    wind_offshore.to_csv(wind_offshore_file, index=False)


def update_solar_pv(data_preprocessed_path):
    solar_pv_file = os.path.join(data_preprocessed_path, 'elements', 'pv.csv')

    solarpv = pd.read_csv(solar_pv_file)

    scalars_solarpv = get_parameter_values('EnergyConversion_Capacity_Electricity_Solar_PV')

    solarpv['name'] = ['-'.join(bus.split('-')[:2] + ['solarpv']) for bus in bus_list]

    solarpv['carrier'] = 'solar'

    solarpv['tech'] = 'pv'

    solarpv['capacity'] = scalars_solarpv

    solarpv['bus'] = bus_list

    solarpv['profile'] = ['-'.join(bus.split('-')[:2] + ['solar-pv-profile']) for bus in bus_list]

    solarpv.to_csv(solar_pv_file, index=False)

# not used
def combine_volatile_file(data_preprocessed_path):
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
    # update elements
    update_shortage_file(data_preprocessed_path)
    update_load_file(data_preprocessed_path)
    update_wind_onshore(data_preprocessed_path)
    update_wind_offshore(data_preprocessed_path)
    update_solar_pv(data_preprocessed_path)
    update_link_file(data_preprocessed_path)

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
