import logging
import os
import re

import pandas as pd

from oemof.tools.logger import define_logging
from oemoflex.postprocessing import create_postprocessed_results_subdirs
from oemoflex.helpers import setup_experiment_paths, check_if_csv_dirs_equal, delete_empty_subdirs


name = 'FlexMex1_4a'

year = 2050

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
exp_paths = setup_experiment_paths(name, basepath)

create_postprocessed_results_subdirs(exp_paths.results_postprocessed)

logpath = define_logging(
    logpath=exp_paths.results_postprocessed,
    logfile='oemoflex.log'
)

# load templates
scalars = pd.read_csv(os.path.join(exp_paths.results_template, 'Scalars.csv'))
timeseries = pd.read_csv(os.path.join(exp_paths.results_template, 'TimeSeries.csv'))

scalars = scalars.loc[scalars['UseCase'] == name]
timeseries = timeseries.loc[timeseries['UseCase'] == name]


def calc_curtailment(bus_results, region):
    # EnergyConversion_Curtailment_Electricity_RE [GWh]
    energy_conversion_curtailment_electricity_re = bus_results.filter(regex='curtailment', axis=1)

    energy_conversion_curtailment_electricity_re.columns = [
        'EnergyConversion_Curtailment_Electricity_RE'
    ]

    energy_conversion_curtailment_electricity_re.to_csv(
        os.path.join(
            exp_paths.results_postprocessed,
            'RE',
            'Curtailment',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        )
    )

    return energy_conversion_curtailment_electricity_re


def calc_energy_conversion_secondary_energy_re(
    bus_results, energy_conversion_curtailment_electricity_re, region
):
    r"""
    Calculates EnergyConversion_SecondaryEnergy_RE [GWh]
    """
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
            exp_paths.results_postprocessed,
            'RE',
            'Generation',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        ),
        header=True,
    )

    return energy_conversion_secondary_energy_re


def calc_transmission_import_electricity_grid(bus_results, region):
    r"""
    Calculates EnergyConversion_SecondaryEnergy_RE [GWh]
    """
    transmission_import_electricity_grid = bus_results.filter(regex='import', axis=1)

    transmission_import_electricity_grid.columns = ['Transmission_Import_Electricity_Grid']

    transmission_import_electricity_grid.to_csv(
        os.path.join(
            exp_paths.results_postprocessed,
            'Transmission',
            'Import',
            '{}_oemof_{}_{}.csv'.format(name, region, year),
        )
    )

    return transmission_import_electricity_grid


def calc_fix_om():
    # EnergyConversion_FixOM_Electricity_Solar_PV [Eur/a]
    # EnergyConversion_FixOM_Electricity_Wind_Onshore [Eur/a]
    pass


def calc_var_om():
    # EnergyConversion_VarOM_Electricity_Solar_PV [Eur/a]
    # EnergyConversion_VarOM_Electricity_Wind_Onshore [Eur/a]
    pass


def calc_price_shortage():
    # Energy_Price_Slack [Eur]
    pass


def write_value_to_scalars(scalars, region, param_name, value):
    df = scalars.copy()

    position = (df['Region'] == region) & (df['Parameter'] == param_name)

    if not position.any():
        raise ValueError(
            "There is no field for region '{}' and parameter '{}'.".format(region, param_name)
        )

    else:
        df.loc[position, 'Value'] = value

    return df


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


def main(name=name, scalars=scalars):
    # Postprocess
    bus_results_files = (
        file for file in os.listdir(exp_paths.results_optimization)
        if re.search('el-bus.csv', file)
    )

    for file in bus_results_files:
        region = file.split('-')[0]

        bus_results = pd.read_csv(os.path.join(exp_paths.results_optimization, file))

        # EnergyConversion_Curtailment_Electricity_RE
        energy_conversion_curtailment_electricity_re = calc_curtailment(bus_results, region)

        sum_in_gwh = 1e-3 * energy_conversion_curtailment_electricity_re.sum().values
        scalars = write_value_to_scalars(
            scalars,
            region,
            'EnergyConversion_Curtailment_Electricity_RE',
            sum_in_gwh,
        )

        # EnergyConversion_SecondaryEnergy_RE
        energy_conversion_secondary_energy_re = calc_energy_conversion_secondary_energy_re(
            bus_results, energy_conversion_curtailment_electricity_re, region
        )

        sum_in_gwh = 1e-3 * energy_conversion_secondary_energy_re.sum().values
        scalars = write_value_to_scalars(
            scalars,
            region,
            'EnergyConversion_SecondaryEnergy_RE',
            sum_in_gwh,
        )

        # Transmission_Import_Electricity_Grid
        calc_transmission_import_electricity_grid(
            bus_results, region
        )

    link_flow_results_file = 'links-oemof.csv'

    link_flow_results = pd.read_csv(
        os.path.join(exp_paths.results_optimization, link_flow_results_file),
        header=[0, 1, 2], index_col=0
    )

    link_flow_results = rearrange_link_flows(link_flow_results)

    link_net_flows = calc_net_flows(link_flow_results)

    for column in link_net_flows:
        from_region = column.split('-')[0]
        to_region = column.split('-')[1]
        link_flow_results.loc[:, column].to_csv(
            os.path.join(
                exp_paths.results_postprocessed,
                'Transmission',
                'ImportExport',
                '{}_oemof_{}_{}_{}.csv'.format(name, from_region, to_region, year),
            ),
            header=True,
        )

    for name, value in link_net_flows.sum().iteritems():
        region = name.replace('-', '_')
        value_in_gwh = 1e-3 * value
        scalars = write_value_to_scalars(
            scalars,
            region,
            'Transmission_ImportExport_Electricity_Grid',
            value_in_gwh,
        )

    scalars.to_csv(os.path.join(exp_paths.results_postprocessed, 'Scalars.csv'))
    timeseries.to_csv(os.path.join(exp_paths.results_postprocessed, 'TimeSeries.csv'))

    # Check against previous results
    previous_results_path = exp_paths.results_postprocessed + '_default'
    new_results_path = exp_paths.results_postprocessed

    check_if_csv_dirs_equal(new_results_path, previous_results_path)

    logging.info(f"New results in {new_results_path}"
                 f" match previous results in {previous_results_path}")

    delete_empty_subdirs(exp_paths.results_postprocessed)


if __name__ == '__main__':
    main()
