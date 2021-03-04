import os
import shutil
import sys

import pandas as pd

# Switch for Snakemake run vs. command line call (debugging)
if 'snakemake' in globals():
    postprocessed_results_paths = snakemake.params['scenario_paths']  # noqa: F821
    scenarios = snakemake.params['scenarios']  # noqa: F821
    output_path = snakemake.output[0]  # noqa: F821

    # Removing and overwriting output from former runs is managed by Snakemake beforehand

else:
    _, *postprocessed_results_paths, output_path = sys.argv

    # In CLI debugging mode, derive scenario names from paths.
    # Not safe! Needs to be adapted along with changes in directory structure!
    scenarios = [os.path.basename(os.path.dirname(path)) for path in postprocessed_results_paths]

    if os.path.exists(output_path):
        print("Overwriting existing results. OK?")

        userinput = input("If that is fine, type ok: ")

        if userinput == 'ok':
            shutil.rmtree(output_path)
        else:
            sys.exit(f"You typed '{userinput}'. Aborting.")

    os.makedirs(output_path)

print("Joining results of these scenarios:")
for name, path in zip(scenarios, postprocessed_results_paths):
    print(f"{name} ({path})")

all_scalars = pd.DataFrame()

for scenario_name, scenario_path in zip(scenarios, postprocessed_results_paths):

    # Read scenario's Scalars.csv and concat it
    df = pd.read_csv(
        os.path.join(scenario_path, 'Scalars.csv'), index_col=[0])
    all_scalars = pd.concat([all_scalars, df])

    # Copy timeseries directories
    dst = os.path.join(output_path, scenario_name)
    shutil.copytree(scenario_path, dst, ignore=shutil.ignore_patterns(
        'Scalars.csv',
        'oemoflex.log*',
        'oemoflex_scalars.csv',
    ))

# Write concat'ed results
all_scalars.to_csv(
    os.path.join(output_path, 'Scalars.csv')
)
