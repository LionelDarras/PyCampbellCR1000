# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.exceptions
    ---------------------------

    Exceptions

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals


class NoDeviceException(Exception):
    '''Can not access to device.'''
    def __str__(self):
        return self.__doc__


class BadSignatureException(Exception):
    '''No valid signature.'''
    def __str__(self):
        return self.__doc__


class BadDataException(Exception):
    '''No valid data packet.'''
    def __str__(self):
        return self.__doc__


class DeliveryFailureException(Exception):
    '''Delivery failure.'''
    def __str__(self):
        return self.__doc__
