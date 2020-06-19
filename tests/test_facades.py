import os
import pandas as pd

from oemof.solph import Bus, Sink, Source, Flow, EnergySystem, Model
from oemoflex.facades import Bev


def test_bev():
    timeindex = pd.date_range('2020-01-01', periods=3, freq='H')

    es = EnergySystem(timeindex=timeindex)
    # Node.registry = es

    el_bus = Bus(label='electricity')

    el_grid = Source(
        label='el_grid',
        outputs={el_bus: Flow(variable_costs=120)}
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

    es.add(el_bus, el_grid, el_excess, bev)

    m = Model(es)

    lp_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lp-file.lp')
    m.write(lp_file_path, io_options={'symbolic_solver_labels': True})

    import sys
    f = open("pprint.txt", 'w')
    sys.stdout = f
    m.pprint()
    f.close()

    m.solve()

    results = m.results()

    seq_dict = {k: v['sequences'] for k, v in results.items() if 'sequences' in v}
    sequences = pd.concat(seq_dict.values(), 1)
    sequences.columns = seq_dict.keys()
    print(sequences)


if __name__ == '__main__':
    test_bev()
