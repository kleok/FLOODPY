import os
import sys
import pandas as pd
import shapely
import datetime
from IPython.core.display import HTML
import zipfile
from hda import Client
import xarray as xr
from typing import Tuple
import netCDF4
import numpy as np

import warnings
warnings.filterwarnings('ignore')



def dateRange(given_date:str, days_diff:int=30)->Tuple[str, str]:      
    """Produce a temporal range.

    Args:
        flood_event_date (str): Date of flood event (YYYY-MM-DD).
        days_diff (int, optional): How many days before/after flood event\
            to start the temporal range. Defaults to 30.

    Returns:
        Tuple[str, str]: [startdate, enddate], if days_diff is positive number.\
            [enddate, startdate], if days_diff is negative.
    """
    dtf = datetime.datetime.strptime(given_date, '%Y-%m-%d')
    new_date = dtf - datetime.timedelta(days=days_diff)
    new_date = new_date.strftime('%Y-%m-%d')
    return new_date, given_date


def cftime_to_datetime(cfdatetime):
    '''
    Time convertion functionality
    '''
    year=cfdatetime.year
    month=cfdatetime.month
    day=cfdatetime.day
    hour=cfdatetime.hour
    minute=cfdatetime.minute
    second=cfdatetime.second
    return datetime.datetime(year,month,day,hour,minute,second)


def era5_data(aoi:list, flood_date:datetime.datetime, start_datetime:datetime.datetime, end_datetime:datetime.datetime, ERA5_dir:str)->pd.DataFrame:
    """Retrieve ERA5 data hourly, using HDA API.

    Args:
        aoi (list): Area of interest bounding box coordinates.
        flood_date (datetime.datetime): Date of flood event.
        start_datetime (datetime.datetime): Days to examine before flood event.
        end_datetime (datetime.datetime): Days to examine after flood event.
        ERA5_dir (str): Location where retrieved data will be saved.

    Returns:
        pd.DataFrame: _description_
    """

    flood_event_date = flood_date.strftime('%Y-%m-%d')                    
    start_date=start_datetime.strftime('%Y-%m-%d')
    end_date=end_datetime.strftime('%Y-%m-%d')
    minx, miny, maxx, maxy = aoi

    precipitation_filename_df = os.path.join(ERA5_dir,'ERA5_{Start_time}_{End_time}_{bbox_cdsapi}.csv'.format(
        Start_time=start_datetime.strftime("%Y%m%dT%H%M%S"),
        End_time=end_datetime.strftime("%Y%m%dT%H%M%S"),
        bbox_cdsapi='_'.join(str(round(e,5)) for e in aoi)))
    
    request = {
        'datasetId': 'EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS',
        'boundingBoxValues': [{
            'name': 'area',
            'bbox': [ minx, miny, maxx, maxy ]
        }],
        'dateRangeSelectValues': [{
            'name': 'date',
            'start': start_date,
            'end': end_date
        }],
        'multiStringSelectValues': [{
            'name': 'variable',
            'value': ['total_precipitation']
        },{
            'name': 'product_type',
            'value': ['reanalysis']
        },{
              "name": "time",
              "value": [
                "00:00",
                "01:00",
                "02:00",
                "03:00",
                "04:00",
                "05:00",
                "06:00",
                "07:00",
                "08:00",
                "09:00",
                "10:00",
                "11:00",
                "12:00",
                "13:00",
                "14:00",
                "15:00",
                "16:00",
                "17:00",
                "18:00",
                "19:00",
                "20:00",
                "21:00",
                "22:00",
                "23:00"
        ]}
        ],
        'stringChoiceValues': [{
            'name': 'format',
            'value': 'netcdf'
        }]
    }

    os.chdir(ERA5_dir)
    c = Client()
    matches = c.search(request)
    print(f"Downloading matches: {len(vars(matches)['results'])}")
    for m in vars(matches)['results']:
        print(m['filename'])
    matches.download()
    
    ds = xr.open_dataset(m['filename'])
    df = ds.to_dataframe()
    
    Precipitation_data = pd.DataFrame(index = df.index)

    ERA5_data=netCDF4.Dataset(m['filename'])
    ERA5_variables = list(ERA5_data.variables.keys())
        
    df_dict={}
    for ERA5_variable in ERA5_variables:

        if ERA5_variable in ['longitude',  'latitude']:
            pass
        elif ERA5_variable=='time':
            time_var=ERA5_data.variables[ERA5_variable]
            t_cal = ERA5_data.variables[ERA5_variable].calendar
            dtime = netCDF4.num2date(time_var[:],time_var.units, calendar = t_cal)
            dtime_datetime=[cftime_to_datetime(cfdatetime) for cfdatetime in dtime.data]
            df_dict['Datetimes']=dtime_datetime

        elif ERA5_variable!='expver':
            temp_name=ERA5_variable+'__'+ERA5_data[ERA5_variable].units
            temp_dataset=np.mean(np.mean(ERA5_data[ERA5_variable][:],axis=1), axis=1)
            if len(temp_dataset.shape)>1:
                temp_dataset=np.mean(temp_dataset,axis=1)
            df_dict[temp_name]=np.squeeze(temp_dataset)
        else:
            pass

    # create a dataframe
    df_ERA5_tp = pd.DataFrame(df_dict)
    df_ERA5_tp.index = df_ERA5_tp['Datetimes']
    df_ERA5_tp['tp__mm']=df_ERA5_tp['tp__m']*1000
    Precipitation_data = df_ERA5_tp['tp__mm']
    Precipitation_data.index = pd.to_datetime(Precipitation_data.index)
    
    Precipitation_data = Precipitation_data.to_frame(name='ERA5_tp_mm')
    Precipitation_data['Datetime'] = Precipitation_data.index
    Precipitation_data.to_csv(precipitation_filename_df, index=False)
    return Precipitation_data




def S1_data(aoi:list, path:str):
    """Retrieve Sentinel-1 data, using HDA API.

    Args:
        aoi (list): Area of interest bounding box coordinates.
        path (str): Location where retrieved data will be saved and\
            'S1_products.csv' is saved.

    Returns:
        _type_: _description_
    """
    # Define Area of Interest
    minx, miny, maxx, maxy = aoi
    
    def _queryArgs(s1_products_file:pd.Series)->Tuple[str,str,str]:
        """Function to apply on S1_products.csv and source info about image request.

        Args:
            s1_products_file (pd.Series): S1_products.csv containing fields with info about\
                'beginposition' and 'orbitdirection'.

        Returns:
            Tuple[str,str,str]: [start_date, end_date, orbit_dir]
        """
        # Temporal arguments
        beginposition = s1_products_file['beginposition']
        beginposition = datetime.datetime.strptime(beginposition, '%Y-%m-%d %H:%M:%S.%f')
        beginposition = beginposition.strftime('%Y-%m-%dT%H:%M:%S.%f')
        
        endposition = s1_products_file['endposition']
        endposition = datetime.datetime.strptime(endposition, '%Y-%m-%d %H:%M:%S.%f')
        endposition = endposition.strftime('%Y-%m-%dT%H:%M:%S.%f')

        # Datetime strings
        start_date, end_date = f'{beginposition[:-3]}Z', f'{endposition[:-3]}Z'

        # Orbit direction
        orbit_dir = s1_products_file['orbitdirection'].lower()

        return start_date, end_date, orbit_dir
    
    # Read .csv downloaded by class Download_S1_data
    s1_prod = pd.read_csv(os.path.join(path, 'S1_products.csv'))
    
    # For each entry in 'S1_products.csv', define temporal range of 1 day & orbit direction
    for index, row in s1_prod.iterrows():
        start_date, end_date, orbit_dir = _queryArgs(row)

        request = {
            "datasetId": "EO:ESA:DAT:SENTINEL-1:SAR",
            "boundingBoxValues": [{
                "name": "bbox",
                "bbox": [minx, miny, maxx, maxy]
            }],
            "dateRangeSelectValues": [{
                "name": "position",
                "start": start_date,
                "end": end_date
            }],
            "stringChoiceValues": [{
                "name": "productType",
                "value": "GRD"
            },{
                "name": "timeliness",
                "value": "Fast-24h"
            },{
                "name": "orbitDirection",
                "value": orbit_dir
            }]
        }

        os.chdir(path)
        c = Client()
        matches = c.search(request)
        print(f"Downloading matches: {len(vars(matches)['results'])}")
        for m in vars(matches)['results']:
            if os.path.exists(os.path.join(path, m['filename'])):
                print(f"{m['filename']} Already Exists")
                pass
            else:
                print(m['filename'])
                matches.download()
    """
    # Un-zip downloaded
    download_dir_path = os.getcwd()
    for item in os.listdir(download_dir_path):
        if item.startswith('S1') and item.endswith('.zip'):
            with zipfile.ZipFile(item, 'r') as zipObj:
                zipObj.extractall()
    """
    return 0



def S2_data(aoi:list, path:str):
    """Retrieve Sentinel-2 data, using HDA API.

    Args:
        aoi (list): Area of interest bounding box coordinates.
        path (str): Location where retrieved data will be saved and\
            'S2_products.csv' is saved.

    Returns:
        _type_: _description_
    """
    minx, miny, maxx, maxy = aoi

    def _queryArgs(s2_products_file:pd.Series)->Tuple[str,str,str]:
        """Function to apply on S2_products.csv and source info about one image to form\
            an HDA API request. Info concerns datetime and tilename.

        Args:
            s2_products_file (pd.Series): S2_products.csv containing fields with info about\
                'beginposition', 'endposition' and 'title'.

        Returns:
            Tuple[str,str,str]: [start_date, end_date, tilename]
        """
        # Temporal arguments
        beginposition = s2_products_file['beginposition']
        beginposition = datetime.datetime.strptime(beginposition, '%Y-%m-%d %H:%M:%S.%f')
        beginposition = beginposition.strftime('%Y-%m-%dT%H:%M:%S.%f')
        
        endposition = s2_products_file['endposition']
        endposition = datetime.datetime.strptime(endposition, '%Y-%m-%d %H:%M:%S.%f')
        endposition = endposition.strftime('%Y-%m-%dT%H:%M:%S.%f')

        # Datetime strings
        start_date, end_date = f'{beginposition[:-3]}Z', f'{endposition[:-3]}Z'

        # Tilename
        tilename = s2_products_file['title'].split('_')[5]

        return start_date, end_date, tilename

    # Read .csv downloaded by class Download_S2_data
    s2_prod = pd.read_csv(os.path.join(path, 'S2_products.csv'))
    
    # For each entry in 'S2_products.csv', define temporal arguments and tilename
    for index, row in s2_prod.iterrows():
        start_date, end_date, tilename = _queryArgs(row)

        request = {
            'datasetId': 'EO:ESA:DAT:SENTINEL-2:MSI',
            'boundingBoxValues': [{
                'name': 'area',
                'bbox': [minx, miny, maxx, maxy]
            }],
            'dateRangeSelectValues': [{
                'name': 'position',
                'start': start_date,
                'end': end_date
            }],
            'stringChoiceValues': [{
                'name': 'processingLevel',
                'value': 'LEVEL2A'
            }],
            'stringInputValues':[{
                "name": "productIdentifier",
                "value": tilename
            }]
        }
        # print(f"\n{index} {request}")
        
        os.chdir(path)
        c = Client()
        matches = c.search(request)
        print(f"Downloading matches: {len(vars(matches)['results'])}")
        for m in vars(matches)['results']:
            if os.path.exists(os.path.join(path, m['filename'])):
                print(f"{m['filename']} Already Exists")
                pass
            else:
                print(m['filename'])
                matches.download()
    
    # Un-zip downloaded & delete zip files
    download_dir_path = os.getcwd()
    for item in os.listdir(download_dir_path):
        if item.startswith('S2') and item.endswith('.zip'):
            with zipfile.ZipFile(item, 'r') as zipObj:
                zipObj.extractall()
            os.remove(item)
    return 0
