import geopandas as gpd

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world.plot()


import matplotlib.pyplot as plt
plt.show()