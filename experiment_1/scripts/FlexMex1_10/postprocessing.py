import os

import pandas as pd

from oemof.solph import EnergySystem
from oemoflex.postprocessing import \
    create_postprocessed_results_subdirs, get_sequences_by_tech, get_capacities
from oemoflex.helpers import \
    setup_experiment_paths, load_elements


name = 'FlexMex1_10'

year = 2050

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
exp_paths = setup_experiment_paths(name, basepath)

create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

# load scalars templates
scalars_template = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
scalars_template = scalars_template.loc[scalars_template['UseCase'] == name]

# Load preprocessed elements
prep_elements = load_elements(os.path.join(exp_paths.data_preprocessed, 'data', 'elements'))

# restore EnergySystem with results
es = EnergySystem()
es.restore(exp_paths.results_optimization)

# format results sequences
sequences_by_tech = get_sequences_by_tech(es.results)

# then sum the flows
summed_sequences = {key: value.sum() for key, value in sequences_by_tech.items()}

# losses

# get capacities
capacities = get_capacities(es)

# emissions

# costs
