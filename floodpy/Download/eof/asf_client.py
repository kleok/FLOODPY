"""Client to get orbit files from ASF."""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests

from ._auth import NASA_HOST, get_netrc_credentials
from ._select_orbit import T_ORBIT, ValidityError, last_valid_orbit
from ._types import Filename
from .log import logger
from .parsing import EOFLinkFinder
from .products import SentinelOrbit

SIGNUP_URL = "https://urs.earthdata.nasa.gov/users/new"
"""Url to prompt user to sign up for NASA Earthdata account."""


class ASFClient:
    auth_url = (
        "https://urs.earthdata.nasa.gov/oauth/authorize?response_type=code&"
        "client_id=BO_n7nTIlMljdvU6kRRB3g&redirect_uri=https://auth.asf.alaska.edu/login"
    )

    precise_url = "https://s1qc.asf.alaska.edu/aux_poeorb/"
    res_url = "https://s1qc.asf.alaska.edu/aux_resorb/"
    urls = {"precise": precise_url, "restituted": res_url}
    eof_lists = {"precise": None, "restituted": None}

    def __init__(
        self,
        cache_dir: Optional[Filename] = None,
        username: str = "",
        password: str = "",
    ):
        self._cache_dir = cache_dir
        if username and password:
            self._username = username
            self._password = password
        else:
            logger.debug("Get credentials form netrc")
            self._username = ""
            self._password = ""
            try:
                self._username, self._password = get_netrc_credentials(NASA_HOST)
            except FileNotFoundError:
                logger.warning("No netrc file found.")
            except ValueError as e:
                if NASA_HOST not in e.args[0]:
                    raise e
                logger.warning(
                    f"No NASA Earthdata credentials found in netrc file. Please create one using {SIGNUP_URL}"
                )

        self.session: Optional[requests.Session] = None
        if self._username and self._password:
            self.session = self.get_authenticated_session()

    def get_full_eof_list(self, orbit_type="precise", max_dt=None):
        """Get the list of orbit files from the ASF server."""
        if orbit_type not in self.urls.keys():
            raise ValueError("Unknown orbit type: {}".format(orbit_type))

        if self.eof_lists.get(orbit_type) is not None:
            return self.eof_lists[orbit_type]
        # Try to see if we have the list of EOFs in the cache
        elif os.path.exists(self._get_filename_cache_path(orbit_type)):
            eof_list = self._get_cached_filenames(orbit_type)
            # Need to clear it if it's older than what we're looking for
            max_saved = max([e.start_time for e in eof_list])
            if max_saved < max_dt:
                logger.warning("Clearing cached {} EOF list:".format(orbit_type))
                logger.warning(
                    "{} is older than requested {}".format(max_saved, max_dt)
                )
                self._clear_cache(orbit_type)
            else:
                logger.info("Using cached EOF list")
                self.eof_lists[orbit_type] = eof_list
                return eof_list

        logger.info("Downloading all filenames from ASF (may take awhile)")
        resp = requests.get(self.urls.get(orbit_type))
        finder = EOFLinkFinder()
        finder.feed(resp.text)
        eof_list = [SentinelOrbit(f) for f in finder.eof_links]
        self.eof_lists[orbit_type] = eof_list
        self._write_cached_filenames(orbit_type, eof_list)
        return eof_list

    def get_download_urls(self, orbit_dts, missions, orbit_type="precise"):
        """Find the URL for an orbit file covering the specified datetime

        Args:
            dt (datetime): requested
        Args:
            orbit_dts (list[str] or list[datetime]): datetime for orbit coverage
            missions (list[str]): specify S1A or S1B

        Returns:
            str: URL for the orbit file
        """
        eof_list = self.get_full_eof_list(orbit_type=orbit_type, max_dt=max(orbit_dts))
        # Split up for quicker parsing of the latest one
        mission_to_eof_list = {
            "S1A": [eof for eof in eof_list if eof.mission == "S1A"],
            "S1B": [eof for eof in eof_list if eof.mission == "S1B"],
        }
        # For precise orbits, we can have a larger front margin to ensure we
        # cover the ascending node crossing
        if orbit_type == "precise":
            margin0 = timedelta(seconds=T_ORBIT + 60)
        else:
            margin0 = timedelta(seconds=60)

        remaining_orbits = []
        urls = []
        for dt, mission in zip(orbit_dts, missions):
            try:
                filename = last_valid_orbit(
                    dt, dt, mission_to_eof_list[mission], margin0=margin0
                )
                urls.append(self.urls[orbit_type] + filename)
            except ValidityError:
                remaining_orbits.append((dt, mission))

        if remaining_orbits:
            logger.warning("The following dates were not found: %s", remaining_orbits)
            if orbit_type == "precise":
                logger.warning(
                    "Attempting to download the restituted orbits for these dates."
                )
                remaining_dts, remaining_missions = zip(*remaining_orbits)
                urls.extend(
                    self.get_download_urls(
                        remaining_dts, remaining_missions, orbit_type="restituted"
                    )
                )

        return urls

    def _get_cached_filenames(self, orbit_type="precise"):
        """Get the cache path for the ASF orbit files."""
        filepath = self._get_filename_cache_path(orbit_type)
        logger.debug(f"ASF file path cache: {filepath = }")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return [SentinelOrbit(f) for f in f.read().splitlines()]
        return None

    def _write_cached_filenames(self, orbit_type="precise", eof_list=[]):
        """Cache the ASF orbit files."""
        filepath = self._get_filename_cache_path(orbit_type)
        with open(filepath, "w") as f:
            for e in eof_list:
                f.write(e.filename + "\n")

    def _clear_cache(self, orbit_type="precise"):
        """Clear the cache for the ASF orbit files."""
        filepath = self._get_filename_cache_path(orbit_type)
        os.remove(filepath)

    def _get_filename_cache_path(self, orbit_type="precise"):
        fname = "{}_filenames.txt".format(orbit_type.lower())
        return os.path.join(self.get_cache_dir(), fname)

    def get_cache_dir(self):
        """Find location of directory to store .hgt downloads
        Assuming linux, uses ~/.cache/sentineleof/
        """
        if self._cache_dir is not None:
            return self._cache_dir
        path = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        path = os.path.join(path, "sentineleof")  # Make subfolder for our downloads
        logger.debug("Cache path: %s", path)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def _download_and_write(self, url, save_dir=".") -> Path:
        """Wrapper function to run the link downloading in parallel

        Args:
            url (str): url of orbit file to download
            save_dir (str): directory to save the EOF files into

        Returns:
            Path: Filename to saved orbit file
        """
        fname = Path(save_dir) / url.split("/")[-1]
        if os.path.isfile(fname):
            logger.info("%s already exists, skipping download.", url)
            return fname

        logger.info("Downloading %s", url)
        get_function = self.session.get if self.session is not None else requests.get
        try:
            response = get_function(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(e)

            login_url = self.auth_url + f"&state={url}"
            logger.warning(
                "Failed to download %s. Trying URS login url: %s", url, login_url
            )
            # Add credentials
            response = get_function(login_url, auth=(self._username, self._password))
            response.raise_for_status()

        logger.info("Saving to %s", fname)
        with open(fname, "wb") as f:
            f.write(response.content)
        if fname.suffix == ".zip":
            ASFClient._extract_zip(fname, save_dir=save_dir)
            # Pass the unzipped file ending in ".EOF", not the ".zip"
            fname = fname.with_suffix("")
        return fname

    @staticmethod
    def _extract_zip(fname_zipped: Path, save_dir=None, delete=True):
        if save_dir is None:
            save_dir = fname_zipped.parent
        with ZipFile(fname_zipped, "r") as zip_ref:
            # Extract the .EOF to the same direction as the .zip
            zip_ref.extractall(path=save_dir)

            # check that there's not a nested zip structure
            zipped = zip_ref.namelist()[0]
            zipped_dir = os.path.dirname(zipped)
            if zipped_dir:
                no_subdir = save_dir / os.path.split(zipped)[1]
                os.rename((save_dir / zipped), no_subdir)
                os.rmdir((save_dir / zipped_dir))
        if delete:
            os.remove(fname_zipped)

    def get_authenticated_session(self) -> requests.Session:
        """Get an authenticated `requests.Session` using earthdata credentials.

        Fuller example here:
        https://github.com/ASFHyP3/hyp3-sdk/blob/ec72fcdf944d676d5c8c94850d378d3557115ac0/src/hyp3_sdk/util.py#L67C8-L67C8

        Returns
        -------
        requests.Session
            Authenticated session
        """
        s = requests.Session()
        response = s.get(self.auth_url, auth=(self._username, self._password))
        response.raise_for_status()
        return s
