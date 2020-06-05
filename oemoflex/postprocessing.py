import os
import logging
import copy

import numpy as np
import pandas as pd
import yaml

from oemof.solph import EnergySystem, Bus, Sink
from oemof.tabular import facades
import oemof.tabular.tools.postprocessing as pp
from oemof.tools.economics import annuity
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
        all = pp.bus_results(es, es.results, select="scalars", concat=True)

        all.name = "var_value"

        endogenous = all.reset_index()

        endogenous.drop(['from', 'to'], axis=1, inplace=True)

        endogenous["region"] = [
            getattr(t, "region", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["name"] = [
            getattr(t, "label", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["type"] = [
            getattr(t, "type", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["carrier"] = [
            getattr(t, "carrier", np.nan)
            for t in all.index.get_level_values(0)
        ]
        endogenous["tech"] = [
            getattr(t, "tech", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["var_name"] = "invest"
        endogenous.set_index(
            ["region", "name", "type", "carrier", "tech", "var_name"], inplace=True
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
    # copy to avoid manipulating the data in es.results
    sequences = copy.deepcopy({key: value['sequences'] for key, value in results.items()})

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

    # parameter_names = {'Energy_Price_CH4': 'Energy_EmissionFactor_CH4',
    #                    'Energy_Price_Uranium': None}
    #
    # for carrier_price, emission_factor in parameter_names

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


def get_invest_cost(oemoflex_scalars, prep_elements, scalars_raw):

    invest_cost = pd.DataFrame()
    parameters = dict()

    for _, prep_el in prep_elements.items():
        if 'expandable' in prep_el.columns and prep_el['expandable'][0] == True:  # not 'is'! pandas overloads operators!
            # element is expandable --> 'invest' values exist
            df = prep_el[basic_columns]

            try:
                capacities_invested = oemoflex_scalars.loc[
                    oemoflex_scalars['var_name'] == 'invest'].copy()
            except KeyError:
                logging.info("No key 'invest' found to calculate 'cost_invest'.")
                return None

            df = pd.merge(
                df, capacities_invested,
                on=basic_columns
            )

            # TODO This part could be easily modularized and reused (for preprocessing as well)
            # TODO sugg: FlexMex_parameter_mapping(technology)
            if prep_el['tech'][0] == 'gt':
                parameters = {'capex': 'EnergyConversion_Capex_Electricity_CH4_GT',
                              'lifetime': 'EnergyConversion_LifeTime_Electricity_CH4_GT'}
            elif prep_el['tech'][0] == 'nuclear-st':
                parameters = {'capex': 'EnergyConversion_Capex_Electricity_Nuclear_ST',
                              'lifetime': 'EnergyConversion_LifeTime_Electricity_Nuclear_ST'}

            capex = get_parameter_values(scalars_raw, parameters['capex'])

            lifetime = get_parameter_values(scalars_raw, parameters['lifetime'])

            interest = get_parameter_values(
                scalars_raw,
                'EnergyConversion_InterestRate_ALL') * 1e-2  # percent -> 0...1

            annualized_cost = annuity(capex=capex, n=lifetime, wacc=interest)

            df['var_value'] = df['var_value'] * annualized_cost

            df['var_name'] = 'cost_invest'
            df['var_unit'] = 'Eur'

            invest_cost = pd.concat([invest_cost, df], sort=True)

    return invest_cost


def get_fixom_cost(oemoflex_scalars, scalars_raw):

    try:
        capacities_invested = oemoflex_scalars.loc[oemoflex_scalars['var_name'] == 'invest'].copy()
    except KeyError:
        logging.info("No key 'invest' found to calculate 'capacity_cost'.")
        return None

    capacities_invested['var_name'] = 'cost_fixom'

    capex = get_parameter_values(
        scalars_raw,
        'EnergyConversion_Capex_Electricity_CH4_GT')

    fix_cost = get_parameter_values(
        scalars_raw,
        'EnergyConversion_FixOM_Electricity_CH4_GT') * 1e-2  # percent -> 0...1

    capacities_invested['var_value'] *= fix_cost * capex

    return capacities_invested


def aggregate_by_country(df):
    if df is not None:
        aggregated = df.groupby(['region', 'var_name', 'var_unit']).sum()

        aggregated['name'] = 'energysystem'
        aggregated['carrier'] = 'ALL'
        aggregated['tech'] = 'ALL'
        aggregated['type'] = 'ALL'

        aggregated = aggregated.reset_index()

        return aggregated

    return None


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


def run_postprocessing(year, name, exp_paths):
    create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

    # load raw data
    scalars_raw = pd.read_csv(os.path.join(exp_paths.data_raw, 'Scalars.csv'), sep=';')

    # load scalars templates
    flexmex_scalars_template = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
    flexmex_scalars_template = flexmex_scalars_template.loc[
        flexmex_scalars_template['UseCase'] == name
    ]

    # load mapping
    mapping = pd.read_csv(os.path.join(exp_paths.results_mapping, 'mapping.csv'))

    # Load preprocessed elements
    prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(exp_paths.results_optimization)

    # format results sequences
    sequences_by_tech = get_sequences_by_tech(es.results)

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

    # costs
    varom_cost = get_varom_cost(oemoflex_scalars, prep_elements)
    carrier_cost = get_carrier_cost(oemoflex_scalars, prep_elements)
    fuel_cost = get_fuel_cost(carrier_cost, scalars_raw)
    emission_cost = get_emission_cost(carrier_cost, scalars_raw)
    aggregated_emission_cost = aggregate_by_country(emission_cost)
    invest_cost = get_invest_cost(oemoflex_scalars, prep_elements, scalars_raw)
    fixom_cost = get_fixom_cost(oemoflex_scalars, scalars_raw)
    oemoflex_scalars = pd.concat([
        oemoflex_scalars, varom_cost, carrier_cost, fuel_cost, aggregated_emission_cost,
        invest_cost, fixom_cost
    ])

    # emissions
    emissions = get_emissions(oemoflex_scalars, scalars_raw)
    oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

    total_system_cost = get_total_system_cost(oemoflex_scalars)
    oemoflex_scalars = pd.concat([oemoflex_scalars, total_system_cost], sort=True)

    # map direction of links
    oemoflex_scalars = map_link_direction(oemoflex_scalars)

    # set experiment info
    oemoflex_scalars['usecase'] = name
    oemoflex_scalars['year'] = year

    # map to FlexMex data format
    flexmex_scalar_results = map_to_flexmex_results(
        oemoflex_scalars, flexmex_scalars_template, mapping, name
    )

    # save results
    flexmex_scalar_results.to_csv(
        os.path.join(exp_paths.results_postprocessed, 'Scalars.csv'),
        index=False
    )

    save_oemoflex_scalars = False
    if save_oemoflex_scalars:
        oemoflex_scalars.to_csv(
            os.path.join(exp_paths.results_postprocessed, 'oemoflex_scalars.csv'),
            index=False
        )

    save_flexmex_timeseries(
        sequences_by_tech, name, 'oemof', '2050', exp_paths.results_postprocessed
    )
