# <img src="https://github.com/kleok/FLOMPY/blob/main/figures/Flompy_logo.png" width="58"> FLOMPY - FLOod Mapping PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOMPY)
[![Release](https://img.shields.io/badge/Release-0.2.0-brightgreen)](https://github.com/kleok/FLOMPY)
[![Facebook](https://img.shields.io/badge/Group-Flompy-yellowgreen.svg)](https://www.facebook.com/groups/876299509742954)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)
[![Build Status](https://app.travis-ci.com/kleok/FLOMPY.svg?branch=main)](https://app.travis-ci.com/github/kleok/FLOMPY)

## Introduction

The FLOod Mapping PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOMPY's floodwater maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOMPY/blob/main/figures/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

### 1.1 Create python environment 
FLOMPY is written in Python3 and relies on several Python modules, check the file [FLOMPY_0.2_env.yml](https://github.com/kleok/FLOMPY/blob/main/docs/FLOMPY_0.2_env.yml) for details. We recommend using conda to install the python environment and the prerequisite packages, because of the convenient management.

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
[FLOMPYapp.py]("https://github.com/kleok/FLOMPY/blob/main/flompy/FLOMPYapp.py")

FLOMPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. FLOMPYapp.py includes the functionalities for FLOMPY's routine processing for generating floodwater maps. User should provide the following information at configuration file flompy/FLOMPYapp_template.cfg
```
######### CONFIGURATION FILE ######
###################################
# PROJECT DEFINITION
Projectname=Palamas
projectfolder=/RSL03/FLOMPY_palamas
src_dir=/home/kleanthis/bin/FLOMPY/flompy
##################################
# Processing parameters
# number of relative orbit (Default value: Auto)
relOrbit=Auto
# code of Sentinel-2 tile (Default value: Auto)
S2_TILE=Auto
# precipitation threshold in mm for 5 days
rain_thres=40
# minimum mapping unit area in square meters
minimum_mapping_unit_area_m2=3000
##################################
# Credentials
scihub_username = *****
scihub_password = *****
##################################
# Time information of the Flood event
# the datetime of flood event (Format is YYYYMMDDTHHMMSS
Flood_datetime = 20200921T030000
# Days before flood event for baseline stack construction
before_flood_days = 60
# Days after flood event for floodwater detection
after_flood_days = 3
##################################
# Spatial information of the Flood event
# AOI VECTOR FILE (if given AOI BBOX parameters can be ommited)
AOI_File = /home/kleanthis/bin/FLOMPY/tests/Palamas_AOI.geojson
# AOI BBOX DEFINITION (WGS84)
LONMIN=22.02
LATMIN=39.38
LONMAX=22.245
LATMAX=39.518

##################################
# SNAP ORBIT DIRECTORY
snap_dir = /home/kleanthis/.snap/auxdata/Orbits/Sentinel-1
# SNAP GPT 
GPTBIN_PATH=/home/kleanthis/bin/snap8/snap/bin/gpt
##################################
# COMPUTING RESOURCES TO EMPLOY
CPU=8
RAM=20G
##################################
```
## 3. Documentation and citation
Algorithms implemented in the software are described in detail at our publication. If FLOMPY was useful for you, we encourage you to cite the following work.

Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

## 4. Contact us
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recommendations. Any help is very welcome! :heart:

FLOMPY Team: [Kleanthis Karamvasis](https://github.com/kleok), [Ioanna Zotou](https://www.researchgate.net/profile/Ioanna-Zotou), [Alekos Falagas](https://github.com/alekfal), [Olympia Gounari](https://github.com/Olyna), [Vasileios Tsironis](https://github.com/tsironisbi), [Fragkiskos Dimos](https://github.com/fdimos), [Panagiotis Sismanidis](https://github.com/pansism), [Pavlos Alexantonakis](https://www.linkedin.com/in/pavlos-alexantonakis)

