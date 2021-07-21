

import os
import pdb

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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


# from analysis import colors


def import_countrydatasheet_data(sheet_name, last_row_to_skip, number_of_rows):
    r"""
    Import a specific range of data from energy_statistical_countrydatasheets.xlsx. The countrydatasheet is a publication
    from the European Commission collecting various energy-related data from all European countries.
    """
    data = os.path.join(os.path.dirname(__file__), '../data/energy_statistical_countrydatasheets.xlsx')
    df = pd.read_excel(data, sheet_name=sheet_name, index_col=2, usecols="A:AG",
                       skiprows=lambda x: x in range(0, last_row_to_skip) and x != 7, nrows=number_of_rows, engine='openpyxl')
    df1 = df.drop([8, 'Unnamed: 1'], axis=1)
    return df1, sheet_name



def preprocessing_stacked_scalars(plot_data, factor, onxaxes): # put a factor here that the values should be devided be, e.g. 1 or 1000
    r"""
    Functions for creating stacked bar plots from a table in the scalars-table-format

    Parameters
    --------------
    plot_data: pandas.DataFrame
        Input data to be plotted. They must contain only data for one single country.
    factor: int or float
        The factor by which all data should be divided, e.g. for conversion from MW to GW.
    onxaxes: str; either 'Scenario' or 'Region'
        If Scenario is chosen, all Scenarios (a-d) for Germany are plotted; if 'Region' is chosen, only the scenario
        'c' is plotted but for all countries.

    Returns
    -------------
    df_plot_conversion_heat: pandas.DataFrame
        Heat conversion data ready to be plotted in the 'stacked_scalars' function. This method is outdated because
        it has been replaced by a function in 'prepare.py'.
    df_plot_conversion_electricity: pandas.DataFrame
        Same as above but for electricity
    df_plot_storage_heat: pandas.DataFrame
        Same as above, for heat storage
    df_plot_storage_electricity: pandas.DataFrame
        Same as above, for electricity storage
    df_plot_capacity_electricity: pandas.DataFrame
        Electricity conversion data ready to be plotted in the 'stacked_scalars' function.
    df_plot_capacity_heat: pandas.DataFrame
        Heat conversion data ready to be plotted in the 'stacked_scalars' function.
    """
    df_plot_conversion_heat = pd.DataFrame()
    df_plot_conversion_electricity = pd.DataFrame()
    df_plot_storage_heat = pd.DataFrame()
    df_plot_storage_electricity = pd.DataFrame()
    df_plot_capacity_heat = pd.DataFrame()
    df_plot_capacity_electricity = pd.DataFrame()

    if plot_data['Parameter'].str.contains('EnergyConversion_Capacity_Electricity').any():
        plot_data['Parameter'] = plot_data['Parameter'].str.replace('EnergyConversion_Capacity_Electricity_', '')
    if plot_data['Parameter'].str.contains('EnergyConversion_').any():
        plot_data['Parameter'] = plot_data['Parameter'].str.replace('EnergyConversion_', '')
    if plot_data['Parameter'].str.contains('Storage').any():
        # store storage in a separate dataframe ...
        df_storage = plot_data.loc[plot_data['Parameter'].str.contains('Storage'), :]
        # df_storage['Parameter'] = df_storage['Parameter'].str.replace('Storage_Capacity_Electricity_', '')
        # Show only output and losses and not inputs; capacities should be plotted separately
        df_storage = df_storage.loc[~df_storage['Parameter'].str.contains('Input|Capacity'), :]
        # ... and remove it from the original one
        plot_data = plot_data[~plot_data['Parameter'].str.contains('Storage')]
        if df_storage['Parameter'].str.contains('Heat').any():
            df_storage_heat = df_storage.loc[df_storage['Parameter'].str.contains('Heat'), :]
            df_plot_storage_heat = pd.crosstab(index=df_storage_heat[onxaxes], columns=df_storage_heat.Parameter,
                                               values=df_storage_heat.Value / factor, aggfunc='mean')

        df_storage_electricity = df_storage[~df_storage['Parameter'].str.contains('Heat')]
        df_plot_storage_electricity = pd.crosstab(index=df_storage_electricity[onxaxes],
                                                      columns=df_storage_electricity.Parameter,
                                                      values=df_storage_electricity.Value / factor, aggfunc='mean')
    # do the same for separating heat and electricity, both for storage and for energy conversion
    # It would be better to use a for loop for this (for dataframe in (plot_data, df_storage): ...
    if plot_data['Parameter'].str.contains('SecondaryEnergy_Heat').any():
        df_conversion_heat = plot_data.loc[plot_data['Parameter'].str.contains('SecondaryEnergy_Heat|Energy_FinalEnergy_Heat'), :]
        df_plot_conversion_heat = pd.crosstab(index=df_conversion_heat[onxaxes], columns=df_conversion_heat.Parameter,
                                              values=df_conversion_heat.Value / factor, aggfunc='mean')
    df_conversion_electricity = plot_data[~plot_data['Parameter'].str.contains('SecondaryEnergy_Heat|Energy_FinalEnergy_Heat')]
    if plot_data['Parameter'].str.contains('Capacity_Heat').any():
        df_capacity_heat = plot_data.loc[plot_data['Parameter'].str.contains('Capacity_Heat')]
        df_plot_capacity_heat = pd.crosstab(index=df_capacity_heat[onxaxes], columns=df_capacity_heat.Parameter,
                                            values=df_capacity_heat.Value / factor, aggfunc='mean')
        df_capacity_electricity = plot_data.loc[~plot_data['Parameter'].str.contains('Capacity_Heat')]
        df_plot_capacity_electricity = pd.crosstab(index=df_capacity_electricity[onxaxes], columns=df_capacity_electricity.Parameter,
                                            values=df_capacity_electricity.Value / factor, aggfunc='mean')

#        df_plot_conversion_heat = pd.crosstab(index=df_conversion_heat.UseCase, columns=df_conversion_heat.Parameter,
#                                       values=df_conversion_heat.Value / factor, aggfunc='mean')
#        df_plot_conversion_electricity = pd.crosstab(index=df_conversion_electricity.UseCase, columns=df_conversion_electricity.Parameter,
#                                       values=df_conversion_electricity.Value / factor, aggfunc='mean')

    df_plot_conversion_electricity = pd.crosstab(index=df_conversion_electricity[onxaxes], columns=df_conversion_electricity.Parameter,
                                           values=df_conversion_electricity.Value / factor, aggfunc='mean')

    return df_plot_conversion_heat, df_plot_conversion_electricity, df_plot_storage_heat, df_plot_storage_electricity, \
           df_plot_capacity_electricity, df_plot_capacity_heat

# The above preprocessing function has become too complicated and doesn't work for electricity flows in FlexMex2_2 now.
# This is why I now write explicit functions for all the plot_dataframes I need.


def stacked_scalars(df_plot, demand, title, ylabel, xlabel):
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
        new_df.plot(kind='bar', stacked=True, bottom = df_plot.loc[:, 'Transmission_Outgoing'], color=colors_odict)
    else:
        labels = generate_labels(df_plot, labels_dict)
        df_plot.plot(kind='bar', stacked=True, color=colors_odict)

    #df_plot = df_plot.drop('Transmission_Outgoing', axis = 1)

    if demand > 0:
        plt.hlines(demand, plt.xlim()[0], plt.xlim()[1])#, label='Demand')
        labels.insert(0, 'Demand')
        print(demand)
    plt.axhline(0, color='black', label='_nolegend_')
    #labels.insert(1, None)
    plt.title(title)
    plt.xlabel(xlabel, fontsize = 12)
    plt.ylabel(ylabel, fontsize = 12)
    plt.legend(labels, bbox_to_anchor=(1,1), loc="upper left")
    plt.savefig(os.path.join(os.path.dirname(__file__), '../../results/FlexMex2_plotted/' + title), bbox_inches='tight')

def preprocessing_timeseries (inputdatapath, type):
    input_file = os.path.join(os.path.dirname(__file__),
                              inputdatapath)
    df_in = pd.read_csv(input_file, index_col='timeindex')
    df_in = df_in[type]
    return(df_in)

def plot_timeseries (df_in, timeframe, label, title, xlabel, ylabel):
    fig = plt.figure()
    fig, ax = plt.subplots()
    if timeframe == 'weeks':
        ax.plot(df_in.iloc[0:168 * 4], label=label)
    elif timeframe == 'year':
        # one point for every day
        # ax.plot(df_in.iloc[range(0, 8760, 24)], label=label)
        # daily averages
        ar = np.zeros(shape=365)

        for i in range (0, 365):
            start = i*24
            end = (i+1)*24
            day_mean = df_in.iloc[range(start, end)].mean()
            ar[i] = day_mean
        ax.plot(ar, label = label)
    # in order to show larger tendencies in wind power, here is another kind of plot with weekly averages
    elif timeframe == 'year-rough':
        ar = np.zeros(shape=52)
        for i in range (0, 52):
            start = i*168
            end = (i+1)*168
            week_mean = df_in.iloc[range(start, end)].mean()
            ar[i] = week_mean
        ax.plot(ar, label = label)
    elif timeframe == 'day':
        ax.plot(df_in.iloc[range(6*168, 6*168 + 24)], label=label) # the first day of the sixth week - the choice of the day is arbitrary
    else:
        print('Only day, weeks, year and year-rough are possible timeframes')
    ax.set_title(title)
    ax.set_ylabel(ylabel, fontsize = 12)
    ax.set_xlabel(xlabel, fontsize = 12)
    ax.legend()  # loc='upper center', bbox_to_anchor=(1.45, 0.8), shadow=True, ncol=1)
    plt.savefig(os.path.join(os.path.dirname(__file__), '../results/timeseries/' + title), bbox_inches='tight')
    # TODO: adjust x-axis depending on timeframe (days or months would be good, not hours)