#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import os
import glob
import time
import numpy as np
import pandas as pd
from datetime import datetime

def check_downloaded_data(S1_GRD_dir:str,product_df_suffle:pd.DataFrame)-> tuple:
    """
    Based on already downloaded Sentinel-1 products in S1_GRD_dir we return 
    only the products that we still need to download.
    
    Improvements: Check the size and the integrity of each downloaded product.
    
    Args:
        S1_GRD_dir (string): The directory that the Sentinel-1 products will be downloaded.
        product_df_suffle (pandas.DataFrame): The results from sentinesat request.

    Returns:
        product_df_suffle (pandas.DataFrame): The Sentinel-1 products that will be downloaded.
        download_flag (boolean): True if we have products to download.
    """
    
    download_flag=False
    
    # checking if all the products are already downloaded!
    already_downloaded_data=glob.glob(os.path.join(S1_GRD_dir,'S1*.zip'))
    
    products_to_be_download=sorted([product.split('.')[0] for product in product_df_suffle['filename'].tolist()])
    products_already_download=sorted([os.path.basename(product).split('.')[0] for product in already_downloaded_data])

    for product in products_to_be_download:
        if product not in products_already_download:
            download_flag = True
        else:
            product_df_suffle.drop(product_df_suffle[product_df_suffle['title']==product].index, inplace=True)
            
    if len(product_df_suffle)>0:
       download_flag = True 
    
    return product_df_suffle, download_flag   


def download_products(product_to_be_downloaded_df: pd.DataFrame, api:SentinelAPI, S1_GRD_dir:str)-> None:
    """
    Download functionality of Sentinel-1 products
    
    Args:
        product_to_be_downloaded_df (pandas.DataFrame): DESCRIPTION.
        api (sentinelsat.sentinel.SentinelAPI ): The api sentinelsat request.
        S1_GRD_dir (string): The directory that the Sentinel-1 products will be
                             downloaded.
    """
    try:
        os.chdir(S1_GRD_dir)
        if 'index' in product_to_be_downloaded_df:
            product_to_be_downloaded_df.index=product_to_be_downloaded_df['index']
        for product_id in product_to_be_downloaded_df.index:
            product_info = api.get_product_odata(product_id)
            if product_info['Online']:
                print('Acquisition {} seems to be online. Starting downloading.'.format(product_info['title']))
                api.download(product_id)
            else:
                print('Acquisition {} is not online.'.format(product_info['title']))
                api.download(product_id)    
    except:
        print ("[I'm sorry] the number of requests to activate off-line products has been reached in this account.")
        print ("[I'm sorry] the number of requests to download this particular product has been reached its limit.")
        print ("We will try again ....")


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

def Download_S1_data(scihub_accounts:dict, # accounts at scihub.copernicus.eu
                S1_GRD_dir:str, # output directory
                geojson_S1:str, # spatial AOI
                Start_time:str,
                End_time:str,
                relOrbit:str,
                flood_datetime:datetime,
                time_sleep:int=1800, # half an hour
                max_tries:int=50,
                download:bool=True)->None:
    """
    This function is the main functionaliry for downloading Sentinel-1 GRD data.
    It support multiple scihub accounts to speed up the LTA retrieval of offline 
    products. It has been tested for products released after May 2017

    TODO:
        * Ensure that slicenumber of slcs products is the same. In some cases different slicenumber messes up the geocoding procedure.
        
    Args:
        scihub_accounts (dict): dict keys (scihub_username) and items (scihub_passwords).
        S1_GRD_dir (string): directory that Sentinel-1 are stored.
        geojson_S1 (string): geojson vector file of the AOI.
        Start_time (string): Starting Date (YYYYMMDD) e.g.  20200924
        End_time (string): Starting Date (YYYYMMDD) e.g.  20201225
        relOrbit (string): number of relative orbit of Sentinel-1 data.
        flood_datetime (datetime object):the user-defined time point of the flood.
        time_sleep (integer, optional): time span for each request (in seconds). Defaults to 1800.
        max_tries (integer, optional): the number of the requests. Defaults to 50.

    """

    download_try_count=0
    download_flag=True
    
    while download_try_count<max_tries and download_flag:
        for username in scihub_accounts:
            # connect to the API
            # search by polygon, time, and Hub query keywords
            footprint = geojson_to_wkt(read_geojson(geojson_S1))
            
            # return only the requested relative orbits
            try:
                api = SentinelAPI(username, scihub_accounts[username], 'https://scihub.copernicus.eu/apihub')
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
            except :
                api = SentinelAPI(username, scihub_accounts[username], 'https://scihub.copernicus.eu/dhus')
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
            flood_S1_image.to_csv(os.path.join(S1_GRD_dir,'flood_S1_filename.csv'))
            
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
            product_df_clean.to_csv(os.path.join(S1_GRD_dir,'S1_products.csv'))
            
            if download:
                product_df_suffle=product_df_clean.sample(frac=1)

                [product_to_be_downloaded_df,
                 download_flag] = check_downloaded_data(S1_GRD_dir,product_df_suffle)

                if download_flag:
                    download_products(product_to_be_downloaded_df, api, S1_GRD_dir)       
                else:
                    break
            else:
                break
                                
        download_try_count+=1
        print ("This is download try # {}.".format(download_try_count))
        print (" We will try to download the requested products in {:02.0f} minutes.".format(time_sleep/60))
        time.sleep(time_sleep)