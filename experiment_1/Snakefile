# load experiment config

raw = ""
preprocessed = ""
optimized = ""
postprocessed = ""


rule all:
    message:
        "Run entire analysis."
    input:
        "results/{scenario}/003_postprocessed"


rule preprocess:
    message:
        "Preprocess input data for scenario {wildcards.scenario}."
    input:
        raw="raw",
        scenario="scenarios/{scenario}.yml",
        script="scripts/preprocessing.py",  # re-run if updated
    output:
        "results/{scenario}/001_preprocessed"
    shell:
        "scripts/preprocessing.py {input.scenario} {input.raw} {output}"


rule optimize:
    message:
        "Optimize scenario {wildcards.scenario}."
    input:
        "results/{scenario}/preprocessed/"
        "scripts/optimization.py"  # re-run if updated
    output:
        "results/{scenario}/002_optimized"
    shell:
        "scripts/optimization.py results/{scenario}/preprocessed/"


rule postprocess:
    message:
        "Postprocess results for scenario {wildcards.scenario}."
    input:
        "results/{scenario}/optimized/"
        "scripts/postprocessing.py"  # re-run if updated
    output:
        "results/{scenario}/postprocessed"
    shell:
        "scripts/postprocessing.py results/{scenario}/optimized/"


rule join_results:
    message:
        "Join results."
    input:
        "results/{scenario}/preprocessed/"
        "scripts/joining.py"  # re-run if updated
    output:
        "results/joined"
    shell:
        "scripts/joining.py results/{scenario}/postprocessed/"


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
        "results/{scenario}/postprocessed"
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
