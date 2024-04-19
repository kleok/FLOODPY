# <img src="https://github.com/kleok/FLOODPY/blob/main/figures/Floodpy_logo.png" width="58"> FLOODPY - FLOOD PYthon toolbox 
[![GitHub license](https://img.shields.io/badge/License-GNU3-green.svg)](https://github.com/kleok/FLOODPY)
[![Release](https://img.shields.io/badge/Release-0.7.0-brightgreen)](https://github.com/kleok/FLOODPY)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/kleok/FLOODPY/issues)
[![Documentation](https://readthedocs.org/projects/floodpy/badge/?version=latest)](https://floodpy.readthedocs.io/en/latest/)

## Introduction

The FLOod Mapping PYthon toolbox is a free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting the FLOODPY's floodwater maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

<img src="https://github.com/kleok/FLOODPY/blob/main/figures/pinieios_results_github.png" width="900">

## 1. Installation

The installation notes below are tested only on Linux. 
Recommended setup: Python 3.9+, SNAP 9.0+

### 1.1 Install snap gpt including Sentinel-1 toolbox

You can download SNAP manually from [here](https://step.esa.int/main/download/snap-download/) and install it using the following commands:

  ```bash
  chmod +x install_snap.sh
  ./install_snap.sh
  ```

### 1.2 Account setup for downloading Sentinel-1 acquisitions

Even though we offer credentials (for demonstration reasons), we encourage you
to create your own account in order to not encounter any problems due to
traffic.

- Please create an account at: [Copernicus-DataSpace](https://dataspace.copernicus.eu/).

### 1.3 Account setup for downloading global atmospheric model data

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

### 1.4 Download FLOODPY

You can download FLOODPY toolbox using the following command:
```git clone https://github.com/kleok/FLOODPY.git```

### 1.5 Create python environment for FLOODPY

FLOODPY is written in Python3 and relies on several Python modules. We suggest to install them by using conda.

- Using **conda**
Create a new conda environement with required packages using the the file [FLOODPY_env.yml](https://github.com/kleok/FLOODPY/blob/main/FLOODPY_env.yml).

```
conda env create -f path_to_FLOODPY/FLOODPY_env.yml
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
You can run FLOODPY via jupyter notebook. See example [here](https://github.com/kleok/FLOODPY/blob/dev/Floodpyapp_notebook.ipynb)


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

