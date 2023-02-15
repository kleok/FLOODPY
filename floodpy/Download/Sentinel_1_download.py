#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import os
import glob
import time
import numpy as np
import pandas as pd
import subprocess
from datetime import datetime
import geopandas as gpd

def check_downloaded_data(S1_dir:str,product_df_suffle:pd.DataFrame)-> tuple:
    """
    Based on already downloaded Sentinel-1 products in S1_dir we return 
    only the products that we still need to download.
    
    Improvements: Check the size and the integrity of each downloaded product.
    
    Args:
        S1_dir (string): The directory that the Sentinel-1 products will be downloaded.
        product_df_suffle (pandas.DataFrame): The results from sentinesat request.

    Returns:
        product_df_suffle (pandas.DataFrame): The Sentinel-1 products that will be downloaded.
        ongoing_download (boolean): True if we have products to download.
    """
    
    ongoing_download=False
    
    # checking if all the products are already downloaded!
    already_downloaded_data=glob.glob(os.path.join(S1_dir,'S1*.zip'))
    
    products_to_be_download=sorted([product.split('.')[0] for product in product_df_suffle['filename'].tolist()])
    products_already_download=sorted([os.path.basename(product).split('.')[0] for product in already_downloaded_data])

    for product in products_to_be_download:
        if product not in products_already_download:
            ongoing_download = True
        else:
            product_df_suffle.drop(product_df_suffle[product_df_suffle['title']==product].index, inplace=True)
            
    if len(product_df_suffle)>0:
       ongoing_download = True 
    
    return product_df_suffle, ongoing_download   


def download_products(scihub_username:str,
                      scihub_password:str,
                      aria_username:str,
                      aria_password:str,
                      products_df: pd.DataFrame,
                      download_variant:str,
                      geojson_S1:str,
                      S1_type:str,
                      S1_dir:str)-> None:
    """
    Download functionality of Sentinel-1 products
    
    Args:
        product_to_be_downloaded_df (pandas.DataFrame): Sentinel-1 products to download.
        download_variant (string) : Download variant (sentinelsat or aria2c)
        S1_dir (string): The directory that the Sentinel-1 products will be
                             downloaded.
    """

    os.chdir(S1_dir)
    # for each product do the following
    if download_variant == 'sentinelsat':
        for product in products_df['index']:
            api = SentinelAPI(scihub_username,
                              scihub_password,
                              'https://scihub.copernicus.eu/dhus')
            # download single scene by known product id
            api.download(product)
    elif download_variant == 'aria2c':
        # more info at: https://docs.asf.alaska.edu/api/tools/
        for index, product in products_df.iterrows():
            #print(product)
            # known Sentinel-1 product
            parms = ("--http-auth-challenge=true --http-user=\'"
                    +aria_username
                    +"\' --http-passwd=\'"
                    +aria_password
                    +"\' --continue=true --auto-file-renaming=false"
                    +" \"https://api.daac.asf.alaska.edu/services/search/param?granule_list="
                    +product['title']+"&output=metalink\"")
                    
            subprocess.check_call("aria2c "+parms,shell=True)
            # #---------- query using aria2c
            # aoi_polygon = str(gpd.read_file(geojson_S1).geometry[0])
            # aoi_polygon = aoi_polygon.replace("POLYGON ", "POLYGON")
            # #aoi_polygon = str(product['footprint'])

            # orbit_number = str(product['relativeorbitnumber'])
            # start_datetime = product['beginposition']
            # start_year = '{:04d}'.format(start_datetime.year)
            # start_month = '{:02d}'.format(start_datetime.month)
            # start_day = '{:02d}'.format(start_datetime.day)
            # start_hour = '{:02d}'.format(start_datetime.hour)
            # start_minute = '{:02d}'.format(start_datetime.minute)
            
            # end_datetime = product['endposition']
            # end_year = '{:04d}'.format(end_datetime.year)
            # end_month = '{:02d}'.format(end_datetime.month)
            # end_day = '{:02d}'.format(end_datetime.day)
            # end_hour = '{:02d}'.format(end_datetime.hour)
            # end_minute = '{:02d}'.format(end_datetime.minute+1)

            # parms = ("--http-auth-challenge=true --http-user=\'"
            #          +aria_username+"\' --http-passwd=\'"+aria_password
            #          +"\' --continue=true --auto-file-renaming=false"
            #          +" \"https://api.daac.asf.alaska.edu/services/search/param?platform=Sentinel-1&intersectsWith="
            #          +aoi_polygon+")&start="+start_year+"-"+start_month
            #          +"-"+start_day+"T"+start_hour+":"+start_minute+":00" + "&end="+end_year+"-"
            #          +end_month+"-"+end_day+ "T"+end_hour+":"+end_minute+":00&processingLevel="+S1_type+"&relativeOrbit="
            #          +orbit_number+"&output=metalink\"")
            # print(parms)
            # subprocess.call("aria2c "+parms,shell=True)
    else:
        raise("Please select one of the supported download variants.")

def get_flood_image(S1_df:pd.DataFrame,flood_datetime:datetime)-> pd.Series:
    """
    Finds the closest Sentinel-1 acquisition after the defined flood datetime.

    Args:
        S1_df (pd.DataFrame): the dataframe with Sentinel-1 acquisition metadata.
        flood_datetime (datetime object): the user-defined time point of the flood.

    Returns:
        pd.Series: the metadata of the considered flood image
    """

    # Get the datime information from all S1 products
    S1_df.reset_index(inplace=True)
    S1_temp=S1_df.copy()
    S1_temp.index=pd.to_datetime(S1_temp['beginposition'])
    
    # Find the S1 product that has the smallest time difference from the 
    # use-defined flood event datetime.
    S1_flood_datetime_diffs=(S1_temp.index-flood_datetime).tolist()
    S1_flood_diffs = [S1_flood_datetime_diff.total_seconds() for S1_flood_datetime_diff in S1_flood_datetime_diffs]
    
    if np.all(np.array(S1_flood_diffs)<0):
        print ("\n At your AOI, 0 (zero) Sentinel-1 images have been acquired")
        print ("from your specified [Flood_datetime] till [Flood_datetime] + [after_flood_days]\n")
        print ("Consider to change your [Flood_datetime] or [after_flood_days] configuration parameters\n")
        day_diff=np.max(np.array(S1_flood_diffs))
    else:
        day_diff = min([i for i in S1_flood_diffs if i >= 0])
   
    S1_flood_index = S1_flood_diffs.index(day_diff)
    flood_S1_image = S1_df['filename'].iloc[S1_flood_index]
    print('{} acquisition \n was acquired after {} hours from the user-defined datetime of flood event {}'.format(flood_S1_image,
                                                                                                                  round(day_diff/3600,2),
                                                                                                                  flood_datetime))

    return S1_df.iloc[S1_flood_index]

def query_S1_data(scihub_username,
                scihub_password,
                footprint,
                Start_time,
                End_time,
                flood_datetime,
                relOrbit,
                S1_dir):
        try:
            api = SentinelAPI(scihub_username,
                              scihub_password,
                              'https://apihub.copernicus.eu/apihub')

            if relOrbit=='All' or relOrbit=='Auto':
                products = api.query(footprint,
                                        date = (Start_time, End_time),
                                        platformname = 'Sentinel-1',
                                        producttype='GRD')
            else:
                products = api.query(scihub_username,
                                        date = (Start_time, End_time),
                                        platformname = 'Sentinel-1',
                                        relativeorbitnumber= int(relOrbit),
                                        producttype='GRD')   
        except :
            api = SentinelAPI(scihub_username,
                              scihub_password,
                              'https://scihub.copernicus.eu/dhus')

            if relOrbit=='All' or relOrbit=='Auto':
                products = api.query(footprint,
                                        date = (Start_time, End_time),
                                        platformname = 'Sentinel-1',
                                        producttype='GRD')
            else:
                products = api.query(footprint,
                                        date = (Start_time, End_time),
                                        platformname = 'Sentinel-1',
                                        relativeorbitnumber= int(relOrbit),
                                        producttype='GRD')                  
            
        # convert to dataframe for easier manipulation
        products_df = api.to_dataframe(products)
        
        # get information of S1 image that will be used a flood image
        flood_S1_image = get_flood_image(products_df,flood_datetime)
        flood_S1_image.to_csv(os.path.join(S1_dir,'flood_S1_filename.csv'))
        
        # select only the images that share the same relative orbit with
        # selected flood image
        products_df=products_df[products_df['orbitdirection']==flood_S1_image['orbitdirection'].upper()]
        relOrbit = flood_S1_image['relativeorbitnumber']
        products_df=products_df[products_df['relativeorbitnumber']==relOrbit]
        
        
        # Filter only images that matches the flood image orbit/slice_number
        #products_df=products_df[products_df['slicenumber']==flood_S1_image['slicenumber']]

        # discard the images with the same datetime and different ingestion date
        products_df=products_df.sort_values("ingestiondate")
        products_df=products_df.drop_duplicates("beginposition", keep='last')
            
        # save to csv for future use
        product_df_clean=products_df.copy()
        product_df_clean.to_csv(os.path.join(S1_dir,'S1_products.csv'))
        return product_df_clean
        
def Download_S1_data(scihub_username:str,
                    scihub_password:str,
                    aria_username:str,
                    aria_password:str,
                    S1_dir:str, # output directory
                    geojson_S1:str, # spatial AOI
                    S1_type:str,
                    Start_time:str,
                    End_time:str,
                    relOrbit:str,
                    flood_datetime:datetime,
                    time_sleep:int=180, # half an hour
                    max_tries:int=50,
                    download:bool=True)->None:
    """
    This function is the main functionaliry for downloading Sentinel-1 data.
    It supports the LTA retrieval of offline products. 
    It has been tested for products released after May 2017

    TODO:
        * Ensure that slicenumber of slcs products is the same. In some cases different slicenumber messes up the geocoding procedure.
        * Add ASF download functionality
    
    Args:
        scihub_username (string): username for downloading S1 data using sentinelsat 
        scihub_password (string): password for downloading S1 data using sentinelsat 
        aria_username (string): username for downloading S1 data using aria2c 
        aria_password (string): password for downloading S1 data using aria2c 
        S1_dir (string): directory that Sentinel-1 are stored.
        geojson_S1 (string): geojson vector file of the AOI.
        S1_type (string): type of S1 product can be GRD or SLC
        Start_time (string): Starting Date (YYYYMMDD) e.g.  20200924
        End_time (string): Starting Date (YYYYMMDD) e.g.  20201225
        relOrbit (string): number of relative orbit of Sentinel-1 data.
        flood_datetime (datetime object):the user-defined time point of the flood.
        time_sleep (integer, optional): time span for each request (in seconds). Defaults to 1800.
        max_tries (integer, optional): the number of the requests. Defaults to 50.

    """
    # Decide what download functionality we should use.
    # Sentinelsat for recent imagery and aria2c for older imagery
    if (datetime.now() - flood_datetime).days > 100:
        download_variant = 'aria2c'
    else:
        download_variant = 'sentinelsat'

    # Read AOI boundaries
    footprint = geojson_to_wkt(read_geojson(geojson_S1))

    download_try_count=0
    ongoing_download=True
    
    while download_try_count<max_tries and ongoing_download:
        # connect to the API
        # search by polygon, time, and Hub query keywords
        
        products_df = query_S1_data(scihub_username,
                                    scihub_password,
                                    footprint,
                                    Start_time,
                                    End_time,
                                    flood_datetime,
                                    relOrbit,
                                    S1_dir)
        
        error_message = ("Houston we've got a problem. Not enough images are"
                         " available between {} and {}. Please increase the" 
                         " value of before_flood_days".format(Start_time,
                                                              End_time))
            
        assert len(products_df) > 2, error_message

        if download:
            # checking if we have already downloaded data
            [products_df, ongoing_download] = check_downloaded_data(S1_dir,products_df)
            
            if ongoing_download: 
                download_products(scihub_username,
                                  scihub_password,
                                  aria_username,
                                  aria_password,
                                  products_df,
                                  download_variant,
                                  geojson_S1,
                                  S1_type,
                                  S1_dir)
            else:
                break
        else:
            break
                            
    download_try_count+=1
    print ("This is download try # {}.".format(download_try_count))
    print (" We will try to download the requested products in {:02.0f} minutes.".format(time_sleep/60))
    time.sleep(time_sleep)