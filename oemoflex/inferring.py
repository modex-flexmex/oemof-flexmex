from oemof.tabular.datapackage import building


all_foreign_keys = {
    'bus': [
        'heat-shortage',
        'heat-excess',
        'heat-demand',
        'heat-storage-large',
        'heat-storage-small',
        'wind-onshore',
        'wind-offshore',
        'solar-pv',
        'electricity-shortage',
        'electricity-curtailment',
        'electricity-demand',
        'electricity-h2_cavern',
        'electricity-liion_battery',
        'hydro-reservoir',
        'electricity-bev',
    ],
    'profile': [
        'wind-onshore',
        'wind-offshore',
        'solar-pv',
        'electricity-demand',
        'hydro-reservoir',
        'heat-demand',
    ],
    'from_to_bus': [
        'electricity-transmission',
        'ch4-gt',
        'uranium-nuclear-st',
        'ch4-boiler-small',
        'ch4-boiler-large',
        'electricity-pth',
        'electricity-heatpump-small',
        'electricity-heatpump-large',
    ],
    'chp': [
        'ch4-bpchp',
        'ch4-extchp',
    ],
    'efficiency': [
        'electricity-heatpump-large',
        'electricity-heatpump-small',
    ],
    'availability': ['electricity-bev'],
    'drive_power': ['electricity-bev'],
    'min_storage_level': ['electricity-bev'],
    'max_storage_level': ['electricity-bev'],
}


def infer(select_components, package_name, path):

    foreign_keys = {
        key: value for key, value in all_foreign_keys.items() if value in select_components
    }

    building.infer_metadata(
        package_name=package_name,
        foreign_keys=foreign_keys,
        path=path,
    )
