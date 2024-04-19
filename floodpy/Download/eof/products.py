# Copyright 2019 Scott Staniewicz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

# Source code copied form:
# https://github.com/scottstanie/apertools/blob/77e6330499adc01c3860f49ee6b3875c49532b76/apertools/parsers.py

"""Utilities for parsing file names of SAR products for relevant info."""
from __future__ import annotations

import re
from datetime import datetime

__all__ = ["Sentinel", "SentinelOrbit"]


class Base(object):
    """Base parser to illustrate expected interface/ minimum data available"""

    def __init__(self, filename, verbose=False):
        """
        Extract data from filename
            filename (str): name of SAR/InSAR product
            verbose (bool): print extra logging into about file loading
        """
        self.filename = filename
        self.full_parse()  # Run a parse to check validity of filename
        self.verbose = verbose

    def __str__(self):
        return "{} product: {}".format(self.__class__.__name__, self.filename)

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return self.filename < other.filename

    def full_parse(self):
        """Returns all parts of the data contained in filename

        Returns:
            tuple: parsed file data. Entry order will match `field_meanings`

        Raises:
            ValueError: if filename string is invalid
        """
        if not hasattr(self, "FILE_REGEX"):
            raise NotImplementedError("Must define class FILE_REGEX to parse")

        match = re.search(self.FILE_REGEX, str(self.filename))
        if not match:
            raise ValueError(
                "Invalid {} filename: {}".format(self.__class__.__name__, self.filename)
            )
        else:
            return match.groupdict()

    @property
    def field_meanings(self):
        """List the fields returned by full_parse()"""
        return self.full_parse().keys()

    def _get_field(self, fieldname):
        """Pick a specific field based on its name"""
        return self.full_parse()[fieldname]

    def __getitem__(self, item):
        """Access properties with uavsar[item] syntax"""
        return self._get_field(item)


class Sentinel(Base):
    """
    Sentinel 1 reference:
    https://sentinel.esa.int/web/sentinel/user-guides/sentinel-1-sar/naming-conventions
    or https://sentinel.esa.int/documents/247904/349449/Sentinel-1_Product_Specification

    Example:
        S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70.zip
        S1A_IW_RAW__0SSV_20151018T005110_20151018T005142_008200_00B886_61EC.zip

    File name format:
        MMM_BB_TTTR_LFPP_YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_OOOOOO_DDDDDD_CCCC.EEEE

    MMM: mission/satellite S1A or S1B
    BB: Mode/beam identifier. The S1-S6 beams apply to SM products IW,
      EW and WV identifiers appply to products from the respective modes.
    TTT: Product Type: RAW, SLC, GRD, OCN
    R: Resolution class: F, H, M, or _ (N/A)
    L: Processing Level: 0, 1, 2
    F: Product class: S (standard), A (annotation, only used internally)
        - we only care about standard
    PP: Polarization: SH (single HH), SV (single VV), DH (dual HH+HV), DV (dual VV+VH)
    Start date + time (date/time separated by T)
    Stop date + time
    OOOOOO: absolute orbit number: 000001-999999
    DDDDDD: mission data-take identifier: 000001-FFFFFF.
    CCCC: product unique identifier: hexadecimal string from CRC-16 hashing
        the manifest file using CRC-CCITT.

    Once unzipped, the folder extension is always "SAFE"

    Attributes:
        filename (str) name of the sentinel data product
    """

    FILE_REGEX = re.compile(
        r"(?P<mission>S1A|S1B)_"
        r"(?P<beam>[\w\d]{2})_"
        r"(?P<product_type>[\w_]{3})"
        r"(?P<resolution_class>[FHM_])_"
        r"(?P<product_level>[012])[SA]"
        r"(?P<polarization>[SDHV]{2})_"
        r"(?P<start_datetime>[T\d]{15})_"
        r"(?P<stop_datetime>[T\d]{15})_"
        r"(?P<orbit_number>\d{6})_"
        r"(?P<datetake_identifier>[\d\w]{6})_"
        r"(?P<unique_id>[\d\w]{4})"
    )
    TIME_FMT = "%Y%m%dT%H%M%S"

    def __init__(self, filename, **kwargs):
        super(Sentinel, self).__init__(filename, **kwargs)
        # The name of the unzipped .SAFE directory (with .zip stripped)

    def __str__(self):
        return "{} {}, path {} from {}".format(
            self.__class__.__name__, self.mission, self.path, self.date
        )

    def __lt__(self, other):
        return (self.start_time, self.filename) < (other.start_time, other.filename)

    def __eq__(self, other):
        # TODO: Do we just want to compare product_uids?? or filenames?
        return self.product_uid == other.product_uid
        # return self.filename == other.filename

    def __hash__(self):
        return hash(self.product_uid)

    @property
    def start_time(self):
        """Returns start datetime from a sentinel file name

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.start_time)
            2018-04-08 04:30:25
        """
        start_time_str = self._get_field("start_datetime")
        return datetime.strptime(start_time_str, self.TIME_FMT)

    @property
    def stop_time(self):
        """Returns stop datetime from a sentinel file name

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.stop_time)
            2018-04-08 04:30:53
        """
        stop_time_str = self._get_field("stop_datetime")
        return datetime.strptime(stop_time_str, self.TIME_FMT)

    @property
    def polarization(self):
        """Returns type of polarization of product

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.polarization)
            DV
        """
        return self._get_field("polarization")

    @property
    def product_type(self):
        """Returns product type/level

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.product_type)
            SLC
        """
        return self._get_field("product_type")

    @property
    def level(self):
        """Alias for product type/level"""
        return self.product_type

    @property
    def mission(self):
        """Returns satellite/mission of product (S1A/S1B)

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.mission)
            S1A
        """
        return self._get_field("mission")

    @property
    def absolute_orbit(self):
        """Absolute orbit of data, included in file name

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.absolute_orbit)
            21371
        """
        return int(self._get_field("orbit_number"))

    @property
    def relative_orbit(self):
        """Relative orbit number/ path

        Formulas for relative orbit from absolute come from:
        https://forum.step.esa.int/t/sentinel-1-relative-orbit-from-filename/7042

        Example:
            >>> s = Sentinel('S1A_IW_SLC__1SDV_20180408T043025_20180408T043053_021371_024C9B_1B70')
            >>> print(s.relative_orbit)
            124
            >>> s = Sentinel('S1B_WV_OCN__2SSV_20180522T161319_20180522T164846_011036_014389_67D8')
            >>> print(s.relative_orbit)
            160
        """
        if self.mission == "S1A":
            return ((self.absolute_orbit - 73) % 175) + 1
        elif self.mission == "S1B":
            return ((self.absolute_orbit - 27) % 175) + 1

    @property
    def path(self):
        """Alias for relative orbit number"""
        return self.relative_orbit

    @property
    def product_uid(self):
        """Unique identifier of product (last 4 of filename)"""
        return self._get_field("unique_id")

    @property
    def date(self):
        """Date of acquisition: shortcut for start_time.date()"""
        return self.start_time.date()


class SentinelOrbit(Base):
    """
    Sentinel 1 orbit reference:
    https://sentinel.esa.int/documents/247904/351187/GMES_Sentinels_POD_Service_File_Format_Specification
        section 2
    https://qc.sentinel1.eo.esa.int/doc/api/
    https://sentinels.copernicus.eu/documents/247904/3372484/Copernicus-POD-Regular-Service-Review-Jun-Sep-2018.pdf
        see here (section 3.6) for differences in orbit accuracy)

    Example:
        S1A_OPER_AUX_PREORB_OPOD_20200325T131800_V20200325T121452_20200325T184952.EOF

    The filename must comply with the following pattern:
        MMM_CCCC_TTTTTTTTTT_<instance_id>.EOF

    MMM = mission, S1A or S1B
    CCCC =  File Class, we only want OPER = routine operational
    TTTTTTTTTT = File type
     = FFFF DDDDDD
        FFFF = file category, we want AUX_:auxiliary data files;
        DDDDDD = Semantic Descriptor
        most common = POEORB: Precise Orbit Ephemerides (POE) Orbit File
            (available after 1-2 weeks)
        also, RESORB: Restituted orbit file
            (covers 6 hour windows, less accurate, more immediate)
        TODO: do I ever want to deal with the AUX antenna files?

    <instance id> has a couple:
    ssss_yyyymmddThhmmsswhere:
        ssss is the Site Centre of the file originator (OPOD for S-1 and S-2)
        and a validity start/stop, same date format

    Attributes:
        filename (str) name of the sentinel data product
    """

    TIME_FMT = "%Y%m%dT%H%M%S"
    FILE_REGEX = (
        r"(?P<mission>S1A|S1B)_OPER_AUX_"
        r"(?P<orbit_type>[\w_]{6})_OPOD_"
        r"(?P<created_datetime>[T\d]{15})_"
        r"V(?P<start_datetime>[T\d]{15})_"
        r"(?P<stop_datetime>[T\d]{15})"
    )

    def __init__(self, filename, **kwargs):
        super(SentinelOrbit, self).__init__(filename, **kwargs)

    def __str__(self):
        return "{} {} from {} to {}".format(
            self.orbit_type, self.__class__.__name__, self.start_time, self.stop_time
        )

    def __lt__(self, other):
        return (self.start_time, self.filename) < (other.start_time, other.filename)

    def __contains__(self, dt):
        """Checks if a datetime lies within the validity window"""
        return self.start_time < dt < self.stop_time

    def __eq__(self, other):
        return (
            self.mission,
            self.start_time,
            self.stop_time,
            self.orbit_type,
        ) == (
            other.mission,
            other.start_time,
            other.stop_time,
            other.orbit_type,
        )

    @property
    def mission(self):
        """Returns satellite/mission of product (S1A/S1B)

        Example:
            >>> s = SentinelOrbit('S1A_OPER_AUX_POEORB_OPOD_20200121T120654_V20191231T225942_20200102T005942.EOF')
            >>> print(s.mission)
            S1A
        """
        return self._get_field("mission")

    @property
    def start_time(self):
        """Returns start datetime of an orbit

        Example:
            >>> s = SentinelOrbit('S1A_OPER_AUX_POEORB_OPOD_20200121T120654_V20191231T225942_20200102T005942.EOF')
            >>> print(s.start_time)
            2019-12-31 22:59:42
        """
        start_time_str = self._get_field("start_datetime")
        return datetime.strptime(start_time_str, self.TIME_FMT)

    @property
    def stop_time(self):
        """Returns stop datetime from a sentinel file name

        Example:
            >>> s = SentinelOrbit('S1A_OPER_AUX_POEORB_OPOD_20200121T120654_V20191231T225942_20200102T005942.EOF')
            >>> print(s.stop_time)
            2020-01-02 00:59:42
        """
        stop_time_str = self._get_field("stop_datetime")
        return datetime.strptime(stop_time_str, self.TIME_FMT)

    @property
    def created_time(self):
        """Returns created datetime from a orbit file name

        Example:
            >>> s = SentinelOrbit('S1A_OPER_AUX_POEORB_OPOD_20200121T120654_V20191231T225942_20200102T005942.EOF')
            >>> print(s.created_time)
            2020-01-21 12:06:54
        """
        stop_time_str = self._get_field("created_datetime")
        return datetime.strptime(stop_time_str, self.TIME_FMT)

    @property
    def orbit_type(self):
        """Type of orbit file (e.g precise, restituted)

        Example:
        >>> s = SentinelOrbit('S1A_OPER_AUX_POEORB_OPOD_20200121T120654_V20191231T225942_20200102T005942.EOF')
        >>> print(s.orbit_type)
        precise
        >>> s = SentinelOrbit('S1B_OPER_AUX_RESORB_OPOD_20200325T151938_V20200325T112442_20200325T144212.EOF')
        >>> print(s.orbit_type)
        restituted
        """
        o = self._get_field("orbit_type")
        if o == "POEORB":
            return "precise"
        elif o == "RESORB":
            return "restituted"
        elif o == "PREORB":
            return "predicted"
        else:
            raise ValueError("unknown orbit type: %s" % self.filename)

    @property
    def date(self):
        """Date of acquisition: shortcut for start_time.date()"""
        return self.start_time.date()
