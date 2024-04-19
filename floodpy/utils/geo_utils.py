from shapely.geometry import Polygon

def create_polygon(coordinates):
    return Polygon(coordinates['coordinates'][0])