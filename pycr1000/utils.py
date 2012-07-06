# -*- coding: utf-8 -*-
'''
    pycr1000.utils
    --------------

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import sys
import time
import csv
import binascii

from .compat import to_char, str, bytes, StringIO, is_py3


class Singleton(object):
    '''Signleton class , only one obejct of this type can be created
    any class derived from it will be Singleton.
    Stolen from:
    http://code.activestate.com/recipes/519627-singleton-base-class/'''
    __instance = None
    def __new__(typ, *args, **kwargs):
        if Singleton.__instance == None:
            obj = object.__new__(typ, *args, **kwargs)
            Singleton.__instance = obj

        return Singleton.__instance


def is_text(data):
    '''Check if data is text instance'''
    return isinstance(data, str)


def is_bytes(data):
    '''Check if data is bytes instance'''
    return isinstance(data, bytes)


class cached_property(object):
    '''A decorator that converts a function into a lazy property.  The
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
    '''

    def __init__(self, func, name=None, doc=None, writeable=False):
        if writeable:
            from warnings import warn
            warn(DeprecationWarning('the writeable argument to the '
                                    'cached property is a noop since 0.6 '
                                    'because the property is writeable '
                                    'by default for performance reasons'))

        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__)
        if value is None:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


class retry(object):
    '''Retries a function or method until it returns True value.
    delay sets the initial delay in seconds, and backoff sets the factor by
    which the delay should lengthen after each failure.
    Tries must be at least 0, and delay greater than 0.'''

    def __init__(self, tries=3, delay=1):
        self.tries = tries
        self.delay = delay

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            for i in range(self.tries - 1):
                try:
                    ret = f(*args, **kwargs)
                    if ret:
                        return ret
                    elif i == self.tries - 1:
                        return ret
                except Exception as e:
                    pass
                if self.delay > 0:
                    time.sleep(self.delay)
            ret = f(*args, **kwargs)
            if ret:
                return ret
            elif i == self.tries - 1:
                return ret
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__name__ = f.__name__
        wrapped_f.__module__ = f.__module__
        return wrapped_f


def bytes_to_hex(byte):
    '''Convert a bytearray to it's hex string representation.'''
    if sys.version_info[0] >= 3:
        hexstr = str(binascii.hexlify(byte), "utf-8")
    else:
        hexstr = str(binascii.hexlify(byte))
    data = []
    for i in range(0, len(hexstr), 2):
        data.append("%s" % hexstr[i:i + 2].upper())
    return ' '.join(data)


def hex_to_bytes(hexstr):
    '''Convert a string hex byte values into a byte string.'''
    return binascii.unhexlify(hexstr.replace(' ', '').encode('utf-8'))


def byte_to_binary(byte):
    '''Convert byte to binary string representation.
    E.g.
    >>> hex_to_binary_string("\x4A")
    '0000000001001010'
    '''
    return ''.join(str((byte & (1 << i)) and 1) for i in reversed(range(8)))


def bytes_to_binary(values):
    '''Convert bytes to binary string representation.
    E.g.
    >>> hex_to_binary_string(b"\x4A\xFF")
    '0100101011111111'
    '''
    if is_py3:
        # TODO: Python 3 convert \x00 to integer 0 ?
        if values == 0:
            data = '00000000'
        else:
            data = ''.join([byte_to_binary(b) for b in values])
    else:
        data = ''.join(byte_to_binary(ord(b)) for b in values)
    return data


def hex_to_binary(hexstr):
    '''Convert hexadecimal string to binary string representation.
    E.g.
    >>> hex_to_binary_string("FF")
    '11111111'
    '''
    if is_py3:
        return ''.join(byte_to_binary(b) for b in hex_to_bytes(hexstr))
    return ''.join(byte_to_binary(ord(b)) for b in hex_to_bytes(hexstr))


def binary_to_int(buf, start=0, stop=None):
    '''Convert binary string representation to integer.
    E.g.
    >>> binary_to_int('1111110')
    126
    >>> binary_to_int('1111110', 0, 2)
    2
    >>> binary_to_int('1111110', 0, 3)
    6
    '''
    return int(buf[::-1][start:(stop or len(buf))][::-1], 2)


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


class Dict(object):
    '''A sorted dict with somes additional methods.'''
    def __init__(self, initial_dict=None):
        initial_dict = initial_dict or {}
        self.store = dict(initial_dict)

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def copy(self):
        return Dict(self)

    def keys(self):
        return self.store.keys()

    def values(self):
        return self.store.values()

    def items(self):
        return self.store.items()

    def __contains__(self, key):
        return key in self.store.keys()

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def filter(self, keys):
        '''Create a dict with only the following `keys`.

        >>> mydict = Dict({"name":"foo", "firstname":"bar", "age":1})
        >>> mydict.filter(['age', 'name'])
        {'age': 1, 'name': 'foo'}
        '''
        data = self.store.copy()
        unused_keys = set(data.keys()) - set(keys)
        for key in unused_keys:
            del data[key]
        return Dict(data)

    def to_csv(self, delimiter=',', header=True):
        '''Serialize list of dictionaries to csv.'''
        return dict_to_csv([self.store], delimiter, header)

    def __str__(self):
        return "%s" % self.store.__str__()

    def __repr__(self):
        return self.store.__repr__()


class ListDict(list):
    '''List of sorteddicts with somes additional methods.'''

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
            data = item.copy()
            unused_keys = set(data.keys()) - set(keys)
            for key in unused_keys:
                del data[key]
            items.append(data)
        return items

    def sorted_by(self, keyword, reverse=False):
        '''Returns list sorted by `keyword`.'''
        return ListDict(sorted(self, key=lambda k: k[keyword],
                                     reverse=reverse))
