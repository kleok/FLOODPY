import geopandas as gpd
import requests
import os
from tqdm import tqdm
import rasterio as rio
from rasterio.merge import merge

def worldcover(aoi:str, savepath:str)->gpd.GeoDataFrame:
    """Downloads landcover maps from worldcover project

    Args:
        aoi (str): Path to AOI file to dowload data
        savepath (str): Path to store data

    Returns:
        gpd.GeoDataFrame: Downloaded tiles 
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
    
    #TODO Clipping raster to AOI
    #TODO Metadata dictionary from LC classes 
    #TODO Visualize on notebook