import os

import numpy as np
import pandas as pd

from oemof.solph import Bus, Sink
from oemof.tabular import facades
import oemof.tabular.tools.postprocessing as pp

basic_columns = ['region', 'name', 'type', 'carrier', 'tech']

POSTPROC_RES_SUBDIR_LIST = [
    'Boiler',
    'CHP/BpCCGT',
    'CHP/ExCCGT',
    'ElectricBoiler',
    'Fossil/Gasturbine',
    'Fossil/Nuclear',
    'Heatpump',
    'Hydro/Reservoir',
    'Hydro/RunOfRiver',
    'RE/Curtailment',
    'RE/Generation',
    'RE/Curtailment',
    'Storage',
    'Transmission/ImportExport',
    'Transmission/Import',
    'Transport',
]


def create_postprocessed_results_subdirs(postprocessed_results_dir):
    for subdir in POSTPROC_RES_SUBDIR_LIST:
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
    summed_sequences['var_unit'] = 'MWh'

    return summed_sequences


def get_re_generation(oemoflex_scalars):
    renewable_carriers = ['solar', 'wind']
    re_generation = pd.DataFrame(columns=oemoflex_scalars.columns)

    re_flow = oemoflex_scalars.loc[(oemoflex_scalars['carrier'].isin(renewable_carriers)) &
                                   (oemoflex_scalars['var_name'] == 'flow_out')]

    sum = re_flow.groupby('region').sum()

    re_generation['region'] = sum.index
    re_generation['carrier'] = 're'
    re_generation['type'] = 'none'
    re_generation['tech'] = 'none'
    re_generation['var_name'] = 're_generation'
    re_generation = re_generation.drop('var_value', 1)
    re_generation = pd.merge(re_generation, sum['var_value'], on='region')
    re_generation['var_unit'] = 'MWh'

    return re_generation


def get_transmission_losses():
    # oemoflex_scalars['var_name'] ==
    #  'flow_gross_forward' - oemoflex_scalars['var_name'] == 'flow_net_forward'
    pass


def get_storage_losses():
    # oemoflex_scalars['var_name'] == 'flow_in' - oemoflex_scalars['var_name'] == 'flow_out'
    pass


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

    return flexmex_scalars


def get_varom_cost(oemoflex_scalars, prep_elements):
    varom_cost = []
    for component, prep_el in prep_elements.items():
        if 'marginal_cost' in prep_el.columns:
            df = prep_el[basic_columns]
            if prep_el['type'][0] == 'excess':
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_in']
            elif prep_el['type'][0] in ['backpressure', 'extraction']:
                flow = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'flow_electricity']
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
    for component, prep_el in prep_elements.items():
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
            df['var_value'] = df['var_value'] * prep_el['marginal_cost']
            df['var_name'] = 'cost_carrier'

            carrier_cost.append(df)

    if carrier_cost:
        carrier_cost = pd.concat(carrier_cost, sort=True)
    else:
        carrier_cost = pd.DataFrame(carrier_cost)

        carrier_cost['var_unit'] = 'Eur'

    return carrier_cost


def get_capacity_cost():
    # TODO: Problem there is no distinction btw fixom and invest cost!
    # capacities * prep_elements[capacity_cost]
    pass


def get_total_system_cost(oemoflex_scalars):
    cost_list = ['cost_varom', 'cost_fuel', 'cost_capacity']
    df = oemoflex_scalars.loc[oemoflex_scalars['var_name'].isin(cost_list)]
    total_system_cost = pd.DataFrame(columns=oemoflex_scalars.columns)
    total_system_cost.loc[0, 'var_name'] = 'total_system_cost'
    total_system_cost.loc[0, 'var_value'] = df['var_value'].sum()
    total_system_cost['carrier'] = 'ALL'
    total_system_cost['tech'] = 'ALL'
    total_system_cost['region'] = 'ALL'
    total_system_cost['var_unit'] = 'Eur'

    return total_system_cost
