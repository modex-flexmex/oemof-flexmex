import os
import sys

import pandas as pd


def write_csv(df, path, mode='w', header=True):
    df.to_csv(path, mode=mode, header=header, index=False, float_format='%.2f')


def append_csv(df, path):
    write_csv(df, path, mode='a', header=False)


scenario_name = sys.argv[1]
input_dir = sys.argv[2]
output_path = sys.argv[3]

infer_path = os.path.join(input_dir, 'benchmark-infer.log')
optimize_path = os.path.join(input_dir, 'benchmark-optimize.log')
postprocess_path =os.path.join(input_dir, 'benchmark-postprocess.log')
preprocess_path = os.path.join(input_dir, 'benchmark-preprocess.log')
solver_path = os.path.join(input_dir, 'solver_time.log')

# Read time values
# Snakemake Benchmark results per processing step
infer_time = pd.read_csv(infer_path, sep='\t')['cpu_time'][0]
optimize_time = pd.read_csv(optimize_path, sep='\t')['cpu_time'][0]
postprocess_time = pd.read_csv(postprocess_path, sep='\t')['cpu_time'][0]
preprocess_time = pd.read_csv(preprocess_path, sep='\t')['cpu_time'][0]

# CBC meta results output from postprocessing
# Use 'System time' for CPU time because it equals 'Total time (CPU seconds)' in CBC's stdout
solver_time = pd.read_csv(solver_path, index_col=False)['system_time'][0]

# Calculate time values
optimize_extra_time = optimize_time - solver_time  # Energy model building AND dumping results
# Assign extra time from optimization step to preprocessing time in lack of precision
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
if os.path.exists(output_path):
    append_csv(df, output_path)
else:
    write_csv(df, output_path)

