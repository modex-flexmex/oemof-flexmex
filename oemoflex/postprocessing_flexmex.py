import os
import logging

import numpy as np
import pandas as pd
from oemof.solph import EnergySystem
from oemof.tools.economics import annuity

import oemoflex.postprocessing as pp
from oemoflex.helpers import load_yaml, delete_empty_subdirs, load_elements, load_scalar_input_data
from oemoflex.parametrization_scalars import get_parameter_values


basic_columns = ['region', 'name', 'type', 'carrier', 'tech']

# Path definitions
module_path = os.path.abspath(os.path.dirname(__file__))

MODEL_CONFIG = 'model_config'

PATH_MAPPINGS_REL = '../flexmex_config'

path_mappings = os.path.abspath(os.path.join(module_path, PATH_MAPPINGS_REL))

path_map_output_timeseries = os.path.join(path_mappings, 'mapping-output-timeseries.yml')

path_map_input_scalars = os.path.join(path_mappings, 'mapping-input-scalars.yml')

# Load mappings
map_output_timeseries = load_yaml(path_map_output_timeseries)

FlexMex_Parameter_Map = load_yaml(path_map_input_scalars)


def get_calculated_parameters(df, oemoflex_scalars, parameter_name, factor):
    r"""
    Takes the pre-calculated parameter 'parameter_name' from
    'oemoflex_scalars' DataFrame and returns it multiplied by 'factor' (element-wise)
    with 'df' as a template

    Parameters
    ----------
    df
        output template DataFrame
    oemoflex_scalars
        DataFrame with pre-calculated parameters
    parameter_name
        parameter to manipulate
    factor
        factor to multiply parameter with

    Returns
    -------

    """
    calculated_parameters = oemoflex_scalars.loc[
        oemoflex_scalars['var_name'] == parameter_name].copy()

    if calculated_parameters.empty:
        logging.info("No key '{}' found.".format(parameter_name))

    # Make sure that values in columns to merge on are strings
    # See here:
    # https://stackoverflow.com/questions/39582984/pandas-merging-on-string-columns-not-working-bug
    calculated_parameters[basic_columns] = calculated_parameters[basic_columns].astype(str)

    df = pd.merge(
        df, calculated_parameters,
        on=basic_columns
    )

    df['var_value'] = df['var_value'] * factor

    return df


def get_invest_cost(oemoflex_scalars, prep_elements, scalars_raw):

    invest_cost = pd.DataFrame()

    for prep_el in prep_elements.values():
        # In the following line: Not 'is'! pandas overloads operators!
        if 'expandable' in prep_el.columns and prep_el['expandable'][0] == True:  # noqa: E712, E501 # pylint: disable=C0121
            # element is expandable --> 'invest' values exist
            df = prep_el[basic_columns]

            tech_name = prep_el['tech'][0]
            parameters = FlexMex_Parameter_Map['tech'][tech_name]

            interest = get_parameter_values(
                scalars_raw,
                'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

            # Special treatment for storages
            if tech_name in ['h2_cavern', 'liion_battery']:

                # Charge device
                capex = get_parameter_values(scalars_raw, parameters['charge_capex'])

                lifetime = get_parameter_values(scalars_raw, parameters['charge_lifetime'])

                annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

                df_charge = get_calculated_parameters(df, oemoflex_scalars,
                                                      'capacity_charge_invest',
                                                      annualized_cost)

                # Discharge device
                capex = get_parameter_values(scalars_raw, parameters['discharge_capex'])

                lifetime = get_parameter_values(scalars_raw, parameters['discharge_lifetime'])

                annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

                df_discharge = get_calculated_parameters(df, oemoflex_scalars,
                                                         'capacity_discharge_invest',
                                                         annualized_cost)

                # Storage cavern
                capex = get_parameter_values(scalars_raw,
                                             parameters['storage_capex']) * 1e-3  # €/MWh -> €/GWh

                lifetime = get_parameter_values(scalars_raw, parameters['storage_lifetime'])

                annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

                df_storage = get_calculated_parameters(df, oemoflex_scalars,
                                                       'storage_capacity_invest',
                                                       annualized_cost)

                df = pd.concat([df_charge, df_discharge, df_storage])

                # Sum the 3 amounts per storage, keep indexes as columns
                df = df.groupby(by=basic_columns, as_index=False).sum()

            else:
                capex = get_parameter_values(scalars_raw, parameters['capex'])

                lifetime = get_parameter_values(scalars_raw, parameters['lifetime'])

                annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

                df = get_calculated_parameters(df, oemoflex_scalars, 'invest', annualized_cost)

            df['var_name'] = 'cost_invest'
            df['var_unit'] = 'Eur'

            invest_cost = pd.concat([invest_cost, df])

    return invest_cost


def get_fixom_cost(oemoflex_scalars, prep_elements, scalars_raw):

    fixom_cost = pd.DataFrame()

    for prep_el in prep_elements.values():
        # not 'is'! pandas overloads operators!
        if 'expandable' in prep_el.columns and prep_el['expandable'][0] == True:  # noqa: E712, E501 # pylint: disable=C0121
            # element is expandable --> 'invest' values exist
            df = prep_el[basic_columns]

            tech_name = prep_el['tech'][0]
            parameters = FlexMex_Parameter_Map['tech'][tech_name]

            # Special treatment for storages
            if tech_name in ['h2_cavern', 'liion_battery']:

                # One fix cost factor for all sub-components
                fix_cost_factor = get_parameter_values(
                    scalars_raw, parameters['fixom']) * 1e-2  # percent -> 0...1

                # Charge device
                capex = get_parameter_values(scalars_raw, parameters['charge_capex'])
                df_charge = get_calculated_parameters(df, oemoflex_scalars,
                                                      'capacity_charge_invest',
                                                      fix_cost_factor * capex)

                # Discharge device
                capex = get_parameter_values(scalars_raw, parameters['discharge_capex'])
                df_discharge = get_calculated_parameters(df, oemoflex_scalars,
                                                         'capacity_discharge_invest',
                                                         fix_cost_factor * capex)

                # Storage cavern
                capex = get_parameter_values(scalars_raw,
                                             parameters['storage_capex']) * 1e-3  # €/MWh -> €/GWh

                df_storage = get_calculated_parameters(df, oemoflex_scalars,
                                                       'storage_capacity_invest',
                                                       fix_cost_factor * capex)

                df = pd.concat([df_charge, df_discharge, df_storage])

                # Sum the 3 amounts per storage, keep indexes as columns
                df = df.groupby(by=basic_columns, as_index=False).sum()

            else:
                capex = get_parameter_values(scalars_raw, parameters['capex'])

                fix_cost_factor = get_parameter_values(
                    scalars_raw, parameters['fixom']) * 1e-2  # percent -> 0...1

                df = get_calculated_parameters(df, oemoflex_scalars,
                                               'invest',
                                               fix_cost_factor * capex)

            df['var_name'] = 'cost_fixom'
            df['var_unit'] = 'Eur'

            fixom_cost = pd.concat([fixom_cost, df])

    return fixom_cost


def get_fuel_cost(oemoflex_scalars, prep_elements, scalars_raw):
    r"""
    Re-calculates the fuel costs from the carrier costs if there are CO2 emissions.

    Bypass for non-emission carriers (cost_carrier = cost_fuel).

    Having emissions or not is determined by the parameter mapping dict (emission_factor).

    TODO Let's think about using the 'flow' values as input because this way we could
     generalize the structure with get_varom_cost() and get_emission_cost() into one function
     for all 'flow'-derived values.

    Parameters
    ----------
    oemoflex_scalars
    prep_elements
    scalars_raw

    Returns
    -------

    """

    fuel_cost = pd.DataFrame()

    # Iterate over oemof.tabular components (technologies)
    for prep_el in prep_elements.values():
        if 'carrier_cost' in prep_el.columns:

            # Set up a list of the current technology's elements
            df = prep_el.loc[:, basic_columns]

            # Select carriers from the parameter map
            carrier_name = prep_el['carrier'][0]
            parameters = FlexMex_Parameter_Map['carrier'][carrier_name]

            # Only re-calculate if there is a CO2 emission
            if 'emission_factor' in parameters.keys():

                price_carrier = get_parameter_values(scalars_raw, parameters['carrier_price'])

                price_emission = get_parameter_values(scalars_raw, parameters['co2_price'])\
                    * get_parameter_values(scalars_raw, parameters['emission_factor'])

                factor = price_carrier / (price_carrier + price_emission)

            # Otherwise take the carrier cost value for the fuel cost
            else:
                factor = 1.0

            df = get_calculated_parameters(df, oemoflex_scalars, 'cost_carrier', factor)

            # Update other columns
            df['var_name'] = 'cost_fuel'
            df['var_unit'] = 'Eur'

            # Append current technology elements to the return DataFrame
            fuel_cost = pd.concat([fuel_cost, df])

    return fuel_cost


def get_emission_cost(oemoflex_scalars, prep_elements, scalars_raw):
    r"""
    Re-calculates the emission costs from the carrier costs if there are CO2 emissions.

    Structure only slightly different (+ else branch) from get_fuel_cost() because there are costs
    of zero instead of the fuel costs (in get_fuel_cost()) if there are no emissions.

    Parameters
    ----------
    oemoflex_scalars
    prep_elements
    scalars_raw

    Returns
    -------

    """

    emission_cost = pd.DataFrame()

    # Iterate over oemof.tabular components (technologies)
    for prep_el in prep_elements.values():
        if 'carrier_cost' in prep_el.columns:

            # Set up a list of the current technology's elements
            df = prep_el.loc[:, basic_columns]

            # Select carriers from the parameter map
            carrier_name = prep_el['carrier'][0]
            parameters = FlexMex_Parameter_Map['carrier'][carrier_name]

            # Only re-calculate if there is a CO2 emission
            if 'emission_factor' in parameters.keys():
                price_carrier = get_parameter_values(scalars_raw, parameters['carrier_price'])

                price_emission = get_parameter_values(scalars_raw, parameters['co2_price']) \
                    * get_parameter_values(scalars_raw, parameters['emission_factor'])

                factor = price_emission / (price_carrier + price_emission)

                df = get_calculated_parameters(df, oemoflex_scalars, 'cost_carrier', factor)

            else:
                df['var_value'] = 0.0

            # Update other columns
            df['var_name'] = 'cost_emission'
            df['var_unit'] = 'Eur'

            # Append current technology elements to the return DataFrame
            emission_cost = pd.concat([emission_cost, df])

    return emission_cost


def create_postprocessed_results_subdirs(postprocessed_results_dir):
    for parameters in map_output_timeseries.values():
        for subdir in parameters.values():
            path = os.path.join(postprocessed_results_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)


def map_to_flexmex_results(oemoflex_scalars, flexmex_scalars_template, mapping, usecase):
    mapping = mapping.set_index('Parameter')
    flexmex_scalars = flexmex_scalars_template.copy()
    oemoflex_scalars = oemoflex_scalars.set_index(['region', 'carrier', 'tech', 'var_name'])
    oemoflex_scalars.loc[oemoflex_scalars['var_unit'] == 'MWh', 'var_value'] *= 1e-3  # MWh to GWh

    for i, row in flexmex_scalars.loc[flexmex_scalars['UseCase'] == usecase].iterrows():
        try:
            select = mapping.loc[row['Parameter'], :]
        except KeyError:
            continue

        try:
            value = oemoflex_scalars.loc[
                (row['Region'],
                 select['carrier'],
                 select['tech'],
                 select['var_name']), 'var_value']

        except KeyError:
            print(f"Key "
                  f"{(row['Region'], select['carrier'], select['tech'], select['var_name'])}"
                  f" not found")

            continue

        if isinstance(value, float):
            flexmex_scalars.loc[i, 'Value'] = np.around(value)

    flexmex_scalars.loc[:, 'Modell'] = 'oemof'

    return flexmex_scalars


def save_flexmex_timeseries(sequences_by_tech, usecase, model, year, dir):

    for carrier_tech in sequences_by_tech.columns.unique(level='carrier_tech'):
        try:
            components_paths = map_output_timeseries[carrier_tech]
        except KeyError:
            print(f"Entry for {carrier_tech} does not exist in {path_map_output_timeseries}.")
            continue

        idx = pd.IndexSlice
        for var_name, subdir in components_paths.items():
            df_var_value = sequences_by_tech.loc[:, idx[:, carrier_tech, var_name]]
            for region in df_var_value.columns.get_level_values('region'):
                filename = os.path.join(
                    dir,
                    subdir,
                    '_'.join([usecase, model, region, year]) + '.csv'
                )

                single_column = df_var_value.loc[:, region]
                single_column = single_column.reset_index(drop=True)
                single_column.columns = single_column.columns.droplevel('carrier_tech')
                remaining_column_name = list(single_column)[0]
                single_column.rename(columns={remaining_column_name: 'value'}, inplace=True)
                single_column.index.name = 'timeindex'
                single_column.to_csv(filename, header=True)

    delete_empty_subdirs(dir)


def run_postprocessing(year, name, exp_paths):
    create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

    # load raw data
    scalars_raw = load_scalar_input_data()

    # load scalars templates
    flexmex_scalars_template = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
    flexmex_scalars_template = flexmex_scalars_template.loc[
        flexmex_scalars_template['UseCase'] == name
    ]

    # load mapping
    mapping = pd.read_csv(os.path.join(path_mappings, 'mapping-output-scalars.csv'))

    # Load preprocessed elements
    prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(exp_paths.results_optimization)

    # format results sequences
    sequences_by_tech = pp.get_sequences_by_tech(es.results)

    flow_net_sum = pp.sum_transmission_flows(sequences_by_tech)

    sequences_by_tech = pd.concat([sequences_by_tech, flow_net_sum], axis=1)

    df_re_generation = pp.aggregate_re_generation_timeseries(sequences_by_tech)

    sequences_by_tech = pd.concat([sequences_by_tech, df_re_generation], axis=1)

    oemoflex_scalars = pd.DataFrame(
        columns=[
            'region',
            'name',
            'type',
            'carrier',
            'tech',
            'var_name',
            'var_value',
            'var_unit'
        ]
    )

    # then sum the flows
    summed_sequences = pp.get_summed_sequences(sequences_by_tech, prep_elements)
    oemoflex_scalars = pd.concat([oemoflex_scalars, summed_sequences])

    # get re_generation
    re_generation = pp.get_re_generation(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, re_generation])

    # losses (storage, transmission)
    transmission_losses = pp.get_transmission_losses(oemoflex_scalars)
    storage_losses = pp.get_storage_losses(oemoflex_scalars)
    reservoir_losses = pp.get_reservoir_losses(oemoflex_scalars)
    oemoflex_scalars = pd.concat([
        oemoflex_scalars,
        transmission_losses,
        storage_losses,
        reservoir_losses
    ])

    # get capacities
    capacities = pp.get_capacities(es)
    formatted_capacities = pp.format_capacities(oemoflex_scalars, capacities)
    oemoflex_scalars = pd.concat([oemoflex_scalars, formatted_capacities])

    # costs
    varom_cost = pp.get_varom_cost(oemoflex_scalars, prep_elements)
    carrier_cost = pp.get_carrier_cost(oemoflex_scalars, prep_elements)
    fuel_cost = get_fuel_cost(carrier_cost, prep_elements, scalars_raw)
    emission_cost = get_emission_cost(carrier_cost, prep_elements, scalars_raw)
    aggregated_emission_cost = pp.aggregate_by_country(emission_cost)
    invest_cost = get_invest_cost(oemoflex_scalars, prep_elements, scalars_raw)
    fixom_cost = get_fixom_cost(oemoflex_scalars, prep_elements, scalars_raw)
    oemoflex_scalars = pd.concat([
        oemoflex_scalars,
        varom_cost,
        carrier_cost,
        fuel_cost,
        aggregated_emission_cost,
        invest_cost,
        fixom_cost
    ])

    # emissions
    emissions = pp.get_emissions(oemoflex_scalars, scalars_raw)
    oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

    storage = pp.aggregate_storage_capacities(oemoflex_scalars)
    other = pp.aggregate_other_capacities(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, storage, other])

    total_system_cost = pp.get_total_system_cost(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, total_system_cost])

    # map direction of links
    oemoflex_scalars = pp.map_link_direction(oemoflex_scalars)

    # set experiment info
    oemoflex_scalars['usecase'] = name
    oemoflex_scalars['year'] = year

    # oemoflex_scalars.to_csv('~/Desktop/oemoflex_scalars.csv')

    # map to FlexMex data format
    flexmex_scalar_results = map_to_flexmex_results(
        oemoflex_scalars, flexmex_scalars_template, mapping, name
    )

    # save results
    flexmex_scalar_results.to_csv(
        os.path.join(exp_paths.results_postprocessed, 'Scalars.csv'),
        index=False
    )

    save_oemoflex_scalars = True
    if save_oemoflex_scalars:
        oemoflex_scalars.sort_values(['carrier', 'tech', 'var_name'], axis=0, inplace=True)
        oemoflex_scalars.to_csv(
            os.path.join(exp_paths.results_postprocessed, 'oemoflex_scalars.csv'),
            index=False
        )

    save_oemoflex_timeseries = False
    if save_oemoflex_timeseries:
        pp.export_bus_sequences(
            es,
            os.path.join(exp_paths.results_postprocessed, 'oemoflex-timeseries')
        )

    save_flexmex_timeseries(
        sequences_by_tech, name, 'oemof', '2050', exp_paths.results_postprocessed
    )
