import requests
import geopandas as gpd
import pandas as pd

def get_attribute_value(attribute_column, attr_name):
    for attr_dict in attribute_column:
        if attr_dict['Name'] == attr_name:
            return attr_dict['Value']
        
def query_Sentinel_1(Floodpy_app):

    data_collection = 'SENTINEL-1'
    AOI_Polygon = gpd.read_file(Floodpy_app.geojson_bbox).geometry.iloc[0]
    start_date = Floodpy_app.pre_flood_datetime_start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    end_date = Floodpy_app.flood_datetime_end.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    product_type = 'GRD'
    orbit_dir = 'ASCENDING'
    num_return_products = 1000

    base_str = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter='
    data_col_str = f"Collection/Name eq '{data_collection}'"
    aoi_polygon_str = "OData.CSC.Intersects(area=geography%27SRID=4326;{}')".format(str(AOI_Polygon))
    aoi_point_str = "OData.CSC.Intersects(area=geography%27SRID=4326;POINT({lon}%20{lat})%27)".format(lon=AOI_Polygon.centroid.x,
                                                                                                lat = AOI_Polygon.centroid.y)

    temporal_str = f"ContentDate/Start gt {start_date} and ContentDate/Start lt {end_date}" 
    product_type_str = f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}')"
    num_products = f"&$top={num_return_products}"
    attributes_str = "&%24expand=Attributes"
    request_str = f"{base_str+data_col_str} and {aoi_polygon_str} and {product_type_str} and {temporal_str+num_products}{attributes_str}"

    ############################

    query_json = requests.get(request_str).json()
    query_df = pd.DataFrame.from_dict(query_json['value'])

    attrs_names = ['sliceNumber',
                    'orbitDirection',
                    'processorVersion',
                    'relativeOrbitNumber',
                    'platformSerialIdentifier',
                    'beginningDateTime']
    for attr_name in attrs_names:
        query_df[attr_name] = query_df['Attributes'].apply(get_attribute_value, attr_name=attr_name)


    # I cleap up the query_df because I can have multiple products for the same data/tile/orbit that corresponds to different processing baselines.
    # I keep the product that is related to the most recent publication date, or processing baseline number (e.g. N9999)
    query_df.sort_values(['beginningDateTime'], ascending=False, inplace=True)
    query_df.index = pd.to_datetime(query_df['beginningDateTime'])
    query_df = query_df.drop_duplicates('beginningDateTime').sort_index()

    flood_candidate_dates = query_df['relativeOrbitNumber'][Floodpy_app.flood_datetime_start:Floodpy_app.flood_datetime_end].index.values
    return query_df, flood_candidate_dates