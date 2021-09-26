# FLOMPY - FLOod Mapping PYthon toolbox

Introduction

The FLOod Mapping PYthon toolbox is a new fully automatic, free and open-source python toolbox for mapping of floodwater. It exploits the dense Sentinel-1 GRD intensity time series and is based on four processing steps. In the first step, a selection of Sentinel-1 images related to pre-flood (baseline) state and flood state is performed. In the second step, the preprocessing of the selected images is performed in order to create a co-registered stack with all the pre-flood and flood images. In the third step, a statistical temporal analysis is performed and a t-score map that represents the changes due to flood event is calculated. Finally, in the fourth step, a multi-scale iterative thresholding algorithm based on t-score map is performed to extract the final flood map. We believe that the end-user community can benefit by exploiting
the FLompy flood maps.

This is research code provided to you "as is" with NO WARRANTIES OF CORRECTNESS. Use at your own risk.

1. Installation

The installation note below is tested only on Linux.
FLOMPY is written in Python3 and relies on several Python modules, check the requirements.txt file for details. We recommend using conda to install the python environment and the prerequisite packages, because of the convenient management.

Account setup for Sentinel-1 acquisitions
Sentinel-1 data donwload functionality require user credentials. More information at https://scihub.copernicus.eu/

Account setup for global atmospheric models
ERA-5 data set is redistributed over the Copernicus Climate Data Store (CDS), create a new account on the CDS website if you don't own a user account yet. On the profile, you will find your user id (UID) and your personal API Key. Create a file .cdsapirc under your home directory and add the following information:

url: https://cds.climate.copernicus.eu/api/v2
key: UID:personal API Key

More details on CDSAPI can be found here [https://cds.climate.copernicus.eu/api-how-to].

2. Running Flompy
4. Documentation
5. Contact us
6. Citing this work
