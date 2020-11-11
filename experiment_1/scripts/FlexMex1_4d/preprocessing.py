import os

from oemof.tools.logger import define_logging
from oemoflex.preprocessing import (
    create_default_elements,
    update_electricity_shortage, update_heat_shortage,
    update_heat_demand, update_electricity_demand,
    update_extchp, update_boiler,
    update_wind_onshore, update_wind_offshore, update_solar_pv,
    create_profiles)
from oemoflex.helpers import setup_experiment_paths, load_scalar_input_data, check_if_csv_dirs_equal


name = 'FlexMex1_4d'

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
    scalars = scalars.loc[scalars['Scenario'].isin([name, 'FlexMex1', 'ALL']), :]

    components = [
        'electricity-shortage',
        'electricity-curtailment',
        'electricity-demand',
        'heat-demand',
        'heat-excess',
        'heat-shortage',
        'wind-offshore',
        'wind-onshore',
        'solar-pv',
        'ch4-extchp',
        'ch4-boiler',
    ]

    # Prepare oemof.tabular input CSV files
    create_default_elements(
        os.path.join(exp_paths.data_preprocessed, 'elements'),
        select_components=components
    )

    # update elements
    update_electricity_shortage(exp_paths.data_preprocessed, scalars)
    update_heat_shortage(exp_paths.data_preprocessed, scalars)
    update_heat_demand(exp_paths.data_preprocessed, scalars)
    update_electricity_demand(exp_paths.data_preprocessed, scalars)
    update_extchp(exp_paths.data_preprocessed, scalars)
    update_boiler(exp_paths.data_preprocessed, scalars)
    update_wind_onshore(exp_paths.data_preprocessed, scalars)
    update_wind_offshore(exp_paths.data_preprocessed, scalars)
    update_solar_pv(exp_paths.data_preprocessed, scalars)

    # create sequences
    create_profiles(exp_paths, select_components=components)

    # compare with previous data
    previous_path = os.path.join(os.path.split(exp_paths.data_preprocessed)[0] + '_default', 'data')
    new_path = exp_paths.data_preprocessed
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        print(e)


if __name__ == '__main__':
    main()
