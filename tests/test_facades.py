import pandas as pd

from oemof.network import Node
from oemof.solph import Bus, Source, Flow, EnergySystem, Model
from oemoflex.facades import Bev


def test_bev():
    timeindex = pd.date_range('2020-01-01', periods=3, freq='H')

    es = EnergySystem(timeindex=timeindex)
    Node.registry = es

    el_bus = Bus(label='electricity')

    Source(
        label='el_grid',
        outputs={el_bus: Flow(variable_costs=120)}
    )

    Bev(
        label='my_bev',
        bus=el_bus,
        carrier='electricity',
        tech='bev',
        storage_capacity=1000,
        capacity=50,
        availability=[0.8, 0.7, 0.6],  # GridAvailabilityRate
        drive_power=[0.01, 0.02, 0.006],  # DrivePower
        amount=1000,  # AnnualDemand
        loss_rate=0.01,
        initial_storage_level=0.5,
        min_storage_level=[0.1, 0.2, 0.15],  # MinBatteryLevel
        max_storage_level=[0.9, 0.95, 0.92],  # MaxBatteryLevel
        efficiency=0.93
    )

    m = Model(es)
    m.solve()

    m.results()
