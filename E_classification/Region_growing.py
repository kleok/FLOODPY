#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Region Growing

Copyright (C) 2021 by K.Karamvasis

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

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

import numpy as np
from skimage.util.shape import view_as_blocks
from scipy.stats import kurtosis, skew
from scipy.ndimage import gaussian_filter
   
def Bimodality_test(region):
    
    '''
    A more robust split selection methodology has been developed by means of the 
    application of the bimodality coefficient (BC) [1]. The BC is based on a 
    straightforward (and therefore suitable for a rapid computation) empirical 
    relationship between bimodality and the third and fourth statistical moments
    of a distribution (skewness s and kurtosis k, respectively) [2]
    
    BC = (s2 + 1)/(k + 3(N−1)^2/(N−2)(N−3))
    
    where N represents the sample size. The rationale the BC is that a bimodal 
    distribution has very low kurtosis, and/or is asymmetric; these conditions 
    imply an increase of BC, which ranges from 0 to 1. The value of BC for the 
    uniform distribution is 5/9 (∼0.555), while values greater than 5/9 may 
    indicate a bimodal (or multimodal) distribution [1]–[2]. The maximum value
    (BC = 1) is reached only by a Bernoulli distribution with only two distinct 
    values, or the sum of two different Dirac functions.
    
    [1] J. B. Freeman and R. Dale, “Assessing bimodality to detect the presence
    of a dual cognitive process,” Behav. Res. Methods, vol. 45, pp. 83–97,
    2013.
    [2] T. R. Knapp, “Bimodality revisited,” J. Mod. Appl. Statist. Methods,
    vol. 6, pp. 8–20, 2007.
    '''
    
    if np.all(np.isnan(region)):
        BC=np.nan
    else:
        # smoothing
        data = gaussian_filter(region, sigma=5)
        # flattening
        data=data.flatten()
        data=data[~np.isnan(data)]
        n=data.shape[0]
        if n<100:
            BC=np.nan
        else:
            s = skew(data) 
            k = kurtosis(data)
            denom2=np.divide(3*(n-1)**2,(n-2)*(n-3))
            BC=np.divide(s*s+1,k+denom2)    
            
    return BC
    

def Create_Regions(data, window_size=200):
    shape1, shape2 = data.shape
    new_shape1=int(np.ceil(shape1/window_size)*window_size)
    new_shape2=int(np.ceil(shape2/window_size)*window_size)
    new_t_score_dataset=np.empty((new_shape1,new_shape2))
    new_t_score_dataset[:] = np.nan
    new_t_score_dataset[:shape1,:shape2]=data
    Blocks = view_as_blocks(new_t_score_dataset, (window_size,window_size))
    
    return Blocks

def Kittler(data):
    """
    The reimplementation of Kittler-Illingworth Thresholding algorithm by Bob Pepin
    Works on 8-bit images only
    Original Matlab code: https://www.mathworks.com/matlabcentral/fileexchange/45685-kittler-illingworth-thresholding
    Paper: Kittler, J. & Illingworth, J. Minimum error thresholding. Pattern Recognit. 19, 41–47 (1986).
    """
    min_value=int(np.percentile(data, 0.1))
    max_value=int(np.percentile(data, 99.9))
    num_values=len(range(min_value,max_value+1))*10
    h,g = np.histogram(data.ravel(),num_values,[min_value,max_value])
    h = h.astype(np.float)
    g = g.astype(np.float)
    g = g[:-1]
    c = np.cumsum(h)
    m = np.cumsum(h * g)
    s = np.cumsum(h * g**2)
    sigma_f = np.sqrt(s/c - (m/c)**2)
    cb = c[-1] - c
    mb = m[-1] - m
    sb = s[-1] - s
    sigma_b = np.sqrt(sb/cb - (mb/cb)**2)
    p =  c / c[-1]
    v = p * np.log(sigma_f) + (1-p)*np.log(sigma_b) - p*np.log(p) - (1-p)*np.log(1-p)
    v[~np.isfinite(v)] = np.inf
    idx = np.argmin(v)
    thres = g[idx]
    return thres

def RG(window_data,window_current_result,RG_thres):
    '''

    Parameters
    ----------
    window_data : TYPE
        DESCRIPTION.
    window_current_result : TYPE
        DESCRIPTION.
    RG_thres : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    
    # find center pixel
    x0=int(np.ceil(window_data.shape[0]/2)-1)
    y0=int(np.ceil(window_data.shape[1]/2)-1)
    # calculate differences 
    diff=window_data-window_data[x0,y0]
    # select only negative differences
    negative_mask=diff<=0
    # return mask that corresponds to negative differences ||---||
    diff_mask=np.abs(diff)<RG_thres
    # combine masks
    RG_result=np.logical_or(window_current_result,diff_mask,negative_mask)
    return RG_result

    
def adapt_RG_threshold(RG_thres,window_data, water_mean_float,std_water_float ):
    low_value=water_mean_float
    high_value=water_mean_float+2*std_water_float
    
    values=window_data[~np.isnan(window_data)]
    values_median=np.median(values)
    
    factor=np.abs((values_median-high_value))/np.abs((low_value-high_value))
    # factor usually takes values between [0-1]
    # for low factor values we have lower threshold (more strict)
    # for high factor values we have higher threshold (less strict)

    if values_median>=high_value:
        factor=0
        
    if values_median<low_value:
        factor=1
 
    result= factor*RG_thres
    
    return result   

def Region_Growing(t_score_dataset_temp,
                   seeds,
                   RG_thres,
                   water_mean_float,
                   std_water_float,
                   max_num_iter=1000,
                   search_window_size=1):

    # Assert that the shapes of image and seed mask agree
    assert (t_score_dataset_temp.shape==seeds.shape)
    seeds=seeds.astype(np.bool)
    rows=t_score_dataset_temp.shape[0]
    columns=t_score_dataset_temp.shape[1]
    RG_result=np.copy(seeds)
    num_iter = 1
    
    while (num_iter<max_num_iter and np.sum(seeds)!=0) :
        
        
        print( 'Iteration : {}'.format(num_iter) )
        seeds_indices=np.nonzero(seeds)
        RG_result_updated=np.copy(RG_result)
        
        
        for seed_index in range(len(seeds_indices[0])):  
            
            if seed_index%100000==1:
                print ('{}/{}'.format(seed_index,len(seeds_indices[0])))
                
            row = seeds_indices[0][seed_index]
            column = seeds_indices[1][seed_index]
            
            row_min = row-search_window_size
            if row_min<0: row_min=0
            row_max = row+search_window_size+1
            if row_max>rows: row_min=rows
            column_min = column-search_window_size
            if column_min<0: column_min=0
            column_max = column+search_window_size+1
            if column_max>columns: column_max=columns
                     
            window_data=t_score_dataset_temp[row_min:row_max,column_min:column_max]
            window_current_result=RG_result[row_min:row_max,column_min:column_max]
            
            if window_current_result.shape[0]>1 and window_current_result.shape[1]>1: # checks if window is not in the corner of the image
                if ~np.all(window_current_result==True):
                    RG_thres_modified=adapt_RG_threshold(RG_thres,window_data, water_mean_float, std_water_float )
                    window_updated_result=RG(window_data,window_current_result,RG_thres_modified) 
                    RG_result_updated[row_min:row_max,column_min:column_max]=window_updated_result 
                
        
        # update RG_result seeds and iteration counter      
        seeds=np.logical_and(~RG_result,RG_result_updated)
        num_iter+=1
        RG_result=RG_result_updated
                      
    return RG_result_updated
