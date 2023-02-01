import geopandas as gpd
import requests
import os
from tqdm import tqdm
import rasterio as rio
from rasterio.merge import merge
from rasterio.io import MemoryFile
from rasterio.mask import mask

def worldcover(aoi: str, savepath: str) -> tuple:
    """Downloads landcover maps from worldcover project
    TODO: Clipping raster to AOI, Metadata dictionary from LC classes,
            Visualize on notebook
    Args:
        aoi (str): Path to AOI file to dowload data
        savepath (str): Path to store data

    Returns:
        tuple: the full filename of the downloaded LC map, a dictionary with the fullnames for categories and a dictionary with the RGBA colors  
    """
    # works for one polygon/multipolygon
    aoi_gdf = gpd.read_file(aoi)
    aoi_geometry = aoi_gdf.iloc[0].explode().geometry
    # load worldcover grid
    s3_url_prefix = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    url = f'{s3_url_prefix}/v100/2020/esa_worldcover_2020_grid.geojson'
    grid = gpd.read_file(url)

    # get grid tiles intersecting AOI
    tiles = grid[grid.intersects(aoi_geometry)]

    lc_filenames = []
    # works only if AOI covers one tile
    for tile in tqdm(tiles.ll_tile):
        url = f"{s3_url_prefix}/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        r = requests.get(url, allow_redirects=True)
        out_fn = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        lc_filename = os.path.join(savepath, out_fn)
        lc_filenames.append(lc_filename)
        with open(lc_filename, 'wb') as f:
            f.write(r.content)    
    
    lc_mosaic_filename = os.path.join(savepath,
                        "ESA_WorldCover_10m_2021_v200.tif")

    if len(tiles) > 1:
        # creates a list with rasterio opendataset objects
        tiles_data = []
        for r in lc_filenames:
            raster = rio.open(r)
            tiles_data.append(raster)

        # mergings all tiles in tiles_data
        mosaic, tranform = merge(tiles_data)
        mosaic_meta = raster.meta.copy()
        mosaic_meta.update(
            {"driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": tranform,})
        
        # cropping mosaic using aoi
        with MemoryFile() as memfile:
            with memfile.open(**mosaic_meta) as dst:
                dst.write(mosaic)

            src = memfile.open()
            if src.crs != aoi_gdf.crs:
                aoi_gdf = aoi_gdf.to_crs(src.crs.to_epsg())
            
            mosaic_clip_data, transform = mask(src,
                                               aoi_gdf.geometry,
                                               nodata = mosaic_meta['nodata'],
                                               crop = True)
            
            mosaic_meta.update({"driver": "GTiff",
                    "height": mosaic_clip_data.shape[1],
                    "width": mosaic_clip_data.shape[2],
                    "transform": transform,
                    })
            with rio.open(lc_mosaic_filename, "w", **mosaic_meta) as dst:
                dst.write(mosaic_clip_data)

    else: # we have only one worldcover LC tile

        tile_data = rio.open(lc_filenames[0])
        tile_metadata = tile_data.meta.copy()

        if tile_data.crs != aoi_gdf.crs:
            aoi_gdf = aoi_gdf.to_crs(src.crs.to_epsg())


        tile_clip_data, transform = mask(tile_data,
                                        aoi_gdf.geometry,
                                        nodata = tile_metadata['nodata'],
                                        crop = True)


        tile_metadata.update({"driver": "GTiff",
                "height": tile_clip_data.shape[1],
                "width": tile_clip_data.shape[2],
                "transform": transform,
                })
        
        with rio.open(lc_mosaic_filename, "w", **tile_metadata) as dst:
            dst.write(tile_clip_data)

    # Adding LandCover categories dict
    # As key is the DN number and as value the fullname category 
    LC_CATEGORIES = {0: "No data",
                    10: "Tree cover",
                    20: "Shrubland",
                    30: "Grassland",
                    40: "Cropland",
                    50: "Built-up",
                    60: "Bare/sparse vegetation",
                    70: "Snow and Ice",
                    80: "Permanent water bodies",
                    90: "Herbaceous wetland",
                    95: "Mangroves",
                    100: "Moss and lichen"}
    
    # Adding LandCover colorbar dict
    # Again as DN is the key and value the respective color as RGBA tuple
    LC_COLORBAR = { 0: (0, 0, 0, 0),
                    10: (0, 100, 0, 1),
                    20: (255, 187, 34, 1),
                    30: (255, 255, 76, 1),
                    40: (240, 150, 255, 1),
                    50: (250, 0, 0, 1),
                    60: (180, 180, 180, 1),
                    70: (240, 240, 240, 1),
                    80: (0, 100, 200, 1),
                    90: (0, 150, 160, 1),
                    95: (0, 207, 117, 1),
                    100: (250, 230, 160, 1)}

    return lc_mosaic_filename, LC_CATEGORIES, LC_COLORBAR
