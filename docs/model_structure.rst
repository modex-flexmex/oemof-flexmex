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

All busses are defined in :file:`oemof_flexmex/results/{scenario}/01_preprocessed/data/elements/bus.csv`.

The preprocessed component data is also stored in :file:`oemof_flexmex/results/{scenario}/01_preprocessed/data/elements`

The filenames for the components are of the form

::

    {carrier}-{tech}.csv
(e.g. :file:`electricity-demand.csv`, :file:`gas-bpchp.csv`).

The first columns of the component scalars file are similar in all of the files. They contain the following information:

* **region**: Region of a component. Modelled :ref:`regions<Regions>` are defined here
* **name**: Unique name (:py:attr:`'region-carrier-tech'`, eg. :py:attr:`'LU-gas-bpchp'`,
  :py:attr:`'AT-electricity-airsourcehp'`)
* **type**: Type of oemof.tabular.facade
* **carrier**: Energy sector according to carrier (e.g. solar, wind, biomass, coal, lignite, uranium, oil, gas, methane, hydro, waste, electricity, heat).
* **tech**: Specification of the technology (e.g. pv, onshore, offshore, battery, demand, curtailment, shortage, transmission, ror, st, ocgt, ccgt, extchp, bpchp)

Following these columns, the attributes for the respective components are defined. The number and kind of attributes
varies between components.


Sequences
---------

The input timeseries are combined into a new set of CSV files, with one file per technology.
The preprocessed sequences are stored in ::

    results/{scenario name}/01_preprocessed/data/sequences/{technology}_profile.csv

The filenames are of the form

::

    <carrier>-<tech>_<profile>.csv

(e.g. :file:`wind-offshore_profile.csv`, :file:`electricity-demand_profile.csv`).

Each sequence file contains the hourly profile of all the regions, organized in rows. They are indexed by a pandas
datetimeindex. The column names have the structure ``{region}-{technology}-profile``.


Available components
====================

These components are available in oemof-flexmex.

.. csv-table::
   :header-rows: 1
   :file: ../oemof_flexmex/model_structure/components.csv

Component attributes
====================

The component's attributes are defined in separate csv files contained in
:file:`oemof-flexmex/model_structure/component_attrs/`


Extra parameters
----------------

tabular supports handing over extra ``output_parameters`` and ``input_parameters`` to the components’ classes.
These have to be given as ``dict``'s in the corresponding CSV field.
If you want to pass more than two parameters:

A) Enclose the ``dict`` with quotes and use double-quotes in it (*less readable*).

*OR*

B) Make the CSV file semicolon-separated and separate the output_parameters and/or
   input_parameters with commas (*better readable*).

   More over, all component ``read_csv()`` function calls in ``preprocessing.csv`` must be adapted to the new separator (``sep=';'``).

   See https://github.com/modex-flexmex/oemo-flex/issues/57 for details.
