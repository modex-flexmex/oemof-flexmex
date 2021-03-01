import os
import logging
import copy

import numpy as np
import pandas as pd

from oemof.solph import EnergySystem, Bus, Sink, Source
import oemof.tabular.tools.postprocessing as pp
from oemof.tools.economics import annuity
from oemoflex.helpers import delete_empty_subdirs, load_elements, load_scalar_input_data, load_yaml
from oemoflex.parametrization_scalars import get_parameter_values

from oemoflex.facades import TYPEMAP


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


def create_postprocessed_results_subdirs(postprocessed_results_dir):
    for parameters in map_output_timeseries.values():
        for subdir in parameters.values():
            path = os.path.join(postprocessed_results_dir, subdir)
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


def map_to_flexmex_results(oemoflex_scalars, flexmex_scalars_template, mapping, scenario):
    mapping = mapping.set_index('Parameter')
    flexmex_scalars = flexmex_scalars_template.copy()
    oemoflex_scalars = oemoflex_scalars.set_index(['region', 'carrier', 'tech', 'var_name'])
    oemoflex_scalars.loc[oemoflex_scalars['var_unit'] == 'MWh', 'var_value'] *= 1e-3  # MWh to GWh

    for i, row in flexmex_scalars.loc[flexmex_scalars['UseCase'] == scenario].iterrows():
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
            logging.info(
                f"No key "
                f"{(row['Region'], select['carrier'], select['tech'], select['var_name'])}"
                f"found to be mapped to FlexMex."
            )

            continue

        if isinstance(value, float):
            flexmex_scalars.loc[i, 'Value'] = np.around(value)

    flexmex_scalars.loc[:, 'Modell'] = 'oemof'

    return flexmex_scalars


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
        logging.info("No key '{}' found as input"
                     "for postprocessing calculation.".format(parameter_name))

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


def save_flexmex_timeseries(sequences_by_tech, scenario, model, year, dir):

    for carrier_tech in sequences_by_tech.columns.unique(level='carrier_tech'):
        try:
            components_paths = map_output_timeseries[carrier_tech]
        except KeyError:
            logging.info(f"No entry found in {path_map_output_timeseries} for '{carrier_tech}'.")
            continue

        idx = pd.IndexSlice
        for var_name, subdir in components_paths.items():
            df_var_value = sequences_by_tech.loc[:, idx[:, carrier_tech, var_name]]
            for region in df_var_value.columns.get_level_values('region'):
                filename = os.path.join(
                    dir,
                    subdir,
                    '_'.join([scenario, model, region, year]) + '.csv'
                )

                single_column = df_var_value.loc[:, region]
                single_column = single_column.reset_index(drop=True)
                single_column.columns = single_column.columns.droplevel('carrier_tech')
                remaining_column_name = list(single_column)[0]
                single_column.rename(columns={remaining_column_name: 'value'}, inplace=True)
                single_column.index.name = 'timeindex'
                single_column.to_csv(filename, header=True)

    delete_empty_subdirs(dir)


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


def aggregate_heat(oemoflex_scalars):
    print(oemoflex_scalars)

    oemoflex_scalars.set_index(['region', 'name', 'type', 'carrier', 'tech'])

    aggregated = (
        oemoflex_scalars
        .loc[
            (
                oemoflex_scalars['carrier'].isin(['heat_central', 'heat_decentral']) &
                oemoflex_scalars['tech'].isin(['excess', 'shortage'])

            )
        ]
        .loc[:, ['region', 'type', 'tech', 'var_name', 'var_value', 'var_unit']]
        .groupby(['region', 'type', 'tech', 'var_name', 'var_unit'])
        .sum()
        .reset_index()
    )

    aggregated['carrier'] = 'heat'

    aggregated['name'] = aggregated\
        .apply(lambda x: '-'.join(x[['region', 'carrier', 'tech']]), 1)

    oemoflex_scalars = pd.concat([oemoflex_scalars, aggregated])

    return oemoflex_scalars


def export_bus_sequences(es, destination):

    if not os.path.exists(destination):
        os.mkdir(destination)

    bus_results = pp.bus_results(es, es.results)

    for key, value in bus_results.items():
        if value.empty:
            continue

        file_path = os.path.join(destination, key + '.csv')

        value.to_csv(file_path)


def run_postprocessing(scenario_specs, exp_paths):
    create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

    # load raw data
    scalars_raw = load_scalar_input_data(scenario_specs, exp_paths)

    # load scalars templates
    exp, case = scenario_specs['scenario'].split('_')

    if exp == 'FlexMex1':
        flexmex_scalars_template = pd.read_csv(
            os.path.join(exp_paths.results_template, 'Scalars_FlexMex1.csv')
        )

    elif exp == 'FlexMex2':
        flexmex_scalars_template = pd.read_csv(
            os.path.join(exp_paths.results_template, 'Scalars_FlexMex2.csv')
        )

    flexmex_scalars_template = flexmex_scalars_template.loc[
        flexmex_scalars_template['UseCase'] == scenario_specs['scenario']
    ]

    # load mapping
    mapping = pd.read_csv(os.path.join(path_mappings, 'mapping-output-scalars.csv'))

    # Load preprocessed elements
    prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(exp_paths.results_optimization)

    # format results sequences
    sequences_by_tech = get_sequences_by_tech(es.results)

    flow_net_sum = sum_transmission_flows(sequences_by_tech)

    sequences_by_tech = pd.concat([sequences_by_tech, flow_net_sum], axis=1)

    df_re_generation = aggregate_re_generation_timeseries(sequences_by_tech)

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
    summed_sequences = get_summed_sequences(sequences_by_tech, prep_elements)
    oemoflex_scalars = pd.concat([oemoflex_scalars, summed_sequences])

    # get re_generation
    re_generation = get_re_generation(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, re_generation])

    # losses (storage, transmission)
    transmission_losses = get_transmission_losses(oemoflex_scalars)
    storage_losses = get_storage_losses(oemoflex_scalars)
    reservoir_losses = get_reservoir_losses(oemoflex_scalars)
    oemoflex_scalars = pd.concat([
        oemoflex_scalars,
        transmission_losses,
        storage_losses,
        reservoir_losses
    ])

    # get capacities
    capacities = get_capacities(es)
    formatted_capacities = format_capacities(oemoflex_scalars, capacities)
    oemoflex_scalars = pd.concat([oemoflex_scalars, formatted_capacities])

    # costs
    varom_cost = get_varom_cost(oemoflex_scalars, prep_elements)
    carrier_cost = get_carrier_cost(oemoflex_scalars, prep_elements)
    fuel_cost = get_fuel_cost(carrier_cost, prep_elements, scalars_raw)
    emission_cost = get_emission_cost(carrier_cost, prep_elements, scalars_raw)
    aggregated_emission_cost = aggregate_by_country(emission_cost)
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
    emissions = get_emissions(oemoflex_scalars, scalars_raw)
    oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

    storage = aggregate_storage_capacities(oemoflex_scalars)
    other = aggregate_other_capacities(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, storage, other])

    total_system_cost = get_total_system_cost(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, total_system_cost])

    # map direction of links
    oemoflex_scalars = map_link_direction(oemoflex_scalars)

    # sum heat shortage and excess
    oemoflex_scalars = aggregate_heat(oemoflex_scalars)

    # set experiment info
    oemoflex_scalars['usecase'] = scenario_specs['scenario']
    oemoflex_scalars['year'] = scenario_specs['year']

    # oemoflex_scalars.to_csv('~/Desktop/oemoflex_scalars.csv')

    # map to FlexMex data format
    flexmex_scalar_results = map_to_flexmex_results(
        oemoflex_scalars, flexmex_scalars_template, mapping, scenario_specs['scenario']
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
        export_bus_sequences(
            es,
            os.path.join(exp_paths.results_postprocessed, 'oemoflex-timeseries')
        )

    save_flexmex_timeseries(
        sequences_by_tech, scenario_specs['scenario'], 'oemof', '2050',
        exp_paths.results_postprocessed
    )
