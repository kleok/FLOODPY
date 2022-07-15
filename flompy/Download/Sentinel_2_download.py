from collections import OrderedDict
from sentinelsat import SentinelAPI

def Download_S2_data(user, passwd, tiles, Start_time, End_time, write_dir, product = 'S2MSI2A', download = True, cloudcoverage = 100):
    """Download Sentinel 2/3 imagery by MGRS tile system.

    Args:
        user (str): APIHUB username.
        passwd (str): APIHUB password.
        tiles (list): Tile codes.
        product (str): S2MSI2A or S2MSI1C.
        Start_time (str): Start date
        End_time (str): End date
        download (bool, optional): If True downloads data. Defaults to True.
        write_dir (str, optional): Path to write data. Defaults to './'.
        cloudcoverage(float, optional): Maximum cloud coverage. Defaults to 100.
    
    Todo:
        * Work with other Sentinel programs i.e S1
    """
    api = SentinelAPI(user, passwd, api_url='https://apihub.copernicus.eu/apihub/', show_progressbars=True, timeout=None)

    if cloudcoverage == 100:
        query_kwargs = {
            'platformname': 'Sentinel-2',
            'producttype': product,
            'date': (Start_time, End_time)}
    else:
        query_kwargs = {
            'platformname': 'Sentinel-2',
            'producttype': product,
            'cloudcoverpercentage': (0, cloudcoverage),
            'date': (Start_time, End_time)}

    products = OrderedDict()

    for tile in tiles:
        kw = query_kwargs.copy()
        if product == "S2MSI2A":
            kw['filename'] = "*_T{}_*".format(tile)
        else:
            kw['tileid'] = tile  # products after 2017-03-31
        pp = api.query(**kw)
        products.update(pp)

    if download == True:
        # When trying to download an offline product with download_all(), the method will instead attempt to trigger its retrieval from the LTA.
        api.download_all(products , directory_path = write_dir)
    else:
        print ("No download option is enabled. Printing the query results...")
        for p in products:
            print (api.get_product_odata(p))
