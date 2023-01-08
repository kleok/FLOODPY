#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import gdal
import numpy as np

def nparray_to_tiff(nparray:np.array, reference_gdal_dataset:str, target_gdal_dataset:str)->None:
    """
    Functionality that saves information numpy array to geotiff given a reference geotiff.

    Args:
        nparray (np.array): Information we want to save to geotiff
        reference_gdal_dataset (str): Path of the reference geotiff file
        target_gdal_dataset (str): Path of the output geotiff file
    """
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