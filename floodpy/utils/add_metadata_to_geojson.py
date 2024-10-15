import geopandas as gpd
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os


def add_metadata(Floodpy_app_objs, Floodpy_app, plot_flag = True):

    distinctDarkTones = np.array([
        '#264653',  # dark teal/gray
        '#2a9d8f',  # deep green/teal
        '#1d3557',  # dark blue
        '#4b5320',  # army green
        '#039BE5',  # vivid blue
        '#006400',  # dark green
        '#81D4FA',  # sky blue
    ])

    # choose the visualization colors
    num_flood_events = len(Floodpy_app_objs)
    color_indices = np.array([np.ceil(len(distinctDarkTones)*flood_ind/num_flood_events) for flood_ind in range(num_flood_events)], dtype=np.int32)
    colors = distinctDarkTones[color_indices]

    # calculate the pandas dataframe with flooded regions and add metadata (plot_color and max_entend)
    Flooded_regions_df = pd.DataFrame()
    for flood_date in Floodpy_app_objs.keys():
        # calculate the area of flooded regions
        Flood_map_vector_data = gpd.read_file(Floodpy_app_objs[flood_date].Flood_map_vector_dataset_filename)
        Flood_map_vector_data_projected = Flood_map_vector_data.to_crs(Flood_map_vector_data.estimate_utm_crs())
        area_km2 = round(Flood_map_vector_data_projected.area.sum()/1000000,2 )
        flooded_region_temp = pd.DataFrame({'Flooded area (km2)':area_km2,
                                            'geojson_filename':Floodpy_app_objs[flood_date].Flood_map_vector_dataset_filename}, index=[flood_date])
        Flooded_regions_df = pd.concat([Flooded_regions_df,flooded_region_temp])
        
    # Ascending sorting of flood events based on flooded area
    Flooded_regions_df = Flooded_regions_df.sort_values(by=['Flooded area (km2)'])
    Flooded_regions_df['plot_color'] = colors
    Flooded_regions_df['max_extend'] = 'false'
    max_extend_ind = Flooded_regions_df['Flooded area (km2)'].idxmax()
    Flooded_regions_df.loc[max_extend_ind, ['max_extend']] = 'true'

    # overwrite existing geojson files with metadata information

    for index, row in Flooded_regions_df.iterrows():
        with open(row['geojson_filename']) as f:
            flooded_regions_json = json.load(f)

        #Add top-level metadata (e.g., title, description, etc.)
        flooded_regions_json['plot_color'] = row['plot_color']
        flooded_regions_json['max_extend'] = row['max_extend']

        #Save the modified GeoJSON with metadata to a file
        with open(row['geojson_filename'], "w") as f:
            json.dump(flooded_regions_json, f, indent=2)


    if plot_flag:
        Flooded_regions_df['Datetime'] = pd.to_datetime(Flooded_regions_df.index)

        df = Flooded_regions_df.sort_index().copy()
        # Plot the data
        fig = plt.figure(figsize=(6, 5))
        plt.bar(df['Datetime'].astype(str), df['Flooded area (km2)'], color='royalblue', width=0.7)

        # Adjust the plot
        plt.ylabel('Flooded area (km²)', fontsize=16)
        plt.xticks(df['Datetime'].astype(str), df['Datetime'].dt.strftime('%d-%b-%Y'), rotation=30, ha='right', fontsize=16)  # Set custom date format
        plt.yticks(fontsize=16)
        plt.grid()
        plt.tight_layout()  # Adjust layout for better fit

        # Display the plot
        fig_filename = os.path.join(Floodpy_app.Results_dir, '{}.svg'.format(Floodpy_app.flood_event))
        plt.savefig(fig_filename,format="svg")
        # plt.close()
        print('The figure can be found at: {}'.format(fig_filename))