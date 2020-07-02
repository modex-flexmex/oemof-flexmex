import os
import pandas as pd


compare_with = 'REMix'
usecase = 'FlexMex1_4b'

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
comparison_path = os.path.join(basepath, '006_results_comparison')


def load_oemof_and_comparision_scalars(model):

    sc_path = os.path.join(comparison_path, model, 'Scalars.csv')

    sc = pd.read_csv(sc_path)

    return sc


def filter_by_usecase(sc_in, usecase):

    sc = sc_in.copy()  # copy to avoid inintended overwriting

    sc = sc.loc[sc['UseCase'] == usecase]

    return sc


def prepare_scalars(model, usecase, index=['UseCase', 'Region', 'Year', 'Parameter']):

    sc = load_oemof_and_comparision_scalars(model)

    sc = filter_by_usecase(sc, usecase)

    sc.set_index(index, inplace=True)  # set index to the columns that are common

    sc.sort_index(inplace=True)

    sc = sc['Value']

    sc.name = f'value_{model}'

    return sc


def calculate_diff_and_relative_deviation(a, b):

    abs_diff = a - b

    rel_diff = abs_diff / a * 100  # decimal to percent

    rel_diff = rel_diff.round(1)

    abs_diff.name = 'abs_diff'

    rel_diff.name = 'rel_diff'

    diff = pd.concat([a, b, abs_diff, rel_diff], 1)

    return diff


sc_oemof = prepare_scalars('oemof', usecase)

sc_compare = prepare_scalars(compare_with, usecase)

diff = calculate_diff_and_relative_deviation(sc_oemof, sc_compare)

print(diff.head())

save_to_path = os.path.join(comparison_path, f'Relative_dev_{usecase}_oemof_{compare_with}.csv')
diff.to_csv(save_to_path, header=True)
