from shapely.geometry import Polygon
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
import rasterio
import numpy as np

def create_polygon(coordinates):
    return Polygon(coordinates['coordinates'][0])


def convert_to_vector(Floodpy_app):
    with rasterio.open(Floodpy_app.Flood_map_dataset_filename) as src:
        data = src.read(1).astype(np.int16)

        # Use a generator instead of a list
        shape_gen = ((shape(s), v) for s, v in shapes(data, transform=src.transform))

        # either build a pd.DataFrame
        # df = DataFrame(shape_gen, columns=['geometry', 'class'])
        # gdf = GeoDataFrame(df["class"], geometry=df.geometry, crs=src.crs)

        # or build a dict from unpacked shapes
        gdf = gpd.GeoDataFrame(dict(zip(["geometry", "flooded_regions"], zip(*shape_gen))), crs=src.crs)
        gdf = gdf.loc[gdf.flooded_regions == 1,:]
        gdf.datetime = Floodpy_app.flood_datetime_str

        gdf.to_file(Floodpy_app.Flood_map_vector_dataset_filename, driver='GeoJSON')