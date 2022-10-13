#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import gdal
from osgeo import ogr

def rasterize(vector_layer, raster_layer, target_layer, field_name):
    '''
    Rasterize functionality

    '''
    # open the raster layer and get its relevant properties
    raster_ds = gdal.Open(raster_layer, gdal.GA_ReadOnly)
    xSize = raster_ds.RasterXSize
    ySize = raster_ds.RasterYSize
    geotransform = raster_ds.GetGeoTransform()
    projection = raster_ds.GetProjection()
    
    # create the target layer (1 band)
    driver = gdal.GetDriverByName('GTiff')
    target_ds = driver.Create(target_layer, xSize, ySize, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform(geotransform)
    target_ds.SetProjection(projection)
    source_ds = ogr.Open(vector_layer)
    source_layer = source_ds.GetLayer()
    
    ds = gdal.RasterizeLayer(target_ds, [1], source_layer, options = ["ATTRIBUTE={}".format(field_name)])
    
    target_ds = 0
    return target_layer






