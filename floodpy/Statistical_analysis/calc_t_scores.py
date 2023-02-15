#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import h5py
import os, glob
import pandas as pd
import numpy as np
from osgeo import gdal
import itertools

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()

def image_combinations(wet_image_date,dry_images_dates):
    '''
    Functionality for creating combinations between "dry" and "wet" image dates.
    '''
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
    '''
    Functionality that saves information numpy array to geotiff given a reference
    geotiff.

    Args:
        nparray (np.array): information we want to save to geotiff.
        reference_gdal_dataset (string): path of the reference geotiff file.
        target_gdal_dataset (string): path of the output geotiff file.
    '''
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

def Calc_t_scores(Results_dir,
                  S1_dir,
                  Preprocessing_dir,
                  band='VV_VH_db'):
    '''
    T-score change image functionality
    '''
    # get tiff file
    master_tiff_wgs84=glob.glob(os.path.join(Preprocessing_dir,'*_wgs84.tif'))[0]
 
    # read sar stack
    SAR_stack_file=os.path.join(Preprocessing_dir,'Stack/SAR_Stack.h5')
    SAR_stack=h5py.File(SAR_stack_file,'r')
    
    # get baseline_dates
    images=os.path.join(S1_dir,'baseline_images.csv')
    images_df=pd.read_csv(images)
    baseline_images=images_df[images_df['baseline']==True]
    baseline_dates=[os.path.basename(image)[17:32] for image in baseline_images['S1_GRD'].tolist()]

    # get flood_date
    flood_S1_image_filename = os.path.join(S1_dir,'flood_S1_filename.csv')
    assert os.path.exists(flood_S1_image_filename)
    flood_S1_image = pd.read_csv(flood_S1_image_filename, index_col=0).loc['title'].values[0]
    flood_date = flood_S1_image[17:32]

    
    # calculate mean and std of baseline images
    #SAR_stack_datetimes = [element.decode("utf-8") for element in SAR_stack['Datetime_SAR'][:]]
    SAR_stack_datetimes = [element.decode('utf-8') for element in SAR_stack['Datetime_SAR'][:]]
    
    baseline_common_dates= set(baseline_dates).intersection(SAR_stack_datetimes)
    indices_A = sorted([SAR_stack_datetimes.index(x) for x in baseline_common_dates])
    weights=np.cos(np.radians(SAR_stack["localIncidenceAngle"][:]))
    mean_baseline=np.mean(SAR_stack[band][indices_A,:,:], axis=0)*weights
    std_baseline=np.std(SAR_stack[band][indices_A,:,:], axis=0)*weights
    number_images_baseline=len(indices_A) # degrees of freedom
    
    error_message = ("Houston we've got a problem. We encountered a problem "
                     "in the coregistration procedure due to a small number "
                     "of images before flood. Please increase the " 
                     "value of before_flood_days")
        
    assert number_images_baseline > 2, error_message

    # get value of flood image
    flood_index=SAR_stack_datetimes.index(flood_date)
    flood_value=SAR_stack[band][flood_index,:,:]*weights
    
    # t_score = (flood_value - mean(baseline)/(std(baseline)/sqrt(number_images_baseline))
    t_scores = np.divide(flood_value-mean_baseline,std_baseline/np.sqrt(number_images_baseline))
    
    export_filename=os.path.join(Results_dir,'t_scores_{}.tif'.format(band))

    nparray_to_tiff(t_scores,
                    master_tiff_wgs84,
                    export_filename)
    
    print("T-score changes due to flood can be found at {}".format(export_filename))
    
    return t_scores
