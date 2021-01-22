import copy

import pandas as pd

from oemof.solph import Bus, EnergySystem
from oemof.outputlib import processing

from oemoflex.postprocessing import create_postprocessed_results_subdirs


def get_flow_by_oemof_tuple(oemof_tuple):
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


def filter_sequences(dict):

    _dict = copy.deepcopy(dict)

    seq = {key: value['sequences'] for key, value in _dict.items() if 'sequences' in value}

    return seq


def sum_sequences(sequences):

    _sequences = copy.deepcopy(sequences)

    for oemof_tuple, value in _sequences.items():

        _sequences[oemof_tuple] = value.sum()

    return _sequences


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

    seq = filter_sequences(es.results)

    summed_flows = sum_sequences(seq)
