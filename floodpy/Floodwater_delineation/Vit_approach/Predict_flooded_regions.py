import xarray as xr
import rioxarray
import torch
import numpy as np
from torchvision import transforms
import xbatcher
from tqdm import tqdm
import sys

def save_to_netcdf(S1_dataset, prediction_data, flooded_region_filename, flooded_regions_value = 2):

    Flooded_xarray = xr.Dataset({'flooded_regions': (["y","x"], prediction_data == flooded_regions_value)},
                                        coords={
                                                "x": (["x"], S1_dataset.x.data),
                                                "y": (["y"], S1_dataset.y.data),
                                        },
                                        )

    Flooded_xarray.x.attrs['standard_name'] = 'X'
    Flooded_xarray.x.attrs['long_name'] = 'Coordinate X'
    Flooded_xarray.x.attrs['units'] = 'degrees'
    Flooded_xarray.x.attrs['axis'] = 'X'

    Flooded_xarray.y.attrs['standard_name'] = 'Y'
    Flooded_xarray.y.attrs['long_name'] = 'Coordinate Y'
    Flooded_xarray.y.attrs['units'] = 'degrees'
    Flooded_xarray.y.attrs['axis'] = 'Y'

    Flooded_xarray.rio.write_crs("epsg:4326", inplace=True)
    Flooded_xarray.to_netcdf(flooded_region_filename, format='NETCDF4')

def predict_flooded_regions(Floodpy_app, ViT_model_filename, device):

    # loading pretrained ViT model
    sys.path.insert(0, Floodpy_app.src)
    vit_model = torch.load(ViT_model_filename)
    vit_model.to(device)

    batch_size = 224
    starting_points = np.arange(0, batch_size, batch_size/4).astype(np.int32)
    data_mean =  [0.0953, 0.0264]
    data_std = [0.0427, 0.0215]
    clamp_input = 0.15
    Normalize = transforms.Normalize(mean=data_mean, std=data_std)

    # load Sentinel-1 data
    S1_dataset = xr.open_dataset(Floodpy_app.S1_stack_filename, decode_coords='all')
    pre1_time, pre2_time, post_time = S1_dataset.time[-3:] # assumes last time is the recent (flooded) one

    prediction_data_list = []

    for starting_point in starting_points:
        print('Predictions with starting point: {} pixel'.format(starting_point))
        xr_dataset = S1_dataset.sel(x=slice(S1_dataset.x.isel(x=starting_point).data,S1_dataset.x.isel(x=-1).data),
                                    y=slice(S1_dataset.y.isel(y=starting_point).data,S1_dataset.y.isel(y=-1).data))
        
        predictions_batches_list = []
        post_bgen = xbatcher.BatchGenerator(xr_dataset.sel(time = post_time), input_dims = {'x': batch_size, 'y': batch_size})
        pre1_bgen = xbatcher.BatchGenerator(xr_dataset.sel(time = pre1_time), input_dims = {'x': batch_size, 'y': batch_size})
        pre2_bgen = xbatcher.BatchGenerator(xr_dataset.sel(time = pre2_time), input_dims = {'x': batch_size, 'y': batch_size})
        num_patches = len(post_bgen)

        for patch_i in tqdm(range(num_patches)):

            post_dB = np.stack([post_bgen[patch_i].VV_dB.values, post_bgen[patch_i].VH_dB.values],axis=0)
            post = np.power(10, post_dB/10) # convert to linear

            pre1_dB = np.stack([pre1_bgen[patch_i].VV_dB.values, pre1_bgen[patch_i].VH_dB.values],axis=0)
            pre1 = np.power(10, pre1_dB/10) # convert to linear

            pre2_dB = np.stack([pre2_bgen[patch_i].VV_dB.values, pre2_bgen[patch_i].VH_dB.values],axis=0)
            pre2 = np.power(10, pre2_dB/10) # convert to linear

            post = torch.clamp(torch.from_numpy(post).float(), min=0.0, max=clamp_input)
            post = torch.nan_to_num(post,clamp_input)
            pre1 = torch.clamp(torch.from_numpy(pre1).float(), min=0.0, max=clamp_input)
            pre1 = torch.nan_to_num(pre1,clamp_input)
            pre2 = torch.clamp(torch.from_numpy(pre2).float(), min=0.0, max=clamp_input)
            pre2 = torch.nan_to_num(pre2,clamp_input)

            with torch.cuda.amp.autocast(enabled=False):
                with torch.no_grad():
                    post_event = Normalize(post).to(device).unsqueeze(0)
                    pre_event_1 = Normalize(pre1).to(device).unsqueeze(0)
                    pre_event_2 = Normalize(pre2).to(device).unsqueeze(0)

                    pre_event_1 = pre_event_1.to(device)
                    post_event = torch.cat((post_event, pre_event_1), dim=1)
                    post_event = torch.cat((post_event, pre_event_2.to(device)), dim=1)
                    output = vit_model(post_event)

                    predictions = output.argmax(1)

            prediction_data = np.squeeze(predictions.to('cpu').numpy())

            prediction_patch_xarray = xr.Dataset({'flood_vit': (["y","x"], prediction_data)},
                                                coords={
                                                        "x": (["x"], post_bgen[patch_i].x.data),
                                                        "y": (["y"], post_bgen[patch_i].y.data),
                                                },
                                                )
            prediction_patch_xarray.rio.write_crs("epsg:4326", inplace=True)
            predictions_batches_list.append(prediction_patch_xarray)
        # merging all patches 
        prediction_merged_batches = xr.combine_by_coords(predictions_batches_list)
        # reindexing to have the same shape as the given dataset
        prediction_merged_batches = prediction_merged_batches.reindex_like(S1_dataset, method=None)
        # append to list
        prediction_data_list.append(prediction_merged_batches.flood_vit.data)

    # stacking all prediction and calculate the most common prediction value
    prediction_data_array = np.stack(prediction_data_list)
    prediction_data_median = np.nanmedian(prediction_data_array, axis=0)

    save_to_netcdf(S1_dataset = S1_dataset,
                   prediction_data = prediction_data_median,
                   flooded_region_filename = Floodpy_app.Flood_map_dataset_filename,
                   flooded_regions_value = 2)





