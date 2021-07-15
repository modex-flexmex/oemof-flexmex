import os

from oemof_flexmex.helpers import load_yaml

here = os.path.abspath(os.path.dirname(__file__))

plot_labels = load_yaml(os.path.join(here, 'plot_labels.yml'))