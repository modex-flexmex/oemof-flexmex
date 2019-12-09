import os
import re

import pandas as pd

year = 2050
name = "FlexMex1_10"
abspath = os.path.abspath(os.path.dirname(__file__))

# path to directory with datapackage to load
datapackage_dir = os.path.join(abspath, '..', 'input_data', name)

# create  path for results (we use the datapackage_dir to store results)
results_dir = os.path.join(abspath, '..', 'optimization_results', name)
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

template_dir = os.path.join(abspath, '..', 'template_data')

postprocessed_results_dir = os.path.join(abspath, '..', 'postprocessed_results', name)

postprocessed_results_subdir_list = ['RE/Curtailment', 'RE/Generation', 'Transmission/ImportExport']

for subdir in postprocessed_results_subdir_list:
    path = os.path.join(postprocessed_results_dir, subdir)
    if not os.path.exists(path):
        os.makedirs(path)


# load template
template_scalars = pd.read_csv(os.path.join(template_dir, 'Scalars.csv'))

template_scalars = template_scalars.loc[template_scalars['UseCase'] == name]


# load results
bus_results_files = (file for file in os.listdir(results_dir) if re.search('el-bus.csv', file))
for file in bus_results_files:
    region = file.split('-')[0]

    bus_results = pd.read_csv(os.path.join(results_dir, file))

    # EnergyConversion_Curtailment_Electricity_RE
    energy_conversion_curtailment_electricity_re = bus_results.filter(regex='curtailment', axis=1)

    energy_conversion_curtailment_electricity_re.columns = [
        'EnergyConversion_Curtailment_Electricity_RE'
    ]

    energy_conversion_curtailment_electricity_re.to_csv(
        os.path.join(
            postprocessed_results_dir,
            'RE',
            'Curtailment',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        )
    )

    # EnergyConversion_SecondaryEnergy_RE
    energy_conversion_secondary_energy_re = bus_results.filter(regex='el-wind|solarpv', axis=1)

    energy_conversion_secondary_energy_re = pd.DataFrame(
        energy_conversion_secondary_energy_re.sum(axis=1)
    )

    energy_conversion_secondary_energy_re -= energy_conversion_curtailment_electricity_re

    energy_conversion_secondary_energy_re.columns = ['EnergyConversion_SecondaryEnergy_RE']
    energy_conversion_secondary_energy_re.to_csv(
        os.path.join(
            postprocessed_results_dir,
            'RE',
            'Generation',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        ),
        header=True,
    )

    # Transmission_Import_Electricity_Grid
    transmission_import_electricity_grid = bus_results.filter(regex='import', axis=1)

    transmission_import_electricity_grid.columns = ['Transmission_Import_Electricity_Grid']

    transmission_import_electricity_grid.to_csv(
        os.path.join(
            postprocessed_results_dir,
            'Transmission',
            'ImportExport',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        )
    )
