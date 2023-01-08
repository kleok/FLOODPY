#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scipy.stats import entropy, norm, ks_2samp
import warnings
import numpy as np

## For UserWarning
def fxnUw():
    warnings.warn("UserWarning arose", UserWarning)

def Is_similar_non_parametric(cand_values: np.array, ref_values: np.array, p_value: float = 0.05, norm_flag:bool = False) -> bool:
    """Similarity check using non-parametric Kolmogorov-Smirnov test.

    TODO:
        Add Andersen-Darling statistical test. For example:

        AD_statistic, critical_values, p_value = anderson_ksamp([cand_water_values_norm_scaled, water_values_norm_scaled])
        significance_levels=[15. , 10. ,  5. ,  2.5,  1. ]
        critical_values_dict=dict(zip(significance_levels, critical_values.tolist()))
        if AD_statistic > critical_values_dict[p_value*100]:
            result=False
        else:
            result=
            
    Args:
        cand_values (np.array): "Candidate" values that we want to examine.
        ref_values (np.array): Reference values.
        p_value (float, optional): the probability that the null hypothesis is True. Defaults to 0.05.
        norm_flag (bool, optional): If True mean-std normalization is applied. Defaults to False.

    Returns:
        bool: True if two given samples belong to the same population.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fxnUw()

        # normalize
        if norm_flag:
            cand_values_norm_scaled=(cand_values-np.mean(cand_values))/(np.std(cand_values))
            ref_values_norm_scaled=(ref_values-np.mean(ref_values))/(np.std(ref_values))
            ks_stat, pvalue = ks_2samp(cand_values_norm_scaled, ref_values_norm_scaled)
        else:
            ks_stat, pvalue = ks_2samp(cand_values, ref_values)

        # statistical decision
        if pvalue<p_value:
            result=False
        else:
            result=True
        
    return result

def Is_distr_water(values: np.array, water_mean_float: float, std_water_float: float, threshold: float) -> bool:
    """Checks if values come from the provided gaussian distribution (mean and std are provided)
    based on Jensen - Shannon divergence metric. 

    Args:
        values (np.array): Values to be examined.
        water_mean_float (float): Mean of the water distribution (assumed gaussian).
        std_water_float (float): Stardard deviation of the water distribution (assumed gaussian).
        threshold (float): Maximum Jensen - Shannon divergence value allowed for similarity.

    Returns:
        bool: True if values come from the provided gaussian distribution (mean and std are provided).
    """

    try:
        # create gaussian distribution for water
        water_mean=water_mean_float
        water_std=std_water_float
        water_pdf=norm(water_mean, water_std)
        
        # create gaussian distribution for candidate values
        values_mean=np.mean(values)
        values_std=np.std(values)
        values_pdf=norm(values_mean, values_std)
        
        # define grid that Jensen–Shannon divergence will be calculated
        x = np.linspace(np.min(values), np.max(values), 100)

        # calculate symmetric KL divergence (Jensen–Shannon divergence)
        JS_divergence=(entropy(water_pdf.pdf(x), values_pdf.pdf(x))+entropy(values_pdf.pdf(x), water_pdf.pdf(x)))/2

        # compare with provided threshold
        result=JS_divergence<threshold
        
    except RuntimeError: # in case entropy cannot be calculated we certaintly dont have similar distributions
        result=False
        
    return result

def Is_darker_than(values: np.array, water_mean_float: float, std_water_float:float, FDR_thres: float = 5.0) -> bool:
    """Checking if provided values are significatly lower (darker) that water distribution (Gaussian)
    using False discovery rate.

    Args:
        values (np.array): Values to be examined.
        water_mean_float (float): Mean of the water distribution (assumed gaussian).
        std_water_float (float): Stardard deviation of the water distribution (assumed gaussian).
        FDR_thres (float, optional): Minimum value of FDR for values to be darker than water. Defaults to 5.0.

    Returns:
        bool: True if values are significantly smaller (darker) than the provided gaussian distribution (mean and std are provided).
    """

    # mean and std of water ditribution (gaussian)
    water_mean=water_mean_float
    water_std=std_water_float 
    
    # mean and std of examined values ditribution (gaussian)
    values_mean=np.median(values)
    values_std=np.std(values)
    
    # for comparison of the mean values
    threshold = water_mean
    
    if values_mean <= threshold:

        FDR=np.power(water_mean-values_std,2)/(np.power(water_std,2)+np.power(values_std,2))

        if FDR > FDR_thres:
            result=True
        else:
            result=False

    else:
        result=False

    return result

def Is_brighter_than(values: np.array, water_mean_float: float, std_water_float: float, FDR_thres: float = 5.0) -> bool:
    """Checking if provided values are significatly larger (brighter) that water distribution (Gaussian)
    using False discovery rate.

    Args:
        values (np.array): Values to be examined.
        water_mean_float (float): Mean of the water distribution (assumed gaussian).
        std_water_float (float): Stardard deviation of the water distribution (assumed gaussian).
        FDR_thres (float, optional): Minimum value of FDR for values to be darker than water. Defaults to 5.0.

    Returns:
        bool: True if values are significantly larger (brighter) than the provided gaussian distribution (mean and std are provided).
    """

    # mean and std of water ditribution (gaussian)
    water_mean=water_mean_float
    water_std=std_water_float 
    
    # mean and std of examined values ditribution (gaussian)
    values_mean=np.median(values)
    values_std=np.std(values)
    
    # for comparison of the mean values
    threshold = water_mean

    if values_mean>=threshold:

        FDR=np.power(water_mean-values_std,2)/(np.power(water_std,2)+np.power(values_std,2))

        if FDR > FDR_thres:
            result=True
        else:
            result=False
    else:
        result=False

    return result