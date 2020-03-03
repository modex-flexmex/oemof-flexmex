import os

import pandas as pd


bus_list = [
    'AT-el-bus',
    'BE-el-bus',
    'CH-el-bus',
    'CZ-el-bus',
    'DE-el-bus',
    'DK-el-bus',
    'FR-el-bus',
    'IT-el-bus',
    'LU-el-bus',
    'NL-el-bus',
    'PL-el-bus',
]

country_list = [
    'AT',
    'BE',
    'CH',
    'CZ',
    'DE',
    'DK',
    'FR',
    'IT',
    'LU',
    'NL',
    'PL',
]

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

datetimeindex = pd.date_range(start='2019-01-01', freq='H', periods=8760)

module_path = os.path.dirname(os.path.abspath(__file__))


def create_default_elements_files(
    dir,
    components_file='components.csv',
    component_attrs_dir='component_attrs'
):
    r"""

    Parameters
    ----------
    dir
    components_file
    component_attrs_dir

    Returns
    -------
    None
    """
    components_file = os.path.join(module_path, components_file)

    component_attrs_dir = os.path.join(module_path, component_attrs_dir)

    components = pd.read_csv(components_file)

    for component in components.name.values:
        component_attrs_file = os.path.join(component_attrs_dir, component + '.csv')

        try:
            component_attrs = pd.read_csv(component_attrs_file)

        except FileNotFoundError:
            print(f"There is no file with the name {component}")

        component_data = {
            c_attr['attribute']: c_attr['default'] for _, c_attr in component_attrs.iterrows()
        }

        component_data['name'] = country_list
        if component == 'link':
            component_data['name'] = link_list

        df = pd.DataFrame(component_data).set_index('name')

        df.to_csv(os.path.join(dir, component + '.csv'))
