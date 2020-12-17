import logging
import os

import pandas as pd

from oemof.tools.economics import annuity


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
        scalars, 'EnergyConversion_Capacity_ElectricityHeat_CH4_BpCCGT'
    ) * get_parameter_values(
        scalars, 'EnergyConversion_Availability_ElectricityHeat_CH4_BpCCGT'
    ) * 1e-2  # percent to decimals

    electricity_per_heat = get_parameter_values(
        scalars, 'EnergyConversion_Power2HeatRatio_ElectricityHeat_CH4_BpCCGT')

    # eta_el = eta_total / (1 + 1 / electricity_per_heat)
    df['electric_efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_BpCCGT'
    ) / (1 + 1/electricity_per_heat) * 1e-2  # percent to decimal

    # eta_th = eta_total / (1 + electricity_per_heat)
    df['thermal_efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_BpCCGT'
    ) / (1 + electricity_per_heat) * 1e-2  # percent to decimal

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
        scalars, 'EnergyConversion_Capacity_ElectricityHeat_CH4_ExCCGT'
    ) * get_parameter_values(
        scalars, 'EnergyConversion_Availability_ElectricityHeat_CH4_ExCCGT'
    ) * 1e-2  # percent to decimals

    electricity_per_heat = get_parameter_values(
        scalars, 'EnergyConversion_Power2HeatRatio_ElectricityHeat_CH4_ExCCGT')

    # eta_el = eta_total / (1 + 1 / electricity_per_heat)
    electric_efficiency = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_ExCCGT'
    ) / (1 + 1/electricity_per_heat) * 1e-2  # percent to decimal

    df['electric_efficiency'] = electric_efficiency

    # eta_th = eta_total / (1 + electricity_per_heat)
    thermal_efficiency = get_parameter_values(
        scalars, 'EnergyConversion_EtaNominal_ElectricityHeat_CH4_ExCCGT'
    ) / (1 + electricity_per_heat) * 1e-2  # percent to decimal

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


def update_boiler_large(data_preprocessed_path, scalars):
    logging.info("Updating ch4-boiler-large file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-boiler-large.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['name'] = df['name'].str.replace(
        'ch4-boiler', 'ch4-boiler-large', regex=False
    )

    df['tech'] = 'boiler-large'

    df['capacity'] = get_parameter_values(scalars, 'EnergyConversion_Capacity_Heat_CH4_Large')

    df['efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_Eta_Heat_CH4_Large') * 0.01  # Percent to decimals

    df['carrier_cost'] = get_parameter_values(
        scalars, 'Energy_Price_CH4') * 1e-3  # Eur/GWh to Eur/MWh

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_CH4_Large') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_boiler_small(data_preprocessed_path, scalars):
    logging.info("Updating ch4-boiler-small file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'ch4-boiler-small.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    # Replace AT-ch4-boiler by AT-ch4-boiler-small
    df['name'] = df['name'].str.replace(
        'ch4-boiler', 'ch4-boiler-small', regex=False
    )

    df['tech'] = 'boiler-small'

    df['capacity'] = get_parameter_values(scalars, 'EnergyConversion_Capacity_Heat_CH4_Small')

    df['efficiency'] = get_parameter_values(
        scalars, 'EnergyConversion_Eta_Heat_CH4_Small') * 0.01  # Percent to decimals

    df['carrier_cost'] = get_parameter_values(
        scalars, 'Energy_Price_CH4') * 1e-3  # Eur/GWh to Eur/MWh

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_CH4_Small') * 1e-3  # Eur/GWh to Eur/MWh

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
        scalars, 'EnergyConversion_VarOM_Heat_Electricity_Large') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_electricity_heatpump_small(data_preprocessed_path, scalars):
    logging.info("Updating electricity-heatpump-small file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-heatpump-small.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['name'] = df['name'].str.replace(
        'electricity-heatpump', 'electricity-heatpump-small', regex=False
    )

    df['tech'] = 'heatpump-small'

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_Heat_ElectricityHeat_Small'
    )

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_ElectricityHeat_Small') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_electricity_heatpump_large(data_preprocessed_path, scalars):
    logging.info("Updating electricity-heatpump-large file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-heatpump-large.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['name'] = df['name'].str.replace(
        'electricity-heatpump', 'electricity-heatpump-large', regex=False
    )

    df['tech'] = 'heatpump-large'

    df['capacity'] = get_parameter_values(
        scalars, 'EnergyConversion_Capacity_Heat_ElectricityHeat_Large'
    )

    df['marginal_cost'] = get_parameter_values(
        scalars, 'EnergyConversion_VarOM_Heat_ElectricityHeat_Large') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_heat_storage_small(data_preprocessed_path, scalars):
    logging.info("Updating heat-storage-large file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'heat-storage-small.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['name'] = df['name'].str.replace(
        'heat-storage', 'heat-storage-small', regex=False
    )

    df['tech'] = 'storage-small'

    df['capacity'] = get_parameter_values(scalars, 'Storage_Capacity_Heat_SmallCharge')

    df['storage_capacity'] = get_parameter_values(
        scalars, 'Storage_Capacity_Heat_SmallStorage') * 1e3  # GWh to MWh

    df['loss_rate'] = get_parameter_values(
        scalars, 'Storage_SelfDischarge_Heat_Small') * 0.01  # Percent to decimals

    df['efficiency'] = get_parameter_values(
        scalars, 'Storage_Eta_Heat_SmallCharge') * 0.01  # Percent to decimals

    df['marginal_cost'] = get_parameter_values(
        scalars, 'Storage_VarOM_Heat_Small') * 1e-3  # Eur/GWh to Eur/MWh

    # Write back to csv file
    df.to_csv(file_path)


def update_heat_storage_large(data_preprocessed_path, scalars):
    logging.info("Updating heat-storage-large file")

    file_path = os.path.join(data_preprocessed_path, 'elements', 'heat-storage-large.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    df['name'] = df['name'].str.replace(
        'heat-storage', 'heat-storage-large', regex=False
    )

    df['tech'] = 'storage-large'

    df['capacity'] = get_parameter_values(scalars, 'Storage_Capacity_Heat_LargeCharge')

    df['storage_capacity'] = get_parameter_values(
        scalars, 'Storage_Capacity_Heat_LargeStorage') * 1e3  # GWh to MWh

    df['loss_rate'] = get_parameter_values(
        scalars, 'Storage_SelfDischarge_Heat_Large') * 0.01  # Percent to decimals

    df['efficiency'] = get_parameter_values(
        scalars, 'Storage_Eta_Heat_LargeCharge') * 0.01  # Percent to decimals

    df['marginal_cost'] = get_parameter_values(
        scalars, 'Storage_VarOM_Heat_Large') * 1e-3  # Eur/GWh to Eur/MWh

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

    link['from_to_capacity'] = transmission_capacity

    link['to_from_capacity'] = transmission_capacity

    # Calculation with pandas series
    link['loss'] = (
        transmission_length * 0.01  # km -> 100 km
        * transmission_loss_per_100km * 0.01  # percent -> 0..1
    )

    varom = get_parameter_values(scalars, 'Transmission_VarOM_Electricity_Grid')

    link['marginal_cost'] = (
        varom *
        transmission_length
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


def update_h2_cavern(
        data_preprocessed_path,
        scalars,
        expandable=False,
        greenfield=False
):
    r"""
    Parameterization of a electricity H2 storage as asymmetrical storage.

    Discharging and charging device are lumped together.

    Undependent expansion of either storage or (dis)charging devices is neglected.
    (we only need full expandability for FlexMex_1_2b)

    Parameters
    ----------
    data_preprocessed_path
    scalars

    expandable : bool
    Determines whether capacity (discharge/charge and storage) is expandable

    greenfield : bool
    If true initial capacity is 0.

    Returns
    -------

    """
    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-h2_cavern.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    # Operation parameters
    availability = get_parameter_values(
        scalars,
        'Storage_Availability_H2_Cavern') * 1e-2  # percent -> 0...1

    capacity_charge = get_parameter_values(scalars, 'Storage_Capacity_H2_CavernCharge')

    capacity_discharge = get_parameter_values(scalars, 'Storage_Capacity_H2_CavernDischarge')

    storage_capacity = get_parameter_values(
        scalars, 'Storage_Capacity_H2_CavernStorage') * 1e3  # GWh to MWh

    self_discharge = get_parameter_values(
        scalars, 'Storage_SelfDischarge_Electricity_H2_Cavern') * 1e-2  # percent -> 0...1

    operation_cost = get_parameter_values(
        scalars, 'Storage_VarOM_H2_Cavern') * 1e-3  # Eur/GWh -> Eur/MWh

    eta_charge = get_parameter_values(
        scalars, 'Storage_Eta_H2_CavernCharge') * 1e-2  # percent -> 0...1

    eta_discharge = get_parameter_values(
        scalars, 'Storage_Eta_H2_CavernDischarge') * 1e-2  # percent -> 0...1

    # Investment parameters
    capex_charge = get_parameter_values(
        scalars,
        'Storage_Capex_H2_CavernCharge')

    capex_discharge = get_parameter_values(
        scalars,
        'Storage_Capex_H2_CavernDischarge')

    capex_storage = get_parameter_values(
        scalars,
        'Storage_Capex_H2_CavernStorage') * 1e-3  # Eur/GWh -> Eur/MWh

    fix_cost = get_parameter_values(
        scalars,
        'Storage_FixOM_H2_Cavern') * 1e-2  # percent -> 0...1

    # ignored:
    # Storage_LifeTime_H2_CavernCharge
    # Storage_LifeTime_H2_CavernDischarge

    lifetime = get_parameter_values(
        scalars,
        'Storage_LifeTime_H2_CavernStorage')

    interest = get_parameter_values(
        scalars,
        'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

    annualized_cost_charge = annuity(
        capex=capex_charge,
        n=lifetime,
        wacc=interest)

    annualized_cost_discharge = annuity(
        capex=capex_discharge,
        n=lifetime,
        wacc=interest)

    annualized_cost_storage = annuity(
        capex=capex_storage,
        n=lifetime,
        wacc=interest)

    # Actual assignments
    df['expandable'] = expandable

    if expandable and greenfield:
        df['capacity_charge'] = 0
        df['capacity_discharge'] = 0
        df['storage_capacity'] = 0
    else:
        df['capacity_charge'] = capacity_charge * availability
        df['capacity_discharge'] = capacity_discharge * availability
        df['storage_capacity'] = storage_capacity * availability

    df['loss_rate'] = self_discharge

    df['efficiency_charge'] = eta_charge
    df['efficiency_discharge'] = eta_discharge

    if expandable:
        df['capacity_cost_charge'] = annualized_cost_charge + fix_cost * capex_charge
        df['capacity_cost_discharge'] = annualized_cost_discharge + fix_cost * capex_discharge

        df['storage_capacity_cost'] = annualized_cost_storage + fix_cost * capex_storage

    df['marginal_cost'] = operation_cost

    # Write back to csv file
    df.to_csv(file_path)


def update_liion_battery(
        data_preprocessed_path,
        scalars,
        expandable=False,
        greenfield=False
):
    r"""
    Parameterization of a Li-ion battery storage.

    The battery storage is expandable only in conjunction with (dis)charging because the devices
    are not separated. The same is true for greenfield/brownfield optimization:
    Further (dis)charging devices cannot be added to existing storage capacities or vice versa.

    Mapping and calculation could be easier since symmetric parametrization of a battery fits
    perfectly to oemof facade's Storage object. For consistency reasons, however, we use H2_cavern
    update function as a template and keep as much as possible similar (values in Scalars.csv will
    make sure that it is symmetric again) making future abstraction into one update function
    easier.

    Parameters
    ----------
    data_preprocessed_path
    scalars

    expandable : bool
    Determines whether capacity is expandable

    greenfield : bool
    If true initial capacity is 0.

    Returns
    -------

    """
    file_path = os.path.join(data_preprocessed_path, 'elements', 'electricity-liion_battery.csv')

    # Read prepared csv file
    df = pd.read_csv(file_path, index_col='region')

    # Operation parameters
    availability = get_parameter_values(
        scalars,
        'Storage_Availability_Electricity_LiIonBattery') * 1e-2  # percent -> 0...1

    capacity_charge = get_parameter_values(
        scalars, 'Storage_Capacity_Electricity_LiIonBatteryCharge')

    capacity_discharge = get_parameter_values(
        scalars, 'Storage_Capacity_Electricity_LiIonBatteryDischarge')

    storage_capacity = get_parameter_values(
        scalars, 'Storage_Capacity_Electricity_LiIonBatteryStorage') * 1e3  # GWh to MWh

    self_discharge = get_parameter_values(
        scalars, 'Storage_SelfDischarge_Electricity_LiIonBattery') * 1e-2  # percent -> 0...1

    operation_cost = get_parameter_values(
        scalars, 'Storage_VarOM_Electricity_LiIonBattery') * 1e-3  # Eur/GWh -> Eur/MWh

    eta_charge = get_parameter_values(
        scalars, 'Storage_Eta_Electricity_LiIonBatteryCharge') * 1e-2  # percent -> 0...1

    eta_discharge = get_parameter_values(
        scalars, 'Storage_Eta_Electricity_LiIonBatteryDischarge') * 1e-2  # percent -> 0...1

    # Investment parameters
    capex_charge = get_parameter_values(
        scalars,
        'Storage_Capex_Electricity_LiIonBatteryCharge')

    capex_discharge = get_parameter_values(
        scalars,
        'Storage_Capex_Electricity_LiIonBatteryDischarge')

    capex_storage = get_parameter_values(
        scalars,
        'Storage_Capex_Electricity_LiIonBatteryStorage') * 1e-3  # Eur/GWh -> Eur/MWh

    fix_cost = get_parameter_values(
        scalars,
        'Storage_FixOM_Electricity_LiIonBattery') * 1e-2  # percent -> 0...1

    # ignored:
    # Storage_LifeTime_Electricity_LiIonBatteryCharge
    # Storage_LifeTime_Electricity_LiIonBatteryDischarge

    lifetime = get_parameter_values(
        scalars,
        'Storage_LifeTime_Electricity_LiIonBatteryStorage')

    interest = get_parameter_values(
        scalars,
        'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

    annualized_cost_charge = annuity(
        capex=capex_charge + capex_discharge,
        n=lifetime,
        wacc=interest)

    annualized_cost_storage = annuity(
        capex=capex_storage,
        n=lifetime,
        wacc=interest)

    # Actual assignments
    df['expandable'] = expandable

    if expandable and greenfield:
        df['capacity'] = 0
        df['storage_capacity'] = 0
    else:
        df['capacity'] = (capacity_charge + capacity_discharge) / 2 * availability
        df['storage_capacity'] = storage_capacity * availability

    df['loss_rate'] = self_discharge

    df['efficiency'] = (eta_charge + eta_discharge) / 2

    if expandable:
        df['capacity_cost'] = annualized_cost_charge + fix_cost * (capex_charge + capex_discharge)

        df['storage_capacity_cost'] = annualized_cost_storage + fix_cost * capex_storage

    df['marginal_cost'] = operation_cost

    # Write back to csv file
    df.to_csv(file_path)


def update_nuclear_st(data_preprocessed_path, scalars, expandable=False, greenfield=False):

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
    df['capacity'] = 0 if expandable and greenfield else capacity * availability

    if expandable:
        df['capacity_cost'] = annualized_cost + fix_cost * capex

    df['marginal_cost'] = operation_cost

    df['carrier_cost'] = carrier_price

    df['efficiency'] = eta

    df.to_csv(file_path)


def update_ch4_gt(data_preprocessed_path, scalars, expandable=False, greenfield=False):
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
    df['capacity'] = 0 if expandable and greenfield else capacity * availability

    if expandable:
        df['capacity_cost'] = annualized_cost + fix_cost * capex

    df['marginal_cost'] = operation_cost

    df['carrier_cost'] = carrier_price + emission_factor * co2_price

    df['efficiency'] = eta

    df.to_csv(file_path)


def update_hydro_reservoir(data_preprocessed_path, scalars):
    component = 'hydro-reservoir'

    logging.info(f"Updating {component} file")

    # TODO: This filepath should be moved to components.csv
    file_path = os.path.join(data_preprocessed_path, 'elements', component + '.csv')

    element_df = pd.read_csv(file_path, index_col='region')

    element_df['capacity_turbine'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Hydro_ReservoirTurbine')

    element_df['capacity_pump'] = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Hydro_ReservoirPump')

    storage_capacity = get_parameter_values(
        scalars,
        'EnergyConversion_Capacity_Electricity_Hydro_ReservoirStorage')

    initial_storage_level = get_parameter_values(
        scalars,
        'Energy_PrimaryEnergy_Hydro_Reservoir_FillingLevelStart')

    element_df['storage_capacity'] = storage_capacity

    # Recalculate filling level as a ratio of storage capacity (refer oemof.solph.components)
    element_df['initial_storage_level'] = initial_storage_level / storage_capacity

    element_df['efficiency_turbine'] = get_parameter_values(
        scalars,
        'EnergyConversion_Eta_Electricity_Hydro_ReservoirTurbine') * 1e-2  # percent -> 0...1

    element_df['efficiency_pump'] = get_parameter_values(
        scalars,
        'EnergyConversion_Eta_Electricity_Hydro_ReservoirPump') * 1e-2  # percent -> 0...1

    element_df['marginal_cost'] = get_parameter_values(
        scalars,
        'EnergyConversion_VarOM_Electricity_Hydro_Reservoir') * 1e-3  # Eur/GWh -> Eur/MWh

    element_df.to_csv(file_path)


def update_electricity_bev(data_preprocessed_path, scalars):
    electricity_bev_file = os.path.join(data_preprocessed_path, 'elements', 'electricity-bev.csv')

    electricity_bev = pd.read_csv(electricity_bev_file, index_col='region')

    electricity_bev['capacity'] = get_parameter_values(
        scalars,
        'Transport_CarNumber_Electricity_Cars'
    ) * get_parameter_values(
        scalars,
        'Transport_ConnecPower_Electricity_Cars')

    electricity_bev['storage_capacity'] = get_parameter_values(
        scalars,
        'Transport_CarNumber_Electricity_Cars'
    ) * get_parameter_values(
        scalars,
        'Transport_BatteryCap_Electricity_Cars') * 1e3  # GWh to MWh

    electricity_bev['efficiency_v2g'] = get_parameter_values(
        scalars,
        'Transport_EtaFeedIn_Electricity_Cars') * 1e-2  # percentage to decimal

    electricity_bev['amount'] = get_parameter_values(
        scalars,
        'Transport_AnnualDemand_Electricity_Cars') * 1e3  # GWh to MWh

    electricity_bev['marginal_cost'] = get_parameter_values(
        scalars,
        'Transport_VarOMGridFeedIn_Electricity_Cars') * 1e-3  # Eur/GWh to Eur/MWh

    electricity_bev.to_csv(electricity_bev_file)


update_dict = {
    'ch4-boiler-large': update_boiler_large,
    'ch4-boiler-small': update_boiler_small,
    'ch4-bpchp': update_bpchp,
    'ch4-extchp': update_extchp,
    'ch4-gt': update_ch4_gt,
    'electricity-bev': update_electricity_bev,
    'electricity-demand': update_electricity_demand,
    'electricity-heatpump_large': update_electricity_heatpump_large,
    'electricity-heatpump_small': update_electricity_heatpump_small,
    'electricity-pth': update_pth,
    'electricity-shortage': update_electricity_shortage,
    'electricity-transmission': update_link,
    'electricity-h2_cavern': update_h2_cavern,
    'heat-demand': update_heat_demand,
    'heat-shortage': update_heat_shortage,
    'heat-storage-large': update_heat_storage_large,
    'heat-storage-small': update_heat_storage_small,
    'hydro-reservoir': update_hydro_reservoir,
    'electricity-liion_battery': update_liion_battery,
    'uranium-nuclear-st': update_nuclear_st,
    'solar-pv': update_solar_pv,
    'wind-offshore': update_wind_offshore,
    'wind-onshore': update_wind_onshore,
}


def update_scalars(select_components, destination, scalars):
    for component, kwargs in select_components.items():
        print(f"Updating {component}")

        try:
            function = update_dict[component]

        except KeyError:
            print(f"There is no update function for component {component}!")
            continue

        if not kwargs:
            kwargs = {}

        function(data_preprocessed_path=destination, scalars=scalars, **kwargs)
