import sys
import os

import pandas as pd
import matplotlib.pyplot as plt
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
    regions = ["DE"]
    objects_all = ["elec", "stor_elec", "costs"]
    objects_2_2 = ["heat", "stor_heat"]
    combinations = list(itertools.product(scenarios, regions, objects_all))
    combinations.extend(list(itertools.product([scenarios[1]], regions, objects_2_2)))
    print(combinations)

    ylabel_dict = {"elec" : "Electricity in TWh",
                   "stor_elec" : "Storage in TWh",
                   "costs" : "Costs in mio Euro",
                   "heat" : "Heat in TWh",
                   "stor_heat" : "Storage in TWh"}

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


    for (scenario, region, object) in combinations:
        df_in = result_scalars[result_scalars.loc[:, "Scenario"].str.contains(scenario)]
        df_plot, demand = prepare.prepare(df_in, scenario, region, object, df_demand)
        df_plot.to_csv(os.path.join(os.path.dirname(__file__), '../results/FlexMex2_plotted/' + scenario + "_" + object + "_"+region+'.csv'))
        fig = draw.stacked_scalars(df_plot, demand, "Scenario", ylabel_dict[object])
        plt.savefig(
            os.path.join(os.path.dirname(__file__), '../results/FlexMex2_plotted/' + scenario + "_" + object + "_"+region),
            bbox_inches='tight')