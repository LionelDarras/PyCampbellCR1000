# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.utils
    -------------------

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import math
import time
import calendar
import csv
import binascii

from datetime import datetime

from .compat import to_char, str, StringIO, is_py3, OrderedDict


class Singleton(object):
    '''Signleton class , only one obejct of this type can be created
    any class derived from it will be Singleton.
    Stolen from:
    http://code.activestate.com/recipes/519627-singleton-base-class/'''
    __instance = None

    def __new__(typ, *args, **kwargs):
        if Singleton.__instance is None:
            obj = object.__new__(typ, *args, **kwargs)
            Singleton.__instance = obj

        return Singleton.__instance


class cached_property(object):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.
    Stolen from:
    https://raw.github.com/mitsuhiko/werkzeug/master/werkzeug/utils.py
    """

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        value = obj.__dict__.get(self.__name__)
        if value is None:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


def nsec_to_time(nsec):
    '''Convert nsec to datetime.'''
    nsec_base = calendar.timegm((1990, 1, 1, 0, 0, 0))
    nsec_tick = 1E-9
    timestamp = nsec_base + nsec[0]
    timestamp += nsec[1] * nsec_tick
    return datetime.fromtimestamp(timestamp).replace(microsecond=0)


def time_to_nsec(dtime):
    '''Convert timestamp to nsec value.'''
    nsec_base = calendar.timegm((1990, 1, 1, 0, 0, 0))
    nsec_tick = 1E-9
    timestamp = time.mktime(dtime.timetuple())
    # separate fractional and integer part of timestamp
    (fp, ip) = math.modf(timestamp)
    # Calculate two integer values for NSec
    nsec = (int(ip - nsec_base), int(fp / nsec_tick))
    return nsec


def bytes_to_hex(byte):
    '''Convert a bytearray to it's hex string representation.'''
    if is_py3:
        hexstr = binascii.hexlify(byte).decode("utf-8")
    else:
        hexstr = str(binascii.hexlify(byte))
    data = []
    for i in range(0, len(hexstr), 2):
        data.append("%s" % hexstr[i:i + 2].upper())
    return ' '.join(data)


def hex_to_bytes(hexstr):
    '''Convert a string hex byte values into a byte string.'''
    return binascii.unhexlify(hexstr.replace(' ', '').encode('utf-8'))


def csv_to_dict(file_input, delimiter=','):
    '''Deserialize csv to list of dictionaries.'''
    delimiter = to_char(delimiter)
    table = []
    reader = csv.DictReader(file_input, delimiter=delimiter,
                            skipinitialspace=True)
    for d in reader:
        table.append(d)
    return ListDict(table)


def dict_to_csv(items, delimiter, header):
    '''Serialize list of dictionaries to csv.'''
    content = ""
    if len(items) > 0:
        delimiter = to_char(delimiter)
        output = StringIO()
        csvwriter = csv.DictWriter(output, fieldnames=items[0].keys(),
                                   delimiter=delimiter)
        if header:
            csvwriter.writerow(dict((key, key) for key in items[0].keys()))
            # writeheader is not supported in python2.6
            # csvwriter.writeheader()
        for item in items:
            csvwriter.writerow(dict(item))

        content = output.getvalue()
        output.close()
    return content


class Dict(OrderedDict):
    '''A dict with somes additional methods.'''

    def filter(self, keys):
        '''Create a dict with only the following `keys`.

        >>> mydict = Dict({"name":"foo", "firstname":"bar", "age":1})
        >>> mydict.filter(['age', 'name'])
        {'age': 1, 'name': 'foo'}
        '''
        data = Dict()
        real_keys = set(self.keys()) - set(set(self.keys()) - set(keys))
        for key in keys:
            if key in real_keys:
                data[key] = self[key]
        return data

    def to_csv(self, delimiter=',', header=True):
        '''Serialize list of dictionaries to csv.'''
        return dict_to_csv([self], delimiter, header)


class ListDict(list):
    '''List of dicts with somes additional methods.'''

    def to_csv(self, delimiter=',', header=True):
        '''Serialize list of dictionaries to csv.'''
        return dict_to_csv(list(self), delimiter, header)

    def filter(self, keys):
        '''Create a list of dictionaries with only the following `keys`.

        >>> mylist = ListDict([{"name":"foo", "age":31},
        ...                    {"name":"bar", "age":24}])
        >>> mylist.filter(['name'])
        [{'name': 'foo'}, {'name': 'bar'}]
        '''
        items = ListDict()
        for item in self:
            items.append(item.filter(keys))
        return items

    def sorted_by(self, keyword, reverse=False):
        '''Returns list sorted by `keyword`.'''
        key_ = keyword
        return ListDict(sorted(self, key=lambda k: k[key_], reverse=reverse))
