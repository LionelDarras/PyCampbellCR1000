# coding: utf8
'''
    PyCampbellCRX.tests.test_device
    -------------------------------

    The device test suite for.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
from datetime import datetime, timedelta

from ..logger import active_logger
from ..device import CR1000


active_logger()

device = None


def get_device(url):
    global device
    if device is None:
        device = CR1000.from_url(url, 1)
    return device


def test_gettime(url):
    device = get_device(url)
    assert isinstance(device.gettime(), datetime)


def test_settime(url):
    device = get_device(url)
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
    device = get_device(url)
    assert device.settings[0]['SettingId'] == 0
    print (device.settings[0]['SettingValue'])
    print (type(device.settings[0]['SettingValue']))
    assert b"CR" in device.settings[0]['SettingValue']
    assert device.settings[0]['ReadOnly'] == 1
    assert device.settings[0]['LargeValue'] == 0


def test_list_and_get_file(url):
    device = get_device(url)
    files = device.list_files()
    if len(files) > 1:
        for filename in files[1:]:
            filename = filename.decode('utf-8')
            if filename != "CPU:":
                fd = device.getfile(filename)
                assert fd != b""
                break


def get_data_generator(url, table):
    device = get_device(url)
    generator = device.get_data_generator(table, None, None)
    try:
        first_records = next(generator)
    except StopIteration:
        first_records = []
    if len(first_records) > 0:
        rec = first_records[0]
        for next_rec in first_records[1:]:
            assert rec['Datetime'] < next_rec['Datetime']
            rec = next_rec


def get_data(url, table):
    device = get_device(url)
    start_date = datetime.now() - timedelta(days=2)
    stop_date = datetime.now() - timedelta(days=1, hours=6)
    records = device.get_data(table, start_date, stop_date)
    if len(records) > 0:
        for item in records:
            assert start_date <= item["Datetime"] < stop_date


def test_list_get_tables(url):
    device = get_device(url)
    tables = device.list_tables()
    if len(tables) > 0:
        for table in tables:
            table = table.decode('utf-8')
            get_data(url, table)
            get_data_generator(url, table)


def test_getprogstat(url):
    device = get_device(url)
    osversion = device.getprogstat()['OSVer'].decode('utf-8')
    osversion = osversion.split(".")[0]
    assert (osversion == "CR800" or osversion == "CR1000")
