import os
import pandas as pd

from oemoflex.plotting import dispatch_plot
from oemoflex.helpers import setup_experiment_paths


if __name__ == '__main__':


    name = 'FlexMex1_4e'

    exp_paths = setup_experiment_paths(name)

    path_df = os.path.join(
        exp_paths.results_postprocessed,
        'oemoflex-sequences',
        'DE-electricity.csv'
    )

    pd.read_csv(path_df)
