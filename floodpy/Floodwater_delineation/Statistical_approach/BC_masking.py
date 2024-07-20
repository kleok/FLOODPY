#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from skimage.util.shape import view_as_blocks
from scipy.ndimage import gaussian_filter
from scipy.stats import kurtosis, skew

def Bimodality_test(region: np.array, smoothing: bool = True) ->  float:
    """The Bimodality Coefficient (BC) is based on a straightforward 
    empirical relationship (Knapp 2007; Freeman et al., 2013) between the third and fourth statistical moments
    of a distribution (skewness s and kurtosis k).

     .. math:: BC = (s2 + 1) / (k + 3 * (N - 1) ^ {2} / ((N - 2) * (N - 3)))

     Where N represents the sample size.

    The rationale the BC is that a bimodal distribution has very low kurtosis and/or is asymmetric.
    These conditions imply an increase of BC, which ranges from 0 to 1. The value of BC for the 
    uniform distribution is 5/9 (~0.555), while values greater than 5/9 may indicate a 
    bimodal (or multimodal) distribution (Knapp 2007; Freeman et al., 2013). 
    The maximum value (BC = 1) is reached only by a Bernoulli distribution with only 
    two distinct values, or the sum of two different Dirac functions.

    Args:
        region (np.array): 2D numpy array that contains the values to be tested in terms of bimodality
        smoothing (bool, optional): smoothing operation. Defaults to True.

    Returns:
        float: Bimodality coefficient value

    References:
        .. J. B. Freeman and R. Dale, “Assessing bimodality to detect the presence of a dual cognitive process,” Behav. Res. Methods, vol. 45, pp. 83-97, 2013.
        .. T. R. Knapp, “Bimodality revisited,” J. Mod. Appl. Statist. Methods, vol. 6, pp. 8-20, 2007.
    """
    
    if np.all(np.isnan(region)):
        BC=np.nan
    else:
        if smoothing:
            # smoothing
            data = gaussian_filter(region, sigma=5)
        else:
            data = region
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

def Create_Regions(data: np.array, window_size:int = 200) -> np.array:
    """Creates blocks of a certain size from a given 2D numpy array. 
    Blocks are non-overlapping views of the input array.

    Args:
        data (np.array): 2D input array
        window_size (int, optional): the size of . Defaults to 200.

    Returns:
        np.array: Block view of input array based on window_size
    """

    assert data.ndim == 2
    shape1, shape2 = data.shape
    new_shape1=int(np.ceil(shape1/window_size)*window_size)
    new_shape2=int(np.ceil(shape2/window_size)*window_size)
    new_t_score_dataset=np.empty((new_shape1,new_shape2))
    new_t_score_dataset[:] = np.nan
    new_t_score_dataset[:shape1,:shape2]=data
    Blocks = view_as_blocks(new_t_score_dataset, (window_size,window_size))
    
    return Blocks

    
def Calculation_bimodality_mask(t_score_dataset: np.array,
                                min_window_size: int = 50,
                                max_window_size: int = 500,
                                step_window_size: int = 50,
                                bimodality_thres: float = 0.555,
                                segmentation_thres: float = 0.1) -> np.array:

    """Calculation of the bimodality mask.

    TODO: 
        Add an extra condition on the selected of bimodal tiles. 
        I can compare the mean intensity value of the tile 
        with the mean value of all intensity.
    
    Args:
        t_score_dataset (np.array): _description_
        min_window_size (int, optional): Minimum size of window. Defaults to 25.
        max_window_size (int, optional): Maximum size of window. Defaults to 500.
        step_window_size (int, optional): Size of step. Defaults to 50.
        bimodality_thres (float, optional): Threshold of Bimodality coefficient. Defaults to 0.555.
        segmentation_thres (float, optional): Thresholding percentage to create binary bimodality mask. Defaults to 0.6.

    Returns:
        np.array: a boolean array where True (1) represents the regions where bimodality exists.
    """

    data_mask=~np.isnan(t_score_dataset)
    assert len(t_score_dataset.shape)==2
    dim1=t_score_dataset.shape[0]
    dim2=t_score_dataset.shape[1]
    
    window_sizes=range(min_window_size,max_window_size+step_window_size,step_window_size)
    segmentations=np.empty((len(window_sizes),dim1,dim2))
    
    for index, window_size in enumerate(window_sizes):
    
        Blocks=Create_Regions(t_score_dataset, window_size=window_size)
        
        BC=np.empty((Blocks.shape[0],Blocks.shape[1]))
        BC_flag=np.empty((Blocks.shape[0]*window_size,Blocks.shape[1]*window_size), dtype=np.int32)
    
        for ix in range(Blocks.shape[0]):
            for iy in range(Blocks.shape[1]):
                BC[ix,iy] = Bimodality_test(Blocks[ix,iy])
                # get indices relative with given dataset
                dim1_index_min=ix*window_size
                dim1_index_max=ix*window_size+window_size
                dim2_index_min=iy*window_size
                dim2_index_max=iy*window_size+window_size 
                
                if BC[ix,iy]>bimodality_thres :
                    if np.nanmean(Blocks[ix,iy]) < 0:
                        BC_flag[dim1_index_min:dim1_index_max,dim2_index_min:dim2_index_max] = 1
                    else:
                        BC_flag[dim1_index_min:dim1_index_max,dim2_index_min:dim2_index_max] = 0
                else:
                    BC_flag[dim1_index_min:dim1_index_max,dim2_index_min:dim2_index_max] = 0
                    
        segmentations[index,:,:]=BC_flag[:dim1,:dim2]
               
    bimodality_mask=np.mean(segmentations, axis=0)>segmentation_thres
    bimodality_mask=bimodality_mask*data_mask
    
    if np.sum(bimodality_mask)==0:
        bimodality_mask=np.ones_like(t_score_dataset)*data_mask
    
    return bimodality_mask.astype(np.bool_)