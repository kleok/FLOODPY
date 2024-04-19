import datetime
from pathlib import Path

import pytest

from eof import download, products


@pytest.mark.vcr
def test_find_scenes_to_download(tmpdir):
    with tmpdir.as_cwd():
        name1 = (
            "S1A_IW_SLC__1SDV_20180420T043026_20180420T043054_021546_025211_81BE.zip"
        )
        name2 = (
            "S1B_IW_SLC__1SDV_20180502T043026_20180502T043054_021721_025793_5C18.zip"
        )
        open(name1, "w").close()
        open(name2, "w").close()
        orbit_dates, missions = download.find_scenes_to_download(search_path=".")

        assert sorted(orbit_dates) == [
            datetime.datetime(2018, 4, 20, 4, 30, 26),
            datetime.datetime(2018, 5, 2, 4, 30, 26),
        ]

        assert sorted(missions) == ["S1A", "S1B"]


@pytest.mark.vcr
def test_download_eofs_errors():
    orbit_dates = [datetime.datetime(2018, 5, 2, 4, 30, 26)]
    with pytest.raises(ValueError):
        download.download_eofs(orbit_dates, missions=["BadMissionStr"])
    # 1 date, 2 missions ->
    # ValueError: missions arg must be same length as orbit_dts
    with pytest.raises(ValueError):
        download.download_eofs(orbit_dates, missions=["S1A", "S1B"])


def test_main_nothing_found():
    # Test "no sentinel products found"
    assert download.main(search_path="/notreal") == []


def test_main_error_args():
    with pytest.raises(ValueError):
        download.main(search_path="/notreal", mission="S1A")


@pytest.mark.vcr
def test_download_mission_date(tmpdir):
    with tmpdir.as_cwd():
        filenames = download.main(mission="S1A", date="20200101")
    assert len(filenames) == 1
    product = products.SentinelOrbit(filenames[0])
    assert product.start_time < datetime.datetime(2020, 1, 1)
    assert product.stop_time > datetime.datetime(2020, 1, 1, 23, 59)


@pytest.mark.vcr
def test_edge_issue45(tmpdir):
    date = "2023-10-13 11:15:11"
    with tmpdir.as_cwd():
        filenames = download.main(mission="S1A", date=date)
    assert len(filenames) == 1


@pytest.mark.vcr
@pytest.mark.parametrize("force_asf", [True, False])
def test_download_multiple(tmpdir, force_asf):
    granules = [
        "S1A_IW_SLC__1SDV_20180420T043026_20180420T043054_021546_025211_81BE.zip",
        "S1B_IW_SLC__1SDV_20180502T043026_20180502T043054_021721_025793_5C18.zip",
    ]
    with tmpdir.as_cwd():
        # Make empty files
        for g in granules:
            Path(g).write_text("")

        out_paths = download.main(search_path=".", force_asf=force_asf, max_workers=1)
        # should find two .EOF files
        expected_eofs = [
            "S1A_OPER_AUX_POEORB_OPOD_20210307T053325_V20180419T225942_20180421T005942.EOF",
            "S1B_OPER_AUX_POEORB_OPOD_20210313T012515_V20180501T225942_20180503T005942.EOF",
        ]
        assert len(out_paths) == 2
        assert sorted((p.name for p in out_paths)) == expected_eofs
