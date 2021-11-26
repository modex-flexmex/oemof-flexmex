

import os
import pdb

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.ticker import EngFormatter
from collections import OrderedDict
from oemoflex.tools.helpers import load_yaml
from oemof_flexmex.plotting.prepare import generate_labels

dir_name = os.path.abspath(os.path.dirname(__file__))
colors_csv = pd.read_csv(
    os.path.join(dir_name, "colors.csv"), header=[0], index_col=[0])

colors_csv = colors_csv.T
colors_odict = OrderedDict()
for i in colors_csv.columns:
    colors_odict[i] = colors_csv.loc["Color", i]


def stacked_scalars(df_plot, demand, xlabel, ylabel):
    r"""
    Plots stacked scalars.

    Parameters
    --------------
    df_plot: pandas.DataFrame
        Must have scenarios on the rows and technologies in the columns.
    demand: int or float
        Demand which will be plotted as a horizontal line in the bar plot.
    title: str
        Title for the bar plot.
    ylabel: str
    xlabel: str
    """
    df_plot.dropna(axis=1, how='all', inplace = True)
    # load labels dict
    labels_dict = load_yaml(os.path.join(dir_name, "stacked_plot_labels.yaml"))

    if df_plot.columns.str.contains('Transmission_Outgoing').any():
        new_df = df_plot.drop('Transmission_Outgoing', axis = 1)
        labels = generate_labels(new_df, labels_dict)
        ax = new_df.plot(kind='bar', stacked=True, bottom = df_plot.loc[:, 'Transmission_Outgoing'], color=colors_odict)
    else:
        labels = generate_labels(df_plot, labels_dict)
        ax = df_plot.plot(kind='bar', stacked=True, color=colors_odict)

    #df_plot = df_plot.drop('Transmission_Outgoing', axis = 1)

    if demand > 0:
        # convert from GWh to TWh
        demand = demand/1000
        ax.hlines(demand, plt.xlim()[0], plt.xlim()[1])#, label='Demand')
        labels.insert(0, 'Demand')
    ax.axhline(0, color='black', label='_nolegend_')
    #labels.insert(1, None)

    plt.xlabel(xlabel, fontsize = 12)
    plt.ylabel(ylabel, fontsize = 12)
    plt.legend(labels, bbox_to_anchor=(1,1), loc="upper left")

    fig = ax.get_figure()

    return fig
