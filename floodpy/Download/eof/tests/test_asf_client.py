import datetime

import pytest

from eof.asf_client import ASFClient

# pytest --record-mode=all


@pytest.mark.vcr
def test_asf_client():
    ASFClient()


@pytest.mark.vcr
def test_asf_full_url_list(tmp_path):
    cache_dir = tmp_path / "sentineleof1"
    cache_dir.mkdir()
    asfclient = ASFClient(cache_dir=cache_dir)

    urls = asfclient.get_full_eof_list()
    assert len(urls) > 0
    # Should be quick second time
    assert len(asfclient.get_full_eof_list())


@pytest.mark.vcr
def test_asf_client_download(tmp_path):
    cache_dir = tmp_path / "sentineleof2"
    cache_dir.mkdir()
    asfclient = ASFClient(cache_dir=cache_dir)

    dt = datetime.datetime(2020, 1, 1)
    mission = "S1A"
    urls = asfclient.get_download_urls([dt], [mission], orbit_type="precise")
    expected = "https://s1qc.asf.alaska.edu/aux_poeorb/S1A_OPER_AUX_POEORB_OPOD_20210315T155112_V20191230T225942_20200101T005942.EOF"  # noqa
    assert urls == [expected]
