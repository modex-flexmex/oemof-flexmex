from oemof.tabular.tools import building


all_foreign_keys = {
    'bus': [
       'wind-onshore',
       'wind-offshore',
       'solar-pv',
       'electricity-shortage',
       'electricity-curtailment',
       'electricity-demand',
    ],
    'profile': [
       'wind-onshore',
       'wind-offshore',
       'solar-pv',
       'electricity-demand',
    ],
    'from_to_bus': [
       'ch4-gt',
       'uranium-nuclear-st',
    ],
}


def inferring(select_components, package_name, path):

    foreign_keys = {key: value for key, value in all_foreign_keys if value in select_components}

    building.infer_metadata(
        package_name=package_name,
        foreign_keys=foreign_keys,
        path=path,
    )
