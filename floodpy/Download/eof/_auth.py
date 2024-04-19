from __future__ import annotations

import getpass
import netrc
import os
from pathlib import Path

from ._types import Filename
from .log import logger as _logger

NASA_HOST = "urs.earthdata.nasa.gov"
DATASPACE_HOST = "dataspace.copernicus.eu"


def check_netrc(netrc_file: Filename = "~/.netrc"):
    """Chech that the netrc file exists and has the proper permissions."""
    if not _file_is_0600(netrc_file):
        # User has a netrc file, but it's not set up correctly
        _logger.warning(
            f"Your netrc file ('{netrc_file}') does not have the "
            f"correct permissions: 0600* (read/write for user only).",
        )


def setup_netrc(
    netrc_file: Filename = "~/.netrc",
    host: str = NASA_HOST,
    dryrun: bool = False,
):
    """Prompt user for NASA/Dataspace username/password, store as attribute of ~/.netrc."""
    netrc_file = Path(netrc_file).expanduser()
    try:
        n = netrc.netrc(netrc_file)
        has_correct_permission = _file_is_0600(netrc_file)
        if not has_correct_permission:
            # User has a netrc file, but it's not set up correctly
            if dryrun:
                _logger.warning(
                    f"Your netrc file ('{netrc_file}') does not have the "
                    f"correct permissions: 0600* (read/write for user only).",
                )
            else:
                _logger.warning(
                    "Your ~/.netrc file does not have the correct"
                    " permissions.\n*Changing permissions to 0600*"
                    " (read/write for user only).",
                )
                os.chmod(netrc_file, 0o600)
        # Check account exists, as well is having username and password
        authenticator = n.authenticators(host)
        if authenticator is not None:
            username, _, password = authenticator

        _has_existing_entry = (
            host in n.hosts
            and username  # type: ignore
            and password  # type: ignore
        )
        if _has_existing_entry:
            return username, password
    except FileNotFoundError:
        if not dryrun:
            # User doesn't have a netrc file, make one
            print("No ~/.netrc file found, creating one.")
            Path(netrc_file).write_text("")
            n = netrc.netrc(netrc_file)

    username, password = _get_username_pass(host)
    if not dryrun:
        # Add account to netrc file
        n.hosts[host] = (username, None, password)
        print(f"Saving credentials to {netrc_file} (machine={host}).")
        with open(netrc_file, "w") as f:
            f.write(str(n))
        # Set permissions to 0600 (read/write for user only)
        # https://www.ibm.com/docs/en/aix/7.1?topic=formats-netrc-file-format-tcpip
        os.chmod(netrc_file, 0o600)

    return username, password


def _file_is_0600(filename: Filename):
    """Check that a file has 0600 permissions (read/write for user only)."""
    return oct(Path(filename).stat().st_mode)[-4:] == "0600"


def get_netrc_credentials(host: str) -> tuple[str, str]:
    """Get username and password from netrc file for a given host."""
    n = netrc.netrc()
    auth = n.authenticators(host)
    if auth is None:
        raise ValueError(f"No username/password found for {host} in ~/.netrc")
    username, _, password = auth
    if username is None or password is None:
        raise ValueError(f"No username/password found for {host} in ~/.netrc")
    return username, password


def _get_username_pass(host: str):
    """If netrc is not set up, get username/password via command line input."""
    if host == NASA_HOST:
        from .asf_client import SIGNUP_URL as signup_url
    elif host == DATASPACE_HOST:
        from .dataspace_client import SIGNUP_URL as signup_url

    print(f"Please enter credentials for {host} to download data.")
    print(f"See the {signup_url} for signup info")

    username = input("Username: ")

    password = getpass.getpass("Password (will not be displayed): ")
    return username, password
