# Imports
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import urllib.request
import os
import glob
import pygrib


def retrieve_GFS_data(GFS_variables: str, GFS_levels: str, days_before: int, hours_ahead: int, bbox: list, export_directory: str) -> str:
    """Download functionality for GFS

    Args:
        GFS_variables (str): Name of parameter to be downloaded as defined in GFS model docs
        GFS_levels (str): Name of parameter level as defined in GFS model docs
        days_before (int): Days in the past to be downloaded
        hours_ahead (int): Forecast horizon hours
        bbox (list): List of latitude/longitude [LONMIN, LATMIN,  LONMAX, LATMAX]
        export_directory (str): full path of dataset
    """
    """
    Returns:
        export_filename (str): Full path of dataset
    """

    def find_latest_run(input_time_hour):
        input_list = [0, 6, 12, 18]
        t = [input_time_hour > y for y in input_list]
        return int(len([i for i, x in enumerate(t) if x])-1)

    rhours = ['00', '06', '12', '18']
    latency = 4  # latency of run in hours
    time_now = datetime.utcnow().strftime('%H')
    today_rhours = [rhours[i] for i in range(0, find_latest_run(int(time_now)-latency)+1)]
    latest_run = today_rhours[-1]
    date_today = datetime.now().strftime('%Y%m%d')
    history_dates = [(datetime.now()-timedelta(i)).strftime('%Y%m%d') for i in range(0,days_before)]
    last_run_hour_list = [f'f{str(x).zfill(3)}' for x in range(0, hours_ahead)]
    hour_list = ['anl', 'f001', 'f002', 'f003', 'f004', 'f005']

    parameters = f'{GFS_variables}=on' # var_PRATE
    levels = f'{GFS_levels}=on' # lev_surface
    LONMIN, LATMIN, LONMAX, LATMAX = bbox

    url_dir = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'
    url_dir1 = 'z.pgrb2.0p25.'
    url_dir2 = f'&{levels}&{parameters}&subregion=&leftlon={LONMIN}&rightlon={LONMAX}&toplat={LATMAX}&bottomlat={LATMIN}&dir=%2Fgfs.'
    url_dir3 = '%2F'
    url_dir4 = '%2Fatmos'

    number_retries = 1
    for date in history_dates:
        sub_dir = f"gfs_{date}"
        path = os.path.join(export_directory, sub_dir)
        Path(path).mkdir(parents=True, exist_ok=True)
        if date == date_today:
            for rhour in today_rhours:
                if rhour == latest_run:
                    for f_time in last_run_hour_list:
                        retries = 1
                        while retries<=number_retries:
                            try:
                                file_name = (datetime.strptime(f'{date}{rhour}', '%Y%m%d%H')+timedelta(hours=int(f_time[1:]))).strftime('%Y%m%d%H')
                                print(f"Downloading {file_name} ---> ",end='')
                                url = f"{url_dir}{rhour}{url_dir1}{f_time}{url_dir2}{date}{url_dir3}{rhour}{url_dir4}"

                                urllib.request.urlretrieve(url, f"{path}/{file_name}")
                                print("Success")
                            except Exception as e:
                                retries+=1
                                print(f"{str(e)}...retry downloading {f_time}")
                                continue
                            break
                else:
                    for f_time in hour_list:
                        retries = 1
                        while retries <= number_retries:
                            try:
                                if f_time == 'anl':
                                    file_name = (datetime.strptime(f'{date}{rhour}', '%Y%m%d%H')).strftime('%Y%m%d%H')
                                else:
                                    file_name = (datetime.strptime(f'{date}{rhour}', '%Y%m%d%H') + timedelta(
                                        hours=int(f_time[1:]))).strftime('%Y%m%d%H')
                                print(f"Downloading {file_name} ---> ", end='')
                                url = f"{url_dir}{rhour}{url_dir1}{f_time}{url_dir2}{date}{url_dir3}{rhour}{url_dir4}"
                                urllib.request.urlretrieve(url, f"{path}/{file_name}")
                                print("Success")
                            except Exception as e:
                                retries += 1
                                print(f"{str(e)}...retry downloading {f_time}")
                                continue
                            break
        else:
            for rhour in rhours:
                for f_time in hour_list:
                    retries = 1
                    while retries<=number_retries:
                        try:
                            if f_time == 'anl':
                                file_name = (datetime.strptime(f'{date}{rhour}', '%Y%m%d%H')).strftime('%Y%m%d%H')
                            else:
                                file_name = (datetime.strptime(f'{date}{rhour}', '%Y%m%d%H') + timedelta(
                                    hours=int(f_time[1:]))).strftime('%Y%m%d%H')
                            print(f"Downloading {file_name} ---> ",end='')
                            url = f"{url_dir}{rhour}{url_dir1}{f_time}{url_dir2}{date}{url_dir3}{rhour}{url_dir4}"
                            urllib.request.urlretrieve(url, f"{path}/{file_name}")
                            print("Success")
                        except Exception as e:
                            retries+=1
                            print(f"{str(e)}...retry downloading {f_time}")
                            continue
                        break

    return export_directory


def Get_GFS_data(GFS_variables:list,
                 start_datetime:datetime,
                 end_datetime:datetime,
                 bbox:list,
                 GFS_dir:str) -> pd.DataFrame:
    """Downloads GFS datasets between two given dates.

    Args:
        GFS_variables (list): list of ERA5 variables e.g. ['total_precipitation',]
        start_datetime (datetime.datetime): Starting Datetime e.g.  datetime.datetime(2021, 12, 2, 0, 0)
        end_datetime (datetime.datetime): Ending Datetime e.g.  datetime.datetime(2022, 2, 8, 0, 0)
        bbox (list): List of latitude/longitude [LONMIN, LATMIN,  LONMAX, LATMAX]
        GFS_dir (str): Path that ERA5 data will be saved.

    Returns:
        Precipitation_data (pd.DataFrame): precipitation data
    """

    LONMIN, LATMIN, LONMAX, LATMAX = bbox
    bbox_gfs = [LATMAX, LONMIN, LATMIN, LONMAX, ]

    precipitation_filename_df = os.path.join(GFS_dir,'GFS_{Start_time}_{End_time}_{bbox_gfs}.csv'.format(Start_time=start_datetime.strftime("%Y%m%dT%H%M%S"),
                                                                                            End_time=end_datetime.strftime("%Y%m%dT%H%M%S"),
                                                                                            bbox_gfs='_'.join(str(round(e,5)) for e in bbox_gfs)))

    if not os.path.exists(precipitation_filename_df):

        # Calculate the forecast horizon in hours based on the end_datetime
        horizon_hours = int((end_datetime-datetime.now()).total_seconds()//3600)
        days_before = int((datetime.now()-start_datetime).days)

        gfs_dir = retrieve_GFS_data(GFS_variables[0], GFS_variables[1], days_before, horizon_hours, bbox_gfs, GFS_dir)

        gfs_files = []
        for folder in glob.glob(f'{gfs_dir}/gfs*', recursive=True):
            for path, subdirs, files in os.walk(folder):
                for name in files:
                    gfs_files.append(os.path.join(path, name))

        precipitation_df = pd.DataFrame()
        for grib_file in gfs_files:
            try:
                grib = pygrib.open(grib_file)
                g = grib[1]
                hour = g['hour']
                forecast_hour_ahead = g['forecastTime']
                day = g['day']
                month = g['month']
                year = g['year']
                dateTime = datetime(year, month, day, hour)+timedelta(hours=forecast_hour_ahead)
                value = g['values'][:][:].mean()*3600 # convert to hourly as values of PRATE are in kg m**-2 s**-1
                df_int = pd.DataFrame({'Datetime': dateTime, 'GFS_tp_mm': value}, index=[0])
            except Exception as e:
                print(e)
            precipitation_df = pd.concat([precipitation_df, df_int], axis=0)

        precipitation_df = precipitation_df.sort_values('Datetime')
        precipitation_df.to_csv(precipitation_filename_df, index=False)

        return precipitation_df

