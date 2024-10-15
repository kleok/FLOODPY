from shapely.geometry import Polygon
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
import rasterio
import numpy as np
import datetime
import json

def create_polygon(coordinates):
    return Polygon(np.array(coordinates['coordinates']).squeeze())

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

        #Convert GeoDataFrame to GeoJSON format (as a dictionary)
        geojson_str = gdf.to_json()  # This gives the GeoJSON as a string
        geojson_dict = json.loads(geojson_str)  # Convert the string to a dictionary

        #Add top-level metadata (e.g., title, description, etc.)
        geojson_dict['flood_event'] = Floodpy_app.flood_event
        geojson_dict['description'] = "This GeoJSON contains polygons of flooded regions using Sentinel-1 data."
        geojson_dict['produced_by'] = "Floodpy"
        geojson_dict['creation_date_UTC'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
        geojson_dict['flood_datetime_UTC'] = Floodpy_app.flood_datetime_str
        geojson_dict['bbox'] = Floodpy_app.bbox

        #Save the modified GeoJSON with metadata to a file
        with open(Floodpy_app.Flood_map_vector_dataset_filename, "w") as f:
            json.dump(geojson_dict, f, indent=2)

        #gdf.to_file(Floodpy_app.Flood_map_vector_dataset_filename, driver='GeoJSON')