# FLOMPY - FLOod Mapping PYthon toolbox

## Introduction

The FLOod Mapping PYthon toolbox is a new fully automatic, free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting
the FLompy flood maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

## 1. Installation

The installation note below is tested only on Linux. Recommended minimum setup: Python 3.6, SNAP 8.0

### 1.1 Create python environment 
FLOMPY is written in Python3 and relies on several Python modules, check the requirements.txt file for details. We recommend using conda to install the python environment and the prerequisite packages, because of the convenient management.

### 1.2 Install snap gpt including [Sentinel-1 toolbox](https://step.esa.int/main/download/snap-download/)

### 1.3 Account setup for Sentinel-1 acquisitions
Sentinel-1 data donwload functionality require user credentials. More information [here](https://scihub.copernicus.eu/)

### 1.4 Account setup for global atmospheric models
ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS), create a new account on the CDS website if you don't own a user account yet. On the profile, you will find your user id (UID) and your personal API Key. Create a file .cdsapirc under your home directory and add the following information:

-url: https://cds.climate.copernicus.eu/api/v2
-key: UID:personal API Key

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

FLOMPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. In case of S1FloodwaterApp_EMSRXXX the user should download EMS product in order to compare FLOMPY and EMS results. The user should provide the following information at the Set parameter section in S1FloodwaterApp.py or S1FloodwaterApp_EMSR.py. 

## 3. Documentation and citation
Algorithms implemented in the software are described in details at our publication. If FLOMPY was useful for you, we encourage you to cite the following work.

Karamvasis, K., & Karathanassi, V. (2021). FLOMPY: An Open-Source Toolbox for Floodwater Mapping
Using Sentinel-1 Intensity Time Series. Water, XXXX (under review)

## 4. Contact us
Feel free to open an issue, comment or pull request. We would like to listen to your thoughts and your recomendations. Any help is very welcome!
