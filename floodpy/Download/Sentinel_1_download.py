#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import requests
import os

def get_access_token(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Access token creation failed. Reponse from the server was: {r.json()}"
        )
    return r.json()["access_token"]

def download_single_product(id, outname, access_token):
    url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({id})/$value"

    headers = {"Authorization": f"Bearer {access_token}"}
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, headers=headers, stream=True)

    with open(outname, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

def download_S1_data(Floodpy_app):
    t1 = datetime.now()
    print('Creating token for downloading Copernicus products')
    access_token = get_access_token("karamvasis_k@hotmail.com", "!!2024fJ21k0G9")
    download_df = Floodpy_app.query_S1_sel_df.reset_index(drop=True)
    for index, query_row in download_df.iterrows():
        print(' Downloading {}/{}'.format(index+1, len(download_df.index)))
        print(query_row['Name'])
        print('---------------')
        # I can add a for loop to update the access token every 10 min and not every image request.
        if (datetime.now()-t1).seconds > 600:
            print('Updating token for downloading Copernicus products')
            access_token = get_access_token("karamvasis_k@hotmail.com", "!!2024fJ21k0G9")
            t1 = datetime.now()

        product_id = query_row['Id']
        outname_product = os.path.join(Floodpy_app.S1_dir,'{}.zip'.format(query_row['Name']))
        if not os.path.exists(outname_product):
            download_single_product(product_id, outname_product, access_token)