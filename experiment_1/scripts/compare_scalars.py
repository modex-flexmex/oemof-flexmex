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

    return sc


def calculate_diff_and_relative_deviation(a, b):

    diff = a - b

    dev = diff / a * 100  # decimal to percent

    dev = dev.round(1)

    return diff, dev


sc_oemof = prepare_scalars('oemof', usecase)

sc_compare = prepare_scalars(compare_with, usecase)

diff, relative_dev = calculate_diff_and_relative_deviation(sc_oemof['Value'], sc_compare['Value'])

print(relative_dev.head())

relative_dev.to_csv(f'~/Desktop/relative_dev_{usecase}_oemof_{compare_with}.csv', header=True)
