import os

from oemof.tools.logger import define_logging
from oemoflex.model_structure import create_default_elements
from oemoflex.parametrization_scalars import update_scalars
from oemoflex.parametrization_sequences import create_profiles
from oemoflex.helpers import setup_experiment_paths, load_scalar_input_data, check_if_csv_dirs_equal
from oemoflex.inferring import infer


name = 'FlexMex1_2a'

# Get paths
exp_paths = setup_experiment_paths(name)

exp_paths.data_preprocessed = os.path.join(exp_paths.data_preprocessed, 'data')

logpath = define_logging(
    logpath=exp_paths.results_postprocessed,
    logfile='oemoflex.log'
)

if not os.path.exists(exp_paths.data_preprocessed):
    for subdir in ['elements', 'sequences']:
        os.makedirs(os.path.join(exp_paths.data_preprocessed, subdir))


def main():
    # Load common input parameters
    scalars = load_scalar_input_data()

    # Filter out only scenario-related input parameters
    scalars = scalars.loc[scalars['Scenario'].isin([name, 'FlexMex1', 'FlexMex1UC2', 'ALL']), :]

    # There are two values for "Energy_SlackCost_Electricity"
    # one for 'FlexMex1' and one for 'FlexMex1UC2'
    # Drop the second one, only keep "Energy_SlackCost_Electricity" for use case 2b
    rows_to_drop = scalars.loc[
        (scalars['Parameter'] == 'Energy_SlackCost_Electricity')
        & (scalars['Scenario'] == 'FlexMex1'), :].index

    scalars = scalars.drop(rows_to_drop)

    components = {
        'electricity-shortage': {},
        'electricity-curtailment': {},
        'electricity-demand': {},
        'wind-offshore': {},
        'wind-onshore': {},
        'solar-pv': {},
        'uranium-nuclear-st': {'expandable': True, 'from_green_field': True},
        'ch4-gt': {'expandable': True, 'from_green_field': True},
    }

    # Prepare oemof.tabular input CSV files
    create_default_elements(
        os.path.join(exp_paths.data_preprocessed, 'elements'),
        select_components=components
    )

    # update elements
    update_scalars(components, exp_paths.data_preprocessed, scalars)

    # create sequences
    create_profiles(exp_paths, select_components=components)

    # compare with previous data
    previous_path = os.path.join(os.path.split(exp_paths.data_preprocessed)[0] + '_default', 'data')
    new_path = exp_paths.data_preprocessed
    check_if_csv_dirs_equal(new_path, previous_path)

    # this becomes necessary because 'data' is manually added some lines above. Needs to be cleaned
    # up.
    exp_paths.data_preprocessed = exp_paths.data_preprocessed.strip('data')

    infer(select_components=components, package_name=name, path=exp_paths.data_preprocessed)


if __name__ == '__main__':
    main()
