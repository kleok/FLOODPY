#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scipy.stats import kurtosis, skew, entropy, norm, ks_2samp
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from osgeo import gdal
import time
import os
import numpy as np
from skimage.util.shape import view_as_blocks
from scipy.ndimage import gaussian_filter
from skimage.filters import threshold_otsu, threshold_multiotsu
from skimage import morphology
import warnings
from scipy.ndimage.filters import maximum_filter as maxf2D
from joblib import Parallel, delayed
from joblib import wrap_non_picklable_objects
from floodpy.Floodwater_classification.Region_growing import Region_Growing

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler('CPLQuietErrorHandler')

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()

## For UserWarning
def fxnUw():
    warnings.warn("UserWarning arose", UserWarning)
    
def Kittler(data):
    """
    The reimplementation of Kittler-Illingworth Thresholding algorithm by Bob Pepin
    Works on 8-bit images only
    Original Matlab code: https://www.mathworks.com/matlabcentral/fileexchange/45685-kittler-illingworth-thresholding
    Paper: Kittler, J. & Illingworth, J. Minimum error thresholding. Pattern Recognit. 19, 41–47 (1986).
    """
    np.seterr(divide = 'ignore', invalid = 'ignore')
    min_value=int(np.percentile(data, 0.1))
    max_value=int(np.percentile(data, 99.9))
    num_values=len(range(min_value,max_value+1))*10
    h,g = np.histogram(data.ravel(),num_values,[min_value,max_value])
    h = h.astype(np.float)
    g = g.astype(np.float)
    g = g[:-1]
    c = np.cumsum(h)
    m = np.cumsum(h * g)
    s = np.cumsum(h * g**2)
    sigma_f = np.sqrt(s/c - (m/c)**2)
    cb = c[-1] - c
    mb = m[-1] - m
    sb = s[-1] - s
    sigma_b = np.sqrt(sb/cb - (mb/cb)**2)
    p =  c / c[-1]
    v = p * np.log(sigma_f) + (1-p)*np.log(sigma_b) - p*np.log(p) - (1-p)*np.log(1-p)
    v[~np.isfinite(v)] = np.inf
    idx = np.argmin(v)
    thres = g[idx]
    return thres

def Create_Regions(data, window_size = 200):
    """Creates blocks of a certain size from a given numpy array."""
    
    shape1, shape2 = data.shape
    new_shape1=int(np.ceil(shape1/window_size)*window_size)
    new_shape2=int(np.ceil(shape2/window_size)*window_size)
    new_t_score_dataset=np.empty((new_shape1,new_shape2))
    new_t_score_dataset[:] = np.nan
    new_t_score_dataset[:shape1,:shape2]=data
    Blocks = view_as_blocks(new_t_score_dataset, (window_size,window_size))
    
    return Blocks

def nparray_to_tiff(nparray:np.array, reference_gdal_dataset:str, target_gdal_dataset:str)->None:
    """
    Functionality that saves information numpy array to geotiff given a reference geotiff.

    Args:
        nparray (np.array): Information we want to save to geotiff
        reference_gdal_dataset (str): Path of the reference geotiff file
        target_gdal_dataset (str): Path of the output geotiff file
    """
    # open the reference gdal layer and get its relevant properties
    raster_ds = gdal.Open(reference_gdal_dataset, gdal.GA_ReadOnly)   
    xSize = raster_ds.RasterXSize
    ySize = raster_ds.RasterYSize
    geotransform = raster_ds.GetGeoTransform()
    projection = raster_ds.GetProjection()
    
    # create the target layer 1 (band)
    driver = gdal.GetDriverByName('GTIFF')
    target_ds = driver.Create(target_gdal_dataset, xSize, ySize, bands = 1, eType = gdal.GDT_Float32)
    target_ds.SetGeoTransform(geotransform)
    target_ds.SetProjection(projection)
    target_ds.GetRasterBand(1).WriteArray(nparray)  
    
    target_ds = None
    
def Bimodality_test(region, smoothing = True):
    r"""
    A more robust split selection methodology has been developed by means of the 
    application of the bimodality coefficient (BC) [1]. The BC is based on a 
    straightforward (and therefore suitable for a rapid computation) empirical 
    relationship between bimodality and the third and fourth statistical moments
    of a distribution (skewness s and kurtosis k, respectively) [2]
    
    .. math:: BC = (s2 + 1) / (k + 3 * (N − 1) ^ {2} / ((N − 2) * (N − 3)))
    
    where N represents the sample size. The rationale the BC is that a bimodal 
    distribution has very low kurtosis, and/or is asymmetric; these conditions 
    imply an increase of BC, which ranges from 0 to 1. The value of BC for the 
    uniform distribution is 5/9 (∼0.555), while values greater than 5/9 may 
    indicate a bimodal (or multimodal) distribution [1]–[2]. The maximum value
    (BC = 1) is reached only by a Bernoulli distribution with only two distinct 
    values, or the sum of two different Dirac functions.
    
    [1] J. B. Freeman and R. Dale, “Assessing bimodality to detect the presence
    of a dual cognitive process,” Behav. Res. Methods, vol. 45, pp. 83–97,
    2013.
    [2] T. R. Knapp, “Bimodality revisited,” J. Mod. Appl. Statist. Methods,
    vol. 6, pp. 8–20, 2007.
    """
    
    if np.all(np.isnan(region)):
        BC=np.nan
    else:
        if smoothing:
            # smoothing
            data = gaussian_filter(region, sigma=5)
        else:
            data = region
        # flattening
        data=data.flatten()
        data=data[~np.isnan(data)]
        n=data.shape[0]
        if n<100:
            BC=np.nan
        else:
            s = skew(data) 
            k = kurtosis(data)
            denom2=np.divide(3*(n-1)**2,(n-2)*(n-3))
            BC=np.divide(s*s+1,k+denom2)    
            
    return BC
    
def Calculation_bimodality_mask(t_score_dataset,
                                min_window_size=25,
                                max_window_size=500,
                                step_window_size=50,
                                bimodality_thres=0.555,
                                segmentation_thres=0.5):
    '''
    Calculation of the bimodality mask. Maybe i should consider to add an 
    extra condition on the selected of bimodal tiles. I can compare the mean 
    intensity value of the tile with the mean value of all intensity.

    Args:
        t_score_dataset (np.array): the t-score dataset.
        min_window_size (int, optional): min_window_size. Defaults to 25.
        max_window_size (int, optional): max_window_size. Defaults to 500.
        step_window_size (int, optional): step_window_size. Defaults to 50.
        bimodality_thres (int, optional): bimodality_thres. Defaults to 0.555.
        segmentation_thres (int, optional): segmentation_thres. Defaults to 0.5.
    '''

    data_mask=~np.isnan(t_score_dataset)
    assert len(t_score_dataset.shape)==2
    dim1=t_score_dataset.shape[0]
    dim2=t_score_dataset.shape[1]
    
    window_sizes=range(min_window_size,max_window_size+step_window_size,step_window_size)
    segmentations=np.empty((len(window_sizes),dim1,dim2))
    
    for index, window_size in enumerate(window_sizes):
    
        Blocks=Create_Regions(t_score_dataset, window_size=window_size)
        
        BC=np.empty((Blocks.shape[0],Blocks.shape[1]))
        BC_flag=np.empty((Blocks.shape[0]*window_size,Blocks.shape[1]*window_size), dtype=np.int32)
    
        for ix in range(Blocks.shape[0]):
            for iy in range(Blocks.shape[1]):
                BC[ix,iy] = Bimodality_test(Blocks[ix,iy])
                # get indices relative with given dataset
                dim1_index_min=ix*window_size
                dim1_index_max=ix*window_size+window_size
                dim2_index_min=iy*window_size
                dim2_index_max=iy*window_size+window_size 
                
                if BC[ix,iy]>bimodality_thres :
                    BC_flag[dim1_index_min:dim1_index_max,dim2_index_min:dim2_index_max] = 1
                else:
                    BC_flag[dim1_index_min:dim1_index_max,dim2_index_min:dim2_index_max] = 0
                    
        segmentations[index,:,:]=BC_flag[:dim1,:dim2]
               
    bimodality_mask=np.mean(segmentations, axis=0)>segmentation_thres
    bimodality_mask=bimodality_mask*data_mask
    
    if np.sum(bimodality_mask)==0:
        bimodality_mask=np.ones_like(t_score_dataset)*data_mask
    
    return bimodality_mask.astype(np.bool_)

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
    """Similarity check using Jensen–Shannon divergence metric."""

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

# @delayed
@wrap_non_picklable_objects
def thresholding_pixel(row,
                       column,
                       rows,
                       columns,
                       t_score_dataset,
                       water_mean_float,
                       std_water_float,
                       Flood_global_binary,
                       window_half_size_min,
                       window_half_size_max,
                       window_step,
                       bimodality_thres,
                       thresholding_method,
                       p_value,
                       flood_percentage_threshold):
    '''
    Adaptive local thresholding fucntionality at a single pixel
    '''
    ##################################
    #=======================================================
    # 1. For a range of window sizes calculate Bimodality index values.
    #    This is used to determine the optimal window size to analyze the
    #    the local neighborhood.
    #=======================================================
    BCs=[]
    for window_half_size in range(window_half_size_min, window_half_size_max+1,window_step):
        
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns
        
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        BCs.append(Bimodality_test(window_data))
    
    BCs=np.array(BCs)
    BCs[np.isnan(BCs)]=0.0
    
    #=======================================================
    # 2. Check if the maximum bimodality index is above a threshold. 
    #    If the maximum bimodality index is above a threshold that corresponds
    #    to bi/multi model population
    #--------------------------------------------------------------------------
    #    If yes then we have bi/multi modal population inside the window. 
    #       -We select the window size with the highest BC as the optimal one
    #       -We recalculate threhold only at the window level. 
    #       -We calculate the mean,std of candidate local floodwater 
    #        population with lowest mean value
    #       So we have two possibilities:
    #       1. If the candidate population is similar with floodwater 
    #          population or has a lower mean that the water population 
    #          we keep it. We return the local mask.
    #       2. Else there is not water inside the window. We return zeros
    #
    #    Else we have only ONE population in the local neighborhood.
    #       We select the window size with the lowest BC as the optimal one
    #       So we have two possibilities:
    #       The majority of the pixels are non-flooded  or flooded!
    #         -We compare with the floodwater population. If it is similar we
    #          return ones in the local neighborhood
    #         -if pixels have a lower mean that the water population we return
    #          return ones in the local nieghborhood
    #         - else we return zeros in the local neighborhood 
    #=======================================================
    if np.max(BCs)>bimodality_thres: 
        
        best_window_index=np.argmax(BCs)
        window_half_size =  range(window_half_size_min, window_half_size_max+1)[best_window_index]
        
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns    
        
        # subsetting the t_score and the global binary mask
        window_mask=Flood_global_binary[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        # selecting only valid data
        valid_data=window_data[~np.isnan(window_data)]   
        flood_pixels_percent=np.sum(window_mask)*100/len(valid_data)   
         
    
        if thresholding_method=='Otsu':
            thresh = threshold_otsu(valid_data)
        elif thresholding_method=='Kittler':
            thresh = Kittler(valid_data)
        else:
            raise('error defining thresholding method')  
                
        local_water_mask=window_data<thresh
        cand_water_values=window_data[local_water_mask]  

        local_land_mask=window_data>=thresh
        cand_land_values=window_data[local_land_mask]
        
        # if np.median(cand_land_values)<water_mean_float:
        #     flood_occurences = np.ones(window_mask.shape)
        # else:
            
        # check if the values look like water
        
        ### parametric way
        # if Is_distr_water(cand_water_values, water_mean_float, std_water_float, threshold=flood_threshold): # if the extracted distribution looks like water
        #     flood_occurences = local_water_mask
        #     visits = np.ones(window_mask.shape)

        ### calculate flags
        
        if len(cand_water_values)==0 or len(cand_land_values)==0 or len(window_data[window_mask])==0 or len(window_data[~window_mask])==0 :
            flood_occurences = window_mask
            visits = np.ones(window_mask.shape)
            
        else:
            # calculate flags for water  
            
            similar_water_flag = Is_similar_non_parametric(cand_values = cand_water_values,
                                                           ref_values = window_data[window_mask],
                                                           p_value = p_value)
            
            darker_than_water_flag = Is_darkest_than(cand_water_values, water_mean_float, std_water_float)

            # check candidate water pixels if they are similar with water or darker
            if similar_water_flag or darker_than_water_flag:
                
                # calculate flags for land
                brighter_than_water = Is_brighter_than(cand_land_values, water_mean_float, std_water_float)
                
                similar_land_flag = Is_similar_non_parametric(cand_values = cand_land_values,
                                                             ref_values = window_data[~window_mask],
                                                             p_value = p_value)
                
                # calculate flag for flood pixels
                flood_pixels_percent_flag = flood_pixels_percent>flood_percentage_threshold
                # check candidate land pixels if they are similar with land or brighter than water
                if (brighter_than_water or similar_land_flag) and flood_pixels_percent_flag:
                       flood_occurences = local_water_mask
                       visits = np.ones(window_mask.shape)
                else:
                    flood_occurences = window_mask
                    visits = np.ones(window_mask.shape)
            # if values are brigther that typical water do nothing 
            else:
                flood_occurences = np.zeros(window_mask.shape)
                visits = np.zeros(window_mask.shape)
     
    else:

        # selecting the window size with the lowest BC as the optimal one
        best_window_index=np.argmin(BCs)
        window_half_size =  range(window_half_size_min, window_half_size_max+1)[best_window_index]
        # calculate indices 
        row_min = row-window_half_size
        if row_min<0: row_min=0
        row_max = row+window_half_size+1
        if row_max>rows: row_min=rows
        column_min = column-window_half_size
        if column_min<0: column_min=0
        column_max = column+window_half_size+1
        if column_max>columns: column_max=columns 
        
        window_mask=Flood_global_binary[row_min:row_max,column_min:column_max]
        window_data=t_score_dataset[row_min:row_max,column_min:column_max]
        
        values=window_data[~np.isnan(window_data)]  
        if len(values)==0:
            flood_occurences = np.zeros(window_mask.shape)
            visits = np.zeros(window_mask.shape)
        else:
        #######################################################################       
        # first alternative
        #######################################################################
            flood_occurences =  window_mask
            visits = np.ones(window_mask.shape)      
        #######################################################################       
        # second alternative
        #######################################################################    
            
            # # check if the values look like water
            # if Is_distr_water(values, water_mean_float, std_water_float, threshold=flood_threshold):
            #     flood_occurences = window_mask 
            #     visits = np.ones(window_mask.shape)
            # # check if the values are darkest that water       
            # elif Is_darkest_than_water(values, water_mean_float, std_water_float):
            #     flood_occurences = window_mask
            #     visits = np.ones(window_mask.shape)
            # # if values are brigther that typical water do nothing 
            # else:
            #     # produces some holes inside the flood area
            #     flood_occurences =  np.zeros(window_mask.shape) 
            #     visits = np.zeros(window_mask.shape)
            #     #flood_occurences = window_mask
        
    borders=np.array([row_min, row_max, column_min, column_max])
    
    return borders, flood_occurences, visits


def Adaptive_local_thresholdin_parallel(t_score_dataset_temp,
                                        Flood_global_binary_temp,
                                        water_mean_float,
                                        std_water_float,
                                        thresholding_method,
                                        p_value,
                                        window_half_size_min,
                                        window_half_size_max,
                                        window_step,
                                        num_cores,
                                        bimodality_thres,
                                        flood_percentage_threshold):
    '''
    Parallelized Adaptive local thresholding fucntionality.
    '''
    # adaptive thresholding
    rows=Flood_global_binary_temp.shape[0]
    columns=Flood_global_binary_temp.shape[1]
    flood_occurences=np.zeros(Flood_global_binary_temp.shape)
    visits=np.zeros(Flood_global_binary_temp.shape)
    t=time.time()
    for row in range(rows):
        
        if row%250 == 1:
            print ('{}/{}'.format(row,rows))
            print("Processing {} %.".format(round(((row+1)*100/rows),2)))
            elapsed = time.time() - t   
            print("{} sec elapsed...".format(round((elapsed))))
        
        test_list = Parallel(n_jobs=num_cores)(delayed(thresholding_pixel)(row,column,rows,columns,t_score_dataset_temp, water_mean_float, std_water_float, Flood_global_binary_temp, window_half_size_min, window_half_size_max, window_step, bimodality_thres, thresholding_method, p_value, flood_percentage_threshold) for column in range(columns) if Flood_global_binary_temp[row,column] )


        for pixel_index in range(len(test_list)):
            borders, flood_occurences_temp, visits_temp= test_list[pixel_index]
            row_min=borders[0]
            row_max=borders[1]
            column_min=borders[2]
            column_max=borders[3]
            flood_occurences[row_min:row_max,column_min:column_max] += flood_occurences_temp
            visits[row_min:row_max,column_min:column_max] += visits_temp
            

           
        
    #Create a [flood_probability_map] using number of visits and number of flood occurences.
    probability_map=(flood_occurences)/(visits+1)
    
    return probability_map

def morphological_postprocessing(Flood_map, minimum_mapping_unit_area_m2=1000, pixel_size_m = 10):
    '''
    Morphological processing based on provided minimum mapping unit. Procedure
    consists of steps (a) remove_small_holes (b) diameter_opening 
    and (c) remove_small_objects.
    '''
    
    # Remove small objects based on given minimum mapping unit area
    #Flood_local_map_RG_closing = morphology.closing(Flood_local_map_RG, morphology.square(3))
    minimum_mapping_unit_area_pixels=minimum_mapping_unit_area_m2/pixel_size_m
    
    Flood_map_temp1=morphology.remove_small_holes(Flood_map,
                                                  area_threshold=minimum_mapping_unit_area_pixels)
    
    diameter=int(np.sqrt(4*minimum_mapping_unit_area_pixels/np.pi))
    
    Flood_map_temp2=morphology.diameter_opening(Flood_map_temp1,
                                                diameter_threshold=diameter,
                                                connectivity=2)
    
    Flood_map_temp3 = morphology.remove_small_objects(Flood_map_temp2,
                                                      minimum_mapping_unit_area_pixels/2,
                                                      connectivity=2)
    
    return Flood_map_temp3

def RG_processing(t_score_dataset, Flood_map, RG_weight, search_window_size ):
    '''
    Region growing processing functionality.
    '''
    # get updated information of floodwater based on local adaptive thresholding
    floodwater_pixels=t_score_dataset[Flood_map]
    # discard pixel with nan values
    floodwater_pixels = floodwater_pixels[~np.isnan(floodwater_pixels)]
    # recalculating mean and standard deviation for floodwater population
    water_mean_float=np.mean(floodwater_pixels)
    std_water_float=np.std(floodwater_pixels)
 
    Flood_map_RG=Region_Growing(t_score_dataset_temp = t_score_dataset,
                                seeds = Flood_map,
                                RG_thres = std_water_float*RG_weight,
                                water_mean_float = water_mean_float,
                                std_water_float = std_water_float,
                                max_num_iter=1000,
                                search_window_size=search_window_size) 
    return Flood_map_RG

def Get_flood_map(Preprocessing_dir,
                  Results_dir,
                  Projectname,
                  num_cores,
                  fast_flag = True,
                  minimum_mapping_unit_area_m2 = 1000): # 4000 m2 equals 4 stremata
    '''
    The main funcionality that detected floodwater from t-score change image.
    '''

    processing_parms={'thresholding_method':'Otsu',
                      'p_value': 0.05,
                      'window_half_size_min':15,
                      'window_half_size_max':30,
                      'window_step':5,
                      'bimodality_thres':0.555,
                      'probability_thres_otsu': 0.25,
                      'search_RG_window_size':2,
                      'RG_weight':0.45,
                      'flood_percentage_threshold':10}
    ##########################################################################
    ## Read Data and calculate bimodality mask (Step-1)
    ##########################################################################
    t_score_filename = os.path.join(Results_dir,'t_scores_VV_VH_db.tif')
    assert os.path.exists(t_score_filename)
    t_score_dataset=gdal.Open(t_score_filename).ReadAsArray()
    multimodality_mask=Calculation_bimodality_mask(t_score_dataset) 
    
    ##########################################################################
    ## Create initial flood map using global thresholding (Step-2)
    ##########################################################################
    t_scores_flatten = t_score_dataset[multimodality_mask].flatten()
    vmin = np.quantile(t_scores_flatten, 0.01)
    vmax = np.quantile(t_scores_flatten, 0.99)

    t_scores_flatten[t_scores_flatten<vmin]=np.nan
    t_scores_flatten[t_scores_flatten>vmax]=np.nan
    t_scores_flatten = t_scores_flatten[~np.isnan(t_scores_flatten)]

    #glob_thresh = Kittler(t_scores_flatten)
    #print(glob_thresh)
    glob_thresh = threshold_otsu(t_scores_flatten)
    #print(glob_thresh)
    Flood_global_binary = t_score_dataset < glob_thresh # binary mask (1: water surfaces, 0: non water surfaces)  
    
    ##########################################################################
    ##########################################################################
    ## discard high slope regions in order to work on less pixels
    ##########################################################################
    slope_filename = os.path.join(Preprocessing_dir,'dem_slope_wgs84.tif')
    slope=gdal.Open(slope_filename).ReadAsArray()
    
    # Store shapes of inputs
    N = 7
    M = 7
    P,Q = slope.shape

    # Use 2D max filter and slice out elements not affected by boundary conditions
    maxs = maxf2D(slope, size=(M,N))
    
    slope_max_blur = gaussian_filter(maxs, sigma=7)
    slope_mask=slope_max_blur<12
    Flood_global_binary=Flood_global_binary*slope_mask
    ##########################################################################
    ## Local adaptive thresholding (Step-3) [corrects commission/omission errors] (Step-3)
    ## Create mean and standard deviation of floodwater 
    ##########################################################################    
    
    water_mean_float = np.mean(t_score_dataset[Flood_global_binary])
    std_water_float = np.std(t_score_dataset[Flood_global_binary])
   
    ##########################################################################
    ## create a subset of the initial dataset for faster experimentation
    ##########################################################################
    
    # t_score_dataset=t_score_dataset[1900:2100,1700:2000]
    # Flood_global_binary=Flood_global_binary[1900:2100,1700:2000]
    
    # t_score_dataset=t_score_dataset[400:600,1400:1600]
    # Flood_global_binary=Flood_global_binary[400:600,1400:1600]
    
    # Remove really small objects based on given minimum mapping unit area.
    # These objects are due to speckle
    #Flood_global_binary_despck = morphology.remove_small_objects(Flood_global_binary, 10, connectivity=2)
    
    # Close holes
    #Flood_global_binary_despck_refined=morphology.closing(Flood_global_binary_despck, morphology.square(2))

    ################################################################################
    ## 
    ################################################################################
    
    ## For each pixel that was identified as flood pixel select a window and do the following
    
    ### 1. if more than 80% of the pixels in the select window were already identified as flood do nothing
    
    ### 2. if less that 80% of the pixels in the select window were already identified as flood do nothing
    ###   and window has binomial distribution then recalculate threshold and use the new mask as flood mask

    ### 3. else increase the window size and go to step 1
    
    # minimum_mapping_unit_area_pixels=minimum_mapping_unit_area_m2/10
    # # the feature that should cover at least 20% of the considered window area
    # window_bbox_size=np.sqrt(minimum_mapping_unit_area_pixels/0.2)
    # window_half_size=int(np.floor(window_bbox_size/2))
    
    if not fast_flag:
    
        probability_map_otsu=Adaptive_local_thresholdin_parallel(t_score_dataset_temp = t_score_dataset,
                                                                Flood_global_binary_temp = Flood_global_binary,
                                                                water_mean_float = water_mean_float,
                                                                std_water_float = std_water_float,
                                                                thresholding_method ='Otsu',
                                                                p_value = processing_parms['p_value'],
                                                                window_half_size_min = processing_parms['window_half_size_min'],
                                                                window_half_size_max = processing_parms['window_half_size_max'],
                                                                window_step = processing_parms['window_step'],
                                                                num_cores = num_cores,
                                                                bimodality_thres = processing_parms['bimodality_thres'],
                                                                flood_percentage_threshold = processing_parms['flood_percentage_threshold'])    
        
        
        # Keep only high probability flood pixels (>0.6)
        Flood_local_map=probability_map_otsu>processing_parms['probability_thres_otsu']
    
    
    # ##########################################################################

    # ##########################################################################    
    
    ##########################################################################
    ## Region growing (Step-4) [corrects omission errors]
    ##########################################################################
    if not fast_flag:
        # Region growing
        Flood_local_map_RG = RG_processing(t_score_dataset = t_score_dataset,
                                           Flood_map = Flood_local_map,
                                           RG_weight = processing_parms['RG_weight'],
                                           search_window_size = processing_parms['search_RG_window_size'])
    Flood_global_map_RG = Flood_global_binary
    #Flood_global_map_RG = RG_processing(t_score_dataset,
                                        #Flood_global_binary,
                                        #processing_parms['RG_weight'],
                                        #processing_parms['search_RG_window_size'])
        

    # diff = np.invert(Flood_global_binary)
    # test = Flood_global_map_RG*diff
    # nparray_to_tiff(test,
    #                 t_score_filename,
    #                 output_filename.split('.')[0]+'_RG_example3.tif')


    ##########################################################################
    ## Postprocessing processing for refinement (Step-5) 
    ##########################################################################
    if not fast_flag:
        # discard high slope pixels
        Flood_local_map_RG=Flood_local_map_RG*slope_mask
            
        # morphological filtering of local flood mask
        Flood_local_map_RG_ref=morphological_postprocessing(Flood_local_map_RG)
    

    # discard high slope pixels
    Flood_global_map_RG=Flood_global_map_RG*slope_mask
        
    # morphological filtering of local flood mask
    Flood_global_map_RG_ref=morphological_postprocessing(Flood_global_map_RG, minimum_mapping_unit_area_m2)
    

    ##########################################################################
    ## Write data to disk
    ##########################################################################
    # file1 = open("{}/Accuracy_report.txt".format(Results_dir),"w")
    # file1.write("Accuracy Results \n")
    # file1.writelines(Accuracy_results)
    # file1.close() #to change file access modes
    output_filename = os.path.join(Results_dir,'Flood_map_{}.tif'.format(Projectname))
    print('Floodwater map can be found at {}'.format(output_filename))

    
    nparray_to_tiff(multimodality_mask,
                    t_score_filename,
                    output_filename.split('.')[0]+'_multimodality_mask.tif')
    
    # saving final flood map to tiff file
    nparray_to_tiff(Flood_global_map_RG_ref,
                    t_score_filename,
                    output_filename)    
    
    if not fast_flag:
        # saving final flood map to tiff file
        nparray_to_tiff(Flood_local_map_RG_ref,
                        t_score_filename,
                        output_filename.split('.')[0]+'_local.tif')
 
    return 0
