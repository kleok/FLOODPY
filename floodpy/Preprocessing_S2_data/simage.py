#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import xml.etree.ElementTree as Etree
import fnmatch
import rasterio
import datetime
import pyproj
from rasterio.enums import Resampling
from rasterio.warp import reproject
import numpy as np
from floodpy.Preprocessing_S2_data.vi import vi
from floodpy.Preprocessing_S2_data.exceptions import VegetationIndexNotInList, BandNotFound, PathError

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
        self.tile_md_file = None
        self.satellite = None
        self.datetime = None
        self.date = None
        self.time = None
        self.str_datetime = None
        self.gml_coordinates = None
        self.cloud_cover = None
        self.processing_level = None
        self.tile_id = None
        self.crs = None
        self.orbit = None

    def getmetadata(self):
        """Searching for metadata (XML) files.
        """
        for (dirpath, _, filenames) in os.walk(os.path.join(self.path, self.name)):
            for file in filenames:
                if file.startswith("MTD_MSI"):
                    self.md_file = file
                    XML = self._readXML(dirpath, file)
                    self._parseGeneralMetadata(XML)
                elif file.startswith("MTD_TL"):
                    self.tile_md_file = file
                    XML = self._readXML(dirpath, file)
                    self._parseTileMetadata(XML)

    def _readXML(self, path:str, file:str):
        """Reads XML file.

        Args:
            path (str): Path to file
            file (str): Name of the file plus extention

        Returns:
            Etree.Element: XML opened file
        """
        tree = Etree.parse(os.path.join(path, file))
        root = tree.getroot()

        return root

    def _parseGeneralMetadata(self, root):
        """Parsing general S2 metadata from eTree.Element type object.

        Args:
            root (eTree.Element): S2 metadata from eTree.Element type object
        """
        logging.info("Parsing Image Metadata file...")
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
        logging.info("Done!")

    def _parseTileMetadata(self, root):
        """Parsing general S2 tile metadata from eTree.Element type object.

        Args:
            root (eTree.Element): S2 tile metadata from eTree.Element type object
        """

        logging.info("Parsing Tile Metadata file...")
        epsg = root[1][0][1].text
        self.crs = pyproj.crs.CRS(epsg)
        logging.info("Done!")

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
            "TCI": "10",
            "NDVI": "10",
            "NDBI": "20",
            "NDWI": "10",
        }
        return resolutions.get(band)

    def getBands(self):
        """Finds all the available bands of an image and sets new attributes for each band.
        """

        bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12', "SCL", "TCI"]

        for band in bands:
            resolution = self.setResolution(band)

            for (dirpath, _, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            setattr(self, 'datapath_{}'.format(resolution), os.path.join(dirpath))
                            break
                    else:
                        if fnmatch.fnmatch(file, "*_{}.jp2".format(band)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, 'datapath', os.path.join(dirpath))
                            break

            for (dirpath, _, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            setattr(self, '{}'.format(band), {resolution: {"raw" : os.path.join(dirpath, file)}})
                    else:    
                        if fnmatch.fnmatch(file, "*_{}.jp2".format(band)):
                            setattr(self, '{}'.format(band), {resolution: {"raw" : os.path.join(dirpath, file)}})

    @property
    def show_metadata(self):
        """Prints metadata using __dict__
        """
        print (self.__dict__)
    
    @staticmethod
    def writeResults(path:str, name:str, array:np.array, metadata:dict):
        """Writing a new image with the use of rasterio module.
        Args:
            path (str): Path to image
            name (str): Image name
            array (np.ndarray): Image numpy array
            metadata (dict): Metadata dictionary
        """
        logging.info("Saving {}...".format(name))
        with rasterio.open(os.path.join(path, name), "w", **metadata) as dst:
            if array.ndim == 2:
                dst.write(array, 1)
            else:
                dst.write(array)

    def upsample(self, store = None, band = None, new = None, subregion = None, method = None, ext = 'tif'):
        if subregion is None:
            region = "raw"
        else:
            region = subregion

        if band != None:
            if hasattr(self, band):
                resolution = self.setResolution(band)
                if int(resolution) == 20:
                    if hasattr(self, 'datapath'):
                        if store is None:
                            path = self.datapath
                            res = 10
                        else:
                            path = store
                            res = 10
                    else:
                        if store is None:
                            if hasattr(self, 'datapath_10'):
                                res = 10
                                path = self.datapath_10
                            else:
                                raise PathError("Could not find a path to store the image.")
                        else:
                            res = 10
                            path = store
                
                if new is None:
                    new = str(res) + "_Upsampled"
                    
                # New name for output image
                out_tif = os.path.join(path, "T{}_{}_{}_{}.{}".format(self.tile_id, self.str_datetime, band, new, ext))

                if os.path.exists(out_tif) == True and os.stat(out_tif).st_size != 0:
                    # Pass if file already exists & it's size is not zero
                    logging.warning("File {} already exists...".format(os.path.join(path, "T{}_{}_{}_{}.{}".format(self.tile_id, self.str_datetime, band, new, ext))))
                    try:
                        getattr(self, band)[str(res)][region] = out_tif
                    except KeyError:
                        getattr(self, band).update({str(res): {region: out_tif}})    
                    return
                
                if method is None:
                    resampling = Resampling.nearest
                else:
                    resampling = method

                # Use as high resolution bands only 4 and 8 that are trustworthy
                hr_bands = ['B04', 'B08']
                hr_band = None
                for hrb in hr_bands:
                    if hasattr(self, hrb):
                        hr_band = getattr(self, hrb)["10"][region]
                        break
                if hr_bands is None:
                    raise BandNotFound("No high resolution band found!")

                fpath = getattr(self, band)[str(resolution)][region]
                self.reproj_match(os.path.join(path, fpath), hr_band, to_file = True, outfile = out_tif, resampling = resampling)

                try:
                    getattr(self, band)[str(res)][region] = out_tif
                except KeyError:
                    getattr(self, band).update({str(res): {region: out_tif}})
            
            else:
                raise BandNotFound("Object {} has no attribute {} (band).".format(self, band))
    
    @staticmethod
    def reproj_match(image:str, base:str, to_file:bool = False, outfile:str = "output.tif", resampling:rasterio.warp.Resampling = Resampling.nearest) -> None:
        """Reprojects/Resamples an image to a base image.
        Args:
            image (str): Path to input file to reproject/resample
            base (str): Path to raster with desired shape and projection 
            outfile (str): Path to saving Geotiff
        """
        # open input
        with rasterio.open(image) as src:
            # open input to match
            with rasterio.open(base) as match:
                dst_crs = match.crs
                dst_transform = match.meta["transform"]
                dst_width = match.width
                dst_height = match.height
            # set properties for output
            metadata = src.meta.copy()
            metadata.update({"crs": dst_crs,
                            "transform": dst_transform,
                            "width": dst_width,
                            "height": dst_height,
                            })
            if to_file:
                with rasterio.open(outfile, "w", **metadata) as dst:
                    # iterate through bands and write using reproject function
                    for i in range(1, src.count + 1):
                        reproject(
                            source = rasterio.band(src, i),
                            destination = rasterio.band(dst, i),
                            src_transform = src.transform,
                            src_crs = src.crs,
                            dst_transform = dst_transform,
                            dst_crs = dst_crs,
                            resampling = resampling)
                return None
            else:
                array, transform = reproject(
                            source = rasterio.band(src, 1),
                            destination = np.ndarray((1, dst_height, dst_width)),
                            src_transform = src.transform,
                            src_crs = src.crs,
                            dst_transform = dst_transform,
                            dst_crs = dst_crs,
                            resampling = resampling)
                
                return(array, transform)


    def calcVI(self, index, store = None, subregion = None):
        """Calculates a selected vegetation index (NDVI, NDBI, NDWI).
        Args:
            index (str): Vegetation index to be calculated and saved. Currently only NDVI, NDMI are supported
        """
        driver = "Gtiff"
        ext = "tif"

        if subregion is None:
            region = "raw"
            new_name = "T{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, ext)

        else:
            region = subregion
            new_name = "T{}_{}_{}_{}_{}.{}".format(self.tile_id, self.str_datetime, index, self.setResolution(index), subregion, ext)

        if index == 'NDVI':
            if store == None:
                if os.path.isfile(os.path.join(self.datapath_10, new_name)):
                    logging.warning("File {} already exists...".format(os.path.join(self.datapath_10, new_name)))
                    if not hasattr(self, index):
                        setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(self.datapath_10, new_name)}})
                    return
                else:
                    if hasattr(self, "B08"):
                        if self.B08.get("10").get(region) != None:
                            nir = rasterio.open(self.B08["10"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B08 (Image: {})".format(self, self.name))
                    
                    if hasattr(self, "B04"):
                        if self.B04.get("10").get(region) != None:
                            red = rasterio.open(self.B04["10"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B04 (Image: {})".format(self, self.name))
                    
                    logging.info("Calculating {} for image {}...".format(index, self.name))
                    nir_array = nir.read().astype(rasterio.float32)
                    red_array = red.read().astype(rasterio.float32)
                    ndvi_array = vi.ndvi(red_array, nir_array)
                    ndvi_array[nir_array == nir.meta["nodata"]] = -9999.
                    ndvi_array[red_array == red.meta["nodata"]] = -9999.
                    path = self.datapath_10
                    metadata = red.meta.copy()
                    metadata.update({"driver": driver, "dtype": ndvi_array.dtype, "nodata": -9999.})
                    self.writeResults(path, new_name, ndvi_array, metadata)
                    # Setting NDVI attribute to S2 image
                    setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(self.datapath_10, new_name)}})
            else:
                if os.path.isfile(os.path.join(store, new_name)):
                    logging.warning("File {} already exists...".format(os.path.join(store, new_name)))
                    if not hasattr(self, index):
                        setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(store, new_name)}})
                    return
                else:
                    if hasattr(self, "B08"):
                        if self.B08.get("10").get(region) != None:
                            nir = rasterio.open(self.B08["10"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B08 (Image: {})".format(self, self.name))
                    
                    if hasattr(self, "B04"):
                        if self.B08.get("10").get(region) != None:
                            red = rasterio.open(self.B04["10"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B04 (Image: {})".format(self, self.name))
                    
                    logging.info("Calculating {} for image {}...".format(index, self.name))
                    nir_array = nir.read().astype(rasterio.float32)
                    red_array = red.read().astype(rasterio.float32)
                    ndvi_array = vi.ndvi(red_array, nir_array)
                    ndvi_array[nir_array == nir.meta["nodata"]] = -9999.
                    ndvi_array[red_array == red.meta["nodata"]] = -9999.
                    path = store
                    metadata = red.meta.copy()
                    metadata.update({"driver": driver, "dtype": ndvi_array.dtype, "nodata": -9999.})
                    self.writeResults(path, new_name, ndvi_array, metadata)
                    # Setting NDVI attribute to S2 image
                    setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(path, new_name)}})

        elif index == 'NDMI':
            if store == None:
                if os.path.isfile(os.path.join(self.datapath_20, new_name)):
                    logging.warning("File {} already exists...".format(os.path.join(self.datapath_20, new_name)))
                    if not hasattr(self, index):
                        setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(self.datapath_20, new_name)}})
                    return
                else:
                    if hasattr(self, "B8A"):
                        if self.B8A.get("20").get(region) != None:
                            nir = rasterio.open(self.B8A["20"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B8A (Image: {})".format(self, self.name))
                    
                    if hasattr(self, "B11"):
                        if self.B11.get("20").get(region) != None:
                            swir = rasterio.open(self.B11["20"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B11 (Image: {})".format(self, self.name))
                    
                    logging.info("Calculating {} for image {}...".format(index, self.name))
                    nir_array = nir.read().astype(rasterio.float32)
                    swir_array = swir.read().astype(rasterio.float32)
                    ndmi_array = vi.ndmi(nir_array, swir_array)
                    ndmi_array[nir_array == nir.meta["nodata"]] = -9999.
                    ndmi_array[swir_array == swir.meta["nodata"]] = -9999.
                    path = self.datapath_20
                    metadata = nir.meta.copy()
                    metadata.update({"driver": driver, "dtype": ndmi_array.dtype, "nodata": -9999.})
                    self.writeResults(path, new_name, ndmi_array, metadata)
                    # Setting NDVI attribute to S2 image
                    setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(self.datapath_20, new_name)}})
            else:
                if os.path.isfile(os.path.join(store, new_name)):
                    logging.warning("File {} already exists...".format(os.path.join(store, new_name)))
                    if not hasattr(self, index):
                        setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(store, new_name)}})
                    return
                else:
                    if hasattr(self, "B8A"):
                        if self.B8A.get("20").get(region) != None:
                            nir = rasterio.open(self.B8A["20"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B8A (Image: {})".format(self, self.name))
                    
                    if hasattr(self, "B11"):
                        if self.B11.get("20").get(region) != None:
                            swir = rasterio.open(self.B11["20"][region])
                        else:
                            raise BandNotFound("{} object has no stored path for resolution {} and raw data.".format(self, self.setResolution(index)))
                    else:
                        raise BandNotFound("{} object has no attribute B11 (Image: {})".format(self, self.name))
                    
                    logging.info("Calculating {} for image {}...".format(index, self.name))
                    nir_array = nir.read().astype(rasterio.float32)
                    swir_array = swir.read().astype(rasterio.float32)
                    ndmi_array = vi.ndvi(nir_array, swir_array)
                    ndmi_array[nir_array == nir.meta["nodata"]] = -9999.
                    ndmi_array[swir_array == swir.meta["nodata"]] = -9999.
                    path = store
                    metadata = nir.meta.copy()
                    metadata.update({"driver": driver, "dtype": ndmi_array.dtype, "nodata": -9999.})
                    self.writeResults(path, new_name, ndmi_array, metadata)
                    # Setting NDVI attribute to S2 image
                    setattr(self, '{}'.format(index), {self.setResolution(index): {region : os.path.join(path, new_name)}})
        else:
            VegetationIndexNotInList(f"Index {index} not in list of available indexes.")

