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
from .pakbus import PakBus

class CR1000(object):
    '''Communicates with the datalogger by sending commands, reads the binary
    data and parsing it into usable scalar values.

    :param url: A `PyLink` connection.
    '''

    def __init__(self, link):
        link.open()
        self.pakbus = PakBus(link)
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

    def gettime(self):
        pass
