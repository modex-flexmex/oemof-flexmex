import pandas as pd
from oemof.solph import (Sink, Source, Bus, Flow, Model,
                         EnergySystem)
from oemoflex.facades import AsymmetricStorage
from oemof.outputlib import views


solver = 'cbc'


def check_init_methods():
    # bus = Bus('bus_elec')
    # storage =  AsymmetricStorage(
    #        label="h2-cavern",
    #        bus=bus,
    #        carrier="electricity",
    #        tech="cavern",
    #        storage_capacity_cost=10,
    #        invest_relation_output_capacity=1/6, # oemof.solph
    #        marginal_cost=5,
    #        initial_storage_level=1, # oemof.solph argument
    # )
    #
    # assert storage.inputs[bus] == 0.3
    # assert storage.conversion_factors[bus] ==

    bus = Bus('bus_elec')
    storage = AsymmetricStorage(
           label="h2-cavern",
           bus=bus,
           carrier="electricity",
           tech="cavern",
           storage_capacity=10,
           marginal_cost=5,
    )

    # assert storage.inputs[bus] == 0.3
    # assert storage.conversion_factors[bus] ==

    bus = Bus('bus_elec')
    storage = AsymmetricStorage(
        label="h2-cavern",
        bus=bus,
        carrier="electricity",
        tech="cavern",
        expandable=True,
        storage_capacity_cost=100,
        marginal_cost=5,
    )


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
