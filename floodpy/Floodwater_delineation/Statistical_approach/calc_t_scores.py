#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import xarray as xr
import pandas as pd
import os

def Calculate_t_scores(Floodpy_app):
    if not os.path.exists(Floodpy_app.t_score_filename):
        S1_stack_dB = xr.open_dataset(Floodpy_app.S1_stack_filename)[Floodpy_app.polar_comb]
        LIA = xr.open_dataset(Floodpy_app.LIA_filename)['LIA']

        Weights = np.cos(np.radians(LIA.values))
        S1_stack_dB = S1_stack_dB*Weights

        # checking
        Flood_data = S1_stack_dB.isel(time = -1)
        Flood_data_test = S1_stack_dB.sel(time = pd.to_datetime(Floodpy_app.flood_datetime_str))
        assert(np.allclose(Flood_data.values, Flood_data_test.values, equal_nan=True))

        Flood_data = S1_stack_dB.isel(time = -1)
        pre_flood_data = S1_stack_dB.isel(time = slice(0,-1))

        num_pre_flood_images = float(pre_flood_data.time.shape[0])
        pre_flood_mean = pre_flood_data.mean(dim="time")
        pre_flood_std = pre_flood_data.std(dim="time")

        t_scores= (Flood_data-pre_flood_mean)/(pre_flood_std/np.sqrt(num_pre_flood_images))
        t_scores = t_scores.clip(np.nanquantile(t_scores.values, 0.0001), np.nanquantile(t_scores.values, 0.9999))

        t_scores.to_netcdf(Floodpy_app.t_score_filename)
