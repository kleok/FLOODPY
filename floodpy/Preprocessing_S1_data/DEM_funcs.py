import xarray as xr
from xrspatial import slope
import rioxarray  # activate the rio accessor

def calc_slope_mask(Floodpy_app):

    DEM_xarray = xr.open_dataset(Floodpy_app.DEM_filename, decode_coords='all')
    DEM_utm_xarray = DEM_xarray.rio.reproject(DEM_xarray.rio.estimate_utm_crs())
    DEM_utm_xarray = DEM_utm_xarray.coarsen(x=6, boundary='pad').max().coarsen(y=6,boundary='pad').max()
    DEM_xarray['slope'] = slope(DEM_utm_xarray.DEM).rio.reproject_match(DEM_xarray)
    DEM_xarray['slope_mask'] = DEM_xarray['slope'] < Floodpy_app.slope_thres

    # overwriting file
    DEM_xarray.to_netcdf(Floodpy_app.DEM_slope_filename, mode='a')