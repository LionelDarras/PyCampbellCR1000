# coding: utf8
'''
    pycr1000.tests.test_cr1000
    --------------------------

    The CR1000 test suite for.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import pytest

from datetime import datetime, timedelta

from ..logger import active_logger
from ..device import CR1000


# active logging for tests
active_logger()

@pytest.mark.cr1000
def test_gettime(url):
    device = CR1000.from_url(url, 1)
    assert isinstance(device.gettime(), datetime)

@pytest.mark.cr1000
def test_settime(url):
    device = CR1000.from_url(url, 1)
    now = datetime.now().replace(second=10, microsecond=0)
    device_time = device.settime(now)
    assert device_time.second in (10, 11, 12)
    assert now == device_time.replace(second=10)

@pytest.mark.cr1000
def test_settings(url):
    device = CR1000.from_url(url, 1)
    assert device.settings[0]['SettingId'] == 0
    print (device.settings[0]['SettingValue'])
    print (type(device.settings[0]['SettingValue']))
    assert b"CR1000" in device.settings[0]['SettingValue']
    assert device.settings[0]['ReadOnly'] == 1
    assert device.settings[0]['LargeValue'] == 0

@pytest.mark.cr1000
def test_listdir(url):
    device = CR1000.from_url(url, 1)
    assert len(device.listdir()) > 1

@pytest.mark.cr1000
def test_getfile(url):
    device = CR1000.from_url(url, 1)
    fd = device.getfile('CPU:CR1000_LABO.CR1')
    assert b"CR1000" in fd

@pytest.mark.cr1000
def test_getprogstat(url):
    device = CR1000.from_url(url, 1)
    b"CR1000" in device.getprogstat()['OSVer']

