#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from osgeo import gdal
from sklearn.metrics import cohen_kappa_score, confusion_matrix


def Accuracy_metrics_calc(EMS_gdal_raster, Floodpy_gdal_raster, EMS_AOI_mask):
    '''
    Calculation of accuracy metrics between a given map and FLOMPY`s map. 
    Args:
        EMS (TYPE): DESCRIPTION.
        Floodpy (TYPE): DESCRIPTION.

    Returns:
        accuracy_dict (dictionary): Dictionary with accuracy metrics.

    '''
    EMS=gdal.Open(EMS_gdal_raster).ReadAsArray()
    Floodpy=gdal.Open(Floodpy_gdal_raster).ReadAsArray()
    EMS_AOI = gdal.Open(EMS_AOI_mask).ReadAsArray()
    EMS_mask = EMS_AOI>0
    Floodpy_mask = ~np.isnan(Floodpy)
    mask = EMS_mask*Floodpy_mask
    
    EMS=EMS>0
    Floodpy=Floodpy>0  
    
    EMS=EMS[mask]
    Floodpy=Floodpy[mask]
    cf=confusion_matrix(EMS.flatten(), Floodpy.flatten())
    #Accuracy is sum of diagonal divided by total observations
    accuracy  = np.trace(cf) / float(np.sum(cf))
    precision = cf[1,1] / sum(cf[:,1]) # precision (i.e., user’s accuracy) 
    recall    = cf[1,1] / sum(cf[1,:]) # recall (i.e., producer’s accuracy)
    f1_score  = 2*precision*recall / (precision + recall)
    Kappa_score =  cohen_kappa_score(EMS.flatten(), Floodpy.flatten())
    
    accuracy_dict={'Overall_accuracy':accuracy,
                   'Precision':precision,
                   'Recall':recall,
                   'F1_score':f1_score,
                   'Kappa_score':Kappa_score}
    
    return accuracy_dict
