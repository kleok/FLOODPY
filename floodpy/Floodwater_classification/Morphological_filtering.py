import numpy as np
from skimage import morphology

def morphological_postprocessing(Flood_map: np.array, min_map_unit_m2: float  = 1000, pixel_m2: float = 100) -> np.array:
    """
    Morphological processing according to provided minimum mapping unit and area of pixel of flood map. 
    The following morphological operations are applied:
    - remove_small_holes
    - diameter_opening
    - remove_small_objects.

    Args:
        Flood_map (np.array): Initial flood map
        min_map_unit_m2 (float, optional): The area (in m2) of the minimum mapping unit. Defaults to 1000.
        pixel_m2 (float, optional): The area (in m2) of pixel of the initial flood map. Defaults to 100.

    Returns:
        np.array: flood map after refinement using morphological operations
    """

    # removing small holes
    min_map_unit_pixels=min_map_unit_m2/pixel_m2
    Flood_map_temp1=morphology.remove_small_holes(Flood_map, area_threshold=min_map_unit_pixels)

    # Opening is a process in which first erosion operation is performed and then dilation operation is performed.
    diameter=int(np.sqrt(4*min_map_unit_pixels/np.pi))
    Flood_map_temp2=morphology.diameter_opening(Flood_map_temp1, diameter_threshold=diameter, connectivity=2)

    # remove small objects
    Flood_map_temp3 = morphology.remove_small_objects(Flood_map_temp2, min_map_unit_pixels/2, connectivity=2)
    
    return Flood_map_temp3