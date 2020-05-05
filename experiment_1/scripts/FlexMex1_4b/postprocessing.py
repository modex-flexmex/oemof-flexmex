import os

import pandas as pd

from oemof.solph import EnergySystem
from oemoflex.postprocessing import \
    create_postprocessed_results_subdirs, get_sequences_by_tech,\
    get_capacities, format_capacities,\
    get_summed_sequences, get_re_generation,\
    get_transmission_losses, get_storage_losses, get_emissions, \
    get_varom_cost, get_carrier_cost, get_total_system_cost, \
    map_to_flexmex_results
from oemoflex.helpers import \
    setup_experiment_paths, load_elements


name = 'FlexMex1_4b'

year = 2050

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
exp_paths = setup_experiment_paths(name, basepath)

create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

# load scalars templates
flexmex_scalars_template = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
flexmex_scalars_template = flexmex_scalars_template.loc[flexmex_scalars_template['UseCase'] == name]

# load mapping
mapping = pd.read_csv(os.path.join(exp_paths.results_template, 'mapping.csv'))

# Load preprocessed elements
prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

# restore EnergySystem with results
es = EnergySystem()
es.restore(exp_paths.results_optimization)

# format results sequences
sequences_by_tech = get_sequences_by_tech(es.results)

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
oemoflex_scalars = pd.concat([oemoflex_scalars, summed_sequences], sort=True)

# get re_generation
re_generation = get_re_generation(oemoflex_scalars)
oemoflex_scalars = pd.concat([oemoflex_scalars, re_generation], sort=True)

# losses (storage, transmission)
transmission_losses = get_transmission_losses()
storage_losses = get_storage_losses()
# oemoflex_scalars = pd.concat([oemoflex_scalars, transmission_losses, storage_losses])

# get capacities
capacities = get_capacities(es)
formatted_capacities = format_capacities(oemoflex_scalars, capacities)
oemoflex_scalars = pd.concat([oemoflex_scalars, formatted_capacities])

# emissions
emissions = get_emissions()
# oemoflex_scalars = pd.concat([oemoflex_scalars, emissions])

# costs
varom_cost = get_varom_cost(oemoflex_scalars, prep_elements)
carrier_cost = get_carrier_cost(oemoflex_scalars, prep_elements)
oemoflex_scalars = pd.concat([oemoflex_scalars, varom_cost, carrier_cost])

total_system_cost = get_total_system_cost(oemoflex_scalars)
oemoflex_scalars = pd.concat([oemoflex_scalars, total_system_cost], sort=True)

# set experiment info
oemoflex_scalars['usecase'] = name
oemoflex_scalars['model'] = 'oemof'
oemoflex_scalars['year'] = 2050

oemoflex_scalars.to_csv('~/Desktop/oemoflex_scalars.csv')
# map to FlexMex data format
flexmex_scalar_results = map_to_flexmex_results(
    oemoflex_scalars, flexmex_scalars_template, mapping, name
)

flexmex_scalar_results.to_csv(os.path.join(exp_paths.results_postprocessed, 'Scalars.csv'))

# save_flexmex_timeseries(sequences_by_tech)
