import os
import sys

from oemoflex.postprocessing_sketch import run_postprocessing_sketch
from oemoflex.helpers import setup_experiment_paths, check_if_csv_dirs_equal, load_yaml


if __name__ == '__main__':
    scenario_specs = load_yaml(sys.argv[1])

    exp_paths = setup_experiment_paths(scenario_specs['scenario'])

    run_postprocessing_sketch(scenario_specs['year'], scenario_specs['scenario'], exp_paths)

    # compare with previous data
    previous_path = os.path.join(exp_paths.results_postprocessed + '_default')
    new_path = exp_paths.results_postprocessed
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        print(e)
