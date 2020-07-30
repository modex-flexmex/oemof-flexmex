import os

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd


module_path = os.path.dirname(os.path.abspath(__file__))

countries = list(
    pd.read_csv(os.path.join(module_path, 'model_structure', 'regions.csv'), squeeze=True)['name']
)

link_list = list(
    pd.read_csv(os.path.join(module_path, 'model_structure', 'links.csv'), squeeze=True)
)

# Shapefile downloaded from https://thematicmapping.org/downloads/world_borders.php
shapefile_path = os.path.join(
    module_path, 'model_structure', 'TM_WORLD_BORDERS-0.3', 'TM_WORLD_BORDERS-0.3.shp'
)

world = gpd.read_file(shapefile_path)

europe = (world.loc[world['NAME'].isin(countries)])

ax = europe.plot(figsize=(10, 10), alpha=0.5, edgecolor='k')
plt.show()
