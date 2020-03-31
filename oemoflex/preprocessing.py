import os

import pandas as pd


bus_list = [
    'AT-el-bus',
    'BE-el-bus',
    'CH-el-bus',
    'CZ-el-bus',
    'DE-el-bus',
    'DK-el-bus',
    'FR-el-bus',
    'IT-el-bus',
    'LU-el-bus',
    'NL-el-bus',
    'PL-el-bus',
]

country_list = [
    'AT',
    'BE',
    'CH',
    'CZ',
    'DE',
    'DK',
    'FR',
    'IT',
    'LU',
    'NL',
    'PL',
]

link_list = [
    'AT-CH',
    'AT-CZ',
    'AT-IT',
    'BE-FR',
    'BE-LU',
    'BE-NL',
    'CH-FR',
    'CH-IT',
    'CZ-PL',
    'DE-AT',
    'DE-BE',
    'DE-CH',
    'DE-CZ',
    'DE-DK',
    'DE-FR',
    'DE-LU',
    'DE-NL',
    'DE-PL',
    'DK-NL',
    'FR-IT',
    'FR-LU',

]

datetimeindex = pd.date_range(start='2019-01-01', freq='H', periods=8760)

module_path = os.path.dirname(os.path.abspath(__file__))


def get_name(component, component_data):
    if component == 'link':
        name = link_list

        return name

    name = [country + '-' + component_data['name'] for country in country_list]

    return name


def specify_bus_connection(compo_data):
    comp_data = compo_data.copy()

    if 'bus' in comp_data:
        comp_data['bus'] = [country + '-' + comp_data['bus'] for country in country_list]

        return comp_data

    if all(attr in comp_data for attr in ['from_bus', 'to_bus']):

        comp_data['from_bus'] = [
            link.split('-')[0] + '-' + comp_data['from_bus'] for link in link_list
        ]

        comp_data['to_bus'] = [link.split('-')[1] + '-' + comp_data['to_bus'] for link in link_list]

        return comp_data

    return comp_data


def create_default_elements_files(
        dir,
        components_file='components.csv',
        component_attrs_dir='component_attrs'
):
    r"""

    Parameters
    ----------
    dir
    components_file
    component_attrs_dir

    Returns
    -------
    None
    """
    components_file = os.path.join(module_path, components_file)

    component_attrs_dir = os.path.join(module_path, component_attrs_dir)

    components = pd.read_csv(components_file)

    for component in components.name.values:
        component_attrs_file = os.path.join(component_attrs_dir, component + '.csv')

        try:
            component_attrs = pd.read_csv(component_attrs_file)

        except FileNotFoundError:
            print(f"There is no file with the name {component}")

        component_data = {
            c_attr['attribute']: c_attr['default'] for _, c_attr in component_attrs.iterrows()
        }

        component_data['name'] = get_name(component, component_data)

        component_data = specify_bus_connection(component_data)

        df = pd.DataFrame(component_data).set_index('name')

        df.to_csv(os.path.join(dir, component + '.csv'))


def get_parameter_values(scalars_df, parameter_name):
    r"""
    Selects rows from common input file "Scalars.csv" by column=='parameter_name'

    Parameters
    ----------
    scalars_df : DataFrame
    DataFrame of "Scalars.csv"

    parameter_name : str
    Specifies the rows to select by the name in column "Parameter"

    Returns
    -------
    The parameter's values (column 'Value') as numpy.ndarray
    """
    # Select corresponding rows from the common input file "Scalars.csv"
    # TODO Assure that both data sets perfectly fit, i.e. element 'AT-el-load'
    #  gets the value of AT in 'Scalars.csv' (only assumed at the moment!)
    parameter_df = scalars_df.loc[scalars_df['Parameter'] == parameter_name]

    return parameter_df['Value'].values


def update_shortage_file(data_preprocessed_path):
    logging.info("Updating shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file)

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = 5000

    # Write back to the CSV file
    shortage.to_csv(shortage_file, index=False)


def update_load_file(data_preprocessed_path, scalars):
    logging.info("Updating load file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'load.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file)

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values(scalars, 'Energy_FinalEnergy_Electricity') * 1e6  # TWh to MWh

    # Put in a reference to the corresponding time series
    load['profile'] = ['{}-el-load-profile'.format(bus.split('-')[0]) for bus in bus_list]

    # Write back to the CSV file
    load.to_csv(load_file, index=False)


def update_link_file(data_preprocessed_path, scalars):
    logging.info("Updating link file")

    link_file = os.path.join(data_preprocessed_path, 'elements', 'link.csv')

    link = pd.read_csv(link_file)

    transmission_loss_per_100km = get_parameter_values(scalars, 'Transmission_Losses_Electricity_Grid')

    transmission_length = get_parameter_values(scalars, 'Transmission_Length_Electricity_Grid')

    transmission_capacity = get_parameter_values(scalars, 'Transmission_Capacity_Electricity_Grid')

    link['capacity'] = transmission_capacity

    link['loss'] = (
        transmission_length
        * 0.01
        * transmission_loss_per_100km
        / transmission_capacity
    )

    link.to_csv(link_file, index=False)


def update_wind_onshore(data_preprocessed_path, scalars):
    wind_onshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv')

    wind_onshore = pd.read_csv(wind_onshore_file)

    scalars_wind_onshore = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Wind_Onshore')

    wind_onshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-onshore']) for bus in bus_list]

    wind_onshore['capacity'] = scalars_wind_onshore

    wind_onshore['bus'] = bus_list

    wind_onshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-onshore-profile']) for bus in bus_list
    ]

    wind_onshore.to_csv(wind_onshore_file, index=False)


def update_wind_offshore(data_preprocessed_path, scalars):
    wind_offshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')

    wind_offshore = pd.read_csv(wind_offshore_file)

    scalars_wind_offshore = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Wind_Offshore')

    wind_offshore['name'] = ['-'.join(bus.split('-')[:2] + ['wind-offshore']) for bus in bus_list]

    wind_offshore['capacity'] = scalars_wind_offshore

    wind_offshore['bus'] = bus_list

    wind_offshore['profile'] = [
        '-'.join(bus.split('-')[:2] + ['wind-offshore-profile']) for bus in bus_list
    ]

    wind_offshore.to_csv(wind_offshore_file, index=False)


def update_solar_pv(data_preprocessed_path, scalars):
    solar_pv_file = os.path.join(data_preprocessed_path, 'elements', 'pv.csv')

    solarpv = pd.read_csv(solar_pv_file)

    scalars_solarpv = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Solar_PV')

    solarpv['name'] = ['-'.join(bus.split('-')[:2] + ['solarpv']) for bus in bus_list]

    solarpv['capacity'] = scalars_solarpv

    solarpv['bus'] = bus_list

    solarpv['profile'] = ['-'.join(bus.split('-')[:2] + ['solar-pv-profile']) for bus in bus_list]

    solarpv.to_csv(solar_pv_file, index=False)