import os
import sys

from oemof.tools.logger import define_logging
from oemoflex.model_structure import create_default_elements
from oemoflex.parametrization_scalars import update_scalars
from oemoflex.parametrization_sequences import create_profiles
from oemoflex.helpers import (
    setup_experiment_paths, load_scalar_input_data, filter_scalar_input_data,
    check_if_csv_dirs_equal, load_yaml, has_duplicates
)


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

    # Get experiment name - necessary as long as "Data_In" contains two versions of Scalars.csv
    experiment_name = scenario_specs['scenario'].split('_')[0]

    # Load common input parameters
    scalars = load_scalar_input_data(exp_paths.data_raw, experiment_name)

    # Filter out only scenario-related input parameters
    scalars = filter_scalar_input_data(
        scalars,
        scenario_select=scenario_specs['scenario_select'],
        scenario_overwrite=scenario_specs['scenario_overwrite']
    )

    # After filtering there musn't be any duplicates left.
    if has_duplicates(scalars, ['Scenario', 'Region', 'Parameter']):
        raise ValueError('Found duplicates in Scalars data. Check input data and filtering.')

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
    previous_path = os.path.join(os.path.split(exp_paths.data_preprocessed)[0] + '_default', 'data')
    new_path = exp_paths.data_preprocessed
    # check_if_csv_dirs_equal(new_path, previous_path)
