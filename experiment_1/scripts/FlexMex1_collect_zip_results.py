import os

import zipfile

from oemoflex.helpers import get_experiment_paths


abspath = os.path.abspath(os.path.dirname(__file__))

path_config = os.path.join(abspath, '../config.yml')

experiment_paths = get_experiment_paths('', path_config)

UseCases = [
    'FlexMex1_2',
    'FlexMex1_3',
    'FlexMex1_4',
    'FlexMex1_5',
    'FlexMex1_7',
    'FlexMex1_10',
]

zip_archive = os.path.join(experiment_paths['results_comparison'], 'oemof.zip')

zipf = zipfile.ZipFile(zip_archive, 'w', zipfile.ZIP_DEFLATED)

for path in os.listdir(experiment_paths['results_postprocessed']):
    if path in UseCases:
        full_path = os.path.join(experiment_paths['results_postprocessed'], path)

        for root, dirs, files in os.walk(full_path):
            for file in files:
                file_to_write = os.path.join(root, file)

                relative_path = os.path.relpath(
                    file_to_write,
                    experiment_paths['results_postprocessed'])

                zipf.write(file_to_write, relative_path)

zipf.close()

print(f"Wrote zip file to {zip_archive}")
