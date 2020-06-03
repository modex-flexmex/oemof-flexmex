from oemof.tabular.facades import Facade
from oemof.solph import Flow, Investment
from oemof.solph.components import GenericStorage
from oemof.solph.plumbing import sequence


class Facade(Facade):

    def _nominal_value(self):
        """ Returns None if self.expandable ist True otherwise it returns
        the capacities
        """
        if self.expandable is True:
            return None

        else:
            if isinstance(self, AsymmetricStorage):
                return {
                    "charge": self.capacity_charge,
                    "discharge": self.capacity_discharge}
            else:
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
        """
        """
        self.nominal_storage_capacity = self.storage_capacity

        self.inflow_conversion_factor = sequence(self.efficiency_charge)

        self.outflow_conversion_factor = sequence(self.efficiency_discharge)

        # make it investment but don't set costs (set below for flow (power))
        self.investment = self._investment()

        if self.investment:
            self.invest_relation_input_output = 1

            for attr in ["invest_relation_input_output"]:
                if getattr(self, attr) is None:
                    raise AttributeError(
                        (
                            "You need to set attr " "`{}` " "for component {}"
                        ).format(attr, self.label)
                    )

            # set capacity costs at one of the flows
            fi = Flow(
                investment=Investment(
                    ep_costs=self.capacity_cost_charge,
                    maximum=self.capacity_potential_charge,
                    existing=self.capacity_charge,
                ),
                **self.input_parameters
            )
            # set investment, but no costs (as relation input / output = 1)
            fo = Flow(
                investment=Investment(
                    ep_costs=self.capacity_cost_discharge,
                    maximum=self.capacity_potential_discharge,
                    existing=self.capacity_discharge,
                ),
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
                variable_costs=self.marginal_cost,
                **self.output_parameters
            )

        self.inputs.update({self.bus: fi})

        self.outputs.update({self.bus: fo})

        self._set_flows()