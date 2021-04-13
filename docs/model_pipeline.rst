.. _model_pipeline_label:

~~~~~~~~~~~~~~
Model pipeline
~~~~~~~~~~~~~~

TODO: Start with a short section on snakemake, explain that this is the workflow management tool that is used.

Data processing in oemoflex is divided in 4 main steps:

* preprocessing
* inferring
* optimization
* postprocessing

TODO: Each of these steps is represented by a snakemake rule, which runs the script with the same name.

The data each step is provided with is held in different forms:

* raw data
* preprocessed data
* optimization results
* postprocessed results

.. Todo Simple Diagram?


.. _input data format:

Raw data
========

The raw data holds the energy system model definition for all scenarios.
It consists of a parameter database (parameters are called `scalars`) and a bunch of timeseries (`sequences` or `profiles`).

The data is expected to be CSV-formatted and is read from ``data/In``.
The format of timeseries and scalars is described below.

.. note:: Raw data for FlexMex is not part of the oemoflex github repository but can be provided by the FlexMex project partners.

Scalars
-------

The scalars database defines parameters for all scenarios and regions.
It is held in a CSV file called ``Scalars.csv``.

.. Path needs to be added

The following table shows the first lines of an example ``Scalars.csv`` and its format:

========  ======  ====  =============================================  =======  =========
Scenario  Region  Year  Parameter                                      Unit     Value
========  ======  ====  =============================================  =======  =========
FlexMex1  ALL     ALL   Energy_SlackCost_Electricity                   Eur/GWh  50000000
FlexMex1  ALL     ALL   Energy_SlackCost_Electricity                   Eur/GWh  5000000
ALL       ALL     ALL   Energy_SlackCost_Heat                          Eur/GWh  1000000
ALL       ALL     ALL   Energy_SlackCost_H2                            Eur/GWh  1000000
FlexMex1  AT      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  248
FlexMex1  BE      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  584
FlexMex1  CH      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  183
FlexMex1  CZ      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  275
FlexMex1  DE      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  2950
FlexMex1  DK      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  391
FlexMex1  FR      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  3361
FlexMex1  IT      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  2304
FlexMex1  LU      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  58
FlexMex1  NL      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  947
FlexMex1  PL      2050  DemandResponse_Capacity_Electricity_Cooling    MW (el)  1497
FlexMex1  AT      2050  DemandResponse_Capacity_Electricity_HVAC       MW (el)  964
FlexMex1  BE      2050  DemandResponse_Capacity_Electricity_HVAC       MW (el)  2144
FlexMex1  CH      2050  DemandResponse_Capacity_Electricity_HVAC       MW (el)  1027
FlexMex1  CZ      2050  DemandResponse_Capacity_Electricity_HVAC       MW (el)  1117
========  ======  ====  =============================================  =======  =========

Scenario: `string`
    Special identifier to address scenario or group of scenarios ('experiment')

    .. note:: The keyword ``ALL`` can be used as a universal quantifier to avoid repetition.


Region: `string`
    Region identifier

    .. note:: The keyword ``ALL`` can be used as a universal quantifier to avoid repetition.


Year: `integer`
    Year

    .. warning:: Years support is not fully implemented!


Parameter: `string`
    The parameter name used in the FlexMex project. This is mapped via preprocessing to the components parameters.


Unit: `string`
    Unit of measurement of the given value

    .. warning:: Unit support is incomplete! Especially, there is no check for unit equivalence nor any automatic unit conversion!


Value: `float`
    Value of the parameter


Timeseries
----------

Timeseries in oemoflex assign a value to every hour of the year (1...8760).
They are hold in CSV files with time index-value pairs per line and one timeseries per file.

.. warning:: The time index is ignored at the moment. It will be overwritten by a ``pandas`` ``datetimeindex``.

The paths to the timeseries are defined in ``flexmex_config/mapping-input-timeseries.yml`` per component.
If a component has no timeseries defined here, an info line is added to the log output.

The found filenames are interpreted according to the following pattern::

    {experiment name}_{region code}_{year}.csv

.. note:: ``Experiment name`` and ``year`` are ignored at the moment.


Preprocessing
=============



Preprocessing brings the raw data into the `oemof.tabular format <https://oemof-tabular.readthedocs.io/en/latest/usage.html>`_.
In this step, scalars belonging to a component are mapped to the components model parameters and saved within an input CSV file.
Timeseries are attached in a similar way.
The so formed input data is held in a ``datapackage`` format comprising a JSON schema file (meta data) and the CSV files containing the actual data.

TODO: This repeates information that is already found in "model structure". Move the docs on extra parameters there.

The found timeseries are combined into a new set of CSV files, with one file per technology and ``{region code}-{component}-profile`` as column names.
They are stored in ::

    results/{scenario name}/01_preprocessed/data/sequences/{technology}_profile.csv

for the optimization step.

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

Optimization
============

Optimization is performed by oemof-solph. Specifically, with the help of oemof.tabular, an :class:`EnergySystem` can be created from the data package
created in preprocessing.

.. _postprocessing:

Postprocessing
==============

Postprocessing translates the results into an exchange-friendly format defined by the FlexMex project partners.
For that, a result template defines the parameters to be output for each scenario.
The oemoflex-internal parameters are recalculated and mapped to the FlexMex parameter names.

The results template is provided by the FlexMex project partners.
It consists of an output directory structure and a scaffold Scalars.csv output file (with no values).
It should be placed in the path::

    flexmex_config/output_template/

The mapping is read from the two CSV files::

    flexmex_config/mapping-output-scalars.csv
    flexmex_config/mapping-output-timeseries.yml
