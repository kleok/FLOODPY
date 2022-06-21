#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script generates auxiliary data that can be used for postprocessing 
for flood water mapping

Copyright (C) 2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Karamvasis Kleanthis
Last edit: 13.4.2022

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

import h5py
from osgeo import gdal
import numpy as np
import os, glob
from utils.Reproject import reproject_image_to_master
import richdem as rd
import pyproj

def nparray_to_tiff(nparray, reference_gdal_dataset, target_gdal_dataset):
    '''
    Functionality that saves information numpy array to geotiff given a reference
    geotiff.

    Args:
        nparray (np.array): information we want to save to geotiff.
        reference_gdal_dataset (string): path of the reference geotiff file.
        target_gdal_dataset (string): path of the output geotiff file.

    Returns:
        None.
    '''
    # open the reference gdal layer and get its relevant properties
    raster_ds = gdal.Open(reference_gdal_dataset, gdal.GA_ReadOnly)   
    xSize = raster_ds.RasterXSize
    ySize = raster_ds.RasterYSize
    geotransform = raster_ds.GetGeoTransform()
    projection = raster_ds.GetProjection()
    
    # create the target layer 1 (band)
    driver = gdal.GetDriverByName('GTIFF')
    target_ds = driver.Create(target_gdal_dataset, xSize, ySize, bands = 1, eType = gdal.GDT_Float32)
    target_ds.SetGeoTransform(geotransform)
    target_ds.SetProjection(projection)
    target_ds.GetRasterBand(1).WriteArray(nparray)  
    
    target_ds = None


def reproject(outname, infilename, UTM_CRS_EPSG ):
    '''
    Reproject funcionality
    '''
    
    ds = gdal.Warp(outname, infilename, dstSRS='EPSG:{}'.format(UTM_CRS_EPSG),
                   srcNodata = -32768, dstNodata = -32768)
               #outputType=gdal.GDT_Int16, xRes=0.00892857142857143, yRes=0.00892857142857143)
    ds = None
    return 0
    
def generate_slope_aspect(dem_file, slope_outname, aspect_outname):
    '''
    Calculates aspect and slope of given DEM 
    Args:
        dem_file (string): path to DEM geotiff file .
        slope_outname (string): path to DEM-slope generated geotiff file.
        aspect_outname (string): path to DEM-aspect generated geotiff file.

    Returns:
        None.

    '''
    dem_temp = rd.LoadGDAL(dem_file, no_data=-32768)
    slope = rd.TerrainAttribute(dem_temp, attrib='slope_degrees')
    rd.SaveGDAL(slope_outname, slope)
    aspect = rd.TerrainAttribute(dem_temp, attrib='aspect')
    rd.SaveGDAL(aspect_outname, aspect)

def WGS84_to_UTM(lon_list, lat_list):
    '''
    Finds the best WGS84 UTM projection given a list of lats/lons
    Args:
        lon_list (list): list of longitudes.
        lat_list (list): list of latitudes.

    Returns:
        utm_crs_epsg (string): the UTM code projection.

    '''
    representative_longitude = round(np.mean(lon_list), 10)
    utm_zone = int(np.floor((representative_longitude + 180) / 6) + 1)
    representative_latitude = round(np.mean(lat_list), 10)
    if representative_latitude>0:
        hemisphere='north'
    else:
        hemisphere='south'
    utm_crs_str = '+proj=utm +zone={} +{} +ellps=WGS84 +datum=WGS84 +units=m +no_defs'.format(utm_zone,hemisphere)

    utm_crs_epsg = pyproj.CRS(utm_crs_str).to_epsg()
    
    return utm_crs_epsg
    

def get_S1_aux (Preprocessed_dir):
    '''
    Funcionality that calculates and reprojects to UTM the auxiliary data 
    (DEM-slope & aspect) that are required for latest steps.
    '''
    SAR_stack_file=os.path.join(Preprocessed_dir,'Stack/SAR_Stack.h5')
    SAR_stack=h5py.File(SAR_stack_file,'r')
    
    tiff_files=glob.glob(os.path.join(Preprocessed_dir,'*.tif'))
    
    master_tiff_wgs84=None
    for tiff_file in tiff_files:
        if os.path.exists(tiff_file.split('.')[0]+'.h5'):
            master_tiff_wgs84 = tiff_file
    
    # asserts that we found the master tiff file!
    assert (master_tiff_wgs84)
         
    # Calculate UTM projection 
    lon_nparray=SAR_stack['longitude'][:].flatten()
    lon_list = list(lon_nparray[np.nonzero(lon_nparray)])
    lat_nparray=SAR_stack['latitude'][:].flatten()
    lat_list = list(lat_nparray[np.nonzero(lat_nparray)])
    
    UTM_CRS_EPSG = WGS84_to_UTM(lon_list, lat_list)
    del lon_nparray, lon_list, lat_nparray, lat_list
    #############################
    # B. Calculate slopes from DEM and threshold (<12 degrees) to get low slopes [slope_mask]
    #############################
    
    # reproject master_tiff (sigma_VV, sigma_VH, elevation, lat, lon, localIncidenceAngle) from wgs84 to utm
    master_tiff_utm=master_tiff_wgs84[:-4]+'_utm.tif'
    reproject(master_tiff_utm, master_tiff_wgs84,UTM_CRS_EPSG )
    
    # write dem_utm
    dem_nparray=gdal.Open(master_tiff_utm).ReadAsArray()[1,:,:] # order of writing
    dem_nparray[dem_nparray==-32768]=np.nan # nan values
    dem_utm_dataset=os.path.join(os.path.dirname(master_tiff_utm), 'dem_utm.tif')
    nparray_to_tiff(dem_nparray, master_tiff_utm, dem_utm_dataset)
    del dem_nparray
    
    # calculate aspect and slope at UTM projection
    slope_outname=os.path.join(os.path.dirname(master_tiff_utm),'dem_slope_utm.tif')
    aspect_outname=os.path.join(os.path.dirname(master_tiff_utm),'dem_aspect_utm.tif')
    generate_slope_aspect(dem_utm_dataset, slope_outname, aspect_outname)
    
    # reproject dem,slope,aspect UTM to WGS84
    reproject_image_to_master(master_tiff_wgs84, dem_utm_dataset, dem_utm_dataset[:-7]+'wgs84.tif')
    reproject_image_to_master(master_tiff_wgs84, slope_outname, slope_outname[:-7]+'wgs84.tif')
    reproject_image_to_master(master_tiff_wgs84, aspect_outname, aspect_outname[:-7]+'wgs84.tif')
    
    
    
    
    
    
    
    
    
    
    
    
    
