import os
import sys

from oemof.tools.logger import define_logging
from oemoflex.model_structure import create_default_elements
from oemoflex.parametrization_scalars import update_scalars
from oemoflex.parametrization_sequences import create_profiles
from oemoflex.helpers import (
    setup_experiment_paths, check_if_csv_dirs_equal, load_yaml, load_scalar_input_data)

if __name__ == '__main__':
    # load scenario specifications
    scenario_specs = load_yaml(sys.argv[1])

    # Get paths
    exp_paths = setup_experiment_paths(scenario_specs['scenario'])

    exp_paths.data_preprocessed = os.path.join(exp_paths.data_preprocessed, 'data')

    logpath = define_logging(
        logpath=exp_paths.results_postprocessed,
        logfile='oemoflex.log'
    )

    if not os.path.exists(exp_paths.data_preprocessed):
        for subdir in ['elements', 'sequences']:
            os.makedirs(os.path.join(exp_paths.data_preprocessed, subdir))

    scalars = load_scalar_input_data(scenario_specs, exp_paths.data_raw)

    # Prepare oemof.tabular input CSV files
    create_default_elements(
        os.path.join(exp_paths.data_preprocessed, 'elements'),
        select_components=scenario_specs['components']
    )

    # update elements
    update_scalars(scenario_specs['components'], exp_paths.data_preprocessed, scalars)

    # create sequences
    create_profiles(exp_paths, select_components=scenario_specs['components'])

    # compare with previous data
    previous_path = exp_paths.data_preprocessed.replace('results', 'defaults')
    new_path = exp_paths.data_preprocessed
    check_if_csv_dirs_equal(new_path, previous_path)
