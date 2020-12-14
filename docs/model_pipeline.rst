.. _model_pipeline_label:

~~~~~~~~~~~~~~
Model pipeline
~~~~~~~~~~~~~~

Data processing in oemoflex is divided in 3 main steps:

* preprocessing
* optimisation
* postprocessing

The data each step is provided with is held in different forms:

* raw data
* preprocessed data
* optimisation results
* postprocessed results

.. Todo Simple Diagram?

Raw data
========

The raw data holds the energy system model definition for every use case.
It consists of a parameter database (parameters are called `scalars`) and a bunch of timeseries (`sequences` or `profiles`).

Scalars
-------

The scalars database defines parameters for all use cases and regions.
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
    Special identifier to address use case or group of use cases ('experiment')

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

Preprocessing
=============

Preprocessing brings the raw data into the `oemof.tabular format <https://oemof-tabular.readthedocs.io/en/latest/usage.html>`_.
In this step, scalars belonging to a component are mapped to the components model parameters and saved within an input CSV file.
Timeseries are attached in a similar way.
The so formed input data is held in a `datapackage` format comprising a JSON schema file (meta data) and the CSV files containing the actual data.

Extra parameter format
----------------------

tabular supports handing over extra ``output_parameters`` and ``input_parameters`` to the component’s classes.
These have to be given as ``dict``’s in the corresponding CSV field.
If you want to pass more than two parameters, turn the CSV file into semicolon-separated and separate the output_parameters and/or input_parameters with commas.
More over, all component ``read_csv()`` function calls in ``preprocessing.csv`` must be adapted to the new seperator (``sep=';'``).
See https://github.com/modex-flexmex/oemo-flex/issues/57 for details.

Optimisation
============

Optimisation is performed by oemof-solph.

Postprocessing
==============

Postprocessing translates the results into an exchange-friendly format defined by the FlexMex project partners.
For that, a result template defines the parameters to be output for each use case.
