import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt

def plot_flooded_area_over_time(Floodpy_app, Floodpy_app_objs):

    Flooded_regions_areas_km2 = {}
    for flood_date in Floodpy_app_objs.keys():
        # calculate the area of flooded regions
        Flood_map_vector_data = gpd.read_file(Floodpy_app_objs[flood_date].Flood_map_vector_dataset_filename)
        Flood_map_vector_data_projected = Flood_map_vector_data.to_crs(Flood_map_vector_data.estimate_utm_crs())
        area_km2 = round(Flood_map_vector_data_projected.area.sum()/1000000,2 )
        Flooded_regions_areas_km2[flood_date] = area_km2


    def getcolor(val):
        return colorTones[Floodpy_app.flood_datetimes.index(val)]

    Flooded_regions_areas_km2_df = pd.DataFrame.from_dict(Flooded_regions_areas_km2, orient='index', columns=['Flooded area (km2)'])
    Flooded_regions_areas_km2_df['Datetime'] = pd.to_datetime(Flooded_regions_areas_km2_df.index)
    Flooded_regions_areas_km2_df['color'] = Flooded_regions_areas_km2_df['Datetime'].apply(getcolor)

    df = Flooded_regions_areas_km2_df.copy()
    # Plot the data
    fig = plt.figure(figsize=(6, 5))
    plt.bar(df['Datetime'].astype(str), df['Flooded area (km2)'], color=df['color'], width=0.7)

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

