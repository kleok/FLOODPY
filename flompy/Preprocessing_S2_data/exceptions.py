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
class timeseriesError(Exception):
    """ Base class for exceptions in this module."""
    pass

class imageError(Exception):
    """ Base class for exceptions in this module."""
    pass

class GeometryError(Exception):
    """ Base class for exceptions in this module."""
    pass

class NotSameGeometryError(GeometryError):
    """Error raised when two geometry objects should be the same and their not."""

class NoDataError(timeseriesError):
    """Error raised when no satellite data was found."""
    pass

class NameNotInTimeSeriesError(timeseriesError):
    """Error raised when the provided name is not in the time series object."""
    pass

class MinMaxCloudBoundError(timeseriesError):
    """Error raised when the provided maximum cloud coverage value is less than the minimum cloud coverage value."""
    pass

class MinMaxDateError(timeseriesError):
    """Error raised when the provided maximum date value is less or equal than the minimum date value."""
    pass


class BBOXError(timeseriesError):
    """Error raised when there is no provided bounding box for the time series."""
    pass

class VegetationIndexNotInList(imageError):
    """Error raised whrn the provided Vegetation Index name is not in the list."""
    pass


class BandNotFound(imageError):
    """Error raised when an attribute is not found.""" 
    pass

class PathError(imageError):
    """Raise when the path is not correct."""
    pass