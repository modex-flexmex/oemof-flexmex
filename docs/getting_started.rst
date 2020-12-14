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
1. To use `oemof-solph`, the core of oemoflex, a LP/MILP solver must be installed.
   To use the CBC solver install the `coinor-cbc` package:

   ::

    apt-get install coinor-cbc

2. oemoflex needs `oemof-tabular` for data preprocessing.
   Please install the dev version from github rather than installing from PyPi/pip.

   ::

    git clone https://github.com/oemof/oemof-tabular.git
    cd oemof-tabular/
    git checkout dev
    pip install -e ./


.. for the moment, as a todo:

(for further installing issues and their solution, see https://github.com/modex-flexmex/oemo-flex/issues/12)


Required data
-------------

**Not** provided with the github repository:

* Raw input data, see :ref:`input data format`.
* Output template data, see ...

This data will be provided on github in the future.

Contributing to oemoflex
========================

You can write issues to announce bugs or errors or to propose
enhancements.
