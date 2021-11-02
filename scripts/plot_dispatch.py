import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import oemoflex.tools.plots as plots
from oemof_flexmex.model_config import plot_labels, colors_odict
import pandas as pd
from addict import Dict

def sum_demands(data, bus_name, demand_name):
    d_demand = pd.DataFrame()
    for i in data.columns:
        if demand_name in i[1]:
            d_demand[i] = data[i]
            data.drop(columns=[i], inplace=True)
    total_demand = d_demand.sum(axis=1)
    data[(bus_name, bus_name + '-demand', 'flow')] = total_demand
    return data


def draw_plots(df, start_date, end_date, bus_name, colors_odict):
    r"""
    Creates a dispatch plot for the specified bus and time frame.

    Parameters
    -------------
    df : dataframe
         oemoflex time series data for a single bus in a single region
    start_date : datetime64
        the first hour of the dispatch plot
    end_date : datetime64
        the last hour of the dispatch plot
    bus_name : str
        format: RE-carrier (e.g. "PL-electricity")
    colors_odict : dict
        defines colors for each plotted component with the keys taken from the plot legend

    Returns
    ---------
    fig: fig
        figure containing the dispatch plot
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    # filter timeseries
    df_time_filtered = plots.filter_timeseries(df, start_date, end_date)
    df_demand_time_filtered = plots.filter_timeseries(
        df_demand, start_date, end_date
    )
    # plot time filtered data
    plots.plot_dispatch(
        ax=ax, df=df_time_filtered, df_demand=df_demand_time_filtered, unit="W", colors_odict=colors_odict
    )

    plt.grid()
    plt.title(bus_name + " dispatch", pad=20, fontdict={"size": 22})
    plt.xlabel("Date", loc="right", fontdict={"size": 17})
    plt.ylabel("Power", loc="top", fontdict={"size": 17})
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    # format x-axis representing the dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())

    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.15, box.width, box.height * 0.85]
    )
    # Put a legend below current axis
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        fancybox=True,
        ncol=4,
        fontsize=14,
    )

    fig.tight_layout()
    return fig


if __name__ == "__main__":

    paths = Dict()
    paths.postprocessed = sys.argv[1]
    paths.plotted = sys.argv[2]

    # create the directory plotted where all plots are saved
    if not os.path.exists(paths.plotted):
        os.makedirs(paths.plotted)

    timeseries_directory = os.path.join(paths.postprocessed, "oemoflex-timeseries")
    timeseries_files = os.listdir(timeseries_directory)

    # select timeframe
    timeframe = [
        ("2019-01-01 00:00:00", "2019-01-31 23:00:00"),
        ("2019-07-01 00:00:00", "2019-07-31 23:00:00"),
    ]

    # possible carriers: "electricity.csv", "heat_decentral", "heat_central"
    carriers = ["electricity.csv", "heat_decentral", "heat_central"]
    # possible regions: "AT", "BE", "CH", "CZ", "DK", "DE", "FR", "IT", "LU", "NL", "PL"
    regions = ["DE", "FR", "PL"]


    selected_timeseries_files = [file for file in timeseries_files for carrier in carriers for region in regions
                                 if carrier in file and region in file]

    for bus_file in selected_timeseries_files:

        bus_name = os.path.splitext(bus_file)[0]
        bus_path = os.path.join(timeseries_directory, bus_file)

        data = pd.read_csv(bus_path, header=[0, 1, 2], parse_dates=[0], index_col=[0])

        # prepare dispatch data
        # convert data to SI-unit
        conv_number = 1000
        data = data * conv_number
        data = sum_demands(data, bus_name=bus_name, demand_name="demand")
        df, df_demand = plots.prepare_dispatch_data(
            data, bus_name=bus_name, demand_name="demand", labels_dict=plot_labels
        )

        # interactive plotly dispatch plot
        fig_plotly = plots.plot_dispatch_plotly(
            df=df,
            df_demand=df_demand,
            unit="W",
            colors_odict=colors_odict
        )

        file_name = bus_name + "_dispatch_interactive" + ".html"
        fig_plotly.write_html(
            file=os.path.join(paths.plotted, file_name),
            # include_plotlyjs=False,
            # full_html=False
        )


        for start_date, end_date in timeframe:
            fig = draw_plots(df=df, start_date=start_date, end_date=end_date, bus_name=bus_name, colors_odict=colors_odict)
            file_name = bus_name + "_" + start_date[5:7] + ".png"
            plt.savefig(os.path.join(paths.plotted, file_name), bbox_inches="tight")
            file_name = bus_name + "_" + start_date[5:7] + ".pdf"
            plt.savefig(os.path.join(paths.plotted, file_name), bbox_inches="tight")
