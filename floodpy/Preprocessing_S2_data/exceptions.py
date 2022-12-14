#!/usr/bin/env python
# -*- coding: utf-8 -*-

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