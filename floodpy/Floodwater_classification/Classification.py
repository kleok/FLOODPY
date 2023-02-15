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
from floodpy.Floodwater_classification.Adaptive_thresholding import Adapt_local_thresholding
from floodpy.Floodwater_classification.Morphological_filtering import morphological_postprocessing

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()

def Calc_flood_map(Preprocessing_dir: str,
                Results_dir: str,
                Projectname: str,
                num_cores: int,
                min_map_unit_m2: float = 3000,
                pixel_m2: float = 100) -> Tuple[dict, np.array, float, np.array, np.array, np.array, np.array]:


    """
    Calculates flood map based on the methodology described at (Karamvasis & Karathanassi 2021).
    The steps of the particular functionality are:
    - Load Data and calculate bimodality mask
    - Create initial flood map using global thresholding
    - Discard high slope regions
    - Local adaptive thresholding
    - Region growing
    - Morphological filtering
    - Write results to disk

    Args:
        Preprocessing_dir (str): _description_
        Results_dir (str): _description_
        Projectname (str): Name  of  the project
        num_cores (int): number of CPU cores to be employed
        min_map_unit_m2 (float, optional): The area (in m2) of the minimum mapping unit. Defaults to 3000.
        pixel_m2 (float, optional): The area (in m2) of pixel of the initial flood map. Defaults to 100.

    Returns:
        Tuple[dict, np.array, float, np.array, np.array, np.array, np.array]: processing_parms,
            multimodality_mask, Flood_global_binary, glob_thresh, Flood_local_map,
            Flood_local_map_RG, Flood_local_map_RG_morph

    ..References:
        Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943

    """

    processing_parms={'thresholding_method' : 'Otsu',
                      'p_value' : 0.05,
                      'window_half_size_min' : 15,
                      'window_half_size_max' : 30,
                      'window_step' : 5,
                      'bimodality_thres' : 0.7,
                      'probability_thres' : 0.25,
                      'search_RG_window_size' : 1,
                      'RG_thres' : 0.5,
                      'flood_percentage_threshold' : 10,
                      'num_cores' : num_cores,
                      'min_map_unit_m2' : min_map_unit_m2,
                      'pixel_m2' : pixel_m2}

    #%%
    ## Read Data and calculate bimodality mask (Step-1)
    ###########################################################################
    print("Calculating Bi/multi modality mask...")

    t_score_filename = os.path.join(Results_dir,'t_scores_VV_VH_db.tif')
    assert os.path.exists(t_score_filename)
    t_score_dataset=gdal.Open(t_score_filename).ReadAsArray()
    multimodality_mask=Calculation_bimodality_mask(t_score_dataset) 
    
    #%%
    ## Create initial flood map using global thresholding (Step-2)
    ###########################################################################
    print("Calculating global flood mask using global threshold...")

    t_scores_flatten = t_score_dataset[multimodality_mask].flatten()
    vmin = np.quantile(t_scores_flatten, 0.01)
    vmax = np.quantile(t_scores_flatten, 0.99)

    t_scores_flatten[t_scores_flatten<vmin]=np.nan
    t_scores_flatten[t_scores_flatten>vmax]=np.nan
    t_scores_flatten = t_scores_flatten[~np.isnan(t_scores_flatten)]

    glob_thresh = threshold_Otsu(t_scores_flatten)

    # binary mask (1: water surfaces, 0: non water surfaces)
    Flood_global_binary = t_score_dataset < glob_thresh   
    
    #%%
    ## Discard high slope regions (optional)
    ###########################################################################
    print("Discard high slope regions ...")

    slope_filename = os.path.join(Preprocessing_dir,'dem_slope_wgs84.tif')
    slope=gdal.Open(slope_filename).ReadAsArray()
    
    # Store shapes of inputs
    N = 7
    M = 7

    # Use 2D max filter and slice out elements not affected by boundary conditions
    maxs = maxf2D(slope, size=(M,N))
    
    slope_max_blur = gaussian_filter(maxs, sigma=7)
    slope_mask=slope_max_blur<12
    Flood_global_binary=Flood_global_binary*slope_mask

    #%%
    ## Local adaptive thresholding (Step-3) 
    ## [corrects commission/omission errors]
    ###########################################################################  
    print("Performing local adaptive thresholding ...")

    # Calculate mean and standard deviation of floodwater 
    raw_water_data = t_score_dataset[Flood_global_binary]
    water_data = np.clip(raw_water_data,
                        np.quantile(raw_water_data, 0.01),
                        np.quantile(raw_water_data, 0.99))

    water_mean_float = np.mean(water_data)
    std_water_float = np.std(water_data)

    # Calculate local probability flood map
    probability_map=Adapt_local_thresholding(t_score_data = t_score_dataset,
                                            Flood_global_mask = Flood_global_binary,
                                            water_mean_float = water_mean_float,
                                            std_water_float = std_water_float,
                                            processing_parms = processing_parms)
                                                              
    # Drop low probability flood pixels (<0.2)
    Flood_local_map=probability_map>processing_parms['probability_thres']
    
    #%%
    ## Region growing (Step-4) 
    ## [corrects omission errors]
    ###########################################################################
    print("Running Region Growing operation...")

    Flood_local_map_RG = Region_Growing(t_score_dataset = t_score_dataset,
                                        Flood_map = Flood_local_map,
                                        RG_thres = processing_parms['RG_thres'],
                                        search_window_size = processing_parms['search_RG_window_size'])
    
    #%%
    ## Postprocessing processing for refinement (Step-5) 
    ##########################################################################
    print("Running Morphological filtering operation...")

    # discard high slope pixels
    Flood_local_map_RG=Flood_local_map_RG*slope_mask

    # morphological filtering of local flood mask
    Flood_local_map_RG_morph=morphological_postprocessing(Flood_local_map_RG,
                                                          min_map_unit_m2,
                                                          pixel_m2)

    #%%
    ## Writing final Flood map to disk
    ##########################################################################
    print("Saving final flood map to disk ...")
    
    output_filename = os.path.join(Results_dir,
                                   'Flood_map_{}.tif'.format(Projectname))
                                   
    print('Floodwater map can be found at {}'.format(output_filename))

    nparray_to_tiff(Flood_local_map_RG_morph,
                    t_score_filename,
                    output_filename)
    
    return processing_parms, multimodality_mask, glob_thresh, Flood_global_binary, Flood_local_map, Flood_local_map_RG, Flood_local_map_RG_morph
