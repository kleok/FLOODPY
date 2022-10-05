# Imports
from datetime import datetime, timedelta
import numpy as np
import urllib.request
import os
from pathlib import Path


def closest_value(input_value):
    input_list=[0,6,12,18]
    arr = np.asarray(input_list)
    i = (np.abs(arr - input_value)).argmin()
    return i


days_before = 6 # Depending on ERA5 availability
rhours = ['00', '06', '12', '18']
time_now = datetime.now().strftime('%H')
today_rhours = [rhours[i] for i in range(0,closest_value(int(time_now)-4))]
date_today = datetime.now().strftime('%Y%m%d')
history_dates = [(datetime.now()-timedelta(i)).strftime('%Y%m%d') for i in range(0,days_before)]
hour_list = ['anl','f001', 'f002', 'f003', 'f004', 'f005']

parameters = 'var_PRATE=on'
levels = 'lev_surface=on'
lon_left = 0
lon_right = 360
lat_top = 90
lat_bottom = -90


url_dir = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'
url_dir1 = 'z.pgrb2.0p25.'
url_dir2 = f'&{levels}&{parameters}&subregion=&leftlon={lon_left}&rightlon={lon_right}&toplat={lat_top}&bottomlat={lat_bottom}&dir=%2Fgfs.'
url_dir3 = '%2F'
url_dir4 = '%2Fatmos'

output_dir = "/RSL03/DEMO_GFS"



# COMMAND ----------

number_retries = 1
for date in history_dates:
    sub_dir = f"gfs_{date}"
    path = os.path.join(output_dir, sub_dir)
    Path(path).mkdir(parents=True, exist_ok=True)
    if date == date_today:
        for rhour in today_rhours:
            for f_time in hour_list:
                retries=0
                while retries<=number_retries:
                    try:
                        print(f"Downloading {f_time} ---> ",end='')
                        url = f"{url_dir}{rhour}{url_dir1}{f_time}{url_dir2}{date}{url_dir3}{rhour}{url_dir4}"
                        urllib.request.urlretrieve(url, f"{path}/gfs.t{rhour}{url_dir1}{f_time}")
                        print("Success")
                    except Exception as e:
                        retries+=1
                        print(f"{str(e)}...retry downloading {f_time}")
                        continue
                    break
    else:
        for rhour in rhours:
            for f_time in hour_list:
                retries=0
                while retries<=number_retries:
                    try:
                        print(f"Downloading {f_time} ---> ",end='')
                        url = f"{url_dir}{rhour}{url_dir1}{f_time}{url_dir2}{date}{url_dir3}{rhour}{url_dir4}"
                        urllib.request.urlretrieve(url, f"{path}/gfs.t{rhour}{url_dir1}{f_time}")
                        print("Success")
                    except Exception as e:
                        retries+=1
                        print(f"{str(e)}...retry downloading {f_time}")
                        continue
                    break
            

