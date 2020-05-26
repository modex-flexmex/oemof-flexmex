import os
import pandas as pd
from oemof.solph import (Sink, Source, Transformer, Bus, Flow, Model,
                         EnergySystem, Investment)
from oemof.outputlib import views

import matplotlib.pyplot as plt


solver = 'cbc'

periods = 4
datetimeindex = pd.date_range('1/1/2016', periods=periods, freq='H')
energysystem = EnergySystem(timeindex=datetimeindex)
# filename = os.path.join(os.path.dirname(__file__), 'gradient_example.csv')
# data = pd.read_csv(filename, sep=",")

bel = Bus(label='electricity')

energysystem.add(bel)

# an excess and a shortage variable can help to avoid infeasible problems
# energysystem.add(Sink(label='excess_el', inputs={bel: Flow()}))
energysystem.add(
    Source(
        label='shortage_el',
        outputs={bel: Flow(variable_costs=200)}
    )
)

energysystem.add(
    Source(
        label='plants',
        outputs={
            bel: Flow(
                nominal_value=None,
                investment=Investment(),
                # actual_value=[1, 0.5, 0.75, 0.5],
                # fixed=True
                positive_gradient={'ub': 0.2, 'costs': 0},
                negative_gradient = {'ub': 0.2, 'costs': 0}
                )
        }
    )
)

energysystem.add(
    Sink(
        label='demand',
        inputs={
            bel: Flow(
                nominal_value=150,
                actual_value=[1, 0.3, 0.75, 0.2],
                fixed=True
            )
        }
    )
)

# ################################ optimization ###########################

# create optimization model based on energy_system
optimization_model = Model(energysystem=energysystem)

# solve problem
optimization_model.solve(solver=solver,
                         solve_kwargs={'tee': True, 'keepfiles': False})

# write back results from optimization object to energysystem
optimization_model.results()

# ################################ results ################################

# subset of results that includes all flows into and from electrical bus
# sequences are stored within a pandas.DataFrames and scalars e.g.
# investment values within a pandas.Series object.
# in this case the entry data['scalars'] does not exist since no investment
# variables are used
data = views.node(optimization_model.results(), 'electricity')
data['sequences'].info()
print('Optimization successful. Showing some results:')

# see: https://pandas.pydata.org/pandas-docs/stable/visualization.html
node_results_bel = views.node(optimization_model.results(), 'electricity')
node_results_flows = node_results_bel['sequences']

fig, ax = plt.subplots(figsize=(10, 5))
# node_results_flows.plot(ax=ax, kind='bar', stacked=True, linewidth=0, width=1)
node_results_flows.plot(ax=ax, stacked=False)
ax.set_title('Sums for optimization period')
ax.legend(loc='upper right', bbox_to_anchor=(1, 1))
ax.set_xlabel('Energy (MWh)')
ax.set_ylabel('Flow')
plt.legend(loc='center left', prop={'size': 8}, bbox_to_anchor=(1, 0.5))
fig.subplots_adjust(right=0.8)

dates = node_results_flows.index
tick_distance = int(len(dates) / 7) - 1
ax.set_xticks(range(0, len(dates), tick_distance), minor=False)
ax.set_xticklabels(
    [item.strftime('%d-%m-%Y') for item in dates.tolist()[0::tick_distance]],
    rotation=90, minor=False)

plt.show()