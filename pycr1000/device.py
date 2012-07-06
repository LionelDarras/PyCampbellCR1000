# -*- coding: utf-8 -*-
'''
    pycr1000.device
    ---------------

    Allows data query of CR1000 device

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals
import calendar

from datetime import datetime
from pylink import link_from_url

from .logger import LOGGER
from .pakbus import PakBus
from .exceptions import NoDeviceException
from .utils import retry

class CR1000(object):
    '''Communicates with the datalogger by sending commands, reads the binary
    data and parsing it into usable scalar values.

    :param link: A `PyLink` connection.
    :parm dest_node: Destination node ID (12-bit int)
    :parm src_node: Source node ID (12-bit int)
    :parm security_code: 16-bit security code (optional)
    '''
    nsec_base = calendar.timegm((1990, 1, 1, 0, 0, 0))
    nsec_tick = 1E-9
    connected = False

    def __init__(self, link, dest_node=0x001, src_node=0x802,
                 security_code=0x0000):
        link.open()
        LOGGER.info("init CR1000")
        self.pakbus = PakBus(link, dest_node, src_node, security_code)
        for i in xrange(3):
            try:
                if self.ping_node():
                    self.connected = True
            except:
                self.pakbus.link.close()
                self.pakbus.link.open()

        if not self.connected:
            raise NoDeviceException()

    @classmethod
    def from_url(cls, url, timeout=10, dest_node=0x001, src_node=0x802,
                 security_code=0x0000):
        ''' Get device from url.

        :param url: A `PyLink` connection URL.
        :param timeout: Set a read timeout value.
        '''
        link = link_from_url(url)
        link.settimeout(timeout)
        return cls(link, dest_node, src_node)

    def send_wait(self, cmd):
        '''Send command and wait for response packet.'''
        packet = cmd[0]
        transac_id = cmd[1]
        self.pakbus.write(packet)
        # wait response packet
        return self.pakbus.wait_packet(transac_id)

    def ping_node(self):
        '''Check if remote host is available.'''
        # send hello command and wait for response packet
        hdr, msg = self.send_wait(self.pakbus.get_hello_cmd())
        if not (hdr and msg):
            raise NoDeviceException()
        self.connected = True
        return self.connected

    def nsec_to_time(self, nsec):
        '''Calculate datetime with fractional seconds.'''
        timestamp = self.nsec_base + nsec[0]
        timestamp += nsec[1] * self.nsec_tick
        return datetime.fromtimestamp(timestamp).replace(microsecond=0)

    def gettime(self):
        '''Returns the current datetime.'''
        LOGGER.info('Try gettime')
        # send clock command and wait for response packet
        hdr, msg = self.send_wait(self.pakbus.get_clock_cmd())
        return self.nsec_to_time(msg['Time'])

    def settime(self, dtime):
        '''Set the given `dtime` and return the new current datetime'''
        LOGGER.info('Try settime')
        current_time = self.gettime()
        diff = dtime - current_time
        diff = diff.days * 86400 + diff.seconds
        hdr, msg = self.send_wait(self.pakbus.get_clock_cmd((diff, 0)))
        return self.nsec_to_time(msg['Time'])

    def bye(self):
        '''Send bye command.'''
        LOGGER.info("Send bye command")
        if self.connected:
            packet, transac_id = self.pakbus.get_bye_cmd()
            self.pakbus.write(packet)
            self.connected = False

    def __del__(self):
        '''Send bye cmd when object is deleted.'''
        self.bye()
