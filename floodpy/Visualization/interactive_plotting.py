import geopandas as gpd
import rasterio as rio
import rasterio.mask
import os
import pandas as pd
import xarray as xr
import numpy as np

# plotting functionalities
import matplotlib.pyplot as plt
import folium
import matplotlib
from branca.element import Template, MacroElement
import branca.colormap as cm
from folium.plugins import MeasureControl, Draw
from xyzservices.lib import TileProvider

# FLOODPY libraries
from floodpy.utils.folium_categorical_legend import get_folium_categorical_template

def plot_interactive_map(Floodpy_app):

    # Read AOI
    aoi = gpd.read_file(Floodpy_app.geojson_bbox)

    # AOI bounds
    left, bottom, right, top = aoi.total_bounds

    # Define map bounds
    map_bounds = [[bottom, left], [top, right]]

    # Create a map located to the AOI
    m = folium.Map(location=[aoi.centroid.y[0], aoi.centroid.x[0]], tiles="openstreetmap", zoom_start=13)

    folium.TileLayer("openstreetmap").add_to(m)
    folium.TileLayer('cartodbdark_matter').add_to(m)

    # measuring funcs
    MeasureControl('bottomleft').add_to(m)

    # drawing funcs
    draw = Draw(export = True,
                filename=os.path.join(Floodpy_app.projectfolder,'myJson.json'),
                position='topleft').add_to(m)

    # add geojson AOI
    folium.GeoJson(aoi["geometry"],
                show = False,
                name='Area of Interest').add_to(m)

    #------------------------------------------------------------------------------
    # ESA worldcover 

    with rio.open(Floodpy_app.lc_mosaic_filename) as src:
        LC_cover, out_transform = rasterio.mask.mask(src, aoi.geometry, crop=True)
        LC_cover = LC_cover[0,:,:]

    LC_map = folium.raster_layers.ImageOverlay(image = LC_cover,
                                            name = 'ESA Worldcover 2021',
                                            opacity = 1,
                                            bounds = map_bounds,
                                            show = False,
                                            colormap = lambda x: Floodpy_app.LC_COLORBAR[x])

    m.add_child(LC_map)

    legend_categories = {Floodpy_app.LC_CATEGORIES[x]: Floodpy_app.LC_COLORBAR[x] for x in np.unique(LC_cover)}

    template = get_folium_categorical_template(legend_categories)
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)

    #------------------------------------------------------------------------------
    # S1 VV backscatter Flood image

    S1_stack_dB = xr.open_dataset(Floodpy_app.S1_stack_filename)['VV_dB']
    Flood_data = S1_stack_dB.sel(time = pd.to_datetime(Floodpy_app.flood_datetime_str)).values

    vmin = np.nanquantile(Flood_data, 0.01)
    vmax = np.nanquantile(Flood_data, 0.99)

    S1_data = np.clip(Flood_data, vmin, vmax)

    cmap = cm.LinearColormap(['black', 'white'],
                                index=[vmin, vmax],
                                vmin=vmin, vmax=vmax)

    cmap.caption = "Backscatter coefficient VV (dB)"
    cmap_func = lambda x: matplotlib.colors.to_rgba(cmap(x)) if ~np.isnan(x) else (0,0,0,0)

    folium.raster_layers.ImageOverlay(image = S1_data,
                                    name = "Sentinel-1 ({})".format(Floodpy_app.flood_datetime_str),
                                    opacity = 1,
                                    bounds = map_bounds,
                                    colormap = cmap_func).add_to(m)
    m.add_child(cmap)

    #------------------------------------------------------------------------------
    # Flood binary mask

    Flood_map_dataset = xr.open_dataset(Floodpy_app.Flood_map_dataset_filename)
    flooded_regions = Flood_map_dataset.flooded_regions.data.astype(np.int32)

    raster_to_coloridx = {1: (0.0, 0.0, 1.0, 0.8),
                        0: (0.0, 0.0, 0.0, 0.0)}

    m.add_child(folium.raster_layers.ImageOverlay(image = flooded_regions, 
                                                name = 'Flooded Regions {} (UTC)'.format(Floodpy_app.flood_datetime_str),
                                                bounds = map_bounds,
                                                colormap = lambda x: raster_to_coloridx[x]))

    folium.LayerControl('bottomleft', collapsed=False).add_to(m)

    return m
