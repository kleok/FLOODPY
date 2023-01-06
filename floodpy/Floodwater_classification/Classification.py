#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from osgeo import gdal
import numpy as np
from scipy.ndimage.filters import maximum_filter as maxf2D
from scipy.ndimage import gaussian_filter

from floodpy.utils.save_raster import nparray_to_tiff
from floodpy.Floodwater_classification.BC_masking import Calculation_bimodality_mask
from floodpy.Floodwater_classification.Region_growing import Region_Growing
from floodpy.Floodwater_classification.Thresholding_methods import threshold_Otsu
from floodpy.Floodwater_classification.Adaptive_thresholding import Adaptive_local_thresholdin_parallel
from floodpy.Floodwater_classification.Morphological_filtering import morphological_postprocessing

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()

def Calc_flood_map(Preprocessing_dir: str,
                Results_dir: str,
                Projectname: str,
                num_cores: int,
                quick_version: bool = True,
                min_map_unit_m2: float = 1000,
                pixel_m2: float = 100) -> Tuple[np.array, np.array]:

    """
    Calculates flood map based on the methodology described at (Karamvasis & Karathanassi 2021).
    The steps of the particular functionality are:
    - Load Data and calculate bimodality mask
    - Create initial flood map using global thresholding
    - Discard high slope regions in order to work on less pixels
    - Local adaptive thresholding
    - Region growing
    - Morphological filtering
    - Write results to disk

    Args:
        Preprocessing_dir (str): _description_
        Results_dir (str): _description_
        Projectname (str): Name  of  the project
        num_cores (int): number of CPU cores to be employed
        quick_version (bool, optional): _description_. Defaults to True.
        min_map_unit_m2 (float, optional): The area (in m2) of the minimum mapping unit. Defaults to 1000.
        pixel_m2 (float, optional): The area (in m2) of pixel of the initial flood map. Defaults to 100.

    Returns:
        Tuple[np.array, np.array]: _description_

    ..References:
        Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943

    """

    processing_parms={'thresholding_method':'Otsu',
                      'p_value': 0.05,
                      'window_half_size_min':15,
                      'window_half_size_max':30,
                      'window_step':5,
                      'bimodality_thres':0.555,
                      'probability_thres_otsu': 0.25,
                      'search_RG_window_size':1,
                      'RG_weight':0.5,
                      'flood_percentage_threshold':10}

    ##########################################################################
    ## Read Data and calculate bimodality mask (Step-1)
    ##########################################################################
    t_score_filename = os.path.join(Results_dir,'t_scores_VV_VH_db.tif')
    assert os.path.exists(t_score_filename)
    t_score_dataset=gdal.Open(t_score_filename).ReadAsArray()
    multimodality_mask=Calculation_bimodality_mask(t_score_dataset) 
    
    ##########################################################################
    ## Create initial flood map using global thresholding (Step-2)
    ##########################################################################
    t_scores_flatten = t_score_dataset[multimodality_mask].flatten()
    vmin = np.quantile(t_scores_flatten, 0.01)
    vmax = np.quantile(t_scores_flatten, 0.99)

    t_scores_flatten[t_scores_flatten<vmin]=np.nan
    t_scores_flatten[t_scores_flatten>vmax]=np.nan
    t_scores_flatten = t_scores_flatten[~np.isnan(t_scores_flatten)]

    glob_thresh = threshold_Otsu(t_scores_flatten)

    # binary mask (1: water surfaces, 0: non water surfaces)
    Flood_global_binary = t_score_dataset < glob_thresh   
    
    ##########################################################################
    ##########################################################################
    ## discard high slope regions in order to work on less pixels
    ##########################################################################
    slope_filename = os.path.join(Preprocessing_dir,'dem_slope_wgs84.tif')
    slope=gdal.Open(slope_filename).ReadAsArray()
    
    # Store shapes of inputs
    N = 7
    M = 7
    P,Q = slope.shape

    # Use 2D max filter and slice out elements not affected by boundary conditions
    maxs = maxf2D(slope, size=(M,N))
    
    slope_max_blur = gaussian_filter(maxs, sigma=7)
    slope_mask=slope_max_blur<12
    Flood_global_binary=Flood_global_binary*slope_mask
    ##########################################################################
    ## Local adaptive thresholding (Step-3) [corrects commission/omission errors] (Step-3)
    ## Create mean and standard deviation of floodwater 
    ##########################################################################    
    
    water_mean_float = np.mean(t_score_dataset[Flood_global_binary])
    std_water_float = np.std(t_score_dataset[Flood_global_binary])

    ################################################################################
    
    ## For each pixel that was identified as flood pixel select a window and do the following
    
    ### 1. if more than 80% of the pixels in the select window were already identified as flood do nothing
    
    ### 2. if less that 80% of the pixels in the select window were already identified as flood do nothing
    ###   and window has binomial distribution then recalculate threshold and use the new mask as flood mask

    ### 3. else increase the window size and go to step 1
    
    # minimum_mapping_unit_area_pixels=min_map_unit_m2/10
    # # the feature that should cover at least 20% of the considered window area
    # window_bbox_size=np.sqrt(minimum_mapping_unit_area_pixels/0.2)
    # window_half_size=int(np.floor(window_bbox_size/2))
    
    if not quick_version:
    
        probability_map_otsu=Adaptive_local_thresholdin_parallel(t_score_dataset_temp = t_score_dataset,
                                                                Flood_global_binary_temp = Flood_global_binary,
                                                                water_mean_float = water_mean_float,
                                                                std_water_float = std_water_float,
                                                                thresholding_method ='Otsu',
                                                                p_value = processing_parms['p_value'],
                                                                window_half_size_min = processing_parms['window_half_size_min'],
                                                                window_half_size_max = processing_parms['window_half_size_max'],
                                                                window_step = processing_parms['window_step'],
                                                                num_cores = num_cores,
                                                                bimodality_thres = processing_parms['bimodality_thres'],
                                                                flood_percentage_threshold = processing_parms['flood_percentage_threshold'])    
        
        
        # Keep only high probability flood pixels (>0.6)
        Flood_local_map=probability_map_otsu>processing_parms['probability_thres_otsu']
    
    ##########################################################################
    ## Region growing (Step-4) [corrects omission errors]
    ##########################################################################
    print("Running Region Growing operation...")
    Flood_global_map_RG = Region_Growing(t_score_dataset = t_score_dataset,
                                        Flood_map = Flood_global_binary,
                                        RG_thres = processing_parms['RG_weight'],
                                        search_window_size = processing_parms['search_RG_window_size'])
    
    ##########################################################################
    ## Postprocessing processing for refinement (Step-5) 
    ##########################################################################
    print("Running Morphological filtering operation...")

    # discard high slope pixels
    Flood_global_map_RG=Flood_global_map_RG*slope_mask

    # morphological filtering of local flood mask
    Flood_global_map_RG_ref=morphological_postprocessing(Flood_global_map_RG, min_map_unit_m2, pixel_m2)

    ##########################################################################
    ## Write data to disk
    ##########################################################################

    output_filename = os.path.join(Results_dir,'Flood_map_{}.tif'.format(Projectname))
    print('Floodwater map can be found at {}'.format(output_filename))

    nparray_to_tiff(multimodality_mask,
                    t_score_filename,
                    output_filename.split('.')[0]+'_multimodality_mask.tif')
    
    # saving final flood map to tiff file
    nparray_to_tiff(Flood_global_map_RG_ref,
                    t_score_filename,
                    output_filename)    
    
    if not quick_version:
        # saving final flood map to tiff file
        nparray_to_tiff(Flood_local_map_RG_ref,
                        t_score_filename,
                        output_filename.split('.')[0]+'_local.tif')
 
    return multimodality_mask, Flood_local_map_RG_ref
