#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2021-2022 by K.Karamvasis
Email: karamvasis_k@hotmail.com

Authors: Karamvasis Kleanthis, Alekos Falagas

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

    @staticmethod
    def evi(nir, red, blue):
        r"""Enhanced Vegetation Index
        
        General formula:
            .. math:: 2.5 * NIR - RED * (NIR + 6 * RED - 7.5 * BLUE) + 1
        
        Sentinel 2:
            .. math:: 2.5 * B08 - B04 *(B08 + 6 * B04 -7.5 * B02) + 1

        Args:
            nir (ndarray): NIR numpy array
            red (ndarray): Red numpy array
            blue (ndarray): Blue numpy array

        Returns:
            ndarray: EVI numpy array
        """

        return 2.5 * (nir - red) / ((nir + 6 * red - 7.5 * blue) + 1)

    @staticmethod
    def savi(nir, red, L = 0.4):
        r"""Soil Adjusted Vegetation Index  (abbrv. SAVI)
        
        General formula:
            .. math:: (800nm - 670nm) / (800nm + 670nm + L) * (1 + L)
        
        Sentinel 2:
            .. math:: (B08 - B04) / (B08 + B04 + L) * (1.0 + L)

        Args:
            nir (ndarray): NIR numpy array
            red (ndarray): Red numpy array
            L (float, optional): SAVI correction factor (0-high vegetation cover, 1-low vegetation cover). Defaults to 0.4.

        Returns:
            ndarray: SAVI numpy array
        """

        return ((nir - red) / (nir + red + L) * (1 + L))

    @staticmethod
    def psri(nir, red, blue):
        r"""Plant Senescence Reflectance Index
        
        General formula: 
            .. math:: 678nm − 500nm / 750nm
        
        Sentinel 2: 
            .. math:: (B04 - B03) / B08

        Args:
            nir (ndarray): NIR numpy array
            red (ndarray): Red numpy array
            blue (ndarray): Blue numpy array

        Returns:
            ndarray: PSRI numpy array
        """

        return ((red - blue) / nir)

    @staticmethod
    def gitelson_green(red, green):
        r"""Green normalized difference vegetation index
        Source: Gitelson et al., 1996

        General formula:
            .. math:: (750nm - 550nm) / (750nm + 550nm)
        
        Sentinel 2: 
            .. math:: (B04 - B03) / (B04 + B03) - 1
        

        Args:
            red (ndarray): Red numpy array
            green (ndarray): Green numpy array

        Returns:
            ndarray: GNDVI Gitelson numpy array
        """
        
        return ((red - green) / (red + green) - 1)

    @staticmethod
    def mcari(red_edge, red, green):
        r"""Modified Chlorophyll Absorption in Reflectance Index   (abbrv. MCARI)

        General formula: 
            .. math:: ((700nm - 670nm) - 0.2 * (700nm - 550nm)) * (700nm /670nm)
        
        Sentinel 2:
            .. math:: (B05 - B04) - 0.2 * (B05 - B03)) * (B05 / B04)

        Args:
            red_edge (ndarray): Red Edge numpy array
            red (ndarray): Red numpy array
            green (ndarray): Green numpy array

        Returns:
            ndarray: MCARI numpy array
        """

        return (((red_edge - red) - 0.2 * (red_edge - green)) * (red_edge / red))

    @staticmethod
    def gndvi(nir, green):
        r"""Green Normalized Difference Vegetation Index   (abbrv. GNDVI)

        General formula: 
            .. math:: (NIR - [540:570]) / (NIR + [540:570])
        
        Sentinel 2: 
            .. math:: (B08 - B03) / (B08 + B03)

        Args:
            nir (ndarray): NIR numpy array
            green (ndarray): Green numpy array

        Returns:
            ndarray: GNDVI numpy array
        """

        return ((nir - green) / (nir + green))

    @staticmethod
    def evi2 (nir, red):
        r"""Enhanced Vegetation Index 2  (abbrv. EVI2)

        General formula:
            .. math:: 2.4 * (NIR - RED) / (NIR + RED + 1)
        
        Sentinel 2:
            .. math:: 2.4 * (B08 - B04) / (B08 + B04 + 1.0)

        Args:
            nir (ndarray): NIR numpy array
            red (ndarray): Red numpy array

        Returns:
            ndarray: EVI2 numpy array
        """

        return (2.4 * (nir - red) / (nir + red + 1))

    @staticmethod
    def gitelson_red_edge(red_edge_2, red_edge):
        r""" Chlorophyll Red-Edge  (abbrv. Chl. red-edge)
        
        General formula:
            .. math:: ([760:800] / [690:720]) ^ (-1)
        
        Sentinel 2:
            .. math:: (B07 / B05) ^ (-1.0)

        Args:
            red_edge_2 (ndarray): Red edge [760:800 nm] numpy array
            red_edge (ndarray): Red edge [690:720nm] numpy array

        Returns:
            ndarray: Gitelson red edge index numpy array
        """
        
        return (np.power((red_edge_2 / red_edge), -1))

    @staticmethod
    def ari(red_edge, green):
        r"""Anthocyanin reflectance index  (abbrv. ARI)
        
        General formula:
            .. math:: 1/550nm-1/700nm
        
        Sentinel 2:
            .. math:: (1.0 / B03) - (1.0 / B05)

        Args:
            red_edge (ndarray): Red edge numpy array
            green (ndarray): Green numpy array

        Returns:
            ndarray: ARI numpy array
        """
        
        return ((1.0 / green) - (1.0 / red_edge))