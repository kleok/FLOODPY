#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation metrics calculation

Copyright (C) 2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Karamvasis Kleanthis
Last edit: 13.4.2022

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
