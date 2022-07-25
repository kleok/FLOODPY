import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box
import os

wd = os.chdir(os.path.dirname(__file__))

s2_orbits = gpd.read_file('S2_orbit.gpkg')

s2_umtz = gpd.read_file('S2_utm_zones.gpkg')

s2_tiles = gpd.read_file('S2_tiles.gpkg')

x_min, y_min, x_max, y_max = s2_orbits.total_bounds


### Random Polygon

# set sample size
n = 100
# generate random data within the bounds
x = np.random.uniform(x_min, x_max, n)
y = np.random.uniform(y_min, y_max, n)
shapes = [box(bla[0], bla[1], bla[0]+0.5, bla[1]+0.5) for bla in list(zip(x,y))]
# convert them to a polygon GeoSeries
gdf_polygons = gpd.GeoSeries(shapes)
# only keep those polygons within polygons
gdf_polygons = gdf_polygons[gdf_polygons.within(s2_orbits.unary_union)]
gdf_polygons.iloc[0:1].to_file(
    'test_polygon.shp',
    crs=s2_orbits.crs,
    geometri='geometry',
    drive='ESRI Shapefile')

# Test polygon
tpol=gdf_polygons.iloc[0]
print(tpol)

# Orbits intersecting with AOI
df_intersected_orbits = s2_orbits[s2_orbits.intersects(tpol)]
intersecting_orbits = df_intersected_orbits['OrbitRelative'].tolist()

# Keep within orbits
df_within_orbits = df_intersected_orbits[df_intersected_orbits.contains(tpol)]
within_orbits = df_within_orbits['OrbitRelative'].tolist()

if len(within_orbits) == 1:
    print(f"AOI in single orbit: {within_orbits}")
    forbit = within_orbits
elif len(within_orbits) > 1:
    print(f"AOI in intersecting orbits: {within_orbits}")
    forbit = within_orbits
elif len(within_orbits) == 0:
    print(f"AOI splits between orbits: {intersecting_orbits}")
    forbit = intersecting_orbits
else:
    print(f"AOI WTF orbit {intersecting_orbits}")
    forbit = intersecting_orbits

# f, ax = plt.subplots()
# df_intersected_orbits.plot(ax=ax, cmap='tab20c', alpha=0.5)
# gdf_polygons.iloc[0:1].plot(ax=ax, color='red')
# plt.show()


# utm_zones intersecting with AOI
df_intersected_utmz = s2_umtz[s2_umtz.intersects(tpol)]
intersecting_utmz = df_intersected_utmz['utm'].tolist()

# Keep within utm_zones
df_within_utmz = s2_umtz[s2_umtz.contains(tpol)]
within_utmz = df_within_utmz['utm'].tolist()

if len(within_utmz) == 1:
    print(f"AOI in single utm-zone: {within_utmz}")
    futmz = within_utmz
elif len(within_utmz) > 1:
    print(f"AOI in intersecting utm-zones: {within_utmz}")
    futmz = within_utmz
elif len(within_utmz) == 0:
    print(f"AOI splits between utm-zones: {intersecting_utmz}")
    futmz = intersecting_utmz
else:
    print(f"AOI WTF utm-zone {intersecting_utmz}")
    futmz = intersecting_utmz

# f, ax = plt.subplots()
# df_intersected_utmz.plot(ax=ax, cmap='tab20c', alpha=0.5)
# gdf_polygons.iloc[0:1].plot(ax=ax, color='red')
# plt.show()


# Tiles intersecting with AOI
df_intersected_tiles = s2_tiles[s2_tiles.intersects(tpol) & s2_tiles['utm_zone'].isin(futmz)]
intersecting_tiles = df_intersected_tiles['tilename'].tolist()

# Keep within tiles
df_within_tiles = s2_tiles[s2_tiles.contains(tpol) & s2_tiles['utm_zone'].isin(futmz)]
within_tile = df_within_tiles['tilename'].tolist()

if len(within_tile) == 1:
    print(f"AOI in single tile: {within_tile}")
    ftile = within_tile
elif len(within_tile) > 1:
    print(f"AOI in intersecting tiles: {within_tile}")
    ftile = within_tile
elif len(within_tile) == 0:
    print(f"AOI splits between tiles: {intersecting_tiles}")
    ftile = intersecting_tiles
else:
    print(f"AOI WTF tile {intersecting_tiles}")
    ftile = intersecting_tiles


# f, ax = plt.subplots()
# df_intersected_tiles.plot(ax=ax, cmap='tab20c', alpha=0.5)
# gdf_polygons.iloc[0:1].plot(ax=ax, color='red')
# plt.show()