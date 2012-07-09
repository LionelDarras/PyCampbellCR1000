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
    assert device_time.second in (10,11,12)
    assert now == device_time.replace(second=10)


def test_settings(url):
    device = CR1000.from_url(url, 1)
    assert device.settings[0]['SettingId'] == 0
    print (device.settings[0]['SettingValue'])
    print (type(device.settings[0]['SettingValue']))
    assert b"CR" in device.settings[0]['SettingValue']
    assert device.settings[0]['ReadOnly'] == 1
    assert device.settings[0]['LargeValue'] == 0

