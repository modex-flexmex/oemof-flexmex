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


def get_capacities(m):
    r"""
    Calculates the capacities of all components.

    Extracted from oemof.tabular.tools.postprocessing.write_results()

    Parameters
    ----------
    m : oemof.solph.Model
        Model containing the results.

    Returns
    -------
    capacities : pd.DataFrame
        DataFrame containing the capacities.
    """
    try:
        all = pp.bus_results(m.es, m.results, select="scalars", concat=True)
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
    for node in m.es.nodes:
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
