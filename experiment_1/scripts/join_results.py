import os
import shutil
import sys

import pandas as pd

from oemoflex.helpers import setup_experiment_paths


# Get paths
basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
exp_paths = setup_experiment_paths('', basepath)

exp_paths.results_comparison = os.path.join(exp_paths.results_comparison, 'oemof')

if os.path.exists(exp_paths.results_comparison):
    print("Overwriting existing results. OK?")

    ok = input("If that is fine, type ok: ")

    if ok == 'ok':
        shutil.rmtree(exp_paths.results_comparison)
    else:
        sys.exit(f"You typed '{ok}'. Aborting.")


os.makedirs(exp_paths.results_comparison)

experiments = [
    'FlexMex1_4a',
    'FlexMex1_4b',
    'FlexMex1_4c',
    'FlexMex1_4d',
    'FlexMex1_5',
    'FlexMex1_10',
]


def join_scalars(experiments):
    all_scalars = []
    for subdir in experiments:
        scalar = pd.read_csv(
            os.path.join('../005_results_postprocessed', subdir, 'Scalars.csv'), index_col=[0])
        all_scalars.append(scalar)

    all_scalars = pd.concat(all_scalars)

    return all_scalars


def copy_timeseries(experiments, fro, to):
    from_to = {os.path.join(fro, e): os.path.join(to, e) for e in experiments}

    for src, dst in from_to.items():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('Scalars.csv', 'oemoflex.log*'))


all_scalars = join_scalars(experiments)
all_scalars.to_csv('../006_results_comparison/oemof/Scalars.csv')

copy_timeseries(experiments, exp_paths.results_postprocessed, exp_paths.results_comparison)
