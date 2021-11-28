import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from addict import Dict
from collections import OrderedDict
import oemoflex.tools.plots as plots
import oemoflex.tools.helpers as helpers

from oemof_flexmex.model_config import plot_labels, colors_odict
from oemof_flexmex.model_config.user_definitions import timeframe, regions

def plot_on_axes(ax, df, colors_odict=colors_odict):
    for i in df.columns:
        ax.plot(
            df.index,
            df[i],
            label=i,
            linewidth=2,
            color=colors_odict[i],
        )


def plot_storage_levels(df_dict, colors_odict=colors_odict):
    r"""
    Reads in the storage level time series from a dataframe and plots them according to their busses.

    Parameters
    ----------
    df_dict : dictionary of pandas.DataFrame()
        List with 1-3 dataframes, each for one bus,
         with storage level time series for a single country.

    Returns
    -------
    figure
    """
    if len(df_dict.items()) > 1:
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(14, 5), linewidth=20)
    else:
        fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(14, 5), linewidth=20)

    plot_on_axes(ax1, df_dict["df_elec"])
    ax1.legend(loc="upper left")
    ax1.set_ylabel("Electricity [GWh]")
    ax1.tick_params(axis="y", labelcolor=colors_odict["BAT"])

    if "df_heat" in df_dict.keys():
        plot_on_axes(ax2, df_dict["df_heat"])
        ax2.legend(loc="upper left")
        ax2.set_ylabel("Heat [GWh]")

    if "df_h2" in df_dict.keys():
        ax3 = ax1.twinx()
        ax3.set(ylim=(0, 45))
        #        df_dict["df_h2"] = df_dict["df_h2"] / 1000 # conversion from GWh to TWh
        plot_on_axes(ax3, df_dict["df_h2"])
        ax3.set_ylabel("Electricity [TWh]")
        ax3.legend(loc="upper right")
        ax3.tick_params(axis="y", labelcolor=colors_odict["H2 cavern"])

    return fig


if __name__ == "__main__":
    paths = Dict()
    paths.postprocessed = sys.argv[1]
    paths.plotted = sys.argv[2]
    if not os.path.exists(paths.plotted):
        os.makedirs(paths.plotted)
    timeseries_directory = os.path.join(
        paths.postprocessed, "oemoflex-timeseries/variable"
    )
    # oemof.solph 0.3.2 used 'capacity' to name this variable, oemof.solph > 0.4.0 renamed it to 'storage level'.
    storage_level_data = os.path.join(timeseries_directory, "capacity.csv")
    capacities = pd.read_csv(
        storage_level_data, header=[0, 1, 2], parse_dates=[0], index_col=[0]
    )


    for timeframe, region in itertools.product(timeframe, regions):
        df = pd.DataFrame()
        for column in capacities.columns:
            if region in column[0]:
                df[column] = capacities.loc[:, column]
        df = df / 1000  # conversion from MWh to GWh

        # separate df into several dataframes that will be plotted each on a separate axis
        heat_columns = [column for column in df.columns if "heat" in column[0]]
        elec_columns = [
            column
            for column in df.columns
            if "elec" in column[0] and "h2" not in column[0] and "bev" not in column[0]
        ]
        h2_columns = [column for column in df.columns if "h2" in column[0]]

        # TODO: not sure if it is good to define them here because these dfs remain untouched
        # even when I change those in the dict, which is confusing.
        df_heat = df[heat_columns]
        df_elec = df[elec_columns]
        df_h2 = df[h2_columns] / 1000  # Conversion from GWh to TWh

        dfs = {"df_heat": df_heat, "df_elec": df_elec, "df_h2": df_h2}
        df_dict = {k: df for k, df in dfs.items() if df.empty == False}

        # rename columns into short, understandable labels
        for k, df in df_dict.items():
            df.columns = plots._rename_by_string_matching(
                columns=df.columns, labels_dict=plot_labels
            )

            # slice selected timeframes

            df_dict[k] = plots.filter_timeseries(
                df=df, start_date=timeframe[0], end_date=timeframe[1]
            )

        figure = plot_storage_levels(df_dict)
        plt.savefig(os.path.join(paths.plotted, region + "_" + timeframe[0][5:7]))
