import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from addict import Dict
import oemoflex.tools.plots as plots
import oemoflex.tools.helpers as helpers


# Goal: In every scenario two png-files for each selected country (with selection being the same as in the dispatch
# plots), which display the storage level change in the two timeframes selected for the dispatch plots. The file should
# also use the colors and the labels files that are used in the dispatch plots.

def plot(df):
    fig, ax = plt.subplots(figsize=(14, 5), linewidth=20)
    if df.columns.str.contains('heat').any():
        ax1 = plt.subplot(2, 1, 1)
        ax3 = plt.subplot(2, 1, 2, sharex=ax1)
    else:
        ax1 = plt.subplot()
    for i in df.columns:
        if 'heat' in i:
            ax3.plot(df.index, df[i], label=i, linewidth=2)  # , color=colors_odict[i])
        else:
            ax1.plot(df.index, df[i], label=i, linewidth=2)#, color=colors_odict[i])
    ax1.legend()
    try:
       ax3.legend()
    except UnboundLocalError:
        pass
    plt.show()

dir_name = os.path.abspath(os.path.dirname(__file__))
labels_dict = helpers.load_yaml(os.path.join(dir_name, "../oemof_flexmex/model_config/plot_labels.yml"))

# first step: data import
paths = Dict()
paths.postprocessed = sys.argv[1]
paths.plotted = sys.argv[2]
if not os.path.exists(paths.plotted):
        os.makedirs(paths.plotted)
timeseries_directory = os.path.join(paths.postprocessed, "oemoflex-timeseries/variable")
capacity_data = os.path.join(timeseries_directory, "capacity.csv")
capacities = pd.read_csv(capacity_data, header=[0, 1, 2], parse_dates=[0], index_col=[0])

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
        if region in column[0]:
            df[column] = capacities.loc[:, column]

# third step: rename columns into short, understandable labels

    df.columns = plots._rename_by_string_matching(columns=df.columns, labels_dict=labels_dict)

# fourth step: slice selected timeframes

    for i in range(len(timeframe)):
        df_filtered = plots.filter_timeseries(df=df, start_date=timeframe[i][0], end_date=timeframe[i][1])

# fifth step: plot

        plot(df_filtered)