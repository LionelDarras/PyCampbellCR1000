# coding: utf8
'''
    PyCampbellCRX.tests.test_utils
    ------------------------------

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import random

from ..utils import (cached_property, Dict, hex_to_bytes, bytes_to_hex,
                     csv_to_dict)
from ..compat import StringIO, is_text, is_bytes


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


def test_dict():
    '''Tests DataDict.'''
    d = Dict()
    d["f"] = "222"
    d["a"] = "111"
    d["b"] = "000"
    assert "a" in d.filter(['a', 'b'])
    assert "b" in d.filter(['a', 'b'])
    assert "f" not in d.filter(['a', 'b'])
    assert "a,f\r\n111,222\r\n" == d.filter(['a', 'f']).to_csv()
    assert "f,b\r\n222,000\r\n" == d.filter(['f', 'b']).to_csv()


def test_ordered_dict():
    '''Tests DataDict.'''
    d = Dict()
    d["f"] = "222"
    d["a"] = "111"
    d["b"] = "000"
    assert "f,a,b\r\n222,111,000\r\n" == d.to_csv()


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


def test_bytes_to_hex():
    '''Tests byte <-> hex and hex <-> byte.'''
    assert bytes_to_hex(b"\xFF") == "FF"
    assert hex_to_bytes(bytes_to_hex(b"\x4A")) == b"\x4A"
    assert bytes_to_hex(hex_to_bytes("4A")) == "4A"
