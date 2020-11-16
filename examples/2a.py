from oemoflex.model import ModelPipeline, run_processing_step


sc_name = 'FlexMex1_2a'

sc_specs = None  # load yaml file


# For special cases, the function for loading raw data can be adapted
def func(self):
    print(f"Load raw data from '{self.sc_name}' using adapted function")


setattr(ModelPipeline, 'load_raw', func)

mp = ModelPipeline(sc_name, sc_specs, '.')

if __name__ == '__main__':
    run_processing_step(mp)
