import os
import pandas as pd


def write_csv(df, path, mode='w', header=True):
    df.to_csv(path, mode=mode, header=header, index=False, float_format='%.2f')


def append_csv(df, path):
    write_csv(df, path, mode='a', header=False)


# Read time values
infer_time = pd.read_csv('results/FlexMex1_2a/benchmark-infer.log', sep='\t')['cpu_time'][0]
optimize_time = pd.read_csv('results/FlexMex1_2a/benchmark-optimize.log', sep='\t')['cpu_time'][0]
postprocess_time = pd.read_csv('results/FlexMex1_2a/benchmark-postprocess.log', sep='\t')['cpu_time'][0]
preprocess_time = pd.read_csv('results/FlexMex1_2a/benchmark-preprocess.log', sep='\t')['cpu_time'][0]
solver_time = pd.read_csv('results/FlexMex1_2a/solver_time.log', header=None, index_col=0).loc['cpu_time', 1]

# Calculate time values
optimize_extra_time = optimize_time - solver_time
preprocessing = preprocess_time + infer_time + optimize_extra_time
solving = solver_time
postprocessing = postprocess_time

# Set up output DataFrame
df = pd.DataFrame(
    {'scenario': ['FlexMex1_2a'],
     'preprocessing': [preprocessing],
     'solving': [solving],
     'postprocessing': [postprocessing]}
)

# Output
output_path = 'results/FlexMex1_2a/cpu_time_analysis.csv'

if os.path.exists(output_path):
    append_csv(df, output_path)
else:
    write_csv(df, output_path)

