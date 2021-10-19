import os
import sys
import pandas as pd
from addict import Dict

# Goal: In every scenario two png-files for each selected country (with selection being the same as in the dispatch
# plots), which display the storage level change in the two timeframes selected for the dispatch plots. The file should
# also use the colors and the labels files that are used in the dispatch plots.

# first step: data selection

paths = Dict()
paths.postprocessed = sys.argv[1]
paths.plotted = sys.argv[2]
if not os.path.exists(paths.plotted):
        os.makedirs(paths.plotted)
timeseries_directory = os.path.join(paths.postprocessed, "oemoflex-timeseries/variable")
capacity_data = os.path.join(timeseries_directory, "capacity.csv")
capacities = pd.read_csv(capacity_data)