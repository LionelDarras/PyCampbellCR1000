# coding: utf8
'''
    pycr1000.tests.test_cr1000
    --------------------------

    The CR1000 test suite for.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
from datetime import datetime, timedelta

from ..logger import active_logger
from ..device import CR1000


# active logging for tests
active_logger()


def test_gettime(url):
    device = CR1000.from_url(url, 1)
    assert isinstance(device.gettime(), datetime)


def test_settime(url):
    device = CR1000.from_url(url, 1)
    now = datetime.now().replace(second=10, microsecond=0)
    device_time = device.settime(now)
    assert device_time.second in (10, 11, 12)
    assert now == device_time.replace(second=10)
    lastday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    assert lastday == device.settime(lastday).replace(second=10)
    assert tomorrow == device.settime(tomorrow).replace(second=10)
    device.settime(datetime.now())


def test_settings(url):
    device = CR1000.from_url(url, 1)
    assert device.settings[0]['SettingId'] == 0
    print (device.settings[0]['SettingValue'])
    print (type(device.settings[0]['SettingValue']))
    assert b"CR1000" in device.settings[0]['SettingValue']
    assert device.settings[0]['ReadOnly'] == 1
    assert device.settings[0]['LargeValue'] == 0


def test_list_files(url):
    device = CR1000.from_url(url, 1)
    assert len(device.list_files()) > 1


def test_getfile(url):
    device = CR1000.from_url(url, 1)
    fd = device.getfile('CPU:CR1000_LABO.CR1')
    assert b"CR1000" in fd


def test_list_tables(url):
    device = CR1000.from_url(url, 1)
    assert b"Public" in device.list_tables()


def test_get_data(url):
    device = CR1000.from_url(url, 1)
    start_date = datetime.now() - timedelta(minutes=30)
    stop_date = datetime.now()
    data = device.get_all_data('Table1', start_date, stop_date)
    assert len(data) > 0
    for item in data:
        assert start_date <= item["Datetime"] < stop_date


def test_getprogstat(url):
    device = CR1000.from_url(url, 1)
    b"CR1000" in device.getprogstat()['OSVer']
