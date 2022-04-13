#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script performs the preprocessing of a Sentinel-1 GRD 


Copyright (C) 2022 by K.Karamvasis

Email: karamvasis_k@hotmail.com
Last edit: 01.4.2021

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

import os, subprocess, glob
import pandas as pd
import geopandas as gpd
import itertools
import h5py
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from osgeo import gdal
import shapely.wkt
from tqdm import tqdm

def _extract_geo_bounds(vector_file, buffer_distance=0.01):
    ''' 
    This function returns a list of coordinates of 
    the bounding box of the given vector file.
    '''
    
    pol1 = gpd.GeoDataFrame.from_file(vector_file)

    bbox_old = pol1.total_bounds
    bbox=[bbox_old[0]-buffer_distance,bbox_old[1]-buffer_distance ,bbox_old[2]-buffer_distance ,bbox_old[3]-buffer_distance ]

    p1 = Point(bbox[0], bbox[3])
    p2 = Point(bbox[2], bbox[3])
    p3 = Point(bbox[2], bbox[1])
    p4 = Point(bbox[0], bbox[1])

    np1 = (p1.coords.xy[0][0], p1.coords.xy[1][0])
    np2 = (p2.coords.xy[0][0], p2.coords.xy[1][0])
    np3 = (p3.coords.xy[0][0], p3.coords.xy[1][0])
    np4 = (p4.coords.xy[0][0], p4.coords.xy[1][0])
    
    bb_polygon = Polygon([np1, np2, np3, np4])
    
    return str(bb_polygon)

def _refine_geo_bounds(S1_products_df, S1_filename, bb_polygon):
    '''
    refines the borders of the AOI
    Parameters
    ----------
    S1_products_df : string
        filename of the csv of the query results for the S1 GRD products.
    S1_filename : string
        the filename of the image that will be used as a master.
    bb_polygon : string
        the filename of the geojson of the AOI.

    Returns
    -------
    shapely polygon
        The intersection of the AOI and the footprint of the master image.

    '''
    # read the metadata of S1 products
    footprints=pd.read_csv(S1_products_df)
    
    # get the geometry of the predifined shapefile AOI
    subset_polygon=gpd.read_file(bb_polygon)['geometry']
    
    # get the footprint geometry of the S1_filename
    df=footprints[footprints['filename']==S1_filename+'.SAFE']
    S1_footprint=shapely.wkt.loads(df['footprint'].iloc[0])
    
    # find the intersection between S1 and AOI shapefile geometry
    subset_polygon=subset_polygon.intersection(S1_footprint)
    
    return subset_polygon.iloc[0]
  

def _Select_slave_image(pair_dataset):
    ''' 
    This function 
    1. reads the created hdf file for each pair 
    2. returns only the slave data
    '''
    All_data=h5py.File(pair_dataset,'r')['bands']
    slave_data=[All_data[data] for data in All_data if 'slv' in data]
    All_data=None
    return slave_data

def check_coregistration_validity(Master_datetime, Slave_datetimes, Preprocessing_dir, valid_ratio = 0.25):
    '''
    discards the pairs of images that the coregistration was not sucessful.
    Assumes that if the coregistration is not sucessful the result is a numpy 
    full of zeros!

    Parameters
    ----------
    Master_datetime : str
        the datetime of the master image of the stack.
    Slave_datetimes : list
        the datetimes of the slav images of the stack.
    Preprocessing_dir : str
        the directory of the preprocessing.

    Returns
    -------
    Slave_datetimes_refined : list
        the datetimes of the images that coregistration was sucessful.

    '''
    
    Slave_datetimes_refined = np.array(Slave_datetimes)
    
    drop_indices=[]
    for image_index, slave_datetime in enumerate(Slave_datetimes_refined):
        print (slave_datetime)
        
        temp_slave_data=_Select_slave_image(os.path.join(Preprocessing_dir,Master_datetime+'_'+slave_datetime+'.h5'))
        temp_VH=temp_slave_data[0][:]
        num_pixels = temp_VH.shape[0]*temp_VH.shape[1]
        
        if np.mean(temp_VH)==0.0:
            drop_indices.append(image_index)
            print ('Dropped... {}'.format(slave_datetime))
            
        elif np.sum(temp_VH==0.0)>(num_pixels*valid_ratio):
            drop_indices.append(image_index)
            print ('Dropped... {}'.format(slave_datetime))
            
        else:
            pass
        
    Slave_datetimes_refined = np.delete(Slave_datetimes_refined,drop_indices)
       
    return list(Slave_datetimes_refined)

def Create_dhf5_stack_file(Master_datetime, Slave_datetimes, Preprocessing_dir):
    ''' 
    This function creates hdf5 stack that contains all the data for the stack.
    Assumes master is the latest image
    '''
    Stack_dir=os.path.join(Preprocessing_dir,'Stack')
    if not os.path.exists(Stack_dir): os.makedirs(Stack_dir)
    #
    All_images=len(Slave_datetimes)+1
    #Define dimensions
    Number_images=All_images
    Master_image_data_shape=gdal.Open(os.path.join(Preprocessing_dir,Master_datetime+'.tif')).ReadAsArray().shape
    
    shape_SAR=(Number_images, Master_image_data_shape[1], Master_image_data_shape[2])
    
    output_stack_name=os.path.join(Stack_dir,'SAR_Stack.h5')
    
    if os.path.exists(output_stack_name):
        return os.path.join(Stack_dir,'SAR_Stack.h5')

    #Create hdf5 file
    dt = h5py.special_dtype(vlen=str) 
    hdf5_file = h5py.File(output_stack_name, mode='w')
    hdf5_file.create_dataset("VV_db", shape_SAR, np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("VH_db", shape_SAR, np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("VV_VH_db", shape_SAR, np.float32, compression='gzip', compression_opts=9)  
    hdf5_file.create_dataset("elevation", shape_SAR[1:], np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("localIncidenceAngle", shape_SAR[1:], np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("latitude", shape_SAR[1:], np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("longitude", shape_SAR[1:], np.float32, compression='gzip', compression_opts=9)
    hdf5_file.create_dataset("Datetime_SAR", shape_SAR[0:1], dtype=dt, compression='gzip', compression_opts=9)
    
    all_dates=Slave_datetimes.copy()
    all_dates.append(Master_datetime)
    all_dates.sort()
    
    for datetime_index, datetime in enumerate(all_dates):
        
        if datetime!=Master_datetime:

            temp_slave_data=_Select_slave_image(os.path.join(Preprocessing_dir,Master_datetime+'_'+datetime+'.h5'))
            
            temp_VH=temp_slave_data[0][:]
            temp_VH[temp_VH<0.0]=1e-15
            temp_VH[temp_VH==0.0]=np.nan
            
            temp_VV=temp_slave_data[1][:]
            temp_VV[temp_VV<0.0]=1e-15
            temp_VV[temp_VV==0.0]=np.nan
            
            temp_VH_db=10*np.log10(temp_VH)
            temp_VV_db=10*np.log10(temp_VV)
            temp_VV_VH_db=10*np.log10(temp_VH*temp_VV)
            
            hdf5_file["VV_db"][datetime_index,:,:] = temp_VV_db
            hdf5_file["VH_db"][datetime_index,:,:] = temp_VH_db
            hdf5_file["VV_VH_db"][datetime_index,:,:] = temp_VV_VH_db
            hdf5_file["Datetime_SAR"][datetime_index] = datetime
            
        else:
        
            temp_master_data=h5py.File(os.path.join(Preprocessing_dir,Master_datetime+'.h5'),'r')['bands']
            
            temp_VH=temp_master_data['Sigma0_VH'][:]
            temp_VH[temp_VH<0.0]=1e-15
            temp_VH[temp_VH==0.0]=np.nan
        
            temp_VV=temp_master_data['Sigma0_VV'][:]
            temp_VV[temp_VV<0.0]=1e-15
            temp_VV[temp_VV==0.0]=np.nan  
            
            temp_VH_db=10*np.log10(temp_VH)
            temp_VV_db=10*np.log10(temp_VV)
            temp_VV_VH_db=10*np.log10(temp_VH*temp_VV)
            
            hdf5_file["VV_db"][datetime_index,:,:] = temp_VV_db
            hdf5_file["VH_db"][datetime_index,:,:] = temp_VH_db
            hdf5_file["VV_VH_db"][datetime_index,:,:] = temp_VV_VH_db
            hdf5_file["Datetime_SAR"][datetime_index] = Master_datetime
    
            elevation=temp_master_data['elevation'][:]
            elevation[elevation==-32768]=np.nan
        
            hdf5_file["elevation"][:] = elevation
            hdf5_file["longitude"][:] =temp_master_data['longitude'][:]
            hdf5_file["latitude"][:] =temp_master_data['latitude'][:]
            hdf5_file["localIncidenceAngle"][:] = temp_master_data['localIncidenceAngle'][:]
    
    hdf5_file.close()

    return os.path.join(Stack_dir,'SAR_Stack.h5')


def _perform_master_preprocessing(gptcommand,master,outfile,Subset_AOI,xml_file,ext):
    ''' 
    This function extracts information that shared among all SLC acquisitions
    in the stack. In uses a customized version of pair_preprocessing graph xml
    file and writes lat,lon,DEM, incidence angle as well as Polarimetric matrix
    information for the master image.
    '''
    if not os.path.exists(outfile+ext):
        argvs=[gptcommand, '-e',
               xml_file,
               '-Pfilein='+master,
               '-Ppolygon='+str(Subset_AOI),
               '-Pfileout='+outfile]

        subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        pass


def _perform_pair_preprocessing(gptcommand,master,slave,outfile,Subset_AOI,xml_file):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not os.path.exists(outfile):
        argvs=[gptcommand, '-e',
               xml_file,
               '-Pfilein1='+master,
               '-Pfilein2='+slave,
               '-Ppolygon='+str(Subset_AOI),
               '-Pfileout='+outfile]
        
        subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        pass

def _Plot_SAR_Stack(hdf5_stack_file,Stack_dir):
    
    Plot_dir=os.path.join(Stack_dir,'Plots')
    if not os.path.exists(Plot_dir): os.makedirs(Plot_dir)
    
    plot_stack=h5py.File(hdf5_stack_file)
    number_of_images=plot_stack['Datetime_SAR'].shape[0]
    
    TS_Datasets=['C11', 'C12_imag', 'C12_real', 'C22']
    
    for Dataset in TS_Datasets:
        fig, axes = plt.subplots(number_of_images, 1, sharex=True, sharey=True)
        
        for i, ax in enumerate(axes.ravel()):
            im = ax.imshow(10*np.log10(plot_stack[Dataset][i,...]))
            ax.set_title(i)
        plt.tight_layout()
        plt.savefig(os.path.join(Plot_dir,'{}_plot.png'.format(Dataset)))
        plt.close()
     
    Static_Datasets=['elevation', 'latitude', 'localIncidenceAngle', 'longitude']
    
    for Static_dataset in Static_Datasets:
        data=plot_stack[Static_dataset][:]
        if Static_dataset=='elevation':
            data_plot=np.ma.masked_where(data == -32768.0, data)
        else :
            data_plot=np.ma.masked_where(data == 0, data)
        plt.imshow(data_plot)
        plt.title(Static_dataset)
        plt.tight_layout()
        plt.savefig(os.path.join(Plot_dir,'{}_plot.png'.format(Static_dataset)))
        plt.close()
    return 0

def _delete_intermediate_files(Output_dir):
    intermediate_files=glob.glob(Output_dir+'/*.h5')
    for intermediate_file in intermediate_files:
        os.remove(intermediate_file) 

def _normalize_raster(numpy_array_3d):
    temp3d=numpy_array_3d
    temp_norm_3d=np.zeros(temp3d.shape)
    for index in range(temp3d.shape[0]):
        temp2d=temp3d[index,:,:]
        temp_nan=temp2d[temp2d==0]=np.nan
        temp_nan_log10=np.log10(temp_nan)
        temp_nan_log10_normed=(temp_nan_log10-np.nanmean(temp_nan_log10))/np.nanstd(temp_nan_log10)
        temp_norm_3d[index,:,:]=temp_nan_log10_normed
    return temp_norm_3d


def get_flood_image(S1_GRD_dir, flood_datetime):
    S1_products = glob.glob(S1_GRD_dir+'/S1_products.csv')[0]
    S1_df=pd.read_csv(S1_products)
    S1_df.reset_index(inplace=True)
    
    S1_temp=S1_df.copy()
    S1_temp.index=pd.to_datetime(S1_temp['beginposition'])
    
    S1_flood_datetime_diffs=(S1_temp.index-flood_datetime).tolist()
    S1_flood_diffs = [S1_flood_datetime_diff.days for S1_flood_datetime_diff in S1_flood_datetime_diffs ]
    
    if np.all(np.array(S1_flood_diffs)<0):
        day_diff=np.max(np.array(S1_flood_diffs))
    else:
        day_diff = min([i for i in S1_flood_diffs if i >= 0])
   
    S1_flood_index = S1_flood_diffs.index(day_diff)
    flood_S1_image = S1_df['filename'].iloc[S1_flood_index]
    print('{} product is picked \n as the "Flood image" because it was \
          acquired after {} days \n from the time of flood event'.format(flood_S1_image,day_diff))
    flood_S1_filename_df = pd.DataFrame([flood_S1_image])
    flood_S1_filename_df.to_csv(os.path.join(S1_GRD_dir,'flood_S1_filename.csv'))
    
    return 0

def Run_Preprocessing(gpt_exe,
                      graph_dir,
                      S1_GRD_dir,
                      geojson_S1,
                      Preprocessing_dir):
    '''
    Performs all the preprocessing procedure 
    '''
    
    S1_products = os.path.join(S1_GRD_dir,'S1_products.csv')
    assert os.path.exists(S1_products)
    
    master_xml_file = os.path.join(graph_dir,'preprocessing_GRD_master.xml')
    pair_xml_file = os.path.join(graph_dir,'preprocessing_GRD_pair.xml')
    master_xml_tiff_file = os.path.join(graph_dir,'preprocessing_GRD_master_tiff.xml')
    
    # Create output directory
    if not os.path.exists(Preprocessing_dir):
        os.makedirs(Preprocessing_dir)

    # check that master image is downloaded
    
    flood_S1_image_filename = os.path.join(S1_GRD_dir,'flood_S1_filename.csv')
    assert os.path.exists(flood_S1_image_filename)
    
    flood_S1_image = pd.read_csv(flood_S1_image_filename, index_col=0).iloc[0][0]
    
    if not flood_S1_image.endswith('zip'):
        flood_S1_image = flood_S1_image.split('.')[0]+'.zip'
    Flood_image=os.path.join(S1_GRD_dir, flood_S1_image)
    assert (os.path.exists(Flood_image))
    
    
    S1_images_df = pd.read_csv(os.path.join(S1_GRD_dir,'baseline_images.csv'))   
    # # selects the latest baseline image as master
    # try:
    #     Master_image=S1_images_df[S1_images_df['baseline']==True]['S1_GRD'].iloc[0]
    # except:
    #     Master_image=S1_images_df['S1_GRD'].iloc[0]
    # selects the flood image as master
    Master_image=Flood_image
    
    Master_datetime=os.path.basename(Master_image)[17:32]
    print(" We coregister the images in respect with the acquisition of {}".format(os.path.basename(Master_image)))

    Master_image_filename=os.path.join(S1_GRD_dir,Master_image)
    assert (os.path.exists(Master_image_filename))
    
    # A polygon object of the given AOI
    Master_filename=os.path.basename(Master_image).split('.')[0]
    AOI_Polygon=_refine_geo_bounds(S1_products,Master_filename , geojson_S1)
    
    if str(AOI_Polygon)=='POLYGON EMPTY' :
        return
    
    # perform the processing for master image 
    print ('Processing of flood image {}'.format(os.path.basename(Master_image)))
    outfile=os.path.join(Preprocessing_dir,Master_datetime)
    _perform_master_preprocessing(gpt_exe,Master_image_filename,outfile,AOI_Polygon,master_xml_file,'.h5')
    _perform_master_preprocessing(gpt_exe,Master_image_filename,outfile,AOI_Polygon,master_xml_tiff_file,'.tif')
    # Create pair combinations with one master
    One_master_combinations=[]
    
    slave_products_filenames=S1_images_df[S1_images_df['baseline']==True]['S1_GRD'].tolist()
    #slave_products_filenames = [glob.glob(S1_GRD_dir+'/*/'+slave_image)[0] for slave_image in slave_products ]
    # slave_products_filenames.append(Flood_image)
    # slave_products_filenames.remove(Master_image)
    
    for pair in itertools.product([Master_image],slave_products_filenames):
        One_master_combinations.append(pair)
    
    Slave_datetimes=[]
    
    # perform the pre-processing for each pair
    
    # Step A
    # orbit correction
    # subset
    # coregistration
    # cross-correlation
    # warp
    # geocoding
    
    for pair in tqdm(One_master_combinations, total=len(One_master_combinations)):
        Slave_image=pair[1]
        Slave_datetime=os.path.basename(pair[1])[17:32]
        Slave_datetimes.append(Slave_datetime)
        outfile=os.path.join(Preprocessing_dir,Master_datetime+'_'+Slave_datetime+'.h5')
        _perform_pair_preprocessing(gpt_exe,Master_image,Slave_image,outfile,AOI_Polygon,pair_xml_file)
    
    print("Refine borders of Sentinel-1 acquisitions")
    Slave_datetimes_refined = check_coregistration_validity(Master_datetime,
                                                            Slave_datetimes,
                                                            Preprocessing_dir,
                                                            0.5)
    print('Baseline Stack images:')
    [print(image) for image in Slave_datetimes]
    print('Flood image:')
    print(Master_datetime)
    
    hdf5_stack_file=Create_dhf5_stack_file(Master_datetime,
                                           Slave_datetimes_refined,
                                           Preprocessing_dir)
    print ('All information from SAR imagery are stored at {}'.format(hdf5_stack_file))
    #_Plot_SAR_Stack(hdf5_stack_file,Output_dir)
    #_delete_intermediate_files(Output_dir)
    
    return hdf5_stack_file
    


