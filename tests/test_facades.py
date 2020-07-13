import os
import pandas as pd

from oemof.solph import Bus, Sink, Source, Flow, EnergySystem, Model
from oemoflex.facades import ReservoirWithPump


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
        amount=1000,
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


if __name__ == '__main__':
    test_reservoir()
