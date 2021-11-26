import pandas as pd
import os
from oemoflex.tools.helpers import load_yaml

dir_name = os.path.abspath(os.path.dirname(__file__))
parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))

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
#    df_total_losses = plot_data[(plot_data.loc[:, 'Parameter'] == 'Transmission_Losses_Electricity_Grid') &
#                                (plot_data.loc[:, 'Scenario'] == scenario) &
#                                (plot_data.loc[:, 'Region'].str.contains(region))]
#    total_losses = -df_total_losses['Value'].sum()
#    row_total_losses = {'Scenario': scenario, 'Region': region, 'Parameter': 'Transmission_Losses', 'Unit': 'GWh',
#                        'Value': total_losses}

    plot_data.drop(df_total_outgoing.index.to_list(), inplace=True)
    plot_data.drop(df_total_incoming.index.to_list(), inplace=True)
#    plot_data.drop(df_total_losses.index.to_list(), inplace=True)
    plot_data = plot_data.append(row_total_outgoing, ignore_index=True) #is substituted by shifted bottom line
    plot_data = plot_data.append(row_total_ingoing, ignore_index=True)
#    plot_data = plot_data.append(row_total_losses, ignore_index=True)

    return plot_data

def make_losses_negative(plot_data):
    # TODO: This is very bad style. Generally, one shouldn't iterate over rows. -> improve
    for i in range(len(plot_data)):
        if 'Losses' in plot_data.loc[:, 'Parameter'].iloc[i]:
            plot_data.iloc[i, plot_data.columns.get_loc('Value')] = plot_data.iloc[
                                                                        i, plot_data.columns.get_loc('Value')] * -1
    return plot_data

def prepare(plot_data, scenario, region, object, df_demand=False):
    print("Preparing data for " + object + " in " + region + " for " + scenario)
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters[object + "_" + scenario]]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # TODO: Here the table should be sorted according to the order in the parameters.yaml file.
    plot_data = make_losses_negative(plot_data)

    if object == "elec":
        for step in ["a", "b", "c", "d"]:
            plot_data = sum_transmissions(plot_data, scenario + step, region)
    plot_data = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                                 values=plot_data.Value / 1000, aggfunc='mean')


    if object == "costs":
        plot_data = plot_data / 1000  # conversion from 1000 Euro to mio. Euro
    if df_demand is not False:  # This doesn't work.
        if scenario == "FlexMex2_1" and object == "elec":
            demand_list = ["Energy_FinalEnergy_Electricity"]
        elif scenario == "FlexMex2_2" and object == "elec":
            demand_list = ["Energy_FinalEnergy_Electricity", 'Energy_FinalEnergy_Electricity_H2', 'Transport_AnnualDemand_Electricity_Cars']
        elif scenario == "FlexMex2_2" and object == "heat":
            demand_list = ['Energy_FinalEnergy_Heat_CHP', 'Energy_FinalEnergy_Heat_HeatPump']
        else:
            demand_list = []
            #  print ("This scenario and / or object is not yet implemented in the scalar plotting function.")
        demand = 0
        for parameter in demand_list:
            demand = demand + df_demand[(df_demand.loc[:, 'Parameter'] == parameter) & (df_demand.loc[:, 'Region'] == region)].loc[:, 'Value'].iloc[0]
    print(demand)
    return plot_data, demand

def conversion_electricity_FlexMex2_1(plot_data, df_demand, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['elec_FlexMex2_1']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario
    for scenario in ('FlexMex2_1a', 'FlexMex2_1b', 'FlexMex2_1c', 'FlexMex2_1d'):
        plot_data = sum_transmissions(plot_data, scenario, region)
        demand = df_demand[(df_demand.loc[:, 'Parameter'] == 'Energy_FinalEnergy_Electricity') &
                               (df_demand.loc[:, 'Region'] == region)].loc[:, 'Value'].iloc[0]


    df_plot_conversion_electricity = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                           values=plot_data.Value / 1000, aggfunc='mean')
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

def conversion_electricity_FlexMex2_2(plot_data, df_demand, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['elec_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario
    for scenario in ('FlexMex2_2a', 'FlexMex2_2b', 'FlexMex2_2c', 'FlexMex2_2d'):
        plot_data = sum_transmissions(plot_data, scenario, region)
    demand = 0
    for i in ['Energy_FinalEnergy_Electricity', 'Energy_FinalEnergy_Electricity_H2', 'Transport_AnnualDemand_Electricity_Cars']:
        demand = demand + df_demand[(df_demand.loc[:, 'Parameter'] == i) & (df_demand.loc[:, 'Region'] == region)].loc[:, 'Value'].iloc[0]
    print(demand)
    df_plot_conversion_electricity = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                           values=plot_data.Value / 1000, aggfunc='mean')
#    df_plot_conversion_electricity = \
#            df_plot_conversion_electricity.reindex(columns=['EnergyConversion_SecondaryEnergy_Electricity_CH4_GT',
#                                                            'EnergyConversion_SecondaryEnergy_Electricity_RE',
#                                                            'Transmission_Incoming',
#                                                            'EnergyConversion_SecondaryEnergy_Electricity_Slack',
#                                                            'EnergyConversion_Curtailment_Electricity_RE',
#                                                            'Transmission_Losses',
#                                                            'Transmission_Outgoing'])
    return df_plot_conversion_electricity, demand

def conversion_heat_FlexMex2_2(plot_data, df_demand, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['heat_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    # sum all outgoing and all ingoing transmissions for each scenario

    demand = 0
    for i in ['Energy_FinalEnergy_Heat_CHP', 'Energy_FinalEnergy_Heat_HeatPump']:
        demand = demand + df_demand[(df_demand.loc[:, 'Parameter'] == i) & (df_demand.loc[:, 'Region'] == region)].loc[:,
                        'Value'].iloc[0]

    df_plot_conversion_heat = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                           values=plot_data.Value / 1000, aggfunc='mean')
#    df_plot_conversion_electricity = \
#            df_plot_conversion_electricity.reindex(columns=[])
    return df_plot_conversion_heat, demand

def electricity_storage_FlexMex2_1(plot_data, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['stor_elec_FlexMex2_1']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_electricity_FlexMex2_1 = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                          values=plot_data.Value / 1000, aggfunc='mean')
    return df_plot_storage_electricity_FlexMex2_1

def electricity_storage_FlexMex2_2(plot_data, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['stor_elec_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_electricity_FlexMex2_2 = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                          values=plot_data.Value / 1000, aggfunc='mean')
    return df_plot_storage_electricity_FlexMex2_2

def heat_storage_FlexMex2_2(plot_data, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['stor_heat_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_storage_heat = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                  values=plot_data.Value / 1000, aggfunc='mean')
    return df_plot_storage_heat

def costs_FlexMex2_1(plot_data, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['costs_FlexMex2_1']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_costs_FlexMex2_1 = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                       values=plot_data.Value / 1000000, aggfunc='mean')
    return df_plot_costs_FlexMex2_1

def costs_FlexMex2_2(plot_data, region):
    plot_data = plot_data.loc[plot_data['Region'].str.contains(region), :]
    parameters = load_yaml(os.path.join(dir_name, "parameters.yaml"))
    parameters = [*parameters['costs_FlexMex2_2']]
    plot_data = plot_data.loc[plot_data['Parameter'].isin(parameters)]
    df_plot_costs_FlexMex2_2 = pd.crosstab(index=plot_data["Scenario"], columns=plot_data.Parameter,
                                       values=plot_data.Value / 1000000, aggfunc='mean')
    return df_plot_costs_FlexMex2_2

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