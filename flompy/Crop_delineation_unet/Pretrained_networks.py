#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 19:47:35 2022

Authors : Kleanthis Karamvasis, Bill Tsironis
"""

import os, glob
import typing
from tqdm import tqdm
from osgeo import gdal

import tensorflow.keras as keras
import numpy as np
import rasterio
import tensorflow as tf
from tensorflow.keras.layers import (
    BatchNormalization,
    Convolution2D,
    LeakyReLU,
    ZeroPadding2D,
)
from keras_unet.models import satellite_unet
from patchify import patchify, unpatchify

def get_weights(uuid, name, network_path):
    """Generates three file names for the model, weights and history file and
    the networks readme.

    File name order of returned tuple:
        * readme
        * model
        * weights
        * history

    :param uuid: Universal unique identifier of a trained network
    :param name: The networks name
    :return: Tuple with files in the order mentioned above
    """
    base = f"{network_path}/{str(uuid)}-{name}"

    f_weights = f"{base}-weights.h5"

    return f_weights


def read_tif_FLOMPY(index, IMAGE_DIRS,  fit_size=None):
    bands_data = []
    for band in ["B02", "B03", "B04", "B08"]:
        base_image_name = glob.glob(IMAGE_DIRS[index]+'/GRANULE/*/IMG_DATA/R10m/*{}*.tif'.format(band))[0]
        bands_data.append(gdal.Open(base_image_name).ReadAsArray())

    if fit_size is None:
        return np.stack(bands_data, axis=-1)
    else:
        Q = np.zeros(
            (fit_size[0], fit_size[1], len(bands_data)), dtype=bands_data[0].dtype
        )
        D = np.stack(bands_data, axis=-1)
        Q[0 : D.shape[0], 0 : D.shape[1]] = D
        return Q
    

def normalize_array(arr):
    """Takes a 3D array as input, iterates over the bands and normalizes those.

    :param arr: input array (original image data)
    :return: normalized data with values between 0 and 1
    """
    arr_norm = np.zeros(arr.shape, dtype=np.float32)

    for i in range(arr.shape[2]):
        min = arr[:, :, i].min()
        max = arr[:, :, i].max()

        arr_norm = (arr - min) / (max - min)

    return arr_norm


def build_fcndk(
    x: int,
    y: int,
    bands: int,
    labels: int,
    layers=4,) -> tf.keras.Model:
    """Build a new network model based on the configuration of the networks
    FCNDK2, ..., FCNDK6. Specify the layers to use in the parameters.

    :param x: Number of rows
    :param y: Number of columns
    :param bands: Number of bands in the input images
    :param labels: Number of different labels to choose as the classification
    :param layers: The number of FCNDK layers; Should be between 2 and 6 [default: 4]
    :return: Model of the corresponding FCNDK network
    """
    """Model builder function for FCN-DK6."""
    model = keras.models.Sequential()
    model.add(ZeroPadding2D((2, 2), input_shape=(x, y, bands)))
    model.add(Convolution2D(filters=16, kernel_size=(5, 5), dilation_rate=(1, 1)))
    model.add(BatchNormalization(axis=3))
    model.add(LeakyReLU(0.1))

    if layers >= 2:
        # FCNDK2
        model.add(ZeroPadding2D((4, 4)))
        model.add(Convolution2D(filters=32, kernel_size=(5, 5), dilation_rate=(2, 2)))
        model.add(BatchNormalization(axis=3))
        model.add(LeakyReLU(0.1))

    if layers >= 3:
        # FCNDK3
        model.add(ZeroPadding2D((6, 6)))
        model.add(Convolution2D(filters=32, kernel_size=(5, 5), dilation_rate=(3, 3)))
        model.add(BatchNormalization(axis=3))
        model.add(LeakyReLU(0.1))

    if layers >= 4:
        # FCNDK4
        model.add(ZeroPadding2D((8, 8)))
        model.add(Convolution2D(filters=32, kernel_size=(5, 5), dilation_rate=(4, 4)))
        model.add(BatchNormalization(axis=3))
        model.add(LeakyReLU(0.1))

    if layers >= 5:
        # FCNDK5
        model.add(ZeroPadding2D((10, 10)))
        model.add(Convolution2D(filters=32, kernel_size=(5, 5), dilation_rate=(5, 5)))
        model.add(BatchNormalization(axis=3))
        model.add(LeakyReLU(0.1))

    if layers >= 6:
        # FCNDK6
        model.add(ZeroPadding2D((12, 12)))
        model.add(Convolution2D(filters=32, kernel_size=(5, 5), dilation_rate=(6, 6)))
        model.add(BatchNormalization(axis=3))
        model.add(LeakyReLU(0.1))

    # Output layer
    model.add(Convolution2D(filters=labels, kernel_size=(1, 1)))

    model.add(keras.layers.Activation(activation="softmax"))
    return model


def build_fcndk5(
    x: int,
    y: int,
    bands: int,
    labels: int,
) -> tf.keras.Model:
    """Wrapper function to build an FCNDK with 5 layers"""
    return build_fcndk(x, y, bands, labels, layers=5)


def build_fcndk6(
    x: int,
    y: int,
    bands: int,
    labels: int,
) -> tf.keras.Model:
    """Wrapper function to build an FCNDK with 6 layers"""
    return build_fcndk(x, y, bands, labels, layers=6)


def build_unet(
    x: int,
    y: int,
    bands: int,
    labels: int,
    layers: int = 2,
) -> tf.keras.Model:
    """Create  a model of the popular U-Net network.

    :param x: Number of rows (x-shape)
    :param y: Number of columns (y-shape)
    :param bands: Number of bands (z-shape)
    :param lables: Number of labels to predict with the network
    :param layers: Number of layers of the network
    :return: Model of the corresponding U-Net network
    """
    model = satellite_unet(
        input_shape=(x, y, bands),
        num_classes=labels,
        output_activation="softmax",
        num_layers=layers,
    )
    return model


def build_unet3(
    x: int,
    y: int,
    bands: int,
    labels: int,
) -> tf.keras.Model:
    """Wrapper function to build an UNet with 3 layers"""
    return build_unet(x, y, bands, labels, layers=3)


def build_network(name: str) -> typing.Callable:
    """Builds a new network, based on the networks name
    :param name: The networks name
    :return: The builder function of the corresponding network.
    """
    if name.lower() == "fcndk5":
        return build_fcndk5
    elif name.lower() == "fcndk6":
        return build_fcndk6
    elif name.lower() == "unet3":
        return build_unet3

def save_tif(array:np.array, name:str, metadata:dict)->None:
    """Save array to image by providing all the necessary metadata. Can be used by copying
    metadata from a source rasterio object with src.meta.copy().
    
    Args:
        array (np.array): Numpy array
        name (str): Path to store the image
        metadata (dict): Metadata to write the image
    """
    with rasterio.open(name, "w", **metadata) as dst:
        if array.ndim == 2:
            dst.write(array, 1)
        else:
            dst.write(array)

def construct_patches(data, patch_size=512, stride=500, bands=4):
    '''

    Args:
        data (np.array): the image that we want to patchify. 
                        example shape = (3072,4608,4)
        patch_size (integer, optional): patch window size. Defaults to 512.
        stride (integer, optional): stride. Defaults to 500.
        bands (integer, optional): number of bands. Defaults to 4.

    Returns:
        patches (np.array): array with patches.
                            example shape (6, 9, 1, 512, 512, 4)

    '''
    patches = patchify(data, (patch_size,patch_size,bands), step=stride)
    return patches

def reconstruct_patches (patches, rows, cols, bands):
    '''

    Args:
        patches (np.array): array with patches.
                            example shape (6, 9, 1, 512, 512, 1)
        rows (integer): first dimension of initial image.
        cols (integer): second dimension of initial image.
        bands (integer): number of bands.

    Returns:
        reconstructed_image (np.array): array with patches.
                            example shape (3072,4608,1)

    '''
    
    reconstructed_image = unpatchify(patches,(rows, cols, bands))
    
    return reconstructed_image

def model_predict_batch(A, model, force_cpu, window_size=512, stride = 500):

    # break down A to overlapping batches
    A_batches = construct_patches(A, stride = stride)

    rows_batches = A_batches.shape[0]
    cols_batches = A_batches.shape[1]
    band_batches = 2

    preds_batches = np.zeros((rows_batches, cols_batches,1,window_size,window_size,band_batches))

    for row_batches in range(rows_batches):
        for col_batches in range(cols_batches):
            A_batch = A_batches[row_batches,col_batches,...]
            # model prediction
            if force_cpu:
                with tf.device("/CPU:0"):
                    pred_batch = model.predict(A_batch)[0]
            else:
                pred_batch = model.predict(A_batch)[0]
            
            preds_batches[row_batches,col_batches,:,...] = pred_batch
            
    rows = A.shape[0]
    cols = A.shape[1]
    preds = reconstruct_patches(preds_batches, rows, cols, bands=2)
    preds = 255 * np.argmax(preds, axis=2).astype(np.uint8)
    
    return preds

def Crop_delineation_Unet(model_name, model_dir, BASE_DIR , results_pretrained, force_cpu = True):

    if not os.path.exists(results_pretrained):
        os.makedirs(results_pretrained)

    IMAGE_DIRS = glob.glob(BASE_DIR+'/*.SAFE')
    
    PRETRAINED_MODELS = {
        "FCNDK5": (
            "653e6d98-5974-11eb-a09d-0242ac1c0002",
            os.path.join(model_dir, "Crop_delineation_unet/FCN-DK5"),
        ),
        "FCNDK6": (
            "2111a6e4-5a5a-11eb-99e0-0242ac1c0002",
            os.path.join(model_dir, "Crop_delineation_unet/FCN-DK6"),
        ),
        "UNet3": (
            "371dd574-5b78-11eb-8f58-0242ac1c0002",
            os.path.join(model_dir, "Crop_delineation_unet/UNet3"),
        ),
    }
    
    model_uuid, model_path = PRETRAINED_MODELS[model_name]
    fit_in_size = None
    
    # initial shape of first image
    A = read_tif_FLOMPY(0, IMAGE_DIRS, fit_in_size)
    x, y, bands = A.shape

    # we change the dimension because unet needs 512
    if "unet" in model_name.lower():
        if x % 512 != 0:
            x = (x // 512 + 1) * 512

        if y % 512 != 0:
            y = (y // 512 + 1) * 512
        fit_in_size = (x, y)

    A = read_tif_FLOMPY(0, IMAGE_DIRS, fit_in_size)

    # we load the model
    model_builder_fun: typing.Callable = build_network(model_name)
    model = model_builder_fun(512, 512, bands, 2)
    model.load_weights(get_weights(model_uuid, model_name, model_path))

    # we get the geographic infromation
    src =  rasterio.open(glob.glob(IMAGE_DIRS[0]+'/GRANULE/*/IMG_DATA/R10m/*B02_*.tif')[0])

    print("Running pretrained model...")
    for i in tqdm(range(len(IMAGE_DIRS))):

        # load and normalize each image
        A = read_tif_FLOMPY(i, IMAGE_DIRS, fit_in_size)
        A = normalize_array(A)
        
        preds = model_predict_batch(A, model, force_cpu, stride = 512)
        metadata = src.meta.copy()
        metadata.update(dtype = np.uint8, height = preds.shape[0], width = preds.shape[1])
        save_tif(preds, os.path.join(results_pretrained, os.path.basename(IMAGE_DIRS[i]).split('.')[0] + "_" + model_name + ".tif"), metadata)

    # get filenames of all model predictions
    Results_Model_filenames = glob.glob(os.path.join(results_pretrained,'*{}*'.format(model_name)))
    
    # read the first image
    src = rasterio.open(Results_Model_filenames[0])
    metadata = src.meta.copy()

    Image_Model_temp = src.read()
    Crop_delineation = np.zeros(Image_Model_temp.shape)
    
    # Add all predictions
    for Image_Model_filename in Results_Model_filenames:
        Image_Model_temp = rasterio.open(Image_Model_filename).read()
        Crop_delineation = Crop_delineation + Image_Model_temp
    # create boolean mask
    Crop_delineation_bool = Crop_delineation>0
    print("Saving result...")
    metadata.update(dtype = np.uint8)
    save_tif(Crop_delineation_bool.astype(np.uint8), os.path.join(results_pretrained,'{}_crop_delineation.tif'.format(model_name)), metadata)