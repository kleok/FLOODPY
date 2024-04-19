"""Module for parsing the orbit state vectors (OSVs) from the .EOF file"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from xml.etree import ElementTree

from .log import logger


class EOFLinkFinder(HTMLParser):
    """Finds EOF download links in aux.sentinel1.eo.esa.int page

    Example page to search:
    http://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/S1B/2020/10/

    Usage:
    >>> import requests
    >>> resp = requests.get("http://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/S1B/2020/10/")
    >>> parser = EOFLinkFinder()
    >>> parser.feed(resp.text)
    """

    def __init__(self):
        super().__init__()
        self.eof_links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and (
                    value.endswith(".EOF.zip") or value.endswith(".EOF")
                ):
                    self.eof_links.add(value)


def parse_utc_string(timestring):
    #    dt = datetime.strptime(timestring, 'TAI=%Y-%m-%dT%H:%M:%S.%f')
    #    dt = datetime.strptime(timestring, 'UT1=%Y-%m-%dT%H:%M:%S.%f')
    return datetime.strptime(timestring, "UTC=%Y-%m-%dT%H:%M:%S.%f")


def secs_since_midnight(dt):
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1000000.0


def _convert_osv_field(osv, field, converter=float):
    # osv is a xml.etree.ElementTree.Element
    field_str = osv.find(field).text
    return converter(field_str)


def parse_orbit(
    eof_filename,
    min_time=datetime(1900, 1, 1),
    max_time=datetime(2100, 1, 1),
    extra_osvs=1,
):
    min_time = to_datetime(min_time)
    max_time = to_datetime(max_time)
    logger.info(
        "parsing OSVs from %s between %s and %s",
        eof_filename,
        min_time,
        max_time,
    )
    tree = ElementTree.parse(eof_filename)
    root = tree.getroot()
    all_osvs = []
    idxs_in_range = []
    for idx, osv in enumerate(root.findall("./Data_Block/List_of_OSVs/OSV")):
        all_osvs.append(osv)
        utc_dt = to_datetime(_convert_osv_field(osv, "UTC", parse_utc_string))
        if utc_dt >= min_time and utc_dt <= max_time:
            idxs_in_range.append(idx)

    if not idxs_in_range:
        return []

    min_idx = min(idxs_in_range)
    for ii in range(extra_osvs):
        idxs_in_range.append(min_idx - 1 - ii)
    max_idx = max(idxs_in_range)
    for ii in range(extra_osvs):
        idxs_in_range.append(max_idx + 1 + ii)
    idxs_in_range.sort()

    osvs_in_range = []
    for idx in idxs_in_range:
        cur_osv = all_osvs[idx]
        utc_dt = _convert_osv_field(cur_osv, "UTC", parse_utc_string)
        utc_secs = secs_since_midnight(utc_dt)
        cur_line = [utc_secs]
        for field in ("X", "Y", "Z", "VX", "VY", "VZ"):
            # Note: the 'unit' would be elem.attrib['unit']
            cur_line.append(_convert_osv_field(cur_osv, field, float))
        osvs_in_range.append(cur_line)

    return osvs_in_range


def write_orbinfo(orbit_tuples, outname="out.orbtiming"):
    """Write file with orbit states parsed into simpler format

    seconds x y z vx vy vz ax ay az
    """
    with open(outname, "w") as f:
        f.write("0\n")
        f.write("0\n")
        f.write("0\n")
        f.write("%s\n" % len(orbit_tuples))
        for tup in orbit_tuples:
            # final 0.0 0.0 0.0 is ax, ax, az accelerations
            f.write(" ".join(map(str, tup)) + " 0.0 0.0 0.0\n")


def to_datetime(dates, tzinfo=timezone.utc):
    """Convert a single (or list of) `datetime.date` to timezone-aware `datetime.datetime`"""
    if isinstance(dates, datetime):
        return datetime(*dates.timetuple()[:6], tzinfo=tzinfo)
    try:
        iter(dates)
        if len(dates) == 0:
            return dates
        try:  # Check if its a list of tuples (an ifglist)
            iter(dates[0])
            return [to_datetime(tup) for tup in dates]
        except TypeError:
            return [datetime(*d.timetuple()[:6], tzinfo=tzinfo) for d in dates]
    # Or if it's just one sigle date
    except TypeError:
        return datetime(*dates.timetuple()[:6], tzinfo=tzinfo)
