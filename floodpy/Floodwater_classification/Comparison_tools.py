#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scipy.stats import entropy, norm, ks_2samp
import warnings
import numpy as np

## For UserWarning
def fxnUw():
    warnings.warn("UserWarning arose", UserWarning)

def Is_similar_non_parametric(cand_values, ref_values, p_value = 0.05, norm_flag=False):
    """Similarity check using non-parametric test (Kolmogorov-Smirnov)."""

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
        if pvalue<p_value:
            result=False
        else:
            result=True
            
        # AD_statistic, critical_values, p_value = anderson_ksamp([cand_water_values_norm_scaled, water_values_norm_scaled])
        # significance_levels=[15. , 10. ,  5. ,  2.5,  1. ]
        # critical_values_dict=dict(zip(significance_levels, critical_values.tolist()))
        # if AD_statistic > critical_values_dict[p_value*100]:
        #     result=False
        # else:
        #     result=True

    return result

def Is_distr_water(values, water_mean_float, std_water_float, threshold):
    """Similarity check using Jensen - Shannon divergence metric."""

    try:
        water_mean=water_mean_float
        water_std=std_water_float
        water_pdf=norm(water_mean, water_std)
        #np.random.normal(water_mean, water_std, 1000)
        
        values_mean=np.mean(values)
        values_std=np.std(values)
        values_pdf=norm(values_mean, values_std)
        
        x = np.linspace(np.min(values), np.max(values), 100)

        # calculate symmetric KL divergence (Jensen–Shannon divergence )
        JS_divergence=(entropy(water_pdf.pdf(x), values_pdf.pdf(x))+entropy(values_pdf.pdf(x), water_pdf.pdf(x)))/2
        result=JS_divergence<threshold
        
    except RuntimeError:
        result=False
        
    return result

def Is_darkest_than(values, water_mean_float, std_water_float):
    """Checking if provided values are significatly lower that water distribution
    using False discovery rate."""

    water_mean=water_mean_float
    water_std=std_water_float 
        
    values_mean=np.median(values)
    values_std=np.std(values)
    
    #threshold = water_mean-water_std
    threshold = water_mean
    
    FDR=np.power(water_mean-values_std,2)/(np.power(water_std,2)+np.power(values_std,2))
    
    if values_mean<=threshold:
        if FDR>5.0:
            result=True
        else:
            result=False
    else:
        result=False

    return result

def Is_brighter_than(values, water_mean_float, std_water_float):
    '''
    Checking if provided values are significatly bigger that water distribution
    using False discovery rate.
    '''
    water_mean=water_mean_float
    water_std=std_water_float 
        
    values_mean=np.median(values)
    values_std=np.std(values)
    
    FDR=np.power(water_mean-values_std,2)/(np.power(water_std,2)+np.power(values_std,2))
    
    #threshold = water_mean+water_std
    threshold = water_mean

    if values_mean>=threshold:
        if FDR>5.0:
            result=True
        else:
            result=False
    else:
        result=False

    return result