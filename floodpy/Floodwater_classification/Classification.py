#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import numpy as np
import xarray as xr
import os

from floodpy.Floodwater_classification.BC_masking import Calculation_bimodality_mask
from floodpy.Floodwater_classification.Region_growing import Region_Growing
from floodpy.Floodwater_classification.Thresholding_methods import threshold_Otsu
from floodpy.Floodwater_classification.Adaptive_thresholding import Adapt_local_thresholding
from floodpy.Floodwater_classification.Morphological_filtering import morphological_postprocessing

def Calc_flood_map(Floodpy_app):

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
                      'num_cores' : Floodpy_app.CPU,
                      'min_map_unit_m2' : Floodpy_app.min_map_area,
                      'pixel_m2' : Floodpy_app.pixel_m2}

    if not os.path.exists(Floodpy_app.Flood_map_dataset_filename):
        #%%
        ## Read Data and calculate bimodality mask (Step-1)
        ###########################################################################
        print("Calculating Bi/multi modality mask...")

        t_scores = xr.open_dataset(Floodpy_app.t_score_filename, decode_coords='all')[Floodpy_app.polar_comb]
        Flood_map_dataset = t_scores.rename('t_scores').to_dataset()

        multimodality_mask=Calculation_bimodality_mask(t_scores.values) 
        Flood_map_dataset = Flood_map_dataset.assign(multimodality_mask=(['y','x'],multimodality_mask))
        
        #%%
        ## Create initial flood map using global thresholding (Step-2)
        ###########################################################################
        print("Calculating global flood mask using global threshold...")

        t_scores_flatten = t_scores.values[multimodality_mask].flatten()
        vmin = np.quantile(t_scores_flatten, 0.01)
        vmax = np.quantile(t_scores_flatten, 0.99)

        t_scores_flatten[t_scores_flatten<vmin]=np.nan
        t_scores_flatten[t_scores_flatten>vmax]=np.nan
        t_scores_flatten = t_scores_flatten[~np.isnan(t_scores_flatten)]

        glob_thresh = threshold_Otsu(t_scores_flatten)

        # binary mask (1: water surfaces, 0: non water surfaces)
        Flood_global_binary = t_scores < glob_thresh 

        Flood_map_dataset['Flood_global_binary'] = Flood_global_binary  
        
        #%%
        ## Discard high slope regions (optional)
        ###########################################################################
        print("Discard high slope regions ...")

        slope_mask = xr.open_dataset(Floodpy_app.DEM_slope_filename)['slope_mask']
        Flood_map_dataset['slope_mask'] = slope_mask
        Flood_map_dataset['Flood_global_binary_masked'] = Flood_map_dataset['Flood_global_binary'] * Flood_map_dataset['slope_mask']

        #%%
        ## Local adaptive thresholding (Step-3) 
        ## [corrects commission/omission errors]
        ###########################################################################  
        print("Performing local adaptive thresholding ...")

        raw_water_data = Flood_map_dataset['t_scores']*Flood_map_dataset['Flood_global_binary_masked']

        water_data = np.clip(raw_water_data.values,
                            np.nanquantile(raw_water_data, 0.01),
                            np.nanquantile(raw_water_data, 0.99))

        water_mean_float = np.nanmean(water_data)
        std_water_float = np.nanstd(water_data)

        # Calculate local probability flood map
        probability_map=Adapt_local_thresholding(t_score_data = Flood_map_dataset['t_scores'].values,
                                                Flood_global_mask = Flood_map_dataset['Flood_global_binary'].values,
                                                water_mean_float = water_mean_float,
                                                std_water_float = std_water_float,
                                                processing_parms = processing_parms)
                                                                    
        # Drop low probability flood pixels (<0.2)
        Flood_local_map=probability_map>processing_parms['probability_thres']

        Flood_map_dataset = Flood_map_dataset.assign(Flood_local_map=(['y','x'],Flood_local_map))
        
        #%%
        ## Region growing (Step-4) 
        ## [corrects omission errors]
        ###########################################################################
        print("Running Region Growing operation...")

        Flood_local_map_RG = Region_Growing(t_score_dataset = Flood_map_dataset['t_scores'].values,
                                            Flood_map = Flood_map_dataset['Flood_local_map'].values,
                                            RG_thres = processing_parms['RG_thres'],
                                            search_window_size = processing_parms['search_RG_window_size'])
        
        Flood_map_dataset = Flood_map_dataset.assign(Flood_local_map_RG=(['y','x'],Flood_local_map_RG))
        
        #%%
        ## Postprocessing processing for refinement (Step-5) 
        ##########################################################################
        print("Running Morphological filtering operation...")

        # discard high slope pixels
        Flood_local_map_RG=Flood_map_dataset['Flood_local_map_RG'] * Flood_map_dataset['slope_mask']

        # morphological filtering of local flood mask
        Flood_local_map_RG_morph=morphological_postprocessing(Flood_local_map_RG.values,
                                                                Floodpy_app.min_map_area,
                                                                Floodpy_app.pixel_m2)

        Flood_map_dataset = Flood_map_dataset.assign(Flood_local_map_RG_morph=(['y','x'],Flood_local_map_RG_morph))

        #%%
        ## Writing final Flood map to disk
        ##########################################################################
        print("Saving flood map dataset to disk ...")
        Flood_map_dataset.to_netcdf(Floodpy_app.Flood_map_dataset_filename)

        print('Floodwater map can be found at {}'.format(Floodpy_app.Flood_map_dataset_filename))

