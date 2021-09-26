#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creates a geojson file from N/W/S/E bbox 

Copyright (C) 2021 by K.Karamvasis

Email: karamvasis_k@hotmail.com
Last edit: 01.9.2021

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
    along with GECORIS. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

import geopandas as gpd
from shapely.geometry import Polygon
import os

def Create_geojson(bbox, outdir, out_name='AOI.geojson'):
    '''
    Writes a geojson file from the Input EOM json file.
        
    *args: 
        temp_data_df (pandas dataframe). one row dataframe
        outdir (str) the path that the geojson file will be saved.
    
    returns:
        polygon (geojson object) Default name: 'input_EOM.geojson'
    '''
    
    lon_list=[bbox[1], bbox[1], bbox[3], bbox[3], bbox[1]]
    lat_list=[bbox[0], bbox[2],  bbox[2], bbox[0], bbox[0]]
    
    polygon_geom = Polygon(zip(lon_list, lat_list))
    
    # for Google Maps
    # crs = {'init': 'epsg:3857'}
    
    #polygon_google_earth = gpd.GeoDataFrame(index=[0], crs={'init': 'epsg:4326'}, geometry=[polygon_geom])
    polygon_google_earth = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon_geom])
    polygon_wgs_84 = polygon_google_earth.to_crs("EPSG:4326")
    
    geojson_filename=os.path.join(outdir,out_name)
    polygon_wgs_84.to_file(filename=geojson_filename, driver='GeoJSON')
    
    return geojson_filename
    
