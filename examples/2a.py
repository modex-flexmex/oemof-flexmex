# This part will be in the module oemoflex/model.py


class ModelPipeline():
    def __init__(self, sc_name, sc_specs, root_dir):
        self.sc_name = sc_name

        self.sc_specs = sc_specs

        self.root_dir = root_dir

        self.logging = self.setup_logging()

        self.exp_dirs = self.setup_experiment_dirs()

        self.raw = None

        self.preprocessed = None

        self.metadata = None

        self.optimized = None

        self.postprocessed = None

    def setup_logging(self):
        pass

    def setup_experiment_dirs(self):
        experiment_dirs = None
        return experiment_dirs

    def setup_model_structure(self):
        pass

    def load_raw(self):
        print(f"Load raw data from '{self.sc_name}'")

    def parametrize(self):
        # Here, the update functions and create timeseries are called
        print(f"Parametrize scenario '{self.sc_name}'")

    def infer(self):
        print(f"Infer metadata for scenario '{self.sc_name}'")

    def optimize(self):
        print(f"Optimize scenario '{self.sc_name}'")

    def postprocess(self):
        print(f"Postprocess scenario '{self.sc_name}'")

    def map_results(self):
        # This maps the results to the projects data format.
        print(f"Mapping results for scenario '{self.sc_name}'")

    def run_all(self):
        print(f"Run scenario '{self.sc_name}'")
        self.load_raw()
        self.setup_model_structure()
        self.parametrize()
        self.infer()
        self.optimize()
        self.postprocess()
        self.map_results()


def run_processing_step(mp):
    if len(sys.argv) == 1:

        mp.run_all()

    elif len(sys.argv) > 1:

        processing_step = sys.argv[1]

        getattr(mp, processing_step)()


# This part could be the one remaining in UC scripts:
import sys

sc_name = 'FlexMex1_2a'

sc_specs = None  # load yaml file


# For special cases, the function for loading raw data can be adapted
def func(self):
    print(f"Load raw data from '{self.sc_name}' using adapted function")


setattr(ModelPipeline, 'load_raw', func)

mp = ModelPipeline(sc_name, sc_specs, '.')

if __name__ == '__main__':
    run_processing_step(mp)
