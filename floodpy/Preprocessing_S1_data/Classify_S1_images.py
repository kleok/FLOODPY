#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
import glob
import os

def Get_images_for_baseline_stack(projectfolder,
                                  S1_dir,
                                  Precipitation_data,
                                  flood_datetime,
                                  days_back=5,
                                  rain_thres=20):
    '''
    Creates a pandas DataFrame of Sentinel-1 acquisitions. Creates a column with
    boolean values with name 'baseline'. If True the particular acquisition 
    can be used for calculation of baseline stack

    '''
    Precipitation_data.index = Precipitation_data['Datetime']
    Precipitation_data.drop(columns = ['Datetime'], inplace=True)

    # calculate cumulative rain over the past days (given) for each date
    df2 = (Precipitation_data.shift().rolling(window=24*days_back, min_periods=1).sum()
           .reset_index())
    
    df2.index=pd.to_datetime(Precipitation_data.index)
    df2.drop(columns=['Datetime'], inplace=True)

    # get the S1_dates
    S1_products=glob.glob(S1_dir+'/*.zip')
    S1_dates=[pd.Timestamp(os.path.basename(S1_product)[17:32]) for S1_product in S1_products ]
    S1_df=pd.DataFrame(index=S1_dates, columns=['S1_GRD'], data=S1_products)
    S1_df.sort_index(inplace=True)
    
    # plot
    ax = df2[['ERA5_tp_mm']].plot()
    ymin, ymax = ax.get_ylim()
    ax.vlines(x=S1_dates, ymin=ymin, ymax=ymax-1, color='k', linestyle='--')
    plt.savefig(os.path.join(projectfolder,'baseline_images.png'), dpi=200)
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
    Good_images_for_baseline['ERA5_tp_mm']=Sum_5D_Precipitation_S1_date['ERA5_tp_mm'].tolist()
    Good_images_for_baseline['baseline']=(Sum_5D_Precipitation_S1_date['ERA5_tp_mm']<rain_thres).tolist()
    
    Good_images_for_baseline['baseline'].loc[flood_datetime:]=False
    
    # make sure the Image corresponds to flood state is not selected for
    # baseline stack creation
    flood_S1_image_filename = os.path.join(S1_dir,'flood_S1_filename.csv')
    assert os.path.exists(flood_S1_image_filename)
    flood_S1_image = pd.read_csv(flood_S1_image_filename, index_col=0).loc['title'].values[0]
    flood_S1_datetime = pd.Timestamp(flood_S1_image[17:32])
    
    Good_images_for_baseline['baseline'].loc[flood_S1_datetime:]=False
    assert np.all(S1_df.index==Good_images_for_baseline.index)==True
    
    Good_images_for_baseline['S1_GRD']=S1_df['S1_GRD']
    Good_images_for_baseline['Datetime'] =  pd.to_datetime(S1_df.index)
    Good_images_for_baseline.to_csv(os.path.join(S1_dir,'baseline_images.csv'), index=False)
    
    return 0
    
    

