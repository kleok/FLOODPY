#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, glob
import pandas as pd
import geopandas as gpd
import h5py
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from osgeo import gdal
import shapely.wkt
from tqdm import tqdm

def _shapely_to_snap_polygon(AOI):
    
    x, y = AOI.exterior.coords.xy
    
    str_polygon=str(AOI)
    str_polygon = str_polygon.split('))')[0]
    
    last_coords = ', {} {}))'.format(x[-1], y[-1])
    
    snap_polygon = str_polygon+last_coords
    return snap_polygon
    
def _extract_geo_bounds(vector_file, buffer_distance=0.01):
    ''' 
    This function returns a list of coordinates of 
    the bounding box of the given vector file.
    '''
    
    pol1 = gpd.GeoDataFrame.from_file(vector_file)

    bbox_old = pol1.total_bounds
    bbox=[bbox_old[0]-buffer_distance,
          bbox_old[1]-buffer_distance,
          bbox_old[2]-buffer_distance,
          bbox_old[3]-buffer_distance ]

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
    Refines the borders of the AOI based on footprint geometries of Sentinel-1
    acquisitions.
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
  

def _Select_slave_image(baseline_filename):
    ''' 
    This function returns the secondary image from a given pair of images
    # changeeee
    '''
    All_data=h5py.File(baseline_filename,'r')['bands']
    Baseline_data=[All_data[data] for data in All_data if 'slv' in data]
    All_data=None
    return Baseline_data

def check_coregistration_validity(Master_datetime, Baseline_datetimes, Preprocessing_dir, valid_ratio = 0.25):
    '''
    Discards the pairs of images that the coregistration was not sucessful.
    Assumes that if the coregistration is not sucessful the result is a numpy 
    full of zeros!
    '''
    
    Baseline_datetimes_refined = np.array(Baseline_datetimes)
    
    drop_indices=[]
    for image_index, baseline_datetime in enumerate(Baseline_datetimes_refined):
        print (baseline_datetime)
        
        temp_baseline_data=_Select_slave_image(os.path.join(Preprocessing_dir,baseline_datetime+'.h5'))
        temp_VH=temp_baseline_data[0][:]
        num_pixels = temp_VH.shape[0]*temp_VH.shape[1]
        
        if np.mean(temp_VH)==0.0:
            drop_indices.append(image_index)
            print ('Dropped... {}'.format(baseline_datetime))
            
        elif np.sum(temp_VH==0.0)>(num_pixels*valid_ratio):
            drop_indices.append(image_index)
            print ('Dropped... {}'.format(baseline_datetime))
            
        else:
            pass
        
    Baseline_datetimes_refined = np.delete(Baseline_datetimes_refined,drop_indices)
       
    return list(Baseline_datetimes_refined)

def Create_dhf5_stack_file(Master_datetime, Slave_datetimes, Preprocessing_dir, overwrite):
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
    
    if not overwrite:
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

            temp_slave_data=_Select_slave_image(os.path.join(Preprocessing_dir,datetime+'.h5'))
            
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


def _perform_single_GRD_preprocessing(gptcommand,master,outfile,Subset_AOI,xml_file,ext, overwrite):
    ''' 
    This function extracts information that shared among all SLC acquisitions
    in the stack. In uses a customized version of pair_preprocessing graph xml
    file and writes lat,lon,DEM, incidence angle as well as Polarimetric matrix
    information for the master image.
    '''
    if not overwrite:
        if os.path.exists(outfile+ext):
            return 0

    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein='+master,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]

    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

    
def _perform_assembly_GRD_preprocessing(gptcommand, img1, img2 ,outfile, Subset_AOI, xml_file, ext, overwrite):
    ''' 
    This function extracts information that shared among all SLC acquisitions
    in the stack. In uses a customized version of pair_preprocessing graph xml
    file and writes lat,lon,DEM, incidence angle as well as Polarimetric matrix
    information for the master image.
    '''
    if not overwrite:
        if os.path.exists(outfile+ext):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+img1,
            '-Pfilein2='+img2,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile+ext]

    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

def _perform_pair_preprocessing(gptcommand,master,slave,outfile,Subset_AOI,xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0

    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+master,
            '-Pfilein2='+slave,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    
    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

    
def _perform_assembly_pair_preprocessing(gptcommand, master1, master2, slave1, slave2, outfile, Subset_AOI, xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+master1,
            '-Pfilein2='+master2,
            '-Pfilein3='+slave1,
            '-Pfilein4='+slave2,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    
    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

def Plot_SAR_Stack(hdf5_stack_file,Plot_dir):
    '''
    Plotting functionality of SAR stack
    '''
    
    plot_stack=h5py.File(hdf5_stack_file,'r')
    number_of_images=plot_stack['Datetime_SAR'].shape[0]

    # lats=np.nanmean(plot_stack['latitude'][:], axis=1)
    # lons=np.nanmean(plot_stack['longitude'][:], axis=0)

    # min_lat = np.min(lats)
    # min_lon = np.min(lons)
    # max_lat = np.max(lats)
    # max_lon = np.max(lons)
    
    # del lats, lons

    Static_Datasets=['elevation', 'localIncidenceAngle']
    
    for Static_dataset in Static_Datasets:
        data=plot_stack[Static_dataset][:]
        if Static_dataset=='elevation':
            data_plot=np.ma.masked_where(data == -32768.0, data)
            Dataset_units='meters'
        else :
            data_plot=np.ma.masked_where(data == 0, data)
            Dataset_units='degrees' 
        plt.figure(figsize = (15,15))
        #plt.imshow(data_plot, extent=[min_lon,max_lon,min_lat,max_lat], aspect='auto')
        plt.imshow(data_plot)
        cbar = plt.colorbar()
        cbar.set_label('{}'.format(Dataset_units), rotation=270)
        plt.title(Static_dataset)
        plt.tight_layout()
        plt.savefig(os.path.join(Plot_dir,'{}_plot.png'.format(Static_dataset)), dpi=120)
        plt.close()
        
    del data, data_plot
    
    TS_Datasets=['VV_db']
    for Dataset in TS_Datasets:
        for band_index, image in enumerate(range(number_of_images)):
            if band_index==0:
                vmin=np.nanquantile(plot_stack[Dataset][band_index,...].flatten(), 0.01)
                vmax=np.nanquantile(plot_stack[Dataset][band_index,...].flatten(), 0.99)
                
            plt.figure(figsize = (15,15))
            # plt.imshow(plot_stack[Dataset][band_index,...],
            #            vmin=vmin,
            #            vmax=vmax,
            #            extent=[min_lon,max_lon,min_lat,max_lat],
            #            aspect='auto')
            plt.imshow(plot_stack[Dataset][band_index,...],
                       vmin=vmin,
                       vmax=vmax)
            plt.title(plot_stack['Datetime_SAR'][band_index])
            cbar = plt.colorbar()
            cbar.set_label('{}'.format('Decibel'), rotation=270)
            plt.tight_layout()
            plt.savefig(os.path.join(Plot_dir,'{}_{}.png'.format(str(plot_stack['Datetime_SAR'][band_index]),
                                                                 Dataset)),
                        dpi=120)
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


def Run_Preprocessing(projectfolder,
                      gpt_exe,
                      graph_dir,
                      S1_dir,
                      geojson_S1,
                      Preprocessing_dir,
                      overwrite):
    '''
    Performs all the preprocessing procedure of Sentinel-1 dataset
    '''
    
    # check that we have S1 products to work with
    S1_products = os.path.join(S1_dir,'S1_products.csv')
    assert os.path.exists(S1_products)
    
    # check that primary/flood image is downloaded
    flood_S1_image_filename = os.path.join(S1_dir,'flood_S1_filename.csv')
    assert os.path.exists(flood_S1_image_filename)
    
    flood_S1_image = pd.read_csv(flood_S1_image_filename, index_col=0).loc['title'].values[0]
    
    if not flood_S1_image.endswith('zip'):
        flood_S1_image = flood_S1_image.split('.')[0]+'.zip'
    Flood_image=os.path.join(S1_dir, flood_S1_image)
    assert (os.path.exists(Flood_image))
    
    # SNAP graphs that will be used for preprocessing
    # AOI is covered by a single GRD
    single_grd_xml_file = os.path.join(graph_dir,'preprocessing_single_GRD.xml')
    single_grd_xml_tiff_file = os.path.join(graph_dir,'preprocessing_single_GRD_tiff.xml')
    single_baseline_grd_xml_file = os.path.join(graph_dir,'preprocessing_GRD_pair.xml')
    
    # AOI is covered by two GRDs
    assembly_grd_xml_file = os.path.join(graph_dir,'preprocessing_assembly_GRD.xml')
    assembly_grd_xml_tiff_file = os.path.join(graph_dir,'preprocessing_assembly_GRD_tiff.xml')
    assembly_baseline_grd_xml_file = os.path.join(graph_dir,'preprocessing_assembly_GRD_pair.xml')

    S1_images_df = pd.read_csv(os.path.join(S1_dir,'baseline_images.csv'))   

    # Flood image is selected as Primary/master image
    Flood_image_filename = Flood_image
    Flood_datetime=os.path.basename(Flood_image)[17:32]
    print(" We coregister the images in respect with the acquisition of {}".format(os.path.basename(Flood_image_filename)))

    Flood_filename=os.path.basename(Flood_image_filename).split('.')[0]
    
    # now we check if assembly functionalities are required for master image
    
    time_diffs_df = pd.to_datetime(S1_images_df['Datetime'])-pd.to_datetime(Flood_datetime)
    S1_flood_img_index = np.abs(time_diffs_df.dt.total_seconds())<60
    
    flood_outfile=os.path.join(Preprocessing_dir,Flood_datetime)
    print ('Processing of flood image {}'.format(os.path.basename(Flood_datetime)))
    
    if np.sum(S1_flood_img_index) == 1: # we have only a single GRD for the flood date
        AOI_Polygon=_refine_geo_bounds(S1_products,Flood_filename , geojson_S1)
        assert str(AOI_Polygon) !='POLYGON EMPTY' 
        
        _perform_single_GRD_preprocessing(gpt_exe,
                                          Flood_image_filename,
                                          flood_outfile,
                                          AOI_Polygon,
                                          single_grd_xml_file,
                                          '.h5',
                                          overwrite)
        
        _perform_single_GRD_preprocessing(gpt_exe,
                                          Flood_image_filename,
                                          flood_outfile,
                                          AOI_Polygon,
                                          single_grd_xml_tiff_file,
                                          '.tif',
                                          overwrite)
        flood_img1 = None
        flood_img2 = None
        
    elif np.sum(S1_flood_img_index) == 2: # we have two GRD images to assebly for the flood date
        
        flood_img1, flood_img2 = S1_images_df['S1_GRD'][S1_flood_img_index]
        Subset_AOI = gpd.read_file(geojson_S1)['geometry'][0]
        
        _perform_assembly_GRD_preprocessing(gpt_exe,
                                            flood_img1,
                                            flood_img2,
                                            flood_outfile,
                                            Subset_AOI,
                                            assembly_grd_xml_file,
                                            '.h5',
                                            overwrite)
        
        _perform_assembly_GRD_preprocessing(gpt_exe,
                                            flood_img1,
                                            flood_img2,
                                            flood_outfile,
                                            Subset_AOI,
                                            assembly_grd_xml_tiff_file,
                                            '.tif',
                                            overwrite)
    
    else:
        print("It seems that in order to cover you AOI more that 2 GRDs of the same orbit are needed.")
        print("Currently we dont support this.")
        print("Please use a smaller AOI.")
        #return
        
    # preprocessing of baseline images
    # we drop the images that are not going to be used for baseline stack
    # we first drop the images that are used for flood image
    S1_images_df.drop(S1_images_df.index[S1_flood_img_index], inplace=True)
    
    # we drop the images that have big accumulated rain precipitation
    S1_img_drop_index = S1_images_df['baseline']==False
    S1_images_df.drop(S1_images_df.index[S1_img_drop_index], inplace=True)
    
    Baseline_datetimes = []
    
    while len(S1_images_df)>0:
        
        Baseline_datetime = pd.to_datetime(S1_images_df['Datetime'].iloc[0]).strftime('%Y%m%dT%H%M%S')
        Baseline_image_filename = S1_images_df['S1_GRD'].iloc[0]
        time_diffs_df = pd.to_datetime(S1_images_df['Datetime'])-pd.to_datetime(Baseline_datetime)
        S1_baseline_img_index = np.abs(time_diffs_df.dt.total_seconds())<60
        baseline_outfile=os.path.join(Preprocessing_dir,Baseline_datetime)
        print ('Processing of baseline image {}'.format(os.path.basename(Baseline_datetime)))
        Baseline_datetimes.append(Baseline_datetime)

        # We need to coregister the assembly products in order to work         
        if np.sum(S1_baseline_img_index) == 1:
             
            _perform_pair_preprocessing(gpt_exe,
                                        Flood_image_filename,
                                        Baseline_image_filename,
                                        baseline_outfile,
                                        AOI_Polygon,
                                        single_baseline_grd_xml_file,
                                        overwrite)
            
        elif np.sum(S1_baseline_img_index) == 2:   
            
            baseline_img1, baseline_img2 = S1_images_df['S1_GRD'][S1_baseline_img_index]
            Subset_AOI = gpd.read_file(geojson_S1)['geometry'][0]
            
            _perform_assembly_pair_preprocessing(gpt_exe,
                                                 flood_img1,
                                                 flood_img2,
                                                 baseline_img1,
                                                 baseline_img2,
                                                 baseline_outfile,
                                                 Subset_AOI,
                                                 assembly_baseline_grd_xml_file,
                                                 overwrite)
            
        else:
            
            print("It seems that in order to cover you AOI more that 2 GRDs of the same orbit are needed.")
            print("Currently we dont support this.")
            print("Please use a smaller AOI.")
            #return
        
        # We drop each baseline image after the processing
        S1_images_df.drop(S1_images_df.index[S1_baseline_img_index], inplace=True)


    print("Refine borders of Sentinel-1 acquisitions")
    Baseline_datetimes_refined = check_coregistration_validity(Flood_datetime,
                                                            Baseline_datetimes,
                                                            Preprocessing_dir,
                                                            0.5)
    print('Baseline Stack images:')
    [print(image) for image in Baseline_datetimes]
    print('Flood image:')
    print(Flood_datetime)
    
    hdf5_stack_file=Create_dhf5_stack_file(Flood_datetime,
                                           Baseline_datetimes_refined,
                                           Preprocessing_dir,
                                           overwrite)
    
    print ('All information from SAR imagery are stored at {}'.format(hdf5_stack_file))
    Plot_SAR_Stack(hdf5_stack_file,projectfolder)
    #_delete_intermediate_files(Output_dir)
    
    return hdf5_stack_file
