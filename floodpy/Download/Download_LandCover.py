import geopandas as gpd
import requests
import os
from tqdm import tqdm
import rasterio as rio
from rasterio.merge import merge

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
    aoi = gpd.read_file(aoi).iloc[0].explode().geometry
    # load worldcover grid
    s3_url_prefix = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    url = f'{s3_url_prefix}/v100/2020/esa_worldcover_2020_grid.geojson'
    grid = gpd.read_file(url)

    # get grid tiles intersecting AOI
    tiles = grid[grid.intersects(aoi)]

    # works only if AOI covers one tile
    for tile in tqdm(tiles.ll_tile):
        url = f"{s3_url_prefix}/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        r = requests.get(url, allow_redirects=True)
        out_fn = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        with open(os.path.join(savepath, out_fn), 'wb') as f:
            f.write(r.content)    
        
        lc_data = f"ESA_WorldCover_10m_2021_v200.tif"

        if len(tiles) > 1:
            lc_data = os.listdir(savepath)
            raster_data = []
            for r in lc_data:
                raster = rio.open(r)
                raster_data.append(raster)

            mosaic, output = merge(raster_data)
            output_meta = raster.meta.copy()
            output_meta = output_meta.update(
                {"driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": output,})
            
            with rio.open(os.path.join(savepath, lc_data), "w", **output_meta) as m:
                m.write(mosaic)

        else:
            lc_data = f"ESA_WorldCover_10m_2021_v200.tif"
            os.rename(os.path.join(savepath, out_fn), os.path.join(savepath, lc_data))
    
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

    return os.path.join(savepath, lc_data), LC_CATEGORIES, LC_COLORBAR
