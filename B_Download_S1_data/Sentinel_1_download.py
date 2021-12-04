#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloads Sentinel-1 imagery

Copyright (C) 2021 by K.Karamvasis

Email: karamvasis_k@hotmail.com
Last edit: 01.4.2021

This file is part of FLOMPY - FLOod Mapping PYthon toolbox.

    FLOMPY is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FLOMPY is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FLOMPY. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')


from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import os
import shutil
import glob
import time
import numpy as np
import pandas as pd

def check_downloaded_data(S1_GRD_dir,product_df):
    
    delete_flag=False
    download_flag=False
    
    # checking if all the products are already downloaded!
    already_downloaded_data=glob.glob(os.path.join(S1_GRD_dir,'S1*.zip'))
    already_downloaded_data_parent_dir=glob.glob(os.path.join(os.path.dirname(S1_GRD_dir),'S1*.zip'))
    
    products_to_be_download=sorted([product.split('.')[0] for product in product_df['filename'].tolist()])
    
    products_already_download=sorted([os.path.basename(product).split('.')[0] for product in already_downloaded_data])
    
    products_already_download_parent_dir=sorted([os.path.basename(product).split('.')[0] for product in already_downloaded_data_parent_dir])
    
    if len(products_already_download)>0 :        # Some downloaded products exist
        for product in products_already_download:
            if product not in products_to_be_download:
                delete_flag = True
                # print( "{} product dont meet the query parameters. Consider to manualy delete them.".format(product))
            else:
                product_df.drop(product_df[product_df['title']==product].index, inplace=True)
    
    if len(already_downloaded_data_parent_dir)>0:
        for index, product in enumerate(products_already_download_parent_dir):
            if product in products_to_be_download:
                # discared already downloaded product
                product_df.drop(product_df[product_df['title']==product].index, inplace=True)
                
                # moving downloaded file to the right directory
                old_filename=os.path.join(os.path.dirname(S1_GRD_dir),product+'.zip')
                new_filename=os.path.join(S1_GRD_dir,product+'.zip')
                shutil.move(old_filename, new_filename)
    
    if len(product_df)>0:
       download_flag = True 
        
    return product_df, delete_flag, download_flag

def download_products(product_to_be_downloaded_df, api, S1_GRD_dir):
    
    try:
        os.chdir(S1_GRD_dir)
        if 'index' in product_to_be_downloaded_df:
            product_to_be_downloaded_df.index=product_to_be_downloaded_df['index']
        for product_id in product_to_be_downloaded_df.index:
            product_info = api.get_product_odata(product_id)
            if product_info['Online']:
                print('Product {} seems to be online. Starting downloading.'.format(product_id))
                api.download(product_id)
            else:
                print('Product {} is not online.'.format(product_id))
                api.download(product_id)    
    except:
        print ("[I'm sorry] the number of requests to activate off-line products has been reached in this account.")
        print ("[I'm sorry] the number of requests to download this particular product has been reached its limit.")
        print ("We will try again with other provided account")

    return 0

def get_flood_image(S1_df,flood_datetime):
    S1_df.reset_index(inplace=True)
    
    S1_temp=S1_df.copy()
    S1_temp.index=pd.to_datetime(S1_temp['beginposition'])
    
    S1_flood_datetime_diffs=(S1_temp.index-flood_datetime).tolist()


    S1_flood_diffs = [S1_flood_datetime_diff.total_seconds() for S1_flood_datetime_diff in S1_flood_datetime_diffs]
    
    if np.all(np.array(S1_flood_diffs)<0):
        day_diff=np.max(np.array(S1_flood_diffs))
    else:
        day_diff = min([i for i in S1_flood_diffs if i >= 0])
   
    S1_flood_index = S1_flood_diffs.index(day_diff)
    flood_S1_image = S1_df['filename'].iloc[S1_flood_index]
    print('{} product was acquired after {} hours from the predefined flood event'.format(flood_S1_image,
                                                                                          round(day_diff/3600,2)))
    
    return S1_df.iloc[S1_flood_index]

def Download_data(scihub_accounts, # accounts at scihub.copernicus.eu
                S1_GRD_dir, # output directory
                geojson_S1, # spatial AOI
                Start_time,
                End_time,
                relOrbit,
                flood_datetime,
                time_sleep=1800, # half an hour
                max_tries=50):
    
    ''' This function download Sentinel-2 data. It uses multiple scihub accounts
    to speed up the LTA retrieval of offline products. It has been tested for 
    products released after May 2017'''
    
    # Create download directory
    if not os.path.exists(S1_GRD_dir): os.mkdir(S1_GRD_dir)

    download_try_count=0
    download_flag=True
    
    while download_try_count<max_tries and download_flag:
        for username in scihub_accounts:
            print (username)    
            # connect to the API
            #
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
            # get flood_date image
            flood_S1_image = get_flood_image(products_df,flood_datetime)

            # Filter only images that matches the flood image orbit/slice_number
            products_df=products_df[products_df['orbitdirection']==flood_S1_image['orbitdirection'].upper()]
            relOrbit = flood_S1_image['relativeorbitnumber']
            products_df=products_df[products_df['relativeorbitnumber']==relOrbit]
            products_df=products_df[products_df['slicenumber']==flood_S1_image['slicenumber']]

            # discard the images with the same datetime and different ingestion date
            products_df=products_df.sort_values("ingestiondate")
            products_df=products_df.drop_duplicates("beginposition", keep='last')
             
            # save to csv for future use
            product_df_clean=products_df.copy()
            product_df_clean.to_csv(os.path.join(S1_GRD_dir,'S1_products.csv'))
            
            product_df_suffle=product_df_clean.sample(frac=1)
            
            product_to_be_downloaded_df, delete_flag, download_flag = check_downloaded_data(S1_GRD_dir,product_df_suffle)
            
            if download_flag:
                download_products(product_to_be_downloaded_df, api, S1_GRD_dir)                                 
          
        download_try_count+=1
        print ("This is the {} download try.".format(download_try_count))
        print (" We will try to download the requested products in {} minutes.".format(time_sleep/60))
        time.sleep(time_sleep) # sleeping for one hour

    return S1_GRD_dir
