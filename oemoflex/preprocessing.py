import logging
import os

import pandas as pd

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


def create_default_elements(
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
            component_data['name'] = link_list

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
                if attr_name in ['from_bus', 'to_bus']:
                    component_data[attr_name] = [link + suffix
                                                 for link in component_data[attr_name]]

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
```suggestion
    parameter_values : float / pd.Series
        The parameter's values (column 'Value') as a single value (float) 
        or as a 'Region'-indexed Series     
    """

    is_parameter_name = scalars_df['Parameter'] == parameter_name
    is_scenario_name = scalars_df['Scenario'].isin(['FlexMex1', 'ALL'])

    query_result = scalars_df.loc[is_parameter_name & is_scenario_name, :]

    # The query result DataFrame can either be multi-row or single-row
    if len(query_result['Region']) == 1 and query_result['Region'].item() == 'ALL':

        # Result is single-row. The parameter takes one value, that is, one line for all 'Regions'.
        # No merging required. Index doesn't make sense. Return plain value (short for .values[0])
        parameter_value = query_result['Value'].item()
        return parameter_value

    # Result is multi-row. Each 'Region' has its own value.
    # Return the 'Value' column as an 'Region'-indexed Series to merge correctly.
    parameter_value = query_result.set_index('Region')['Value']
    return parameter_value


def update_shortage(data_preprocessed_path, scalars):
    logging.info("Updating shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file, index_col='region')

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = get_parameter_values(
        scalars,
        'Energy_SlackCost_Electricity') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to the CSV file
    shortage.to_csv(shortage_file)


def update_load(data_preprocessed_path, scalars):
    logging.info("Updating load file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'load.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file, index_col='region')

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values(
        scalars,
        'Energy_FinalEnergy_Electricity') * 1e3  # GWh to MWh

    # Write back to the CSV file
    load.to_csv(load_file)


def update_link(data_preprocessed_path, scalars):
    logging.info("Updating link file")

    link_file = os.path.join(data_preprocessed_path, 'elements', 'link.csv')

    link = pd.read_csv(link_file, index_col='region')

    # Scalars.csv has only one line of 'Transmission_Losses_Electricity_Grid' for all Regions.
    # 'Region' value of that line is 'ALL'. So mapping by index doesn't work anymore.
    # Use its plain value instead.
    transmission_loss_per_100km = get_parameter_values(
        scalars,
        'Transmission_Losses_Electricity_Grid')

    transmission_length = get_parameter_values(
        scalars,
        'Transmission_Length_Electricity_Grid')

    transmission_capacity = get_parameter_values(
        scalars,
        'Transmission_Capacity_Electricity_Grid')

    link['capacity'] = transmission_capacity

    # Calculation with pandas series
    link['loss'] = (
        transmission_length
        * 0.01
        * transmission_loss_per_100km
        / transmission_capacity
    )

    link.to_csv(link_file)


def update_wind_onshore(data_preprocessed_path, scalars):
    wind_onshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-onshore.csv')

    wind_onshore = pd.read_csv(wind_onshore_file, index_col='region')

    wind_onshore['capacity'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Wind_Onshore')

    wind_onshore.to_csv(wind_onshore_file)


def update_wind_offshore(data_preprocessed_path, scalars):
    wind_offshore_file = os.path.join(data_preprocessed_path, 'elements', 'wind-offshore.csv')

    wind_offshore = pd.read_csv(wind_offshore_file, index_col='region')

    wind_offshore['capacity'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Wind_Offshore')

    wind_offshore.to_csv(wind_offshore_file)


def update_solar_pv(data_preprocessed_path, scalars):
    solar_pv_file = os.path.join(data_preprocessed_path, 'elements', 'pv.csv')

    solarpv = pd.read_csv(solar_pv_file, index_col='region')

    solarpv['capacity'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Solar_PV')

    solarpv.to_csv(solar_pv_file)


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
