#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
# Ignoring all runtime, divided by zero numpy warnings
np.seterr(all='ignore')

class vi():
    """
    A collection of functions for Vegetation Incices in Python. Created for use with Sentinel 2.
    Sources: http://www.sentinel-hub.com/eotaxonomy/indices
    """

    @staticmethod
    def ndvi(red, nir):
        r"""Normalized Difference Vegetation Index

        General formula:
            .. math:: (NIR — VIS)/(NIR + VIS)

        Sentinel 2:
            .. math:: (B08 - B04) / (B08 + B04)

        Args:
            red (ndarray): Red numpy array
            nir (ndarray): NIR numpy array

        Returns:
            ndarray: NDVI numpy array
        """
        

        return (nir - red) / (nir + red)

    @staticmethod
    def ndmi(nir, swir):
        r"""The NDMI is a normalized difference moisture index, that uses NIR and SWIR bands to display moisture.
        The SWIR band reflects changes in both the vegetation water content and the spongy mesophyll structure in
        vegetation canopies, while the NIR reflectance is affected by leaf internal structure and leaf dry matter
        content but not by water content. The combination of the NIR with the SWIR removes variations induced by
        leaf internal structure and leaf dry matter content, improving the accuracy in retrieving the vegetation
        water content. The amount of water available in the internal leaf structure largely controls the spectral
        reflectance in the SWIR interval of the electromagnetic spectrum. SWIR reflectance is therefore negatively
        related to leaf water content. 
        
        General formula:
            .. math:: (NIR — SWIR)/(NIR + SWIR)

        Sentinel 2:
            .. math:: (B8A - B11) / (B8A + B11)

        Args:
            nir (ndarray): NIR numpy array
            swir (ndarray): SWIR numpy array

        Returns:
            ndarray: NDMI numpy array
        """
        

        return (nir - swir) / (nir + swir)