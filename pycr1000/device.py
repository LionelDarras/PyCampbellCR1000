# -*- coding: utf-8 -*-
'''
    pycr1000.device
    ---------------

    Allows data query of CR1000 device

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals

from pylink import link_from_url

from .logger import LOGGER


class NoDeviceException(Exception):
    '''Can not access to device.'''
    value = __doc__


class BadAckException(Exception):
    '''No valid acknowledgement.'''
    def __str__(self):
        return self.__doc__


class BadCRCException(Exception):
    '''No valid checksum.'''
    def __str__(self):
        return self.__doc__


class BadDataException(Exception):
    '''No valid data.'''
    def __str__(self):
        return self.__doc__


class CR1000(object):
    '''Communicates with the datalogger by sending commands, reads the binary
    data and parsing it into usable scalar values.

    :param url: A `PyLink` connection URL.
    '''

    def __init__(self, url):
        self.link = link_from_url(url)
        self.link.open()
        LOGGER.info("init CR1000")

    @classmethod
    def from_url(cls, url, timeout=10):
        ''' Get device from url.

        :param url: A `PyLink` connection URL.
        :param timeout: Set a read timeout value.
        '''
        link = link_from_url(url)
        link.settimeout(timeout)
        return cls(link)
