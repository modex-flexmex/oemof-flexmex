import os
import logging
import sys

from oemof_flexmex.model_structure import create_default_elements
from oemof_flexmex.parametrization_scalars import update_scalars
from oemof_flexmex.parametrization_sequences import create_profiles
from oemof_flexmex.helpers import (
    check_if_csv_dirs_equal,
    load_yaml,
    load_scalar_input_data,
    setup_logging,
)

if __name__ == "__main__":
    # load scenario specifications
    scenario_specs = load_yaml(sys.argv[1])
    data_raw_path = sys.argv[2]
    preprocessed_output_path = sys.argv[3]
    logging_path = sys.argv[4]

    setup_logging(logging_path)

    if not os.path.exists(preprocessed_output_path):
        for subdir in ["elements", "sequences"]:
            os.makedirs(os.path.join(preprocessed_output_path, subdir))

    scalars = load_scalar_input_data(scenario_specs, data_raw_path)

    # Prepare oemof.tabular input CSV files
    create_default_elements(
        os.path.join(preprocessed_output_path, "elements"),
        select_components=scenario_specs["components"],
    )

    # update elements
    update_scalars(scenario_specs["components"], preprocessed_output_path, scalars)

    # create sequences
    create_profiles(
        data_raw_path,
        preprocessed_output_path,
        select_components=scenario_specs["components"],
    )

    # compare with previous data
    previous_path = preprocessed_output_path.replace("results", "defaults")
    new_path = preprocessed_output_path
    try:
        check_if_csv_dirs_equal(new_path, previous_path)
    except AssertionError as e:
        logging.warning(e)
