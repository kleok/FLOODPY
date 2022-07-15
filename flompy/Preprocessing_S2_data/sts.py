#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import fnmatch
import zipfile

from .simage import senimage
from .exceptions import NoDataError, BBOXError, imageError
from .clipper import Clipper
from .ts import timeseries

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(message)s', level = logging.INFO)

class sentimeseries(timeseries):
    """Sentinel 2 time series."""
    
    def __init__(self, name):
        timeseries.__init__(self, name)
        self.tiles = []

    def find_zip(self, path, level = "L2A", force_uncompress = False):
        """Find and extract automatically Sentinel-2 data from *.zip.

        Args:
            path (str): Path to stored data
            level (str, optional): Sentinel 2 product level. Defaults to "L2A"
            force_uncompress (bool, optional): Force to re-uncompress in case an *.SAFE file already exists. Defaults to False
        """
        image = None
        logging.info("---------------------------------------------------------------------------------------------")
        logging.info("Searching for Sentinel 2 Satellite data...")
        for (dirpath, _, _) in os.walk(path):
            for file in os.listdir(dirpath):
                # Find data
                if fnmatch.fnmatch(str(file), '*{}*.zip'.format(level)):
                    logging.info("Raw data found (*.zip file): {}".format(str(file)))
                    name = os.path.splitext(os.path.split(file)[-1])[0] + ".SAFE"  
                    if (os.path.exists(os.path.join(dirpath, name))) and (force_uncompress is False):
                        logging.info("File {} exists! No need to uncompress".format(name))
                        image = senimage(dirpath, name)
                        image.getmetadata()
                        image.getBands()
                        self.data.append(image)
                        self.names.append(image.name)
                        self.dates.append(image.datetime)
                        self.cloud_cover.append(image.cloud_cover)
                        self.tiles.append(image.tile_id)
                    else:
                        if zipfile.is_zipfile(os.path.join(dirpath, file)):
                            with zipfile.ZipFile(os.path.join(dirpath, file), 'r') as src:
                                src.extractall(dirpath)
                            
                            image = senimage(dirpath, name)
                            image.getmetadata()
                            image.getBands()
                            self.data.append(image)
                            self.names.append(image.name)
                            self.dates.append(image.datetime)
                            self.cloud_cover.append(image.cloud_cover)
                            self.tiles.append(image.tile_id)
                        else:
                            raise imageError("File {} seems corrupted!".format(file))
        
        if len(self.data) == 0:
            raise NoDataError("0 Sentinel 2 raw data found in the selected path.")
        else:
            self.total = len(self.data)
        
        if len(list(set(self.tiles))) > 1:
            logging.warning("Available data are in more than one tiles!")
        
        logging.info("---------------------------------------------------------------------------------------------")

    def find(self, path, level = "L2A"):
        """Finds automatically all the available data in a provided path based on the S2 level
        product (L1C or L2A) that the user provides.

        Args:
            path (str, path-like): Search path
            level (str, optional): Level of the S2 time series (L1C or L2A). Defaults to 'L2A'.

        Raises:
            NoDataError: Raises when no data were found in the provided path
        """
        image = None
        logging.info("---------------------------------------------------------------------------------------------")
        logging.info("Searching for Sentinel 2 Satellite data...")
        for (dirpath, _, _) in os.walk(path):
            for file in os.listdir(dirpath):
                # Find data
                if fnmatch.fnmatch(str(file), '*{}*.SAFE'.format(level)):
                    logging.info("Raw data found (*.SAFE file): {}".format(str(file)))
                    
                    image = senimage(dirpath, file)
                    image.getmetadata()
                    image.getBands()
                    self.data.append(image)
                    self.names.append(image.name)
                    self.dates.append(image.datetime)
                    self.cloud_cover.append(image.cloud_cover)
                    self.tiles.append(image.tile_id)

        if len(self.data) == 0:
            raise NoDataError("0 Sentinel 2 raw data found in the selected path.")
        else:
            self.total = len(self.data)
        
        if len(list(set(self.tiles))) > 1:
            logging.warning("Available data are in more than one tiles!")

        logging.info("---------------------------------------------------------------------------------------------")
  
    def getVI(self, index, image = None):
        """Calculates a vegetation index for an image if the user provides an image or
        for all the time series.

        Args:
            index (str): Vegetation index. Currently works only for NDVI, EVI and MCARI image (senimage, optional): An complete S2image object that if the user provides the method calculates the selected vegetation index. Defaults to None
            image (senimage): If an senimage object is provided calculates VI for this image only
        """
        
        # User can provide either the image name or the object.
        if image is None:
            logging.info("Calculating {} for all time series...".format(index))
            
            for im in self.data:
                im.calcVI(index)
        else:
            if isinstance(image, senimage):
                image.calcVI(index)
            else:
                raise TypeError("Only senimage objects are supported as image!")
        


    def createbbox(self, minx, maxx, miny, maxy, srid):
        """Creating a bounding box to mask the image.

        Args:
            minx (int): Minimum x coordinate of the bounding box
            maxx (int): Maximum x coordinate of the bounding box
            miny (int): Minimum y coordinate of the bounding box
            maxy (int): Maximum y coordinate of the bounding box
            srid (int): SRID code
        """
        bbox = Clipper.boundingBox(minx, maxx, miny, maxy, srid)
        
        setattr(self, 'bbox', bbox)

    def clip(self, bbox = None, image = None, band = None):
        """Masks an image or a time series

        Args:
            bbox (GeoDataFrame, optional): Bounding box to mask the time series. Currently works only with a bounding box created by .createbox(). Defaults to None
            image (senimage, optional): An complete S2image object that if the user
            provides the method masks the selected image. Defaults to None
            band (str, optional): If the user provides a band the method masks only the specific band. Defaults to None
        """
        
        bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12']

        if bbox is None:
            logging.info("Checking if a bounding box is setted for the time series...")
            if hasattr(self, 'bbox'):
                if image is None:
                    if band is None:
                        logging.info("Clipping all time series...")

                        for im in self.data:
                            for b in bands:
                                Clipper.clip(im, self.bbox, band = b)
                    else:
                        logging.info("Clipping band {} for all time series...".format(band))
                        for im in self.data:
                            Clipper.clip(im, self.bbox, band = band)

                else:
                    if band is None:
                        logging.info("Clipping all bands of image {}...".format(image.name))
                        for b in bands:
                            Clipper.clip(image, self.bbox, band = b)
                    else:
                        logging.info("Clipping band {} of image {}...".format(band, image.name))
                        Clipper.clip(image, self.bbox, band = band)
            else:
                raise BBOXError("No bounding box is provided. Provide a BBOX or either use .createbbox() method to create one.")
        else:
            raise BBOXError("Currently works only with .createbbox() method.")

    def clipbyMask(self, shapefile, image = None, band = None, resize = False, method = None, new = None):
        """Masks an image or the complete time series with a shapefile.

        Args:
            shapefile (path-like, str): Path to shapefile mask
            image (senimage, optional): Masks a specific image. Defaults to None
            band (str, optional): Masks a specific band. Defaults to None
            resize (bool, optional): Resize band. Defaults to False
            method (rasterio.enums.Resampling): Available resampling methods. If None the Nearest is used. Defaults to None
        """
        bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12', "SCL"]

        if image is None:
            if band is None:
                logging.info("Masking all time series with {}...".format(shapefile))
                for im in self.data:
                    for b in bands:
                        Clipper.clipByMask(im, shapefile, band = b, resize = resize, method = method, new = new)
            else:
                logging.info("Masking band {} for all time series with {}...".format(band, shapefile))
                for im in self.data:
                    Clipper.clipByMask(im, shapefile, band = band, resize = resize, method = method, new = new)
        else:
            if band is None:
                logging.info("Masking {} with {}...".format(image, shapefile))
                for b in bands:
                    Clipper.clipByMask(image, shapefile, band = b, resize = resize, method = method, new = new)
            else:
                logging.info("Masking band {} of image {} with {}...".format(band, image, shapefile))
                Clipper.clipByMask(image, shapefile, band = band, resize = resize, method = method, new = new)
        
    def remove_orbit(self, orbit):
        """Remove images with specific orbit.

        Args:
            orbit (str): Number of orbit
        """
        if not isinstance(orbit, str):
            raise TypeError("Provide orbit as a string!")

        new = []
        for image in self.data:
            if image.orbit == None:
                logging.warning("Image {} has no date information stored!".format(image.name))
            elif image.orbit == orbit:
                logging.info("Removing {} with orbit {}...".format(image.name, image.orbit))
                self.names.remove(image.name)
                self.dates.remove(image.datetime)
                self.cloud_cover.remove(image.cloud_cover)
                self.tiles.remove(image.tile_id)
            else:
                new.append(image)
                logging.info("Keeping {} with orbit {}...".format(image.name, image.orbit))
        self.data = new
        self.total = len(self.data)
        del new
        logging.info("New number of data after removing orbit {} is: {}".format(orbit, len(self.data)))

