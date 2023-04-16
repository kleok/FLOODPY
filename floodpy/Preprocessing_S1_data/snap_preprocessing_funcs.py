import os
import subprocess
import geopandas as gpd
from shapely.geometry import Point, Polygon

def _extract_geo_bounds(vector_file, buffer_distance=0.01):
    ''' 
    This function returns a list of coordinates of 
    the bounding box of the given vector file.
    '''
    
    pol1 = gpd.GeoDataFrame.from_file(vector_file)

    bbox_old = pol1.total_bounds
    bbox=[bbox_old[0]-buffer_distance,
          bbox_old[1]-buffer_distance,
          bbox_old[2]-buffer_distance,
          bbox_old[3]-buffer_distance ]

    p1 = Point(bbox[0], bbox[3])
    p2 = Point(bbox[2], bbox[3])
    p3 = Point(bbox[2], bbox[1])
    p4 = Point(bbox[0], bbox[1])

    np1 = (p1.coords.xy[0][0], p1.coords.xy[1][0])
    np2 = (p2.coords.xy[0][0], p2.coords.xy[1][0])
    np3 = (p3.coords.xy[0][0], p3.coords.xy[1][0])
    np4 = (p4.coords.xy[0][0], p4.coords.xy[1][0])
    
    bb_polygon = Polygon([np1, np2, np3, np4])
    
    return str(bb_polygon)

def _shapely_to_snap_polygon(AOI):
    
    x, y = AOI.exterior.coords.xy
    
    str_polygon=str(AOI)
    str_polygon = str_polygon.split('))')[0]
    
    last_coords = ', {} {}))'.format(x[-1], y[-1])
    
    snap_polygon = str_polygon+last_coords
    return snap_polygon

def perform_single_1GRD_preprocessing(gptcommand,master,outfile,Subset_AOI,xml_file,ext, overwrite):
    ''' 
    This function extracts information that shared among all SLC acquisitions
    in the stack. In uses a customized version of pair_preprocessing graph xml
    file and writes lat,lon,DEM, incidence angle as well as Polarimetric matrix
    information for the master image.
    '''
    if not overwrite:
        if os.path.exists(outfile+ext):
            return 0

    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein='+master,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]

    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

    
def perform_single_2GRD_preprocessing(gptcommand, img1, img2 ,outfile, Subset_AOI, xml_file, ext, overwrite):
    ''' 
    This function extracts information that shared among all SLC acquisitions
    in the stack. In uses a customized version of pair_preprocessing graph xml
    file and writes lat,lon,DEM, incidence angle as well as Polarimetric matrix
    information for the master image.
    '''
    if not overwrite:
        if os.path.exists(outfile+ext):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+img1,
            '-Pfilein2='+img2,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile+ext]

    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

def perform_pair_preprocessing_1GRD_1GRD(gptcommand,primary1,secondary1,outfile,Subset_AOI,xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0

    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+primary1,
            '-Pfilein2='+secondary1,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    try:
        subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    except:
        print('---------------------------')
        print(argvs)
        print("Coregistration between \n {image1} \n and \n {image2} \n has failed!".format(image1 = os.path.basename(primary1),
                                                                                            image2 = os.path.basename(secondary1)))
        print("We have to drop {image2} image from the stack processing.".format(image2 = os.path.basename(secondary1)))
        print('---------------------------')
    return 0

def perform_pair_preprocessing_1GRD_2GRD(gptcommand, primary1, secondary1, secondary2, outfile, Subset_AOI, xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+primary1,
            '-Pfilein3='+secondary1,
            '-Pfilein4='+secondary2,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    
    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0

def perform_pair_preprocessing_2GRD_1GRD(gptcommand, primary1, primary2, secondary1, outfile, Subset_AOI, xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+primary1,
            '-Pfilein2='+primary2,
            '-Pfilein3='+secondary1,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    
    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0
    
def perform_pair_preprocessing_2GRD_2GRD(gptcommand, primary1, primary2, secondary1, secondary2, outfile, Subset_AOI, xml_file, overwrite):
    
    """
    This function performs the preprocessing of the given pair from the
    input S1 SLC stack. 
    """
    if not overwrite:
        if os.path.exists(outfile+'.h5'):
            return 0
        
    argvs=[gptcommand, '-e',
            xml_file,
            '-Pfilein1='+primary1,
            '-Pfilein2='+primary2,
            '-Pfilein3='+secondary1,
            '-Pfilein4='+secondary2,
            '-Ppolygon='+_shapely_to_snap_polygon(Subset_AOI),
            '-Pfileout='+outfile]
    
    subprocess.check_call(argvs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return 0