# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.client
    -----------------------

    Allows data query of Campbell CR1000-type devices.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals
import time

from datetime import datetime, timedelta
from pylink import link_from_url

from .logger import LOGGER
from .pakbus import PakBus
from .exceptions import NoDeviceException
from .compat import xrange, is_py3
from .utils import cached_property, ListDict, Dict, nsec_to_time, time_to_nsec, bytes_to_hex


class CR1000(object):
    '''Communicates with the datalogger by sending commands, reads the binary
    data and parses it into usable scalar values.

    :param link: A `PyLink` connection.
    :param dest_addr: Destination physical address (12-bit int) (default dest)
    :param dest: Destination node ID (12-bit int) (default 0x001)
    :param src_addr: Source physical address (12-bit int) (default src)
    :param src: Source node ID (12-bit int) (default 0x802)
    :param security_code: 16-bit security code (default 0x0000)
    '''
    connected = False

    def __init__(self, link, dest_addr=None, dest=0x001, src_addr=None,
                 src=0x802, security_code=0x0000):
        link.open()
        LOGGER.info("init client")
        self.pakbus = PakBus(link, dest_addr, dest, src_addr, src, security_code)
        self.pakbus.wait_packet()
        # try ping the datalogger
        for i in xrange(20):
            LOGGER.info('%d'%(i))
            try:
                if self.ping_node():
                    self.connected = True
                    break
            except NoDeviceException:
                self.pakbus.link.close()
                self.pakbus.link.open()
        if not self.connected:
            raise NoDeviceException()

    @classmethod
    def from_url(cls, url, timeout=10, dest_addr=None, dest=0x001,
                 src_addr=None, src=0x802, security_code=0x0000):
        ''' Get device from url.

        :param url: A `PyLink` connection URL.
        :param timeout: Set a read timeout value.
        :param dest_addr: Destination physical address (12-bit int) (default dest)
        :param dest: Destination node ID (12-bit int) (default 0x001)
        :param src_addr: Source physical address (12-bit int) (default src)
        :param src: Source node ID (12-bit int) (default 0x802)
        :param security_code: 16-bit security code (default 0x0000)
        '''
        link = link_from_url(url)
        link.settimeout(timeout)
        return cls(link, dest_addr, dest, src_addr, src, security_code)     #EGC Add security code to the constructor call

    def send_wait(self, cmd):
        '''Send command and wait for response packet.'''
        packet, transac_id = cmd
        begin = time.time()
        self.pakbus.write(packet)
        # wait response packet
        response = self.pakbus.wait_packet(transac_id)
        end = time.time()
        send_time = timedelta(seconds=int((end - begin) / 2))
        return response[0], response[1], send_time

    def ping_node(self):
        '''Check if remote host is available.'''
        # send hello command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_hello_cmd())
        if not (hdr and msg):
            raise NoDeviceException()
        return True

    def gettime(self):
        '''Return the current datetime.'''
        self.ping_node()
        LOGGER.info('Try gettime')
        # send clock command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_clock_cmd())
        # remove transmission time
        return nsec_to_time(msg['Time']) - send_time

    def settime(self, dtime):
        '''Sets the given `dtime` and returns the new current datetime'''
        LOGGER.info('Try settime')
        current_time = self.gettime()
        self.ping_node()
        diff = dtime - current_time
        diff = diff.total_seconds()
        # settime (OldTime in response)
        hdr, msg, sdt1 = self.send_wait(self.pakbus.get_clock_cmd((diff, 0)))
        # gettime (NewTime in response)
        hdr, msg, sdt2 = self.send_wait(self.pakbus.get_clock_cmd())
        # remove transmission time

        return nsec_to_time(msg['Time']) - (sdt1 + sdt2)

    @cached_property
    def settings(self):
        '''Get device settings as ListDict'''
        LOGGER.info('Try get settings')
        self.ping_node()
        # send getsettings command and wait for response packet
        hdr, msg, send_time = self.send_wait(self.pakbus.get_getsettings_cmd())
        # remove transmission time
        settings = ListDict()
        for item in msg["Settings"]:
            settings.append(Dict(dict(item)))
        return settings

    def getfile(self, filename):
        '''Get the file content from the datalogger.'''
        LOGGER.info('Try get file')
        self.ping_node()
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

    def sendfile(self, data, filename):
        '''Upload a file to the datalogger.'''
        LOGGER.info('Try send file')
        raise NotImplementedError('Filedownload transaction is not implemented'
                                  ' yet')

    def list_files(self):
        '''List the files available in the datalogger.'''
        data = self.getfile('.DIR')
        # List files in directory
        filedir = self.pakbus.parse_filedir(data)
        return [item['FileName'] for item in filedir['files']]

    @cached_property
    def table_def(self):
        '''Return table definition.'''
        data = self.getfile('.TDF')
        # List tables
        tabledef = self.pakbus.parse_tabledef(data)
        return tabledef

    def list_tables(self):
        '''List the tables available in the datalogger.'''
        return [item['Header']['TableName'] for item in self.table_def]

    def _collect_data(self, tablename, start_date=None, stop_date=None):
        '''Collect fragment data from `tablename` from `start_date` to
        `stop_date` as ListDict.'''
        LOGGER.info('Send collect_data cmd')
        if start_date is not None:
            mode = 0x07  # collect from p1 to p2 (nsec)
            p1 = time_to_nsec(start_date)
            p2 = time_to_nsec(stop_date or datetime.now())
        else:
            mode = 0x03  # collect all
            p1 = 0
            p2 = 0

        tabledef = self.table_def
        # Get table number
        tablenbr = None
        if is_py3:
            tablename = bytes(tablename, encoding="utf-8")
        for i, item in enumerate(tabledef):
            if item['Header']['TableName'] == tablename:
                tablenbr = i + 1
                break
        if tablenbr is None:
            raise StandardError('table %s not found' % tablename)
        # Get table definition signature
        tabledefsig = tabledef[tablenbr - 1]['Signature']

        # Send collect data request
        cmd = self.pakbus.get_collectdata_cmd(tablenbr, tabledefsig, mode,
                                              p1, p2)
        hdr, msg, send_time = self.send_wait(cmd)
        more = True
        data, more = self.pakbus.parse_collectdata(msg['RecData'], tabledef)
        # Return parsed record data and flag if more records exist
        return data, more

    def get_data(self, tablename, start_date=None, stop_date=None):
        '''Get all data from `tablename` from `start_date` to `stop_date` as
        ListDict. By default the entire contents of the data will be
        downloaded.

        :param tablename: Table name that contains the data.
        :param start_date: The beginning datetime record.
        :param stop_date: The stopping datetime record.'''
        records = ListDict()
        for items in self.get_data_generator(tablename, start_date, stop_date):
            records.extend(items)
        return records

    def get_data_generator(self, tablename, start_date=None, stop_date=None):
        '''Get all data from `tablename` from `start_date` to `stop_date` as
        generator. The data can be fragmented into multiple packets, this
        generator can return parsed data from each packet before receiving
        the next one.

        :param tablename: Table name that contains the data.
        :param start_date: The beginning datetime record.
        :param stop_date: The stopping datetime record.
        '''
        self.ping_node()
        start_date = start_date or datetime(1990, 1, 1, 0, 0, 1)
        stop_date = stop_date or datetime.now()
        more = True
        while more:
            records = ListDict()
            data, more = self._collect_data(tablename, start_date, stop_date)
            for i, rec in enumerate(data):
                if not rec["NbrOfRecs"]:
                    more = False
                    break
                for j, item in enumerate(rec['RecFrag']):
                    if start_date <= item['TimeOfRec'] <= stop_date:
                        start_date = item['TimeOfRec']
                        # for no duplicate record
                        if more and ((j == (len(rec['RecFrag']) - 1))
                                     and (i == (len(data) - 1))):
                            break
                        new_rec = Dict()
                        new_rec["Datetime"] = item['TimeOfRec']
                        new_rec["RecNbr"] = item['RecNbr']
                        for key in item['Fields']:
                            new_rec["%s" % key] = item['Fields'][key]
                        records.append(new_rec)

            if records:
                records = records.sorted_by('Datetime')
                yield records.sorted_by('Datetime')
            else:
                more = False

    def get_raw_packets(self, tablename):
        '''Get all raw packets from table `tablename`.

        :param tablename: Table name that contains the data.
        '''
        self.ping_node()
        more = True
        records = ListDict()
        while more:
            packets, more = self._collect_data(tablename)
            for rec in packets:
                records.append(rec)
        return records

    def getprogstat(self):
        '''Get programming statistics as dict.'''
        LOGGER.info('Try get programming statistics')
        self.ping_node()
        hdr, msg, send_time = self.send_wait(self.pakbus.get_getprogstat_cmd())
        # remove transmission time
        data = Dict(dict(msg['Stats']))
        if data:
            data['CompTime'] = nsec_to_time(data['CompTime'])
        return data

    def bye(self):
        '''Send a bye command.'''
        LOGGER.info("Send bye command")
        if self.connected:
            packet, transac_id = self.pakbus.get_bye_cmd()
            self.pakbus.write(packet)
            self.connected = False

    def __del__(self):
        '''Send bye cmd when object is deleted.'''
        self.bye()
