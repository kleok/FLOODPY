from floodpy.Download.eof.download import download_eofs
import os, glob
from datetime import datetime

def download_S1_POEORB_orbits(Floodpy_app):

    S1_GRD_images = glob.glob(os.path.join(Floodpy_app.S1_dir,'*.zip'))
    for GRD_image in S1_GRD_images:
        print(os.path.basename(GRD_image))
        image_year = os.path.basename(GRD_image)[17:21]
        image_month = os.path.basename(GRD_image)[21:23]
        image_sensor = os.path.basename(GRD_image)[0:3]

        image_Datetime = datetime.strptime(os.path.basename(GRD_image)[17:32], '%Y%m%dT%H%M%S')


        S1_orbit_dir = os.path.join(Floodpy_app.snap_orbit_dir,
                                    'POEORB',
                                    image_sensor,
                                    image_year,
                                    image_month)
        
        if not os.path.exists(S1_orbit_dir): os.makedirs(S1_orbit_dir)
        
        download_eofs(orbit_dts = [image_Datetime],
                missions = [image_sensor],
                save_dir = S1_orbit_dir,
                orbit_type="precise",
                cdse_user = Floodpy_app.Copernicus_username,
                cdse_password = Floodpy_app.Copernicus_password,
                force_asf = False)
