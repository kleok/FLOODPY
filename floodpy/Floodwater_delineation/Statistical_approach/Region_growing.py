#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

def RG_window(window_data: np.array, window_current_result: np.array, RG_thres: float) -> np.array:
    """Regions growing in a single block/window

    Args:
        window_data (np.array): Input values of window to be processed
        window_current_result (np.array): Boolean mask of the window. True represent floodwater.
        RG_thres (np.float): Positive threshold value.

    Returns:
        np.array: Boolean mask of window (True represents floodwater) after region growing operation.
    """

    # find the mean value of t-scores based on current result
    mean_value = np.nanmean(window_data[window_current_result])

    # calculate differences 
    diffs=window_data-mean_value

    # select only negative differences
    negative_diffs=diffs<0

    # return mask that corresponds to negative differences
    RG_mask=np.abs(negative_diffs)>RG_thres

    # combine masks
    RG_result=np.logical_or(window_current_result,RG_mask)

    return RG_result
  
def adapt_RG_factor(window_data: np.array, water_mean_float: float,std_water_float: float) -> float:
    """Calculates the adapting factor that will be used to tune RG threshold value.
    Adapting factor takes values from 0 to 1. 
    For low factor values we have lower threshold (more strict).
    For high factor values we have higher threshold (less strict).

    Args:
        window_data (np.array): Input values of window to be processed
        water_mean_float (float): The global mean of floodwater distribution
        std_water_float (float): The global standard deviation of floodwater distribution

    Returns:
        float: adapting factor (ranges from 0 to 1)
    """

    low_water_value=water_mean_float
    high_water_value=water_mean_float+2*std_water_float
    
    values=window_data[~np.isnan(window_data)]
    values_median=np.median(values)

    if values_median>=high_water_value:
        factor=0.0
    elif values_median<low_water_value:
        factor=1.0
    else:
        factor=np.abs((values_median-high_water_value))/np.abs((low_water_value-high_water_value))
    
    return factor   

def Region_Growing(t_score_dataset: np.array,
                   Flood_map: np.array,
                   RG_thres: float,
                   max_num_iter: int = 1000,
                   search_window_size: int = 1) -> np.array:
    """
    Adaptive region growing functionality

    Args:
        t_score_dataset (np.array): 2D array with t-score values
        Flood_map (np.array): Boolean 2D array (initial floodwater mask)
        RG_thres (float): Nominal region growing threshold value
        max_num_iter (int, optional): Maximum number of iterations of the iterative region growing process. Defaults to 1000.
        search_window_size (int, optional): Size of window that will be used for region growing. Defaults to 1.

    Returns:
        np.array: Boolean mask (True represents floodwater) after region growing operation.
    """

    # get updated information of floodwater based on local adaptive thresholding
    floodwater_pixels=t_score_dataset[Flood_map]
    # discard pixel with nan values
    floodwater_pixels = floodwater_pixels[~np.isnan(floodwater_pixels)]
    # recalculating mean and standard deviation for floodwater population
    water_mean_float=np.mean(floodwater_pixels)
    std_water_float=np.std(floodwater_pixels)

    # Assert that the shapes of image and seed mask agree
    assert (t_score_dataset.shape==Flood_map.shape)
    seeds=Flood_map.astype(np.bool_)
    rows=t_score_dataset.shape[0]
    columns=t_score_dataset.shape[1]
    RG_result=np.copy(seeds)
    num_iter = 1
    
    while (num_iter<max_num_iter and np.sum(seeds)!=0) :

        seeds_indices=np.nonzero(seeds)
        RG_result_updated=np.copy(RG_result)
        
        for seed_index in range(len(seeds_indices[0])):  
                
            row = seeds_indices[0][seed_index]
            col = seeds_indices[1][seed_index]
            
            row_min = row-search_window_size
            if row_min<0: row_min=0
            row_max = row+search_window_size+1
            if row_max>rows: row_min=rows
            col_min = col-search_window_size
            if col_min<0: col_min=0
            col_max = col+search_window_size+1
            if col_max>columns: col_max=columns
                     
            window_data=t_score_dataset[row_min:row_max,col_min:col_max]
            window_current_result=RG_result[row_min:row_max,col_min:col_max]
            
            if window_current_result.shape[0]>1 and window_current_result.shape[1]>1: # checks if window is not in the corner of the image
                if ~np.all(window_current_result==True):
                    adapt_factor = adapt_RG_factor(window_data, water_mean_float, std_water_float )
                    RG_thres_modified = adapt_factor * RG_thres
                    window_updated_result=RG_window(window_data,window_current_result,RG_thres_modified) 
                    RG_result_updated[row_min:row_max,col_min:col_max]=window_updated_result 
                
        # update RG_result, seeds and iteration counter      
        seeds=np.logical_and(~RG_result,RG_result_updated)
        num_iter+=1
        RG_result=RG_result_updated
                      
    return RG_result_updated