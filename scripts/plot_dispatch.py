import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import oemoflex.tools.plots as plots
from oemof_flexmex.model_config import plot_labels, colors_odict
import pandas as pd
from addict import Dict

def sum_demands(data, bus_name, demand_name):
    df_demand = pd.DataFrame()
    for i in data.columns:
        if demand_name in i[1]:
            df_demand[i] = data[i]
            data.drop(columns=[i], inplace=True)
            if len(df_demand.columns) > 1:
                total_demand = df_demand.sum(axis=1)
                data[(bus_name, bus_name + '-demand', 'flow')] = total_demand
    return data

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

    # select carrier
    carrier = "electricity.csv" # "electricity.csv" or "heat_decentral" or "heat_central"

    selected_timeseries_files = [file for file in timeseries_files if carrier in file]

    for bus_file in selected_timeseries_files:

        bus_name = os.path.splitext(bus_file)[0]
        bus_path = os.path.join(timeseries_directory, bus_file)

        data = pd.read_csv(bus_path, header=[0, 1, 2], parse_dates=[0], index_col=[0])

        # prepare dispatch data
        # convert data to SI-unit
        conv_number = 1000
        data = data * conv_number
        sum_demands(data, bus_name=bus_name, demand_name="demand")
        df, df_demand = plots.prepare_dispatch_data(
            data, bus_name=bus_name, demand_name="demand", general_labels_dict=plot_labels
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

        # normal dispatch plot
        # plot one winter and one summer month
        for start_date, end_date in timeframe:
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
            file_name = bus_name + "_" + start_date[5:7] + ".pdf"
            plt.savefig(os.path.join(paths.plotted, file_name), bbox_inches="tight")
            file_name = bus_name + "_" + start_date[5:7] + ".png"
            plt.savefig(os.path.join(paths.plotted, file_name), bbox_inches="tight")
