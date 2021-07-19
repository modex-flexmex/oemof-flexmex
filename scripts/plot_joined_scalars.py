import os
import sys

import pandas as pd
from addict import Dict

import oemof_flexmex.plotting as plotting
from oemof_flexmex.helpers import read_scalar_input_data

if __name__ == '__main__':
    # get paths of input data and where to save plots.
    paths = Dict()
    paths.results_joined = sys.argv[1]
    paths.results_joined_plotted = sys.argv[2]

    # create directory if it does not exist yet.
    if not os.path.exists(paths.results_joined_plotted):
        os.makedirs(paths.results_joined_plotted)

    scalars = pd.read_csv(paths.results_joined)

    # plot
