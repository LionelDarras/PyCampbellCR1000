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
import time

from datetime import datetime, timedelta
from pylink import link_from_url

from .logger import LOGGER
from .pakbus import PakBus
from .exceptions import NoDeviceException
from .compat import xrange
from .utils import cached_property, ListDict, Dict


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
            except NoDeviceException:
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
        begin = time.time()
        packet = cmd[0]
        transac_id = cmd[1]
        self.pakbus.write(packet)
        # wait response packet
        response = self.pakbus.wait_packet(transac_id)
        end = time.time()
        send_time = timedelta(seconds=((begin - end) / 2))
        return response[0], response[1], send_time

    def ping_node(self):
        '''Check if remote host is available.'''
        # send hello command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_hello_cmd())
        if not (hdr and msg):
            raise NoDeviceException()
        self.connected = True
        return self.connected

    def nsec_to_time(self, nsec, send_time=0):
        '''Calculate datetime with fractional seconds.'''
        timestamp = self.nsec_base + nsec[0]
        timestamp += nsec[1] * self.nsec_tick
        device_time = datetime.fromtimestamp(timestamp) - send_time
        return device_time.replace(microsecond=0)

    def gettime(self):
        '''Returns the current datetime.'''
        LOGGER.info('Try gettime')
        # send clock command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_clock_cmd())
        # remove transmission time
        return self.nsec_to_time(msg['Time'], send_time)

    def settime(self, dtime):
        '''Set the given `dtime` and return the new current datetime'''
        LOGGER.info('Try settime')
        current_time = self.gettime()
        diff = dtime - current_time
        diff = diff.days * 86400 + diff.seconds
        # settime (OldTime in response)
        hdr, msg, sdt1 = self.send_wait(self.pakbus.get_clock_cmd((diff, 0)))
        # gettime (NewTime in response)
        hdr, msg, sdt2 = self.send_wait(self.pakbus.get_clock_cmd())
        # remove transmission time
        return self.nsec_to_time(msg['Time'], sdt1 + sdt2)

    @cached_property
    def settings(self):
        '''Get device settings as dict'''
        LOGGER.info('Try get settings')
        # send getsettings command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_getsettings_cmd())
        # remove transmission time
        settings = ListDict()
        for item in msg["Settings"]:
            settings.append(Dict(dict(item)))
        return settings

    def getfile(self, filename):
        '''Get a complete file from CR1000 datalogger.'''
        LOGGER.info('Try get file')
        data = []
        # Send file upload command packets until no more data is returned
        offset = 0x00000000
        transac_id = None
        while True:
            # Upload chunk from file starting at offset
            cmd = self.pakbus.get_fileupload_cmd(filename,
                                                 offset=offset,
                                                 closeflag=0x00,
                                                 transac_id=transac_id)
            transac_id = cmd[1]
            hdr, msg, send_time = self.send_wait(cmd)
            try:
                if msg['RespCode'] == 1:
                    raise ValueError("Permission denied")
                # End loop if no more data is returned
                if not msg['FileData']:
                    break
                # Append file data
                data.append(msg['FileData'])
                offset += len(msg['FileData'])
            except KeyError:
                break

        return b"".join(data)

    def list_files(self):
        data = self.getfile('.DIR')
        # List files in directory
        filedir = self.pakbus.parse_filedir(data)
        return filedir['files']

    def get_table_def(self):
        data = self.getfile('.TDF')
        # List tables
        return self.pakbus.parse_tabledef(data)

    def list_tables(self):
        names = []
        for item in self.get_table_def():
            names.append(item['Header']['TableName'])
        return names

    def collect_data(self, tablename, mode=0x05):
        '''Collect data.'''
        tabledef = self.get_table_def()
        # Get table number
        tablenbr = None
        for i, item in enumerate(tabledef):
            if item['Header']['TableName'] == tablename:
                tablenbr = i + 1
                break
        if tablenbr is None:
            raise StandardError('table %s not found' % tablename)
        # Get table definition signature
        tabledefsig = tabledef[tablenbr - 1]['Signature']

        # Send collect data request
        cmd = self.pakbus.get_collectdata_cmd(tablenbr, tabledefsig, mode)
        hdr, msg, send_time = self.send_wait(cmd)
        data, more = self.pakbus.parse_collectdata(msg['RecData'], tabledef)
        if more:
            # TODO: get this data ?
            pass
        # Return parsed record data and flag if more records exist
        return data

    def getprogstat(self):
        '''Get Programming Statistics.'''
        LOGGER.info('Try get settings')
        hdr, msg, send_time = self.send_wait(self.pakbus.get_getprogstat_cmd())
        # remove transmission time
        return Dict(dict(msg['Stats']))

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
