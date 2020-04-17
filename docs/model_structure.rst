.. _model_structure_label:

~~~~~~~~~~~~~~~
Model structure
~~~~~~~~~~~~~~~

oemoflex is a model of the integrated European energy system, featuring many flexibility options.

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

The filenames are of the form type.csv (e.g. :file:`bus.csv`, :file:`backpressure.csv`).

* **region** Region of a component. Modelled regions are defined here (TODO: Add link to region
  definition)
* **name** Unique name (:py:attr:`'carrier-type-tech-region'`, eg. :py:attr:`'heat-bus-central-LU'`,
  :py:attr:`'heat-heatpump-airsource-AT'`)
* **type** Type of oemof.tabular.facade
* **carrier** Energy sector according to carrier (e.g. electricity, heat, natural_gas,
  methane, hard_coal).
* **tech** Specification of the technology

Sequences
---------

The filenames are of the form type_profile (e.g.
:file:`volatile_profile.csv`, :file:`load_profile.csv`).

Available components
====================

These components are available in oemoflex.

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/components.csv

Component attributes
====================

Here is an overview over the component's attributes.

Bus
---

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/bus.csv

Shortage
--------

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/shortage.csv

Curtailment
-----------

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/curtailment.csv

PV
--

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/pv.csv

Wind onshore
------------

Wind offshore is identical apart from onshore replaced by offshore.

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/wind-onshore.csv

Link
----

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/component_attrs/link.csv
