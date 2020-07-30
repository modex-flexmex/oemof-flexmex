from oemof.solph import sequence, Bus, Sink, Transformer, Flow, Investment
from oemof.solph.components import GenericStorage

from oemof.tabular.facades import Facade, TYPEMAP


class Facade(Facade):  # pylint: disable=E0102

    def _nominal_value(self):
        """ Returns None if self.expandable ist True otherwise it returns
        the capacities
        """
        if self.expandable is True:
            return None

        if isinstance(self, AsymmetricStorage):
            return {
                "charge": self.capacity_charge,
                "discharge": self.capacity_discharge}

        return self.capacity


class AsymmetricStorage(GenericStorage, Facade):

    def __init__(self, *args, **kwargs):

        super().__init__(
            _facade_requires_=["bus", "carrier", "tech"], *args, **kwargs
        )

        self.storage_capacity = kwargs.get("storage_capacity", 0)

        self.capacity_charge = kwargs.get("capacity_charge", 0)
        self.capacity_discharge = kwargs.get("capacity_discharge", 0)

        self.capacity_cost_charge = kwargs.get("capacity_cost_charge")
        self.capacity_cost_discharge = kwargs.get("capacity_cost_discharge")

        self.storage_capacity_cost = kwargs.get("storage_capacity_cost")

        self.storage_capacity_potential = kwargs.get(
            "storage_capacity_potential", float("+inf")
        )

        self.capacity_potential_charge = kwargs.get(
            "capacity_potential_charge", float("+inf")
        )

        self.capacity_potential_discharge = kwargs.get(
            "capacity_potential_discharge", float("+inf")
        )

        self.expandable = bool(kwargs.get("expandable", False))

        self.marginal_cost = kwargs.get("marginal_cost", 0)

        self.efficiency_charge = kwargs.get("efficiency_charge", 1)

        self.efficiency_discharge = kwargs.get("efficiency_discharge", 1)

        self.input_parameters = kwargs.get("input_parameters", {})

        self.output_parameters = kwargs.get("output_parameters", {})

        self.build_solph_components()

    def build_solph_components(self):

        self.nominal_storage_capacity = self.storage_capacity

        self.inflow_conversion_factor = sequence(self.efficiency_charge)

        self.outflow_conversion_factor = sequence(self.efficiency_discharge)

        # self.investment = self._investment()
        if self.expandable is True:
            if any([self.capacity_cost_charge,
                    self.capacity_cost_discharge,
                    self.storage_capacity_cost]) is None:
                msg = (
                    "If you set `expandable` to True you need to set "
                    "attribute `storage_capacity_cost`,"
                    "`capacity_cost_charge` and `capacity_cost_discharge` of component {}!"
                )
                raise ValueError(msg.format(self.label))

            self.investment = Investment(
                ep_costs=self.storage_capacity_cost,
                maximum=getattr(self, "storage_capacity_potential", float("+inf")),
                minimum=getattr(self, "minimum_storage_capacity", 0),
                existing=getattr(self, "storage_capacity", 0),
            )

            fi = Flow(
                investment=Investment(
                    ep_costs=self.capacity_cost_charge,
                    maximum=getattr(self, "capacity_potential_charge", float("+inf")),
                    existing=getattr(self, "capacity_charge", 0),
                ),
                **self.input_parameters
            )

            fo = Flow(
                investment=Investment(
                    ep_costs=self.capacity_cost_discharge,
                    maximum=getattr(self, "capacity_potential_discharge", float("+inf")),
                    existing=getattr(self, "capacity_discharge", 0),
                ),
                # Attach marginal cost to Flow out
                variable_costs=self.marginal_cost,
                **self.output_parameters
            )
            # required for correct grouping in oemof.solph.components
            self._invest_group = True

        else:
            fi = Flow(
                nominal_value=self._nominal_value()["charge"], **self.input_parameters
            )
            fo = Flow(
                nominal_value=self._nominal_value()["discharge"],
                # Attach marginal cost to Flow out
                variable_costs=self.marginal_cost,
                **self.output_parameters
            )

        self.inputs.update({self.bus: fi})

        self.outputs.update({self.bus: fo})

        self._set_flows()


class Bev(GenericStorage, Facade):
    r""" A Battery electric vehicle unit.

    Note that the investment option is not available for this facade at
    the current development state.

    Parameters
    ----------
    bus: oemof.solph.Bus
        An oemof bus instance where the storage unit is connected to.
    storage_capacity: numeric
        The total storage capacity of the storage (e.g. in MWh)
    capacity: numeric
        Installed production capacity of the turbine installed at the
        reservoir
    efficiency: numeric
        Efficiency of the turbine converting inflow to electricity
        production, default: 1
    profile: array-like
        Absolute inflow profile of inflow into the storage
    input_parameters: dict
        Dictionary to specifiy parameters on the input edge. You can use
        all keys that are available for the  oemof.solph.network.Flow class.
    output_parameters: dict
        see: input_parameters


    The reservoir is modelled as a storage with a constant inflow:

    .. math::

        x^{level}(t) =
        x^{level}(t-1) \cdot (1 - c^{loss\_rate}(t))
        + x^{profile}(t) - \frac{x^{flow, out}(t)}{c^{efficiency}(t)}
        \qquad \forall t \in T

    .. math::
        x^{level}(0) = 0.5 \cdot c^{capacity}

    The inflow is bounded by the exogenous inflow profile. Thus if the inflow
    exceeds the maximum capacity of the storage, spillage is possible by
    setting :math:`x^{profile}(t)` to lower values.

    .. math::
        0 \leq x^{profile}(t) \leq c^{profile}(t) \qquad \forall t \in T


    The spillage of the reservoir is therefore defined by:
    :math:`c^{profile}(t) - x^{profile}(t)`.

    Note
    ----
    As the Reservoir is a sub-class of `oemof.solph.GenericStorage` you also
    pass all arguments of this class.


    Examples
    --------
    Basic usage examples of the GenericStorage with a random selection of
    attributes. See the Flow class for all Flow attributes.

    >>> from oemof import solph
    >>> from oemof.tabular import facades
    >>> my_bus = solph.Bus('my_bus')
    >>> my_bev = Bev(
    ...     name='my_bev',
    ...     bus=el_bus,
    ...     carrier='electricity',
    ...     tech='bev',
    ...     storage_capacity=1000,
    ...     capacity=50,
    ...     availability=[0.8, 0.7, 0.6],
    ...     drive_power=[1, 2, 6],
    ...     amount=1e9,
    ...     loss_rate=0.01,
    ...     initial_storage_level=0,
    ...     min_storage_level=[0.1, 0.2, 0.15],
    ...     max_storage_level=[0.9, 0.95, 0.92],
    ...     efficiency=0.93
    ...     )

    """

    def __init__(self, *args, **kwargs):

        kwargs.update(
            {
                "_facade_requires_": [
                    "bus",
                    "carrier",
                    "tech",
                    "availability",
                    "drive_power",
                    "amount",
                    "efficiency",
                ]
            }
        )
        super().__init__(*args, **kwargs)

        self.storage_capacity = kwargs.get("storage_capacity")

        self.capacity = kwargs.get("capacity")

        self.efficiency = kwargs.get("efficiency", 1)

        self.profile = kwargs.get("profile")

        self.input_parameters = kwargs.get("input_parameters", {})

        self.output_parameters = kwargs.get("output_parameters", {})

        self.expandable = bool(kwargs.get("expandable", False))

        self.build_solph_components()

    def build_solph_components(self):
        """
        """
        self.nominal_storage_capacity = self.storage_capacity

        self.inflow_conversion_factor = sequence(self.efficiency)

        self.outflow_conversion_factor = sequence(self.efficiency)

        if self.expandable:
            raise NotImplementedError(
                "Investment for reservoir class is not implemented."
            )

        internal_bus = Bus(label=self.label + "-internal_bus")

        vehicle_to_grid = Transformer(
            label=self.label + '-vehicle_to_grid',
            inputs={internal_bus: Flow()},
            outputs={self.bus: Flow(nominal_value=self.capacity)},
            conversion_factors={internal_bus: self.efficiency},
        )

        drive_power = Sink(
            label=self.label + "-drive_power",
            inputs={
                internal_bus: Flow(nominal_value=self.amount,
                                   actual_value=self.drive_power,
                                   fixed=True)
            },
        )

        self.inputs.update(
            {
                self.bus: Flow(
                    nominal_value=self.capacity,
                    max=self.availability,
                    conversion_factors=self.efficiency,
                    variable_costs=0.00001,
                    **self.input_parameters
                )
            }
        )

        self.outputs.update(
            {
                internal_bus: Flow()
            }
        )

        self.subnodes = (internal_bus, drive_power, vehicle_to_grid)


TYPEMAP.update({"asymmetric storage": AsymmetricStorage, "bev": Bev})
