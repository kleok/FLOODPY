import xarray as xr
import rioxarray
import torch
import numpy as np
from torchvision import transforms
import torch.nn.functional as F
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

    patch_size = 224
    batch_size = 1
    bands_out = 1
    starting_points = np.arange(0, patch_size, patch_size/4).astype(np.int32)
    data_mean =  [0.0953, 0.0264]
    data_std = [0.0427, 0.0215]
    clamp_input = 0.15
    Normalize = transforms.Normalize(mean=data_mean, std=data_std)

    # load Sentinel-1 data
    S1_dataset = xr.open_dataset(Floodpy_app.S1_stack_filename, decode_coords='all')

    post = np.power(10, (np.stack([S1_dataset.isel(time=-1).VV_dB.values, S1_dataset.isel(time=-1).VH_dB.values],axis=0))/10)
    pre1 = np.power(10, (np.stack([S1_dataset.isel(time=-2).VV_dB.values, S1_dataset.isel(time=-2).VH_dB.values],axis=0))/10)
    pre2 = np.power(10, (np.stack([S1_dataset.isel(time=-3).VV_dB.values, S1_dataset.isel(time=-3).VH_dB.values],axis=0))/10)

    post = torch.clamp(torch.from_numpy(post).float(), min=0.0, max=clamp_input)
    post = torch.nan_to_num(post,clamp_input)
    pre1 = torch.clamp(torch.from_numpy(pre1).float(), min=0.0, max=clamp_input)
    pre1 = torch.nan_to_num(pre1,clamp_input)
    pre2 = torch.clamp(torch.from_numpy(pre2).float(), min=0.0, max=clamp_input)
    pre2 = torch.nan_to_num(pre2,clamp_input)

    # Normalize input data
    post_event_norm = Normalize(post)
    pre_event_1_norm = Normalize(pre1)
    pre_event_2_norm = Normalize(pre2)

    # Concatenate input data as expected from the model (post,pre1,pre2)
    input_data = torch.cat((post_event_norm, pre_event_1_norm, pre_event_2_norm), dim=0)

    [bands, rows, cols] = input_data.shape
    predictions_list = []

    for starting_point in starting_points:
        print('Predictions with starting point: {} pixel'.format(starting_point))

        # Calculate the original number of patches along the width and height 
        num_patches_x = (cols - starting_point) // patch_size
        num_patches_y = (rows - starting_point) // patch_size

        ending_point_x =  num_patches_x*patch_size+starting_point
        ending_point_y =  num_patches_y*patch_size+starting_point

        # Select section from original image and add a batch dimension (1, B, H, W) since unfold expects a batched input
        input_data_section  = torch.tensor(input_data[:,starting_point:ending_point_y, starting_point:ending_point_x]).unsqueeze(0)
        
        # Use unfold to extract patches
        # It extracts patches as columns of shape (B * patch_size * patch_size, L),
        # where L is the number of patches.
        patches = F.unfold(input_data_section, kernel_size=patch_size, stride=patch_size)

        # Reshape the patches to (num_patches, B, patch_size, patch_size)
        # The number of patches (num_patches) is (H // patch_size) * (W // patch_size)
        num_patches = patches.size(-1)
        patches = patches.permute(0, 2, 1)  # (1, L, B * patch_size * patch_size)
        patches = patches.reshape(1, num_patches, bands, patch_size, patch_size)

        # Remove the batch dimension if not needed (optional)
        patches = patches.squeeze(0)

        # Now, patches contains all the patches with shape (bands, patch_size, patch_size)
        # print(f"Patches shape: {patches.shape}")

        num_patches = patches.shape[0] 
        with torch.cuda.amp.autocast(enabled=False):
            with torch.no_grad():
                predictions_patches= torch.zeros((num_patches, bands_out, patch_size, patch_size))
                for i in tqdm(range(0,num_patches, batch_size)):
                    patches_torch=torch.tensor(patches[i:i+batch_size,:,:,:]).to(device)
                            
                    output = vit_model(patches_torch).detach().cpu()

                    predictions = output.argmax(1)
                    predictions_patches[i:i+batch_size,:,:,:]=predictions

        del predictions, patches_torch, patches, output   

        # Reshape the patches array back to the shape (num_patches_y, num_patches_x, bands, patch_size, patch_size)
        predictions_patches = predictions_patches.reshape(num_patches_y, num_patches_x, bands_out, patch_size, patch_size)

        # Transpose the axes back to (bands, num_patches_y * patch_size, num_patches_x * patch_size)
        reconstructed_image = predictions_patches.permute(2, 0, 3, 1, 4).reshape(bands_out, num_patches_y * patch_size, num_patches_x * patch_size)
        
        #print(f"Reconstructed image shape: {reconstructed_image.shape}")

        reconstructed_image_full = torch.zeros((bands_out,rows,cols)) 
        reconstructed_image_full[:,starting_point:ending_point_y, starting_point:ending_point_x] = reconstructed_image
        predictions_list.append(reconstructed_image_full)
        del reconstructed_image_full, reconstructed_image

    # stacking all prediction and calculate the most common prediction value
    prediction_data_array = np.stack(predictions_list)
    del predictions_list
    prediction_data_median = np.nanmedian(prediction_data_array, axis=0).squeeze()

    save_to_netcdf(S1_dataset = S1_dataset,
                    prediction_data = prediction_data_median,
                    flooded_region_filename = Floodpy_app.Flood_map_dataset_filename,
                    flooded_regions_value = 2)
        
                    
        



