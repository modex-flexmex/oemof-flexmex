import sys
import os

import pandas as pd
from addict import Dict

import oemof_flexmex.plotting.draw as draw
import oemof_flexmex.plotting.prepare as prepare

if __name__ == "__main__":
    # get paths of input data and where to save plots.
    paths = Dict()
    paths.results_joined = sys.argv[1]
    paths.results_joined_plotted = sys.argv[2]

    scenario = "FlexMex2_2"
    onxaxes = 'Scenario'  # either Region or Scenario

    # create directory if it does not exist yet.
    if not os.path.exists(paths.results_joined_plotted):
        os.makedirs(paths.results_joined_plotted)

    scalars = pd.read_csv(paths.results_joined)

    # Retrieve the demand; demand is the same in all scenarios.
    # TODO: This is true for demand, but is it also for the other values imported from this scalars file?
    demand_file = os.path.join(
        os.path.dirname(__file__),
        "../data/In/v0.09/FlexMex2_Scalars_2a.csv",
    )

    df_demand = pd.read_csv(demand_file)

    scalars.rename(columns={"UseCase": "Scenario"}, inplace=True)

    df_in = scalars[scalars.loc[:, "Scenario"].str.contains(scenario)]

    if scenario == "FlexMex2_1":
        (
            df_plot_conversion_electricity,
            electricity_demand,
        ) = prepare.conversion_electricity_FlexMex2_1(df_in, df_demand, onxaxes)

    elif scenario == "FlexMex2_2":
        (
            df_plot_conversion_electricity,
            electricity_demand,
        ) = prepare.conversion_electricity_FlexMex2_2(df_in, df_demand, onxaxes)

        df_plot_conversion_heat, heat_demand = prepare.conversion_heat_FlexMex2_2(
            df_in, df_demand, onxaxes
        )

        df_plot_storage_electricity = prepare.electricity_storage_FlexMex2_2(
            df_in, onxaxes
        )

        df_plot_storage_heat = prepare.heat_storage_FlexMex2_2(
            df_in, onxaxes
        )

    draw.stacked_scalars(
        df_plot_conversion_electricity,
        electricity_demand,
        "Electricity flows " + scenario + onxaxes,
        "electricity in GWh",
        "Scenario",
    )

    if scenario == "FlexMex2_2":
        draw.stacked_scalars(
            df_plot_conversion_heat,
            heat_demand,
            "Heat flows " + scenario + onxaxes,
            "heat in GWh",
            "Scenario",
        )
        draw.stacked_scalars(
            df_plot=df_plot_storage_electricity,
            demand=0,
            title="Electricity storage" + scenario + onxaxes,
            ylabel="Storage in GWh",
            xlabel="Scenario",
        )
        draw.stacked_scalars(
            df_plot=df_plot_storage_heat,
            demand=0,
            title="Heat storage" + scenario + onxaxes,
            ylabel="Storage in GWh",
            xlabel="Scenario",
        )
