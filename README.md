# <img src="https://github.com/kleok/FLOODPY/blob/main/figures/Floodpy_logo.png" width="58"> FLOODPY - FLOOD PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOODPY)
[![Release](https://img.shields.io/badge/Release-0.2.0-brightgreen)](https://github.com/kleok/FLOODPY)
[![Facebook](https://img.shields.io/badge/Group-Flompy-yellowgreen.svg)](https://www.facebook.com/groups/876299509742954)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/kleok/FLOODPY/issues)
[![Documentation](https://readthedocs.org/projects/floodpy/badge/?version=latest)](https://floodpy.readthedocs.io/en/latest/)

## Introduction

The FLOod Mapping PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOODPY's floodwater maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOODPY/blob/main/figures/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

### 1.1 Install snap gpt including [Sentinel-1 toolbox](https://step.esa.int/main/download/snap-download/previous-versions/)

For the installation of ESA SNAP you can run the automated script [aux/install_snap.sh](https://github.com/kleok/FLOODPY/blob/main/aux/install_snap.sh) for downloading and installing the official Linux installer from the official ESA repository. To install SNAP run the following commands:

```bash
chmod +x install_snap.sh
./install_snap.sh
```

### 1.2 Account setup for downloading Sentinel-1 acquisitions
Sentinel-1 data download functionality require user credentials. More information [here](https://scihub.copernicus.eu/)

Please create an account
Install aria using thw following command:
```sudo apt-get install aria2```

### 1.3 Account setup for downloading global atmospheric model data
ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS). You have to create a new account on the CDS website if you don't own a user account yet. After the creation of your profile, you will find your user id (UID) and your personal API Key. Now, a ```.cdsapirc``` file must be created under your ```HOME``` directory with the following information:
```
url: https://cds.climate.copernicus.eu/api/v2
key: UID:personal API Key
```
In case you dont want to create the .cdsapirc file manually, you can run [aux/install_CDS_key.sh](https://github.com/kleok/FLOODPY/blob/main/aux/install_CDS_key.sh) script as follows:

```bash
chmod +x install_CDS_key.sh
./install_CDS_key.sh
```
More details on CDSAPI can be found [here](https://cds.climate.copernicus.eu/api-how-to).

### 1.4 Download FLOODPY
First you have to download FLOODPY toolbox using the following command
```git clone https://github.com/kleok/FLOODPY.git```

### 1.5 Create python environment for FLOODPY

FLOODPY is written in Python3 and relies on several Python modules. You can install them by using conda or pip.

- Using **conda**
Create a new conda environement with required packages using the the file [FLOODPY_env.yml](https://github.com/kleok/FLOODPY/blob/main/FLOODPY_env.yml).

```
conda env create -f ~/FLOODPY/FLOODPY_env.yml
```

- Using **pip**
  You can install python packages using [setup.py](https://github.com/kleok/FLOODPY/blob/main/setup.py)
  
```
cd ~/FLOODPY
pip install .
```

### 1.6 Set environmental variables

on GNU/Linux, append to .bashrc file:
```
export FLOODPY_HOME=~/FLOODPY
export PYTHONPATH=${PYTHONPATH}:${FLOODPY_HOME}
export PATH=${PATH}:${FLOODPY_HOME}/floodpy
```

## 2. Running FLOODPY
[FLOODPYapp.py]("https://github.com/kleok/FLOODPY/blob/main/floodpy/FLOODPYapp.py")

FLOODPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. FLOODPYapp.py includes the functionalities for FLOODPY's routine processing for generating floodwater maps. User should provide the following information at configuration file FLOODPYapp_template.cfg
We suggest you to can have a look at the plots for each Sentinel-1 image (located at projectfolder) to find out if you have a considerable decrease of backscatter in the flood image with respect to the baseline images. If you are able to identify a decrease of backscatter in the flood image (darker tones), then you can expect that FLOODPY will generate a useful floodwater map. In cases that you have similar or bigger backscatter values of flood image with respect to baseline images (due to complex backscatter mechanisms) FLOODPY`s results cannot be trusted.
```
#######################################
#             CONFIGURATION FILE      #
#######################################

#######################################
# A. Project Definition #
#######################################
#A1. The name of your project withough special characters.
Projectname = Palamas

#A2. The location that everything is going to be saved. Make sure 
#        you have enough free space disk on the specific location.
projectfolder = /RSL03/FLOODPY_palamas

#A3. The location of FLOODPY code 
src_dir = /RSL03/FLOODPY_0.4/FLOODPY/floodpy

#A4. SNAP ORBIT DIRECTORY
snap_dir = /home/kleanthis/.snap/auxdata/Orbits/Sentinel-1

#A5. SNAP GPT full path
GPTBIN_PATH=/home/kleanthis/bin/snap8/snap/bin/gpt

##########################################
# B. Flood event temporal information  #
##########################################
#---------------------- Instructions------------------------
# Your have to provide the datetime of your flood event. Make sure that
# a flood event took place at your provided datetime. 
# Based on your knowledge you can change [before_flood_days] in order
# to create a biggest 
# Sentinel-1 image that is going to be used to extract flood information
# will be between Flood_datetime and Flood_datetime+after_flood_days
# the closest Sentinel-1 to the Flood_datetime is picked
#--------------------------------------------------------
# B1. The datetime of flood event (Format is YYYYMMDDTHHMMSS)
Flood_datetime = 20200921T030000

# B2. Days before flood event for baseline stack construction
before_flood_days = 60

# B3. Days after flood event
after_flood_days = 3

#########################################
# C. Flood event spatial information #
#########################################
#---------------------- Instructions------------------------
# You can provide AOI VECTOR FILE or AOI BBOX. 
# Please ensure that your AOI BBOX has dimensions smaller than 100km x 100km
# If you provide AOI VECTOR, AOI BBOX parameters will be ommited
#-In case you provide AOI BBOX coordinates, set  AOI_File = None
#--------------------------------------------------------
# C1. AOI VECTOR FILE (if given AOI BBOX parameters can be ommited)
AOI_File = /home/kleanthis/bin/FLOODPY/tests/Palamas_AOI.geojson

# C2. AOI BBOX (WGS84)
LONMIN=22.02
LATMIN=39.38
LONMAX=22.245
LATMAX=39.518

###################################
# D. Precipitation information #
###################################
#---------------------- Instructions------------------------
#  Based on your knowledge, provide information related to the 
# accumulated precipitation that is required in order a flooding to occur. 
# These particular values will be used to classify Sentinel-1 images
#  which images correspond to flood and non-flood conditions.
#--------------------------------------------------------
# D1. number of consequent days that precipitation will be accumulated.
#       before each Sentinel-1 acquisition datetime
days_back = 5

# D2. The threshold of acculated precipitation
accumulated_precipitation_threshold = 40

########################################
# E.  Data access and processing    #
########################################
#E1. The number of Sentinel-1 relative orbit. The default 
#       value is Auto. Auto means that the relative orbit that has
#       the Sentinel-1 image closer to the Flood_datetime is selected. 
relOrbit=Auto

#E2. The minimum mapping unit area in square meters
minimum_mapping_unit_area_m2=4000

#E3. Computing resources to employ
CPU=8
RAM=20G

#E4. Credentials for Sentinel-1/2 downloading
scihub_username = ******
scihub_password = ******
```

After the setup of the configuration file you can use the default recipe script FLOODPYapp.py to run the following following individual steps that will
automatically run for the selected AOI:

### 2.1. Download Precipitation data from ERA5.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Download_Precipitation_data
```

### 2.2. Download Sentinel 1 data.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Download_S1_data
```

### 2.3. Preprocessing Sentinel 1 data.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Preprocessing_S1_data
```

### 2.4. Sentinel 1 statistical analysis.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Statistical_analysis
```

### 2.5. And at last the floodwater classification step. At this point the result of the estimated flooded region is exported.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Floodwater_classification
```

If the flood was on an agricultural region you can also run the following steps to estimate the amount of the damaged fields by performing delineation (with a methodology based on Yan & Roy, 2014 and a pretrained Unet delineation network) and active-inactive field classification based on NDVI timeseries with Sentinel 2 data. For more information check at Gounari et al. 2022 bellow.

### 2.6. Download Sentinel 2 multispectral data (Optional). 

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Download_S2_data
```

### 2.7. Run crop delineation and field classification (Optional, requires 6).

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Crop_delineation
```

## 3. Documentation and citation
Algorithms implemented in the software are described in detail at our publications. If FLOODPY was useful for you, we encourage you to cite the following work.

- Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

- Gounari 0., Falagas A., Karamvasis K., Tsironis V., Karathanassi V., Karantzalos K.: Floodwater Mapping & Extraction of Flood-Affected Agricultural Fields. Living Planet Symposium Bonn 23-27 May 2022. https://drive.google.com/file/d/1HiGkep3wx45gAQT6Kq34CdECMpQc8GUV/view?usp=sharing

- Zotou I., Karamvasis K., Karathanassi V., Tsihrintzis V.: Sensitivity of a coupled 1D/2D model in input parameter variation exploiting Sentinel-1-derived flood map. 7th IAHR Europe Congress. September 7-9, 2022. Page 247 at https://www.iahreuropecongress.org/PDF/IAHR2022_ABSTRACT_BOOK.pdf 

## 4. Contact us
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recommendations. Any help is very welcome! :heart:

FLOODPY Team: [Kleanthis Karamvasis](https://github.com/kleok), [Ioanna Zotou](https://www.researchgate.net/profile/Ioanna-Zotou), [Alekos Falagas](https://github.com/alekfal), [Olympia Gounari](https://github.com/Olyna), [Vasileios Tsironis](https://github.com/tsironisbi), [Markos Mylonas](https://github.com/mylonasma), [Pavlos Alexantonakis](https://www.linkedin.com/in/pavlos-alexantonakis)

