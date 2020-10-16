import oemof
import oemof.tabular
from oemoflex.helpers import make_dirs


class Usecase:

    def __init__(self, name, basepath, datapath, components):
        self.name = name
        self.basepath = basepath
        self.datapath = datapath
        self.components = components

        self.init_logging()
        self.dirs = self.setup_directories()
        self.read_input_data()

    def init_logging(self):
        pass

    def setup_directories(self):
        dirs = self.read_dirs_from_config()
        make_dirs(dirs)
        return dirs

    def read_input_data(self):
        # read input data from directories
        # filter input data for use case
        pass

    def run(self):
        self.preprocess()
        self.infer()
        self.optimize()
        self.postprocess()

    def preprocess(self):
        self.setup_components()
        self.setup_timeseries()

    def setup_components(self):
        # the 'update_...' functions
        # process self.components
        pass

    def setup_timeseries(self):
        # the 'create_..._profile' functions
        pass

    def infer(self):
        pass

    def optimize(self):
        pass

    def postprocess(self):
        pass
