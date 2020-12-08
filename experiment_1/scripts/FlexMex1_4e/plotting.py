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

    df = pd.read_csv(path_df, index_col=0, header=[0, 1, 2])

    ax = dispatch_plot(df.head(168), 'DE-electricity')

    plt.tight_layout()

    plt.show()
