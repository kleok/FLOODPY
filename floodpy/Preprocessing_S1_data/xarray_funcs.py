import xarray as xr
import numpy as np
import h5py
import os
import gc
import pandas as pd
import geopandas as gpd

def save_DEM_xarray(DEM, S1_lon_vector, S1_lat_vector, geojson_bbox, ref_xarray, DEM_xarray_outfile):

    df = xr.Dataset(

    {"DEM": (["y", "x"], DEM)},

    coords={
            "x": (["x"], S1_lon_vector),
            "y": (["y"], S1_lat_vector),
    },
    )
    
    df.DEM.attrs["long_name"] = 'Digital Elevation Model'
    df.DEM.attrs["description"] = 'Digital Elevation Model'
    df.DEM.attrs["units"] = 'degrees'

    df.x.attrs['standard_name'] = 'X'
    df.x.attrs['long_name'] = 'Coordinate X'
    df.x.attrs['units'] = 'degrees'
    df.x.attrs['axis'] = 'X'

    df.y.attrs['standard_name'] = 'Y'
    df.y.attrs['long_name'] = 'Coordinate Y'
    df.y.attrs['units'] = 'degrees'
    df.y.attrs['axis'] = 'Y'

    df.rio.write_crs("epsg:4326", inplace=True)

    df_coreg = df.rio.clip(gpd.read_file(geojson_bbox)['geometry'])

    S1_coreg = df_coreg.rio.reproject_match(ref_xarray)
    S1_coreg.to_netcdf(DEM_xarray_outfile, format='NETCDF4')
    S1_coreg.close()

    del df, df_coreg, S1_coreg
    gc.collect()

def save_LIA_xarray(LIA, S1_lon_vector, S1_lat_vector, geojson_bbox, ref_xarray, LIA_xarray_outfile):

    df = xr.Dataset(

    {"LIA": (["y", "x"], LIA)},

    coords={
            "x": (["x"], S1_lon_vector),
            "y": (["y"], S1_lat_vector),
    },
    )
    
    df.LIA.attrs["long_name"] = 'Local Incidence Angle'
    df.LIA.attrs["description"] = 'Local Incidence Angle'
    df.LIA.attrs["units"] = 'degrees'

    df.x.attrs['standard_name'] = 'X'
    df.x.attrs['long_name'] = 'Coordinate X'
    df.x.attrs['units'] = 'degrees'
    df.x.attrs['axis'] = 'X'

    df.y.attrs['standard_name'] = 'Y'
    df.y.attrs['long_name'] = 'Coordinate Y'
    df.y.attrs['units'] = 'degrees'
    df.y.attrs['axis'] = 'Y'

    df.rio.write_crs("epsg:4326", inplace=True)

    df_coreg = df.rio.clip(gpd.read_file(geojson_bbox)['geometry'])

    S1_coreg = df_coreg.rio.reproject_match(ref_xarray)
    S1_coreg.to_netcdf(LIA_xarray_outfile, format='NETCDF4')
    S1_coreg.close()

    del df, df_coreg, S1_coreg
    gc.collect()

def save_backscatter_xarray(VV_dB, VH_dB, VV_VH_dB, S1_lon_vector, S1_lat_vector, S1_datetime, geojson_bbox, ref_xarray, backscatter_xarray_outfile):


    df = xr.Dataset(

    {"VV_dB": (["y", "x"], VV_dB),
    "VH_dB": (["y", "x"], VH_dB),
    "VV_VH_dB": (["y", "x"], VV_VH_dB)},

    coords={
            "x": (["x"], S1_lon_vector),
            "y": (["y"], S1_lat_vector),
            "time": pd.to_datetime(S1_datetime),
    },
    )
    
    df.VV_dB.attrs["long_name"] = 'Backscatter VV'
    df.VV_dB.attrs["description"] = ' The despeckled version of VV using Distributed scatterer concept at ~ 70m.'
    df.VV_dB.attrs["units"] = 'dB'

    df.VH_dB.attrs["long_name"] = 'Backscatter VH'
    df.VH_dB.attrs["description"] = ' The despeckled version of VH using Distributed scatterer concept at ~ 70m.'
    df.VH_dB.attrs["units"] = 'dB'

    df.VV_VH_dB.attrs["long_name"] = 'Product of Backscatter VV*VH'
    df.VV_VH_dB.attrs["description"] = 'Product of Backscatter VV*VH'
    df.VV_VH_dB.attrs["units"] = 'dB'

    df.x.attrs['standard_name'] = 'X'
    df.x.attrs['long_name'] = 'Coordinate X'
    df.x.attrs['units'] = 'degrees'
    df.x.attrs['axis'] = 'X'

    df.y.attrs['standard_name'] = 'Y'
    df.y.attrs['long_name'] = 'Coordinate Y'
    df.y.attrs['units'] = 'degrees'
    df.y.attrs['axis'] = 'Y'

    df.rio.write_crs("epsg:4326", inplace=True)

    df_coreg = df.rio.clip(gpd.read_file(geojson_bbox)['geometry'])

    S1_coreg = df_coreg.rio.reproject_match(ref_xarray)
    S1_coreg.to_netcdf(backscatter_xarray_outfile, format='NETCDF4')
    S1_coreg.close()

    del df, df_coreg, S1_coreg
    gc.collect()

def create_coreg_xarray(netcdf4_out_filename, snap_hdf5_in_filename, geojson_bbox, ref_tif_file, primary_image = True, delete_hdf5 = True):

    # read reference dataset
    ref_xarray = xr.open_dataset(ref_tif_file)

    # extract data from h5 file
    S1_file = h5py.File(snap_hdf5_in_filename,'r')['bands']

    # output directory
    out_dir = os.path.dirname(netcdf4_out_filename)

    if primary_image:

        S1_VV_key = 'Sigma0_VV'
        S1_VH_key = 'Sigma0_VH'

        S1_lat = S1_file['latitude'][:]
        S1_lat[S1_lat==0] = np.nan
        S1_lat_vector = np.nanmean(S1_lat, axis=1)

        S1_lon = S1_file['longitude'][:]
        S1_lon[S1_lon==0] = np.nan
        S1_lon_vector = np.nanmean(S1_lon, axis=0)

        Elevation = S1_file['elevation'][:]
        Elevation[Elevation==0] = np.nan

        LIA = S1_file['localIncidenceAngle'][:]
        LIA[LIA==0] = np.nan

        save_LIA_xarray(LIA = LIA,
                        S1_lon_vector = S1_lon_vector,
                        S1_lat_vector = S1_lat_vector,
                        geojson_bbox = geojson_bbox,
                        ref_xarray = ref_xarray,
                        LIA_xarray_outfile = os.path.join(out_dir,'LIA.nc'))
        
        save_DEM_xarray(DEM = Elevation,
                        S1_lon_vector = S1_lon_vector,
                        S1_lat_vector = S1_lat_vector,
                        geojson_bbox = geojson_bbox,
                        ref_xarray = ref_xarray,
                        DEM_xarray_outfile = os.path.join(out_dir,'DEM.nc'))
        
        np.save(os.path.join(out_dir,'S1_lat_vector.npy'), S1_lat_vector)
        np.save(os.path.join(out_dir,'S1_lon_vector.npy'), S1_lon_vector)

    else:

        S1_VV_key = [S1_key for S1_key in S1_file.keys() if S1_key.startswith('Sigma0_VV_slv')][0]
        S1_VH_key = [S1_key for S1_key in S1_file.keys() if S1_key.startswith('Sigma0_VH_slv')][0]
        
        assert(os.path.exists(os.path.join(out_dir,'S1_lat_vector.npy')))
        assert(os.path.exists(os.path.join(out_dir,'S1_lon_vector.npy')))
        S1_lat_vector = np.load(os.path.join(out_dir,'S1_lat_vector.npy'))
        S1_lon_vector = np.load(os.path.join(out_dir,'S1_lon_vector.npy'))

    VH_linear = S1_file[S1_VH_key][:]
    VH_linear[VH_linear==0] = np.nan
    VH_dB = 10*np.log10(VH_linear)

    VV_linear = S1_file[S1_VV_key][:]
    VV_linear[VV_linear==0] = np.nan
    VV_dB = 10*np.log10(VV_linear)

    VV_VH_dB = 10*np.log10(VV_linear*VH_linear)

    S1_datetime = os.path.basename(snap_hdf5_in_filename).split('.')[0]

    save_backscatter_xarray(VV_dB = VV_dB,
                            VH_dB = VH_dB,
                            VV_VH_dB = VV_VH_dB,
                            S1_lon_vector = S1_lon_vector,
                            S1_lat_vector = S1_lat_vector,
                            S1_datetime = S1_datetime,
                            geojson_bbox = geojson_bbox,
                            ref_xarray = ref_xarray,
                            backscatter_xarray_outfile = os.path.join(out_dir,'{}.nc'.format(S1_datetime)))

    if delete_hdf5:
        if os.path.isfile(snap_hdf5_in_filename): os.remove(snap_hdf5_in_filename)