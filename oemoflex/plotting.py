import os

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

from shapely.geometry import LineString

module_path = os.path.dirname(os.path.abspath(__file__))

regions = pd.read_csv(
    os.path.join(module_path, 'model_structure', 'regions.csv'), squeeze=True)

links = pd.read_csv(os.path.join(module_path, 'model_structure', 'links.csv'))
links['from'] = links['link'].apply(lambda x: x.split('-')[0], 1)
links['to'] = links['link'].apply(lambda x: x.split('-')[1], 1)
# links['geometry']

# Shapefile downloaded from https://thematicmapping.org/downloads/world_borders.php
shapefile_path = os.path.join(
    module_path, 'model_structure', 'TM_WORLD_BORDERS-0.3', 'TM_WORLD_BORDERS-0.3.shp'
)

world = gpd.read_file(shapefile_path)
df = (world.loc[world['ISO2'].isin(regions['region'])])
df.loc[:, 'centroid'] = df.centroid
print(df)
for i, row in links.iterrows():
    print(row)
    from_point = df.loc[df['ISO2'] == row['from'], 'centroid']
    to_point = df.loc[df['ISO2'] == row['to'], 'centroid']
    print(from_point, to_point)
    # line = LineString([from_point, to_point])
    # print(line)

print(links)
print(df)

ax = df.plot(figsize=(10, 10), alpha=0.5, edgecolor='k', color='violet')
plt.savefig('map.pdf')
