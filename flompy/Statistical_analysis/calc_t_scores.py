#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate t-scores 

Copyright (C) 2022 by K.Karamvasis

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

import h5py
import os, glob
import pandas as pd
import numpy as np
from osgeo import gdal
import itertools
import scipy.stats as stats

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()

def image_combinations(wet_image_date,dry_images_dates):
    wet_combinations=[]
    for pair in itertools.product(wet_image_date,dry_images_dates):
        wet_combinations.append(pair)
    
    dry_combinations=[]
    dry_images_dates_desc=np.sort(dry_images_dates)[::-1]
    
    for dry_master in dry_images_dates_desc:
        dry_images_dates.remove(dry_master)
        for pair in itertools.product([dry_master],dry_images_dates):
            dry_combinations.append(pair)
    return wet_combinations, dry_combinations

def nparray_to_tiff(nparray, reference_gdal_dataset, target_gdal_dataset):
    
    # open the reference gdal layer and get its relevant properties
    raster_ds = gdal.Open(reference_gdal_dataset, gdal.GA_ReadOnly)   
    xSize = raster_ds.RasterXSize
    ySize = raster_ds.RasterYSize
    geotransform = raster_ds.GetGeoTransform()
    projection = raster_ds.GetProjection()
    
    # create the target layer 1 (band)
    driver = gdal.GetDriverByName('GTIFF')
    target_ds = driver.Create(target_gdal_dataset, xSize, ySize, bands = 1, eType = gdal.GDT_Float32)
    target_ds.SetGeoTransform(geotransform)
    target_ds.SetProjection(projection)
    target_ds.GetRasterBand(1).WriteArray(nparray)  
    
    target_ds = None

def Calc_t_scores(projectfolder, 
                  Results_dir,
                  S1_GRD_dir,
                  Preprocessing_dir,
                  band='VV_VH_db'):
    '''

    Parameters
    ----------
    SAR_stack_file : (str)
        full path of preprocessed hdf5 SAR stack .
    master_tiff_wgs84 : full path of gdal tiff file (str)
        Used as reference for generation of tiff products
    flood_date : list of one element
        DESCRIPTION.
    baseline_dates : list of multiple elements
        DESCRIPTION.
    band : str
        'VV_VH_db' # other choise can be VH_db or VV_db
    exportDir : full path of dir to write t_score(str)
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    # get tiff file
    master_tiff_wgs84=glob.glob(os.path.join(Preprocessing_dir,'*_wgs84.tif'))[0]
 
    # read sar stack
    SAR_stack_file=os.path.join(Preprocessing_dir,'Stack/SAR_Stack.h5')
    SAR_stack=h5py.File(SAR_stack_file,'r')
    
    # get baseline_dates
    images=os.path.join(S1_GRD_dir,'baseline_images.csv')
    images_df=pd.read_csv(images)
    baseline_images=images_df[images_df['baseline']==True]
    baseline_dates=[os.path.basename(image)[17:32] for image in baseline_images['S1_GRD'].tolist()]

    # get flood_date
    flood_S1_image_filename = os.path.join(S1_GRD_dir,'flood_S1_filename.csv')
    assert os.path.exists(flood_S1_image_filename)
    flood_S1_image = pd.read_csv(flood_S1_image_filename, index_col=0).iloc[0][0]
    flood_date = flood_S1_image[17:32]

    
    # calculate mean and std of baseline images
    SAR_stack_datetimes = [element.decode("utf-8") for element in SAR_stack['Datetime_SAR'][:]]

    baseline_common_dates= set(baseline_dates).intersection(SAR_stack_datetimes)
    indices_A = sorted([SAR_stack_datetimes.index(x) for x in baseline_common_dates])
    weights=np.cos(np.radians(SAR_stack["localIncidenceAngle"][:]))
    mean_baseline=np.mean(SAR_stack[band][indices_A,:,:], axis=0)*weights
    std_baseline=np.std(SAR_stack[band][indices_A,:,:], axis=0)*weights
    number_images_baseline=len(indices_A) # degrees of freedom
    df=number_images_baseline

    # get value of flood image
    flood_index=SAR_stack_datetimes.index(flood_date)
    flood_value=SAR_stack[band][flood_index,:,:]*weights
    
    # t_score = (flood_value - mean(baseline)/(std(baseline)/sqrt(number_images_baseline))
    t_scores = np.divide(flood_value-mean_baseline,std_baseline/np.sqrt(df))
    
    export_filename=os.path.join(Results_dir,'t_scores_{}.tif'.format(band))

    nparray_to_tiff(t_scores,
                    master_tiff_wgs84,
                    export_filename)
    
    print("T-score changes due to flood can be found at {}".format(export_filename))
    
    return 0


def Calc_changes_stat(t_scores, df):
   # calculate the critical 
    # The critical value can be calculated using the percent point function 
    # (PPF) for a given significance level, such as 0.05 (95% confidence).
    alpha = 0.05
    cv = stats.t.ppf(1.0 - alpha, df)
    
    # interpret via critical value
    # Reject the null hypothesis that no change has happened
    change_map_cv=(np.abs(t_scores)>cv).astype(np.int) # 1 is change 0 is no change
    

    # calculate the p-value map
    # The p-value can be calculated using the cumulative distribution function 
    # on the t-distribution, again in SciPy.
    p = (1 - stats.t.cdf(abs(t_scores), df)) * 2
    
    # Here, we assume a two-tailed distribution, where the rejection of the 
    # null hypothesis could be interpreted as the first mean is either 
    # smaller or larger than the second mean.
    
    p=p/2 
    
    change_map_p=(np.abs(t_scores)>p).astype(np.int) # 1 is change 0 is no change
    
    return change_map_cv, change_map_p
