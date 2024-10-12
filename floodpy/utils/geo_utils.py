from shapely.geometry import Polygon
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
import rasterio
import numpy as np
import datetime
import json

colorTones = {
  6: '#CC3A5D', # dark pink
  5: '#555555',   # dark grey 
  4: '#A17C44',  # dark brown
  3: '#8751A1', # dark purple
  2: '#C1403D', # dark red
  1: '#2E5A87',  # dark blue
  0: '#57A35D', # dark green
}


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

        #Convert GeoDataFrame to GeoJSON format (as a dictionary)
        geojson_str = gdf.to_json()  # This gives the GeoJSON as a string
        geojson_dict = json.loads(geojson_str)  # Convert the string to a dictionary

        # find the color of plotting
        color_ind = Floodpy_app.flood_datetimes.index(Floodpy_app.flood_datetime) 
        plot_color = colorTones[color_ind]
        #Add top-level metadata (e.g., title, description, etc.)
        geojson_dict['flood_event'] = Floodpy_app.flood_event
        geojson_dict['description'] = "This GeoJSON contains polygons of flooded regions using Sentinel-1 data."
        geojson_dict['produced_by'] = "Floodpy"
        geojson_dict['creation_date_UTC'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
        geojson_dict['flood_datetime_UTC'] = Floodpy_app.flood_datetime_str
        geojson_dict['plot_color'] = plot_color
        geojson_dict['bbox'] = Floodpy_app.bbox

        #Save the modified GeoJSON with metadata to a file
        with open(Floodpy_app.Flood_map_vector_dataset_filename, "w") as f:
            json.dump(geojson_dict, f, indent=2)

        #gdf.to_file(Floodpy_app.Flood_map_vector_dataset_filename, driver='GeoJSON')