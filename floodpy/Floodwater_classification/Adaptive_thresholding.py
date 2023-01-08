#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import numpy as np
from joblib import Parallel, delayed, wrap_non_picklable_objects
from itertools import product

from floodpy.Floodwater_classification.BC_masking import Bimodality_test
from floodpy.Floodwater_classification.Thresholding_methods import threshold_Kittler, threshold_Otsu
from floodpy.Floodwater_classification.Comparison_tools import Is_similar_non_parametric, Is_darker_than, Is_brighter_than

def sel_borders(row: int,
                col: int,
                rows: int,
                cols: int,
                win_half_size: int) -> Tuple[int, int, int, int]:

    """Calculates the window extent given the pixel location (row, col)
    and size of window (win_half_size). 

    Args:
        row (int): Row of center of window/kernel
        col (int): Col of center of window/kernel
        rows (int): Number of rows
        cols (int): Number of columns
        win_half_size (int): The half size of window

    Returns:
        Tuple[int, int, int, int]: The window extent (row_min, row_max, col_min, col_max)
    """

    row_min = row-win_half_size
    if row_min<0: row_min=0
    row_max = row+win_half_size+1
    if row_max>rows: row_min=rows
    col_min = col-win_half_size
    if col_min<0: col_min=0
    col_max = col+win_half_size+1
    if col_max>cols: col_max=cols 

    return row_min, row_max, col_min, col_max

def calc_grid(Flood_global_mask: np.array,
              min_map_unit_m2: float  = 5000,
              pixel_m2: float = 100) -> list:

    """Calculates the grid points based on minimum mapping unit and
    pixel area size.

    Args:
        Flood_global_mask (np.array): The global flood map
        min_map_unit_m2 (float, optional): Minimum mapping unit area (in m2). Defaults to 5000.
        pixel_m2 (float, optional): Area of the pixel (in m2). Defaults to 100.

    Returns:
        list: List of grid points. Each element of the list is a tuple with row, col of grid point.
    """

    min_map_unit_pixels=min_map_unit_m2/pixel_m2  
    grid_size = int(np.sqrt(min_map_unit_pixels))  
    # create a grid of points (np.arange) based on local window size
    rows=Flood_global_mask.shape[0]
    columns=Flood_global_mask.shape[1]
    row_coords = np.arange(0,rows,grid_size)
    col_coords = np.arange(0,columns,grid_size)
    coords = list(product(row_coords, col_coords))

    # Select only the points that fall into the global flood map
    coords = [coord for coord in coords if Flood_global_mask[coord]]
        
    return coords

@wrap_non_picklable_objects
def thresholding_pixel(grid_point: tuple,
                       t_score_dataset: np.array,
                       Flood_global_mask: np.array,
                       water_mean_float: float,
                       std_water_float: float,
                       processing_parms: dict) -> Tuple[np.array, np.array, np.array]:

    """Adaptive local thresholding fucntionality at a single grid point

    Args:
        grid_point (tuple): the location of grid point (row, col)
        t_score_dataset (np.array): 2D array with t-score values
        Flood_global_mask (np.array): Boolean global floodwater mask (True: water)
        water_mean_float (float): Mean of floodwater (from global thresholding)
        std_water_float (float): Standard deviation of floodwater (from global thresholding)
        processing_parms (dict): Contains parameters for processing. 
                                 Example: processing_parms={'thresholding_method' : 'Otsu',
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

    Returns:
        Tuple[np.array, np.array, np.array]: win_borders (row_min, row_max, column_min, column_max),
                                             win_flood_mask (updated local floodwater mask),
                                             win_visits (Boolean Trues at window shape)
    """
    #%%
    # 0. Load data
    #--------------------------------------------------------------------------

    window_half_size_min = processing_parms['window_half_size_min']
    window_half_size_max =processing_parms['window_half_size_max']
    window_step = processing_parms['window_step']
    bimodality_thres = processing_parms['bimodality_thres']
    thresholding_method = processing_parms['thresholding_method']
    p_value = processing_parms['p_value']
    flood_percentage_threshold = processing_parms['flood_percentage_threshold']
    row, column = grid_point
    rows=Flood_global_mask.shape[0]
    columns=Flood_global_mask.shape[1]
    #%% 
    # 1. For a range of window sizes calculate Bimodality index values.
    #    This is used to determine the optimal window size to analyze the
    #    the local neighborhood.
    #--------------------------------------------------------------------------
    
    BCs=[]
    win_sizes = np.arange(window_half_size_min, window_half_size_max+1,window_step)
    for window_half_size in win_sizes:

        row_min, row_max, column_min, column_max = sel_borders(row, column,
                                                               rows, columns,
                                                               window_half_size)

        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        BCs.append(Bimodality_test(window_data))
    
    BCs=np.array(BCs)
    BCs[np.isnan(BCs)]=0.0
    
    #%%
    # 2. Check if the maximum bimodality index is above a threshold. 
    #    If the maximum bimodality index is above a threshold that corresponds
    #    to bi/multi modal population of the selected pixels.
    #--------------------------------------------------------------------------
    #    If yes then we have bi/multi modal population inside the window. 
    #       -We select the window size with the highest BC as the optimal one
    #       -We recalculate threhold only at the window level. 
    #       -We calculate the mean,std of candidate local floodwater 
    #        population with lowest mean value
    #       So we have two possibilities:
    #       1. If the candidate population is similar with floodwater 
    #          population or has a lower mean that the water population 
    #          we keep it. We return the local mask.
    #       2. Else there is not water inside the window. We return zeros
    #
    #    Else we have only ONE population in the local neighborhood.
    #    In this case we do nothing and we keep the initial (global) floodmap
    #--------------------------------------------------------------------------
    if np.max(BCs)>bimodality_thres: 
        
        # selecting the borders of the window
        best_window_index = np.argmax(BCs)
        window_half_size =  win_sizes[best_window_index]
        
        row_min, row_max, column_min, column_max = sel_borders(row, column,
                                                               rows, columns,
                                                               window_half_size)
   
        # subsetting the t_score and the global binary mask
        window_mask=Flood_global_mask[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        # selecting only valid data
        valid_data=window_data[~np.isnan(window_data)]   
        flood_pixels_percent=np.sum(window_mask)*100/len(valid_data)   

        # Thresholding
        if thresholding_method=='Otsu':
            thresh = threshold_Otsu(valid_data)
        elif thresholding_method=='Kittler':
            thresh = threshold_Kittler(valid_data)
        else:
            raise('error defining thresholding method')  
                
        local_water_mask = window_data < thresh
        cand_water_values = window_data[local_water_mask]  

        local_land_mask = window_data >= thresh
        cand_land_values = window_data[local_land_mask]
        
        if len(cand_water_values)==0 or len(cand_land_values)==0 or len(window_data[window_mask])==0 or len(window_data[~window_mask])==0 :
            win_flood_mask = window_mask 
        else:
            # calculate flags for water  
            similar_water_flag = Is_similar_non_parametric(cand_values = cand_water_values,
                                                           ref_values = window_data[window_mask],
                                                           p_value = p_value)
            
            darker_than_water_flag = Is_darker_than(values = cand_water_values,
                                                    water_mean_float = water_mean_float,
                                                    std_water_float = std_water_float)

            # check candidate water pixels if they are similar with water or darker
            if similar_water_flag or darker_than_water_flag:
                
                # calculate flags for land
                brighter_than_water = Is_brighter_than(values = cand_land_values,
                                                        water_mean_float = water_mean_float,
                                                        std_water_float = std_water_float)

                similar_land_flag = Is_similar_non_parametric(cand_values = cand_land_values,
                                                             ref_values = window_data[~window_mask],
                                                             p_value = p_value)
                
                # calculate flag for flood pixels
                flood_pixels_percent_flag = flood_pixels_percent > flood_percentage_threshold
                
                # check candidate land pixels if they are similar with land or brighter than water
                if (brighter_than_water or similar_land_flag) and flood_pixels_percent_flag:
                       win_flood_mask = local_water_mask
                else:
                    win_flood_mask = window_mask
            # if values are brigther that typical water do nothing 
            else:
                win_flood_mask = np.zeros(window_mask.shape)
     
    else:
        window_half_size =  window_half_size_max

        # select borders 
        row_min, row_max, column_min, column_max = sel_borders(row, column,
                                                               rows, columns,
                                                               window_half_size)
        
        window_mask=Flood_global_mask[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        values=window_data[~np.isnan(window_data)]  
        if len(values)==0:
            win_flood_mask = np.zeros(window_mask.shape)
        else:
            win_flood_mask =  window_mask

    # calculate borders of local window and visit mask
    win_borders=np.array([row_min, row_max, column_min, column_max])
    win_visits = np.ones(window_mask.shape)
    
    return win_borders, win_flood_mask, win_visits

def Adapt_local_thresholding(t_score_data,
                             Flood_global_mask,
                             water_mean_float,
                             std_water_float,
                             processing_parms):

    # Reading parameters
    num_cores = processing_parms['num_cores']
    min_map_unit_m2 = processing_parms['min_map_unit_m2']
    pixel_m2 = processing_parms['pixel_m2']

    # Initialization
    flood_occurences=np.zeros(Flood_global_mask.shape)
    visits=np.zeros(Flood_global_mask.shape)

    grid_points = calc_grid(Flood_global_mask, min_map_unit_m2, pixel_m2)

    test_list = Parallel(n_jobs=num_cores)(delayed(thresholding_pixel)(grid_point, t_score_data, Flood_global_mask, water_mean_float, std_water_float, processing_parms) for grid_point in grid_points)

    for pixel_index in range(len(test_list)):
        borders_temp, flood_occurences_temp, visits_temp = test_list[pixel_index]
        row_min, row_max, col_min, col_max = borders_temp
        flood_occurences[row_min:row_max, col_min:col_max] += flood_occurences_temp
        visits[row_min:row_max, col_min:col_max] += visits_temp

    probability_map=(flood_occurences)/(visits+1)
    
    return probability_map