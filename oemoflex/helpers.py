import os

import yaml


def get_experiment_paths(name, path_config):
    r"""

    Parameters
    ----------
    name : str
        Name of the scenario
    path_config : str
        Path to the config.yml containing the experiment's path structure

    Returns
    -------
    experiment_paths : dict
        Dictionary containing the experiment's path structure

    """
    abspath = os.path.abspath(os.path.dirname(path_config))

    with open(path_config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    experiment_paths = {k: os.path.join(abspath, v) for k, v in config.items()}

    experiment_paths['data_preprocessed'] = os.path.join(
        experiment_paths['data_preprocessed'], name)

    experiment_paths['results_optimization'] = os.path.join(
        experiment_paths['results_optimization'], name)

    experiment_paths['results_postprocessed'] = os.path.join(
        experiment_paths['results_postprocessed'], name)

    return experiment_paths
