#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pandas as pd
import datetime
import platform


from floodpy.utils.read_AOI import Coords_to_geojson, Input_vector_to_geojson
from floodpy.utils.geo_utils import create_polygon
from floodpy.Download.Query_Sentinel_1_products import query_Sentinel_1
from floodpy.Download.Sentinel_1_download import download_S1_data
from floodpy.Download.Sentinel_1_orbits_download import download_S1_POEORB_orbits
from floodpy.Preprocessing_S1_data.DEM_funcs import calc_slope_mask
# Visualization
from floodpy.Visualization.plot_ERA5_data import plot_ERA5

from floodpy.Download.Download_ERA5_precipitation import Get_ERA5_data
from floodpy.Download.Download_LandCover import worldcover
from floodpy.Preprocessing_S1_data.Preprocessing_S1_data import Run_Preprocessing
from floodpy.Floodwater_delineation.Statistical_approach.calc_t_scores import Calculate_t_scores
from floodpy.Floodwater_delineation.Statistical_approach.Classification import Calc_flood_map

def is_platform_linux():
    return platform.system() == "Linux"

class FloodwaterEstimation:
    """ 
    Processing workflow for floodwater estimation from satellite remote sensing data.
    """
    
    def __init__(self, params_dict:dict):

        # Check if we are working in Lixun OS

        if not is_platform_linux:
            print(" We support only processing in Linux environment!")

        # Project Definition
        self.projectfolder  = params_dict['projectfolder']
        self.src            = params_dict['src_dir']
        self.gpt            = params_dict['GPTBIN_PATH']
        self.snap_orbit_dir = params_dict['snap_orbit_dir']
        
        # Pre-flood and Flood temporal information
        self.pre_flood_datetime_start = datetime.datetime.strptime(params_dict['pre_flood_start'],'%Y%m%dT%H%M%S')
        self.pre_flood_datetime_end   = datetime.datetime.strptime(params_dict['pre_flood_end'],'%Y%m%dT%H%M%S')
        self.flood_datetime_start     = datetime.datetime.strptime(params_dict['flood_start'],'%Y%m%dT%H%M%S')
        self.flood_datetime_end       = datetime.datetime.strptime(params_dict['flood_end'],'%Y%m%dT%H%M%S')
   
        # Flood spatial information
        self.AOI_File       = params_dict['AOI_File']
        self.LATMIN         = float(params_dict['LATMIN'])
        self.LONMIN         = float(params_dict['LONMIN'])
        self.LATMAX         = float(params_dict['LATMAX'])
        self.LONMAX         = float(params_dict['LONMAX'])
        
        # Data access and processing
        self.relOrbit            = params_dict['relOrbit']
        self.min_map_area        = float(params_dict['minimum_mapping_unit_area_m2'])
        self.pixel_m2            = 100.0
        self.CPU                 = int(params_dict['CPU'])
        self.RAM                 = params_dict['RAM']
        self.Copernicus_username = params_dict['Copernicus_username']
        self.Copernicus_password = params_dict['Copernicus_password']
        
        #-------------------------------------------------------------------
        #-- Creating directory structure
        #-------------------------------------------------------------------
        if not os.path.exists(self.snap_orbit_dir): os.makedirs(self.snap_orbit_dir)
        if not os.path.exists(self.projectfolder): os.mkdir(self.projectfolder)
        self.graph_dir = os.path.join(self.src,'Preprocessing_S1_data/Graphs')
        assert os.path.exists(self.graph_dir)
        assert os.path.exists(self.gpt)

        self.S1_dir = os.path.join(self.projectfolder,'Sentinel_1_data')
        
        self.ERA5_dir = os.path.join(self.projectfolder,'ERA5')
        self.Results_dir = os.path.join(self.projectfolder, 'Results')
        self.temp_export_dir = os.path.join(self.S1_dir,"S1_orbits")
        self.S2_dir = os.path.join(self.projectfolder,'Sentinel_2_data')
        self.Land_Cover = os.path.join(self.projectfolder, "Land_Cover")
        self.directories = [self.projectfolder,
                            self.ERA5_dir,
                            self.S1_dir,
                            self.Results_dir,
                            self.temp_export_dir,
                            self.S2_dir,
                            self.Land_Cover,]
        
        [os.mkdir(directory) for directory in self.directories if not os.path.exists(directory)]

        #-------------------------------------------------------------------
        #-- Create AOI polygon
        #-------------------------------------------------------------------
        if self.AOI_File.upper() == "NONE":
            # creates a geojson file with the bounding box of the 
            # provided Lons, Lats

            self.bbox           = [self.LONMIN,
                                   self.LATMIN,
                                   self.LONMAX,
                                   self.LATMAX,] 

            self.geojson_bbox     = Coords_to_geojson(self.bbox,
                                                    self.projectfolder,
                                                    'bbox_AOI.geojson')
        else:
            # reads the provided vector file, calculated the lats,lons of the 
            # bounding box and writes a geojson file.
            
            self.bbox, self.geojson_S1 = Input_vector_to_geojson(self.AOI_File,
                                                                 self.projectfolder,
                                                                 'AOI.geojson')
            self.geojson_bbox     = Coords_to_geojson(self.bbox,
                                                    self.projectfolder,
                                                    'bbox_AOI.geojson')
    
    def download_landcover_data(self):
        self.lc_mosaic_filename, self.LC_CATEGORIES, self.LC_COLORBAR = worldcover(self.geojson_bbox, self.Land_Cover)

    def download_ERA5_Precipitation_data(self):

        self.precipitation_df = Get_ERA5_data(ERA5_variables = ['total_precipitation',],
                                            start_datetime = self.pre_flood_datetime_start,
                                            end_datetime = self.flood_datetime_end ,
                                            bbox = self.bbox,
                                            ERA5_dir = self.ERA5_dir )

        print("Precipitation data can be found at {}".format(self.ERA5_dir))   
    
    def plot_ERA5_precipitation_data(self):
        self.era5_fig = plot_ERA5(self)

    def query_S1_data(self):
        self.query_S1_df, self.flood_candidate_dates = query_Sentinel_1(self)

    def sel_S1_data(self, sel_flood_date):
        if pd.to_datetime(sel_flood_date) not in self.flood_candidate_dates:
            print('Please select one of the available dates for flood mapping: {}'.format(self.flood_candidate_dates))

        self.flood_datetime = sel_flood_date
        self.flood_datetime_str = pd.to_datetime(self.flood_datetime).strftime('%Y%m%dT%H%M%S')
        orbit_direction_sel = self.query_S1_df.loc[sel_flood_date]['orbitDirection']
        rel_orbit_sel = self.query_S1_df.loc[sel_flood_date]['relativeOrbitNumber']
        self.query_S1_sel_df = self.query_S1_df[self.query_S1_df["orbitDirection"].isin([orbit_direction_sel])]
        self.query_S1_sel_df = self.query_S1_sel_df[self.query_S1_sel_df["relativeOrbitNumber"].isin([rel_orbit_sel])]
        self.query_S1_sel_df['geometry'] = self.query_S1_sel_df.GeoFootprint.apply(create_polygon)

    def download_S1_GRD_products(self):

        download_S1_data(self)

    def download_S1_orbits(self):

        download_S1_POEORB_orbits(self)

    def create_S1_stack(self, overwrite = False):

        self.Preprocessing_dir = os.path.join(self.projectfolder, 'Preprocessed_{}'.format(self.flood_datetime_str))
        if not os.path.exists(self.Preprocessing_dir): os.mkdir(self.Preprocessing_dir) 
        self.S1_stack_filename = os.path.join(self.Preprocessing_dir,'S1_stack_{}.nc'.format(self.flood_datetime_str))
        self.DEM_filename = os.path.join(self.Preprocessing_dir,'DEM.nc')
        self.LIA_filename = os.path.join(self.Preprocessing_dir,'LIA.nc')

        Run_Preprocessing(self, overwrite = overwrite) 


    def calc_slope(self, slope_thres = 10):
        self.slope_thres = slope_thres
        self.DEM_slope_filename = os.path.join(self.Preprocessing_dir,'DEM_slope.nc')
        calc_slope_mask(self)

    def calc_t_scores(self):

        self.polar_comb = 'VV_VH_dB'
        self.t_score_filename = os.path.join(self.Preprocessing_dir,'t_scores_{}_{}.nc'.format(self.polar_comb,
                                                                                               self.flood_datetime_str))
        Calculate_t_scores(self)    

    def get_reference_water_map(self):
        pass

    def calc_floodmap_dataset(self):
        
        self.Flood_map_dataset_filename = os.path.join(self.Results_dir, 'Flood_map_dataset_{}.nc'.format(self.flood_datetime_str))
        Calc_flood_map(self)