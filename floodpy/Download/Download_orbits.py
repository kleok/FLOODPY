#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess
import datetime
import pandas as pd
import requests
from tqdm import tqdm
import platform

def _get_orbit_filenames(start_datetime:datetime.datetime, end_datetime:datetime.datetime, temp_export_dir:str, wget_path:str = "", orbit_type:str = 'AUX_POEORB')->str:
    """Gets orbit filenames,

    Args:
        start_datetime (datetime.datetime): Starting date
        end_datetime (datetime.datetime): Ending date
        temp_export_dir (str): Temporary directory
        wget_path (str, optional): Windows users must provide the full path to wget executable. Defaults to "".
        orbit_type (str, optional): Type of orbit. Defaults to 'AUX_POEORB'

    Returns:
        str: Path to orbit file
    """

    username = "gnssguest"
    password = "gnssguest"

    time1 = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
    time2 = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
    

    url_request="https://{username}:{password}@scihub.copernicus.eu/gnss/search?format=json&start=0&rows=100&q=producttype:%22{orbit_type}%22%20AND%20beginposition:[{time1} TO {time2}] AND endposition:[{time1} TO {time2}]".format(username = username,
                                password = password,
                                orbit_type = orbit_type,
                                time1 = time1,
                                time2 = time2)
    
    os.chdir(temp_export_dir)
    string_command = f'{os.path.join(wget_path, "wget")} --no-check-certificate --output-document=query_results.json "{url_request}"'
    
    # if platform.system().startswith('Win'):
    #     string_command = f'{os.path.join(wget_path, "wget")} --no-check-certificate --output-document=query_results.json "{url_request}"'
    # else:
    #     raise ValueError("System is not supported! Only windows and Linux systems are supported")

    subprocess.Popen(string_command, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.DEVNULL).wait()

    return os.path.join(temp_export_dir,"query_results.json")


def download_single_orbit(single_orbit_dictionary, snap_orbit_dir, S1_datetime, username, password, orbit_type):
    """Downloads and saves single orbit filename."""

    if orbit_type=='AUX_POEORB':
        export_name=single_orbit_dictionary['title'].split('.')[0]+'.EOF'
    else:
        export_name=single_orbit_dictionary['str'][6]['content']
    
    snap_directory=os.path.join(snap_orbit_dir, export_name[0:3], str(S1_datetime.year), '{:02}'.format(S1_datetime.month))
    if not os.path.exists(snap_directory): os.makedirs(snap_directory)
    
    local_file = os.path.join(snap_directory,export_name)
    try:
        os.chdir(snap_orbit_dir)
        download_link=single_orbit_dictionary['link'][0]['href']
        download_link_user_pass='https://{username}:{password}@scihub.copernicus.eu'.format(username = username, password = password)+download_link.split('https://scihub.copernicus.eu')[1]

        # Make http request for remote file data
        data = requests.get(download_link_user_pass)
        # Save file data to local copy
        with open(local_file, 'wb') as file:
            file.write(data.content)

    
    except:
        os.chdir(snap_orbit_dir)
        altern_download_link=single_orbit_dictionary['link'][1]['href']
        altern_download_link_user_pass='https://{username}:{password}@scihub.copernicus.eu'.format(username = username, password = password)+altern_download_link.split('https://scihub.copernicus.eu')[1]
        
        # Make http request for remote file data
        data = requests.get(altern_download_link_user_pass)
        # Save file data to local copy
        with open(local_file, 'wb')as file:
            file.write(data.content)     
    

def downloads_orbit_filename(orbit_dictionary, snap_orbit_dir,S1_filename, S1_datetime, username, password, orbit_type):    
    """Downloads single orbit filename."""
    
    if isinstance(orbit_dictionary, dict):
        Orbit_filename=orbit_dictionary['str'][6]['content']
        if Orbit_filename.startswith(S1_filename[0:3]):
            download_single_orbit(orbit_dictionary, snap_orbit_dir, S1_datetime, username, password, orbit_type )
    else:
        for orbit_dict in orbit_dictionary:
            Orbit_filename=orbit_dict['title']
            if Orbit_filename.startswith(S1_filename[0:3]):
                download_single_orbit(orbit_dict, snap_orbit_dir,S1_datetime , username, password, orbit_type)
            
    
 
def download_orbits(snap_dir:str, temp_export_dir:str, S1_dir:str, wget_path:str = "")->None:
    """
    Download Sentinel-1 orbits

    Args:
        snap_dir (str): Directory that snap stores Sentinel-1 orbits files.
        temp_export_dir (str): Temporary directory.
        S1_dir (str): Directory the Sentinel-1 images are stored.
        wget_path (str, optional): Windows users must provide the full path to wget executable. Defaults to "".
    """
    
    S1_products = os.path.join(S1_dir,'S1_products.csv')
    assert os.path.exists(S1_products)
    S1_filenames=pd.read_csv(S1_products)

    username = "gnssguest"
    password = "gnssguest"
    
    for index, S1_row in tqdm(S1_filenames.iterrows(), total=S1_filenames.shape[0]):
        S1_filename=S1_row['filename']
        S1_datetime = pd.to_datetime(S1_row['beginposition'])
        end_datetime=S1_datetime+datetime.timedelta(hours=4)
        start_datetime=S1_datetime-datetime.timedelta(hours=6)
    
        orbits_json=_get_orbit_filenames(start_datetime, end_datetime, temp_export_dir, wget_path = wget_path,  orbit_type='AUX_RESORB')
        
        orbits_df=pd.read_json(orbits_json)
        if orbits_df['feed']['opensearch:totalResults']=='0': # downloads precise orbit files
            end_datetime=S1_datetime+datetime.timedelta(hours=48)
            start_datetime=S1_datetime-datetime.timedelta(hours=48)
            orbits_json=_get_orbit_filenames(start_datetime, end_datetime, temp_export_dir, wget_path = wget_path, orbit_type='AUX_POEORB')
            orbits_df=pd.read_json(orbits_json)
            orbit_dictionary=orbits_df['feed']['entry']
            snap_POEORB_dir = os.path.join(snap_dir, 'POEORB')
            downloads_orbit_filename(orbit_dictionary, snap_POEORB_dir, S1_filename, S1_datetime, username, password, orbit_type='AUX_POEORB')
        else:
            orbit_dictionary=orbits_df['feed']['entry'] # downloads restributed orbit files
            # Define the local filename to save data
            snap_RESORB_dir = os.path.join(snap_dir, 'RESORB')
            downloads_orbit_filename(orbit_dictionary, snap_RESORB_dir,S1_filename, S1_datetime, username, password, orbit_type='AUX_RESORB')
