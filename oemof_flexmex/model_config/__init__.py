import os
import pandas as pd
from collections import OrderedDict
from oemof_flexmex.helpers import load_yaml

here = os.path.abspath(os.path.dirname(__file__))

plot_labels = load_yaml(os.path.join(here, "plot_labels.yml"))

colors_csv = pd.read_csv(
    os.path.join(here, "plot_colors.csv"), header=[0], index_col=[0]
)
colors_csv = colors_csv.T
colors_odict = OrderedDict()
for i in colors_csv.columns:
    colors_odict[i] = colors_csv.loc["Color", i]
