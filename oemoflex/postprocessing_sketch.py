import copy

import numpy as np
import pandas as pd

from oemof.solph import Bus, EnergySystem
from oemof.outputlib import processing

from oemoflex.postprocessing import create_postprocessed_results_subdirs


def get_flow_from_oemof_tuple(oemof_tuple):
    r"""
    Returns the flow object for a given oemof tuple.

    Parameters
    ----------
    oemof_tuple : tuple
        Tuple of type (bus, component, xx)

    Returns
    -------
    flow : oemof.solph.Flow
        Flow object corresponding to the tuple
    """
    if isinstance(oemof_tuple[0], Bus):
        component = oemof_tuple[1]
        bus = oemof_tuple[0]

    elif isinstance(oemof_tuple[1], Bus):
        component = oemof_tuple[0]
        bus = oemof_tuple[1]

    else:
        return None

    flow = component.outputs[bus]

    return flow


def select_from_dict(dict, name):
    r"""
    Returns
    Parameters
    ----------
    dict
    name

    Returns
    -------

    """
    def has_var_name(v, name):
        return (name in v['scalars'].index) or (name in v['sequences'].columns)

    def get_var_value(v, name):
        if name in v['scalars'].index:
            return v['scalars'][name]
        elif name in v['sequences'].columns:
            return v['sequences'][name]

    selected_param_dict = copy.deepcopy(
        {
            k: get_var_value(v, name)
            for k, v in dict.items()
            if has_var_name(v, name)
         }
    )

    return selected_param_dict


def multiply_param_with_variable(params, results, param_name, var_name):
    def get_label(k):
        if isinstance(k, tuple):
            return tuple(map(str, k))
        return str(k)

    parameter = select_from_dict(params, param_name)

    variable = select_from_dict(results, var_name)

    intersection = (
        processing.convert_keys_to_strings(parameter).keys()
        & processing.convert_keys_to_strings(variable).keys()
    )

    product = {}
    for k, var in variable.items():
        if get_label(k) in intersection:
            par = processing.convert_keys_to_strings(parameter)[get_label(k)]

            if isinstance(par, pd.Series):
                par.index = var.index

            prod = var * par
            product.update({k: prod})

    return product


def get_sequences(dict):

    _dict = copy.deepcopy(dict)

    seq = {key: value['sequences'] for key, value in _dict.items() if 'sequences' in value}

    return seq


def get_scalars(dict):

    _dict = copy.deepcopy(dict)

    scalars = {key: value['scalars'] for key, value in _dict.items() if 'scalars' in value}

    return scalars


def sum_sequences(sequences):

    _sequences = copy.deepcopy(sequences)

    for oemof_tuple, value in _sequences.items():

        _sequences[oemof_tuple] = value.sum()

    return _sequences


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


def filter_components_by_attr(sequences, **kwargs):

    filtered_seqs = {}

    for oemof_tuple, data in sequences.items():
        component = get_component_from_oemof_tuple(oemof_tuple)

        for key, value in kwargs.items():
            if not hasattr(component, key):
                continue

            if getattr(component, key) in value:
                filtered_seqs[oemof_tuple] = data

    return filtered_seqs


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


def sum_sequences_df(df):
    df = df.sum()

    return df


def substract_output_from_input(inputs, outputs):

    def reduce_component_index(series, level):

        _series = series.copy()

        _series.name = 'var_value'

        _series = pd.DataFrame(_series)

        _series.reset_index(inplace=True)

        _series = _series[[level, 'var_value']]

        _series.set_index(level, inplace=True)

        return _series

    _inputs = reduce_component_index(inputs, 'level_1')

    _outputs = reduce_component_index(outputs, 'level_0')

    losses = _inputs - _outputs

    losses.index.name = 'level_0'

    losses.reset_index(inplace=True)

    losses['level_1'] = np.nan

    losses['level_2'] = 'losses'

    losses.set_index(['level_0', 'level_1', 'level_2'], inplace=True)

    return losses


def get_losses(summed_flows):
    r"""


    Parameters
    ----------
    results

    Returns
    -------

    """
    inputs = get_inputs(summed_flows)

    outputs = get_outputs(summed_flows)

    losses = substract_output_from_input(inputs, outputs)

    return losses


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

    scalars = get_scalars(es.results)

    scalars = scalars_to_df(scalars)

    sequences = get_sequences(es.results)

    sequences = sequences_to_df(sequences)

    summed_flows = sum_sequences_df(sequences)

    summed_flows_re = filter_series_by_component_attr(summed_flows, tech=['wind', 'solar'])

    summed_flows_storage = filter_series_by_component_attr(summed_flows, type='storage')

    storage_losses = get_losses(summed_flows_storage)

    summed_flows_transmission = filter_series_by_component_attr(summed_flows, type='link')

    transmission_losses = get_losses(summed_flows_transmission)
