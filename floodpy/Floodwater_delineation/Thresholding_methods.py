#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from skimage.filters import threshold_otsu

def threshold_Kittler(data: np.array) -> float:
    """ Reimplementation of Kittler-Illingworth Thresholding algorithm by Bob Pepin.
    Works on 8-bit images only. Original Matlab code: https://www.mathworks.com/matlabcentral/fileexchange/45685-kittler-illingworth-thresholding
    
    Args:
        data (np.array): Input data that are at least bimodal.

    Returns:
        float: Threshold value

    ..References:
        Kittler, J. & Illingworth, J. Minimum error thresholding. Pattern Recognit. 19, 41-47 (1986).    
    """
    np.seterr(divide = 'ignore', invalid = 'ignore')
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

def threshold_Otsu(data: np.array) -> float:
    """Otsu thresholding based on skimage functionalities

    Args:
        data (np.array): Input data that are at least bimodal

    Returns:
        float: Threshold value
    """
    return threshold_otsu(data.flatten())
