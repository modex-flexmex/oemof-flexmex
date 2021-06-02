.. _model_structure_label:

~~~~~~~~~~~~~~~
Model structure
~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top

Data format
===========

The preprocessing brings the raw data into the data defined data format that serves as input for
the optimisation.

Elements
--------

All buses are defined in :file:`bus.csv`.

The filenames for the components are of the form carrier-tech.csv (e.g. :file:`electricity-demand.csv`, :file:`gas-bpchp.csv`).

* **region** Region of a component. Modelled regions are defined here (TODO: Add link to region
  definition)
* **name** Unique name (:py:attr:`'region-carrier-tech'`, eg. :py:attr:`'LU-gas-bpchp'`,
  :py:attr:`'AT-electricity-airsourcehp'`)
* **type** Type of oemof.tabular.facade
* **carrier** Energy sector according to carrier (e.g. solar, wind, biomass, coal, lignite, uranium, oil, gas, methane, hydro, waste, electricity, heat).
* **tech** Specification of the technology (e.g. st, ocgt, ccgt, pv, onshore, offshore, ror, phs, extchp, bpchp, battery)

Sequences
---------

The filenames are of the form type_profile (e.g.
:file:`wind-offshore_profile.csv`, :file:`electricity-demand_profile.csv`).

Available components
====================

These components are available in oemof-flexmex.

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/components.csv

Component attributes
====================

Here is an overview over the component's attributes.

Bus
---

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/busses.csv

Shortage
--------

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/component_attrs/electricity-shortage.csv

Curtailment
-----------

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/component_attrs/electricity-curtailment.csv

PV
--

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/component_attrs/solar-pv.csv

Wind onshore
------------

Wind offshore is identical apart from onshore replaced by offshore.

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/component_attrs/wind-onshore.csv

Link
----

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/component_attrs/electricity-transmission.csv
