import os
import re

import pandas as pd

year = 2050
name = "FlexMex1_10"
abspath = os.path.abspath(os.path.dirname(__file__))

# path to directory with datapackage to load
datapackage_dir = os.path.join(abspath, '../..', 'input_data', name)

# create  path for results (we use the datapackage_dir to store results)
results_dir = os.path.join(abspath, '../..', 'optimization_results', name)
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

template_dir = os.path.join(abspath, '../..', 'template_data')

postprocessed_results_dir = os.path.join(abspath, '../..', 'postprocessed_results', name)

postprocessed_results_subdir_list = [
    'RE/Curtailment',
    'RE/Generation',
    'Transmission/ImportExport',
    'Transmission/Import',
]

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

    energy_conversion_secondary_energy_re.columns = ['EnergyConversion_SecondaryEnergy_RE']

    energy_conversion_secondary_energy_re[
        'EnergyConversion_SecondaryEnergy_RE'
    ] -= energy_conversion_curtailment_electricity_re['EnergyConversion_Curtailment_Electricity_RE']

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
            'Import',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        )
    )


def rearrange_link_flows(link_flow_results):
    idx = pd.IndexSlice
    filter_values = [
        level_value
        for level_value in link_flow_results.columns.get_level_values(1)
        if re.search('bus', level_value)
    ]

    link_flow_results = link_flow_results.loc[:, idx[:, filter_values, :]]

    link_flow_results.columns = link_flow_results.columns.tolist()

    revert_columns = {}
    for item in link_flow_results.columns:
        if item[0].split('-')[0] == item[1].split('-')[0]:
            new_item = list(item)
            new_item[0] = new_item[0].split('-')
            new_item[0].reverse()
            new_item[0] = '-'.join(new_item[0])
            new_item = tuple(new_item)
            revert_columns[item] = new_item

    link_flow_results = link_flow_results.rename(columns=revert_columns)
    link_flow_results.columns = [column[0] for column in link_flow_results.columns]

    return link_flow_results


def calc_net_flows(link_flow_results):
    link_list = [
        'AT-CH',
        'AT-CZ',
        'AT-IT',
        'BE-FR',
        'BE-LU',
        'BE-NL',
        'CH-FR',
        'CH-IT',
        'CZ-PL',
        'DE-AT',
        'DE-BE',
        'DE-CH',
        'DE-CZ',
        'DE-DK',
        'DE-FR',
        'DE-LU',
        'DE-NL',
        'DE-PL',
        'DK-NL',
        'FR-IT',
        'FR-LU',
    ]

    link_net_flow = pd.DataFrame()
    for item in link_list:
        reverse_item = item.split('-')

        reverse_item.reverse()

        reverse_item = '-'.join(reverse_item)

        link_net_flow[item] = (
            link_flow_results.loc[:, item] - link_flow_results.loc[:, reverse_item]
        )

    return link_net_flow


link_flow_results_file = 'links-oemof.csv'

link_flow_results = pd.read_csv(
    os.path.join(results_dir, link_flow_results_file), header=[0, 1, 2], index_col=0
)

link_flow_results = rearrange_link_flows(link_flow_results)

link_net_flows = calc_net_flows(link_flow_results)
print(link_net_flows)
for column in link_net_flows:
    from_region = column.split('-')[0]
    to_region = column.split('-')[1]
    link_flow_results.loc[:, column].to_csv(
        os.path.join(
            postprocessed_results_dir,
            'Transmission',
            'ImportExport',
            '{}_oemof_{}_{}_{}.csv'.format(name, from_region, to_region, year),
        ),
        header=True,
    )
