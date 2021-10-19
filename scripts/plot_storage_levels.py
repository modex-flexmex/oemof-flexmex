import os
import sys
import pandas as pd
from addict import Dict

# Goal: In every scenario two png-files for each selected country (with selection being the same as in the dispatch
# plots), which display the storage level change in the two timeframes selected for the dispatch plots. The file should
# also use the colors and the labels files that are used in the dispatch plots.

# first step: data import

paths = Dict()
paths.postprocessed = sys.argv[1]
paths.plotted = sys.argv[2]
if not os.path.exists(paths.plotted):
        os.makedirs(paths.plotted)
timeseries_directory = os.path.join(paths.postprocessed, "oemoflex-timeseries/variable")
capacity_data = os.path.join(timeseries_directory, "capacity.csv")
capacities = pd.read_csv(capacity_data, parse_dates=[0], index_col=[0])

# second step: data selection: timeframe, country
#TODO: integrate time frame and region definition for dispatch plots and for storage level plots
timeframe = [
        ("2019-01-01 00:00:00", "2019-01-31 23:00:00"),
        ("2019-07-01 00:00:00", "2019-07-31 23:00:00"),
    ]
regions = ["DE", "FR", "PL"]

for region in regions:
    df = pd.DataFrame()
    for column in capacities.columns:
        if region in column:
            df[column] = capacities.loc[:, column]
    print(df)
