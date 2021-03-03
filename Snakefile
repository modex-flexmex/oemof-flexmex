import os

# load experiment config
scenario_yml = "scenarios/{scenario}.yml"

raw = "data/In/v0.06"
results_dir = "results/{scenario}"  # for logging
preprocessed_dir = "results/{scenario}/01_preprocessed"
optimized = "results/{scenario}/02_optimized"
postprocessed = "results/{scenario}/03_postprocessed"

results_template = "flexmex_config/output_template/v0.06/Template"

# Set oemof.tabular sub-paths
preprocessed_data = preprocessed_dir + "/data"
inferred_datapackage = preprocessed_dir + "/datapackage.json"


rule all:
    message:
        "Run entire analysis."
    input:
        "results/{scenario}/03_postprocessed"


rule preprocess:
    message:
        "Preprocess input data for scenario '{wildcards.scenario}'."
    input:
        raw=raw,
        scenario_yml=scenario_yml,
        script="scripts/preprocessing.py",  # re-run if updated
    output:
        directory(preprocessed_data)
    params:
        log=results_dir
    shell:
        "python scripts/preprocessing.py {input.scenario_yml} {input.raw} {output} {params.log}"


rule infer:
    message:
        "Infer meta-data from preprcoessed data for scenario '{wildcards.scenario}'."
    input:
        preprocessed_data,  # for monitoring only
        scenario_yml=scenario_yml,
        script="scripts/infer.py",  # re-run if updated
    output:
        inferred_datapackage
    params:
        # tabular's infer_metadata() expects the datapackage base dir as input:
        preprocessed_dir=preprocessed_dir,
    shell:
        "python scripts/infer.py {input.scenario_yml} {params.preprocessed_dir}"


rule optimize:
    message:
        "Optimize scenario '{wildcards.scenario}'."
    input:
        preprocessed_data,  # for monitoring only
        inferred_datapackage,  # for monitoring only
        scenario_yml=scenario_yml,
        script="scripts/optimization.py"  # re-run if updated
    output:
        directory(optimized)
    params:
        # oemoflex's optimize() expects the datapackage base dir as input:
        preprocessed_dir=preprocessed_dir,
        log=results_dir,
    shell:
        "python scripts/optimization.py {input.scenario_yml} {params.preprocessed_dir}"
        " {output} {params.log}"


rule postprocess:
    message:
        "Postprocess results for scenario '{wildcards.scenario}'."
    input:
        preprocessed_data,  # for monitoring only
        scenario_yml=scenario_yml,
        optimized=optimized,
        results_template=results_template,
        script="scripts/postprocessing.py"  # re-run if updated
    output:
        directory(postprocessed)
    params:
        # Not necessarily as input, whole pipeline must be re-run anyway if this changes:
        raw=raw,
        # postprocessing load_elements() expects the datapackage base dir as input:
        preprocessed_dir=preprocessed_dir,
        log=results_dir,
    shell:
        "python scripts/postprocessing.py {input.scenario_yml}"
        " {params.raw} {params.preprocessed_dir}"
        " {input.optimized} {input.results_template}"
        " {output} {params.log}"


def postprocessed_scenarios(wildcards):
    scenarios = [dirname for dirname in os.listdir("results") if dirname.startswith(wildcards.experiment)]
    # Use the pre-defined path "postprocessed" and expand the inner "scenario" key with the list
    return expand(expand("{postprocessed}/Scalars.csv", postprocessed=postprocessed), scenario=scenarios)


rule join_results:
    message:
        "Join results."
    wildcard_constraints:
        experiment="(FlexMex1|FlexMex2)"
    input:
        # Only use existing scenario runs as an input (function call)
        scenario_list=postprocessed_scenarios,
        script="scripts/join_results.py"  # re-run if updated
    output:
        directory("results/{experiment}")
    shell:
        "python scripts/join_results.py {input.scenario_list} {output}"


rule check_against_default:
    message:
        "Check against default"
    input:
        "results/{scenario}/{processing_step}/"
        "scripts/check.py"  # re-run if updated
    shell:
        "scripts/check.py results/{wildcards.scenario}/{wildcards.processing_step}/"


rule plot_scenario:
    message:
        "Plot scenario {wildcards.scenario}."
    input:
        "results/{scenario}/03_postprocessed"
    output:
        "results/{scenario}/plotted"
    shell:
        "scripts/plot_scenario.py"


rule plot_joined:
    message:
        "Plot."
    input:
        "results/{scenario}/joined"
    output:
        "results/joined_plotted"
    shell:
        "scripts/plot_joined.py"


rule clean:
    message:
        "Delete results."
    shell:
        "rm results/{scenario}"
