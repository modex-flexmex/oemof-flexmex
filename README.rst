~~~~~~~~~~~~~
oemof-flexmex
~~~~~~~~~~~~~

oemof-flexmex (open energy model for FlexMex) is an oemof model built for model comparison within
the Modex project FlexMex.

The model has been developed in the context of the model comparison project FlexMex and builds upon the open energy modeling framework _oemof_.
oemof-flexmex defines a data format to run energy system optimization using oemof.solph and oemof.tabular. It provides pre- and postprocessing routines
to feed the project's harmonized input data into the model and transform the output data into the output data template.

For more information, please visit the `docs <https://oemof-flexmex.readthedocs.io/>`_.

Install oemof-flexmex and its dependencies by setting up a virtual environment and from within call

.. code-block:: bash

    pip install -e oemof_flexmex


Experiment 1
____________


Experiment 1 consists of a list of UseCases. To run a UseCase, type:

.. code-block:: bash

    python experiment_1/scripts/<name-of-UseCase>/<name-of-UseCase>_runall.py


This runs all scripts of the modeling pipeline.

The directory structure reflects the consecutive steps taken from raw data, preprocessing,
optimization, postprocessed data and comparison with the results of other models.

.. code-block:: text

    experiment_1
    ├── 001_data_raw
    ├── 002_data_preprocessed
    ├── 003_results_optimization
    ├── 004_results_data_template
    ├── 005_results_postprocessed
    ├── 006_results_comparison
    └── scripts

A log will be saved in `005_results_postprocessed`.
