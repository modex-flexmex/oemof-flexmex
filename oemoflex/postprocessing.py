import os
import logging
import copy

import numpy as np
import pandas as pd

from oemof.solph import Bus, Sink, Source
import oemof.tabular.tools.postprocessing as pp

from oemoflex.parametrization_scalars import get_parameter_values

from oemoflex.facades import TYPEMAP


basic_columns = ['region', 'name', 'type', 'carrier', 'tech']


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

    def get_facade_attr(attr):
        # Function constructor for getting a specific property from
        # the Facade object in bus_results() DataFrame columns "from" or "to"
        def fnc(flow):
            # Get property from the Storage object in "from" for the discharge device
            if isinstance(flow['from'], (TYPEMAP["storage"],
                                         TYPEMAP["asymmetric storage"])):
                return getattr(flow['from'], attr, np.nan)

            # Get property from the Storage object in "to" for the charge device
            if isinstance(flow['to'], (TYPEMAP["storage"],
                                       TYPEMAP["asymmetric storage"])):
                return getattr(flow['to'], attr, np.nan)

            # Get property from other object in "from"
            return getattr(flow['from'], attr, np.nan)

        return fnc

    def get_parameter_name(flow):
        if isinstance(flow['from'], (TYPEMAP["storage"],
                                     TYPEMAP["asymmetric storage"])):
            return "capacity_discharge_invest"

        if isinstance(flow['to'], (TYPEMAP["storage"],
                                   TYPEMAP["asymmetric storage"])):
            return "capacity_charge_invest"

        return np.nan

    try:
        flows = pp.bus_results(es, es.results, select="scalars", concat=True)

        flows.name = "var_value"

        endogenous = flows.reset_index()

        # Results already contain a column named "type". Call this "var_name" to
        # preserve its content ("invest" for now)
        endogenous.rename(columns={"type": "var_name"}, inplace=True)

        # Update "var_name" with Storage specific parameter names for charge and discharge devices
        df = pd.DataFrame({'var_name': endogenous.apply(get_parameter_name, axis=1)})
        endogenous.update(df)

        endogenous["region"] = endogenous.apply(get_facade_attr('region'), axis=1)
        endogenous["name"] = endogenous.apply(get_facade_attr('label'), axis=1)
        endogenous["type"] = endogenous.apply(get_facade_attr('type'), axis=1)
        endogenous["carrier"] = endogenous.apply(get_facade_attr('carrier'), axis=1)
        endogenous["tech"] = endogenous.apply(get_facade_attr('tech'), axis=1)

        endogenous.drop(['from', 'to'], axis=1, inplace=True)

        endogenous.set_index(
            ["region", "name", "type", "carrier", "tech", "var_name"], inplace=True
        )

    except ValueError:
        endogenous = pd.DataFrame()

    d = dict()
    for node in es.nodes:
        if not isinstance(node, (Bus, Sink, TYPEMAP["shortage"], TYPEMAP["link"])):
            # Specify which parameters to read depending on the technology
            parameters_to_read = []
            if isinstance(node, TYPEMAP["storage"]):

                # TODO for brownfield optimization
                # parameters_to_read = ['capacity', 'storage_capacity']

                # WORKAROUND Skip 'capacity' to safe some effort in aggregation and elsewhere
                # possible because storages are greenfield optimized only: 'capacity' = 0
                parameters_to_read = ['storage_capacity']

            elif isinstance(node, TYPEMAP["asymmetric storage"]):
                parameters_to_read = ['capacity_charge', 'capacity_discharge', 'storage_capacity']
            elif getattr(node, "capacity", None) is not None:
                parameters_to_read = ['capacity']

            # Update dict with values in oemof's parameter->value structure
            for p in parameters_to_read:
                key = (
                    node.region,
                    node.label,
                    # [n for n in node.outputs.keys()][0],
                    node.type,
                    node.carrier,
                    node.tech,  # tech & carrier are oemof-tabular specific
                    p
                )  # for oemof logic
                d[key] = {'var_value': getattr(node, p)}

    exogenous = pd.DataFrame.from_dict(d).T  # .dropna()

    if not exogenous.empty:
        exogenous.index = exogenous.index.set_names(
            ['region', 'name', 'type', 'carrier', 'tech', 'var_name']
        )

    # Read storage capacities (from oemof.heat)
    # only component_results() knows about 'storage_capacity'
    try:
        components = pd.concat(pp.component_results(es, es.results, select='scalars'))
        components.name = 'var_value'

        storage = components.reset_index()

        storage.drop('level_0', 1, inplace=True)

        storage.columns = ['name', 'to', 'var_name', 'var_value']
        storage['region'] = [
            getattr(t, "region", np.nan) for t in components.index.get_level_values('from')
        ]
        storage['type'] = [
            getattr(t, "type", np.nan) for t in components.index.get_level_values('from')
        ]
        storage['carrier'] = [
            getattr(t, "carrier", np.nan) for t in components.index.get_level_values('from')
        ]
        storage['tech'] = [
            getattr(t, "tech", np.nan) for t in components.index.get_level_values('from')
        ]
        storage = storage.loc[storage['to'].isna()]
        storage.drop('to', 1, inplace=True)
        storage = storage[['region', 'name', 'type', 'carrier', 'tech', 'var_name', 'var_value']]

        # Delete unused 'init_cap' rows - parameter name misleading! (oemof issue)
        storage.drop(storage.loc[storage['var_name'] == 'init_cap'].index, axis=0, inplace=True)

        storage.replace(
            ['invest'],
            ['storage_capacity_invest'],
            inplace=True
        )
        storage.set_index(
            ['region', "name", "type", "carrier", "tech", "var_name"], inplace=True
        )

    except ValueError:
        storage = pd.DataFrame()

    capacities = pd.concat([endogenous, exogenous, storage])

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
    # copy to avoid manipulating the data in es.results
    sequences = copy.deepcopy({key: value['sequences'] for key, value in results.items()})

    sequences_by_tech = []

    # Get internal busses for all 'ReservoirWithPump' and 'Bev' nodes to be ignored later
    internal_busses = get_subnodes_by_type(sequences, Bus)

    # Get inflows for all 'ReservoirWithPump' nodes
    reservoir_inflows = get_subnodes_by_type(sequences, Source)

    for key, df in sequences.items():
        if isinstance(key[0], Bus):
            component = key[1]
            bus = key[0]

            if isinstance(component, TYPEMAP["link"]):
                if bus == component.from_bus:
                    var_name = 'flow_gross_forward'
                elif bus == component.to_bus:
                    var_name = 'flow_gross_backward'

            elif isinstance(component, (TYPEMAP["extraction"], TYPEMAP["backpressure"])):
                var_name = 'flow_fuel'

            else:
                var_name = 'flow_in'

        if isinstance(key[1], Bus):
            bus = key[1]
            component = key[0]

            if isinstance(component, TYPEMAP["link"]):
                if bus == component.to_bus:
                    var_name = 'flow_net_forward'
                elif bus == component.from_bus:
                    var_name = 'flow_net_backward'

            elif isinstance(component, (TYPEMAP["extraction"], TYPEMAP["backpressure"])):
                if bus == component.electricity_bus:
                    var_name = 'flow_electricity'

                elif bus == component.heat_bus:
                    var_name = 'flow_heat'

            elif component in reservoir_inflows:
                var_name = 'flow_inflow'

            else:
                var_name = 'flow_out'

        if key[1] is None:
            component = key[0]
            var_name = 'storage_content'

        # Ignore sequences FROM internal busses (concerns ReservoirWithPump, Bev)
        if bus in internal_busses and component not in reservoir_inflows:
            continue

        carrier_tech = component.carrier + '-' + component.tech

        if isinstance(component, TYPEMAP["link"]):
            # Replace AT-DE by AT_DE to be ready to be merged with DataFrames from preprocessing
            region = component.label.replace('-', '_')
        else:
            # Take AT from AT-ch4-gt, string op since sub-nodes lack of a 'region' attribute
            region = component.label.split('-')[0]

        df.columns = pd.MultiIndex.from_tuples([(region, carrier_tech, var_name)])
        df.columns.names = ['region', 'carrier_tech', 'var_name']
        sequences_by_tech.append(df)

    sequences_by_tech = pd.concat(sequences_by_tech, axis=1)

    return sequences_by_tech


def get_subnodes_by_type(sequences, cls):
    r"""
    Get all the subnodes of type 'cls' in the <to> nodes of 'sequences'

    Parameters
    ----------
    sequences : dict (special format, see get_sequences_by_tech() and before)
        key: tuple of 'to' node and 'from' node: (from, to)
        value: timeseries DataFrame

    cls : Class
        Class to check against

    Returns
    -------
    A list of all subnodes of type 'cls'
    """

    # Get a list of all the components
    to_nodes = []
    for k in sequences.keys():
        # It's sufficient to look into one side of the flows ('to' node, k[1])
        to_nodes.append(k[1])

    subnodes_list = []
    for component in to_nodes:
        if hasattr(component, 'subnodes'):
            # Only get subnodes of type 'cls'
            subnodes_per_component = [n for n in component.subnodes if isinstance(n, cls)]
            subnodes_list.extend(subnodes_per_component)

    return subnodes_list


def get_summed_sequences(sequences_by_tech, prep_elements):
    # Put component definitions into one DataFrame - drops 'carrier_tech' information in the keys
    base = pd.concat(prep_elements.values())
    df = base.loc[:, basic_columns]
    sum = sequences_by_tech.sum()
    sum.name = 'var_value'
    sum_df = sum.reset_index()
    # Form helper column for proper merging with component definition
    df['carrier_tech'] = df['carrier'] + '-' + df['tech']
    summed_sequences = pd.merge(df, sum_df, on=['region', 'carrier_tech'])
    # Drop helper column
    summed_sequences.drop('carrier_tech', axis=1, inplace=True)

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
    storage_data = oemoflex_scalars.loc[
        oemoflex_scalars['type'].isin(['storage', 'asymmetric storage'])
    ]
    flow_in = storage_data.loc[storage_data['var_name'] == 'flow_in'].set_index('name')
    flow_out = storage_data.loc[storage_data['var_name'] == 'flow_out'].set_index('name')

    losses = flow_in.copy()
    losses['var_name'] = 'loss'
    losses['var_value'] = flow_in['var_value'] - flow_out['var_value']
    losses = losses.reset_index()

    return losses


def get_reservoir_losses(oemoflex_scalars):
    reservoir_data = oemoflex_scalars.loc[
        oemoflex_scalars['type'].isin(['reservoir'])
    ]
    flow_in = reservoir_data.loc[reservoir_data['var_name'] == 'flow_in'].set_index('name')
    flow_out = reservoir_data.loc[reservoir_data['var_name'] == 'flow_out'].set_index('name')
    flow_inflow = reservoir_data.loc[reservoir_data['var_name'] == 'flow_inflow'].set_index('name')

    losses = flow_in.copy()
    losses['var_name'] = 'losses'
    losses['var_value'] = flow_inflow['var_value'] - (flow_out['var_value'] - flow_in['var_value'])
    losses = losses.reset_index()

    return losses


def aggregate_storage_capacities(oemoflex_scalars):
    storage = oemoflex_scalars.loc[
        oemoflex_scalars['var_name'].isin(['storage_capacity', 'storage_capacity_invest'])].copy()

    # Make sure that values in columns used to group on are strings and thus equatable
    storage[basic_columns] = storage[basic_columns].astype(str)

    storage = storage.groupby(by=basic_columns, as_index=False).sum()
    storage['var_name'] = 'storage_capacity_sum'
    storage['var_value'] = storage['var_value'] * 1e-3  # MWh -> GWh
    storage['var_unit'] = 'GWh'

    charge = oemoflex_scalars.loc[
        oemoflex_scalars['var_name'].isin(['capacity_charge', 'capacity_charge_invest'])]
    charge = charge.groupby(by=basic_columns, as_index=False).sum()
    charge['var_name'] = 'capacity_charge_sum'
    charge['var_unit'] = 'MW'

    discharge = oemoflex_scalars.loc[
        oemoflex_scalars['var_name'].isin(['capacity_discharge', 'capacity_discharge_invest'])]
    discharge = discharge.groupby(by=basic_columns, as_index=False).sum()
    discharge['var_name'] = 'capacity_discharge_sum'
    discharge['var_unit'] = 'MW'

    return pd.concat([storage, charge, discharge])


def aggregate_other_capacities(oemoflex_scalars):
    capacities = oemoflex_scalars.loc[
        oemoflex_scalars['var_name'].isin(['capacity', 'invest'])
        ].copy()

    # Make sure that values in columns used to group on are strings and thus equatable
    capacities[basic_columns] = capacities[basic_columns].astype(str)

    capacities = capacities.groupby(by=basic_columns, as_index=False).sum()
    capacities['var_name'] = 'capacity_sum'
    capacities['var_unit'] = 'MW'

    return capacities


def get_emissions(oemoflex_scalars, scalars_raw):
    try:
        emissions = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'cost_emission'].copy()
    except KeyError:
        logging.info("No key 'cost_emissions' found to calculate 'emissions'.")
        return None

    price_emission = get_parameter_values(scalars_raw, 'Energy_Price_CO2')

    emissions['var_value'] *= 1/price_emission

    emissions['var_name'] = 'emissions'

    emissions['var_unit'] = 'tCO2'

    return emissions


def map_link_direction(oemoflex_scalars):
    r"""Swaps name and region for backward flows of links."""
    backward = (
        (oemoflex_scalars['type'] == 'link') &
        (oemoflex_scalars['var_name'].str.contains('backward'))
    )

    def swap(series, delimiter):
        return series.str.split(delimiter).apply(lambda x: delimiter.join(x[::-1]))

    def drop_regex(series, regex):
        return series.str.replace(regex, '', regex=True)

    oemoflex_scalars.loc[backward, 'name'] = swap(oemoflex_scalars.loc[backward, 'name'], '-')
    oemoflex_scalars.loc[backward, 'region'] = swap(oemoflex_scalars.loc[backward, 'region'], '_')

    oemoflex_scalars.loc[:, 'var_name'] = drop_regex(
        oemoflex_scalars.loc[:, 'var_name'], '.backward|.forward'
    )

    return oemoflex_scalars


def get_varom_cost(oemoflex_scalars, prep_elements):
    r"""
    Calculates the VarOM cost by multiplying consumption by marginal cost.

    Which value is taken as consumption depends on the actual technology type.

    Parameters
    ----------
    oemoflex_scalars
    prep_elements

    Returns
    -------

    """
    varom_cost = []
    for prep_el in prep_elements.values():
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

    varom_cost = pd.concat(varom_cost)
    varom_cost['var_unit'] = 'Eur'

    return varom_cost


def get_carrier_cost(oemoflex_scalars, prep_elements):
    carrier_cost = []
    for prep_el in prep_elements.values():
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
        carrier_cost = pd.concat(carrier_cost)
    else:
        carrier_cost = pd.DataFrame(carrier_cost)

    carrier_cost['var_unit'] = 'Eur'

    return carrier_cost


def aggregate_by_country(df):
    if not df.empty:
        aggregated = df.groupby(['region', 'var_name', 'var_unit']).sum()

        aggregated['name'] = 'energysystem'
        aggregated['carrier'] = 'ALL'
        aggregated['tech'] = 'ALL'
        aggregated['type'] = 'ALL'

        aggregated = aggregated.reset_index()

        return aggregated

    return None


def get_total_system_cost(oemoflex_scalars):
    cost_list = ['cost_varom', 'cost_fuel', 'cost_invest', 'cost_emission']
    df = oemoflex_scalars.loc[oemoflex_scalars['var_name'].isin(cost_list)]
    total_system_cost = pd.DataFrame(columns=oemoflex_scalars.columns)
    total_system_cost.loc[0, 'var_name'] = 'total_system_cost'
    total_system_cost.loc[0, 'var_value'] = df['var_value'].sum()
    total_system_cost['carrier'] = 'ALL'
    total_system_cost['tech'] = 'ALL'
    total_system_cost['region'] = 'ALL'
    total_system_cost['var_unit'] = 'Eur'

    return total_system_cost


def sum_transmission_flows(sequences_by_tech):

    idx = pd.IndexSlice

    try:
        flow_net_fw = sequences_by_tech. \
            loc[:, idx[:, 'electricity-transmission', 'flow_net_forward']]

        flow_net_bw = sequences_by_tech. \
            loc[:, idx[:, 'electricity-transmission', 'flow_net_backward']]

    except KeyError:
        return None

    flow_net_fw = flow_net_fw.rename(columns={'flow_net_forward': 'flow_net_sum'})

    flow_net_bw = flow_net_bw.rename(columns={'flow_net_backward': 'flow_net_sum'})

    flow_net_sum = flow_net_fw - flow_net_bw

    return flow_net_sum


def aggregate_re_generation_timeseries(sequences_by_tech):

    idx = pd.IndexSlice

    # Sum flow_out sequences from renewable energies
    renewable_techs = ['wind-offshore', 'wind-onshore', 'solar-pv']
    df_renewable = sequences_by_tech.loc[:, idx[:, renewable_techs, 'flow_out']]
    df_renewable_sum = df_renewable.groupby(['region'], axis=1).sum()
    df_renewable_sum.columns = pd.MultiIndex.from_product(
        [list(df_renewable_sum.columns), ['energysystem'], ['re_generation']],
        names=['region', 'carrier_tech', 'var_name']
    )

    # Substract Curtailment
    df_curtailment = sequences_by_tech.loc[:, (slice(None), 'electricity-curtailment')]
    df_curtailment.columns = df_renewable_sum.columns
    df_re_generation = df_renewable_sum.sub(df_curtailment, axis=0)

    return df_re_generation


def export_bus_sequences(es, destination):

    if not os.path.exists(destination):
        os.mkdir(destination)

    bus_results = pp.bus_results(es, es.results)

    for key, value in bus_results.items():
        if value.empty:
            continue

        file_path = os.path.join(destination, key + '.csv')

        value.to_csv(file_path)
