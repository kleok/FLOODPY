# <img src="https://github.com/kleok/FLOODPY/blob/main/figures/Floodpy_logo.png" width="58"> FLOODPY - FLOOD PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOODPY)
[![Release](https://img.shields.io/badge/Release-0.6.0-brightgreen)](https://github.com/kleok/FLOODPY)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/kleok/FLOODPY/issues)
[![Documentation](https://readthedocs.org/projects/floodpy/badge/?version=latest)](https://floodpy.readthedocs.io/en/latest/)

## Introduction

The FLOod Mapping PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOODPY's floodwater maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOODPY/blob/main/figures/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux.
We provide some notes for Windows. 
Recommended setup: Python 3.9, SNAP 9.0

### 1.1 Install snap gpt including Sentinel-1 toolbox

 - Option 1: You can either run the automated script [aux/install_snap.sh](https://github.com/kleok/FLOODPY/blob/main/aux/install_snap.sh) for downloading and installing the official Linux installer from the official ESA repository. 

 - Option 2: You can download SNAP manually from [here](https://step.esa.int/main/download/snap-download/) and install it using the following commands:

  ```bash
  chmod +x install_snap.sh
  ./install_snap.sh
  ```

### 1.2 Install aria for downloading Sentinel-1 acquisitions

- Please also install aria using the following command:
    ``` sudo apt-get install aria2 ```

### 1.3 Account setup for downloading Sentinel-1 acquisitions

Even though we offer credentials (for demonstration reasons), we encourage you
to create your own account in order to not encounter any problems due to
traffic.

- Please create an account at: [ESA-scihub](https://scihub.copernicus.eu/dhus/#/self-registration).

- Please create an account at: [NASA-earthdata](https://urs.earthdata.nasa.gov/users/new)

### 1.4 Account setup for downloading global atmospheric model data

Currently, FloodPy is based on ERA-5 data. ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS).
You have to create a new account [here](https://cds.climate.copernicus.eu/user/register?destination=%2F%23!%2Fhome) if you don't own a user account yet. 
After the creation of your profile, you will find your user id (UID) and your personal API Key on your User profile page. 

- Option 1: create manually a ```.cdsapirc``` file  under your ```HOME``` directory with the following information:

```
url: https://cds.climate.copernicus.eu/api/v2
key: UID:personal API Key
```
- Option 2: Run [aux/install_CDS_key.sh](https://github.com/kleok/FLOODPY/blob/main/aux/install_CDS_key.sh) script as follows:

```bash
chmod +x install_CDS_key.sh
./install_CDS_key.sh
```

More details for CDS API for windows can be found [here](https://confluence.ecmwf.int/display/CKB/How+to+install+and+use+CDS+API+on+Windows).

### 1.5 Download FLOODPY

You can download FLOODPY toolbox using the following command:
```git clone https://github.com/kleok/FLOODPY.git```

### 1.6 Create python environment for FLOODPY

FLOODPY is written in Python3 and relies on several Python modules. You can install them by using conda or pip.

- Using **conda**
Create a new conda environement with required packages using the the file [FLOODPY_env.yml](https://github.com/kleok/FLOODPY/blob/main/FLOODPY_env.yml).

```
conda env create -f path_to_FLOODPY/FLOODPY_env.yml
```

- Using **pip**
  You can install python packages using [setup.py](https://github.com/kleok/FLOODPY/blob/main/setup.py)
  
```
cd path_to_FLOODPY
pip install .
```

### 1.7 Set environmental variables

Append to .bashrc file
```
export FLOODPY_HOME= path_of_the_FLOODPY_folder
export PYTHONPATH=${PYTHONPATH}:${FLOODPY_HOME}
export PATH=${PATH}:${FLOODPY_HOME}/floodpy
```

## 2. Running FLOODPY

FLOODPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. 
You can run FLOODPY via jupyter notebook or via command line.

### Option 1: Run FloodPy via Jupyter Notebook. See example [here](https://github.com/kleok/FLOODPY/blob/main/notebooks/Floodpy_Ianos.ipynb)

------

### Option 2: Run FloodPy via command line. [FLOODPYapp.py](https://github.com/kleok/FLOODPY/blob/main/floodpy/FLOODPYapp.py)

FLOODPYapp.py includes the functionalities for FLOODPY's routine processing for generating floodwater maps. User should provide the following information at configuration file FLOODPYapp_template.cfg

We suggest you to can have a look at the plots for each Sentinel-1 image (located at projectfolder) to find out if you have a considerable decrease of backscatter in the flood image with respect to the baseline images. If you are able to identify a decrease of backscatter in the flood image (darker tones), then you can expect that FLOODPY will generate a useful floodwater map. In cases that you have similar or bigger backscatter values of flood image with respect to baseline images (due to complex backscatter mechanisms) FLOODPY`s results cannot be trusted.

```
#######################################
#             CONFIGURATION FILE      #
#######################################

# 	A. Project Definition  
#------------------------- 		  
#A1. The name of your project withough special characters.
Projectname = Palamas

#A2. The location that everything is going to be saved. Make sure 
#    you have enough free space disk on the specific location.
projectfolder = /home/kleanthis/Palamas

#A3. The location of floodpy code 
src_dir = /home/kleanthis/Projects/FLOODPY/floodpy/

#A4. SNAP ORBIT DIRECTORY
snap_dir = /home/kleanthis/.snap/auxdata/Orbits/Sentinel-1

#A5. SNAP GPT full path
GPTBIN_PATH = /home/kleanthis/snap9/bin/gpt

#   B. Flood event temporal information  
#-------------------------------------------------------------
# Your have to provide the datetime of your flood event. Make sure that
# a flood event took place at your provided datetime. 
# Based on your knowledge you can change [before_flood_days] in order
# to create a biggest 
# Sentinel-1 image that is going to be used to extract flood information
# will be between Flood_datetime and Flood_datetime+after_flood_days
# the closest Sentinel-1 to the Flood_datetime is picked
#-------------------------------------------------------------
# B1. The datetime (time in UTC) of flood event (Format is YYYYMMDDTHHMMSS)
Flood_datetime = 20200921T030000

# B2. Days before flood event for baseline stack construction
before_flood_days = 20

# B3. Days after flood event
after_flood_days = 3

#  C. Flood event spatial information 
#-------------------------------------------------------------
# You can provide AOI VECTOR FILE or AOI BBOX. 
# Please ensure that your AOI BBOX has dimensions smaller than 100km x 100km
# If you provide AOI VECTOR, AOI BBOX parameters will be ommited
#-In case you provide AOI BBOX coordinates, set  AOI_File = None
#--------------------------------------------------------

# C1. AOI VECTOR FILE (if given AOI BBOX parameters can be ommited)
AOI_File = None

# C2. AOI BBOX (WGS84)
LONMIN=22.02
LATMIN=39.46
LONMAX=22.17
LATMAX=39.518

#  D. Precipitation information   
#-------------------------------------------------------------
#  Based on your knowledge, provide information related to the 
# accumulated precipitation that is required in order a flooding to occur. 
# These particular values will be used to classify Sentinel-1 images
#  which images correspond to flood and non-flood conditions.
#--------------------------------------------------------

# D1. number of consequent days that precipitation will be accumulated.
#       before each Sentinel-1 acquisition datetime
days_back = 12

# D2. The threshold of acculated precipitation [mm]
accumulated_precipitation_threshold = 120

########################################
# 	  E.  Data access and processing    #
########################################
#E1. The number of Sentinel-1 relative orbit. The default 
#       value is Auto. Auto means that the relative orbit that has
#       the Sentinel-1 image closer to the Flood_datetime is selected. 
#       S1_type can be GRD or SLC.
S1_type = GRD
relOrbit = Auto

#E3. The minimum mapping unit area in square meters
minimum_mapping_unit_area_m2=4000

#E4. Computing resources to employ
CPU=8
RAM=20G

#E5. Credentials for Sentinel-1/2 downloading
scihub_username = flompy
scihub_password = rslab2022
aria_username = floodpy
aria_password = RSlab2022
```

After the setup of the configuration file you can use the default recipe script FLOODPYapp.py to run the following individual steps for you case study:

### 2.1. Download Precipitation data.

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

### 2.5. Floodwater classification step.

```
FLOODPYapp.py FLOODPYapp_template.cfg --dostep Floodwater_classification
```

## 3. Documentation and citation
Algorithms implemented in the software are described in detail at our publications. If FLOODPY was useful for you, we encourage you to cite the following work: 
- Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

You can also have a look at other works that are using FLOODPY:

- Gounari 0., Falagas A., Karamvasis K., Tsironis V., Karathanassi V., 
Karantzalos K.: Floodwater Mapping & Extraction of Flood-Affected 
Agricultural Fields. Living Planet Symposium Bonn 23-27 May 2022.      
https://drive.google.com/file/d/1HiGkep3wx45gAQT6Kq34CdECMpQc8GUV/view?usp=sharing

- Zotou I., Karamvasis K., Karathanassi V., Tsihrintzis V.: Sensitivity of a coupled 1D/2D 
model in input parameter variation exploiting Sentinel-1-derived flood map. 
7th IAHR Europe Congress. September 7-9, 2022. Page 247 at 
https://www.iahreuropecongress.org/PDF/IAHR2022_ABSTRACT_BOOK.pdf

- Zotou I, Karamvasis K, Karathanassi V, Tsihrintzis VA. Potential of Two SAR-Based Flood Mapping Approaches in Supporting an Integrated 1D/2D HEC-RAS Model. Water. 2022; 14(24):4020. https://doi.org/10.3390/w14244020 

## 4. Contact us
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recommendations. Any help is very welcome! :heart:

FLOODPY Team: [Kleanthis Karamvasis](https://github.com/kleok), [Ioanna Zotou](https://www.researchgate.net/profile/Ioanna-Zotou), [Alekos Falagas](https://github.com/alekfal), [Olympia Gounari](https://github.com/Olyna), [Vasileios Tsironis](https://github.com/tsironisbi), [Markos Mylonas](https://github.com/mylonasma), [Pavlos Alexantonakis](https://www.linkedin.com/in/pavlos-alexantonakis)

