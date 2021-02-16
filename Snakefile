# load experiment config

raw = ""
preprocessed = ""
optimized = ""
postprocessed = ""


rule all:
    message:
        "Run entire analysis."
    input:
        "results/{scenario}/03_postprocessed"


rule preprocess:
    message:
        "Preprocess input data for scenario '{wildcards.scenario}'."
    input:
        raw="data/In/v0.06",
        scenario_yml="scenarios/{scenario}.yml",
        script="scripts/preprocessing.py",  # re-run if updated
    output:
        directory("results/{scenario}/01_preprocessed")
    shell:
        "python --version & "
        "echo \"Virtualenv:\" $VIRTUAL_ENV &"
        "python scripts/preprocessing.py {input.scenario_yml} {input.raw} {output}"


rule optimize:
    message:
        "Optimize scenario {wildcards.scenario}."
    input:
        "results/{scenario}/01_preprocessed/"
        "scripts/optimization.py"  # re-run if updated
    output:
        "results/{scenario}/02_optimized"
    shell:
        "scripts/optimization.py results/{scenario}/preprocessed/"


rule postprocess:
    message:
        "Postprocess results for scenario {wildcards.scenario}."
    input:
        "results/{scenario}/02_optimized/"
        "scripts/postprocessing.py"  # re-run if updated
    output:
        "results/{scenario}/03_postprocessed"
    shell:
        "scripts/postprocessing.py results/{scenario}/optimized/"


rule join_results:
    message:
        "Join results."
    input:
        "results/{scenario}/01_preprocessed/"
        "scripts/joining.py"  # re-run if updated
    output:
        "results/joined"
    shell:
        "scripts/joining.py results/{scenario}/03_postprocessed/"


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
