#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Main application for flood map production and validation with EMS products

Copyright (C) 2021 by K.Karamvasis

Email: karamvasis_k@hotmail.com
Last edit: 01.9.2020

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

import os, glob
import datetime
import pandas as pd
from B_Download_S1_data.Sentinel_1_download import Download_data
from B_Download_S1_data.Download_orbits import download_orbits
from B_Download_ERA5.Download_ERA5 import Get_ERA5_data_time_period
from C_Classify_dry_wet_images.Classify_S1_images import Get_images_for_baseline_stack
from C_Preprocessing.Preprocessing_S1_data import Run_Preprocessing, get_flood_image
from D_create_auxiliary_data.Generate_aux import get_S1_aux
from E_classification.calc_t_scores import Calc_t_scores
from E_classification.Classification import Get_flood_map
from F_validation.Validation import Accuracy_metrics_calc
from F_validation.EMS_preparation import rasterize
from utils.create_geojson import Create_geojson

###############################################################################
## Set parameters
###############################################################################

src_dir='directory of the flompy'
projectfolder='project directory'

snap_dir = 'path to Sentinel-1 orbit directory for snap processing'
#example: '/home/kleanthis/.snap/auxdata/Orbits/Sentinel-1'

gpt_exe = 'path to gpt exe'
#example:'/home/kleanthis/bin/snap8/snap/bin/gpt'
    
# example datetime
flood_datetime=datetime.datetime(2021,7,16,5,00,00) 

# example boundary coordinates
ulx=7.14
uly=50.35
lrx=7.48
lry=50.13

# Auto option selects the orbit to minimize the distance between defined
# flood date and SAR datetime acquisition
# use can also selects specific Relative orbit number
relOrbit='Auto' 

# cumulative rain in mm for the last 5 days 
rain_thres=45 

# minimum mapping unit area in square meters
minimum_mapping_unit_area_m2=4000 

EMS_vector_folder='path to EMS directory that contains vector files' 
# example: '/RSL03/Flood_detection/EMSR517/EMS/EMSR517_AOI01_DEL_MONIT01_r1_RTP04_v1_vector'

scihub_accounts={'USERNAME_1':'PASSWORD_1',
                 'USERNAME_2':'PASSWORD_2'}

###############################################################################
## Prepare directories
###############################################################################

bbox=[uly,ulx,lry,lrx,]  #N/W/S/E  

# Getting Start (3 months before) and End date (3 days after) of time period
Start_datetime=flood_datetime-datetime.timedelta(days=90)
End_datetime=flood_datetime+datetime.timedelta(days=3)
Start_time=Start_datetime.strftime("%Y%m%d")
End_time=End_datetime.strftime("%Y%m%d")

# processing directories
if not os.path.exists(projectfolder): os.mkdir(projectfolder)
S1_GRD_dir = os.path.join(projectfolder,'Sentinel_1_GRD_imagery')
ERA5_dir = os.path.join(projectfolder,'ERA5')
graph_dir = os.path.join(src_dir,'C_Preprocessing/Graphs')
Preprocessing_dir = os.path.join(projectfolder, 'Preprocessed')
if not os.path.exists(Preprocessing_dir): os.makedirs(Preprocessing_dir)
Results_dir = os.path.join(projectfolder, 'Results')
if not os.path.exists(Results_dir): os.makedirs(Results_dir)
temp_export_dir = os.path.join(S1_GRD_dir,"S1_orbits")
if not os.path.exists(temp_export_dir): os.makedirs(temp_export_dir)

###############################################################################
## Create geojson file for SAR analysis
###############################################################################

geojson_S1=Create_geojson(bbox,
                          projectfolder,
                          out_name='AOI.geojson')

###############################################################################
## Donwload S1 data
###############################################################################

S1_GRD_dir = Download_data(scihub_accounts = scihub_accounts,
                          S1_GRD_dir = S1_GRD_dir,
                          geojson_S1 = geojson_S1,
                          Start_time = Start_time,
                          End_time = End_time,
                          relOrbit = relOrbit,
                          flood_datetime = flood_datetime,
                          time_sleep=360, # 10 minutes
                          max_tries=50)

###############################################################################
## Donwload precipitation data
###############################################################################
# ERA5_variables = ['10m_u_component_of_wind',
#                   '10m_v_component_of_wind',
#                   '2m_temperature',
#                   'precipitation_type',
#                   'runoff',
#                   'snowfall',
#                   'soil_temperature_level_1',
#                   'total_precipitation',
#                   'volumetric_soil_water_layer_1',]
###############################################################################
ERA5_variables = ['total_precipitation',]
ERA5_filename = Get_ERA5_data_time_period(ERA5_variables, Start_time, End_time, bbox, ERA5_dir)

###############################################################################
## Find good images for baseline
###############################################################################
# Improvements
# 1. In the case that the rain_thres discards many images we have to consider
# downloading more data.
#
###############################################################################
baseline_images=os.path.join(projectfolder,'baseline_images.pickle')

Good_images_for_baseline = Get_images_for_baseline_stack(netcdf_file = ERA5_filename,
                                                          S1_GRD_dir = S1_GRD_dir,
                                                          export_filename = baseline_images,
                                                          Start_time = Start_time,
                                                          End_time = End_time,
                                                          flood_datetime = flood_datetime,
                                                          days_back=5,
                                                          rain_thres=rain_thres)

###############################################################################
## Find THE image that can be related with the flood event
###############################################################################

S1_products=glob.glob(S1_GRD_dir+'/S1_products.csv')[0]
flood_S1_image=get_flood_image(S1_products,flood_datetime)

###############################################################################
## Perform Preprocessing
###############################################################################

download_orbits(snap_dir,
                temp_export_dir = temp_export_dir,
                S1_products = S1_products)

Run_Preprocessing(gpt_exe = gpt_exe,
                  graph_dir = graph_dir,
                  S1_GRD_orbit_dir = S1_GRD_dir,
                  geojson_S1 = geojson_S1,
                  flood_S1_image = flood_S1_image,
                  baseline_images = baseline_images,
                  S1_products = S1_products,
                  Preprocessing_dir = Preprocessing_dir)    

###############################################################################
## Generate Auxiliary datasets
###############################################################################

get_S1_aux (Preprocessing_dir)

###############################################################################
## Create t-score map
## t-score is a metric that represents change/no-change
###############################################################################

floodpy_t_scores = Calc_t_scores(projectfolder = projectfolder,
                                  Results_dir = Results_dir,
                                  S1_GRD_orbit_dir = S1_GRD_dir,
                                  Preprocessing_dir = Preprocessing_dir,
                                  flood_datetime = flood_datetime,
                                  band='VV_VH_db')

###############################################################################
## Classification
###############################################################################

Floodpy_results= Get_flood_map(t_score_filename = os.path.join(Results_dir,'t_scores_VV_VH_db.tif'),
                              slope_filename = os.path.join(Preprocessing_dir,'dem_slope_wgs84.tif'),
                              Results_dir= Results_dir,
                              output_filename = os.path.join(Results_dir,'Flood_map.tif'),
                              minimum_mapping_unit_area_m2=minimum_mapping_unit_area_m2)


###############################################################################
## Download EMS product and rasterize to the same extent as t_score raster product
###############################################################################

# Downloading has to be performed manually
# rasterize EMS shapefile

EMS_results = glob.glob(EMS_vector_folder+'/*observedEvent*.shp')
if len(EMS_results)==0:
   EMS_results = glob.glob(EMS_vector_folder+'/*observed_event*.shp') 
   if len(EMS_results)==0:
       print ("EMS observed Event shapefile cannot be found!")

EMS_vector=EMS_results[0]
   
EMS_aoi = glob.glob(EMS_vector_folder+'/*areaOfInterest*.shp')
if len(EMS_aoi)==0:
   EMS_aoi = glob.glob(EMS_vector_folder+'/*area_of_interest*.shp') 
   if len(EMS_aoi)==0:
       print ("EMS area of interest shapefile cannot be found!") 
       
EMS_aoi_vector=EMS_aoi[0]
   
EMS_raster_results = os.path.join(Results_dir,'EMS_rasterized.tif')
EMS_aoi_raster = os.path.join(Results_dir,'EMS_AOI.tif') 

rasterize(vector_layer = EMS_vector,
          raster_layer = Floodpy_results,
          target_layer = EMS_raster_results,
          field_name = 'dmg_src_id')

rasterize(vector_layer = EMS_aoi_vector,
          raster_layer = Floodpy_results,
          target_layer = EMS_aoi_raster,
          field_name = 'area_id')

###############################################################################
## Validation
###############################################################################

Accuracy_metrics=Accuracy_metrics_calc(EMS_raster_results,Floodpy_results, EMS_aoi_raster)
Accuracy_df = pd.DataFrame(Accuracy_metrics.items())
Accuracy_df.to_csv("{}/Accuracy_report.txt".format(Results_dir),header=False,index=False)



