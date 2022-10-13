#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import geopandas as gpd
from shapely.geometry import Polygon
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def Coords_to_geojson(bbox, outdir, out_name='AOI.geojson'):
    '''
    Functionality to convert list of lats/lons to lat/lon Geojson file
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
    '''
    Functionality to convert provided vector file to lat/lon Geojson file
    '''

    given_polygon = gpd.read_file(vector_filename)
    polygon_wgs_84 = given_polygon.to_crs("EPSG:4326")
    
    if len(polygon_wgs_84) != 1:
        raise AssertionError('Please provide a single geometry')

    
    geojson_filename=os.path.join(outdir,out_name)
    polygon_wgs_84.to_file(filename=geojson_filename, driver='GeoJSON')
    return list(polygon_wgs_84.bounds.iloc[0]), geojson_filename