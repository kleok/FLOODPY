#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cdsapi
import datetime
import pandas as pd
import numpy as np
import netCDF4

def cftime_to_datetime(cfdatetime:datetime.datetime)->datetime.datetime:
    """Time convertion functionality.

    Args:
        cfdatetime (datetime.datetime): Datetime object to be converted

    Returns:
        datetime.datetim: Converted datetime object
    """

    year=cfdatetime.year
    month=cfdatetime.month
    day=cfdatetime.day
    hour=cfdatetime.hour
    minute=cfdatetime.minute
    second=cfdatetime.second
    return datetime.datetime(year,month,day,hour,minute,second)

def retrieve_ERA5_data(ERA5_variables:list, year_str:str, month_str:str, days_list:list, time_list:list, bbox_cdsapi:list, export_filename:str)->str: 
    """
    Gets data from ERA-5 (ECMWF) re-analysis dataset with daily global geographical with 0.25 deg (~31 km) spatial resolution. Note that data availability
    has a ~3-month latency

    Args:
        ERA5_variables (list): List of ERA5 variables
        year_str (str): Year
        month_str (str): Month
        days_list (list): days
        time_list (list): times (UTC)
        bbox_cdsapi (list): geographical borders
        export_filename (str): full path of dataset

    Returns:
        export_filename (string): Full path of dataset
    """

    c = cdsapi.Client(quiet=True)
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': ERA5_variables,
            'year': year_str,
            'month': month_str,
            'day': days_list,
            'time': time_list,
            'area': bbox_cdsapi,
            'format': 'netcdf',
        },
        export_filename)
        
    return export_filename
 
def Get_ERA5_data(ERA5_variables:list,
                 start_datetime:datetime.datetime,
                 end_datetime:datetime.datetime,
                 bbox:list,
                 ERA5_dir:str) -> pd.DataFrame:
    
    """Downloads ERA5 datasets between two given dates.

    Args:
        ERA5_variables (list): list of ERA5 variables e.g. ['total_precipitation',]
        start_datetime (datetime.datetime): Starting Datetime e.g.  datetime.datetime(2021, 12, 2, 0, 0)
        end_datetime (datetime.datetime): Ending Datetime e.g.  datetime.datetime(2022, 2, 8, 0, 0)
        bbox (list): List of latitude/longitude [LONMIN, LATMIN,  LONMAX, LATMAX]
        ERA5_dir (str): Path that ERA5 data will be saved.

    Returns:
        Precipitation_data (pd.DataFrame): precipitation data
    """
    
    LONMIN, LATMIN,  LONMAX, LATMAX = bbox
    bbox_cdsapi = [LATMAX, LONMIN, LATMIN, LONMAX, ]

    # change end_datetime in case ERA5 are not yet available
    if datetime.datetime.now()-end_datetime < datetime.timedelta(days=5):
        end_datetime = datetime.datetime.now() - datetime.timedelta(days=5)

    precipitation_filename_df = os.path.join(ERA5_dir,'ERA5_{Start_time}_{End_time}_{bbox_cdsapi}.csv'.format(Start_time=start_datetime.strftime("%Y%m%dT%H%M%S"),
                                                                                            End_time=end_datetime.strftime("%Y%m%dT%H%M%S"),
                                                                                            bbox_cdsapi='_'.join(str(round(e,5)) for e in bbox_cdsapi)))
    
    if not os.path.exists(precipitation_filename_df):
        
        Downloaded_datasets = []
        
        df = pd.date_range(start=start_datetime, end=end_datetime, freq='H').to_frame(name='Datetime')
        
        df['year'] = df['Datetime'].dt.year
        df["year_str"] = ['{:02d}'.format(year) for year in df['year']]
        
        df['month'] = df['Datetime'].dt.month
        df["month_str"] = ['{:02d}'.format(month) for month in df['month']]
        
        df['day'] = df['Datetime'].dt.day
        df["day_str"] = ['{:02d}'.format(day) for day in df['day']]

        df['hour'] = df['Datetime'].dt.hour
        df["hour_str"] = ['{:02d}'.format(hour) for hour in df['hour']]
        
        
        # for the last datetime we do a single request
        
        last_day_df = df.sort_values(by = 'Datetime').iloc[-1]
        last_day_times = np.arange(last_day_df.hour+1)
        last_day_times_str = ['{:02d}'.format(last_day_time) for last_day_time in last_day_times]
        #print("Downloading precipitation for the flood date: {}".format(last_day_df.Datetime.strftime("%Y-%m-%d")))

        last_day_dataset = retrieve_ERA5_data(ERA5_variables = ERA5_variables,
                                              year_str = last_day_df.year_str,
                                              month_str = last_day_df.month_str,
                                              days_list = last_day_df.day_str,
                                              time_list = last_day_times_str,
                                              bbox_cdsapi = bbox_cdsapi,
                                              export_filename = os.path.join(ERA5_dir,'Flood_day_precipitation.nc'))
        
        Downloaded_datasets.append(last_day_dataset)
        
        # For each month we do a request
        df2 = df.truncate(after=datetime.datetime(last_day_df.year, last_day_df.month, last_day_df.day, 0)).iloc[:-1]
        
        for year in np.unique(df2["year_str"].values):
            df_year = df2[df2['year_str']==year]
            year_request = year
            for month in np.unique(df_year["month_str"].values):
                month_request = month
                print("Downloading precipitation for month {} of year {} ...".format(month_request, year_request))
                df_month = df_year[df_year['month_str']==month]
                days_request = np.unique(df_month['day_str']).tolist()
                hours_request = np.unique(df_month['hour_str']).tolist()
                
                monthly_dataset = retrieve_ERA5_data(ERA5_variables = ERA5_variables,
                                                      year_str = year_request,
                                                      month_str = month_request,
                                                      days_list = days_request,
                                                      time_list = hours_request,
                                                      bbox_cdsapi = bbox_cdsapi,
                                                      export_filename = os.path.join(ERA5_dir,
                                                                                     '{}_{}_precipitation.nc'.format(month_request,
                                                                                                                     year_request)))
                
                Downloaded_datasets.append(monthly_dataset)
                
        # Merge the downloaded datasets and save them to a csv file.
        
        Precipitation_data = pd.DataFrame( index = df.index)
        for downloaded_dataset in Downloaded_datasets:
            
            ERA5_data=netCDF4.Dataset(downloaded_dataset)
            ERA5_variables = list(ERA5_data.variables.keys())
        
            df_dict={}
            for ERA5_variable in ERA5_variables:
                
                if ERA5_variable in ['longitude',  'latitude', 'number']:
                    pass
                elif ERA5_variable=='valid_time':
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
            temp_df = df_ERA5_tp['tp__mm']
            temp_df.index = pd.to_datetime(temp_df.index)
            Precipitation_data = pd.concat([temp_df,Precipitation_data], axis=1)
            
        Precipitation_data = Precipitation_data.fillna(0).sum(axis=1).to_frame(name='ERA5_tp_mm')
        Precipitation_data['Datetime'] = Precipitation_data.index
        # in some cases ERA5 precipitation return negative values (issue #36)
        Precipitation_data['ERA5_tp_mm'].clip(lower=0, inplace=True)
        Precipitation_data.to_csv(precipitation_filename_df, index=False)
    
    else: # precipitation data have already been downloaded
        Precipitation_data = pd.read_csv(precipitation_filename_df)
        Precipitation_data.index = pd.to_datetime(Precipitation_data['Datetime'])

    return Precipitation_data