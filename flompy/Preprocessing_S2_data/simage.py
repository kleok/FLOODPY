#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import xml.etree.ElementTree as Etree
import fnmatch
import rasterio
import datetime
from rasterio.enums import Resampling
from flompy.Preprocessing_S2_data.vi import vi
from flompy.Preprocessing_S2_data.exceptions import VegetationIndexNotInList, BandNotFound

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(message)s', level = logging.INFO)

# Define a lambda function to convert dates
convert = lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%fZ')

class senimage():
    """A Sentinel 2 image."""
    
    def __init__(self, path, name):
        """ A Sentinel 2 image.

        Args:
            path (str, path-like): Path to image
            name (str): Name of the file
        """
        self.path = path
        self.name = name
        self.md_file = None
        self.satellite = None
        self.datetime = None
        self.date = None
        self.time = None
        self.str_datetime = None
        self.gml_coordinates = None
        self.cloud_cover = None
        self.processing_level = None
        self.tile_id = None
        self.orbit = None
        
    def getmetadata(self):
        """Searching for metadata (XML) files.
        """
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
            for file in filenames:
                if file.startswith("MTD_MSI"):
                    self.md_file = file
                    self._parseXML(dirpath, file)

    def _parseXML(self, path, file):
        """Parsing XML metadata file.

        Args:
            path (str, path-like): Path to file
            file (str): Name of the file
        """
        #logging.info("  - Reading {}".format(os.path.join(self.path, self.name, file)))
        tree = Etree.parse(os.path.join(self.path, self.name, file))
        root = tree.getroot()
        self.satellite = root.findall(".//SPACECRAFT_NAME")[0].text
        self.str_datetime = self.name[11:26]
        self.datetime = convert(root.findall(".//DATATAKE_SENSING_START")[0].text)
        self.date = self.datetime.date()
        self.time = self.datetime.time()
        self.gml_coordinates = root.findall(".//EXT_POS_LIST")[0].text
  
        self.cloud_cover = "{:.3f}".format(float(root.findall(".//Cloud_Coverage_Assessment")[0].text))
        self.processing_level = root.findall(".//PROCESSING_LEVEL")[0].text
        self.tile_id = self.name[39:44]
        self.orbit = root.findall(".//SENSING_ORBIT_NUMBER")[0].text
        #logging.info("  - Done!")

    @staticmethod
    def setResolution(band):
        """ Getting band resolution for Sentinel 2.

        Args:
            band (str): Band short name as string

        Returns:
            str: Band resolution
        """
        resolutions = {
            "B01": "60",
            "B02": "10",
            "B03": "10",
            "B04": "10",
            "B05": "20",
            "B06": "20",
            "B07": "20",
            "B08": "10",
            "B8A": "20",
            "B09": "60",
            "B10": "60",
            "B11": "20",
            "B12": "20",
            "SCL": "20",
            "NDVI": "10",
            "NDMI": "20",
            "EVI": "10",
            "MCARI": "10"
        }
        return resolutions.get(band)

    def getBands(self):
        """Finds all the available bands of an image and sets new attributes for each band.
        """

        bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12', "SCL"]

        for band in bands:
            resolution = self.setResolution(band)

            for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            setattr(self, 'datapath_{}'.format(resolution), os.path.join(dirpath))
                            break
                    else:
                        if fnmatch.fnmatch(file, "*_{}_*.jp2".format(band)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, 'datapath', os.path.join(dirpath))
                            break

            for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, '{}'.format(band), os.path.join(dirpath, file))
                    else:    
                        if fnmatch.fnmatch(file, "*_{}_*.jp2".format(band)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, '{}'.format(band), os.path.join(dirpath, file))


    def show_metadata(self):
        """Prints metadata using __dict__
        """
        print (self.__dict__)

    def ReadData(self, band = None):
        """Reads bands as rasterio objects and the objects are added as attributes.

        Args:
            band (str, optional): Reads a specific band as rasterio object, in other case reads all the available bands. Defaults to None.

        Returns:
            rasterio.io.DatasetReader, list: Band as rasterio object or list of bands as rasterio objects 
        """

        if band == None:
            bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12']
            images = []
            for b in bands:
                # logging.info("Reading {}".format(getattr(self, b)))
                image = rasterio.open(getattr(self, b))
                setattr(self, 'rasterio{}'.format(b), image)
                images.append(image)
            
            return images
            
        else:
            # logging.info("Reading {}".format(getattr(self, band)))
            image = rasterio.open(getattr(self, band))
            setattr(self, 'rasterio{}'.format(band), image)
        
            return image

    @staticmethod
    def ReadArray(images, height = None, width = None, method = None):
        """Reads rasterio objects as ndarray and if the user provides width and height resampling is applied. 

        Args:
            images (rasterio.io.DatasetReader, list): A rasterio object or a list of objects 
            height (int, optional): New height to resample, if None no resampling is applied. Defaults to None
            width (int, optional): New width to resample, if None no resampling is applied. Defaults to None
            method (rasterio.enums.Resampling, optional): Resampling method if user provided height and width. If None Resampling.nearest is used.\
            Other choices are Resampling.bilinear, Resampling.cubic, Resampling.cubic_spline, Resampling.lanczos etc.\
            For more information read at https://rasterio.readthedocs.io/en/latest/api/rasterio.enums.html#rasterio.enums.Resampling. Defaults to None

        Returns:
             ndarray: Image as numpy array
        """

        #logging.info("Reading array...")
        if isinstance(images, list):
            arrays = []
            for image in images:
                if height is not None and width is not None:
                    if method == None:
                        method = Resampling.nearest
                    array = image.read(out_shape = (height, width), resampling = method)
                else:
                    array = image.read()
                arrays.append(array)
            
            return arrays
        else:
            if height is not None and width is not None:
                    if method == None:
                        method = Resampling.nearest
                    array = images.read(out_shape = (height, width), resampling = method)
            else:
                array = images.read()
            
            return array

    @staticmethod
    def writeResults(path, name, array, width, height, crs, transform, driver = 'Gtiff', count = 1, dtype = rasterio.float32):
        """Writing a new image with the use of rasterio module.

        Args:
            path (str, path-like): Path to image
            name (str): Image name
            array (ndarray): Image numpy array
            width (int): Width of array
            height (int): Height of array
            crs (rasterio.crs.CRS): Coordinate system of the image
            transform (affine.Affine): Transformation type
            driver (str, optional): Currently only Gtiff is supported. Defaults to 'Gtiff'.
            count (int, optional): Numbers of bands to write. Currently only 1 is supported. Defaults to 1.
            dtype (str, optional): Datatype of the image. Defaults to rasterio.float32.
        """

        logging.info("Saving {}...".format(name))
        with rasterio.open(os.path.join(path, name), "w", driver = driver, width = width, height = height, count = count,
            crs = crs, transform = transform, dtype = dtype) as output_image:
            output_image.write(array)

    def calcVI(self, index):
        """Calculates a selected vegetation index (NDVI, EVI, MCARI).

        Args:
            index (str): Vegetation index to be calculated and saved. Currently only NDVI, EVI and MCARI are supported
        """
        ext = 'tif'
        
        if index == 'NDVI':
            if os.path.isfile(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))):
                logging.info("File {} already exists...".format(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))))
                if not hasattr(self, index):
                    name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                    setattr(self, '{}'.format(index), os.path.join(self.datapath_10, name))
                    # Setting NDVI image object to S2 image
                    image = rasterio.open(getattr(self, index))
                    setattr(self, 'rasterio{}'.format(index), image)
                return
            else:
                if hasattr(self, "B08"):
                    nir = self.ReadData('B08')
                else:
                    raise BandNotFound("{} object has no attribute B08 (Image: {})".format(self, self.name))
                
                if hasattr(self, "B04"):
                    red = self.ReadData('B04')
                else:
                    raise BandNotFound("{} object has no attribute B04 (Image: {})".format(self, self.name))
                
                logging.info("Calculating {} for image {}...".format(index, self.name))
                nir_array = self.ReadArray(nir).astype(rasterio.float32)
                red_array = self.ReadArray(red).astype(rasterio.float32)
                ndvi_array = vi.ndvi(red_array, nir_array)
                path = self.datapath_10
                name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                width = nir.width
                height = nir.height
                crs = nir.crs
                transform=nir.transform
                self.writeResults(path, name, ndvi_array, width, height, crs, transform)
                # Setting NDVI attribute to S2 image
                setattr(self, '{}'.format(index), os.path.join(path, name))
                # Setting NDVI image object to S2 image
                image = rasterio.open(getattr(self, index))
                setattr(self, 'rasterio{}'.format(index), image)
                
                #logging.info("Done!")

        elif index == "NDMI":
            if os.path.isfile(os.path.join(self.datapath_20, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))):
                logging.info("File {} already exists...".format(os.path.join(self.datapath_20, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))))
                if not hasattr(self, index):
                    name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                    setattr(self, '{}'.format(index), os.path.join(self.datapath_20, name))
                    # Setting NDVI image object to S2 image
                    image = rasterio.open(getattr(self, index))
                    setattr(self, 'rasterio{}'.format(index), image)
                return
            else:
                if hasattr(self, "B8A"):
                    nir = self.ReadData('B8A')
                else:
                    raise BandNotFound("{} object has no attribute B8A (Image: {})".format(self, self.name))
                
                if hasattr(self, "B11"):
                    swir = self.ReadData('B11')
                else:
                    raise BandNotFound("{} object has no attribute B11 (Image: {})".format(self, self.name))
                
                logging.info("Calculating {} for image {}...".format(index, self.name))
                nir_array = self.ReadArray(nir).astype(rasterio.float32)
                swir_array = self.ReadArray(swir).astype(rasterio.float32)
                ndvi_array = vi.ndmi(nir_array, swir_array)
                path = self.datapath_20
                name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                width = nir.width
                height = nir.height
                crs = nir.crs
                transform=nir.transform
                self.writeResults(path, name, ndvi_array, width, height, crs, transform)
                # Setting NDVI attribute to S2 image
                setattr(self, '{}'.format(index), os.path.join(path, name))
                # Setting NDVI image object to S2 image
                image = rasterio.open(getattr(self, index))
                setattr(self, 'rasterio{}'.format(index), image)
                
                logging.info("Done!")

        elif index == 'EVI':
            
            if os.path.isfile(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))):
                logging.info("File {} already exists...".format(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))))
                return
            else:
                if hasattr(self, "B08"):
                    nir = self.ReadData('B08')
                else:
                    raise BandNotFound("{} object has no attribute B08 (Image: {})".format(self, self.name))
                
                if hasattr(self, "B04"):
                    red = self.ReadData('B04')
                else:
                    raise BandNotFound("{} object has no attribute B04 (Image: {})".format(self, self.name))
                
                if hasattr(self, "B02"):
                    blue = self.ReadData('B02')
                else:
                    raise BandNotFound("{} object has no attribute B02 (Image: {})".format(self, self.name))
                
                logging.info("Calculating {} for image {}...".format(index, self.name))

                nir_array = self.ReadArray(nir).astype(rasterio.float32)
                red_array = self.ReadArray(red).astype(rasterio.float32)
                blue_array = self.ReadArray(blue).astype(rasterio.float32)
                evi_array = vi.evi(nir_array, red_array, blue_array)
                path = self.datapath_10
                name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                width = nir.width
                height = nir.height
                crs = nir.crs
                transform=nir.transform
                self.writeResults(path, name, evi_array, width, height, crs, transform)
                # Setting index attribute to S2 image
                setattr(self, '{}'.format(index), os.path.join(path, name))
                # Setting index image object to S2 image
                image = rasterio.open(getattr(self, index))
                setattr(self, 'rasterio{}'.format(index), image)
                
                logging.info("Done!")

        elif index == 'MCARI':
            #(B05 - B04) - 0.2 * (B05 - B03)) * (B05 / B04)
            if os.path.isfile(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))):
                logging.info("File {} already exists...".format(os.path.join(self.datapath_10, "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext))))
                return
            else:
                if hasattr(self, "B05"):
                    red_edge = self.ReadData('B05')
                else:
                    raise BandNotFound("{} object has no attribute B05 (Image: {})".format(self, self.name))
                
                if hasattr(self, "B04"):
                    red = self.ReadData('B04')
                else:
                    raise BandNotFound("{} object has no attribute B04 (Image: {})".format(self, self.name))
                
                if hasattr(self, "B03"):
                    green = self.ReadData('B03')
                else:
                    raise BandNotFound("{} object has no attribute B03 (Image: {})".format(self, self.name))   
                
                logging.info("Calculating {} for image {}...".format(index, self.name))
                    
                re_array = self.ReadArray(red_edge, red.height, red.width).astype(rasterio.float32)
                red_array = self.ReadArray(red).astype(rasterio.float32)
                green_array = self.ReadArray(green).astype(rasterio.float32)
                mcari_array = vi.mcari(re_array, red_array, green_array)

                path = self.datapath_10
                name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)
                width = red.width
                height = red.height
                crs = red.crs
                transform=red.transform
                self.writeResults(path, name, mcari_array, width, height, crs, transform)
                # Setting index attribute to S2 image
                setattr(self, '{}'.format(index), os.path.join(path, name))
                # Setting index image object to S2 image
                image = rasterio.open(getattr(self, index))
                setattr(self, 'rasterio{}'.format(index), image)

                logging.info("Done!")

        else:
                raise VegetationIndexNotInList("The provided vegetation index is not in the list.")
