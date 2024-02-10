# import geopandas as gpd
# import folium

# # world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
# # world.plot()


# # import matplotlib.pyplot as plt
# # plt.show()

import folium

center = [45, -30]

m = folium.Map(location=center, zoom_start=3)

# folium.Marker([33.756342349687586, -84.39351094004493], popup='<h1>My Favourite Stadium</h1><img src="stadium.jpeg" width=400px><p>This is the best stadium out in Atl</p>', tooltip='ElCruzo Stadium', icon=folium.Icon(icon='heart', icon_color='red', color='green')).add_to(m)

# folium.Circle(
#     location=(33.75596703814469, -84.38916676893841),
#     radius=800,
#     popup="Love the area",
#     color='blue',
#     fill=True,
#     fill_color='blue'
# ).add_to(m)

m.save('map.html')