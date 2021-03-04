import sys

from oemoflex.helpers import load_yaml
from oemoflex.inferring import infer


if __name__ == '__main__':

    # load scenario specifications
    scenario_specs = load_yaml(sys.argv[1])

    preprocessed_path = sys.argv[2]

    infer(
        select_components=scenario_specs['components'],
        package_name=scenario_specs['scenario'],
        path=preprocessed_path,
    )
