#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2021-2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Alekos Falagas, Karamvasis Kleanthis

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
import os
import logging
import rasterio
from shapely.geometry import box
import geopandas as gpd
from fiona.crs import from_epsg
from rasterio.windows import Window
from rasterio.enums import Resampling
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
import numpy as np
from flompy.Preprocessing_S2_data.exceptions import BandNotFound, PathError

class Clipper():

    @staticmethod
    def boundingBox(minx, maxx, miny, maxy, srid):
        """Generates polygon geometry, from given coordinates.
        Given coordinates must be in the same CRS, as image's CRS.

        Args:
            minx (float): West (left) x coordinate
            maxx (float): East (right) x coordinate
            miny (float): South (bottom) y coordinate
            maxy (float): North (top) y coordinate
            srid (int): SRID of the geometry (Should be changed from int)

        Returns:
            geoDataFrame: Bounding box of the coordinates given by the user
        """
        
        # Create bounding box
        bbox = box(minx, miny, maxx, maxy)
        # Create geometry in geoDataFrame forma
        geometry = gpd.GeoDataFrame({'geometry': bbox}, index = [0], crs = from_epsg(srid))
        
        return geometry

    @staticmethod
    def clip(image, geometry, band = None, new = 'clipped', resize = False, resize_val = 2, method = None, ext = 'tif'):
        """Clip image & update metadata of output image. Option to write
        output image to disk.

        Args:
            image (senimage): senimage object
            geometry (geoDataframe): Geometry dataframe used as bounding box to clip image
            band (str, optional): Band to be applied. Note that the band name must be the same with the object attribute name. Defaults to None
            new (str, optional): Piece of string added to the end of the new filename. Defaults to 'clipped'
            resize (bool, optional): If True resizes the output resize_val times. Defaults to False
            resize_val (int, optional): Resize value. Defaults to 2
            method (rasterio.enum.Resampling, optional): Resampling method. Defaults to None
            ext (str, optional): Extention of the image. Defaults to 'tif'

        Raises:
            PathError: Raises when cannot find a path to store the new image
            BandNotFound: Raises when the image has no attribute band selected by the user
        """

        if band != None:

            if hasattr(image, band):

                if hasattr(image, 'datapath'):
                    path = image.datapath
                else:
                    resolution = image.setResolution(band)
                    if int(resolution) == 20 and resize == True:
                        if hasattr(image, 'datapath_10'):
                            path = image.datapath_10
                        else:
                            raise PathError("Could not find a path to store the image.")
                    elif int(resolution) == 20 and resize == False:
                        if hasattr(image, 'datapath_20'):
                            path = image.datapath_20
                        else:
                            raise PathError("Could not find a path to store the image.")
                    else:
                        if hasattr(image, 'datapath_10'):
                            path = image.datapath_10
                        else:
                            raise PathError("Could not find a path to store the image.")

                # New name for output image
                out_tif = os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))

                if os.path.exists(out_tif) == True and os.stat(out_tif).st_size != 0:
                    # Pass if file already exists & it's size is not zero
                    logging.info("File {} already exists...".format(os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))))

                    return

                with rasterio.open(getattr(image, band)) as src:
                    # Image metadata
                    metadata = src.meta

                    # Convert x,y to row, col
                    row_start, col_start = src.index(geometry.bounds['minx'][0], geometry.bounds['maxy'][0])
                    row_stop, col_stop = src.index(geometry.bounds['maxx'][0], geometry.bounds['miny'][0])

                    # Parse pixel size from metadata.
                    pixelSize = list(metadata['transform'])[0]

                    # Create the new transformation.
                    transform = rasterio.transform.from_origin(
                        geometry.bounds['minx'][0], geometry.bounds['maxy'][0], pixelSize, pixelSize)

                    # Update metadata.
                    metadata.update(
                        driver = 'GTiff', transform = transform,
                        height = (row_stop - row_start), width = (col_stop - col_start))

                    # Construct a window by image coordinates.
                    win = Window.from_slices(slice(row_start, row_stop), slice(col_start, col_stop))

                    if resize == True:
                        transform = rasterio.transform.from_origin(
                            geometry.bounds['minx'][0], geometry.bounds['maxy'][0], pixelSize//resize_val, pixelSize//resize_val)

                        # Update metadata for output image
                        metadata.update({"height": src.height * resize_val,
                            "width": src.width * resize_val,
                            "transform": transform})

                        if method == None:
                            method = Resampling.nearest
                        
                        out_img = src.read(out_shape = (src.height * resize_val, src.width * resize_val), resampling = method, window = win)

                    else:
                        # Clip image.
                        out_img = src.read(window = win)


                # Write output image to disk
                with rasterio.open(out_tif, "w", **metadata) as dest:
                    dest.write(out_img)
                
                setattr(image, '{}_clipped'.format(band), out_tif)

            else:
                raise BandNotFound("Object {} has no attribute {} (band).".format(image, band))
            

    @staticmethod
    def clipByMask(image, shapefile, band = None, new = None, resize = False, method = None, ext = 'tif'):
        """Mask image based on a shapefile mask.

        Args:
            image (senimage): senimage object
            shapefile (str, path-like): Path to shapefile mask
            band (str, optional): Band to be applied. Note that the band name must be the same with the object attribute name. Defaults to None
            new (str, optional): Piece of string added to the end of the new filename. Defaults to None. If None then it names the new data with the shapefile name
            resize (bool, optional): If True resizes the output resize_val times. Defaults to False
            method (rasterio.enum.Resampling, optional): Resampling method. Defaults to None
            ext (str, optional): Extention of the image. Defaults to 'tif'

        Raises:
            PathError: Raises when cannot find a path to store the new image
            BandNotFound: Raises when the image has no attribute band selected by the user
        """
        if band != None:

            if hasattr(image, band):

                if hasattr(image, 'datapath'):
                    path = image.datapath
                else:
                    resolution = image.setResolution(band)
                    if int(resolution) == 20 and resize == True:
                        if hasattr(image, 'datapath_10'):
                            path = image.datapath_10
                        else:
                            raise PathError("Could not find a path to store the image.")
                    elif int(resolution) == 20 and resize == False:
                        if hasattr(image, 'datapath_20'):
                            path = image.datapath_20
                        else:
                            raise PathError("Could not find a path to store the image.")
                    else:
                        if hasattr(image, 'datapath_10'):
                            path = image.datapath_10
                        else:
                            raise PathError("Could not find a path to store the image.")

                if new is None:
                    new = os.path.splitext(os.path.basename(shapefile))[0]
                    print(new)
                # New name for output image
                out_tif = os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))

                if os.path.exists(out_tif) == True and os.stat(out_tif).st_size != 0:
                    # Pass if file already exists & it's size is not zero
                    logging.info("File {} already exists...".format(os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))))
                    setattr(image, '{}_masked'.format(band), out_tif)
                    return

                if int(resolution) == 20 and resize == True:
                    logging.info("Extracting {} by mask of inserted SHP and resample to 10 meters resolution...".format(
                        getattr(image, band))
                                )
                else:
                    logging.info("Extracting {} by mask of inserted SHP...".format(getattr(image, band)))

                shapes = gpd.read_file(shapefile)
                
                if int(resolution) == 20 and resize == True:
                    if method is None:
                        resampling = Resampling.nearest
                    
                    src = rasterio.open(getattr(image, band))
                    
                    if src.crs != shapes.crs:
                        shapes = shapes.to_crs(src.crs.to_epsg())

                    # Use as high resolution bands only 4 and 8 that are trustworthy
                    hr_bands = ['B04', 'B08']
                    hr_band = None
                    for hrb in hr_bands:
                        if hasattr(image, hrb):
                            hr_band = getattr(image, hrb)
                            break
                    if hr_bands is None:
                        raise BandNotFound("No high resolution band found!")
                    
                    with rasterio.open(hr_band, "r+") as hr:
                        data, transform = mask(hr, shapes.geometry, crop = True, filled = True, nodata = 0)

                    reproj_array, _ = reproject(
                        source = src.read(1),
                        destination = np.empty(shape=data.shape),
                        src_transform = src.transform,
                        src_crs = src.crs,
                        dst_transform = transform,
                        dst_crs = hr.crs,
                        resampling = resampling
                        )

                    if src.meta["dtype"] == "uint16" or src.meta["dtype"] == "uint8":
                        reproj_array[data == 0] = 0
                        nodata = 0
                    elif src.meta["dtype"] == "float32":
                        reproj_array[data == 0] = -9999
                        nodata = -9999
                    else:
                        raise TypeError("Only float32, uint16 or uint8 datatypes are supported!")

                    metadata = hr.meta.copy()
                    metadata.update({"height": data.shape[1],
                        "width": data.shape[2],
                        "transform": transform,
                        "dtype": src.meta["dtype"],
                        "driver": "GTiff",
                        "nodata": nodata
                        })

                    with rasterio.open(out_tif, 'w', **metadata) as dst:
                        dst.write(reproj_array)
                else:

                    with rasterio.open(getattr(image, band), "r+") as src:
                        if src.crs != shapes.crs:
                            shapes = shapes.to_crs(src.crs.to_epsg())
                        
                        if src.meta["dtype"] == "uint16" or src.meta["dtype"] == "uint8":
                            nodata = 0
                        elif src.meta["dtype"] == "float32":
                            nodata = -9999
                        else:
                            raise TypeError("Only float32, uint16 or uint8 datatypes are supported!")

                        out_image, out_transform = mask(src, shapes.geometry, crop = True, filled = True, nodata = nodata)
                        out_meta = src.meta
                        out_crs = src.crs
                        out_meta.update({"driver": "GTiff",
                                        "crs": out_crs,
                                        "height": out_image.shape[1],
                                        "width": out_image.shape[2],
                                        "transform": out_transform,
                                        "nodata": nodata})
                    
                    with rasterio.open(out_tif, "w", **out_meta) as output_image:
                        output_image.write(out_image)
                
                setattr(image, '{}_masked'.format(band), out_tif)
            
        else:
            raise BandNotFound("Object {} has no attribute {} (band).".format(image, band))
