import os

import matplotlib.pyplot as plt
import pandas as pd

from oemoflex.plotting import dispatch_plot
from oemoflex.helpers import setup_experiment_paths


if __name__ == '__main__':

    name = 'FlexMex1_4e'

    exp_paths = setup_experiment_paths(name)

    path_df = os.path.join(
        exp_paths.results_postprocessed,
        'oemoflex-timeseries',
        'DE-electricity.csv'
    )

    def plot(start, end, bus='DE-electricity'):
        fig, ax = plt.subplots(figsize=(12, 5))

        dispatch_plot(df.iloc[start:end, :], bus=bus, demand=bus + '-demand', ax=ax)

        plt.tight_layout()

        plt.savefig(os.path.join(exp_paths.plots, f'{bus}-{start}-{end}.png'))

    df = pd.read_csv(
        path_df,
        index_col=0,
        header=[0, 1, 2],
        parse_dates=True,
    )

    plot(0, 168, 'DE-electricity')

    plot(860, 1008, 'DE-electricity')

    path_df = os.path.join(
        exp_paths.results_postprocessed,
        'oemoflex-timeseries',
        'DE-heat.csv'
    )

    df = pd.read_csv(path_df, index_col=0, header=[0, 1, 2])

    plot(0, 168, 'DE-heat')

    plot(860, 1008, 'DE-heat')
