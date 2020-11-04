# This part will be in the module oemoflex/model.py

class ModelPipeline():
    def __init__(self, sc_name, sc_specs, root_dir):
        self.sc_name = sc_name

        self.sc_specs = sc_specs

        self.root_dir = root_dir

        self.exp_dirs = None

        self.raw = None

        self.preprocessed = None

        self.metadata = None

        self.optimized = None

        self.postprocessed = None

    def load_raw(self):
        print(f"Load raw data from '{self.sc_name}'")

    def preprocess(self):
        print(f"Preprocess scenario '{self.sc_name}'")

    def infer(self):
        print(f"Infer metadata for scenario '{self.sc_name}'")

    def optimize(self):
        print(f"Optimize scenario '{self.sc_name}'")

    def postprocess(self):
        print(f"Postprocess scenario '{self.sc_name}'")

    def run_all(self):
        print(f"Run scenario '{self.sc_name}'")
        self.load_raw()
        self.preprocess()
        self.optimize()
        self.infer()
        self.postprocess()


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
