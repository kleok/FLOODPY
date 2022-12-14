#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import datetime
import time
import argparse

from floodpy.utils.read_template_file import read_template
from floodpy.utils.read_AOI import Coords_to_geojson, Input_vector_to_geojson
from floodpy.Download.Sentinel_1_download import Download_S1_data
from floodpy.Download.Download_orbits import download_orbits
from floodpy.Download.Download_ERA5_precipitation import Get_ERA5_data
from floodpy.Preprocessing_S1_data.Classify_S1_images import Get_images_for_baseline_stack
from floodpy.Preprocessing_S1_data.Preprocessing_S1_data import Run_Preprocessing
from floodpy.Statistical_analysis.Generate_aux import get_S1_aux
from floodpy.Statistical_analysis.calc_t_scores import Calc_t_scores
from floodpy.Floodwater_classification.Classification import Get_flood_map
# from Validation.Validation import Accuracy_metrics_calc
# from Validation.EMS_preparation import rasterize

# Agriculture fields extraction
from floodpy.Download.Sentinel_2_download import Download_S2_data
from floodpy.Preprocessing_S2_data.sts import sentimeseries
from floodpy.Crop_delineation.delineate import CropDelineation
from floodpy.Crop_delineation_unet.Pretrained_networks import Crop_delineation_Unet

print('FLOod Mapping PYthon toolbox')
print('Copyright (c) 2021-2022 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Technical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

##########################################################################            
STEP_LIST = [
    'Download_Precipitation_data',
    'Download_S1_data',
    'Preprocessing_S1_data',
    'Statistical_analysis',
    'Floodwater_classification',
    'Download_S2_data',
    'Crop_delineation',]

##########################################################################
STEP_HELP = """Command line options for steps processing with \n names are chosen from the following list:

{}

In order to use either --start or --dostep, it is necessary that a
previous run was done using one of the steps options to process at least
through the step immediately preceding the starting step of the current run.
""".format("\n".join(STEP_LIST))

##########################################################################
EXAMPLE = """example:
  FLOMPYapp.py FLOMPYapp.cfg            #run with FLOMPYapp.cfg template
  FLOMPYapp.py -h / --help             #help
  FLOMPYapp.py -H                      #print    default template options

  # Run with --start/stop/dostep options
  FLOMPYapp.py LPS2022.cfg --dostep Download_Precipitation_data  #run at step 'Download_Precipitation_data' only
  FLOMPYapp.py LPS2022.cfg --end download_S2_data    #end after step 'download_S2_data'
"""
##########################################################################
REFERENCE = """
     References:
         
     Karamvasis K., Karathanassi V. FLOMPY: An Open-Source Toolbox for 
     Floodwater Mapping Using Sentinel-1 Intensity Time Series. 
     Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 
     
     Gounari 0., Falagas A., Karamvasis K., Tsironis V., Karathanassi V.,
     Karantzalos K.: Floodwater Mapping & Extraction of Flood-Affected 
     Agricultural Fields. Living Planet Symposium Bonn 23-27 May 2022.      
     https://drive.google.com/file/d/1HiGkep3wx45gAQT6Kq34CdECMpQc8GUV/view?usp=sharing

     Zotou I., Karamvasis K., Karathanassi V., Tsihrintzis V.: Sensitivity of a coupled 1D/2D 
     model in input parameter variation exploiting Sentinel-1-derived flood map. 
     7th IAHR Europe Congress. September 7-9, 2022. Page 247 at 
     https://www.iahreuropecongress.org/PDF/IAHR2022_ABSTRACT_BOOK.pdf
     
"""

def create_parser():
    parser = argparse.ArgumentParser(description='FLOod Mapping PYthon toolbox (FLOMPY)',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=REFERENCE+'\n'+EXAMPLE)

    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.')
    parser.add_argument('-H', dest='print_template', action='store_true',
                        help='print the default template file and exit.')
    parser.add_argument('--noplot', dest='plot', action='store_false',
                        help='do not plot results at the end of the processing.')
    step = parser.add_argument_group('steps processing (start/end/dostep)', STEP_HELP)
    
    step.add_argument('--start', dest='startStep', metavar='STEP', default=STEP_LIST[0],
                      help='start processing at the named step, default: {}'.format(STEP_LIST[0]))
    step.add_argument('--end','--stop', dest='endStep', metavar='STEP',  default=STEP_LIST[-1],
                      help='end processing at the named step, default: {}'.format(STEP_LIST[-1]))
    step.add_argument('--dostep', dest='doStep', metavar='STEP',
                      help='run processing at the named step only')
    
    return parser

def cmd_line_parse(iargs=None):
    """Command line parser."""
    parser = create_parser()
    inps = parser.parse_args(args=iargs)


    # print default template
    if inps.print_template:
        default_template_file = os.path.join(os.path.dirname(__file__), 'FLOMPYapp.cfg')
        raise SystemExit(open(default_template_file, 'r').read())

    if (not inps.customTemplateFile):
        
        parser.print_usage()
        print(EXAMPLE)
        msg = "ERROR: no template file found! It requires:"
        msg += "\n  input a custom template file"
        print(msg)
        raise SystemExit()

    # invalid input of custom template
    if inps.customTemplateFile:
        inps.customTemplateFile = os.path.abspath(inps.customTemplateFile)
        if not os.path.isfile(inps.customTemplateFile):
            raise FileNotFoundError(inps.customTemplateFile)
            
    
    # check input --start/end/dostep
    for key in ['startStep', 'endStep', 'doStep']:
        value = vars(inps)[key]
        if value and value not in STEP_LIST:
            msg = 'Input step not found: {}'.format(value)
            msg += '\nAvailable steps: {}'.format(STEP_LIST)
            raise ValueError(msg)

    # ignore --start/end input if --dostep is specified
    if inps.doStep:
        inps.startStep = inps.doStep
        inps.endStep = inps.doStep

    # get list of steps to run
    idx0 = STEP_LIST.index(inps.startStep)
    idx1 = STEP_LIST.index(inps.endStep)
    if idx0 > idx1:
        msg = 'input start step "{}" is AFTER input end step "{}"'.format(inps.startStep, inps.endStep)
        raise ValueError(msg)
    inps.runSteps = STEP_LIST[idx0:idx1+1]

    # message - processing steps
    if len(inps.runSteps) > 0:
        print('--RUN-at-{}--'.format(datetime.datetime.now()))
        print('Run routine processing with {} on steps: {}'.format(os.path.basename(__file__), inps.runSteps))
        if inps.doStep:
            Remaining_steps = STEP_LIST[idx0+1:]
            print('Remaining steps:')
            [print(step) for step in Remaining_steps]
            print('--dostep option enabled, disable the plotting at the end of the processing.')
            inps.plot = False

    print('-'*50)
    return inps

class FloodwaterEstimation:
    """ Routine processing workflow for floodwater estimation from satellite
    remote sensing data.
    """

    def __init__(self, customTemplateFile=None, workDir=None):
        """customTemplateFile and scihub account is required.""" 
        self.customTemplateFile = customTemplateFile
        self.cwd = os.path.abspath(os.getcwd())

    def startup(self):
        """The starting point of the workflow. It runs everytime. 
        - get and read template(s) options
        - create geojson file
        - creates directory structure
        
        """
    
        #-- Reading configuration parameters
        template_file = os.path.join(self.cwd, self.customTemplateFile)
        self.template_dict=read_template(template_file)
        [print(key,':',value) for key, value in self.template_dict.items()]
        
        # Project Definition
        self.projectname    = self.template_dict['Projectname']
        self.projectfolder  = self.template_dict['projectfolder']
        self.scriptsfolder  = self.template_dict['src_dir']
        self.gptcommand     = self.template_dict['GPTBIN_PATH']
        self.snap_dir       = self.template_dict['snap_dir']
        
        # Flood event temporal information
        self.flood_datetime = datetime.datetime.strptime(self.template_dict['Flood_datetime'],'%Y%m%dT%H%M%S')
        self.baseline_days  = int(self.template_dict['before_flood_days'])
        self.after_flood_days = int(self.template_dict['after_flood_days'])
        
        # Flood event spatial information
        self.AOI_File       = self.template_dict['AOI_File']
        self.LATMIN         = float(self.template_dict['LATMIN'])
        self.LONMIN         = float(self.template_dict['LONMIN'])
        self.LATMAX         = float(self.template_dict['LATMAX'])
        self.LONMAX         = float(self.template_dict['LONMAX'])

        #-- Creating directory structure
        if not os.path.exists(self.snap_dir): os.makedirs(self.snap_dir)
        if not os.path.exists(self.projectfolder): os.mkdir(self.projectfolder)
        self.graph_dir = os.path.join(self.scriptsfolder,'Preprocessing_S1_data/Graphs')
        assert os.path.exists(self.graph_dir)
        assert os.path.exists(self.gptcommand)

        self.S1_GRD_dir = os.path.join(self.projectfolder,'Sentinel_1_GRD_imagery')
        self.ERA5_dir = os.path.join(self.projectfolder,'ERA5')
        self.Preprocessing_dir = os.path.join(self.projectfolder, 'Preprocessed')
        self.Results_dir = os.path.join(self.projectfolder, 'Results')
        self.temp_export_dir = os.path.join(self.S1_GRD_dir,"S1_orbits")
        self.S2_dir = os.path.join(self.projectfolder,'Sentinel_2_imagery')
        self.Land_Cover = os.path.join(self.projectfolder, "Land_Cover")
        self.Results_crop_delineation =  os.path.join(self.projectfolder, "Results_crop_delineation")
        self.directories = [self.projectfolder,
                            self.ERA5_dir,
                            self.S1_GRD_dir,
                            self.Preprocessing_dir,
                            self.Results_dir,
                            self.temp_export_dir,
                            self.S2_dir,
                            self.Land_Cover,
                            self.Results_crop_delineation]
        
        [os.mkdir(directory) for directory in self.directories if not os.path.exists(directory)]

        
        if self.AOI_File.upper() == "NONE":
            self.bbox           = [self.LONMIN,
                                   self.LATMIN,
                                   self.LONMAX,
                                   self.LATMAX,] 

            self.geojson_S1     = Coords_to_geojson(self.bbox,
                                                    self.projectfolder,
                                                    '{}_AOI.geojson'.format(self.projectname))
        else:
            self.bbox, self.geojson_S1 = Input_vector_to_geojson(self.AOI_File,
                                                                 self.projectfolder,
                                                                 '{}_AOI.geojson'.format(self.projectname))

        #Precipitation information
        self.days_back     = int(self.template_dict['days_back'])
        self.rain_thres     = float(self.template_dict['accumulated_precipitation_threshold'])
        
        # Data access and processing
        self.relOrbit       = self.template_dict['relOrbit']
        self.min_map_area   = float(self.template_dict['minimum_mapping_unit_area_m2'])
        self.CPU            = int(self.template_dict['CPU'])
        self.RAM            = self.template_dict['RAM']
        self.credentials    = {self.template_dict['scihub_username']:self.template_dict['scihub_password']}
        
        
        # Define start and end time of analysis
        self.start_datetime = self.flood_datetime-datetime.timedelta(days=self.baseline_days)
        self.end_datetime = self.flood_datetime+datetime.timedelta(days=self.after_flood_days)                               
        self.Start_time=self.start_datetime.strftime("%Y%m%d")
        self.End_time=self.end_datetime.strftime("%Y%m%d")

        return 0
    
    def run_download_Precipitation_data(self, step_name):

        Get_ERA5_data(ERA5_variables = ['total_precipitation',],
                      start_datetime = self.start_datetime,
                      end_datetime = self.end_datetime,
                      bbox = self.bbox,
                      ERA5_dir = self.ERA5_dir )

        print("Precipitation data can be found at {}".format(self.ERA5_dir))
        return 0    
    
    def run_download_S1_data(self, step_name):
        
        Download_S1_data(scihub_accounts = self.credentials,
                          S1_GRD_dir = self.S1_GRD_dir,
                          geojson_S1 = self.geojson_S1,
                          Start_time = self.Start_time,
                          End_time = self.End_time,
                          relOrbit = self.relOrbit,
                          flood_datetime = self.flood_datetime,
                          time_sleep=60, # 1 minute
                          max_tries=100)
        
        download_orbits(snap_dir = self.snap_dir,
                temp_export_dir = self.temp_export_dir,
                S1_GRD_dir = self.S1_GRD_dir)
        
        print("Sentinel-1 data and orbit information have been successfully downloaded")
        
        return 0
    
    def run_preprocessing_S1_data(self, step_name):
        
        Get_images_for_baseline_stack(projectfolder = self.projectfolder,
                                      ERA5_dir = self.ERA5_dir,
                                      S1_GRD_dir = self.S1_GRD_dir,
                                      Start_time = self.Start_time,
                                      End_time = self.End_time,
                                      flood_datetime = self.flood_datetime,
                                      days_back = self.days_back,
                                      rain_thres=self.rain_thres)
        
        Run_Preprocessing(projectfolder = self.projectfolder,
                          gpt_exe = self.gptcommand,
                          graph_dir = self.graph_dir,
                          S1_GRD_dir = self.S1_GRD_dir,
                          geojson_S1 = self.geojson_S1,
                          Preprocessing_dir = self.Preprocessing_dir) 
        
        return 0 

    
    def run_multitemporal_statistics(self, step_name):
        
        get_S1_aux (self.Preprocessing_dir)
        
        Calc_t_scores(projectfolder = self.projectfolder,
                      Results_dir = self.Results_dir,
                      S1_GRD_dir = self.S1_GRD_dir,
                      Preprocessing_dir = self.Preprocessing_dir)
        
        return 0  
    
    def run_get_flood_map(self, step_name):
        
        Get_flood_map(Preprocessing_dir = self.Preprocessing_dir,
                      Results_dir = self.Results_dir,
                      Projectname = self.projectname,
                      num_cores = self.CPU,
                      fast_flag = True,
                      minimum_mapping_unit_area_m2=self.min_map_area)
        return 0
    
    def plot_results(self, print_aux, plot):
        pass

    def run_download_S2_data(self, step_name):

        Download_S2_data(
                        AOI = self.geojson_S1,
                        user = list(self.credentials.keys())[0],
                        passwd = list(self.credentials.values())[0],
                        Start_time = self.Start_time,
                        End_time = self.End_time,
                        write_dir = self.S2_dir,
                        product = 'S2MSI2A',
                        download = False,
                        cloudcoverage = 100,
                        to_file = True)

        print("Sentinel-2 data have been successfully downloaded")
        
        return 0

    def run_crop_delineation(self, step_name):
        """
        TODO: Use a functionallity to find zip and unzipped data -> Done in #5
        TODO: remove orbits if pixels with nan values are above a certain 
        threshold -> Done in #5
        """
        
        # Get data
        eodata = sentimeseries("S2-timeseries")
        
        eodata.find(self.S2_dir)
        eodata.sort_images(date=True)
        
        # Get VIs
        eodata.getVI("NDVI")
        
        # Clip data
        eodata.clipbyMask(self.geojson_S1, band = 'B02', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'B03', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'B04', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'B08', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'B11', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'B12', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = 'SCL', resize = True, new ="masked")
        eodata.clipbyMask(self.geojson_S1, band = "NDVI", new ="masked")
        
        self.S2timeseries = eodata
        

        # create obj
        parcels = CropDelineation(eodata = self.S2timeseries,
                                  dst_path = self.Results_crop_delineation,
                                  lc_path = self.Land_Cover)
        

        # corine and scl masks
        parcels.lc_mask(aoi = self.geojson_S1, write=True)
        parcels.cloud_mask(write=True)

        # edge intensity (0-100) map
        parcels.edge_probab_map(write=True)

        # create ndvi series and apply any created mask (clouds, towns)
        parcels.create_series(write=False)

        # fill values removed by cloud mask
        parcels.crop_probab_map(
            cube = parcels.ndviseries,
            cbmeta = parcels.ndviseries_meta,
            write=True,
            )

        # edges, active and inactive fields Map
        parcels.active_fields()

        # Pretrained 
        Crop_delineation_Unet(model_name = 'UNet3',
                            model_dir = self.scriptsfolder,
                            BASE_DIR = self.S2_dir,
                            results_pretrained = self.Results_crop_delineation,
                            force_cpu = True)

        # Delineate fields: Combine EPM and UNet
        parcels.delineation(self.geojson_S1, os.path.join(self.Results_crop_delineation,
        'UNet3_crop_delineation.tif'))

        # Characterize Cultivated and Not-Cultivated fields
        parcels.flooded_fields(os.path.join(self.Results_dir,'Flood_map_{}.tif'.format(self.projectname)))

        return 0

    def run(self, steps=STEP_LIST, plot=True):
        # run the chosen steps
        for sname in steps:
            print('\n\n******************** step - {} ********************'.format(sname))
            
            if sname == 'Download_Precipitation_data':
                self.run_download_Precipitation_data(sname)

            elif sname == 'Download_S1_data':
                self.run_download_S1_data(sname)

            elif sname == 'Preprocessing_S1_data':
                self.run_preprocessing_S1_data(sname)
                
            elif sname == 'Statistical_analysis':
                self.run_multitemporal_statistics(sname)

            elif sname == 'Floodwater_classification':
                self.run_get_flood_map(sname)
            
            elif sname == 'Download_S2_data':
                self.run_download_S2_data(sname)
                
            elif sname == 'Crop_delineation':
                self.run_crop_delineation(sname)
        
        # plot result (show aux visualization message more multiple steps processing)
        print_aux = len(steps) > 1
        self.plot_results(print_aux=print_aux, plot=plot)

        # go back to original directory
        #print('Go back to directory:', self.cwd)
        os.chdir(self.cwd)

        # message
        msg = '\n################################################'
        msg += '\n   Normal end of FLOMPY processing!'
        msg += '\n################################################'
        print(msg)
        return


##########################################################################
def main(iargs=None):
    start_time = time.time()
    inps = cmd_line_parse(iargs)

    app = FloodwaterEstimation(inps.customTemplateFile)
    app.startup()
    if len(inps.runSteps) > 0:
        app.run(steps=inps.runSteps, plot=inps.plot)

    # Timing
    m, s = divmod(time.time()-start_time, 60)
    print('Time used: {:02.0f} mins {:02.1f} secs\n'.format(m, s))
    return

###########################################################################################
if __name__ == '__main__':
    print("fvaf")
    main()
    
