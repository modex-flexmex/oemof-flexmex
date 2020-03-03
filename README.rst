# oemo-flex

## Getting started

Install oemoflex and its dependencies by setting up a virtual environment and from within call

.. code-block:: bash

    pip install -e oemo-flex


### Experiment 1

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
