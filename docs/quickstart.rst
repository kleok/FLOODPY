Quickstart
==========

Use `FLOMPYapp.py <https://github.com/kleok/FLOMPY/blob/main/flompy/FLOMPYapp.py>`_

FLOMPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data. :file:`FLOMPYapp.py` includes the functionalities for FLOMPY's routine processing for generating floodwater maps. User should provide the following information at configuration file FLOMPYapp_template.cfg.

We suggest you to can have a look at the plots for each Sentinel-1 image (located at projectfolder) to find out if you have a considerable decrease of backscatter in the flood image with respect to the baseline images. If you are able to identify a decrease of backscatter in the flood image (darker tones), then you can expect that FLOMPY will generate a useful floodwater map. In cases that you have similar or bigger backscatter values of flood image with respect to baseline images (due to complex backscatter mechanisms) FLOMPY`s results cannot be trusted.

The user should provide the following information in the :file:`FLOMPYapp_template.cfg`

.. code-block:: bash

	#             CONFIGURATION FILE      #

	# A. Project Definition 

	#A1. The name of your project withough special characters.
	Projectname = Palamas *needs to be modified*

	#A2. The location that everything is going to be saved. Make sure 
	#        you have enough free space disk on the specific location.
	projectfolder = /RSL03/FLOMPY_palamas *needs to be modified*

	#A3. The location of Flompy code 
	src_dir = /RSL03/Flompy_0.3/FLOMPY/flompy *needs to be modified*

	#A4. SNAP ORBIT DIRECTORY
	snap_dir = /home/kleanthis/.snap/auxdata/Orbits/Sentinel-1 *needs to be modified*

	#A5. SNAP GPT full path
	GPTBIN_PATH=/home/kleanthis/bin/snap8/snap/bin/gpt *needs to be modified*


	# B. Flood event temporal information

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
	Flood_datetime = 20200921T030000 *needs to be modified*

	# B2. Days before flood event for baseline stack construction
	before_flood_days = 60

	# B3. Days after flood event
	after_flood_days = 3

	# C. Flood event spatial information
	#---------------------- Instructions------------------------
	# You can provide AOI VECTOR FILE or AOI BBOX. 
	# Please ensure that your AOI BBOX has dimensions smaller than 100km x 100km
	# If you provide AOI VECTOR, AOI BBOX parameters will be ommited
	#-In case you provide AOI BBOX coordinates, set  AOI_File = None
	#--------------------------------------------------------
	# C1. AOI VECTOR FILE (if given AOI BBOX parameters can be ommited)
	AOI_File = /home/kleanthis/bin/FLOMPY/tests/Palamas_AOI.geojson *needs to be modified*

	# C2. AOI BBOX (WGS84)
	LONMIN=22.02 *needs to be modified*
	LATMIN=39.38 *needs to be modified*
	LONMAX=22.245 *needs to be modified*
	LATMAX=39.518 *needs to be modified*

	# D. Precipitation information #
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

	# E.  Data access and processing  
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
	scihub_username = *needs to be filled*
	scihub_password = *needs to be filled*

1. Download Precipitation data from ERA5
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Download_Precipitation_data

2. Download Sentinel 1 data.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Download_S1_data

3. Preprocessing Sentinel 1 data.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Preprocessing_S1_data

4. Sentinel 1 statistical analysis.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Statistical_analysis

5. Sentinel 1 floodwater estimation.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

And at last the floodwater classification step. At this point the result of the estimated flooded region is exported.

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Floodwater_classification

If the flood was on an agricultural region you can also run the following steps to estimate the amount of the damaged fields by performing delineation (with a methodology based on `Yan & Roy, 2014 <https://www.sciencedirect.com/science/article/pii/S0034425714000194>`_ and a pretrained Unet delineation network) and active-inactive field classification based on NDVI timeseries with Sentinel 2 data. For more information check at `Gounari et al. 2022 <https://drive.google.com/file/d/1HiGkep3wx45gAQT6Kq34CdECMpQc8GUV/view?usp=sharing>`_.

6. Download Sentinel 2 multispectral data (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Download_S2_data

7. Run crop delineation and field classification (Optional, requires *Download Sentinel 2 multispectral data*).
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

	FLOMPYapp.py FLOMPYapp_template.cfg --dostep Crop_delineation












