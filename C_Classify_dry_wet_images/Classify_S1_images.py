#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Define a baseline dataset based on ERA-5 variables
Plots the dates of the SAR images and the Rain time series

Copyright (C) 2021 by K.Karamvasis

Email: karamvasis_k@hotmail.com
Last edit: 01.4.2021

This file is part of FLOMPY - FLOod Mapping PYthon toolbox.

    FLOMPY is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FLOMPY is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FLOMPY. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

import netCDF4
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import glob
import os
import datetime

def cftime_to_datetime(cfdatetime):
    year=cfdatetime.year
    month=cfdatetime.month
    day=cfdatetime.day
    hour=cfdatetime.hour
    minute=cfdatetime.minute
    second=cfdatetime.second
    return datetime.datetime(year,month,day,hour,minute,second)


def Get_images_for_baseline_stack(netcdf_file,
                                  S1_GRD_dir,
                                  export_filename,
                                  Start_time,
                                  End_time,
                                  flood_datetime,
                                  days_back=5,
                                  rain_thres=20):
    ERA5_data=netCDF4.Dataset(netcdf_file)
    
    # lons=ERA5_data['longitude'][:]
    # lats=ERA5_data['latitude'][:]
    # u_component_of_wind=ERA5_data['u10'][:]
    # v_component_of_wind=ERA5_data['v10'][:]
    # temperature=ERA5_data['t2m'][:]
    # precipitation_type=ERA5_data['ptype'][:]
    # run_off=ERA5_data['ro'][:]
    # snowfall=ERA5_data['sf'][:]
    # soil_temperature_level_1=ERA5_data['stl1'][:]
    # total_precipitation=ERA5_data['tp'][:]
    # volumetric_soil_water_layer_1=ERA5_data['swvl1'][:]
    #Rain_Venice=np.squeeze(Rain)
    
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
    df = pd.DataFrame(df_dict)
    df.index = df['Datetimes']
    
    df=df[Start_time:End_time]
    
    # convert units to millimeters
    
    # df['ro__mm']=df['ro__m']*1000
    df['tp__mm']=df['tp__m']*1000
    
    # calculate cumulative rain over the last 5 days for each date
    Precipitation_data=df['tp__mm']

    df2 = (Precipitation_data.shift().rolling(window=24*days_back, min_periods=1).sum()
           .reset_index())
    
    df2.index=df2['Datetimes']
    df2.drop(columns=['Datetimes'], inplace=True)
    # df2['swvl1__m**3 m**-3']=df['swvl1__m**3 m**-3']
    # df2['ro__mm']=df['ro__mm']
    # df2['sf__m of water equivalent']=df['sf__m of water equivalent']
    
    # get the S1_dates
    S1_products=glob.glob(S1_GRD_dir+'/*.zip')
    S1_dates=[ pd.Timestamp(os.path.basename(S1_product)[17:32]) for S1_product in S1_products ]
    

    S1_df=pd.DataFrame(index=S1_dates, columns=['S1_GRD'], data=S1_products)
    S1_df.sort_index(inplace=True)
    # plot
    
    ax = df2[['tp__mm']].plot()
    ymin, ymax = ax.get_ylim()
    ax.vlines(x=S1_dates, ymin=ymin, ymax=ymax-1, color='k', linestyle='--')
    plt.savefig(export_filename+'.svg')
    plt.close()
    
    # get values at the specific S1_dates
    for S1_date in S1_dates:
        df2=df2.append(pd.DataFrame(index=[S1_date]))
        
    
    # create a dataframe with the accumulated precipitation values at S1 dates
    
    df2 = df2.sort_index()
    df2=df2.interpolate()
    Sum_5D_Precipitation_S1_date=df2.loc[S1_dates]
    Sum_5D_Precipitation_S1_date.sort_index(inplace=True)
    
    Good_images_for_baseline = pd.DataFrame(index=Sum_5D_Precipitation_S1_date.index)
    Good_images_for_baseline['tp__mm']=Sum_5D_Precipitation_S1_date['tp__mm'].tolist()
    Good_images_for_baseline['baseline']=(Sum_5D_Precipitation_S1_date['tp__mm']<rain_thres).tolist()
    
    Good_images_for_baseline['baseline'].loc[flood_datetime:]=False
    
    if np.all(S1_df.index==Good_images_for_baseline.index)==True:
        Good_images_for_baseline['S1_GRD']=S1_df['S1_GRD']
    Good_images_for_baseline.to_pickle(export_filename)
    
    return Good_images_for_baseline
    
    

