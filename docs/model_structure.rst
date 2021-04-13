.. _model_structure_label:

~~~~~~~~~~~~~~~
Model structure
~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top

Model structure
===============

The model structure defines the format of the preprocessed data which is ready to be optimized by oemof.

Elements
--------

All buses are defined in :file:`bus.csv`.

The filenames for the components are of the form <carrier>-<tech>.csv (e.g. :file:`electricity-demand.csv`, :file:`gas-bpchp.csv`).

TODO: Explain the basic columns in the scalar files.

* **region** Region of a component. Modelled regions are defined here (TODO: Add link to region
  definition)
* **name** Unique name (:py:attr:`'region-carrier-tech'`, eg. :py:attr:`'LU-gas-bpchp'`,
  :py:attr:`'AT-electricity-airsourcehp'`)
* **type** Type of oemof.tabular.facade
* **carrier** Energy sector according to carrier (e.g. solar, wind, biomass, coal, lignite, uranium, oil, gas, methane, hydro, waste, electricity, heat).
* **tech** Specification of the technology (e.g. st, ocgt, ccgt, pv, onshore, offshore, ror, phs, extchp, bpchp, battery)

TODO: Explain that other columns that follow describe the attributes of the components.

Sequences
---------

The filenames are of the form type_profile (e.g.
:file:`wind-offshore_profile.csv`, :file:`electricity-demand_profile.csv`).

TODO: explain the columns and their names within the sequences files

Available components
====================

These components are available in oemoflex.

.. csv-table::
   :header-rows: 1
   :file: ../oemoflex/model_structure/components.csv

Component attributes
====================

The component's attributes are defined in separate csv files contained in
:file:`oemoflex/model_structure/component_attrs/`

TODO: Explain defaults, suffices
