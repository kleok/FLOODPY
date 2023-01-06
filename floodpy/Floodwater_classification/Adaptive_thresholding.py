#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import numpy as np
from joblib import Parallel, delayed, wrap_non_picklable_objects

from floodpy.Floodwater_classification.BC_masking import Bimodality_test
from floodpy.Floodwater_classification.Thresholding_methods import threshold_Kittler, threshold_Otsu
from floodpy.Floodwater_classification.Comparison_tools import Is_similar_non_parametric, Is_distr_water, Is_darkest_than, Is_brighter_than

@wrap_non_picklable_objects
def thresholding_pixel(row,
                       column,
                       rows,
                       columns,
                       t_score_dataset,
                       water_mean_float,
                       std_water_float,
                       Flood_global_binary,
                       window_half_size_min,
                       window_half_size_max,
                       window_step,
                       bimodality_thres,
                       thresholding_method,
                       p_value,
                       flood_percentage_threshold):
    '''
    Adaptive local thresholding fucntionality at a single pixel
    '''
    ##################################
    #=======================================================
    # 1. For a range of window sizes calculate Bimodality index values.
    #    This is used to determine the optimal window size to analyze the
    #    the local neighborhood.
    #=======================================================
    BCs=[]
    for window_half_size in range(window_half_size_min, window_half_size_max+1,window_step):
        
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns
        
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        BCs.append(Bimodality_test(window_data))
    
    BCs=np.array(BCs)
    BCs[np.isnan(BCs)]=0.0
    
    #=======================================================
    # 2. Check if the maximum bimodality index is above a threshold. 
    #    If the maximum bimodality index is above a threshold that corresponds
    #    to bi/multi model population
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
    #       We select the window size with the lowest BC as the optimal one
    #       So we have two possibilities:
    #       The majority of the pixels are non-flooded  or flooded!
    #         -We compare with the floodwater population. If it is similar we
    #          return ones in the local neighborhood
    #         -if pixels have a lower mean that the water population we return
    #          return ones in the local nieghborhood
    #         - else we return zeros in the local neighborhood 
    #=======================================================
    if np.max(BCs)>bimodality_thres: 
        
        best_window_index=np.argmax(BCs)
        window_half_size =  range(window_half_size_min, window_half_size_max+1)[best_window_index]
        
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns    
        
        # subsetting the t_score and the global binary mask
        window_mask=Flood_global_binary[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        # selecting only valid data
        valid_data=window_data[~np.isnan(window_data)]   
        flood_pixels_percent=np.sum(window_mask)*100/len(valid_data)   
         
    
        if thresholding_method=='Otsu':
            thresh = threshold_Otsu(valid_data)
        elif thresholding_method=='Kittler':
            thresh = threshold_Kittler(valid_data)
        else:
            raise('error defining thresholding method')  
                
        local_water_mask=window_data<thresh
        cand_water_values=window_data[local_water_mask]  

        local_land_mask=window_data>=thresh
        cand_land_values=window_data[local_land_mask]
        
        # if np.median(cand_land_values)<water_mean_float:
        #     flood_occurences = np.ones(window_mask.shape)
        # else:
            
        # check if the values look like water
        
        ### parametric way
        # if Is_distr_water(cand_water_values, water_mean_float, std_water_float, threshold=flood_threshold): # if the extracted distribution looks like water
        #     flood_occurences = local_water_mask
        #     visits = np.ones(window_mask.shape)

        ### calculate flags
        
        if len(cand_water_values)==0 or len(cand_land_values)==0 or len(window_data[window_mask])==0 or len(window_data[~window_mask])==0 :
            flood_occurences = window_mask
            visits = np.ones(window_mask.shape)
            
        else:
            # calculate flags for water  
            
            similar_water_flag = Is_similar_non_parametric(cand_values = cand_water_values,
                                                           ref_values = window_data[window_mask],
                                                           p_value = p_value)
            
            darker_than_water_flag = Is_darkest_than(cand_water_values, water_mean_float, std_water_float)

            # check candidate water pixels if they are similar with water or darker
            if similar_water_flag or darker_than_water_flag:
                
                # calculate flags for land
                brighter_than_water = Is_brighter_than(cand_land_values, water_mean_float, std_water_float)
                
                similar_land_flag = Is_similar_non_parametric(cand_values = cand_land_values,
                                                             ref_values = window_data[~window_mask],
                                                             p_value = p_value)
                
                # calculate flag for flood pixels
                flood_pixels_percent_flag = flood_pixels_percent>flood_percentage_threshold
                # check candidate land pixels if they are similar with land or brighter than water
                if (brighter_than_water or similar_land_flag) and flood_pixels_percent_flag:
                       flood_occurences = local_water_mask
                       visits = np.ones(window_mask.shape)
                else:
                    flood_occurences = window_mask
                    visits = np.ones(window_mask.shape)
            # if values are brigther that typical water do nothing 
            else:
                flood_occurences = np.zeros(window_mask.shape)
                visits = np.zeros(window_mask.shape)
     
    else:

        # selecting the window size with the lowest BC as the optimal one
        best_window_index=np.argmin(BCs)
        window_half_size =  range(window_half_size_min, window_half_size_max+1)[best_window_index]
        # calculate indices 
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns 
        
        window_mask=Flood_global_binary[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        values=window_data[~np.isnan(window_data)]  
        if len(values)==0:
            flood_occurences = np.zeros(window_mask.shape)
            visits = np.zeros(window_mask.shape)
        else:
        #######################################################################       
        # first alternative
        #######################################################################
            flood_occurences =  window_mask
            visits = np.ones(window_mask.shape)      
        #######################################################################       
        # second alternative
        #######################################################################    
            
            # # check if the values look like water
            # if Is_distr_water(values, water_mean_float, std_water_float, threshold=flood_threshold):
            #     flood_occurences = window_mask 
            #     visits = np.ones(window_mask.shape)
            # # check if the values are darkest that water       
            # elif Is_darkest_than_water(values, water_mean_float, std_water_float):
            #     flood_occurences = window_mask
            #     visits = np.ones(window_mask.shape)
            # # if values are brigther that typical water do nothing 
            # else:
            #     # produces some holes inside the flood area
            #     flood_occurences =  np.zeros(window_mask.shape) 
            #     visits = np.zeros(window_mask.shape)
            #     #flood_occurences = window_mask
        
    borders=np.array([row_min, row_max, column_min, column_max])
    
    return borders, flood_occurences, visits

def Adaptive_local_thresholdin_parallel(t_score_dataset_temp,
                                        Flood_global_binary_temp,
                                        water_mean_float,
                                        std_water_float,
                                        thresholding_method,
                                        p_value,
                                        window_half_size_min,
                                        window_half_size_max,
                                        window_step,
                                        num_cores,
                                        bimodality_thres,
                                        flood_percentage_threshold):
    '''
    Parallelized Adaptive local thresholding fucntionality.
    '''
    # adaptive thresholding
    rows=Flood_global_binary_temp.shape[0]
    columns=Flood_global_binary_temp.shape[1]
    flood_occurences=np.zeros(Flood_global_binary_temp.shape)
    visits=np.zeros(Flood_global_binary_temp.shape)
    t=time.time()
    for row in range(rows):
        
        if row%250 == 1:
            print ('{}/{}'.format(row,rows))
            print("Processing {} %.".format(round(((row+1)*100/rows),2)))
            elapsed = time.time() - t   
            print("{} sec elapsed...".format(round((elapsed))))
        
        test_list = Parallel(n_jobs=num_cores)(delayed(thresholding_pixel)(row,column,rows,columns,t_score_dataset_temp, water_mean_float, std_water_float, Flood_global_binary_temp, window_half_size_min, window_half_size_max, window_step, bimodality_thres, thresholding_method, p_value, flood_percentage_threshold) for column in range(columns) if Flood_global_binary_temp[row,column] )


        for pixel_index in range(len(test_list)):
            borders, flood_occurences_temp, visits_temp= test_list[pixel_index]
            row_min=borders[0]
            row_max=borders[1]
            column_min=borders[2]
            column_max=borders[3]
            flood_occurences[row_min:row_max,column_min:column_max] += flood_occurences_temp
            visits[row_min:row_max,column_min:column_max] += visits_temp
            

    #Create a [flood_probability_map] using number of visits and number of flood occurences.
    probability_map=(flood_occurences)/(visits+1)
    
    return probability_map