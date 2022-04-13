Quickstart
==========

Use `S1FloodwaterApp.py` or `S1FloodwaterApp_EMSR.py`

FLOMPY generates a floodwater map based on Sentinel-1 GRD products and meteorological data.
In case of `S1FloodwaterApp_EMSR.py` the user should download EMS product in order to compare FLOMPY and EMS results.

The user should provide the following information at the Set parameter section in `S1FloodwaterApp.py` or `S1FloodwaterApp_EMSR.py`. 

.. code-block:: python

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
    # use can also selects specific Relative orbit number
    relOrbit='Auto' 

    # cumulative rain in mm for the last 5 days 
    rain_thres=45 

    # minimum mapping unit area in square meters
    minimum_mapping_unit_area_m2=4000 

    EMS_vector_folder='path to EMS directory that contains vector files' 
    # example: '/RSL03/Flood_detection/EMSR517/EMS/EMSR517_AOI01_DEL_MONIT01_r1_RTP04_v1_vector'

    scihub_accounts={'USERNAME_1':'PASSWORD_1',
                    'USERNAME_2':'PASSWORD_2'}

