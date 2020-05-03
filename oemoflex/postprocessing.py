import os

import numpy as np
import pandas as pd

from oemof.solph import Bus, Sink
from oemof.tabular import facades
import oemof.tabular.tools.postprocessing as pp


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
                        node,
                        [n for n in node.outputs.keys()][0],
                        "capacity",
                        node.tech,  # tech & carrier are oemof-tabular specific
                        node.carrier,
                    )  # for oemof logic
                    d[key] = {"value": node.capacity}
    exogenous = pd.DataFrame.from_dict(d).T  # .dropna()

    if not exogenous.empty:
        exogenous.index = exogenous.index.set_names(
            ["from", "to", "type", "tech", "carrier"]
        )

    capacities = pd.concat([endogenous, exogenous])

    return capacities


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
            carrier_tech = key[1].carrier + '-' + key[1].tech
            if carrier_tech not in sequences_by_tech:
                sequences_by_tech[carrier_tech] = []

            df.columns = pd.MultiIndex.from_tuples([(key[1].label, 'in_flow')])

        if isinstance(key[1], Bus):
            carrier_tech = key[0].carrier + '-' + key[0].tech
            if carrier_tech not in sequences_by_tech:
                sequences_by_tech[carrier_tech] = []

            df.columns = pd.MultiIndex.from_tuples([(key[0].label, 'out_flow')])

        if key[1] is None:
            carrier_tech = key[0].carrier + '-' + key[0].tech
            if carrier_tech not in sequences_by_tech:
                sequences_by_tech[carrier_tech] = []
            df.columns = pd.MultiIndex.from_tuples([(key[0].label, 'storage_content')])

        df.columns.names = ['name', 'var_name']
        sequences_by_tech[carrier_tech].append(df)

    sequences_by_tech = {key: pd.concat(value, 1) for key, value in sequences_by_tech.items()}

    return sequences_by_tech


def get_summed_sequences(sequences_by_tech, prep_elements):
    basic_columns = ['region', 'name', 'type', 'tech', 'bus']
    summed_sequences = []
    for tech_carrier, sequence in sequences_by_tech.items():
        if prep_elements[tech_carrier]['type'][0] == 'link':
            pass  # TODO
        else:
            df = prep_elements[tech_carrier][basic_columns]
            sum = sequence.sum()
            sum.name = 'var_value'
            sum = sum.reset_index()
            df = pd.merge(df, sum, on='name')
            summed_sequences.append(df)

    summed_sequences = pd.concat(summed_sequences)

    return summed_sequences
