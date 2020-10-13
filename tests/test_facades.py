import os
import pandas as pd

from oemof.solph import (Sink, Source, Bus, Flow, Model,
                         EnergySystem)

from oemoflex.facades import Bev
from oemof.outputlib import views
from oemoflex.facades import AsymmetricStorage, ReservoirWithPump

solver = 'cbc'


# def check_init_methods():
#     # bus = Bus('bus_elec')
#     # storage =  AsymmetricStorage(
#     #        label="h2-cavern",
#     #        bus=bus,
#     #        carrier="electricity",
#     #        tech="cavern",
#     #        storage_capacity_cost=10,
#     #        invest_relation_output_capacity=1/6, # oemof.solph
#     #        marginal_cost=5,
#     #        initial_storage_level=1, # oemof.solph argument
#     # )
#     #
#     # assert storage.inputs[bus] == 0.3
#     # assert storage.conversion_factors[bus] ==
#
#     bus = Bus('bus_elec')
#     storage = AsymmetricStorage(
#            label="h2-cavern",
#            bus=bus,
#            carrier="electricity",
#            tech="cavern",
#            storage_capacity=10,
#            marginal_cost=5,
#     )
#
#     # assert storage.inputs[bus] == 0.3
#     # assert storage.conversion_factors[bus] ==
#
#     bus = Bus('bus_elec')
#     storage = AsymmetricStorage(
#         label="h2-cavern",
#         bus=bus,
#         carrier="electricity",
#         tech="cavern",
#         expandable=True,
#         storage_capacity_cost=100,
#         marginal_cost=5,
#     )


def check_asymmetric_storage_optimize_dispatch():
    r"""
    Charge storage in timestep 1 and discharge it with a different power in timestep 2 and 3.
    Storage's capacities (storage, charge, discharge).
    """

    energysystem = EnergySystem(timeindex=pd.date_range('2019', periods=3, freq='H'))

    bel = Bus(label='electricity')

    energysystem.add(bel)

    energysystem.add(Sink(label='excess_el', inputs={bel: Flow()}))

    energysystem.add(
        Source(
            label='shortage_el',
            outputs={bel: Flow(variable_costs=200)}
        )
    )

    energysystem.add(
        Source(
            label='plants',
            outputs={
                bel: Flow(
                    nominal_value=6,
                    actual_value=[1, 0, 0],
                    fixed=True
                )
            }
        )
    )

    energysystem.add(
        Sink(
            label='demand',
            inputs={
                bel: Flow(
                    nominal_value=6,
                    actual_value=[0, 0.5, 0.5],
                    fixed=True
                )
            }
        )
    )

    energysystem.add(
        AsymmetricStorage(
            label="h2-cavern",
            bus=bel,
            carrier="electricity",
            tech="h2-cavern",
            capacity_charge=6,
            capacity_discharge=2,  # limiting quantity
            storage_capacity=6,
            marginal_cost=5,
            initial_storage_level=0,  # oemof.solph argument
        )
    )

    optimization_model = Model(energysystem=energysystem)

    optimization_model.solve(solver=solver,
                             solve_kwargs={'tee': True, 'keepfiles': True})

    # data = views.node(optimization_model.results(), 'electricity')
    # res = pp.results(optimization_model)

    results = views.convert_keys_to_strings(optimization_model.results())

    # Check the limiting condition
    assert all(results[('h2-cavern', 'electricity')]['sequences']['flow'].values == [0, 2., 2.])

    # Check what follows from the limting condition
    assert all(results[('electricity', 'h2-cavern')]['sequences']['flow'].values == [4., 0, 0])


def check_asymmetric_storage_optimize_investment():
    r"""
    Charge storage in timestep 1 and discharge it with a different power in timestep 2 and 3.
    Let the solver decide about the storage's capacities (storage, charge, discharge).
    """

    energysystem = EnergySystem(timeindex=pd.date_range('2019', periods=3, freq='H'))

    bel = Bus(label='electricity')

    energysystem.add(bel)

    energysystem.add(Sink(label='excess_el', inputs={bel: Flow()}))

    energysystem.add(
        Source(
            label='shortage_el',
            outputs={bel: Flow(variable_costs=200)}
        )
    )

    energysystem.add(
        Source(
            label='plants',
            outputs={
                bel: Flow(
                    nominal_value=6,
                    actual_value=[1, 0, 0],
                    fixed=True
                )
            }
        )
    )

    energysystem.add(
        Sink(
            label='demand',
            inputs={
                bel: Flow(
                    nominal_value=6,
                    actual_value=[0, 0.5, 0.5],
                    fixed=True
                )
            }
        )
    )

    energysystem.add(
        AsymmetricStorage(
            label="h2-cavern",
            bus=bel,
            carrier="electricity",
            tech="h2-cavern",
            expandable=True,
            capacity_charge=0,
            capacity_discharge=0,
            storage_capacity=0,
            capacity_cost_charge=1,
            capacity_cost_discharge=1,
            storage_capacity_cost=1,
            marginal_cost=5,
            initial_storage_level=0,  # oemof.solph argument
        )
    )

    optimization_model = Model(energysystem=energysystem)

    optimization_model.solve(solver=solver,
                             solve_kwargs={'tee': True, 'keepfiles': True})

    # data = views.node(optimization_model.results(), 'electricity')
    # res = pp.results(optimization_model)

    results = views.convert_keys_to_strings(optimization_model.results())

    # TODO Check actual invested capacities would be better
    assert all(results[('h2-cavern', 'electricity')]['sequences']['flow'].values == [0, 3., 3.])
    assert all(results[('electricity', 'h2-cavern')]['sequences']['flow'].values == [6., 0, 0])


def test_reservoir():
    timeindex = pd.date_range('2020-01-01', periods=3, freq='H')

    es = EnergySystem(timeindex=timeindex)
    # Node.registry = es

    el_bus = Bus(label='electricity')

    windpark = Source(
        label='windpark',
        outputs={el_bus: Flow(fixed=True,
                              nominal_value=15,
                              actual_value=[0.7, 0.2, 0.9])}
    )

    el_demand = Sink(
        label='el_demand',
        inputs={el_bus: Flow(fixed=True,
                             nominal_value=100,
                             actual_value=[0.1, 0.2, 0.1])}
    )

    el_excess = Sink(
        label='el_excess',
        inputs={el_bus: Flow(variable_costs=0.0001)}
    )

    reservoir = ReservoirWithPump(
        label='my_reservoir',
        bus=el_bus,
        carrier='water',
        tech='reservoir',
        storage_capacity=1000,
        capacity_pump=20,
        capacity_turbine=50,
        profile=[0.2, 0.5, 0.3],
        loss_rate=0.01,
        max_storage_level=0.9,
        min_storage_level=0.1,
        efficiency_pump=0.93,
        efficiency_turbine=0.93,
    )

    es.add(el_bus, windpark, el_demand, el_excess, reservoir)

    m = Model(es)

    lp_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lp-file.lp')
    m.write(lp_file_path, io_options={'symbolic_solver_labels': True})

    m.solve()

    results = m.results()

    seq_dict = {k: v['sequences'] for k, v in results.items() if 'sequences' in v}
    sequences = pd.concat(seq_dict.values(), 1)
    sequences.columns = seq_dict.keys()
    print(sequences)


def test_bev():
    timeindex = pd.date_range('2020-01-01', periods=3, freq='H')

    es = EnergySystem(timeindex=timeindex)
    # Node.registry = es

    el_bus = Bus(label='electricity')

    el_grid = Source(
        label='windpark',
        outputs={el_bus: Flow(fixed=True,
                              nominal_value=150,
                              actual_value=[0.7, 0.2, 0.9])}
    )

    el_demand = Sink(
        label='el_demand',
        inputs={el_bus: Flow(fixed=True,
                             nominal_value=100,
                             actual_value=[0.1, 0.2, 0.1])}
    )

    el_excess = Sink(
        label='el_excess',
        inputs={el_bus: Flow(variable_costs=0.0001)}
    )

    bev = Bev(
        label='my_bev',
        bus=el_bus,
        carrier='electricity',
        tech='bev',
        storage_capacity=1000,
        capacity=50,
        availability=[0.8, 0.7, 0.6],  # GridAvailabilityRate
        drive_power=[0.01, 0.02, 0.022],  # DrivePower
        amount=100,  # AnnualDemand
        loss_rate=0.01,
        # initial_storage_level=0.5,
        min_storage_level=[0.1, 0.2, 0.15],  # MinBatteryLevel
        max_storage_level=[0.9, 0.95, 0.92],  # MaxBatteryLevel
        efficiency=0.93
    )

    es.add(el_bus, el_grid, el_demand, el_excess, bev)

    m = Model(es)

    lp_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lp-file.lp')
    m.write(lp_file_path, io_options={'symbolic_solver_labels': True})

    m.solve()

    results = m.results()

    seq_dict = {k: v['sequences'] for k, v in results.items() if 'sequences' in v}
    sequences = pd.concat(seq_dict.values(), 1)
    sequences.columns = seq_dict.keys()
    print(sequences)


if __name__ == '__main__':
    test_reservoir()
    test_bev()
    check_asymmetric_storage_optimize_dispatch()
    check_asymmetric_storage_optimize_investment()
