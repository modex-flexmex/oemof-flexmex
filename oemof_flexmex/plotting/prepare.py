import pandas as pd
import os
from oemoflex.tools.helpers import load_yaml

dir_name = os.path.abspath(os.path.dirname(__file__))
parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))

def onxaxes_preparation(plot_data, onxaxes, scenario_regions):

    if onxaxes == 'Region':
        plot_data = plot_data.loc[plot_data['Scenario'] == scenario_regions, :]
    elif onxaxes == 'Scenario':

        plot_data = plot_data.loc[plot_data['Region'].str.contains('DE'), :] #choose region here
    else:
        print("Only Region or Scenario can be on the x axes.")

    return plot_data


def sum_transmissions(plot_data, scenario,  region):
    df_total_outgoing = plot_data[(plot_data.loc[:, 'Parameter'] == 'Transmission_Flows_Electricity_Grid') &
                                  (plot_data.loc[:, 'Scenario'] == scenario) &
                                  (plot_data.loc[:, 'Region'].str.contains(region + '_'))]

    total_outgoing = -df_total_outgoing['Value'].sum()
    row_total_outgoing = {'Scenario': scenario, 'Region': region, 'Parameter': 'Transmission_Outgoing', 'Unit': 'GWh',
                          'Value': total_outgoing}
    df_total_incoming = plot_data[(plot_data.loc[:, 'Parameter'] == 'Transmission_Flows_Electricity_Grid') &
                                  (plot_data.loc[:, 'Scenario'] == scenario) &
                                  (plot_data.loc[:, 'Region'].str.contains('_' + region))]
    total_incoming = df_total_incoming['Value'].sum()
    row_total_ingoing = {'Scenario': scenario, 'Region': region, 'Parameter': 'Transmission_Incoming', 'Unit': 'GWh',
                         'Value': total_incoming}
    df_total_losses = plot_data[(plot_data.loc[:, 'Parameter'] == 'Transmission_Losses_Electricity_Grid') &
                                (plot_data.loc[:, 'Scenario'] == scenario) &
                                (plot_data.loc[:, 'Region'].str.contains(region))]
    total_losses = -df_total_losses['Value'].sum()
    row_total_losses = {'Scenario': scenario, 'Region': region, 'Parameter': 'Transmission_Losses', 'Unit': 'GWh',
                        'Value': total_losses}

    plot_data.drop(df_total_outgoing.index.to_list(), inplace=True)
    plot_data.drop(df_total_incoming.index.to_list(), inplace=True)
    plot_data.drop(df_total_losses.index.to_list(), inplace=True)
    plot_data = plot_data.append(row_total_outgoing, ignore_index=True) #is substituted by shifted bottom line
    plot_data = plot_data.append(row_total_ingoing, ignore_index=True)
    plot_data = plot_data.append(row_total_losses, ignore_index=True)

    return plot_data

def conversion_electricity_FlexMex2_1(plot_data, df_demand, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_1c')
    plot_data.to_csv('2021-07-03_plot_data.csv')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['conversion_electricity_FlexMex2_1']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario
    if onxaxes == 'Scenario':
        for scenario in ('FlexMex2_1a', 'FlexMex2_1b', 'FlexMex2_1c', 'FlexMex2_1d'):
            plot_data = sum_transmissions(plot_data, scenario, 'DE') #choose region here
        demand = df_demand[(df_demand.loc[:, 'Parameter'] == 'Energy_FinalEnergy_Electricity') &
                               (df_demand.loc[:, 'Region'] == 'DE')].loc[:, 'Value'].iloc[0]
    elif onxaxes == 'Region':
        for region in ('AT', 'BE', 'CH', 'CZ', 'DE', 'DK', 'FR', 'IT', 'LU', 'NL', 'PL'):
            plot_data = sum_transmissions(plot_data, 'FlexMex2_1c', region)
        demand = 0 # demand will not be plotted in regional plots. This could be an interesting task for the future.


    df_plot_conversion_electricity = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                           values=plot_data.Value, aggfunc='mean')
    df_plot_conversion_electricity = \
            df_plot_conversion_electricity.reindex(columns=['EnergyConversion_SecondaryEnergy_Electricity_CH4_GT',
                                                            'EnergyConversion_SecondaryEnergy_Electricity_RE',
                                                            'Transmission_Incoming',
                                                            'EnergyConversion_SecondaryEnergy_Electricity_Slack',
                                                            'EnergyConversion_Curtailment_Electricity_RE',
                                                            'Transmission_Losses',
                                                            'Transmission_Outgoing'
                                                            ])
    return df_plot_conversion_electricity, demand

def conversion_electricity_FlexMex2_2(plot_data, df_demand, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_2c')
    plot_data.to_csv('2021-07-03_plot_data.csv')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['conversion_electricity_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario
    if onxaxes == 'Scenario':
        for scenario in ('FlexMex2_2a', 'FlexMex2_2b', 'FlexMex2_2c', 'FlexMex2_2d'):
            plot_data = sum_transmissions(plot_data, scenario, 'DE')
        demand = 0
        for i in ['Energy_FinalEnergy_Electricity', 'Energy_FinalEnergy_Electricity_H2', 'Transport_AnnualDemand_Electricity_Cars']:
            demand = demand + df_demand[(df_demand.loc[:, 'Parameter'] == i) & (df_demand.loc[:, 'Region'] == 'DE')].loc[:, 'Value'].iloc[0]
            print(demand)
    elif onxaxes == 'Region':
        for region in ('AT', 'BE', 'CH', 'CZ', 'DE', 'DK', 'FR', 'IT', 'LU', 'NL', 'PL'):
            plot_data = sum_transmissions(plot_data, 'FlexMex2_2c', region)
        demand = 0
    df_plot_conversion_electricity = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                           values=plot_data.Value, aggfunc='mean')
#    df_plot_conversion_electricity = \
#            df_plot_conversion_electricity.reindex(columns=['EnergyConversion_SecondaryEnergy_Electricity_CH4_GT',
#                                                            'EnergyConversion_SecondaryEnergy_Electricity_RE',
#                                                            'Transmission_Incoming',
#                                                            'EnergyConversion_SecondaryEnergy_Electricity_Slack',
#                                                            'EnergyConversion_Curtailment_Electricity_RE',
#                                                            'Transmission_Losses',
#                                                            'Transmission_Outgoing'])
    return df_plot_conversion_electricity, demand

def conversion_heat_FlexMex2_2(plot_data, df_demand, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_2c')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['conversion_heat_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario

    demand = 0
    if onxaxes == 'Scenario':
        for i in ['Energy_FinalEnergy_Heat_CHP', 'Energy_FinalEnergy_Heat_HeatPump']:
            demand = demand + df_demand[(df_demand.loc[:, 'Parameter'] == i) & (df_demand.loc[:, 'Region'] == 'DE')].loc[:,
                          'Value'].iloc[0]

    df_plot_conversion_heat = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                           values=plot_data.Value, aggfunc='mean')
#    df_plot_conversion_electricity = \
#            df_plot_conversion_electricity.reindex(columns=[])
    return df_plot_conversion_heat, demand

def electricity_storage_FlexMex2_1(plot_data, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_2c')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['electricity_storage_FlexMex2_1']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_electricity_FlexMex2_1 = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                          values=plot_data.Value, aggfunc='mean')
    return df_plot_storage_electricity_FlexMex2_1

def electricity_storage_FlexMex2_2(plot_data, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_2c')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['electricity_storage_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_electricity_FlexMex2_2 = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                          values=plot_data.Value, aggfunc='mean')
    return df_plot_storage_electricity_FlexMex2_2

def heat_storage_FlexMex2_2(plot_data, onxaxes):
    plot_data = onxaxes_preparation(plot_data, onxaxes, 'FlexMex2_2c')
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['heat_storage_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_heat = pd.crosstab(index=plot_data[onxaxes], columns=plot_data.Parameter,
                                  values=plot_data.Value, aggfunc='mean')
    return df_plot_storage_heat

def generate_labels(df_plot, labels_dict):
    r"""
    Reads in labels for the stacked bar plots for every individual plot

    Parameters
    -------------
    df_plot: pandas.DataFrame
        dataframe to be plotted; column names are the technologies and row names either scenarios or regions.
    labels_dict: pandas.Dictionary (not completely sure about that yet)
        dictionary from stacked_plot_labels.yaml
    Returns
    -------------
    labels: list
        list with labels for one specific plot
    """
    labels = []
    for i in df_plot.columns:
        label = labels_dict[i]
        labels.append(label)
    return labels