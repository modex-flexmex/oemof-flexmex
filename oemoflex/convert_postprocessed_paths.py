# This restructures postprocessed_paths.py

import os
import yaml

path_config = os.path.join('postprocessed_paths.yaml')

with open(path_config, 'r') as config_file:
    pp_paths = yaml.safe_load(config_file)

restructured = dict()

for path_part_one, data in pp_paths.items():
    component = data['component']
    timeseries = data['sequences']

    timeseries_restructured = dict()

    for path_part_two, oemoflex_key in timeseries.items():
        timeseries_restructured.update({oemoflex_key: path_part_one + '/' + path_part_two})

    restructured.update({component: timeseries_restructured})

print(yaml.dump(restructured))