#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloads ERA-5 variables

  re-analysis_dataset         coverage   temporal_resolution  spatial_resolution      latency     analysis
  --------------------------------------------------------------------------------------------------------
  ERA-5    (ECMWF)             Global      Hourly              0.25 deg (~31 km)       3-month      4D-var



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
    along with GECORIS. If not, see <https://www.gnu.org/licenses/>.
"""
###############################################################################

print('FLOod Mapping PYthon toolbox (FLOMPY) v.1.0')
print('Copyright (c) 2021 Kleanthis Karamvasis, karamvasis_k@hotmail.com')
print('Remote Sensing Laboratory of National Tecnical University of Athens')
print('-----------------------------------------------------------------')
print('License: GNU GPL v3+')
print('-----------------------------------------------------------------')

import os
import cdsapi
import datetime

def months_between(start_datetime, end_datetime):
    """
    Given two instances of ``datetime.date``, the function returns a list of dates on
    the 1st of every month between the two dates (inclusive).

    e.g. "5 Jan 2020" to "17 May 2020" would generate:

        1 Jan 2020, 1 Feb 2020, 1 Mar 2020, 1 Apr 2020, 1 May 2020

    """
    if start_datetime > end_datetime:
        raise ValueError(f"Start date {start_datetime} is not before end date {end_datetime}")
    
    months=[]
    year = start_datetime.year
    month = start_datetime.month
    months.append(month)
    
    while (year, month) <= (end_datetime.year, end_datetime.month):
        yield datetime.date(year, month, 1)

        # Move to the next month.  If we're at the end of the year, wrap around
        # to the start of the next.
        #
        # Example: Nov 2017
        #       -> Dec 2017 (month += 1)
        #       -> Jan 2018 (end of year, month = 1, year += 1)
        #
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
            
        months.append(month)
        
    return months

def Get_ERA5_data_single_datetime(S1_datetime, bbox, ERA5_variables, export_filename):
    '''
    Downloads ERA5 product for a single datetime object.
    '''
    c = cdsapi.Client()
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': ERA5_variables,
            'year': str(S1_datetime.year),
            'month': str(S1_datetime.month),
            'day': str(S1_datetime.day),
            'time': [
                '00:00', '01:00', '02:00',
                '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00',
                '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00',
                '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00',
                '21:00', '22:00', '23:00',
            ],
            'area': bbox,
            'format': 'netcdf',
        },
        export_filename)

def Get_ERA5_data_time_period(ERA5_variables, Start_time, End_time, bbox, ERA5_dir):
    
    if not os.path.exists(ERA5_dir): os.mkdir(ERA5_dir)
    export_filename = os.path.join(ERA5_dir,'ERA5_{Start_time}_{End_time}_{bbox}.nc'.format(Start_time=Start_time,
                                                                                            End_time=End_time,
                                                                                            bbox='_'.join(str(e) for e in bbox)))
    
    if not os.path.exists(export_filename):
        start_datetime = datetime.datetime(int(Start_time[0:4]),
                                           int(Start_time[4:6]),
                                           int(Start_time[6:8]))
        start_datetime= start_datetime - datetime.timedelta(days=5)
        
        end_datetime = datetime.datetime(int(End_time[0:4]),
                                         int(End_time[4:6]),
                                         int(End_time[6:8]))
        
        if start_datetime.year == end_datetime.year:
            year=start_datetime.year
        else:
            year=[start_datetime.year, end_datetime.year]
        
        months=list(months_between(start_datetime, end_datetime))
        months_str=['{:02d}'.format(month.month) for month in months]
        
        c = cdsapi.Client()
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': ERA5_variables,
                'year': year,
                'month': months_str,
                'day': [
                '01', '02', '03',
                '04', '05', '06',
                '07', '08', '09',
                '10', '11', '12',
                '13', '14', '15',
                '16', '17', '18',
                '19', '20', '21',
                '22', '23', '24',
                '25', '26', '27',
                '28', '29', '30',
                '31',
                ],
                'time': [
                    '00:00', '01:00', '02:00',
                    '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00',
                    '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00',
                    '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00',
                ],
                'area': bbox,
                'format': 'netcdf',
            },
            export_filename)
        
    return export_filename
    
