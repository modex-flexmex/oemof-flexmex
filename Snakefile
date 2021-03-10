import os

# Configuration
scenario_yml = "scenarios/{scenario}.yml"
raw_dir = "data/In/v0.06"
preprocessed_dir = "results/{scenario}/01_preprocessed"
optimized_dir = "results/{scenario}/02_optimized"
postprocessed_dir = "results/{scenario}/03_postprocessed"
results_template = "flexmex_config/output_template/v0.06_alt/Template"
log_dir = "results/{scenario}"
results_joined_dir = "results/{experiment}"

# Set oemof.tabular sub-paths
preprocessed_data = os.path.join(preprocessed_dir, "data")
inferred_datapackage = os.path.join(preprocessed_dir, "datapackage.json")


rule all:
    # Test: snakemake -npr
    # Run: snakemake -j1
    message:
        "Run entire analysis."
    input:
        # Read-in a complete list of scenarios (all the files found by 'scenario_yml')
        expand(
            postprocessed_dir,
            scenario=[os.path.splitext(d)[0] for d in os.listdir(os.path.dirname(scenario_yml))]
        )


rule preprocess:
    message:
        "Preprocess input data for scenario '{wildcards.scenario}'."
    input:
        raw=raw_dir,
        scenario_yml=scenario_yml,
        script="scripts/preprocessing.py",  # re-run if updated
    output:
        directory(preprocessed_data)
    params:
        log=log_dir
    benchmark:
        os.path.join(log_dir, "benchmark-preprocess.log")
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
    benchmark:
        os.path.join(log_dir, "benchmark-infer.log")
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
        directory(optimized_dir)
    params:
        # oemoflex's optimize() expects the datapackage base dir as input:
        preprocessed_dir=preprocessed_dir,
        log=log_dir,
    benchmark:
        os.path.join(log_dir, "benchmark-optimize.log")
    shell:
        "python scripts/optimization.py {input.scenario_yml} {params.preprocessed_dir}"
        " {output} {params.log}"


rule postprocess:
    message:
        "Postprocess results for scenario '{wildcards.scenario}'."
    input:
        preprocessed_data,  # for monitoring only
        scenario_yml=scenario_yml,
        optimized=optimized_dir,
        results_template=results_template,
        script="scripts/postprocessing.py"  # re-run if updated
    output:
        directory(postprocessed_dir)
    params:
        # Not necessarily as input, whole pipeline must be re-run anyway if this changes:
        raw=raw_dir,
        # postprocessing load_elements() expects the datapackage base dir as input:
        preprocessed_dir=preprocessed_dir,
        log=log_dir,
    benchmark:
        os.path.join(log_dir, "benchmark-postprocess.log")
    shell:
        "python scripts/postprocessing.py {input.scenario_yml}"
        " {params.raw} {params.preprocessed_dir}"
        " {input.optimized} {input.results_template}"
        " {output} {params.log}"


def processed_scenarios(wildcards):
    # Returns a list of scenarios with completed postprocessing.

    def postprocessing_data_exist(path):
        return os.path.isdir(postprocessed_dir.format(scenario=path))

    scenarios = [
        dirname for dirname in os.listdir("results")
        if dirname.startswith(wildcards.experiment)  # only FlexMex1_ or FlexMex2_ directories
        and dirname != wildcards.experiment  # exclude this rule's output directory
        and postprocessing_data_exist(dirname)  # only postprocessed scenarios
    ]
    return scenarios


def postprocessed_paths(wildcards):
    # Wrap scenario names into their respective postprocessed paths (pre-defined above)
    # 'scenario' is wildcard in 'postprocessed'
    return expand(postprocessed_dir, scenario=processed_scenarios(wildcards))


rule join_results:
    message:
        "Join results."
    wildcard_constraints:
        experiment="(FlexMex1|FlexMex2)"
    input:
        script="scripts/join_results.py"  # re-run if updated
    output:
        directory(results_joined_dir)
    params:
        # Only use existing scenario runs as an input (function call)
        # As 'params' to prevent preceding steps from being run
        scenario_paths=postprocessed_paths,
        scenarios=processed_scenarios,
    script:
        "scripts/join_results.py"

rule analyze_cputime:
    message:
        "Time measurement output."
    input:
        script="scripts/analyze_cputime.py"  # re-run if updated
    output:
        touch(os.path.join(log_dir, "cpu_time_analysis.done"))
    params:
        input_dir=log_dir,
        output_path=os.path.join(log_dir, "cpu_time_analysis.csv")
    shell:
         "python scripts/analyze_cputime.py {wildcards.scenario}"
         " {params.input_dir}"
         " {params.output_path}"