# <img src="https://github.com/kleok/FLOMPY/blob/main/Flompy_logo.png" width="58"> FLOMPY - FLOod Mapping PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOMPY)
[![Release](https://img.shields.io/badge/Release-0.1.0-brightgreen.svg)](https://github.com/kleok/FLOMPY)
[![Facebook](https://img.shields.io/badge/Group-Flompy-yellowgreen.svg)](https://www.facebook.com/groups/876299509742954)

## Introduction

The FLOod Mapping PYthon toolbox is a new fully automatic, free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting
the FLompy flood maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOMPY/blob/main/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

### 1.1 Create python environment 
FLOMPY is written in Python3 and relies on several Python modules, check the requirements.txt file for details. We recommend using conda to install the python environment and the prerequisite packages, because of the convenient management.

### 1.2 Install snap gpt including [Sentinel-1 toolbox](https://step.esa.int/main/download/snap-download/)

### 1.3 Account setup for downloading Sentinel-1 acquisitions
Sentinel-1 data download functionality require user credentials. More information [here](https://scihub.copernicus.eu/)

### 1.4 Account setup for downloading global atmospheric model data
ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS), create a new account on the CDS website if you don't own a user account yet. On the profile, you will find your user id (UID) and your personal API Key. Create a file .cdsapirc under your home directory and add the following information:
```
url: https://cds.climate.copernicus.eu/api/v2
key: UID:personal API Key
```
CDS API is needed to auto-download ERA5 ECMWF data: conda install -c conda-forge cdsapi
More details on CDSAPI can be found [here](https://cds.climate.copernicus.eu/api-how-to).

### 1.5 Download FLOMPY
git clone https://github.com/kleok/FLOMPY.git

on GNU/Linux, append to .bashrc file:
```
export FLOMPY_HOME=~/FLOMPY
export PYTHONPATH=${PYTHONPATH}:${FLOMPY_HOME}
export PATH=${PATH}:${FLOMPY_HOME}
```
## 2. Running Flompy
S1FloodwaterApp.py or S1FloodwaterApp_EMSR.py

FLOMPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. In case of S1FloodwaterApp_EMSR the user should download EMS product in order to compare FLOMPY and EMS results. The user should provide the following information at the Set parameter section in S1FloodwaterApp.py or S1FloodwaterApp_EMSR.py. 
```
src_dir='directory of the flompy'
projectfolder='project directory'

snap_dir = 'path to Sentinel-1 orbit directory for snap processing'
#example: '/home/kleanthis/.snap/auxdata/Orbits/Sentinel-1'

gpt_exe = 'path to gpt exe'
#example:'/home/kleanthis/bin/snap8/snap/bin/gpt'
    
# example datetime
flood_datetime=datetime.datetime(2021,7,16,5,00,00) 

# example boundary coordinates
ulx=7.14
uly=50.35
lrx=7.48
lry=50.13

# Auto option selects the orbit to minimize the distance between defined
# flood date and SAR datetime acquisition
# user can also select specific relative orbit number
relOrbit='Auto' 

# cumulative rain in mm for the last 5 days 
rain_thres=45 

# minimum mapping unit area in square meters
minimum_mapping_unit_area_m2=4000 

EMS_vector_folder='path to EMS directory that contains vector files' 
# example: '/RSL03/Flood_detection/EMSR517/EMS/EMSR517_AOI01_DEL_MONIT01_r1_RTP04_v1_vector'

scihub_accounts={'USERNAME_1':'PASSWORD_1',
                 'USERNAME_2':'PASSWORD_2'}

```

## 3. Documentation and citation
Algorithms implemented in the software are described in detail at our publication. If FLOMPY was useful for you, we encourage you to cite the following work.

Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

## 4. Contact us
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recommendations. Any help is very welcome!
