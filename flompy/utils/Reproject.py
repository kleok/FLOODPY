#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import gdal

def reproject_image_to_master ( master, slave, dst_filename, res=None ):
    '''
    Reprojection funcionality
    '''
    slave_ds = gdal.Open( slave )

    slave_proj = slave_ds.GetProjection()
    slave_geotrans = slave_ds.GetGeoTransform()
    data_type = slave_ds.GetRasterBand(1).DataType
    n_bands = slave_ds.RasterCount

    master_ds = gdal.Open( master )

    master_proj = master_ds.GetProjection()
    master_geotrans = master_ds.GetGeoTransform()
    w = master_ds.RasterXSize
    h = master_ds.RasterYSize
    
    if res is not None:
        master_geotrans[1] = float( res )
        master_geotrans[-1] = - float ( res )

    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_filename,
                                                w, h, n_bands, data_type)
    dst_ds.SetGeoTransform( master_geotrans )
    dst_ds.SetProjection( master_proj)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)

    gdal.ReprojectImage( slave_ds, dst_ds, slave_proj,
                         master_proj, gdal.GRA_Bilinear)
    
    dst_ds = None  # Flush to disk
    return dst_filename

