"""
"""
import os

from oemof.solph import EnergySystem, Model

# DONT REMOVE THIS LINE!
from oemof.tabular import datapackage  # noqa
from oemof.tabular.facades import TYPEMAP
import oemof.tabular.tools.postprocessing as pp

name = "FlexMex1_10"

abspath = os.path.abspath(os.path.dirname(__file__))

# path to directory with datapackage to load
datapackage_dir = os.path.join(abspath, '..', '002_data_preprocessed', name)

# create  path for results (we use the datapackage_dir to store results)
results_path = os.path.join(abspath, '..', '003_results_optimization', name)
if not os.path.exists(results_path):
    os.makedirs(results_path)

# create energy system object
es = EnergySystem.from_datapackage(
    os.path.join(datapackage_dir, "datapackage.json"), attributemap={}, typemap=TYPEMAP,
)

# create model from energy system (this is just oemof.solph)
m = Model(es)

# if you want dual variables / shadow prices uncomment line below
# m.receive_duals()

# save lp file together with optimization results
lp_file_dir = os.path.join(results_path, '{}.lp'.format(name))
m.write(lp_file_dir, io_options={'symbolic_solver_labels': True})

# select solver 'gurobi', 'cplex', 'glpk' etc
m.solve("cbc")

# get the results from the the solved model(still oemof.solph)
m.results = m.results()

# now we use the write results method to write the results in oemof-tabular
# format
pp.write_results(m, results_path, raw=True)