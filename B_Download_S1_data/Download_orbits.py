#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloads S1 orbit data

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

import os
import datetime
import pandas as pd
import requests

def _get_orbit_filenames(start_datetime, end_datetime, temp_export_dir, orbit_type='AUX_POEORB'):

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
    os.system('wget --no-check-certificate --output-document=query_results.json "{url_request}"'.format(url_request=url_request))
    
    
    return os.path.join(temp_export_dir,"query_results.json")


def download_single_orbit(single_orbit_dictionary, snap_orbit_dir, S1_datetime, username, password, orbit_type ):
    
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
    '''
    Download the selected orbit file
    '''    
    
    if isinstance(orbit_dictionary, dict):
        Orbit_filename=orbit_dictionary['str'][6]['content']
        if Orbit_filename.startswith(S1_filename[0:3]):
            download_single_orbit(orbit_dictionary, snap_orbit_dir, S1_datetime, username, password, orbit_type )
    else:
        for orbit_dict in orbit_dictionary:
            Orbit_filename=orbit_dict['title']
            if Orbit_filename.startswith(S1_filename[0:3]):
                download_single_orbit(orbit_dict, snap_orbit_dir,S1_datetime , username, password, orbit_type)
            
    
 
def download_orbits(snap_dir, temp_export_dir, S1_products):
    S1_filenames=pd.read_csv(S1_products)

    username = "gnssguest"
    password = "gnssguest"
    
    for index, S1_row in S1_filenames.iterrows():
        
        S1_filename=S1_row['filename']
        S1_datetime = pd.to_datetime(S1_row['beginposition'])
        end_datetime=S1_datetime+datetime.timedelta(hours=4)
        start_datetime=S1_datetime-datetime.timedelta(hours=6)
    
        orbits_json=_get_orbit_filenames(start_datetime, end_datetime, temp_export_dir, orbit_type='AUX_RESORB')
        
        orbits_df=pd.read_json(orbits_json)
        if orbits_df['feed']['opensearch:totalResults']=='0': # downloads precise orbit files
            end_datetime=S1_datetime+datetime.timedelta(hours=48)
            start_datetime=S1_datetime-datetime.timedelta(hours=48)
            orbits_json=_get_orbit_filenames(start_datetime, end_datetime, temp_export_dir, orbit_type='AUX_POEORB')
            orbits_df=pd.read_json(orbits_json)
            orbit_dictionary=orbits_df['feed']['entry']
            snap_POEORB_dir = os.path.join(snap_dir, 'POEORB')
            downloads_orbit_filename(orbit_dictionary, snap_POEORB_dir, S1_filename, S1_datetime, username, password, orbit_type='AUX_POEORB')
        else:
            orbit_dictionary=orbits_df['feed']['entry'] # downloads restributed orbit files
            # Define the local filename to save data
            snap_RESORB_dir = os.path.join(snap_dir, 'RESORB')
            downloads_orbit_filename(orbit_dictionary, snap_RESORB_dir,S1_filename, S1_datetime, username, password, orbit_type='AUX_RESORB')
