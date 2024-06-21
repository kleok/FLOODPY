import os
import shutil
from pathlib import Path
import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
import ray
import rioxarray as rxr
import torch
from rasterio import features
from shapely.geometry import mapping, shape
from torchvision import transforms
from tqdm import tqdm

#Where to store patch predictions before merging
TMP_PREDICTION_PATH="YOUR_TMP_PREDICTION_PATH"


# For multiprocessing. Could be optimized further

ray.init(num_gpus=2,num_cpus=24)

def infer_on_sample(model, images, image_path, image_id, preds_path, device,ds):
    """
    Function to create the predictions on a single sample
    Args:
        model: Model to use for inference
        images: Tuple of images to use for inference
        image_path: Path to the image
        image_id: ID of the image
        preds_path: Path to save the predictions
        device: Device to use for inference
        ds: Post event image to use as reference for the resulting shape and bounds
    """
    
    with torch.cuda.amp.autocast(enabled=False):
        with torch.no_grad():
            post_event, pre_event_1, pre_event_2 = images

            pre_event_1 = pre_event_1.to(device).unsqueeze(0)
            pre_event_2 = pre_event_2.to(device).unsqueeze(0)
            post_event = post_event.to(device).unsqueeze(0)

            
            
            pre_event_1 = pre_event_1.to(device)
            post_event = torch.cat((post_event, pre_event_1), dim=1)
            post_event = torch.cat((post_event, pre_event_2.to(device)), dim=1)
            output = model(post_event)

            predictions = output.argmax(1)
           

    crs = 'epsg:3857'

    #image_path = list(Path(image_path).glob('post.tif'))[0]
    #ds = rxr.open_rasterio(image_path)
    ds = ds.rio.reproject(crs)

    predictions_arr = predictions.squeeze().cpu().numpy()
    if ds.shape[1:] != predictions_arr.shape:
        ds = ds[:, :predictions_arr.shape[0], :predictions_arr.shape[1]]  # Sometimes there is a small offset

    bbox = ds.rio.bounds()
    transform = rio.transform.from_bounds(*bbox, width=predictions_arr.shape[0], height=predictions_arr.shape[1])

    perm_predictions = np.zeros(predictions_arr.shape)
    perm_predictions[predictions_arr == 1] = 1

    flood_predictions = np.zeros(predictions_arr.shape)
    flood_predictions[predictions_arr == 2] = 1
    print(preds_path)
    with rio.open(preds_path / f'prediction_perm_of_image_{image_id}.tiff', 'w', driver='GTiff', width=perm_predictions.shape[0], height=perm_predictions.shape[1],
        count=1, dtype=perm_predictions.dtype, nodata=0, transform=transform, crs=crs) as dst:
        dst.write(perm_predictions[None, :, :])

    with rio.open(preds_path / f'prediction_flood_of_image_{image_id}.tiff', 'w', driver='GTiff', width=flood_predictions.shape[0], height=flood_predictions.shape[1],
        count=1, dtype=flood_predictions.dtype, nodata=0, transform=transform, crs=crs) as dst:
        dst.write(flood_predictions[None, :, :])

    geoms = []
    with rio.open(preds_path / f'prediction_perm_of_image_{image_id}.tiff') as f:
        img = f.read(1).astype(np.int32)
        metadata = f.meta
        for coords, value in features.shapes(img, transform=f.transform):
            if value != 0:
                geoms.append(shape(coords))

    with fiona.open(preds_path / f'prediction_perm_of_image_{image_id}.shp', 'w', 'ESRI Shapefile', {'geometry': 'Polygon'}, crs=metadata['crs'], transform=metadata['transform']) as f:
        for geom in geoms:
            f.write({'geometry': mapping(geom)})

    geoms = []
    with rio.open(preds_path / f'prediction_flood_of_image_{image_id}.tiff') as f:
        img = f.read(1).astype(np.int32)
        metadata = f.meta
        for coords, value in features.shapes(img, transform=f.transform):
            if value != 0:
                geoms.append(shape(coords))

    with fiona.open(preds_path / f'prediction_flood_of_image_{image_id}.shp', 'w', 'ESRI Shapefile', {'geometry': 'Polygon'}, crs=metadata['crs'], transform=metadata['transform']) as f:
        for geom in geoms:
            f.write({'geometry': mapping(geom)})

    ## Remove tiff files
    #for tiff_file in preds_path.glob('*.tiff'):
    #    tiff_file.unlink()

    return


def reverse_channel_order(image):
    vh = image[0,:,:]
    vv = image[1,:,:]
    
    return np.stack((vv,vh),axis=0)

@ray.remote
def infer_ray(sample, idx,model,samples_dir,area,clamp_input,preds_path,device,Normalize):
    """
        Function to infer flood maps on a single sample. This function is used in a multiprocessing setup with Ray.
        Args:
            sample: Sample to infer on
            idx: Index of the sample
            model: Model to use for inference
            samples_dir: Directory where the samples are stored
            area (str): Area of the sample. Only used for logging
            clamp_input: Whether to clamp the input images
            preds_path: Path to save the predictions
            device: Device to use for inference
            Normalize: Normalization object (Mean and std via torch Normalize) to use for normalization
    """
    print(f'Processing sample {sample}')
    sample_path = Path(samples_dir) / area / sample
    image_path = list(Path(sample_path).glob('post.tif'))[0]
    ds = rxr.open_rasterio(image_path)
    post_path = sample_path / 'post.tif'
    pre1_path = sample_path / 'pre1.tif'
    pre2_path = sample_path / 'pre2.tif'

    post = rxr.open_rasterio(post_path).values #cv.imread(str(post_path), cv.IMREAD_ANYDEPTH)
    pre1 = rxr.open_rasterio(pre1_path).values #cv.imread(str(pre1_path), cv.IMREAD_ANYDEPTH)
    pre2 = rxr.open_rasterio(pre2_path).values #cv.imread(str(pre2_path), cv.IMREAD_ANYDEPTH)
    
    post = reverse_channel_order(post)
    pre1 = reverse_channel_order(pre1)
    pre2 = reverse_channel_order(pre2)
    
    post = torch.clamp(torch.from_numpy(post).float(), min=0.0, max=clamp_input)
    post = torch.nan_to_num(post,clamp_input)
    pre1 = torch.clamp(torch.from_numpy(pre1).float(), min=0.0, max=clamp_input)
    pre1 = torch.nan_to_num(pre1,clamp_input)
    pre2 = torch.clamp(torch.from_numpy(pre2).float(), min=0.0, max=clamp_input)
    pre2 = torch.nan_to_num(pre2,clamp_input)
    
    post = Normalize(post)
    pre1 = Normalize(pre1)
    pre2 = Normalize(pre2)
    
    image_list = [post, pre1, pre2]
    
    infer_on_sample(model, image_list, sample_path, idx, preds_path=preds_path, device=device, ds=ds)
    return 1

def create_annotations(samples_dir,out_dir):  
    """
        Main driver function. This function creates the flood maps for all samples (224x224) in the samples_dir and saves them in out_dir. Will call the infer_ray function in a parallel setup.
        Args:
            samples_dir: Directory where the samples are stored
            out_dir: Directory to save the predictions
    """  
    model = torch.load("floodvit.pt")
   
    # Define normalization parameters
    data_mean =  [0.0953, 0.0264]
    data_std = [0.0427, 0.0215]
    clamp_input = 0.15

    #Process on cpu
    device = "cpu"
    
    model.eval()
   
    model.to(device)

    #Pass model as reference to avoid copying it to each worker
    model =ray.put(model)

    #This is implementation specific. Could be skipped in other setups    
    areas = os.listdir(samples_dir)
    
    for area in areas:
        
        area_path = Path(samples_dir) / area
        samples = os.listdir(area_path)
        preds_path =Path(TMP_PREDICTION_PATH) / area
        preds_path.mkdir(parents=True, exist_ok=True) 

        full_preds_path = Path(out_dir) / area
        full_preds_path.mkdir(parents=True, exist_ok=True)
        
        Normalize = transforms.Normalize(mean=data_mean, std=data_std)

        tasks = []

        #Begin parallel processing
        for idx, sample in tqdm(enumerate(samples)):            
            tasks.append(infer_ray.remote(sample, idx,model,samples_dir,area,clamp_input,preds_path,device,Normalize))
       
        results = ray.get(tasks)

        #Just for logging. Should be a list of 1s.
        print("Task status")
        print(results)

        for tiff_file in preds_path.glob('*.tiff'):
            tiff_file.unlink()

        # Squash all predictions for this specific activation and AOI into a single shapefile
        gdf = gpd.GeoDataFrame()
        for shpfile in preds_path.glob('prediction_perm_*.shp'):
            gdf_1 = gpd.read_file(shpfile)
            gdf = gpd.GeoDataFrame(pd.concat([gdf, gdf_1]))

        gdf['dissolve'] = 1
        dissolved = gdf.dissolve(by='dissolve')
        dissolved.to_file(full_preds_path / 'prediction_perm.shp')

        gdf = gpd.GeoDataFrame()
        for shpfile in preds_path.glob('prediction_flood_*.shp'):
            gdf_1 = gpd.read_file(shpfile)
            gdf = gpd.GeoDataFrame(pd.concat([gdf, gdf_1]))

        gdf['dissolve'] = 1
        dissolved = gdf.dissolve(by='dissolve')
        dissolved.to_file(full_preds_path / 'prediction_flood.shp')

        #Remove tmp files
        shutil.rmtree(preds_path)
        
        #Get difference of shapefiles
        gdf_perm = gpd.read_file(full_preds_path / 'prediction_perm.shp')
        gdf_flood = gpd.read_file(full_preds_path / 'prediction_flood.shp')
        
        #gdf_perm = gpd.overlay(gdf_perm, gdf_flood, how='difference')
        gdf_flood = gpd.overlay(gdf_flood, gdf_perm, how='difference')
        gdf_perm = gdf_perm.explode(ignore_index=True)
        gdf_flood = gdf_flood.explode(ignore_index=True)
        
        gdf_perm.to_file(full_preds_path / 'prediction_perm.shp')
        gdf_flood.to_file(full_preds_path / 'prediction_flood.shp')