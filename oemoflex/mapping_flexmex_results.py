import os

import numpy as np
import pandas as pd

# Path definitions
module_path = os.path.abspath(os.path.dirname(__file__))

MODEL_CONFIG = 'model_config'

PATH_MAPPINGS_REL = '../flexmex_config'

path_mappings = os.path.abspath(os.path.join(module_path, PATH_MAPPINGS_REL))

# load scalars templates
flexmex_scalars_template = pd.read_csv(
    os.path.join(
        path_mappings, 'output_template', 'v0.06', 'Template', 'Scalars.csv'
    )
)

mapping = pd.read_csv(os.path.join(path_mappings, 'mapping-output-scalars.csv'))


def map_to_flexmex_results(
    oemoflex_scalars,
    scenario,
    mapping=mapping,
    flexmex_scalars_template=flexmex_scalars_template,
):
    mapping = mapping.set_index('Parameter')

    flexmex_scalars = flexmex_scalars_template.copy()

    flexmex_scalars = flexmex_scalars.loc[
        flexmex_scalars_template['UseCase'] == scenario,
    ]

    # oemoflex_scalars.loc[oemoflex_scalars['var_unit'] == 'MWh', 'var_value'] *= 1e-3  # MWh to GWh

    for i, row in flexmex_scalars.loc[flexmex_scalars['UseCase'] == scenario].iterrows():
        try:
            select = mapping.loc[row['Parameter'], :]
        except KeyError:
            continue

        try:
            value = oemoflex_scalars.loc[
                (row['Region'],
                 select['carrier'],
                 select['tech'],
                 select['var_name']), 'var_value']

        except KeyError:
            print(f"Key "
                  f"{(row['Region'], select['carrier'], select['tech'], select['var_name'])}"
                  f" not found")

            continue

        if isinstance(value, float):
            flexmex_scalars.loc[i, 'Value'] = np.around(value)

    flexmex_scalars.loc[:, 'Modell'] = 'oemof'

    return flexmex_scalars
