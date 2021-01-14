import os
import sys

from oemoflex.helpers import load_yaml, setup_experiment_paths
from oemoflex.inferring import infer


if __name__ == '__main__':

    # load scenario specifications
    scenario_specs = load_yaml(sys.argv[1])

    # Get paths
    exp_paths = setup_experiment_paths(scenario_specs['name'])

    exp_paths.data_preprocessed = os.path.join(exp_paths.data_preprocessed)

    infer(
        select_components=scenario_specs['components'],
        package_name=scenario_specs['name'],
        path=exp_paths.data_preprocessed,
    )
