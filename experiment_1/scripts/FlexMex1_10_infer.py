"""
Run this script from the root directory of the datapackage to update
or create meta data.
"""
import os

from oemof.tabular.datapackage import building


name = 'FlexMex1_10'

abspath = os.path.abspath(os.path.dirname(__file__))

building.infer_metadata(
    package_name='oemof-tabular-dispatch-example',
    foreign_keys={
        'bus': ['volatile', 'shortage', 'curtailment', 'storage', 'load'],
        'profile': ['load', 'volatile'],
        'from_to_bus': ['link'],
    },
    path=os.path.join(abspath, '..', '002_data_preprocessed', name)
)
