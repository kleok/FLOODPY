#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, glob
import pandas as pd
import geopandas as gpd
import numpy as np
import gc
import xarray as xr

from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_single_1GRD_preprocessing
from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_single_2GRD_preprocessing
from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_pair_preprocessing_1GRD_1GRD
from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_pair_preprocessing_1GRD_2GRD
from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_pair_preprocessing_2GRD_1GRD
from floodpy.Preprocessing_S1_data.snap_preprocessing_funcs import perform_pair_preprocessing_2GRD_2GRD
from floodpy.Preprocessing_S1_data.xarray_funcs import create_coreg_xarray


def Run_Preprocessing(Floodpy_app, overwrite):

    if not overwrite and os.path.exists(Floodpy_app.S1_stack_filename):
        return Floodpy_app.S1_stack_filename

    SNAP_GRAPHS = {
                    '1GRD_h5' : os.path.join(Floodpy_app.graph_dir,
                                            'preprocessing_primary_1GRD.xml'),
                    '2GRD_h5' : os.path.join(Floodpy_app.graph_dir,
                                            'preprocessing_primary_2GRDs.xml'),
                    'pair_1GRD_1GRD' : os.path.join(Floodpy_app.graph_dir,
                                                    'preprocessing_pair_primary_1GRD_secondary_1GRD.xml'),
                    'pair_1GRD_2GRD' : os.path.join(Floodpy_app.graph_dir,
                                                    'preprocessing_pair_primary_1GRD_secondary_2GRD.xml'),
                    'pair_2GRD_1GRD' : os.path.join(Floodpy_app.graph_dir,
                                                    'preprocessing_pair_primary_2GRD_secondary_1GRD.xml'),
                    'pair_2GRD_2GRD' : os.path.join(Floodpy_app.graph_dir,
                                                    'preprocessing_pair_primary_2GRD_secondary_2GRD.xml'),
                    }


    S1_datetimes = Floodpy_app.query_S1_sel_df.sort_index().index.values
    Pre_flood_indices = pd.to_datetime(S1_datetimes)<Floodpy_app.pre_flood_datetime_end
    Pre_flood_datetimes = S1_datetimes[Pre_flood_indices]
    
    # Find the dates for Flood and Pre-flood S1 images
    Flood_date = pd.to_datetime(Floodpy_app.flood_datetime).date()
    S1_dates = [pd.to_datetime(Pre_flood_datetime).date() for Pre_flood_datetime in Pre_flood_datetimes]
    Pre_flood_dates = np.unique(S1_dates)

    S1_flood_rows = Floodpy_app.query_S1_sel_df.loc[pd.to_datetime(Flood_date): pd.to_datetime(Flood_date) + pd.Timedelta(hours=24)]
    AOI_polygon = gpd.read_file(Floodpy_app.geojson_bbox)['geometry'][0]
    Flood_num_GRD_tiles = len(S1_flood_rows)

    if Flood_num_GRD_tiles == 1:
        flood_hdf5_outfile=os.path.join(Floodpy_app.Preprocessing_dir,Floodpy_app.flood_datetime_str)
        flood_xarray_outfile = flood_hdf5_outfile + '.nc'
        flood_img1 = os.path.join(Floodpy_app.S1_dir,S1_flood_rows.iloc[0].Name+'.zip')
        
        if not os.path.exists(flood_xarray_outfile):

            perform_single_1GRD_preprocessing(Floodpy_app.gpt,
                                                flood_img1,
                                                flood_hdf5_outfile,
                                                AOI_polygon,
                                                SNAP_GRAPHS['1GRD_h5'],
                                                '.h5',
                                                overwrite)
    elif Flood_num_GRD_tiles == 2:
        flood_hdf5_outfile=os.path.join(Floodpy_app.Preprocessing_dir,Floodpy_app.flood_datetime_str)
        flood_xarray_outfile = flood_hdf5_outfile + '.nc'

        flood_img1 = os.path.join(Floodpy_app.S1_dir,S1_flood_rows.iloc[0].Name+'.zip')
        flood_img2 = os.path.join(Floodpy_app.S1_dir,S1_flood_rows.iloc[1].Name+'.zip')

        if not os.path.exists(flood_xarray_outfile):

            perform_single_2GRD_preprocessing(Floodpy_app.gpt,
                                                flood_img1,
                                                flood_img2,
                                                flood_hdf5_outfile,
                                                AOI_polygon,
                                                SNAP_GRAPHS['2GRD_h5'],
                                                '.h5',
                                                overwrite)

    else:
        print("It seems that in order to cover you AOI more that 2 GRDs of the same orbit are needed.")
        print("Currently we dont support this.")
        print("Please use a smaller AOI.")

    if not os.path.exists(flood_xarray_outfile):

        # create xarray for flood (primary) image
        create_coreg_xarray(netcdf4_out_filename = flood_xarray_outfile,
                            snap_hdf5_in_filename = flood_hdf5_outfile+ '.h5',
                            geojson_bbox = Floodpy_app.geojson_bbox,
                            ref_tif_file = Floodpy_app.lc_mosaic_filename,
                            primary_image = True,
                            delete_hdf5 = True)

    for Pre_flood_date in Pre_flood_dates:
        S1_pre_flood_rows = Floodpy_app.query_S1_sel_df.loc[pd.to_datetime(Pre_flood_date): pd.to_datetime(Pre_flood_date) + pd.Timedelta(hours=24)]
        AOI_polygon = gpd.read_file(Floodpy_app.geojson_bbox)['geometry'][0]
        Pre_flood_num_GRD_tiles = len(S1_pre_flood_rows)

        if Pre_flood_num_GRD_tiles == 1:

            pre_flood_datetime_str = S1_pre_flood_rows.index[0].strftime('%Y%m%dT%H%M%S')
            pre_flood_hdf5_outfile=os.path.join(Floodpy_app.Preprocessing_dir,pre_flood_datetime_str)
            pre_flood_xarray_outfile = pre_flood_hdf5_outfile + '.nc'

            pre_flood_img1 = os.path.join(Floodpy_app.S1_dir,S1_pre_flood_rows.iloc[0].Name+'.zip')
            
            if Flood_num_GRD_tiles == 1:
                if not os.path.exists(pre_flood_xarray_outfile):
                    print("Coregistrating the primary image (1 GRD): \n {}".format(os.path.basename(flood_img1)))
                    print("with secondary image (1 GRD): \n {}".format(os.path.basename(pre_flood_img1)))
                    print("\n")
                    perform_pair_preprocessing_1GRD_1GRD(Floodpy_app.gpt,
                                                        flood_img1,
                                                        pre_flood_img1,
                                                        pre_flood_hdf5_outfile,
                                                        AOI_polygon,
                                                        SNAP_GRAPHS['pair_1GRD_1GRD'],
                                                        overwrite)

            else: #Flood_num_GRD_tiles == 2
                if not os.path.exists(pre_flood_xarray_outfile):

                    print("Coregistrating the primary image (2 GRDs): \n {} \n {}".format(os.path.basename(flood_img1),os.path.basename(flood_img2)))
                    print("with secondary image (1 GRD): \n {}".format(os.path.basename(pre_flood_img1)))
                    print("\n")

                    perform_pair_preprocessing_2GRD_1GRD(Floodpy_app.gpt,
                                                        flood_img1,
                                                        flood_img2,
                                                        pre_flood_img1,
                                                        pre_flood_hdf5_outfile,
                                                        AOI_polygon,
                                                        SNAP_GRAPHS['pair_2GRD_1GRD'],
                                                        overwrite)

        elif Pre_flood_num_GRD_tiles == 2:

            pre_flood_datetime_str = S1_pre_flood_rows.index.mean().strftime('%Y%m%dT%H%M%S')
            pre_flood_hdf5_outfile=os.path.join(Floodpy_app.Preprocessing_dir,pre_flood_datetime_str)
            pre_flood_xarray_outfile = pre_flood_hdf5_outfile + '.nc'

            pre_flood_img1 = os.path.join(Floodpy_app.S1_dir,S1_pre_flood_rows.iloc[0].Name+'.zip')
            pre_flood_img2 = os.path.join(Floodpy_app.S1_dir,S1_pre_flood_rows.iloc[1].Name+'.zip')


            if Flood_num_GRD_tiles == 1:
                if not os.path.exists(pre_flood_xarray_outfile):
                    print("Coregistrating the primary image (1 GRD): \n {}".format(os.path.basename(flood_img1)))
                    print("with secondary image (2 GRDs): \n {} \n {}".format(os.path.basename(pre_flood_img1),os.path.basename(pre_flood_img2)))
                    print("\n")
                    
                    perform_pair_preprocessing_1GRD_2GRD(Floodpy_app.gpt,
                                                        flood_img1,
                                                        pre_flood_img1,
                                                        pre_flood_img2,
                                                        pre_flood_hdf5_outfile,
                                                        AOI_polygon,
                                                        SNAP_GRAPHS['pair_1GRD_2GRD'],
                                                        overwrite)

            else: #Flood_num_GRD_tiles == 2
                if not os.path.exists(pre_flood_xarray_outfile):
                    print("Coregistrating the primary image (2 GRDs): \n {} \n {}".format(os.path.basename(flood_img1), os.path.basename(flood_img2)))
                    print("with secondary image (2 GRDs): \n {} \n {}".format(os.path.basename(pre_flood_img1), os.path.basename(pre_flood_img2)))
                    print("\n")

                    perform_pair_preprocessing_2GRD_2GRD(Floodpy_app.gpt,
                                                        flood_img1,
                                                        flood_img2,
                                                        pre_flood_img1,
                                                        pre_flood_img2,
                                                        pre_flood_hdf5_outfile,
                                                        AOI_polygon,
                                                        SNAP_GRAPHS['pair_2GRD_2GRD'],
                                                        overwrite)
        else:
            print('Number of tile to analyze: {}'.format(Flood_num_GRD_tiles))
            print("It seems that in order to cover you AOI more that 2 GRDs of the same orbit are needed.")
            print("Currently we dont support this.")
            print("Please use a smaller AOI.")

        if not os.path.exists(pre_flood_xarray_outfile):
            # create xarray for flood (primary) image
            create_coreg_xarray(netcdf4_out_filename = pre_flood_xarray_outfile,
                                snap_hdf5_in_filename = pre_flood_hdf5_outfile+ '.h5',
                                geojson_bbox = Floodpy_app.geojson_bbox,
                                ref_tif_file = Floodpy_app.lc_mosaic_filename,
                                primary_image = False,
                                delete_hdf5 = True)

    S1_products = sorted(glob.glob(os.path.join(Floodpy_app.Preprocessing_dir,'20*.nc')))
    S1_products_xarrays = [xr.open_dataset(S1_product) for S1_product in S1_products ]
    S1_products_xarray_stack = xr.concat(S1_products_xarrays, "time")
    #https://stackoverflow.com/questions/51167677/xarray-wrong-time-after-saving
    #https://stackoverflow.com/questions/54571207/how-to-stop-xarray-from-automatically-changing-time-attributes-when-writing-out
    S1_products_xarray_stack.to_netcdf(Floodpy_app.S1_stack_filename,
                                       format='NETCDF4',
                                       encoding = {'time':{'units': "seconds since 2000-01-01 00:00:00"}})
    del S1_products_xarray_stack
    gc.collect()
