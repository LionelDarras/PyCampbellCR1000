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
import calendar

from datetime import datetime

from .logger import LOGGER
from .pakbus import PakBus

class CR1000(object):
    '''Communicates with the datalogger by sending commands, reads the binary
    data and parsing it into usable scalar values.

    :param url: A `PyLink` connection.
    '''

    def __init__(self, link, dest_node=0x001, src_node=0x802):
        link.open()
        self.pakbus = PakBus(link, dest_node, src_node)
        self.nsec_base = calendar.timegm((1990, 1, 1, 0, 0, 0))
        self.nsec_tick = 1E-9
        LOGGER.info("init CR1000")

    @classmethod
    def from_url(cls, url, timeout=10, dest_node=0x001, src_node=0x802):
        ''' Get device from url.

        :param url: A `PyLink` connection URL.
        :param timeout: Set a read timeout value.
        '''
        link = link_from_url(url)
        link.settimeout(timeout)
        return cls(link, dest_node, src_node)

    def ping_node(self):
        '''Check if remote host is available.'''
        # send hello command and wait for response packet
        packet, transac_id = self.get_hello_cmd()
        self.pakbus.write(packet)
        # wait response packet
        hdr, msg = self.pakbus.wait_packet(transac_id)
        return msg

    def gettime(self):
        packet, transac_id = self.get_clock_cmd()
        self.pakbus.write(packet)
        # wait response packet
        hdr, msg = self.pakbus.wait_packet(transac_id)
        # Calculate timestamp with fractional seconds
        timestamp = self.nsec_base + msg['Time'][0]
        timestamp += msg['Time'][1] * self.nsec_tick
        return datetime.fromtimestamp(timestamp)
