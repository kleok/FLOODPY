import os
from itertools import combinations
import geopandas as gpd
from shapely.ops import unary_union
import rasterio
from rasterio.merge import merge
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.warp import reproject
import numpy as np
from datetime import datetime, timedelta

from floodpy.Download.Sentinel_2_download import Download_S2_data
from floodpy.Preprocessing_S2_data.sts import sentimeseries

def get_S2_background(aoi:str, username:str, password:str, start_time:str, end_time:str, save_path:str, product:str = 'S2MSI1C')->str:
    """Searching and downloads the clearest Sentinel-2 images for the AOI and generates an background image.
    If the AOI is in more than one images (tiles) then finds the best combination to cover it and creates a single
    background image.

    Args:
        aoi (str): Path to AOI file
        username (str): ESA Scihub username
        password (str): ESA Scihub password
        start_time (str): Starting search time (YYYYMMDD format)
        end_time (str): Ending search time (YYYYMMDD format)
        save_path (str): Path to store the data
        product (str, optional): Sentinel-2 product level. Defaults to 'S2MSI1C'

    Returns:
        str: Path of the background image
    """
    RGB_Background = os.path.join(save_path, "background.tif")

    #changing starting data in order to create S2 background with less clouds
    start_time_dt = datetime.strptime(start_time, '%Y%m%d') - timedelta(days=90)
    start_time = start_time_dt.strftime('%Y%m%d')

    data = Download_S2_data(
                        AOI = aoi,
                        user = username,
                        passwd = password,
                        Start_time = start_time,
                        End_time = end_time,
                        write_dir = save_path,
                        product = product,
                        download = False,
                        cloudcoverage = 100,
                        cov_thres=0,
                        to_file = True)
        
    # Getting unique tiles over the region
    tiles = data["tile"].unique()
    tiles_coverage = {}
    combination = None # Initializing a combination variable to None 
    # Searching if a single tile covers the AOI
    for tile in tiles:
        for _, row in data.iterrows():
            if row["coverages"] == 1:
                combination = [row["tile"]]
                break
    # If the combination variable is still None then more than one tiles is required
    if combination is None:
        for tile in tiles:
            for _, row in data.iterrows():
                if row["tile"] == tile:
                    tiles_coverage[tile] = row["geometry"] # find all unique coverages per tile and store them in a dict
                    break
        # Create all possible tile combinations
        combs = sum([list(map(list, combinations(tiles, i))) for i in range(len(tiles) + 1)], [])
        combs.pop(0) # Just remove the empty one
        
        # Reading geometry
        aoi_geometry = gpd.read_file(aoi).iloc[0].geometry
        # Searching for the first available combination to fill the AOI
        for c in combs:
            if len(c)>1:
                geometries = [tiles_coverage[x] for x in c]
                merged = unary_union(geometries)
                intesection_area = merged.intersection(aoi_geometry).area
                ratio = intesection_area/aoi_geometry.area
                if ratio == 1:
                    combination = c
                    break
    # The combination of tiles is completed
    # Downloading the products
    filenames = []
    for tile in combination:
        tile_df = data.loc[data["tile"] == tile]
        clearest_image = tile_df.loc[tile_df["cloudcoverpercentage"] == tile_df["cloudcoverpercentage"].min()]
        _ = Download_S2_data(
                    AOI = aoi,
                    user = username,
                    passwd = password,
                    Start_time = clearest_image,
                    End_time = end_time,
                    write_dir = save_path,
                    product = product,
                    download = True,
                    cloudcoverage = 100,
                    cov_thres=0,
                    to_file = False,
                    filename = clearest_image["filename"][0])
        filenames.append(clearest_image["filename"][0].split(".")[0] + ".zip")
    # Creating an object with the data
    eodata = sentimeseries("Background-data")
    for files in filenames:
        eodata.find_zip(os.path.join(save_path, files))
    # Two case scenario: One tile or many (probably under different CRS)
    if len(filenames) > 1:
        merge_images = []
        default_crs = rasterio.open(eodata.data[0].TCI["10"]["raw"]).crs
        merge_images.append(rasterio.open(eodata.data[0].TCI["10"]["raw"]))
        for image in eodata.data[1:]:
            src = rasterio.open(image.TCI["10"]["raw"])
            metadata = src.meta.copy()
            if src.crs != default_crs:
                reproj, reproj_trans = reproject(source = src.read(),
                        destination = np.empty(shape=src.read().shape),
                        src_transform = src.transform,
                        src_crs = src.crs,
                        dst_crs = default_crs)

                metadata.update({"driver": "GTiff",
                    "height": reproj.shape[1],
                    "width": reproj.shape[2],
                    "transform": reproj_trans,
                    "crs": default_crs
                    })
                with MemoryFile() as memfile:
                    with memfile.open(**metadata) as dst:
                        dst.write(reproj)
                    merge_images.append(memfile.open())
            else:
                merge_images.append(rasterio.open(image.TCI["10"]["raw"]))

        mosaic, transform = merge(merge_images)
        metadata.update({"driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": transform,
                })

        with MemoryFile() as memfile:
            with memfile.open(**metadata) as dst:
                dst.write(mosaic)

            src = memfile.open()
            shapes = gpd.read_file(aoi)
            if src.crs != shapes.crs:
                shapes = shapes.to_crs(src.crs.to_epsg())
            
            data, transform = mask(src, shapes.geometry, nodata = 0, crop = True)
            metadata.update({"driver": "GTiff",
                    "height": data.shape[1],
                    "width": data.shape[2],
                    "transform": transform,
                    })
            with rasterio.open(RGB_Background, "w", **metadata) as dst:
                dst.write(data)
    else:
        src = rasterio.open(eodata.data[0].TCI["10"]["raw"])
        metadata = src.meta.copy()
        shapes = gpd.read_file(aoi)
        if src.crs != shapes.crs:
            shapes = shapes.to_crs(src.crs.to_epsg())
        
        data, transform = mask(src, shapes.geometry, nodata = 0, crop = True)
        metadata.update({"driver": "GTiff",
                "height": data.shape[1],
                "width": data.shape[2],
                "transform": transform,
                })
        with rasterio.open(RGB_Background, "w", **metadata) as dst:
            dst.write(data)
    
    return RGB_Background