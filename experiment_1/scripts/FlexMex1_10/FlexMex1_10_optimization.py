"""
"""
import os

from oemof.solph import EnergySystem, Model

# DONT REMOVE THIS LINE!
from oemof.tabular import datapackage  # noqa
from oemof.tabular.facades import TYPEMAP
import oemof.tabular.tools.postprocessing as pp

from oemoflex.helpers import get_experiment_paths


name = 'FlexMex1_10'

abspath = os.path.abspath(os.path.dirname(__file__))

path_config = os.path.join(abspath, '../../config.yml')

experiment_paths = get_experiment_paths(name, path_config)

# create  path for results (we use the datapackage_dir to store results)
results_path = experiment_paths['results_optimization']
if not os.path.exists(results_path):
    os.makedirs(results_path)


def main():
    r"""
    Takes the specified datapackage, creates an energysystem and solves the
    optimization problem.
    """
    # create energy system object
    es = EnergySystem.from_datapackage(
        os.path.join(experiment_paths['data_preprocessed'], "datapackage.json"),
        attributemap={}, typemap=TYPEMAP,
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


if __name__ == '__main__':
    main()
