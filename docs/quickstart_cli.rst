Running FLOODPY using terminal (CLI) 
====================================
Before running FLOODPY we strongly suggest you to:

- Find the **geographical borders**  of your area of interest (min/max latitude and longitude). 
 For example, you can extract the geographical coordinates (lats,lons) or save a geojson file of you area of interest from `here <https://geojson.io>`_.


- Define one single **flood peak datetime** in the following format DDMMYYYYTHHMMSS (e.g. 10022023T090000 represents the 23rd of February of 2023 09:00 am)
 of the flood event you want to study. For example, for recent flood events you can have a look `here <https://floodlist.com/>`_.


Use `FLOODPYapp.py <https://github.com/kleok/FLOODPY/blob/main/floodpy/FLOODPYapp.py>`_

FLOODPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. :file:`FLOODPYapp.py` includes the functionalities for FLOODPY's routine processing for generating floodwater maps. User should provide the following information at configuration file FLOODPYapp_template.cfg.

We suggest you to can have a look at the plots for each Sentinel-1 image (located at projectfolder) to find out if you have a considerable decrease of backscatter in the flood image with respect to the baseline images. If you are able to identify a decrease of backscatter in the flood image (darker tones), then you can expect that FLOODPY will generate a useful floodwater map. In cases that you have similar or bigger backscatter values of flood image with respect to baseline images (due to complex backscatter mechanisms) FLOODPY`s results cannot be trusted.

The user should provide the following information in the :file:`FLOODPYapp_template.cfg`

.. code-block:: bash

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
	# B1. The datetime of flood event (Format is YYYYMMDDTHHMMSS)
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

1. Download Precipitation data 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOODPYapp.py FLOODPYapp_template.cfg --dostep Download_Precipitation_data

2. Download Sentinel-1 data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOODPYapp.py FLOODPYapp_template.cfg --dostep Download_S1_data

3. Preprocessing Sentinel-1 data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOODPYapp.py FLOODPYapp_template.cfg --dostep Preprocessing_S1_data

4. Sentinel-1 statistical analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOODPYapp.py FLOODPYapp_template.cfg --dostep Statistical_analysis

5. Floodwater classification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

And at last the floodwater classification step. At this point the result of the estimated flooded region is exported.

.. code-block:: bash

	FLOODPYapp.py FLOODPYapp_template.cfg --dostep Floodwater_classification
