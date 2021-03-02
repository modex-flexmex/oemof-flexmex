import os
import shutil
import sys

import pandas as pd

results_postprocessed_path = sys.argv[1]
results_comparison_path = sys.argv[2]

if os.path.exists(results_comparison_path):
    print("Overwriting existing results. OK?")

    ok = input("If that is fine, type ok: ")

    if ok == 'ok':
        shutil.rmtree(results_comparison_path)
    else:
        sys.exit(f"You typed '{ok}'. Aborting.")


os.makedirs(results_comparison_path)

scenarios = [
    'FlexMex1_2a',
    'FlexMex1_2b',
    'FlexMex1_2c',
    'FlexMex1_2d',
    'FlexMex1_3',
    'FlexMex1_4a',
    'FlexMex1_4b',
    'FlexMex1_4c',
    'FlexMex1_4d',
    'FlexMex1_4e',
    'FlexMex1_5',
    'FlexMex1_7b',
    'FlexMex1_10',
]


def join_scalars(experiments):
    scalars = []
    for subdir in experiments:
        scalar = pd.read_csv(
            os.path.join(results_postprocessed_path, subdir, 'Scalars.csv'), index_col=[0])
        scalars.append(scalar)

    scalars = pd.concat(scalars)

    return scalars


def copy_timeseries(experiments, fro, to):
    from_to = {os.path.join(fro, e): os.path.join(to, e) for e in experiments}

    for src, dst in from_to.items():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            'Scalars.csv',
            'oemoflex.log*',
            'oemoflex_scalars.csv',
        ))


all_scalars = join_scalars(scenarios)
all_scalars.to_csv(
    os.path.join(results_comparison_path, 'Scalars.csv')
)

copy_timeseries(scenarios, results_postprocessed_path, results_comparison_path)
