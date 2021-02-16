.. _overview_label:

~~~~~~~~
Overview
~~~~~~~~

oemoflex is sector-integrated multi-node energy system model featuring a lot of flexibility options.
Its region, interconnections and components can be adapted flexibly.


Scenario
=========

In oemoflex, each scenario (called *use case* in the first part of FlexMex project) defines its own energy system
consisting of different types of energy supply, transport and demand.
All scenarios are provided with the same set of timeseries, e.g. for energy demand and renewable energy supply.
Thus, oemoflex helps to model different flexibility options within a given (or future) energy system.


Energy system
=============

In oemoflex an energy system can be composed of

* demands and supplies
* a variety of energy transformers and storages (such as power plants, batteries, renewable energy plants)
* transmission lines, pipelines

Just as its core, `oemof-solph <https://oemof-solph.readthedocs.io/>`_, oemoflex is flexible in modelling
different energy carriers, such as electricity, heat, gas or hydrogen.
It also allows for defining your own components with
the help of `oemof.tabular.facades <https://oemof-tabular.readthedocs.io/en/latest/tutorials/facade-usage.html>`_.


Regions
=======

Each energy system is separated into regions.
Regions can be independent from each other (resulting in a number of isolated energy systems) or linked by transmission lines or pipelines (resulting in a network of energy systems).
Timeseries for demand and supply can be applied to each region seperately.

.. Could regions be seen more general (with different timeseries to model the same energy system in different years)? Would extend the application field.
