.. _overview_label:

~~~~~~~~
Overview
~~~~~~~~

oemof-flexmex is a sector-integrated multi-node energy system model featuring a lot of flexibility options.
Its region, interconnections and components can be adapted flexibly.

The model has been developed in the context of the model comparison project
`FlexMex <https://reiner-lemoine-institut.de/en/flexmex/>`_ and builds upon the open energy modeling
framework _oemof_.

`oemof <https://oemof.org>`_ is an open source, modular toolbox for building energy system models.
It hosts different libraries for different purposes. This model, oemof-flexmex, uses
`oemof.solph <https://oemof-solph.readthedocs.io>`_ for linear optimisation models and
`oemof.tabular <https://oemof-tabular.readthedocs.io>`_ for the handling of input data.


Energy system
=============

In oemof-flexmex an energy system can be composed of

* demands and supplies
* a variety of energy transformers and storages (such as power plants, batteries, renewable energy plants)
* transmission lines, pipelines

Just as its core, `oemof-solph <https://oemof-solph.readthedocs.io/>`_, oemof-flexmex is flexible in modelling
different energy carriers, such as electricity, heat, gas or hydrogen.
It also allows for defining your own components with
the help of `oemof.tabular.facades <https://oemof-tabular.readthedocs.io/en/latest/tutorials/facade-usage.html>`_.


Regions
=======

Each energy system is separated into regions.
Regions can be independent from each other (resulting in a number of isolated energy systems) or linked by transmission lines or pipelines (resulting in a network of energy systems).
Timeseries for demand and supply can be applied to each region seperately.

.. Could regions be seen more general (with different timeseries to model the same energy system in different years)? Would extend the application field.


Scenarios
=========

In oemof-flexmex, each scenario defines its own energy system
which can include different energy carriers (or sectors), primary energy sources, conversion, storage, transmission and demand.
All scenarios are provided with the same set of input data, which consists out of parameters (e.g. capacities) and timeseries
(e.g. energy demand or hourly capacity factors for renewable energies).
Thus, the scenarios help to model different flexibility options within a given energy system.