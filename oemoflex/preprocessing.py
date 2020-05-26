import logging
import os

import pandas as pd

from oemof.tools.economics import annuity
from json import dumps
from csv import QUOTE_NONE

module_path = os.path.dirname(os.path.abspath(__file__))

datetimeindex = pd.date_range(start='2019-01-01', freq='H', periods=8760)

regions_list = list(
    pd.read_csv(os.path.join(module_path, 'model_structure', 'regions.csv'), squeeze=True)
)

link_list = list(
    pd.read_csv(os.path.join(module_path, 'model_structure', 'links.csv'), squeeze=True)
)


def create_default_elements(
        dir,
        busses_file=os.path.join(module_path, 'model_structure', 'busses.csv'),
        components_file=os.path.join(module_path, 'model_structure', 'components.csv'),
        component_attrs_dir=os.path.join(module_path, 'model_structure', 'component_attrs'),
        select_components=None,
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

    select_components : list
        List of default elements to create

    Returns
    -------
    None
    """
    components_file = os.path.join(module_path, components_file)

    # TODO Better put this as another field into the components.csv as well?
    component_attrs_dir = os.path.join(module_path, component_attrs_dir)

    components = pd.read_csv(components_file).name.values

    if select_components is not None:
        undefined_components = set(select_components).difference(set(components))

        assert not undefined_components,\
            f"Selected components {undefined_components} are not in components."

        components = [c for c in components if c in select_components]

    bus_df = create_bus_element(busses_file)

    bus_df.to_csv(os.path.join(dir, 'bus.csv'))

    for component in components:
        component_attrs_file = os.path.join(component_attrs_dir, component + '.csv')

        df = create_component_element(component_attrs_file)

        # Write to target directory
        df.to_csv(os.path.join(dir, component + '.csv'))


def create_bus_element(busses_file):
    r"""

    Parameters
    ----------
    busses_file : path
        Path to busses file.

    Returns
    -------
    bus_df : pd.DataFrame
        Bus element DataFrame
    """
    busses = pd.read_csv(busses_file, index_col='carrier')

    regions = []
    carriers = []
    balanced = []

    for region in regions_list:
        for carrier, row in busses.iterrows():
            regions.append(region)
            carriers.append(region + '-' + carrier)
            balanced.append(row['balanced'])

    bus_df = pd.DataFrame({
        'region': regions,
        'name': carriers,
        'type': 'bus',
        'balanced': balanced
    })

    bus_df = bus_df.set_index('region')

    return bus_df


def create_component_element(component_attrs_file):
    r"""
    Loads file for component attribute specs and returns a pd.DataFrame with the right regions,
    links, names, references to profiles and default values.

    Parameters
    ----------
    component_attrs_file : path
        Path to file with component attribute specifications.

    Returns
    -------
    component_df : pd.DataFrame
        DataFrame for the given component with default values filled.

    """
    try:
        component_attrs = pd.read_csv(component_attrs_file, index_col=0)

    except FileNotFoundError:
        raise FileNotFoundError(f"There is no file {component_attrs_file}")

    # Collect default values and suffices for the component
    defaults = component_attrs.loc[component_attrs['default'].notna(), 'default'].to_dict()

    suffices = component_attrs.loc[component_attrs['suffix'].notna(), 'suffix'].to_dict()

    comp_data = {key: None for key in component_attrs.index}

    # Create dict for component data
    if defaults['type'] == 'link':
        comp_data['region'] = [link.replace('-', '_') for link in link_list]
        comp_data['name'] = link_list
        comp_data['from_bus'] = [link.split('-')[0] + suffices['from_bus'] for link in link_list]
        comp_data['to_bus'] = [link.split('-')[1] + suffices['to_bus'] for link in link_list]

    elif defaults['type'] == 'conversion':
        comp_data['region'] = regions_list
        comp_data['name'] = [region + suffices['name'] for region in regions_list]
        comp_data['from_bus'] = [region + suffices['from_bus'] for region in regions_list]
        comp_data['to_bus'] = [region + suffices['to_bus'] for region in regions_list]

        if 'efficiency' in suffices:
            comp_data['efficiency'] = [region + suffices['efficiency'] for region in regions_list]

    elif defaults['type'] in ['backpressure', 'extraction']:
        comp_data['region'] = regions_list
        comp_data['name'] = [region + suffices['name'] for region in regions_list]
        comp_data['fuel_bus'] = [region + suffices['fuel_bus'] for region in regions_list]
        comp_data['heat_bus'] = [region + suffices['heat_bus'] for region in regions_list]
        comp_data['electricity_bus'] = [
            region + suffices['electricity_bus'] for region in regions_list
        ]

    else:
        comp_data['region'] = regions_list
        comp_data['name'] = [region + suffices['name'] for region in regions_list]
        comp_data['bus'] = [region + suffices['bus'] for region in regions_list]

        if 'profile' in suffices:
            comp_data['profile'] = [region + suffices['profile'] for region in regions_list]

    for key, value in defaults.items():
        comp_data[key] = value

    component_df = pd.DataFrame(comp_data).set_index('region')

    return component_df


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
    parameter_values : float / pd.Series
        The parameter's values (column 'Value') as a single value (float)
        or as a 'Region'-indexed Series
    """

    is_parameter_name = scalars_df['Parameter'] == parameter_name

    query_result = scalars_df.loc[is_parameter_name, :]

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


def update_electricity_shortage(data_preprocessed_path, scalars):
    logging.info("Updating electricity shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'electricity-shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file, index_col='region')

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = get_parameter_values(
        scalars,
        'Energy_SlackCost_Electricity') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to the CSV file
    shortage.to_csv(shortage_file)


def update_heat_shortage(data_preprocessed_path, scalars):
    logging.info("Updating heat shortage file")

    shortage_file = os.path.join(data_preprocessed_path, 'elements', 'heat-shortage.csv')

    # Read prepared CSV file
    shortage = pd.read_csv(shortage_file, index_col='region')

    # Fill column 'marginal_cost' with a fixed value for ALL the elements
    shortage['marginal_cost'] = get_parameter_values(
        scalars,
        'Energy_SlackCost_Heat') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to the CSV file
    shortage.to_csv(shortage_file)


def update_electricity_demand(data_preprocessed_path, scalars):
    logging.info("Updating electricity-demand file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'electricity-demand.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file, index_col='region')

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values(
        scalars,
        'Energy_FinalEnergy_Electricity') * 1e3  # GWh to MWh

    # Write back to the CSV file
    load.to_csv(load_file)


def update_heat_demand(data_preprocessed_path, scalars):
    logging.info("Updating heat-demand file")

    load_file = os.path.join(data_preprocessed_path, 'elements', 'heat-demand.csv')

    # Read prepared CSV file
    load = pd.read_csv(load_file, index_col='region')

    # Fill column for ALL the elements
    load['amount'] = get_parameter_values(
        scalars,
        'Energy_FinalEnergy_Heat') * 1e3  # GWh to MWh

    # Write back to the CSV file
    load.to_csv(load_file)


def update_bpchp(data_preprocessed_path, scalars):
    logging.info("Updating ch4-bpchp file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-bpchp.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_ElectricityHeat_CH4_BpCCGT')

    electricity_per_heat = get_parameter_values(
        scalars, 'EnergyConversion_Power2HeatRatio_ElectricityHeat_CH4_BpCCGT')

    # eta_el = eta_total / (1 + 1 / electricity_per_heat)
    df['electric_efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_BpCCGT'
    ) / (1 + 1/electricity_per_heat)

    # eta_th = eta_total / (1 + electricity_per_heat)
    df['thermal_efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_BpCCGT'
    ) / (1 + electricity_per_heat)

    df['carrier_cost'] = (
        get_parameter_values(scalars, 'Energy_Price_CH4')
        + get_parameter_values(scalars, 'Energy_Price_CO2')
        * get_parameter_values(scalars, 'Energy_EmissionFactor_CH4')) * 1e-3  # Eur/GWh to Eur/MWh

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_ElectricityHeat_CH4_BpCCGT') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_extchp(data_preprocessed_path, scalars):
    logging.info("Updating ch4-extchp file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-extchp.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_ElectricityHeat_CH4_ExCCGT')

    electricity_per_heat = get_parameter_values(
        scalars, 'EnergyConversion_Power2HeatRatio_ElectricityHeat_CH4_ExCCGT')

    # eta_el = eta_total / (1 + 1 / electricity_per_heat)
    electric_efficiency = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_ExCCGT'
    ) / (1 + 1/electricity_per_heat)

    df['electric_efficiency'] = electric_efficiency

    # eta_th = eta_total / (1 + electricity_per_heat)
    thermal_efficiency = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_ExCCGT'
    ) / (1 + electricity_per_heat)

    df['thermal_efficiency'] = thermal_efficiency

    # eta_condensing = beta * eta_th + eta_el
    df['condensing_efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_PowerLossIndex_ElectricityHeat_CH4_ExCCGT')\
        * thermal_efficiency\
        + electric_efficiency

    df['carrier_cost'] = (
        get_parameter_values(scalars, 'Energy_Price_CH4')
        + get_parameter_values(scalars, 'Energy_Price_CO2')
        * get_parameter_values(scalars, 'Energy_EmissionFactor_CH4')) * 1e-3  # Eur/GWh to Eur/MWh

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_ElectricityHeat_CH4_ExCCGT') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_boiler(data_preprocessed_path, scalars):
    logging.info("Updating ch4-boiler file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-boiler.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(scalars, 'EnergyConversion_Capacity_Heat_CH4_Large')

    df['efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_Eta_Heat_CH4_Large') * 0.01  # Percent to decimals

    df['carrier_cost'] = get_parameter_values(
        scalars, 'Energy_Price_CH4') * 1e3  # Eur/GWh to Eur/MWh

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_CH4_Large') * 1e3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_pth(data_preprocessed_path, scalars):
    logging.info("Updating electricity-pth file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-pth.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_Heat_Electricity_Large')

    df['efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_Eta_Heat_Electricity_Large') * 0.01  # Percent to decimals

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_Electricity_Large') * 1e3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_electricity_heatpump(data_preprocessed_path, scalars):
    logging.info("Updating electricity-heatpump file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-heatpump.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_Heat_ElectricityHeat_Small'
    )

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_ElectricityHeat_Small') * 1e3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_heat_storage(data_preprocessed_path, scalars):
    logging.info("Updating heat-storage file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'heat-storage.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['capacity'] = get_parameter_values(scalars, 'Storage_Capacity_Heat_SmallCharge')

    df['storage_capacity'] = get_parameter_values(
        scalars, 'Storage_Capacity_Heat_SmallStorage') * 1e3  # GWh to MWh

    df['losses'] = get_parameter_values(
        scalars, 'Storage_SelfDischarge_Heat_Small') * 0.01  # Percent to decimals

    df['efficiency'] = get_parameter_values(
        scalars, 'Storage_Eta_Heat_SmallCharge') * 0.01  # Percent to decimals

    df['marginal_cost'] = get_parameter_values(
        scalars, 'Storage_VarOM_Heat_Small') * 1e3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_link(data_preprocessed_path, scalars):
    logging.info("Updating link file")

    link_file = os.path.join(data_preprocessed_path, 'elements', 'electricity-transmission.csv')

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
    solar_pv_file = os.path.join(data_preprocessed_path, 'elements', 'solar-pv.csv')

    solarpv = pd.read_csv(solar_pv_file, index_col='region')

    solarpv['capacity'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Solar_PV')

    solarpv.to_csv(solar_pv_file)


def update_nuclear_st(data_preprocessed_path, scalars, expandable=False, from_green_field=False):

    file_path = os.path.join(data_preprocessed_path, 'elements', 'uranium-nuclear-st.csv')

    df = pd.read_csv(file_path, index_col='region')

    # Operation parameters
    capacity = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Nuclear_ST')

    availability = get_parameter_values(
        scalars,
        'EnergyConversion_Availability_Electricity_Nuclear_ST') * 1e-2  # percent -> 0...1

    operation_cost = get_parameter_values(
        scalars,
        'EnergyConversion_VarOM_Electricity_Nuclear_ST') * 1e-3  # Eur/GWh -> Eur/MWh

    eta = get_parameter_values(
        scalars,
        'EnergyConversion_EtaNet_Electricity_Nuclear_ST') * 1e-2  # percent -> 0...1

    carrier_price = get_parameter_values(
        scalars,
        'Energy_Price_Uranium') * 1e-3  # Eur/GWh -> Eur/MWh

    gradient = get_parameter_values(
        scalars,
        "EnergyConversion_MaxPowerChange_Electricity_Nuclear_ST") \
        * 12 * 1e-2  # percent Cap./5min -> 0..1 / 1 h

    gradient_formatted = {"negative_gradient": {"ub": gradient, "costs": 0},
                          "positive_gradient": {"ub": gradient, "costs": 0}}

    # Investment parameters
    capex = get_parameter_values(
        scalars,
        'EnergyConversion_Capex_Electricity_Nuclear_ST')

    fix_cost = get_parameter_values(
        scalars,
        'EnergyConversion_FixOM_Electricity_Nuclear_ST') * 1e-2  # percent -> 0...1

    lifetime = get_parameter_values(
        scalars,
        'EnergyConversion_LifeTime_Electricity_Nuclear_ST')

    interest = get_parameter_values(
        scalars,
        'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

    annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

    # Actual assignments
    df['expandable'] = expandable
    df['capacity'] = 0 if expandable and from_green_field else capacity * availability

    df['capacity_cost'] = annualized_cost + fix_cost * capex

    df['marginal_cost'] = operation_cost

    df['carrier_cost'] = carrier_price

    df['efficiency'] = eta

    # Use string representation of the dict
    df['input_parameters'] = dumps(gradient_formatted)

    # Write to CSV
    # With semicolon as field separator to be able to process "output_parameters" dict
    # Do not quote object str representations for better readability
    df.to_csv(file_path, sep=';', quoting=QUOTE_NONE)


def update_ch4_gt(data_preprocessed_path, scalars, expandable=False, from_green_field=False):
    logging.info("Updating ch4-gt file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-gt.csv')

    df = pd.read_csv(file_path, index_col='region')

    # Operation parameters
    capacity = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_CH4_GT')

    availability = get_parameter_values(
        scalars,
        'EnergyConversion_Availability_Electricity_CH4_GT') * 1e-2  # percent -> 0...1

    operation_cost = get_parameter_values(
        scalars,
        'EnergyConversion_VarOM_Electricity_CH4_GT') * 1e-3  # Eur/GWh -> Eur/MWh

    eta = get_parameter_values(
        scalars,
        'EnergyConversion_EtaNet_Electricity_CH4_GT') * 1e-2  # percent -> 0...1

    carrier_price = get_parameter_values(
        scalars,
        'Energy_Price_CH4') * 1e-3  # Eur/GWh -> Eur/MWh

    co2_price = get_parameter_values(scalars, 'Energy_Price_CO2')

    emission_factor = get_parameter_values(
        scalars,
        'Energy_EmissionFactor_CH4') * 1e-3  # t/GWh -> t/MWh

    # Investment parameters
    capex = get_parameter_values(
        scalars,
        'EnergyConversion_Capex_Electricity_CH4_GT')

    fix_cost = get_parameter_values(
        scalars,
        'EnergyConversion_FixOM_Electricity_CH4_GT') * 1e-2  # percent -> 0...1

    lifetime = get_parameter_values(
        scalars,
        'EnergyConversion_LifeTime_Electricity_CH4_GT')

    interest = get_parameter_values(
        scalars,
        'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

    annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

    # Actual assignments
    df['expandable'] = expandable
    df['capacity'] = 0 if expandable and from_green_field else capacity * availability

    df['capacity_cost'] = annualized_cost + fix_cost * capex

    df['marginal_cost'] = operation_cost

    df['carrier_cost'] = carrier_price + emission_factor * co2_price

    df['efficiency'] = eta

    df.to_csv(file_path)


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


def create_electricity_heatpump_profiles(data_raw_path, data_preprocessed_path):
    logging.info("Creating electricity heatpump profiles")

    raw_profile_paths = os.path.join(
        data_raw_path, 'OtherProfiles', 'COP'
    )

    profile_df = combine_profiles(raw_profile_paths, 'cop-profile')

    profile_df.to_csv(
        os.path.join(data_preprocessed_path, 'sequences', 'efficiency_profile.csv')
    )
