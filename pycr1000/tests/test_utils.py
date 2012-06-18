# coding: utf8
'''
    pyvantagepro.tests.test_link
    ----------------------------

    The pyvantagepro test suite.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''

from __future__ import unicode_literals
import os
import random

from ..utils import (cached_property, retry, Dict, hex_to_bytes,
                     bytes_to_hex, bytes_to_binary, hex_to_binary,
                     binary_to_int, csv_to_dict, is_text, is_bytes)
from ..compat import StringIO


def test_is_text_or_byte():
    '''Tests is text.'''
    assert is_text("Text") is True
    assert is_text(b"\xFF\xFF") is False
    assert is_bytes(b"\xFF\xFF") is True
    assert is_bytes("Text") is False


def test_csv_to_dict():
    '''Tests csv to dict.'''
    file_input = StringIO("a,f\r\n111,222")
    items = csv_to_dict(file_input)
    assert items[0]["a"] == "111"
    assert items[0]["f"] == "222"


def test_csv_to_dict_file():
    '''Tests csv to dict with file archives.'''
    path = os.path.join('pyvantagepro', 'tests', 'ressources', 'archives.csv')
    path = os.path.abspath(os.path.join('.', path))
    file_input = open(path, 'r')
    items = csv_to_dict(file_input).sorted_by("Datetime", reverse=True)
    file_input.close()
    assert items[0]["Barometer"] == "31.838"
    assert items[0]["Datetime"] == "2012-06-08 16:40:00"


def test_csv_to_dict_empty_file():
    '''Tests csv to dict with empty file archives.'''
    path = os.path.join('pyvantagepro', 'tests', 'ressources', 'empty.csv')
    path = os.path.abspath(os.path.join('.', path))
    file_input = open(path, 'r')
    items = csv_to_dict(file_input)
    file_input.close()
    assert len(items) == 0


def test_dict():
    '''Tests DataDict.'''
    d = Dict()
    d["f"] = "222"
    d["a"] = "111"
    # sorteddict({'a': '111', 'f': '222'})
    assert d.keys().index('a') == 0
    assert d.keys().index('f') == 1
    d["b"] = "000"
    assert d.keys().index('a') == 0
    assert d.keys().index('b') == 1
    assert d.keys().index('f') == 2

    assert "a" in d.filter(['a', 'b'])
    assert "b" in d.filter(['a', 'b'])
    assert "f" not in d.filter(['a', 'b'])
    new_d = d.filter(['a', 'f'])
    assert "a,f\r\n111,222\r\n" == new_d.to_csv()


class TestCachedProperty:
    ''' Tests cached_property decorator.'''

    @cached_property
    def random_bool(self):
        '''Returns random bool'''
        return bool(random.getrandbits(1))

    def test_cached_property(self):
        '''Tests cached_property decorator.'''
        value1 = self.random_bool
        value2 = self.random_bool
        assert value1 == value2


class TestRetry:
    '''Test retry decorator.'''
    def setup_class(self):
        '''Setup common data.'''
        self.retries = 0

    @retry(tries=3, delay=0)
    def retries_func(self, num):
        '''Returns random bool.'''
        self.retries += 1
        if self.retries == num:
            return True
        else:
            return False

    def test_cached_property(self):
        '''Tests retry decorator.'''
        assert self.retries_func(3) is True
        self.retries = 0
        assert self.retries_func(5) is False


def test_bytes_to_hex():
    '''Tests byte <-> hex and hex <-> byte.'''
    assert bytes_to_hex(b"\xFF") == "FF"
    assert hex_to_bytes(bytes_to_hex(b"\x4A")) == b"\x4A"
    assert bytes_to_hex(hex_to_bytes("4A")) == "4A"


def test_bytes_binary():
    '''Tests byte <-> binary and binary <-> byte.'''
    assert bytes_to_binary(b'\xFF\x00') == "1111111100000000"
    assert bytes_to_binary(b'\x00\x00') == "0000000000000000"


def test_hex_binary():
    '''Tests hex <-> binary and binary <-> hex.'''
    assert hex_to_binary('FF00') == "1111111100000000"
    assert hex_to_binary('0000') == "0000000000000000"


def test_bin_integer():
    '''Tests bin <-> int conversion.'''
    hexstr = "11111110"
    assert binary_to_int(hexstr) == 254
    assert binary_to_int(hexstr, 0, 1) == 0
    assert binary_to_int(hexstr, 0, 2) == 2
    assert binary_to_int(hexstr, 0, 3) == 6
