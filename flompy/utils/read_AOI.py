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
    along with FLOMPY. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################

import geopandas as gpd
from shapely.geometry import Polygon
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def Coords_to_geojson(bbox, outdir, out_name='AOI.geojson'):
    '''
    Writes a geojson file from the Input EOM json file.
        
    *args: 
        temp_data_df (pandas dataframe). one row dataframe
        outdir (str) the path that the geojson file will be saved.
    
    returns:
        polygon (geojson object) Default name: 'input_EOM.geojson'
    '''

    LONMIN, LATMIN,  LONMAX, LATMAX = bbox   
    lon_list=[LONMIN, LONMIN, LONMAX, LONMAX, LONMIN]
    lat_list=[LATMIN, LATMAX, LATMAX, LATMIN, LATMIN]
    
    polygon_geom = Polygon(zip(lon_list, lat_list))
    
    # for Google Maps
    # crs = {'init': 'epsg:3857'}
    
    #polygon_google_earth = gpd.GeoDataFrame(index=[0], crs={'init': 'epsg:4326'}, geometry=[polygon_geom])
    polygon_google_earth = gpd.GeoDataFrame(crs="EPSG:4326", geometry=[polygon_geom])
    polygon_wgs_84 = polygon_google_earth.to_crs("EPSG:4326")
    
    geojson_filename=os.path.join(outdir,out_name)
    polygon_wgs_84.to_file(filename=geojson_filename, driver='GeoJSON')
    
    return geojson_filename
    
def Input_vector_to_geojson(vector_filename, outdir, out_name='AOI.geojson'):
    
    given_polygon = gpd.read_file(vector_filename)
    polygon_wgs_84 = given_polygon.to_crs("EPSG:4326")
    
    if len(polygon_wgs_84) != 1:
        raise AssertionError('Please provide a single geometry')

    
    geojson_filename=os.path.join(outdir,out_name)
    polygon_wgs_84.to_file(filename=geojson_filename, driver='GeoJSON')
    return list(polygon_wgs_84.bounds.iloc[0]), geojson_filename