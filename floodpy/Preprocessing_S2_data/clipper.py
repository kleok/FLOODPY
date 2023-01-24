#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import rasterio
import geopandas as gpd
from rasterio.enums import Resampling
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
import numpy as np
from floodpy.Preprocessing_S2_data.exceptions import BandNotFound, PathError

class Clipper():

    @staticmethod
    def clipByMask(image, shapefile, store = None, band = None, new = None, resize = False, method = None, ext = 'tif'):
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
                resolution = image.setResolution(band)
                if hasattr(image, 'datapath'):
                    if store == None:
                        path = image.datapath
                    else:
                        path = store
                    
                    if resize:
                        res = 10
                    else:
                        res = image.setResolution(band)
                else:
                    if int(resolution) == 20 and resize == True:
                        if store == None:
                            if hasattr(image, 'datapath_10'):
                                res = 10
                                path = image.datapath_10
                            else:
                                raise PathError("Could not find a path to store the image.")
                        else:
                            res = 10
                            path = store
                    
                    elif int(resolution) == 20 and resize == False:
                        if store == None:
                            if hasattr(image, 'datapath_20'):
                                path = image.datapath_20
                                res = 20
                            else:
                                raise PathError("Could not find a path to store the image.")
                        else:
                            path = store
                            res = 20
                    else:
                        if store == None:
                            if hasattr(image, 'datapath_10'):
                                path = image.datapath_10
                                res = 10
                            else:
                                raise PathError("Could not find a path to store the image.")
                        else:
                            path = store
                            res = 10

                if new is None:
                    new = str(res) + "_" + os.path.splitext(os.path.basename(shapefile))[0]
                    
                # New name for output image
                out_tif = os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))

                if os.path.exists(out_tif) == True and os.stat(out_tif).st_size != 0:
                    # Pass if file already exists & it's size is not zero
                    logging.warning("File {} already exists...".format(os.path.join(path, "T{}_{}_{}_{}.{}".format(image.tile_id, image.str_datetime, band, new, ext))))
                    attr_name = os.path.splitext(os.path.basename(shapefile))[0]
                    try:
                        getattr(image, band)[str(res)][attr_name] = out_tif
                    except KeyError:
                        getattr(image, band).update({str(res): {attr_name: out_tif}})    
                    
                    return

                if int(resolution) == 20 and resize == True:
                    logging.info("Extracting {} by mask of inserted SHP and resample to 10 meters resolution...".format(
                        getattr(image, band)[resolution]["raw"])
                                )
                else:
                    logging.info("Extracting {} by mask of inserted SHP...".format(getattr(image, band)[resolution]["raw"]))

                shapes = gpd.read_file(shapefile)
                
                if int(resolution) == 20 and resize == True:
                    if method is None:
                        resampling = Resampling.nearest
                    else:
                        resampling = method
                    
                    src = rasterio.open(getattr(image, band)[resolution]['raw'])
                    
                    if src.crs != shapes.crs:
                        shapes = shapes.to_crs(src.crs.to_epsg())

                    # Use as high resolution bands only 4 and 8 that are trustworthy
                    hr_bands = ['B04', 'B08']
                    hr_band = None
                    for hrb in hr_bands:
                        if hasattr(image, hrb):
                            hr_band = getattr(image, hrb)["10"]["raw"]
                            break
                    if hr_bands is None:
                        raise BandNotFound("No high resolution band found!")
                    
                    with rasterio.open(hr_band, "r") as hr:
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

                    with rasterio.open(getattr(image, band)[resolution]["raw"], "r") as src:
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
                
                attr_name = os.path.splitext(os.path.basename(shapefile))[0]
                try:
                    getattr(image, band)[str(res)][attr_name] = out_tif
                except KeyError:
                    getattr(image, band).update({str(res): {attr_name: out_tif}})            
        else:
            raise BandNotFound("Object {} has no attribute {} (band).".format(image, band))
