import os
import pandas as pd


dirs = [
    'FlexMex1_4a',
    'FlexMex1_4b',
    'FlexMex1_4c',
    'FlexMex1_4d',
]

all_scalars = []

for dir in dirs:
    scalar = pd.read_csv(
        os.path.join('../005_results_postprocessed', dir, 'Scalars.csv'), index_col=[0])
    all_scalars.append(scalar)

all_scalars = pd.concat(all_scalars)
all_scalars.to_csv('../006_results_comparison/Scalars.csv', index=False)