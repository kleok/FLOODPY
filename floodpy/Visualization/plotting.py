import os
import glob
import numpy as np
from osgeo import gdal
import rasterio as rio
import rasterio.mask
import geopandas as gpd
import pandas as pd
import h5py
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as ticker
import branca.colormap as cm
from branca.element import Template, MacroElement
import folium
from folium.plugins import MeasureControl, Draw

from floodpy.utils.folium_categorical_legend import get_folium_categorical_template
from floodpy.FLOODPYapp import FloodwaterEstimation


class Floodpy_plotting:
    """ Routine processing workflow for floodwater estimation from satellite
    remote sensing data.
    """
    def __init__(self, Floodpy_app: FloodwaterEstimation) -> None:
        self.app = Floodpy_app

    def plot_precipitation(self):
        precipitation_df = pd.read_csv(glob.glob(os.path.join(self.app.projectfolder,'ERA5/*.csv'))[0])
        precipitation_df['Datetime'] = pd.to_datetime(precipitation_df['Datetime'])
        precipitation_df.index = pd.to_datetime(precipitation_df['Datetime'])

        # calculating Daily Total Precipitation
        precipitation_df = precipitation_df.groupby(pd.Grouper(key='Datetime', axis=0,freq='D')).sum()
        precipitation_df.rename(columns={"ERA5_tp_mm": "Daily Total Precipitation (mm)"}, inplace=True)

        #plotting
        ax = precipitation_df.plot(kind='bar', title='Precipitation time series for {} case study'.format(self.Projectname))
        ax.axvline(pd.to_datetime(self.Flood_datetime), color="black", linestyle="dashed", lw=2)

        # Make most of the ticklabels empty so the labels don't get too crowded
        ticklabels = ['']*len(precipitation_df.index)
        # Every 4th ticklable shows the month and day
        ticklabels[::4] = [item.strftime('%b %d') for item in precipitation_df.index[::4]]
        # Every 12th ticklabel includes the year
        ticklabels[::12] = [item.strftime('%b %d\n%Y') for item in precipitation_df.index[::12]]
        ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))
        # Add x-y axis labels
        ax.set_xlabel("Date")
        ax.set_ylabel("Precipitation (mm)")

        plt.show()
        self.precipitation_plot = ax

    def plot_S1_precipitation(self):
        # append nan values in case ERA5 data are not available
        if pd.to_datetime(self.app.flood_datetime.date()) not in precipitation_df.index:
            precipitation_df = precipitation_df.append(pd.DataFrame({'Daily Total Precipitation (mm)':np.nan},
                                                                    index=[pd.to_datetime(self.app.flood_datetime.date())]))
            precipitation_df = precipitation_df.resample('1D').fillna(method=None)

        # Set up figure
        fig, ax = plt.subplots()
        # Plot bars
        precipitation_df.plot.bar(figsize=(17, 7), grid=True, ax=ax)
        # Make most of the ticklabels empty so the labels don't get too crowded
        ticklabels = ['']*len(precipitation_df.index)
        # Every 4th ticklable shows the month and day
        ticklabels[::2] = [item.strftime('%b %d') for item in precipitation_df.index[::2]]
        # Every 12th ticklabel includes the year
        ticklabels[::12] = [item.strftime('%b %d\n%Y') for item in precipitation_df.index[::12]]
        ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))

        S1_images = pd.read_csv(os.path.join(self.app.S1_dir,'baseline_images.csv'))
        S1_images.index = pd.to_datetime(S1_images['Datetime'])
        handles, label1  = ax.get_legend_handles_labels()

        for index, S1_image in S1_images.iterrows():
            x_axis_pos = precipitation_df.index.searchsorted(pd.to_datetime(S1_image['Datetime']))-1
            if S1_image['baseline']:
                S1_pre_flood_line = ax.axvline(x_axis_pos,
                                            color=(0, 0, 0, 0.5),
                                            linestyle='--',
                                            label = 'Pre-flood S1 product')
            else:
                S1_flood_line = ax.axvline(x_axis_pos,
                                        color=(1, 0, 0, 0.5),
                                        linestyle='-',
                                        label = 'Flood S1 product')
                
        handles.append(S1_pre_flood_line)
        handles.append(S1_flood_line)

        User_flood_line = ax.axvline(precipitation_df.index.searchsorted(pd.to_datetime(self.Flood_datetime))-1,
                                                                                        color=(0, 0, 1, 0.5),
                                                                                        linestyle='-',
                                                                                        label = 'User Flood datetime')

        handles.append(User_flood_line)

        labels = [label1[0], "Pre-flood S1 acquisition", "Flood S1 acquisition", "User defined Flood Datetime"]
        plt.legend(handles = handles[:], labels = labels)

        self.S1_precipitation_plot = fig

    def plot_all_S1(self):

        SAR_stack_file=os.path.join(self.app.Preprocessing_dir,'Stack/SAR_Stack.h5')
        plot_stack=h5py.File(SAR_stack_file,'r')
        number_of_images=plot_stack['Datetime_SAR'].shape[0]
        # plot the backscatter information of all the  pre flood Sentinel-1 acquisitions
        layers=['VV_db','VH-db','VV_VH_db']
        S1_plots = []
        for band_index, image in enumerate(range(number_of_images)):
                    if band_index==0:
                        vmin=np.nanquantile(plot_stack[layers[0]][band_index,...].flatten(), 0.01)
                        vmax=np.nanquantile(plot_stack[layers[0]][band_index,...].flatten(), 0.99)

                    plt.figure(figsize = (10,10))
                    ax = plt.gca()
                    im = ax.imshow(plot_stack[layers[0]][band_index,...],
                                vmin=vmin,
                                vmax=vmax)
                    # add title
                    S1_acquisition_time = pd.to_datetime(plot_stack['Datetime_SAR'][band_index].decode("utf-8"))
                    plt.title("S1 at: {}".format(S1_acquisition_time))
                    
                    # add colorbar
                    divider = make_axes_locatable(ax)
                    cax = divider.append_axes("right", size="2%", pad=0.05)
                    cbar = plt.colorbar(im, cax=cax)
                    cbar.set_label('{}'.format('Decibel'), rotation=270)
                    plt.tight_layout()
                    S1_plots.append(im)

        self.S1_plots = S1_plots

    def plot_tscores(self):
        # plot the t-score maps (changes of backscatter information) pre-flood and post-flood
        t_score_filename = glob.glob(os.path.join(self.app.Results_dir,'t_scores*.tif'))[0]
        t_score_image = gdal.Open(t_score_filename).ReadAsArray()
        vmin=np.nanquantile(t_score_image.flatten(), 0.01)
        vmax=np.nanquantile(t_score_image.flatten(), 0.99)
        plt.figure(figsize = (10,8))
        ax = plt.gca()
        im = ax.imshow(t_score_image,
                    vmin=vmin,
                    vmax=vmax)

        # add title
        flood_S1_image_filename = os.path.join(self.app.S1_dir,'flood_S1_filename.csv')
        S1_acquisition_datetime = pd.read_csv(flood_S1_image_filename, index_col=0)
        S1_flood_datetime = pd.to_datetime(S1_acquisition_datetime.loc['beginposition'].values[0])
        S1_flood_str = S1_flood_datetime.strftime('%Y-%m-%d %H:%M')

        pre_flood = os.path.join(self.app.S1_dir,'baseline_images.csv')
        pre_flood_images = pd.read_csv(pre_flood)
        S1_preflood_datetimes = pre_flood_images['Datetime'][pre_flood_images['baseline']==True].values
        S1_preflood_datetimes = [pd.to_datetime(pre_flood_datetime).strftime('%Y-%m-%d %H:%M') for pre_flood_datetime in S1_preflood_datetimes]

        plt.title("t-scores between {} and\n {}".format(S1_flood_str, S1_preflood_datetimes))

        # add colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="1%", pad=0.05)
        cbar = plt.colorbar(im, cax=cax)
        cbar.set_label('{}'.format('t-score change'), rotation=90)
        plt.tight_layout()

        self.tscores_plot = im

    def  plot_multimodality_mask(self):

        t_score_filename = glob.glob(os.path.join(self.app.Results_dir,'t_scores*.tif'))[0]
        t_score_image = gdal.Open(t_score_filename).ReadAsArray()
        vmin=np.nanquantile(t_score_image.flatten(), 0.01)
        vmax=np.nanquantile(t_score_image.flatten(), 0.99)
        plt.figure(figsize = (10,8))
        ax = plt.gca()
        im = ax.imshow(t_score_image,
                    vmin=vmin,
                    vmax=vmax)
        ax.imshow(self.app.multimodality_mask>0, alpha=0.3, cmap = 'Reds')
        plt.title("Bi/Multi modality mask over t-scores.")
        self.multimodality_mask_plot = im

    def plot_histogram_threshold(self):
        t_score_filename = glob.glob(os.path.join(self.app.Results_dir,'t_scores*.tif'))[0]
        t_score_image = gdal.Open(t_score_filename).ReadAsArray()
        t_score_values = t_score_image.flatten()
        vmin = np.nanquantile(t_score_values, 0.005)
        vmax = np.nanquantile(t_score_values, 0.995)
        t_score_values[t_score_values>vmax]=np.nan
        t_score_values[t_score_values<vmin]=np.nan
        t_score_values = t_score_values[~np.isnan(t_score_values)]

        t_score_values_BC = t_score_image[self.app.multimodality_mask].flatten()
        vmin_BC = np.nanquantile(t_score_values_BC, 0.005)
        vmax_BC = np.nanquantile(t_score_values_BC, 0.995)
        t_score_values_BC[t_score_values_BC>vmax_BC]=np.nan
        t_score_values_BC[t_score_values_BC<vmin_BC]=np.nan
        t_score_values_BC = t_score_values_BC[~np.isnan(t_score_values_BC)]

        plt.figure(figsize=(8,6))
        plt.hist(t_score_values, bins=100, alpha=0.5, label="All regions")
        plt.hist(t_score_values_BC, bins=100, alpha=0.5, label="Multi/Bi modal regions")
        plt.title("T-score histogram over all regions and only over regions with Multi/Bi modality")
        plt.xlabel("T-scores", size=11)
        plt.ylabel("Count", size=11)
        plt.legend(loc='upper right')

        plt.axvline(self.app.glob_thresh, color='r', label='axvline - full height')
        plt.text(self.app.glob_thresh+0.5,0,'Global Otsu threshold',rotation=90)

    def plot_interactive_map(self, S2_background: bool, landcover: bool):

        # Downloads requested data for  visualization
        if S2_background:
            self.app.run_download_landcover('Download_worldcover_LC')
        if landcover:
            self.app.run_download_S2_background('Download_S2_background')

        # Read AOI
        aoi = gpd.read_file(self.app.geojson_S1)

        # AOI bounds
        left, bottom, right, top = aoi.total_bounds

        # Define map bounds
        map_bounds = [[bottom, left], [top, right]]

        # Create a map located to the AOI
        m = folium.Map(location=[aoi.centroid.y[0], aoi.centroid.x[0]], tiles="Stamen Terrain", zoom_start=13)

        folium.TileLayer('openstreetmap').add_to(m)
        folium.TileLayer('cartodbdark_matter').add_to(m)
        folium.TileLayer('Stamen Terrain').add_to(m)

        # measuring funcs
        MeasureControl('bottomleft').add_to(m)

        # drawing funcs
        draw = Draw(export = True,
                    filename=os.path.join(self.projectfolder,'myJson.json'),
                    position='topleft').add_to(m)

        # add geojson AOI
        folium.GeoJson(aoi["geometry"],
                    show = False,
                    name='Area of Interest').add_to(m)

        #------------------------------------------------------------------------------
        # Sentinel-2 background
        if hasattr(self.app, 'S2_RGB_background'):
            with rio.open(self.app.S2_RGB_background) as src:
                S2_RGB_background = src.read()
                S2_RGB_background = np.swapaxes(S2_RGB_background,0,2)
                S2_RGB_background = np.swapaxes(S2_RGB_background,0,1)
                
            S2_map = folium.raster_layers.ImageOverlay(image = S2_RGB_background,
                                                    name = 'Recent S2 RGB background',
                                                    opacity = 1,
                                                    show = False,
                                                    bounds = map_bounds)
            
            m.add_child(S2_map)
        #------------------------------------------------------------------------------
        # ESA worldcover 
        if hasattr(self.app, 'LC_worldcover'):
            with rio.open(self.app.LC_worldcover) as src:
                LC_cover, out_transform = rasterio.mask.mask(src, aoi.geometry, crop=True)
                LC_cover = LC_cover[0,:,:]


            LC_map = folium.raster_layers.ImageOverlay(image = LC_cover,
                                                    name = 'ESA Worldcover 2021',
                                                    opacity = 1,
                                                    bounds = map_bounds,
                                                    show = False,
                                                    colormap = lambda x: self.app.LC_worldcover_colors[x])

            m.add_child(LC_map)

            template = get_folium_categorical_template()
            macro = MacroElement()
            macro._template = Template(template) 
            m.get_root().add_child(macro)

        #------------------------------------------------------------------------------
        # S1 VV backscatter Flood image
        S1_images = pd.read_csv(os.path.join(self.app.S1_dir,'baseline_images.csv'))
        S1_floodtime = pd.to_datetime(S1_images[S1_images['baseline']==False]['Datetime'].values[0])
        S1_floodtime_str = S1_floodtime.strftime('%Y%m%dT%H%M%S')
        S1_tiff_path = os.path.join(self.app.Preprocessing_dir,'{}.tif'.format(S1_floodtime_str))

        with rio.open(S1_tiff_path) as src:
            S1_data, out_transform = rasterio.mask.mask(src, aoi.geometry, crop=True)
            S1_data = S1_data[0,:,:]  

        # convert to dB
        S1_data = 10*np.log10(S1_data.copy())
        S1_data_values = S1_data[np.isfinite(S1_data)]
        vmin = np.nanquantile(S1_data_values, 0.01)
        vmax = np.nanquantile(S1_data_values, 0.99)

        S1_data = np.clip(S1_data, vmin, vmax)

        cmap = cm.LinearColormap(['black', 'white'],
                                    index=[vmin, vmax],
                                    vmin=vmin, vmax=vmax)

        cmap.caption = "Backscatter coefficient VV (dB)"
        cmap_func = lambda x: matplotlib.colors.to_rgba(cmap(x)) if ~np.isnan(x) else (0,0,0,0)

        folium.raster_layers.ImageOverlay(image = S1_data,
                                        name = "Sentinel-1 ({})".format(S1_floodtime),
                                        opacity = 1,
                                        bounds = map_bounds,
                                        colormap = cmap_func).add_to(m)
        m.add_child(cmap)

        #------------------------------------------------------------------------------
        # # t-scores
        # t_scores_fpath = os.path.join(app.Results_dir, 't_scores_VV_VH_db.tif')
        # with rio.open(t_scores_fpath) as src:
        #     t_scores, out_transform = rasterio.mask.mask(src, aoi.geometry, crop=True)
        #     t_scores = t_scores[0,:,:]  

        # vmin = np.nanquantile(t_scores.flatten(), 0.005)
        # vmax = np.nanquantile(t_scores.flatten(), 0.995)
        # t_scores = np.clip(t_scores, vmin, vmax)

        # cmap = cm.LinearColormap(['red', 'white', 'lightgreen'],
        #                                index=[vmin, 0, vmax],
        #                                vmin=vmin, vmax=vmax)

        # cmap.caption = 'T-scores (changes)'
        # cmap_func = lambda x: matplotlib.colors.to_rgba(cmap(x)) if ~np.isnan(x) else (0,0,0,0)
        # folium.raster_layers.ImageOverlay(image = t_scores,
        #                                   name = 'T-scores (changes)',
        #                                   opacity = 1,
        #                                   bounds = map_bounds,
        #                                   show = False,
        #                                   colormap = cmap_func).add_to(m)
        # m.add_child(cmap)

        #------------------------------------------------------------------------------
        # Flood binary mask

        flood_fpath = os.path.join(self.app.Results_dir, 'Flood_map_{}.tif'.format(self.app.projectname))
        with rio.open(flood_fpath) as src:
            flood, out_transform = rasterio.mask.mask(src, aoi.geometry, crop=True)
            flood = flood[0,:,:]

        raster_to_coloridx = {1: (0.0, 0.0, 1.0, 0.8),
                            0: (0.0, 0.0, 0.0, 0.0)}

        S1_flood_str = self.app.S1_flood_datetime.strftime('%Y-%m-%d %H:%M')

        m.add_child(folium.raster_layers.ImageOverlay(image = flood, 
                                                    name = 'Flooded Estimations {} (UTC)'.format(S1_flood_str),
                                                    bounds = map_bounds,
                                                    colormap = lambda x: raster_to_coloridx[x]))

        folium.LayerControl('bottomleft', collapsed=False).add_to(m)

        return m