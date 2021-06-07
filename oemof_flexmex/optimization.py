import logging
import os

from oemof.outputlib import processing
from oemof.solph import EnergySystem, Model

# DONT REMOVE THIS LINE!
# pylint: disable=unused-import
from oemof.tabular import datapackage  # noqa
from oemof_flexmex.facades import TYPEMAP


def optimize(data_preprocessed, results_optimization, solver='cbc', save_lp=False):
    r"""
    Takes the specified datapackage, creates an energysystem and solves the
    optimization problem.
    """
    # create energy system object
    logging.info("Creating EnergySystem from datapackage")
    es = EnergySystem.from_datapackage(
        os.path.join(data_preprocessed, "datapackage.json"),
        attributemap={}, typemap=TYPEMAP,
    )

    # create model from energy system (this is just oemof.solph)
    logging.info("Creating the optimization model")
    m = Model(es)

    # if you want dual variables / shadow prices uncomment line below
    # m.receive_duals()

    # save lp file together with optimization results
    if save_lp:
        lp_file_dir = os.path.join(results_optimization, 'model.lp')
        logging.info(f"Saving the lp-file to {lp_file_dir}")
        m.write(lp_file_dir, io_options={'symbolic_solver_labels': True})

    # select solver 'gurobi', 'cplex', 'glpk' etc
    logging.info(f'Solving the problem using {solver}')
    m.solve(solver=solver, solve_kwargs={"tee": True})

    # get the results from the the solved model(still oemof.solph)
    es.meta_results = processing.meta_results(m)
    es.results = processing.results(m)
    es.params = processing.parameter_as_dict(es)

    # now we use the write results method to write the results in oemof-tabular
    # format
    logging.info(f'Writing the results to {results_optimization}')
    es.dump(results_optimization)
