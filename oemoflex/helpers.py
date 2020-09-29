import os
import shutil
import subprocess

from addict import Dict
import pandas as pd
from pandas.testing import assert_frame_equal
import yaml


def get_experiment_paths(basepath):
    r"""

    Parameters
    ----------
    basepath : str
        Path to experiment's root

    Returns
    -------
    experiment_paths : addict.Dict
        Dictionary containing the experiment's path structure

    """
    module_path = os.path.abspath(os.path.dirname(__file__))
    path_config = os.path.join(module_path, 'experiment_paths.yml')

    with open(path_config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    experiment_paths = {k: os.path.join(basepath, v) for k, v in config.items()}

    experiment_paths = Dict(experiment_paths)

    return experiment_paths


def add_usecase_paths(experiment_paths, name):
    r"""
    Add use case name to several paths.

    NOTE: Can be dropped as soon as directory structure is reordered.

    Parameters
    ----------
    experiment_paths : addict.Dict
        experiment paths

    name : str
        Name of the usecase

    Returns
    -------
    experiment_paths : addict.Dict
        Dictionary containing the experiment's path structure
    """

    experiment_paths['data_preprocessed'] = os.path.join(
        experiment_paths['data_preprocessed'], name)

    experiment_paths['results_optimization'] = os.path.join(
        experiment_paths['results_optimization'], name)

    experiment_paths['results_postprocessed'] = os.path.join(
        experiment_paths['results_postprocessed'], name)

    return experiment_paths


def setup_experiment_paths(name, basepath):
    r"""
    Gets the experiment paths for a given experiment and
    a basepath. If they do not exist, they are created.

    Parameters
    ----------
    name : str
        Name of the use case.

    basepath : path
        basepath of the experiment paths.

    Returns
    -------
    experiment_paths : dict
        Dictionary listing all experiment paths
    """
    experiment_paths = get_experiment_paths(basepath)
    experiment_paths = add_usecase_paths(experiment_paths, name)

    for path in experiment_paths.values():
        if not os.path.exists(path):
            os.makedirs(path)

    return experiment_paths


def load_scalar_input_data(path_data_raw):

    scalars = pd.read_csv(
        path_data_raw,
        header=0,
        na_values=['not considered', 'no value'],
        sep=',',
    )

    return scalars


def get_all_file_paths(dir):
    r"""
    Finds all paths of files in a directory.

    Parameters
    ----------
    dir : str
        Directory

    Returns
    -------
    file_paths : list
        list of str
    """
    # pylint: disable=unused-variable
    file_paths = []
    for dir_path, dir_names, file_names in os.walk(dir):
        for file_name in file_names:
            file_paths.append(os.path.join(dir_path, file_name))

    return file_paths


def check_if_csv_files_equal(csv_file_a, csv_file_b):
    r"""
    Compares two csv files.

    Parameters
    ----------
    csv_file_a
    csv_file_b

    """
    df1 = pd.read_csv(csv_file_a)
    df2 = pd.read_csv(csv_file_b)

    assert_frame_equal(df1, df2)


def check_if_csv_dirs_equal(dir_a, dir_b):
    r"""
    Compares the csv files in two directories and asserts that
    they are equal.

    The function asserts that:

    1. The file names of csv files found in the directories are the same.
    2. The file contents are the same.

    Parameters
    ----------
    dir_a : str
        Path to first directory containing csv files

    dir_b : str
        Path to second directory containing csv files

    """
    files_a = get_all_file_paths(dir_a)
    files_b = get_all_file_paths(dir_b)

    files_a = [file for file in files_a if file.split('.')[-1] == 'csv']
    files_b = [file for file in files_b if file.split('.')[-1] == 'csv']

    files_a.sort()
    files_b.sort()

    f_names_a = [os.path.split(f)[-1] for f in files_a]
    f_names_b = [os.path.split(f)[-1] for f in files_b]

    diff = list(set(f_names_a).symmetric_difference(set(f_names_b)))

    assert not diff,\
        f"Lists of filenames are not the same." \
        f" The diff is: {diff}"

    for file_a, file_b in zip(files_a, files_b):
        try:
            check_if_csv_files_equal(file_a, file_b)
        except AssertionError:
            diff.append([file_a, file_b])

    if diff:
        error_message = ''
        for pair in diff:
            short_name_a, short_name_b = (os.path.join(*f.split(os.sep)[-4:]) for f in pair)
            line = ' - ' + short_name_a + ' and ' + short_name_b + '\n'
            error_message += line

        raise AssertionError(f" The contents of these file are different:\n{error_message}")


def get_dir_diff(dir_a, dir_b, ignore_list=None):
    r"""
    Diff's two directories recursively and returns stdout or stderr

    Parameters
    ----------
    dir_a   Directory left-hand side
    dir_b   Directory right-hand side
    ignore_list  list of patterns to ignore in file names, default: .log

    Returns
    -------
    the STDOUT string of the 'diff' system call
    """

    if ignore_list is None:
        ignore_list = ['*.log']

    # Concatenate patterns to a list of diff args of the form "-x PATTERN"
    exclusions = []
    for pattern in ignore_list:
        # Different from a terminal call, it doesn't work with quotes here:
        # -x "*.log" OR -x '*.log' won't work!
        exclusions.append("-x")
        exclusions.append("{}".format(pattern))

    # Set working directory to the common path for the diff output to be trimmed to what is relevant
    working_directory = os.path.commonpath([dir_a, dir_b])

    # Trim directory path names accordingly to the relative paths
    rel_dir_a = os.path.relpath(dir_a, working_directory)
    rel_dir_b = os.path.relpath(dir_b, working_directory)

    # Call 'diff' recursively (-r), with brief output (-b), ignore exclusion patterns (-x),
    # with relative path names, instead of capture_output=True combine STDOUT and STDERR into one
    diff_process = subprocess.run(
        ["diff", "-rq", *exclusions, rel_dir_a, rel_dir_b],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=working_directory,
        check=False
    )

    return diff_process.stdout.decode('UTF-8')


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
                shutil.rmtree(p)
        else:
            break


def get_name_path_dict(dir):
    r"""
    Returns a dictionary with all the csv files in
    a given directory as keys and their paths as
    values.

    Parameters
    ----------
    dir : path

    Returns
    -------
    name_path_dict : dict
    """
    name_path_dict = {
        file.split('.')[0]: os.path.join(dir, file)
        for file in os.listdir(dir)
        if file.endswith('.csv')
    }

    return name_path_dict


def load_elements(dir):
    r"""

    Parameters
    ----------
    dir : path

    Returns
    -------
    name_dataframe_dict : dict
    """
    name_path_dict = get_name_path_dict(dir)

    name_dataframe_dict = {}
    for name, path in name_path_dict.items():
        name_dataframe_dict[name] = pd.read_csv(path)

    return name_dataframe_dict
