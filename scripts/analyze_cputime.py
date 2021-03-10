import os
import sys

import pandas as pd


def write_csv(df, path, mode='w', header=True):
    df.to_csv(path, mode=mode, header=header, index=False, float_format='%.2f')


def append_csv(df, path):
    write_csv(df, path, mode='a', header=False)


scenario_name = sys.argv[1]
input_dir = sys.argv[2]
output_dir = sys.argv[3]

infer_path = os.path.join(input_dir, 'benchmark-infer.log')
optimize_path = os.path.join(input_dir, 'benchmark-optimize.log')
postprocess_path =os.path.join(input_dir, 'benchmark-postprocess.log')
preprocess_path = os.path.join(input_dir, 'benchmark-preprocess.log')
solver_path = os.path.join(input_dir, 'solver_time.log')

# Read time values
infer_time = pd.read_csv(infer_path, sep='\t')['cpu_time'][0]
optimize_time = pd.read_csv(optimize_path, sep='\t')['cpu_time'][0]
postprocess_time = pd.read_csv(postprocess_path, sep='\t')['cpu_time'][0]
preprocess_time = pd.read_csv(preprocess_path, sep='\t')['cpu_time'][0]
solver_time = pd.read_csv(solver_path, index_col=False)['system_time'][0]

# Calculate time values
optimize_extra_time = optimize_time - solver_time
preprocessing = preprocess_time + infer_time + optimize_extra_time
solving = solver_time
postprocessing = postprocess_time

# Set up output DataFrame
df = pd.DataFrame(
    {'scenario': [scenario_name],
     'preprocessing': [preprocessing],
     'solving': [solving],
     'postprocessing': [postprocessing]}
)

# Output
output_path = os.path.join(output_dir, 'cpu_time_analysis.csv')

if os.path.exists(output_path):
    append_csv(df, output_path)
else:
    write_csv(df, output_path)

