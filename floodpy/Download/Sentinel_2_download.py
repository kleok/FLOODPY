#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shapely
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import geopandas as gpd
import pandas as pd
import os

def S2_AOI_coverage(aoi_geometry:shapely.geometry, products_df:gpd.GeoDataFrame)->gpd.GeoDataFrame:
    """Generates the coverage between the satellite images and the AOI.

    Args:
        aoi_geometry (shapely.geometry): AOI as shapely geometry
        products_df (gpd.GeoDataFrame): GeoDataFrame with all the available products that intersect with the AOI

    Returns:
        gpd.GeoDataFrame: Returns GeoDataFrame with an extra coverage percentage field
    """
    coverage_percents = []
    for _, product in products_df.iterrows():
        intesection_area = product.geometry.intersection(aoi_geometry).area
        coverage_percents.append(intesection_area/aoi_geometry.area)
    products_df['coverages'] = coverage_percents
    return products_df
    

def Download_S2_data(AOI:str, user:str, passwd:str, Start_time:str, End_time:str, write_dir:str, product:str = 'S2MSI1C', download:bool = False, cloudcoverage:float = 100, cov_thres:float = 0.5, to_file:bool = True, filename = None)->None:
    """Download Sentinel 2 imagery.

    Args:
        AOI (str): Path to AOI file
        user (str): APIHUB username
        passwd (str): APIHUB password
        product (str): S2MSI2A or S2MSI1C. Defaults to 'S2MSI2A'
        Start_time (str): Start date. Format YYYYMMDD
        End_time (str): End date. Format YYYYMMDD
        write_dir (str): Path to write data
        download (bool, optional): If True downloads data. Defaults to True
        cloudcoverage(float, optional): Maximum cloud coverage. Defaults to 100
        cov_thres(float, optional): Minimum allowed coverage percentage between AOI and data footprint
        to_file(bool, optional): Save all product to be downloaded to a CSV file. Defaults to True
    """
    
    api = SentinelAPI(user, passwd, api_url='https://apihub.copernicus.eu/apihub', show_progressbars=True, timeout=None)
    footprint = geojson_to_wkt(read_geojson(AOI))
    aoi_geometry = gpd.read_file(AOI).iloc[0].geometry
    
    if filename is not None:
        query_kwargs = {'platformname': 'Sentinel-2',
            'filename': filename}
    else:
        query_kwargs = {'area':footprint,
            'platformname': 'Sentinel-2',
            'producttype': product,
            'cloudcoverpercentage': (0, cloudcoverage),
            'date': (Start_time, End_time)}

    pp = api.query(**query_kwargs)

    products_df = api.to_geodataframe(pp)
    
    products_df = S2_AOI_coverage(aoi_geometry, products_df)
    
    products_df = products_df[products_df['coverages']> cov_thres] 
    print(products_df["filename"])
    products_df["tile"] = products_df.apply(lambda tile: tile["filename"].split("_")[5], axis = 1)
    
    if to_file:
        df = pd.DataFrame(products_df.drop(columns='geometry'))
        df.to_csv(os.path.join(write_dir, "S2_products.csv"))

    if download == True:
        # When trying to download an offline product with download_all(), the method will instead attempt to trigger its retrieval from the LTA.
        api.download_all(products_df.index , directory_path = write_dir)
    
    return products_df

