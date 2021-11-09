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

def plot_storage_levels(dfs):
    r"""
        Reads in the storage level time series from a dataframe and plots them according to their busses.

        Parameters
        ----------
        dfs : list of pandas.DataFrame()
            List with 1-3 dataframes, each for one bus,
             with storage level time series for a single country.

        Returns
        -------
        figure
        """
    if len(dfs) > 1:
        n_rows = 2
    else:
        n_rows = 1
    fig, axs = plt.subplots(nrows=n_rows, ncols=1, figsize=(14, 5), linewidth=20)

    for i in df_elec.columns:
        axs[0].plot(df_elec.index, df_elec[i], label=i, linewidth=2)
    axs[0].legend()
    if df_heat in dfs:
        for i in df_heat.columns:
            axs[1].plot(df_heat.index, df_heat[i], label=i, linewidth=2)
        axs[1].legend(loc='upper left')
        axs[1].set_ylabel('Electricity [GWh]')
    import pdb
    pdb.set_trace()
    if df_h2 in dfs:
        ax2 = ax[0].twinx()
        ax2.set(ylim=(0, 45))
        ax2.plot(df_h2.index, df_h2[i] / 1000, label=i)  # , color=colors_odict[i])
        ax2.set_ylabel("Electricity [TWh]")
        ax2.legend(loc='upper right')

        # TODO: set colors as in https://matplotlib.org/stable/gallery/subplots_axes_and_figures/two_scales.html#sphx-glr-gallery-subplots-axes-and-figures-two-scales-py

    return fig

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

        # separate df into several dataframes that will be plotted each on a separate axis

        heat_columns = [column for column in df.columns if "heat" in column[0]]
        elec_columns = [column for column in df.columns if
                        "elec" in column[0] and "h2" not in column[0] and "bev" not in column[0]]
        h2_columns = [column for column in df.columns if "h2" in column[0]]


        df_heat = df[heat_columns]
        df_elec = df[elec_columns]
        df_h2 = df[h2_columns]

        dfs = {"df_heat" : df_heat, "df_elec" : df_elec, "df_h2" : df_h2}
        df_dict = {k : df for k, df in dfs.items() if df.empty == False}


        # third step: rename columns into short, understandable labels
        for i in range(len(dfs)):
            dfs[i].columns = plots._rename_by_string_matching(columns=dfs[i].columns, labels_dict=labels_dict)

            # fourth step: slice selected timeframes

            dfs[i] = plots.filter_timeseries(df=dfs[i], start_date=timeframe[0], end_date=timeframe[1])
            import pdb
            pdb.set_trace()
        # fifth step: plot

        figure = plot_storage_levels(dfs)
        plt.savefig(os.path.join(paths.plotted, region+"_"+timeframe[0][5:7]))