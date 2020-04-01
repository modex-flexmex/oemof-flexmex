import logging
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

def create_default_elements_files(
        dir,
        components_file='components.csv',
        component_attrs_dir='component_attrs'
):
    r"""
    Prepares oemoef.tabluar input CSV files:
    * includes headers according to definitions in CSVs in directory 'component_attrs_dir'
    * pre-define all oemof elements (along CSV rows) without actual dimensions/values

    Parameters
    ----------
    dir : str (dir path)
        target directory where to put the prepared CSVs
    components_file : str (file path)
        CSV where to read the components from
    component_attrs_dir : str (dir path)
        CSV where to read the components' attributes from

    Returns
    -------
    None
    """
    components_file = os.path.join(module_path, components_file)

    # TODO Better put this as another field into the components.csv as well?
    component_attrs_dir = os.path.join(module_path, component_attrs_dir)

    components = pd.read_csv(components_file)

    for component in components.name.values:
        component_attrs_file = os.path.join(component_attrs_dir, component + '.csv')

        try:
            component_attrs = pd.read_csv(component_attrs_file)

        except FileNotFoundError:
            print(f"There is no file with the name {component}")

        # Set up the skeleton of the output dataframe consisting of attribute names as
        # column titles and default values
        component_data = {
            c_attr['attribute']: c_attr['default'] for _, c_attr in component_attrs.iterrows()
        }

        component_suffix = {
            c_attr['attribute']: c_attr['suffix'] for _, c_attr in component_attrs.iterrows()
        }

        # Fill 'region' with country code list
        if component == 'link':
            # Generate region column of the form "AT_DE"
            component_data['region'] = [code.replace('-', '_') for code in link_list]

            # Reserve 'name' column because there is no suffix to use here
            # line could be dropped by defining a suffix such as '-link'
            component_data['name'] = [code for code in link_list]

            # for the two bus attributes reserve the colums with a part of the country code
            component_data['from_bus'] = [code.split('-')[0] for code in link_list]
            component_data['to_bus'] = [code.split('-')[1] for code in link_list]

        else:
            component_data['region'] = country_list

        # Fill other columns with their respective suffixes if available
        for attr_name, suffix in component_suffix.items():

            # If a suffix has to be applied
            if not pd.isna(suffix):

                # for 'link' element use the pre-defined name part instead of the region
                if attr_name == 'from_bus' or attr_name == 'to_bus':
                    component_data[attr_name] = [link + suffix for link in component_data[attr_name]]

                else:
                    component_data[attr_name] = [code + suffix for code in component_data['region']]

        df = pd.DataFrame(component_data).set_index('region')

        # Write to target directory
        df.to_csv(os.path.join(dir, component + '.csv'))


def get_parameter_values(scalars_df, parameter_name):
    r"""
    Selects rows from common input file "Scalars.csv" by column=='parameter_name'
    and maintains the relation 'Region' -> 'Value' at external assignment

    Parameters
    ----------
    scalars_df : DataFrame
    DataFrame of "Scalars.csv"

    parameter_name : str
    Specifies the rows to select by the name in column "Parameter"

    Returns
    -------
    The parameter's values (column 'Value') as a DataFrame, indexed by 'Region'
    """

    return scalars_df.loc[scalars_df['Parameter'] == parameter_name].set_index('Region')['Value']


def update_shortage_file(data_preprocessed_path):
    logging.info("Updating shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file, index_col='region')

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = 5000

    # Write back to the CSV file
    shortage.to_csv(shortage_file, index=False)


def update_load_file(data_preprocessed_path, scalars):
    logging.info("Updating load file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'load.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file, index_col='region')

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values(scalars, 'Energy_FinalEnergy_Electricity') * 1e6  # TWh to MWh

    # Write back to the CSV file
    load.to_csv(load_file, index=False)


def update_link_file(data_preprocessed_path, scalars):
    logging.info("Updating link file")

    link_file = os.path.join(data_preprocessed_path, 'elements', 'link.csv')

    link = pd.read_csv(link_file, index_col='region')

    # Scalars.csv has only one line of 'Transmission_Losses_Electricity_Grid' for all Regions.
    # 'Region' value of that line is 'ALL'. So mapping by index doesn't work anymore.
    # Use its plain value instead.
    transmission_loss_per_100km = get_parameter_values(scalars, 'Transmission_Losses_Electricity_Grid').values

    transmission_length = get_parameter_values(scalars, 'Transmission_Length_Electricity_Grid')

    transmission_capacity = get_parameter_values(scalars, 'Transmission_Capacity_Electricity_Grid')

    link['capacity'] = transmission_capacity

    # Calculation with pandas series
    link['loss'] = (
        transmission_length
        * 0.01
        * transmission_loss_per_100km
        / transmission_capacity
    )

    link.to_csv(link_file, index=False)


def update_wind_onshore(data_preprocessed_path, scalars):
    wind_onshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv')

    wind_onshore = pd.read_csv(wind_onshore_file, index_col='region')

    scalars_wind_onshore = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Wind_Onshore')

    wind_onshore['capacity'] = scalars_wind_onshore

    wind_onshore.to_csv(wind_onshore_file, index=False)


def update_wind_offshore(data_preprocessed_path, scalars):
    wind_offshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')

    wind_offshore = pd.read_csv(wind_offshore_file, index_col='region')

    scalars_wind_offshore = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Wind_Offshore')

    wind_offshore['capacity'] = scalars_wind_offshore

    wind_offshore.to_csv(wind_offshore_file, index=False)


def update_solar_pv(data_preprocessed_path, scalars):
    solar_pv_file = os.path.join(data_preprocessed_path, 'elements', 'pv.csv')

    solarpv = pd.read_csv(solar_pv_file, index_col='region')

    scalars_solarpv = get_parameter_values(scalars, 'EnergyConversion_Capacity_Electricity_Solar_PV')

    solarpv['capacity'] = scalars_solarpv

    solarpv.to_csv(solar_pv_file, index=False)