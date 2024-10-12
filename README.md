# <img src="https://github.com/kleok/FLOODPY/blob/main/figures/Floodpy_logo.png" width="58"> FLOODPY - FLOOD PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOODPY)
[![Release](https://img.shields.io/badge/Release-Floodpy_Oct_2024-brightgreen)](https://github.com/kleok/FLOODPY)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/kleok/FLOODPY/issues)
[![Documentation](https://readthedocs.org/projects/floodpy/badge/?version=latest)](https://floodpy.readthedocs.io/en/latest/)

## Introduction

The Flood mapping python toolbox (Floodpy) is a free and open-source python toolbox for mapping the non-urban flooded regions. It exploits the dense Sentinel-1 GRD intensity time series using a statistical or a ViT (Visual Transfomer) approach. Before running Floodpy make use you know the following information of the flood event of your interest
 - Date and time of the flood event
 - Spatial information (e.g. min,max latitude and min,max longitude) of the flood event

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOODPY/blob/main/figures/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux. 
Recommended setup: Python 3.9+, SNAP 9.0+

### 1.1 Install snap gpt including Sentinel-1 toolbox

Please download ESA-SNAP (All Toolboxes) from [here](https://step.esa.int/main/download/snap-download/) and install it using the following commands:

  ```bash
  chmod +x esa-snap_all_linux-10.0.0.sh
  ./esa-snap_all_linux-10.0.0.sh
  ```

### 1.2 Account setup for downloading Sentinel-1 acquisitions

Even though we offer credentials (for demonstration reasons), we encourage you
to create your own account in order to not encounter any problems due to
traffic.

- Please create an account at: [Copernicus-DataSpace](https://dataspace.copernicus.eu/).

### 1.3 Account setup for downloading global atmospheric model data

FloodPy can download meteorological data from based on ERA-5 data. 
You have to create a new account [here](https://cds.climate.copernicus.eu/) if you don't own a user account yet. 
After the creation of your profile, you will find your Personal Access Token on your User profile page. 
Create manually a ```.cdsapirc``` file  under your ```HOME``` directory with the following information:

```
url: https://cds.climate.copernicus.eu/api
key: Your Personal Access Token
```

### 1.4 Download FLOODPY

You can download FLOODPY toolbox using the following command:
```git clone https://github.com/kleok/FLOODPY.git```

### 1.5 Create python environment for FLOODPY

FLOODPY is written in Python3 and relies on several Python modules. We suggest to install them by using conda.

- Using **conda**
Create a new conda environement with required packages using the the file [FLOODPY_gpu_env.yml](https://github.com/kleok/FLOODPY/blob/main/FLOODPY_gpu_env.yml).

```
conda env create -f path_to_FLOODPY/FLOODPY_gpu_env.yml
```

### 1.6 Set environmental variables (Optional)

Append to .bashrc file
```
export FLOODPY_HOME= path_of_the_FLOODPY_folder
export PYTHONPATH=${PYTHONPATH}:${FLOODPY_HOME}
export PATH=${PATH}:${FLOODPY_HOME}/floodpy
```

## 2. Running FLOODPY

FLOODPY generates a map with flooded regions based on Sentinel-1 GRD products and meteorological data. 
Sentinel-1 orbits are downloaded using the [sentineleof](https://github.com/scottstanie/sentineleof)
You can run FLOODPY using the following jupyter notebooks as templates.

- [Floodpy statistical approach](https://nbviewer.org/github/kleok/FLOODPY/blob/main/Floodpyapp_stat.ipynb)
- [Floodpy deep learning approach](https://nbviewer.org/github/kleok/FLOODPY/blob/main/Floodpyapp_Vit.ipynb)

## 3. Documentation and citation
Algorithms implemented in the software are described in detail at our publications. If FLOODPY was useful for you, we encourage you to cite the following work: 
- Karamvasis K, Karathanassi V. FLOMPY: An Open-Source Toolbox for Floodwater Mapping Using Sentinel-1 Intensity Time Series. Water. 2021; 13(21):2943. https://doi.org/10.3390/w13212943 

- Kuro Siwo: 33 billion m2 under the water. A global multi-temporal satellite dataset for rapid flood mapping. https://paperswithcode.com/paper/kuro-siwo-12-1-billion-m-2-under-the-water-a

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