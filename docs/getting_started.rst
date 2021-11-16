.. _getting_started_label:

~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top

Using oemof-flexmex
===================


Installing the latest (dev) version
-----------------------------------

Clone oemof-flexmex from github:

::

    git clone git@github.com:modex-flexmex/oemof-flexmex.git


Now you can install your local version of oemof-flexmex using pip:

::

    pip install -e <path/to/oemof-flexmex/root/dir>


Requirements
------------
1. To use `oemof-solph`, the core of oemof-flexmex, a LP/MILP solver must be installed.
   To use the CBC solver install the `coinor-cbc` package:

   ::

    apt-get install coinor-cbc

2. oemof-flexmex needs `oemof-tabular` for data preprocessing.
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

* Raw input data, see :ref:`Raw data`.
* Output template data, see :ref:`Postprocessing`.

This data is planned to be published at a later point in time by the project FlexMex.

Contributing to oemof-flexmex
=============================

You can write issues to announce bugs or errors or to propose
enhancements.
