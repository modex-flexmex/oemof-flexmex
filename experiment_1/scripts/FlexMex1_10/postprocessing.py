import os

import pandas as pd

from oemof.solph import EnergySystem
from oemoflex.postprocessing import \
    create_postprocessed_results_subdirs, get_sequences_by_tech, get_capacities, \
    get_summed_sequences,\
    get_transmission_losses, get_storage_losses, get_emissions,\
    map_to_flexmex_results, get_varom_cost
from oemoflex.helpers import \
    setup_experiment_paths, load_elements


name = 'FlexMex1_10'

year = 2050

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
exp_paths = setup_experiment_paths(name, basepath)

create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

# load scalars templates
flexmex_scalars_template = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
flexmex_scalars_template = flexmex_scalars_template.loc[flexmex_scalars_template['UseCase'] == name]

# load mapping
# TODO

# Load preprocessed elements
prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

# restore EnergySystem with results
es = EnergySystem()
es.restore(exp_paths.results_optimization)

# format results sequences
sequences_by_tech = get_sequences_by_tech(es.results)
sequences_by_tech['electricity-transmission'].to_csv('~/Desktop/electricity-transmission.csv')
sequences_by_tech['solar-pv'].to_csv('~/Desktop/solar-pv.csv')

oemoflex_scalars = pd.DataFrame(
    columns=[
        'usecase',
        'region',
        'model',
        'year',
        'name',
        'type',
        'carrier',
        'tech',
        'var_name',
        'var_value',
        'var_unit'
    ]
)

# then sum the flows
summed_sequences = get_summed_sequences(sequences_by_tech, prep_elements)
summed_sequences.to_csv('~/Desktop/summed_sequences.csv')
oemoflex_scalars = pd.concat([oemoflex_scalars, summed_sequences], sort=True)

# losses (storage, transmission)
transmission_losses = get_transmission_losses(oemoflex_scalars, prep_elements)
storage_losses = get_storage_losses(oemoflex_scalars, prep_elements)
oemoflex_scalars = pd.concat([oemoflex_scalars, transmission_losses, storage_losses])

# get capacities
capacities = get_capacities(es)
# oemoflex_scalars = pd.concat([oemoflex_scalars, capacities])

# emissions
emissions = get_emissions(oemoflex_scalars, prep_elements)
oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

# costs
varom_costs = get_varom_cost(oemoflex_scalars, prep_elements)
# fuel_cost = get_fuel_cost(oemoflex_scalars, prep_elements)
# fixom_cost = get_fixom_cost(oemoflex_scalars, prep_elements)
# total_cost = get_total_system_cost(oemoflex_scalars, prep_elements)

# set experiment info
oemoflex_scalars['usecase'] = name
oemoflex_scalars['model'] = 'oemof'
oemoflex_scalars['year'] = 2050

# map to FlexMex data format
map_to_flexmex_results(
    oemoflex_scalars, flexmex_scalars_template, exp_paths.results_postprocessed
)
