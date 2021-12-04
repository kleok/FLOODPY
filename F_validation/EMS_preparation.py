#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rasterize the EMS vector data based on floodpy results

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

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

from osgeo import gdal
from osgeo import ogr

def rasterize(vector_layer, raster_layer, target_layer, field_name):
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






