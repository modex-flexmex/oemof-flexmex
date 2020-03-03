import os
import shutil

import pandas as pd
from pandas.util.testing import assert_frame_equal
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


def get_all_file_paths(dir):
    # pylint: disable=unused-variable
    file_paths = []
    for dir_path, dir_names, file_names in os.walk(dir):
        for file_name in file_names:
            file_paths.append(os.path.join(dir_path, file_name))

    return file_paths


def check_if_csv_files_equal(csv_file_a, csv_file_b):
    df1 = pd.read_csv(csv_file_a)
    df2 = pd.read_csv(csv_file_b)

    assert_frame_equal(df1, df2)


def check_if_csv_dirs_equal(dir_a, dir_b, ignore='log'):
    files_a = get_all_file_paths(dir_a)
    files_b = get_all_file_paths(dir_b)
    files_a = [file for file in files_a if file.split('.')[-1] not in ignore]
    files_b = [file for file in files_b if file.split('.')[-1] not in ignore]

    files_a.sort()
    files_b.sort()

    for file_a, file_b in zip(files_a, files_b):
        filename_a = os.path.split(file_a)[-1]
        filename_b = os.path.split(file_b)[-1]

        assert filename_a == filename_b, \
            f"{filename_a} and {filename_b} do not have the same name."

        check_if_csv_files_equal(file_a, file_b)


def delete_empty_subdirs(path):
    r"""Deletes empty subdirectories in path"""
    while True:
        to_delete = []
        for root, dirs, _ in os.walk(path):
            for d in dirs:
                full_path = os.path.join(root, d)
                if not os.listdir(full_path):
                    to_delete.append(full_path)

        if to_delete:
            for p in to_delete:
                print(p)
                shutil.rmtree(p)
        else:
            break
