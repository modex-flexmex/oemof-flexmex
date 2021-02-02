import copy

import numpy as np
import pandas as pd

from oemof.solph import Bus, EnergySystem

from oemoflex.postprocessing import create_postprocessed_results_subdirs


def get_sequences(dict):

    _dict = copy.deepcopy(dict)

    seq = {key: value['sequences'] for key, value in _dict.items() if 'sequences' in value}

    return seq


def get_scalars(dict):

    _dict = copy.deepcopy(dict)

    scalars = {key: value['scalars'] for key, value in _dict.items() if 'scalars' in value}

    return scalars


def get_component_from_oemof_tuple(oemof_tuple):
    if isinstance(oemof_tuple[1], Bus):
        component = oemof_tuple[0]

    elif oemof_tuple[1] is None:
        component = oemof_tuple[0]

    elif oemof_tuple[1] is np.nan:
        component = oemof_tuple[0]

    elif isinstance(oemof_tuple[0], Bus):
        component = oemof_tuple[1]

    return component


def filter_series_by_component_attr(df, **kwargs):

    filtered_index = []
    for id in df.index:
        component = get_component_from_oemof_tuple(id[:2])

        for key, value in kwargs.items():
            if not hasattr(component, key):
                continue

            if getattr(component, key) in value:
                filtered_index.append(id)

    filtered_df = df.loc[filtered_index]

    return filtered_df


def get_inputs(series):

    input_ids = [id for id in series.index if isinstance(id[0], Bus)]

    inputs = series.loc[input_ids]

    return inputs


def get_outputs(series):

    output_ids = [id for id in series.index if isinstance(id[1], Bus)]

    outputs = series.loc[output_ids]

    return outputs


def sequences_to_df(dict):

    result = pd.concat(dict.values(), 1)

    # adapted from oemof.solph.views' node() function
    tuples = {
        key: [c for c in value.columns]
        for key, value in dict.items()
    }

    tuples = [tuple((*k, m) for m in v) for k, v in tuples.items()]

    tuples = [c for sublist in tuples for c in sublist]

    result.columns = pd.MultiIndex.from_tuples(tuples)

    return result


def scalars_to_df(dict):

    result = pd.concat(dict.values(), 0)

    if result.empty:
        return None

    # adapted from oemof.solph.views' node() function
    tuples = {
        key: [c for c in value.index]
        for key, value in dict.items()
    }

    tuples = [tuple((*k, m) for m in v) for k, v in tuples.items()]

    tuples = [c for sublist in tuples for c in sublist]

    result.index = pd.MultiIndex.from_tuples(tuples)

    return result


def sum_flows(df):

    is_flow = df.columns.get_level_values(2) == 'flow'

    df = df.loc[:, is_flow]

    df = df.sum()

    return df


def substract_output_from_input(inputs, outputs, var_name):

    def reduce_component_index(series, level):

        _series = series.copy()

        _series.name = 'var_value'

        _df = pd.DataFrame(_series)

        _df.reset_index(inplace=True)

        _df = _df[[level, 'var_value']]

        _df.set_index(level, inplace=True)

        return _df

    _inputs = reduce_component_index(inputs, 'level_1')

    _outputs = reduce_component_index(outputs, 'level_0')

    losses = _inputs - _outputs

    losses.index.name = 'level_0'

    losses.reset_index(inplace=True)

    losses['level_1'] = np.nan

    losses['level_2'] = var_name

    losses.set_index(['level_0', 'level_1', 'level_2'], inplace=True)

    losses = losses['var_value']  # Switching back to series.
    # TODO: Use DataFrame or Series more consistently.

    return losses


def get_losses(summed_flows, var_name):
    r"""


    Parameters
    ----------
    results

    Returns
    -------

    """
    inputs = get_inputs(summed_flows)

    outputs = get_outputs(summed_flows)

    losses = substract_output_from_input(inputs, outputs, var_name)

    return losses


def index_to_str(index):
    r"""
    Converts multiindex labels to string.
    """
    index = index.map(lambda tupl: tuple(str(node) for node in tupl))

    return index


def reindex_series_on_index(series, index_b):
    r"""
    Reindexes series on new index containing objects that have the same string
    representation. A workaround necessary because oemof.solph results and params
    have differences in the objects of the indices, even if their label is the same.
    """
    _index_b = index_b.copy()

    _series = series.copy()

    _index_b = index_to_str(_index_b)

    _series.index = index_to_str(_series.index)

    _series = _series.reindex(_index_b)

    _series.index = index_b

    _series = _series.loc[~_series.isna()]

    return _series


def multiply_var_with_param(var, param):
    param = reindex_series_on_index(param, var.index)

    result = param * var

    result = result.loc[~result.isna()]

    return result


def get_summed_variable_costs(summed_flows, scalar_params):

    variable_costs = (
        filter_by_var_name(scalar_params, 'variable_costs')
        .unstack(2)['variable_costs']
    )

    variable_costs = variable_costs.loc[variable_costs != 0]

    summed_flows = (
        summed_flows
        .unstack(2)
        .loc[:, 'flow']
    )

    summed_variable_costs = multiply_var_with_param(summed_flows, variable_costs)

    summed_variable_costs = set_index_level(
        summed_variable_costs,
        level='level_2',
        value='summed_variable_costs'
    )

    return summed_variable_costs


def set_index_level(series, level, value):
    r"""
    Sets a value to a multiindex level. If the level does not exist, it
    is appended.

    Parameters
    ----------
    series : pd.Series

    level : str
        Name of the level

    value : str
        Value to set

    Returns
    -------
    series : pd.Series
        Series with level set to value or appended level with value.
    """
    level_names = [f"level_{i}" for i in range(len(series.index.names))]

    series.index.names = level_names

    df = pd.DataFrame(series)

    df.reset_index(inplace=True)

    df[level] = value

    if level not in level_names:
        level_names.append(level)

    df.set_index(level_names, inplace=True)

    series = df.loc[:, 0]

    return series


def filter_by_var_name(series, var_name):

    filtered_ids = series.index.get_level_values(2) == var_name

    filtered_series = series.loc[filtered_ids]

    return filtered_series


def restore_es(path):
    r"""
    Restore EnergySystem with results
    """
    es = EnergySystem()

    es.restore(path)

    return es


def run_postprocessing_sketch(year, scenario, exp_paths):

    create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

    # restore EnergySystem with results
    es = restore_es(exp_paths.results_optimization)

    # separate scalar and sequences in results
    scalars = get_scalars(es.results)

    scalars = scalars_to_df(scalars)

    sequences = get_sequences(es.results)

    sequences = sequences_to_df(sequences)

    # separate scalars and sequences in parameters
    scalar_params = get_scalars(es.params)

    scalar_params = scalars_to_df(scalar_params)

    sequences_params = get_sequences(es.params)

    sequences_params = sequences_to_df(sequences_params)

    # Take the annual sum of the sequences
    summed_flows = sum_flows(sequences)

    # Collect the annual sum of renewable energy
    summed_flows_re = filter_series_by_component_attr(summed_flows, tech=['wind', 'solar'])

    # Calculate storage losses
    summed_flows_storage = filter_series_by_component_attr(summed_flows, type='storage')

    storage_losses = get_losses(summed_flows_storage, var_name='storage_losses')

    # Calculate transmission losses
    summed_flows_transmission = filter_series_by_component_attr(summed_flows, type='link')

    transmission_losses = get_losses(summed_flows_transmission, var_name='transmission_losses')

    # Collect existing (exogenous) capacity (units of power) and storage capacity (units of energy)
    capacity = filter_by_var_name(scalar_params, 'capacity')

    storage_capacity = filter_by_var_name(scalar_params, 'storage_capacity')

    # Collect invested (endogenous) capacity (units of power) and storage capacity (units of energy)

    invested_capacity = None

    invested_storage_capacity = None

    if not (scalars is None or scalars.empty):
        invest = filter_by_var_name(scalars, 'invest')

        target_is_none = invest.index.get_level_values(1).isnull()

        invested_capacity = invest.loc[~target_is_none]

        invested_storage_capacity = invest.loc[target_is_none]

    # Calculate summed variable costs
    summed_variable_costs = get_summed_variable_costs(summed_flows, scalar_params)

    # An oemof.tabular convention: Carrier costs are on inputs, marginal costs on output
    summed_carrier_costs = get_inputs(summed_variable_costs)

    summed_marginal_costs = get_outputs(summed_variable_costs)

    # Get flows with emissions
    carriers_with_emissions = 'ch4'

    inputs = get_inputs(summed_flows)

    flows_with_emissions = filter_series_by_component_attr(inputs, carrier=carriers_with_emissions)

    # Get emissions
    specific_emissions = 1  # TODO: Replace with real data

    summed_emissions = flows_with_emissions * specific_emissions

    summed_emissions = set_index_level(
        summed_emissions,
        level='level_2',
        value='summed_emissions'
    )

    # Get emission costs
    emission_costs = 1  # TODO: Replace this with real data

    summed_emission_costs = summed_emissions * emission_costs

    summed_emission_costs = set_index_level(
        summed_emission_costs,
        level='level_2',
        value='summed_emission_costs'
    )

    # Combine all results
    all_scalars = [
        summed_flows,
        storage_losses,
        transmission_losses,
        capacity,
        storage_capacity,
        invested_capacity,
        invested_storage_capacity,
        summed_carrier_costs,
        summed_marginal_costs,
        summed_emissions,
        summed_emission_costs,
        # total system cost,
        # total system emissions,
    ]

    all_scalars = pd.concat(all_scalars, 0)
