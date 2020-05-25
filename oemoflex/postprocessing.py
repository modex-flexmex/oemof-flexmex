import os
import logging

import numpy as np
import pandas as pd
import yaml

from oemof.solph import EnergySystem, Bus, Sink
from oemof.tabular import facades
import oemof.tabular.tools.postprocessing as pp
from oemoflex.helpers import delete_empty_subdirs, load_elements
from oemoflex.preprocessing import get_parameter_values

basic_columns = ['region', 'name', 'type', 'carrier', 'tech']

module_path = os.path.abspath(os.path.dirname(__file__))
path_config = os.path.join(module_path, 'postprocessed_paths.yaml')

with open(path_config, 'r') as config_file:
    pp_paths = yaml.safe_load(config_file)


def create_postprocessed_results_subdirs(postprocessed_results_dir):
    for subdir, value in pp_paths.items():
        if value['sequences']:
            for subsubdir in value['sequences']:
                path = os.path.join(postprocessed_results_dir, subdir, subsubdir)
                if not os.path.exists(path):
                    os.makedirs(path)


def get_capacities(es):
    r"""
    Calculates the capacities of all components.

    Adapted from oemof.tabular.tools.postprocessing.write_results()

    Parameters
    ----------
    es : oemof.solph.EnergySystem
        EnergySystem containing the results.

    Returns
    -------
    capacities : pd.DataFrame
        DataFrame containing the capacities.
    """
    try:
        # TODO: Adapt this for investment
        all = pp.bus_results(es, es.results, select="scalars", concat=True)
        all.name = "value"
        endogenous = all.reset_index()
        endogenous["tech"] = [
            getattr(t, "tech", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["carrier"] = [
            getattr(t, "carrier", np.nan)
            for t in all.index.get_level_values(0)
        ]
        endogenous.set_index(
            ["from", "to", "type", "tech", "carrier"], inplace=True
        )

    except ValueError:
        endogenous = pd.DataFrame()

    d = dict()
    for node in es.nodes:
        if not isinstance(node, (Bus, Sink, facades.Shortage)):
            if getattr(node, "capacity", None) is not None:
                if isinstance(node, facades.TYPEMAP["link"]):
                    pass
                else:
                    key = (
                        node.region,
                        node.label,
                        # [n for n in node.outputs.keys()][0],
                        node.type,
                        node.carrier,
                        node.tech,  # tech & carrier are oemof-tabular specific
                        'capacity'
                    )  # for oemof logic
                    d[key] = {'var_value': node.capacity}
    exogenous = pd.DataFrame.from_dict(d).T  # .dropna()

    if not exogenous.empty:
        exogenous.index = exogenous.index.set_names(
            ['region', 'name', 'type', 'carrier', 'tech', 'var_name']
        )

    capacities = pd.concat([endogenous, exogenous])

    return capacities


def format_capacities(oemoflex_scalars, capacities):
    df = pd.DataFrame(columns=oemoflex_scalars.columns)
    df.loc[:, 'name'] = capacities.reset_index().loc[:, 'name']
    df.loc[:, 'tech'] = capacities.reset_index().loc[:, 'tech']
    df.loc[:, 'carrier'] = capacities.reset_index().loc[:, 'carrier']
    df.loc[:, 'var_name'] = capacities.reset_index().loc[:, 'var_name']
    df.loc[:, 'var_value'] = capacities.reset_index().loc[:, 'var_value']
    df.loc[:, 'type'] = capacities.reset_index().loc[:, 'type']
    df.loc[:, 'region'] = capacities.reset_index().loc[:, 'region']

    df['var_unit'] = 'MW'

    return df


def get_sequences_by_tech(results):
    r"""
    Creates a dictionary with carrier-tech as keys with the sequences of the components
    from optimization results.

    Parameters
    ----------
    results : dict
        Dictionary containing oemof.solph.Model results.

    Returns
    -------
    sequences_by_tech : dict
        Dictionary containing sequences with carrier-tech as keys.
    """
    sequences = {key: value['sequences'] for key, value in results.items()}

    sequences_by_tech = {}
    for key, df in sequences.items():
        if isinstance(key[0], Bus):
            component = key[1]
            bus = key[0]

            if isinstance(component, facades.Link):
                if bus == component.from_bus:
                    var_name = 'flow_gross_forward'
                elif bus == component.to_bus:
                    var_name = 'flow_gross_backward'

            elif isinstance(component, (facades.ExtractionTurbine, facades.BackpressureTurbine)):
                var_name = 'flow_fuel'

            else:
                var_name = 'flow_in'

        if isinstance(key[1], Bus):
            bus = key[1]
            component = key[0]

            if isinstance(component, facades.Link):
                if bus == component.to_bus:
                    var_name = 'flow_net_forward'
                elif bus == component.from_bus:
                    var_name = 'flow_net_backward'

            elif isinstance(component, (facades.ExtractionTurbine, facades.BackpressureTurbine)):
                if bus == component.electricity_bus:
                    var_name = 'flow_electricity'

                elif bus == component.heat_bus:
                    var_name = 'flow_heat'

            else:
                var_name = 'flow_out'

        if key[1] is None:
            component = key[0]
            var_name = 'storage_content'

        carrier_tech = component.carrier + '-' + component.tech
        if carrier_tech not in sequences_by_tech:
            sequences_by_tech[carrier_tech] = []

        df.columns = pd.MultiIndex.from_tuples([(component.label, var_name)])
        df.columns.names = ['name', 'var_name']
        sequences_by_tech[carrier_tech].append(df)

    sequences_by_tech = {key: pd.concat(value, 1) for key, value in sequences_by_tech.items()}

    return sequences_by_tech


def get_summed_sequences(sequences_by_tech, prep_elements):
    summed_sequences = []
    for tech_carrier, sequence in sequences_by_tech.items():
        df = prep_elements[tech_carrier][basic_columns]
        sum = sequence.sum()
        sum.name = 'var_value'
        sum = sum.reset_index()
        df = pd.merge(df, sum, on='name')
        summed_sequences.append(df)

    summed_sequences = pd.concat(summed_sequences, sort=True)
    summed_sequences = summed_sequences.loc[summed_sequences['var_name'] != 'storage_content']
    summed_sequences['var_unit'] = 'MWh'

    return summed_sequences


def get_re_generation(oemoflex_scalars):
    renewable_carriers = ['solar', 'wind']
    re_generation = pd.DataFrame(columns=oemoflex_scalars.columns)

    re_flow = oemoflex_scalars.loc[(oemoflex_scalars['carrier'].isin(renewable_carriers)) &
                                   (oemoflex_scalars['var_name'] == 'flow_out')]

    curtailment = oemoflex_scalars.loc[(oemoflex_scalars['carrier'] == 'electricity') &
                                       (oemoflex_scalars['tech'] == 'curtailment') &
                                       (oemoflex_scalars['var_name'] == 'flow_in')]

    sum = re_flow.groupby('region').sum() - curtailment.groupby('region').sum()

    re_generation['region'] = sum.index
    re_generation['carrier'] = 're'
    re_generation['type'] = 'none'
    re_generation['tech'] = 'none'
    re_generation['var_name'] = 're_generation'
    re_generation = re_generation.drop('var_value', 1)
    re_generation = pd.merge(re_generation, sum['var_value'], on='region')
    re_generation['var_unit'] = 'MWh'

    return re_generation


def get_transmission_losses(oemoflex_scalars):
    r"""Calculates losses_forward losses_backward for each link."""

    def gross_minus_net_flow(direction):
        flow_gross = oemoflex_scalars.loc[
            oemoflex_scalars['var_name'] == f'flow_gross_{direction}'].set_index('name')

        flow_net = oemoflex_scalars.loc[
            oemoflex_scalars['var_name'] == f'flow_net_{direction}'].set_index('name')

        loss = flow_gross.copy()
        loss['var_name'] = f'loss_{direction}'
        loss['var_value'] = flow_gross['var_value'] - flow_net['var_value']

        return loss

    losses = []
    for direction in ['forward', 'backward']:
        loss = gross_minus_net_flow(direction)
        losses.append(loss)

    losses = pd.concat(losses)
    losses = losses.reset_index()

    return losses


def get_storage_losses(oemoflex_scalars):
    storage_data = oemoflex_scalars.loc[oemoflex_scalars['type'] == 'storage']
    flow_in = storage_data.loc[storage_data['var_name'] == 'flow_in'].set_index('name')
    flow_out = storage_data.loc[storage_data['var_name'] == 'flow_out'].set_index('name')

    losses = flow_in.copy()
    losses['var_name'] = 'losses'
    losses['var_value'] = flow_in['var_value'] - flow_out['var_value']
    losses = losses.reset_index()

    return losses


def get_emissions():
    # TODO: Not included yet
    pass


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


def get_varom_cost(oemoflex_scalars, prep_elements):
    varom_cost = []
    for _, prep_el in prep_elements.items():
        if 'marginal_cost' in prep_el.columns:
            df = prep_el[basic_columns]
            if prep_el['type'][0] == 'excess':
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_in']
            elif prep_el['type'][0] in ['backpressure', 'extraction']:
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_electricity']
            elif prep_el['type'][0] in ['link', 'electrical line']:
                net_flows = ['flow_net_forward', 'flow_net_backward']
                flow = oemoflex_scalars.loc[
                    oemoflex_scalars['var_name'].isin(net_flows)]
                flow = flow.groupby(basic_columns, as_index=False).sum()
            else:
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_out']
            df = pd.merge(
                df, flow,
                on=basic_columns
            )
            df['var_value'] = df['var_value'] * prep_el['marginal_cost']
            df['var_name'] = 'cost_varom'

            varom_cost.append(df)

    varom_cost = pd.concat(varom_cost, sort=True)
    varom_cost['var_unit'] = 'Eur'

    return varom_cost


def get_carrier_cost(oemoflex_scalars, prep_elements):
    carrier_cost = []
    for _, prep_el in prep_elements.items():
        if 'carrier_cost' in prep_el.columns:
            df = prep_el[basic_columns]
            if prep_el['type'][0] in ['backpressure', 'extraction']:
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_fuel']
            else:
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_in']
            df = pd.merge(
                df, flow,
                on=basic_columns
            )
            df['var_value'] = df['var_value'] * prep_el['carrier_cost']
            df['var_name'] = 'cost_carrier'

            carrier_cost.append(df)

    if carrier_cost:
        carrier_cost = pd.concat(carrier_cost, sort=True)
    else:
        carrier_cost = pd.DataFrame(carrier_cost)

    carrier_cost['var_unit'] = 'Eur'

    return carrier_cost


def get_fuel_cost(oemoflex_scalars, scalars_raw):
    # TODO: Generalize to be useful for any kind of fossile carrier, not only CH4.
    try:
        fuel_cost = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'cost_carrier'].copy()
    except KeyError:
        logging.info("No key 'cost_carrier' found to calculate 'cost_fuel'.")
        return None

    fuel_cost['var_name'] = 'cost_fuel'

    price_ch4 = get_parameter_values(scalars_raw, 'Energy_Price_CH4')

    price_emission = get_parameter_values(scalars_raw, 'Energy_Price_CO2')\
        * get_parameter_values(scalars_raw, 'Energy_EmissionFactor_CH4')

    factor = price_ch4 / (price_ch4 + price_emission)

    fuel_cost['var_value'] *= factor

    return fuel_cost


def get_emission_cost(oemoflex_scalars, scalars_raw):
    # TODO: Generalize to be useful for any kind of fossile carrier, not only CH4.
    try:
        emission_cost = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'cost_carrier'].copy()
    except KeyError:
        logging.info("No key 'cost_carrier' found to calculate 'cost_emission'.")
        return None

    emission_cost['var_name'] = 'cost_emission'

    price_ch4 = get_parameter_values(scalars_raw, 'Energy_Price_CH4')

    price_emission = get_parameter_values(scalars_raw, 'Energy_Price_CO2')\
        * get_parameter_values(scalars_raw, 'Energy_EmissionFactor_CH4')

    factor = price_emission / (price_ch4 + price_emission)

    emission_cost['var_value'] *= factor

    return emission_cost


def get_capacity_cost():
    # TODO: Problem there is no distinction btw fixom and invest cost!
    # capacities * prep_elements[capacity_cost]
    pass


def get_total_system_cost(oemoflex_scalars):
    cost_list = ['cost_varom', 'cost_fuel', 'cost_capacity', 'cost_emission']
    df = oemoflex_scalars.loc[oemoflex_scalars['var_name'].isin(cost_list)]
    total_system_cost = pd.DataFrame(columns=oemoflex_scalars.columns)
    total_system_cost.loc[0, 'var_name'] = 'total_system_cost'
    total_system_cost.loc[0, 'var_value'] = df['var_value'].sum()
    total_system_cost['carrier'] = 'ALL'
    total_system_cost['tech'] = 'ALL'
    total_system_cost['region'] = 'ALL'
    total_system_cost['var_unit'] = 'Eur'

    return total_system_cost


def save_flexmex_timeseries(sequences_by_tech, usecase, model, year, dir):
    path_by_carrier_tech = {value['component']: key for key, value in pp_paths.items()}
    sequences = {value['component']: value['sequences'] for key, value in pp_paths.items()}

    for carrier_tech, df in sequences_by_tech.items():
        try:
            subfolder = path_by_carrier_tech[carrier_tech]
        except KeyError:
            print(f"Entry for {carrier_tech} does not exist in {path_config}.")
            continue

        idx = pd.IndexSlice
        for subsubfolder, var_name in sequences[carrier_tech].items():
            df_var_value = df.loc[:, idx[:, var_name]]
            for column in df_var_value.columns:
                region = column[0].split('-')[0]
                filename = os.path.join(
                    dir,
                    subfolder,
                    subsubfolder,
                    '_'.join(['FlexMex1', usecase, model, region, year]) + '.csv'
                )

                single_column = df_var_value[column]
                single_column = single_column.reset_index(drop=True)
                single_column.to_csv(filename)

    delete_empty_subdirs(dir)


def run_postprocessing(
        year,
        name,
        data_raw,
        data_preprocessed,
        results_optimization,
        results_template,
        results_postprocessed
):
    create_postprocessed_results_subdirs(results_postprocessed)

    # load raw data
    scalars_raw = pd.read_csv(os.path.join(data_raw, 'Scalars.csv'))

    # load scalars templates
    flexmex_scalars_template = pd.read_csv(os.path.join(results_template, 'Scalars.csv'))
    flexmex_scalars_template = flexmex_scalars_template.loc[
        flexmex_scalars_template['UseCase'] == name
    ]

    # load mapping
    mapping = pd.read_csv(os.path.join(results_template, 'mapping.csv'))

    # Load preprocessed elements
    prep_elements = load_elements(os.path.join(data_preprocessed, 'data', 'elements'))

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(results_optimization)

    # format results sequences
    sequences_by_tech = get_sequences_by_tech(es.results)

    oemoflex_scalars = pd.DataFrame(
        columns=[
            'usecase',
            'region',
            'year',
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
    summed_sequences = get_summed_sequences(sequences_by_tech, prep_elements)
    oemoflex_scalars = pd.concat([oemoflex_scalars, summed_sequences], sort=True)

    # get re_generation
    re_generation = get_re_generation(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, re_generation], sort=True)

    # losses (storage, transmission)
    transmission_losses = get_transmission_losses(oemoflex_scalars)
    storage_losses = get_storage_losses(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, transmission_losses, storage_losses])

    # get capacities
    capacities = get_capacities(es)
    formatted_capacities = format_capacities(oemoflex_scalars, capacities)
    oemoflex_scalars = pd.concat([oemoflex_scalars, formatted_capacities])

    # emissions
    # emissions = get_emissions()
    # oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

    # costs
    varom_cost = get_varom_cost(oemoflex_scalars, prep_elements)
    carrier_cost = get_carrier_cost(oemoflex_scalars, prep_elements)
    fuel_cost = get_fuel_cost(carrier_cost, scalars_raw)
    emission_cost = get_emission_cost(carrier_cost, scalars_raw)
    oemoflex_scalars = pd.concat([
        oemoflex_scalars, varom_cost, carrier_cost, fuel_cost, emission_cost
    ])

    total_system_cost = get_total_system_cost(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, total_system_cost], sort=True)

    # set experiment info
    oemoflex_scalars['usecase'] = name
    oemoflex_scalars['year'] = year

    oemoflex_scalars.to_csv('~/Desktop/oemoflex_scalars.csv')
    # map to FlexMex data format
    flexmex_scalar_results = map_to_flexmex_results(
        oemoflex_scalars, flexmex_scalars_template, mapping, name
    )

    flexmex_scalar_results.to_csv(os.path.join(results_postprocessed, 'Scalars.csv'))

    save_flexmex_timeseries(
        sequences_by_tech, name, 'oemof', '2050', results_postprocessed
    )
