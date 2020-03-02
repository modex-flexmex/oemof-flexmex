import os


POSTPROC_RES_SUBDIR_LIST = [
    'Boiler',
    'CHP/BpCCGT',
    'CHP/ExCCGT',
    'ElectricBoiler',
    'Fossil/Gasturbine',
    'Fossil/Nuclear',
    'Heatpump',
    'Hydro/Reservoir',
    'Hydro/RunOfRiver',
    'RE/Curtailment',
    'RE/Generation',
    'RE/Curtailment',
    'Storage',
    'Transmission/ImportExport',
    'Transmission/Import',
    'Transport',
]


def create_postprocessed_results_subdirs(postprocessed_results_dir):
    for subdir in POSTPROC_RES_SUBDIR_LIST:
        path = os.path.join(postprocessed_results_dir, subdir)
        if not os.path.exists(path):
            os.makedirs(path)
