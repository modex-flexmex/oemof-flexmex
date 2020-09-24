.. _getting_started_label:

~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

oemoflex is a model of the integrated European energy system, featuring many flexibility options.

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top

Using oemoflex
==============


Installing the latest (dev) version
-----------------------------------

Clone oemoflex from github:

::

    git clone git@github.com:modex-flexmex/oemoflex.git


Now you can install it your local version of oemoflex using pip:

::

    pip install -e <path/to/oemoflex/root/dir>


Requirements
------------
To use `oemof-solph`, the core of oemoflex, a LP/MILP solver must be installed.

To use the CBC solver install the `coinor-cbc` package

::

    apt-get install coinor-cbc


.. for the moment, as a todo:

(for further installing issues and their solution, see https://github.com/modex-flexmex/oemo-flex/issues/12)


Required data
-------------

**Not** provided with the github repository:

* Raw input data, see ...
* Output template data, see ...


Contributing to oemoflex
========================

You can write issues to announce bugs or errors or to propose
enhancements.
