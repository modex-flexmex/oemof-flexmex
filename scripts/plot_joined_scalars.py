import sys
import os

import pandas as pd
from addict import Dict

import oemof_flexmex.plotting.draw as draw
import oemof_flexmex.plotting.prepare as prepare
import itertools

if __name__ == "__main__":
    # get paths of input data and where to save plots.
    paths = Dict()
    paths.results_joined = sys.argv[1]
    paths.results_joined_plotted = sys.argv[2]

    scenarios = ["FlexMex2_1", "FlexMex2_2"]
    onxaxes = 'Scenario'  # either Region or Scenario
    regions = ["DE", "PL"]
    objects_all = ["elec", "stor_elec", "costs"]
    objects_2_2 = ["heat", "stor_heat"]
    combinations = list(itertools.product(scenarios, regions, objects_all))
    combinations.extend(list(itertools.product([scenarios[1]], regions, objects_2_2)))


    # create directory if it does not exist yet.
    if not os.path.exists(paths.results_joined_plotted):
        os.makedirs(paths.results_joined_plotted)

    result_scalars = pd.read_csv(paths.results_joined)

    # Retrieve the demand; demand for FlexMex2_1 can also be retrieved from the scalars of FlexMex2_2.
    demand_file = os.path.join(
        os.path.dirname(__file__),
        "../data/In/v0.09/FlexMex2_Scalars_2a.csv",
    )
    df_demand = pd.read_csv(demand_file)

    result_scalars.rename(columns={"UseCase": "Scenario"}, inplace=True)

    for scenario in scenarios:
        df_in = result_scalars[result_scalars.loc[:, "Scenario"].str.contains(scenario)]

        if scenario == "FlexMex2_1":
            (
                df_plot_conversion_electricity_FlexMex2_1,
                electricity_demand_FlexMex2_1,
            ) = prepare.conversion_electricity_FlexMex2_1(df_in, df_demand, onxaxes)

            df_plot_storage_electricity_FlexMex2_1 = prepare.electricity_storage_FlexMex2_1(
                df_in, onxaxes
            )


            df_plot_costs_FlexMex2_1 = prepare.costs_FlexMex2_1(df_in, onxaxes)


        elif scenario == "FlexMex2_2":
            (
                df_plot_conversion_electricity_FlexMex2_2,
                electricity_demand_FlexMex2_2,
            ) = prepare.conversion_electricity_FlexMex2_2(df_in, df_demand, onxaxes)

            df_plot_conversion_heat, heat_demand = prepare.conversion_heat_FlexMex2_2(
                df_in, df_demand, onxaxes
            )

            df_plot_storage_electricity_FlexMex2_2 = prepare.electricity_storage_FlexMex2_2(
                df_in, onxaxes
            )

            df_plot_storage_heat = prepare.heat_storage_FlexMex2_2(
             df_in, onxaxes
            )

            df_plot_costs_FlexMex2_2 = prepare.costs_FlexMex2_2(df_in, onxaxes)

    df_plot_conversion_electricity_FlexMex2_1.to_csv(os.path.join(os.path.dirname(__file__),
                                                               '../results/FlexMex2_plotted/conv_elec_2_1.csv'))
    draw.stacked_scalars(
        df_plot_conversion_electricity_FlexMex2_1,
        electricity_demand_FlexMex2_1,
        "Electricity flows in FlexMex2_1",
        "Electricity in TWh",
        "Scenario",
    )
    df_plot_conversion_electricity_FlexMex2_2.to_csv(os.path.join(os.path.dirname(__file__),
                                                               '../results/FlexMex2_plotted/conv_elec_2_2.csv'))
    draw.stacked_scalars(
        df_plot_conversion_electricity_FlexMex2_2,
        electricity_demand_FlexMex2_2,
        "Electricity flows in FlexMex2_2",
        "Electricity in TWh",
        "Scenario",
    )
    df_plot_conversion_heat.to_csv(os.path.join(os.path.dirname(__file__),
                                                '../results/FlexMex2_plotted/conv_heat_2_2.csv'))
    draw.stacked_scalars(
        df_plot_conversion_heat,
        heat_demand,
        "Heat flows in FlexMex2_2",
        "Heat in TWh",
        "Scenario",
    )
    df_plot_storage_electricity_FlexMex2_1.to_csv(os.path.join(os.path.dirname(__file__),
                                                '../results/FlexMex2_plotted/stor_elec_2_1.csv'))
    draw.stacked_scalars(
        df_plot=df_plot_storage_electricity_FlexMex2_1,
        demand=0,
        title="Electricity storage in FlexMex2_1",
        ylabel="Storage in TWh",
        xlabel="Scenario",
    )
    df_plot_storage_electricity_FlexMex2_2.to_csv(os.path.join(os.path.dirname(__file__),
                                                               '../results/FlexMex2_plotted/stor_elec_2_2.csv'))
    draw.stacked_scalars(
        df_plot=df_plot_storage_electricity_FlexMex2_2,
        demand=0,
        title="Electricity storage in FlexMex2_2",
        ylabel="Storage in TWh",
        xlabel="Scenario",
    )
    df_plot_storage_heat.to_csv(os.path.join(os.path.dirname(__file__),
                                                               '../results/FlexMex2_plotted/stor_heat_2_2.csv'))
    draw.stacked_scalars(
        df_plot=df_plot_storage_heat,
        demand=0,
        title="Heat storage in FlexMex2_2",
        ylabel="Storage in TWh",
        xlabel="Scenario",
    )

    draw.stacked_scalars(
        df_plot=df_plot_costs_FlexMex2_1,
        demand=0,
        title="Total costs in FlexMex2_1",
        ylabel="Costs in mio Euro",
        xlabel="Scenario"
    )

    draw.stacked_scalars(
        df_plot=df_plot_costs_FlexMex2_2,
        demand=0,
        title="Total costs in FlexMex2_2",
        ylabel="Costs in mio Euro",
        xlabel="Scenario"
    )