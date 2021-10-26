import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import itertools
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
        elif 'BEV' in i:
            pass
        elif 'H2 cavern' in i:
            ax2 = ax1.twinx()
            ax2.set(ylim=(0, 45))
            ax2.plot(df.index, df[i]/1000, label=i)#, color=colors_odict[i])
            ax2.set_ylabel("Electricity [TWh]")
            ax2.legend(loc='upper right')
        # TODO: set colors as in https://matplotlib.org/stable/gallery/subplots_axes_and_figures/two_scales.html#sphx-glr-gallery-subplots-axes-and-figures-two-scales-py
        else:
            ax1.plot(df.index, df[i], label=i, linewidth=2)#, color=colors_odict[i])
    ax1.legend(loc='upper left')
    ax1.set_ylabel('Electricity [GWh]')
    try:
       ax3.legend()
       ax3.set_ylabel('Heat [GWh]')
    except UnboundLocalError:
        pass
    plt.show()

dir_name = os.path.abspath(os.path.dirname(__file__))
labels_dict = helpers.load_yaml(os.path.join(dir_name, "../oemof_flexmex/model_config/plot_labels.yml"))

if __name__ == "__main__":
# first step: data import
    paths = Dict()
    paths.postprocessed = sys.argv[1]
    paths.plotted = sys.argv[2]
    if not os.path.exists(paths.plotted):
            os.makedirs(paths.plotted)
    timeseries_directory = os.path.join(paths.postprocessed, "oemoflex-timeseries/variable")
    # oemof.solph 0.3.2 used 'capacity' to name this variable, oemof.solph > 0.4.0 renamed it to 'storage level'.
    storage_level_data = os.path.join(timeseries_directory, "capacity.csv")
    capacities = pd.read_csv(storage_level_data, header=[0, 1, 2], parse_dates=[0], index_col=[0])

# second step: data selection: timeframe, country
#TODO: integrate time frame and region definition for dispatch plots and for storage level plots
    timeframe = [
            ("2019-01-01 00:00:00", "2019-01-31 23:00:00"),
            ("2019-07-01 00:00:00", "2019-07-31 23:00:00"),
        ]
    regions = ["DE", "PL"]

    for timeframe, region in itertools.product(timeframe, regions):
        df = pd.DataFrame()
        for column in capacities.columns:
            if region in column[0]:
                df[column] = capacities.loc[:, column]
        df = df / 1000 # from MWh to GWh

        # third step: rename columns into short, understandable labels

        df.columns = plots._rename_by_string_matching(columns=df.columns, labels_dict=labels_dict)

        # fourth step: slice selected timeframes

        df_time_filtered = plots.filter_timeseries(df=df, start_date=timeframe[0], end_date=timeframe[1])

        # fifth step: plot

        plot(df_time_filtered)



    print(timeframe, region)