import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

import pandas as pd


idx = pd.IndexSlice


def stack_plot_with_negative_values(timeseries, ax):
    timeseries_pos = timeseries.copy()
    timeseries_pos[timeseries_pos < 0] = 0
    timeseries_pos = timeseries_pos.loc[:, (timeseries_pos != 0).any(axis=0)]

    timeseries_neg = timeseries.copy()
    timeseries_neg[timeseries_neg >= 0] = 0
    timeseries_neg = timeseries_neg.loc[:, (timeseries_neg != 0).any(axis=0)]

    if not timeseries_pos.empty:
        timeseries_pos.plot.area(ax=ax)
    if not timeseries_neg.empty:
        timeseries_neg.plot.area(ax=ax)
    return ax


def dispatch_plot(df_in, bus, demand, ax=None):

    if not ax:
        fig, ax = plt.subplots()

    df = df_in.copy()

    df_demand = df.pop((bus, demand))

    # df = df.drop(('DE-ch4-extchp', bus), axis=1)

    df *= 1e6  # MW to W

    df_demand *= 1e6  # MW to W

    df_demand.plot.line(ax=ax)

    df.loc[:, idx[bus, :]] *= -1

    df.plot.area(ax=ax)

    ax.legend(
        loc='center left',
        bbox_to_anchor=(1.0, 0.5)
    )

    ax.set_ylabel('Power')

    ax.yaxis.set_major_formatter(
        EngFormatter(unit='W')
    )

    ax.grid()

    return ax
