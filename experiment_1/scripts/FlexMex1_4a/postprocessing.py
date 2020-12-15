import os

from oemoflex.postprocessing import run_postprocessing
from oemoflex.helpers import setup_experiment_paths, check_if_csv_dirs_equal


name = 'FlexMex1_4a'

year = 2050

exp_paths = setup_experiment_paths(name)


def main():
    run_postprocessing(year, name, exp_paths)

    # compare with previous data
    previous_path = os.path.join(exp_paths.results_postprocessed + '_default')
    new_path = exp_paths.results_postprocessed
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        print(e)


if __name__ == '__main__':
    main()
