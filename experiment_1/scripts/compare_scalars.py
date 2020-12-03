import os
import pandas as pd


compare_with = 'REMix'

usecases = [
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

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
comparison_path = os.path.join(basepath, '006_results_comparison')


def load_scalars(model, base_path=comparison_path):
    r""" Loads Scalars.csv. Default base_path is comparison_path"""

    sc_path = os.path.join(base_path, model, 'Scalars.csv')

    sc = pd.read_csv(sc_path)

    return sc


def filter_by_usecase(sc_in, usecase):
    r""" Filter scalars for UseCase """

    sc = sc_in.copy()  # copy to avoid unintended overwriting

    sc = sc.loc[sc['UseCase'] == usecase]

    return sc


def prepare_scalars(model, usecase, index=None):
    r""" Load scalars, filter for usecase, sort and set name of pd.Series. """

    if index is None:
        index = ['UseCase', 'Region', 'Year', 'Parameter']

    sc = load_scalars(model)

    sc = filter_by_usecase(sc, usecase)

    sc.set_index(index, inplace=True)  # set index to the columns that are common

    sc.sort_index(inplace=True)

    sc = sc['Value']

    sc.name = f'value_{model}'

    return sc


def calculate_diff_and_relative_deviation(a, b):
    r""" Takes two pd.Series and returns a pd.DataFrame containing the original
    Series' as columns as well as absolute and relative differences. """

    abs_diff = a - b

    rel_diff = abs_diff / b

    abs_diff.name = 'abs_mean_diff'

    rel_diff.name = 'rel_mean_diff'

    diff = pd.concat([b, a, abs_diff, rel_diff], 1)

    return diff


def average_per_region(diff_in):
    r""" Takes the regional average of a pd.DataFrame. """

    mean_diff = diff_in.copy()

    by = list(mean_diff.index.names)

    by.remove('Region')  # groupby all index levels apart from 'Region'

    mean_diff = mean_diff.groupby(by=by).mean()

    return mean_diff


for usecase in usecases:
    print(f"Comparing usecase {usecase}.")
    sc_oemof = prepare_scalars('oemof', usecase)
    sc_compare = prepare_scalars(compare_with, usecase)

    if sc_compare.empty:
        continue

    sc_oemof = average_per_region(sc_oemof)
    sc_compare = average_per_region(sc_compare)

    mean_diff = calculate_diff_and_relative_deviation(sc_oemof, sc_compare)

    mean_diff = mean_diff.round(3)

    print('\n##### diff region average #################################')
    print(mean_diff.head())

    save_to_path = os.path.join(comparison_path, f'Relative_dev_{usecase}_oemof_{compare_with}.csv')
    mean_diff.to_csv(save_to_path, header=True)
