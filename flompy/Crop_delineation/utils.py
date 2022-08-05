#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2021-2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Olympia Gounari, Alekos Falagas, Kleanthis Karamvasis

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
import math
import numpy as np
import pandas as pd
import rasterio as rio
import geopandas as gpd
from scipy import signal
import requests
from requests import exceptions
import json
import shapely.wkt
import rasterio
from rasterio.warp import reproject, Resampling
from tqdm.auto import tqdm

def equation_3(fpaths:list, kernel_N_weight:pd.DataFrame)->list:
    """Square root of gradient between 2 pixels, in selected orientantion, for entire image.
    Equation (3) of original paper. After the convolution, the result image has a pad which must be
    ignored to fearther computations.
    For all bands in an fpaths, for one kernel and corresponding weight. All kernels are flipped
    before convolution.
    Args:
        fpaths (list): List of fullpaths for bands b03, b04, b08, b11, b12.
        kernel_N_weight (pd.DataFrame): Row of iterable dataframe with 2 columns with kernels
            and their weights. 
    Returns:
        list: List containing 2D arrays, one for each kernel. Result for one week (or date),
        for one pixel (orientation of convolution).
    """
    res = []
    for im_path in fpaths:
        with rio.open(im_path) as src:
            b = src.read(1)

            # TODO: mask with scl-cloud-mask
            grad = signal.convolve2d(
                b,
                kernel_N_weight['kernels'],
                mode='same',
                boundary='fill',
                fillvalue=0)
            pow_grad = np.power(grad, 2)
            res.append(pow_grad)
    dweek_onePixel = np.sqrt(sum(res))
    return dweek_onePixel


def equation_4(ndvi:np.array, kernel_N_weight:pd.DataFrame)->list:
    """Convolution only for NDVI image.
    Args:
        ndvi (np.array): Image as 2D array.
        kernel_N_weight (pd.DataFrame): Row of iterable dataframe with 2 columns with kernels
            and their weights. 
    Returns:
        list: List containg 2D arrays, one for each kernel.
    """
    abs_grad = np.absolute(signal.convolve2d(ndvi,
                                            kernel_N_weight['kernels'],
                                            mode='same',
                                            boundary='fill',
                                            fillvalue=0))
    return abs_grad


def equation_5(ndvi:np.array, dweeks:list, dndvi:list, kernels_N_weights:pd.DataFrame)->np.array:
    """Compute edge estimation for one date.
    Args:
        ndvi (np.array): NDVI image as 2D array.
        dweeks (list): Result of equation_3. List containing 2D arrays, one for each kernel.
        dndvi (list): Result of equation_4. List containg 2D arrays, one for each kernel.
        kernels_N_weights (pd.DataFrame): Row of iterable dataframe with 2 columns with kernels
            and their weights.
    Returns:
        np.array: Edge estimation image as 2D array.
    """
    # Compute every convolutioned image with it's corresponding weight.
    bands = []
    indices = []
    for i in range(0, len(kernels_N_weights)):
        temp01 = dweeks[i] * kernels_N_weights['weights'][i]
        temp02 = dndvi[i] * kernels_N_weights['weights'][i]
        bands.append(temp01)
        indices.append(temp02)
    # Sum of weights.
    sw = sum(kernels_N_weights['weights'])
    # Return their multiply, with ndvi as the most important contributor.
    return (ndvi**2) * (sum(bands)/sw) * (sum(indices)/sw)


def wkernels()->pd.DataFrame:
    """Prepare kernels.
    Returns:
        pd.DataFrame: Kernels as dataframe
    """
    # Kernels to compute spectral diference.
    _conv_kern_p1 = np.array([[-1,  0,  0], [ 0, 1,  0], [ 0,  0,  0]]) # ul
    _conv_kern_p2 = np.array([[ 0, -1,  0], [ 0, 1,  0], [ 0,  0,  0]]) # uc
    _conv_kern_p3 = np.array([[ 0,  0, -1], [ 0, 1,  0], [ 0,  0,  0]]) # ur
    _conv_kern_p4 = np.array([[ 0,  0,  0], [ 0, 1, -1], [ 0,  0,  0]]) # cr
    _conv_kern_p5 = np.array([[ 0,  0,  0], [ 0, 1,  0], [ 0,  0, -1]]) # br
    _conv_kern_p6 = np.array([[ 0,  0,  0], [ 0, 1,  0], [ 0, -1,  0]]) # cb
    _conv_kern_p7 = np.array([[ 0,  0,  0], [ 0, 1,  0], [-1,  0,  0]]) # bl
    _conv_kern_p8 = np.array([[ 0,  0,  0], [-1, 1,  0], [ 0,  0,  0]]) # cl
    kernels = [_conv_kern_p1, _conv_kern_p2, _conv_kern_p3, _conv_kern_p4,
                _conv_kern_p5, _conv_kern_p6, _conv_kern_p7, _conv_kern_p8]
    # Weight of each direction.
    weights = [math.sqrt(2)/2, 1, math.sqrt(2)/2, 1, math.sqrt(2)/2, 1, math.sqrt(2)/2, 1]
    # kernels and their weights
    _list = [(kernels[i], weights[i]) for i in range(0, len(weights))]
    return pd.DataFrame(_list, columns=['kernels', 'weights'])


def cube_by_paths(listOfPaths:list, outfname:str=None, **kwargs)->list:
    """Concatenate images as cube.
    Args:
        listOfPaths (list): List containg fullpaths of images to concatenate on
            time-axis.
        outfname (str, optional): Absolute filename for the resulted geotif file.
            Defaults to None. When given, the 3D cube array will be saved.
    Returns:
        list: Cube as 3D np.array, cube's metadata as dict, list of strings containing
            bandnames used to produce the cube.
    """
    # read random image's metadata
    with rio.open(listOfPaths[0], 'r') as src:
        meta = src.meta

    # Preallocate a zero array with appropriate dimensions
    temp = np.zeros((1, meta['height'], meta['width']))

    # Concatenate
    band_names = []
    for bandpath in listOfPaths:
        with rio.open(bandpath, 'r') as src:
            arr = src.read()
            descr = src.name
            band_names.append(os.path.basename(descr))
        cbarr = np.concatenate([temp, arr])
        temp = cbarr

    # Update metadata. Reduce one because of temp array
    meta.update(count=cbarr.shape[0]-1)
    cbarr = cbarr.astype(meta['dtype'])

    if outfname is not None:
        if os.path.isfile(outfname) and os.stat(outfname).st_size != 0:
            print(f"File {outfname} exists.")
        else:
            assert os.path.isabs(outfname)
            with rio.open(outfname, 'w', **meta) as dst:
                for id, layer in enumerate(listOfPaths, start=1):
                    with rio.open(layer) as src:
                        dst.write_band(id, src.read(1))
                        dst.set_band_description(id, band_names[id-1])

    return cbarr[1:, :, :], meta, band_names



def cbdf2cbarr(cbdf:pd.DataFrame, cbmeta:dict)->np.ndarray:
    """Convert dataframe of cube to corresponding 3D cube array.
    Args:
        cbdf (pd.DataFrame): Indexed as (rows:bands, row wise read, columns:individual pixels)
        cbmeta (dict): Containing all cube metadata, as returned by rasterio.
    Returns:
        np.ndarray: Indexed as 3D tensor (count:bands, height:rows, width:columns)
    """
    # Convert dataframe to array
    temp = cbdf.to_numpy(dtype=cbmeta['dtype'])
    # Create axis, from 2D to 3D
    temp = temp[np.newaxis, :, np.newaxis]
    # Reshape array
    cbarr = np.reshape(temp, (cbmeta['count'], cbmeta['height'],  cbmeta['width']))
    return cbarr


def cbarr2cbdf(cbarr:np.ndarray, cbmeta:dict)->pd.DataFrame:
    """Convert 3D cube array to corresponding dataframe of the cube.
    Args:
        cbarr (np.ndarray): Indexed as tensor (count:bands, height:rows, width:columns)
        cbmeta (dict): Containing all cube metadata, as returned by rasterio.
    Returns:
        pd.DataFrame: Indexed as (rows:bands, row wise read, columns:individual pixels)
    """
    # Drop array to 2D.
    temp = np.reshape(cbarr, (cbmeta['count'], cbmeta['height'] *  cbmeta['width']))
    # Convert array to dataframe.
    cbdf = pd.DataFrame(
        temp, columns=["pix_"+str(i) for i in range(0, cbmeta['height'] *  cbmeta['width'])])
    return cbdf


def filter_corine(shppath:str)->gpd.GeoDataFrame:
    corine_data = gpd.read_file(shppath)

    keep = {
        '211':'Non-irrigated arable land',
        '212':'Permanently irrigated land',
        '213':'Rice fields',
        '221':'Vineyards',
        '222':'Fruit trees and berry plantations',
        '223':'Olive groves',
        '231':'Pastures',
        '241':'Annual crops associated with permanent crops',
        '242':'Complex cultivation patterns',
        '243':'Land principally occupied by agriculture',
        '244':'Agro-forestry areas',
        # '311':'Broad-leaved forest',
        # '312':'Coniferous forest',
        # '313':'Mixed forest',
        # '321':'Natural grasslands',
        # '322':'Moors and heathland',
        # '323':'Sclerophyllous vegetation',
        # '324':'Transitional woodland-shrub',
        # '331':'Beaches',
        # '332':'Bare rocks',
        # '333':'Sparsely vegetated areas',
        # '334':'Burnt areas',
        # '335':'Glaciers and perpetual snow',
        }

    corine_data['Code_18'] = corine_data['Code_18'].astype(str)
    corine_data=corine_data[corine_data['Code_18'].isin(list(keep.keys()))]
    return corine_data


def _wkt2esri(wkt:str)->str:
    """Converts WKT geometries to arcGIS geometry strings.
    Args:
        wkt (str): WKT geometry string
    Returns:
        str: ESRI arcGIS polygon geometry string
    """
    geom = shapely.wkt.loads(wkt)
    rings = None
    # Testing for polygon type
    if geom.geom_type == 'MultiPolygon':
        rings = []
        for pg in geom.geoms:
            rings += [list(pg.exterior.coords)] + [list(interior.coords) for interior in pg.interiors]    
    elif geom.geom_type == 'Polygon':
        rings = [list(geom.exterior.coords)] + [list(interior.coords) for interior in geom.interiors]
    else:
        print("Shape is not a polygon")
        return None
            
    # Convert to esri geometry json    
    esri = json.dumps({'rings': rings})

    return esri

def corine(aoi:str, to_file:bool = False, fname:str = "corine_2018.shp")->tuple:
    """Downloads Corine Land Cover 2018 data from Copernicus REST API.
    Args:
        aoi (str): Path to file with the region of interest
        to_file (bool, optional): Save result to file. Defaults to False
        fname (str, optional): Path and name of the created file. Defaults to "corine_2018.shp"
    Returns:
        tuple: Corine Land Cover 2018 data as GeoDataFrame and the path to saved file
    """
    HTTP_OK = 200

    geoms = gpd.read_file(aoi).dissolve()
    polygons = list(geoms.geometry)
    wkt = f"{polygons[0]}"
    esri = _wkt2esri(wkt)
    # Build URL for retrieving data
    server = "https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer/0/query?"
    payload = {
        "geometry": esri, 
        "f": "GeoJSON",
        "inSR": geoms.crs.to_epsg(),
        "geometryType": "esriGeometryPolygon",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": True
        }
    print ("Starting retrieval...")
    request = requests.get(server, params = payload)
    # Check if server didn't respond to HTTP code = 200
    if request.status_code != HTTP_OK:
        raise exceptions.HTTPError("Failed retrieving POWER data, server returned HTTP code: {} on following URL {}.".format(request.status_code, request.url))
    # In other case is successful
    print ("Successfully retrieved data!")
    json_data = request.json()
    data = gpd.GeoDataFrame.from_features(json_data)
    if to_file:
        data.to_file(fname)
    
    return data, fname

def worldcover(aoi:str, savepath:str)->gpd.GeoDataFrame:
    """Downloads landcover maps from worldcover project

    Args:
        aoi (str): Path to AOI file to dowload data
        savepath (str): Path to store data

    Returns:
        gpd.GeoDataFrame: Downloaded tiles 
    """
    # works for one polygon/multipolygon
    aoi = gpd.read_file(aoi).iloc[0].explode().geometry
    # load worldcover grid
    s3_url_prefix = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    url = f'{s3_url_prefix}/v100/2020/esa_worldcover_2020_grid.geojson'
    grid = gpd.read_file(url)

    # get grid tiles intersecting AOI
    tiles = grid[grid.intersects(aoi)]
    
    # works only if AOI covers one tile
    for tile in tqdm(tiles.ll_tile):
        url = f"{s3_url_prefix}/v100/2020/map/ESA_WorldCover_10m_2020_v100_{tile}_Map.tif"
        r = requests.get(url, allow_redirects=True)
        out_fn = f"ESA_WorldCover_10m_2020_v100_{tile}_Map.tif"
        with open(os.path.join(savepath, out_fn), 'wb') as f:
            f.write(r.content)    
    
    return tiles

def reproj_match(image:str, base:str, outfile:str, resampling:rasterio.warp.Resampling = Resampling.nearest) -> None:
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