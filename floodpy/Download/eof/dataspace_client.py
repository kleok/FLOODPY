"""Client to get orbit files from dataspace.copernicus.eu ."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

from ._auth import DATASPACE_HOST, get_netrc_credentials
from ._select_orbit import T_ORBIT
from ._types import Filename
from .log import logger
from .products import Sentinel as S1Product

QUERY_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
"""Default URL endpoint for the Copernicus Data Space Ecosystem (CDSE) query REST service"""

AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
"""Default URL endpoint for performing user authentication with CDSE"""

DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"
"""Default URL endpoint for CDSE download REST service"""

SIGNUP_URL = "https://dataspace.copernicus.eu/"
"""Url to prompt user to sign up for CDSE account."""


class DataspaceClient:
    T0 = timedelta(seconds=T_ORBIT + 60)
    T1 = timedelta(seconds=60)

    def __init__(self, username: str = "", password: str = ""):
        if not (username and password):
            logger.debug("Get credentials form netrc")
            try:
                username, password = get_netrc_credentials(DATASPACE_HOST)
            except FileNotFoundError:
                logger.warning("No netrc file found.")
            except ValueError as e:
                if DATASPACE_HOST not in e.args[0]:
                    raise e
                logger.warning(
                    f"No CDSE credentials found in netrc file. Please create one using {SIGNUP_URL}"
                )

        self._username = username
        self._password = password

    def query_orbit(
        self,
        t0: datetime,
        t1: datetime,
        satellite_id: str,
        product_type: str = "AUX_POEORB",
    ) -> list[dict]:
        assert satellite_id in {"S1A", "S1B"}
        assert product_type in {"AUX_POEORB", "AUX_RESORB"}
        # return run_query(t0, t1, satellite_id, product_type)
        # Construct the query based on the time range parsed from the input file
        logger.info(
            f"Querying for {product_type} orbit files from endpoint {QUERY_URL}"
        )
        query = _construct_orbit_file_query(satellite_id, product_type, t0, t1)
        # Make the query to determine what Orbit files are available for the time
        # range
        return query_orbit_file_service(query)

    def query_orbit_for_product(
        self,
        product,
        orbit_type: str = "precise",
        t0_margin: timedelta = T0,
        t1_margin: timedelta = T1,
    ):
        if isinstance(product, str):
            product = S1Product(product)

        return self.query_orbit_by_dt(
            [product.start_time],
            [product.mission],
            orbit_type=orbit_type,
            t0_margin=t0_margin,
            t1_margin=t1_margin,
        )

    def query_orbit_by_dt(
        self,
        orbit_dts,
        missions,
        orbit_type: str = "precise",
        t0_margin: timedelta = T0,
        t1_margin: timedelta = T1,
    ):
        """Query the Scihub api for product info for the specified missions/orbit_dts.

        Parameters
        ----------
        orbit_dts : list[datetime.datetime]
            List of datetimes to query for
        missions : list[str], choices = {"S1A", "S1B"}
            List of missions to query for. Must be same length as orbit_dts
        orbit_type : str, choices = {"precise", "restituted"}
            String identifying the type of orbit file to query for.
        t0_margin : timedelta
            Margin to add to the start time of the orbit file in the query
        t1_margin : timedelta
            Margin to add to the end time of the orbit file in the query

        Returns
        -------
        list[dict]
            list of results from the query
        """
        remaining_dates: list[tuple[str, datetime]] = []
        all_results = []
        for dt, mission in zip(orbit_dts, missions):
            # Only check for precise orbits if that is what we want
            if orbit_type == "precise":
                products = self.query_orbit(
                    dt - t0_margin,
                    dt + t1_margin,
                    # dt - timedelta(seconds=T_ORBIT + 60),
                    # dt + timedelta(seconds=60),
                    mission,
                    product_type="AUX_POEORB",
                )
                if len(products) == 1:
                    result = products[0]
                elif len(products) > 1:
                    logger.warning(f"Found more than one result: {products}")
                    result = products[0]
                else:
                    result = None
            else:
                result = None

            if result is not None:
                all_results.append(result)
            else:
                # try with RESORB
                products = self.query_orbit(
                    dt - timedelta(seconds=T_ORBIT + 60),
                    dt + timedelta(seconds=60),
                    mission,
                    product_type="AUX_RESORB",
                )
                if len(products) == 1:
                    result = products[0]
                elif len(products) > 1:
                    logger.warning(f"Found more than one result: {products}")
                    result = products[0]
                else:
                    result = None
                    logger.warning(f"Found no restituted results for {dt} {mission}")

                if result:
                    all_results.append(result)

            if result is None:
                remaining_dates.append((mission, dt))

        if remaining_dates:
            logger.warning("The following dates were not found: %s", remaining_dates)
        return all_results

    def download_all(
        self,
        query_results: list[dict],
        output_directory: Filename,
        max_workers: int = 3,
    ):
        """Download all the specified orbit products."""
        return download_all(
            query_results,
            output_directory=output_directory,
            username=self._username,
            password=self._password,
            max_workers=max_workers,
        )


def _construct_orbit_file_query(
    mission_id: str, orbit_type: str, search_start: datetime, search_stop: datetime
):
    """Constructs the query used with the query URL to determine the
    available Orbit files for the given time range.

    Parameters
    ----------
    mission_id : str
        The mission ID parsed from the SAFE file name, should always be one
        of S1A or S1B.
    orbit_type : str
        String identifying the type of orbit file to query for. Should be either
        POEORB for Precise Orbit files, or RESORB for Restituted.
    search_start : datetime
        The start time to use with the query in YYYYmmddTHHMMSS format.
        Any resulting orbit files will have a starting time before this value.
    search_stop : datetime
        The stop time to use with the query in YYYYmmddTHHMMSS format.
        Any resulting orbit files will have an ending time after this value.

    Returns
    -------
    query : str
        The Orbit file query string formatted as the query service expects.

    """
    # Set up templates that use the OData domain specific syntax expected by the
    # query service
    query_template = (
        "startswith(Name,'{mission_id}') and contains(Name,'{orbit_type}') "
        "and ContentDate/Start lt '{start_time}' and ContentDate/End gt '{stop_time}'"
    )

    # Format the query template using the values we were provided
    query_start_date_str = search_start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    query_stop_date_str = search_stop.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    query = query_template.format(
        start_time=query_start_date_str,
        stop_time=query_stop_date_str,
        mission_id=mission_id,
        orbit_type=orbit_type,
    )

    logger.debug(f"query: {query}")

    return query


def query_orbit_file_service(query: str) -> list[dict]:
    """Submit a request to the Orbit file query REST service.

    Parameters
    ----------
    query : str
        The query for the Orbit files to find, filtered by a time range and mission
        ID corresponding to the provided SAFE SLC archive file.

    Returns
    -------
    query_results : list of dict
        The list of results from a successful query. Each result should
        be a Python dictionary containing the details of the orbit file which
        matched the query.

    Raises
    ------
    requests.HTTPError
        If the request fails for any reason (HTTP return code other than 200).

    References
    ----------
    .. [1] https://documentation.dataspace.copernicus.eu/APIs/OData.html#query-by-sensing-date
    """
    # Set up parameters to be included with query request
    query_params = {"$filter": query, "$orderby": "ContentDate/Start asc", "$top": 1}

    # Make the HTTP GET request on the endpoint URL, no credentials are required
    response = requests.get(QUERY_URL, params=query_params)  # type: ignore

    logger.debug(f"response.url: {response.url}")
    logger.debug(f"response.status_code: {response.status_code}")

    response.raise_for_status()

    # Response should be within the text body as JSON
    json_response = response.json()
    logger.debug(f"json_response: {json_response}")

    query_results = json_response["value"]

    return query_results


def get_access_token(username, password) -> Optional[str]:
    """Get an access token for the Copernicus Data Space Ecosystem (CDSE) API.

    Code from https://documentation.dataspace.copernicus.eu/APIs/Token.html
    """
    if not (username and password):
        logger.debug("Get credentials form netrc")
        try:
            username, password = get_netrc_credentials(DATASPACE_HOST)
        except FileNotFoundError:
            logger.warning("No netrc file found.")
            return None

    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }

    try:
        r = requests.post(AUTH_URL, data=data)
        r.raise_for_status()
    except Exception as err:
        raise RuntimeError(f"Access token creation failed. Reason: {str(err)}")

    # Parse the access token from the response
    try:
        access_token = r.json()["access_token"]
    except KeyError:
        raise RuntimeError(
            'Failed to parsed expected field "access_token" from authentication response.'
        )

    return access_token


def download_orbit_file(
    request_url, output_directory, orbit_file_name, access_token
) -> Path:
    """Downloads an Orbit file using the provided request URL.

    Should contain product ID for the file to download, as obtained from a query result.

    The output file is named according to the orbit_file_name parameter, and
    should correspond to the file name parsed from the query result. The output
    file is written to the directory indicated by output_directory.

    Parameters
    ----------
    request_url : str
        The full request URL, which includes the download endpoint, as well as
        a payload that contains the product ID for the Orbit file to be downloaded.
    output_directory : str
        The directory to store the downloaded Orbit file to.
    orbit_file_name : str
        The file name to assign to the Orbit file once downloaded to disk. This
        should correspond to the file name parsed from a query result.
    access_token : str
        Access token returned from an authentication request with the provided
        username and password. Must be provided with all download requests for
        the download service to respond.

    Returns
    -------
    output_orbit_file_path : Path
        The full path to where the resulting Orbit file was downloaded to.

    Raises
    ------
    requests.HTTPError
        If the request fails for any reason (HTTP return code other than 200).

    """
    # Make the HTTP GET request to obtain the Orbit file contents
    headers = {"Authorization": f"Bearer {access_token}"}
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(request_url, headers=headers, stream=True)

    logger.debug(f"r.url: {response.url}")
    logger.debug(f"r.status_code: {response.status_code}")

    response.raise_for_status()

    # Write the contents to disk
    output_orbit_file_path = Path(output_directory) / orbit_file_name

    with open(output_orbit_file_path, "wb") as outfile:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                outfile.write(chunk)

    logger.info(f"Orbit file downloaded to {output_orbit_file_path}")
    return output_orbit_file_path


def download_all(
    query_results: list[dict],
    output_directory: Filename,
    username: str = "",
    password: str = "",
    max_workers: int = 3,
) -> list[Path]:
    """Download all the specified orbit products.

    Parameters
    ----------
    query_results : list[dict]
        list of results from the query
    output_directory : str | Path
        Directory to save the orbit files to.
    username : str
        CDSE username
    password : str
        CDSE password
    max_workers : int, default = 3
        Maximum parallel downloads from CDSE.
        Note that >4 connections will result in a HTTP 429 Error

    """
    downloaded_paths: list[Path] = []
    # Select an appropriate orbit file from the list returned from the query
    # orbit_file_name, orbit_file_request_id = select_orbit_file(
    #     query_results, start_time, stop_time
    # )
    # Obtain an access token the download request from the provided credentials

    access_token = get_access_token(username, password)
    output_names = []
    download_urls = []
    for query_result in query_results:
        orbit_file_request_id = query_result["Id"]

        # Construct the URL used to download the Orbit file
        download_url = f"{DOWNLOAD_URL}({orbit_file_request_id})/$value"
        download_urls.append(download_url)

        orbit_file_name = query_result["Name"]
        output_names.append(orbit_file_name)

        logger.debug(
            f"Downloading Orbit file {orbit_file_name} from service endpoint "
            f"{download_url}"
        )

    downloaded_paths = []
    with ThreadPoolExecutor(max_workers=max_workers) as exc:
        futures = [
            exc.submit(
                download_orbit_file,
                request_url=u,
                output_directory=output_directory,
                orbit_file_name=n,
                access_token=access_token,
            )
            for (u, n) in zip(download_urls, output_names)
        ]
        for f in futures:
            downloaded_paths.append(f.result())

    return downloaded_paths
