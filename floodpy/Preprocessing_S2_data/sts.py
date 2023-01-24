#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import fnmatch
import zipfile
from floodpy.Preprocessing_S2_data.simage import senimage
from floodpy.Preprocessing_S2_data.exceptions import NoDataError, BBOXError, imageError
from floodpy.Preprocessing_S2_data.clipper import Clipper
from floodpy.Preprocessing_S2_data.ts import timeseries

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(message)s', level = logging.INFO)

class sentimeseries(timeseries):
    """Sentinel 2 time series."""
    
    def __init__(self, name):
        timeseries.__init__(self, name)
        self.tiles = []

    def find_zip(self, path, level = "L2A", force_uncompress = False):
        """Find and extract automatically Sentinel-2 data from \*.zip.

        Args:
            path (str): Path to stored data
            level (str, optional): Sentinel 2 product level. Defaults to "L2A"
            force_uncompress (bool, optional): Force to re-uncompress in case an \*.SAFE file already exists. Defaults to False
        """
        image = None
        logging.info("---------------------------------------------------------------------------------------------")
        logging.info("Searching for Sentinel 2 Satellite data...")
        if path.endswith(".zip"):
            if os.path.exists(path):
                dirpath, file = os.path.split(path)
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
                    dirpath, file = os.path.split(path)
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
        else:
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

    def getVI(self, index:str, store:str = None, image:senimage = None, subregion = None):
        """Calculates a vegetation index for an image if the user provides an image or
        for all the time series.
        
        Args:
            index (str): Vegetation index. Currently works only for NDVI, NDWI, NDBI
            image (sentinel2): If an sentinel2 object is provided calculates VI for this image only
        """
        if store is None:
            # User can provide either the image name or the object.
            if image is None:
                logging.info("Calculating {} for all time series...".format(index))
                
                for im in self.data:
                    im.calcVI(index, subregion = subregion)
            else:
                if isinstance(image, senimage):
                    image.calcVI(index, subregion = subregion)
                else:
                    raise TypeError("Only sentinel2 objects are supported as image!")
        else:     
            if image is None:
                logging.info("Calculating {} for all time series...".format(index))
                for im in self.data:
                    generated_path = self._path_generator(im)
                    savepath = os.path.join(store, generated_path, im.name)
                    if not os.path.exists(savepath):
                        os.makedirs(savepath)
                    im.calcVI(index, store = savepath, subregion = subregion)
            else:
                generated_path = self._path_generator(image)
                savepath = os.path.join(store, generated_path, image.name)
                if not os.path.exists(savepath):
                    os.makedirs(savepath)
                if isinstance(image, senimage):
                    image.calcVI(index, store = savepath, subregion = subregion)
                else:
                    raise TypeError("Only sentinel2 objects are supported as image!")

    def clipbyMask(self, shapefile, image = None, band = None, resize = False, method = None, new = None, store = None):
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
                if store is None:
                    for im in self.data:
                        for b in bands:
                            Clipper.clipByMask(im, shapefile, band = b, resize = resize, method = method, new = new)
                else:
                    for im in self.data:
                        generated_path = self._path_generator(im)
                        savepath = os.path.join(store, generated_path, im.name)
                        if not os.path.exists(savepath):
                            os.makedirs(savepath)
                        for b in bands:
                            Clipper.clipByMask(im, shapefile, store = savepath, band = b, resize = resize, method = method, new = new)
            else:
                logging.info("Masking band {} for all time series with {}...".format(band, shapefile))
                if store is None:
                    for im in self.data:
                        Clipper.clipByMask(im, shapefile, band = band, resize = resize, method = method, new = new)
                else:
                    for im in self.data:
                        generated_path = self._path_generator(im)
                        savepath = os.path.join(store, generated_path, im.name)
                        if not os.path.exists(savepath):
                            os.makedirs(savepath)
                        Clipper.clipByMask(im, shapefile, store = savepath, band = band, resize = resize, method = method, new = new)
        else:
            if band is None:
                logging.info("Masking {} with {}...".format(image, shapefile))
                if store is None:
                    for b in bands:
                        Clipper.clipByMask(image, shapefile, band = b, resize = resize, method = method, new = new)
                else:
                    generated_path = self._path_generator(image)
                    savepath = os.path.join(store, generated_path, image.name)
                    if not os.path.exists(savepath):
                        os.makedirs(savepath)
                    for b in bands:
                        Clipper.clipByMask(image, shapefile, store = savepath, band = b, resize = resize, method = method, new = new)
            else:
                logging.info("Masking band {} of image {} with {}...".format(band, image, shapefile))
                if store is None:
                    Clipper.clipByMask(image, shapefile, band = band, resize = resize, method = method, new = new)
                else:
                    generated_path = self._path_generator(image)
                    savepath = os.path.join(store, generated_path, image.name)
                    if not os.path.exists(savepath):
                        os.makedirs(savepath) 
                    Clipper.clipByMask(image, shapefile, store = savepath, band = band, resize = resize, method = method, new = new)

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
    
    def upsample(self, image = None, band = None, resize = False, method = None, new = None, store = None, subregion = None):
        bands = ['B05', 'B06', 'B07', 'B8A', 'B11', 'B12', "SCL"]

        if image is None:
            if band is None:
                logging.info("Upsampling all time series with...")
                if store is None:
                    for im in self.data:
                        for b in bands:
                            im.upsample(band = b, store = store, method = method, new = new, subregion = subregion)
                else:
                    for im in self.data:
                        generated_path = self._path_generator(im)
                        savepath = os.path.join(store, generated_path, im.name)
                        if not os.path.exists(savepath):
                            os.makedirs(savepath)
                        for b in bands:
                            im.upsample(band = b, store = savepath, method = method, new = new, subregion = subregion)
            else:
                logging.info("Upsampling band {} for all time series...".format(band))
                if store is None:
                    for im in self.data:
                            im.upsample(band = b, store = store, method = method, new = new, subregion = subregion)
                else:
                    for im in self.data:
                        generated_path = self._path_generator(im)
                        savepath = os.path.join(store, generated_path, im.name)
                        if not os.path.exists(savepath):
                            os.makedirs(savepath)
                        im.upsample(band = band, store = savepath, method = method, new = new, subregion = subregion)
        else:
            if band is None:
                logging.info("Upsampling image {}...".format(image))
                if store is None:
                    for b in bands:
                            image.upsample(band = b, store = store, method = method, new = new, subregion = subregion)
                else:
                    generated_path = self._path_generator(image)
                    savepath = os.path.join(store, generated_path, image.name)
                    if not os.path.exists(savepath):
                        os.makedirs(savepath)
                    for b in bands:
                        image.upsample(band = b, store = savepath, method = method, new = new, subregion = subregion)
            else:
                logging.info("Upsampling band {} of image {}...".format(band, image))
                if store is None:
                    image.upsample(band = band, store = store, method = method, new = new, subregion = subregion)
                else:
                    generated_path = self._path_generator(image)
                    savepath = os.path.join(store, generated_path, image.name)
                    if not os.path.exists(savepath):
                        os.makedirs(savepath) 
                    image.upsample(band = band, store = savepath, method = method, new = new, subregion = subregion)


