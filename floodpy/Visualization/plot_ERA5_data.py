import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
warnings.filterwarnings('ignore')


def plot_ERA5(Floodpy_app):
    daily_precipitation_df = Floodpy_app.precipitation_df.resample('D').sum()
    daily_precipitation_df.rename(columns={"ERA5_tp_mm": "ERA5 Daily Precipitation (mm)"}, inplace=True)

    # Set up figure
    fig, ax = plt.subplots()
    # Plot bars
    daily_precipitation_df.plot.bar(figsize=(17, 7), grid=True, ax=ax)
    # Make most of the ticklabels empty so the labels don't get too crowded
    ticklabels = ['']*len(daily_precipitation_df.index)
    # Every 4th ticklable shows the month and day
    ticklabels[::2] = [item.strftime('%b %d') for item in daily_precipitation_df.index[::2]]
    # Every 12th ticklabel includes the year
    ticklabels[::12] = [item.strftime('%b %d\n%Y') for item in daily_precipitation_df.index[::12]]
    ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))

    handles, label1  = ax.get_legend_handles_labels()

    pre_flood_start_pos = daily_precipitation_df.index.searchsorted(pd.to_datetime(Floodpy_app.pre_flood_datetime_start))-1
    pre_flood_start_line = ax.axvline(pre_flood_start_pos, color=(1, 0.5 , 1, 0.5), linestyle='--', label = 'Pre-flood start time')
    handles.append(pre_flood_start_line)

    pre_flood_end_pos = daily_precipitation_df.index.searchsorted(pd.to_datetime(Floodpy_app.pre_flood_datetime_end))-1
    pre_flood_end_line = ax.axvline(pre_flood_end_pos, color=(1, 0.5 , 1, 0.5), linestyle='--', label = 'Pre-flood end time')
    handles.append(pre_flood_end_line)

    flood_start_pos = daily_precipitation_df.index.searchsorted(pd.to_datetime(Floodpy_app.flood_datetime_start))-1
    flood_start_line = ax.axvline(flood_start_pos, color=(0, 0, 0, 0.5), linestyle='--', label = 'Flood start time')
    handles.append(flood_start_line)


    flood_end_pos = daily_precipitation_df.index.searchsorted(pd.to_datetime(Floodpy_app.flood_datetime_end))-1
    flood_end_line = ax.axvline(flood_end_pos, color=(0, 0, 0, 0.5), linestyle='--', label = 'Flood end time')
    handles.append(flood_end_line)

    labels = [label1[0],"Pre-flood start time", "Pre-flood end time", "Flood start time", "Flood end time"]
    plt.legend(handles = handles[:], labels = labels)

    # Add x-y axis labels
    ax.set_ylabel("Precipitation (mm)")


    return ax