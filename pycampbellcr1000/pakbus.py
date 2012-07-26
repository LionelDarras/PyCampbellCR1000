# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.pakbus
    -----------------------

    PakBus protocol Implementation.

    Original Author: Dietrich Feist, Max Planck Institute for Biogeochemistry,
                     Jena Germany (PyPak)
    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals

import struct
import time

from .compat import ord, chr, is_text, is_py3, bytes
from .logger import LOGGER
from .utils import Singleton
from .exceptions import DeliveryFailureException
from .utils import bytes_to_hex, nsec_to_time


class Transaction(Singleton):
    id = 0

    def next_id(self):
        self.id += 1
        self.id &= 0xFF
        return self.id


class PakBus(object):
    '''Inteface for a pakbus client.

    :param link: A `PyLink` connection.
    :param dest_node: Destination node ID (12-bit int) (default 0x001)
    :param src_node: Source node ID (12-bit int) (default 0x802)
    :param security_code: 16-bit security code (default 0x0000)
    '''

    DATATYPE = {
        'Byte':     {'code':  1, 'fmt': 'B',   'size': 1},
        'UInt2':    {'code':  2, 'fmt': '>H',  'size': 2},
        'UInt4':    {'code':  3, 'fmt': '>L',  'size': 4},
        'Int1':     {'code':  4, 'fmt': 'b',   'size': 1},
        'Int2':     {'code':  5, 'fmt': '>h',  'size': 2},
        'Int4':     {'code':  6, 'fmt': '>l',  'size': 4},
        'FP2':      {'code':  7, 'fmt': '>H',  'size': 2},
        'FP3':      {'code': 15, 'fmt': '3c',  'size': 3},
        'FP4':      {'code':  8, 'fmt': '4c',  'size': 4},
        'IEEE4B':   {'code':  9, 'fmt': '>f',  'size': 4},
        'IEEE8B':   {'code': 18, 'fmt': '>d',  'size': 8},
        'Bool8':    {'code': 17, 'fmt': 'B',   'size': 1},
        'Bool':     {'code': 10, 'fmt': 'B',   'size': 1},
        'Bool2':    {'code': 27, 'fmt': '>H',  'size': 2},
        'Bool4':    {'code': 28, 'fmt': '>L',  'size': 4},
        'Sec':      {'code': 12, 'fmt': '>l',  'size': 4},
        'USec':     {'code': 13, 'fmt': '6c',  'size': 6},
        'NSec':     {'code': 14, 'fmt': '>2l', 'size': 8},
        'ASCII':    {'code': 11, 'fmt': 's',   'size': None},
        'ASCIIZ':   {'code': 16, 'fmt': 's',   'size': None},
        'Short':    {'code': 19, 'fmt': '<h',  'size': 2},
        'Long':     {'code': 20, 'fmt': '<l',  'size': 4},
        'UShort':   {'code': 21, 'fmt': '<H',  'size': 2},
        'ULong':    {'code': 22, 'fmt': '<L',  'size': 4},
        'IEEE4L':   {'code': 24, 'fmt': '<f',  'size': 4},
        'IEEE8L':   {'code': 25, 'fmt': '<d',  'size': 8},
        'SecNano':  {'code': 23, 'fmt': '<2l', 'size': 8},
    }

    # link state
    RING = 0x9
    READY = 0xA
    FINISHED = 0xB

    def __init__(self, link, dest_node=0x001, src_node=0x802,
                 security_code=0x0000):
        self.link = link
        self.src_node = src_node
        self.dest_node = dest_node
        self.security_code = security_code
        self.transaction = Transaction()
        LOGGER.info('Get the node attention')
        self.link.write(b'\xBD\xBD\xBD\xBD\xBD\xBD')

    def write(self, packet):
        '''Send packet over PakBus.'''
        LOGGER.info('Packet data: %s' % bytes_to_hex(packet))
        LOGGER.info('Calculate signature for packet')
        sign = self.compute_signature(packet)
        LOGGER.info('Calculate signature nullifier to create packet')
        nullifier = self.compute_signature_nullifier(sign)
        frame = self.quote(b''.join((packet, nullifier)))
        packet = b''.join((b'\xBD', frame, b'\xBD'))
        LOGGER.info('Write: %s' % bytes_to_hex(packet))
        self.link.write(packet)

    def read(self):
        '''Receive packet over PakBus.'''
        all_bytes = []
        byte = None
        begin = time.time()
        while byte != b'\xBD':
            if time.time() - begin > self.link.timeout:
                return None
            # Read until first \xBD frame character
            byte = self._read_one_byte()
        while byte == b'\xBD':
            # Read unitl first character other than \xBD
            byte = self._read_one_byte()
        while byte != b'\xBD':
            # Read until next occurence of \xBD character
            all_bytes.append(byte)
            byte = self._read_one_byte()

        # Unquote quoted characters
        packet = b''.join(all_bytes)
        LOGGER.info('Read packet: %s' % bytes_to_hex(packet))
        packet = self.unquote(packet)

        # Calculate signature (should be zero)
        if self.compute_signature(packet):
            LOGGER.error('Check signature : Error')
            return None
        else:
            LOGGER.info('Check signature : OK')
            # Strip last 2 signature bytes and return packet
            return packet[:-2]

    def _read_one_byte(self):
        '''Read only one byte.'''
        data = self.link.read(1)
        if is_text(data):
            return bytes(data.encode('utf-8'))
        else:
            return data

    def wait_packet(self, transac_id):
        '''Wait for an incoming packet.

        :param transac_id: Expected transaction number.
        '''

        LOGGER.info('Wait packet with transaction %s' % transac_id)
        data = self.read()
        if data is None or data == b'':
            return {}, {}

        hdr, msg = self.decode_packet(data)
        if hdr == {} or msg == {}:
            return hdr, msg

        # ignore packets that are not for us
        if (hdr['DstNodeId'] != self.src_node) or \
           (hdr['SrcNodeId'] != self.dest_node):
            return {}, {}

        # Respond to incoming hello command packets
        if msg['MsgType'] == 0x09:
            pkt = self.get_hello_response(hdr['SrcNodeId'], hdr['DstNodeId'],
                                          msg['TranNbr'])
            self.write(pkt)
            return self.wait_packet(transac_id)

        # Handle 'please wait' packets
        if msg['TranNbr'] == transac_id and msg['MsgType'] == 0xa1:
            timewait = msg['WaitSec']
            LOGGER.info('Please Wait Message packet <%s sec>' % timewait)
            time.sleep(timewait)
            return self.wait_packet(transac_id)

        # Handle failure message packets and raise exception
        if msg['MsgType'] == 0x81:
            raise DeliveryFailureException()

        # This should be the packet we are waiting for
        if msg['TranNbr'] == transac_id:
            return hdr, msg

    def pack_header(self, hi_proto, exp_more=0x2, link_state=None,
                    hops=0x0):
        '''Generate PakBus header.

        :param hi_proto: Higher level protocol code (4 bits). 0x0: PakCtrl,
                         0x1: BMP5
        :param exp_more: Whether client should expect another packet (2 bits)
        :param link_state: Link state (4 bits)
        :param hops: Number of hops to destination (4 bits)
        '''
        LOGGER.info('Create header')
        priority = 0x1
        link_state = link_state or self.READY
        # bitwise encoding of header fields
        hdr = struct.pack(str('>4H'),
                          (link_state & 0xF) << 12 | (self.dest_node & 0xFFF),
                          (exp_more & 0x3) << 14 | (priority & 0x3) << 12
                                                 | (self.src_node & 0xFFF),
                          (hi_proto & 0xF) << 12 | (self.dest_node & 0xFFF),
                          (hops & 0xF) << 12 | (self.src_node & 0xFFF))
        return hdr

    def compute_signature(self, buff, seed=0xAAAA):
        '''Compute signature for PakBus packets.'''
        sig = seed
        for x in buff:
            x = ord(x)
            j = sig
            sig = (sig << 1) & 0x1FF
            if sig >= 0x100:
                sig += 1
            sig = ((((sig + (j >> 8) + x) & 0xFF) | (j << 8))) & 0xFFFF
        return sig

    def compute_signature_nullifier(self, sig):
        '''Compute signature nullifier needed to create valid PakBus
        packets.'''
        nulb = nullif = b''
        for i in (1, 2):
            sig = self.compute_signature(nulb, sig)
            sig2 = (sig << 1) & 0x1FF
            if sig2 >= 0x100:
                sig2 += 1
            nulb = chr((0x100 - (sig2 + (sig >> 8))) & 0xFF)
            nullif += nulb
        return nullif

    def quote(self, packet):
        '''Quote the PakBus packet.'''
        LOGGER.info('Quote packet')
        packet = packet.replace(b'\xBC', b'\xBC\xDC')
        packet = packet.replace(b'\xBD', b'\xBC\xDD')
        return packet

    def unquote(self, packet):
        '''Unquote the PakBus packet.'''
        LOGGER.info('Unquote packet')
        packet = packet.replace(b'\xBC\xDD', b'\xBD')
        packet = packet.replace(b'\xBC\xDC', b'\xBC')
        return packet

    def encode_bin(self, types, values):
        '''Encode binary data according to data type.'''
        buff = []  # buffer for binary data
        for i, type_ in enumerate(types):
            fmt = self.DATATYPE[type_]['fmt']  # get default format for type_
            value = values[i]

            if type_ == 'ASCIIZ':
                # special handling: nul-terminated string
                value += '\0'
                # Add nul to end of string
                fmt_ = str('%d%s' % (len(value), fmt))
                if is_py3:
                    enc = struct.pack(fmt_, bytes(value, encoding='utf8'))
                else:
                    enc = struct.pack(fmt_, str(value))
            elif type_ == 'ASCII':
                # special handling: fixed-length string
                fmt_ = str('%d%s' % (len(value), fmt))
                enc = struct.pack(fmt_, str(value))
            elif type_ == 'NSec':
                # special handling: NSec time
                enc = struct.pack(str(fmt), value[0], value[1])
            else:
                # default encoding scheme
                enc = struct.pack(str(fmt), value)

            buff.append(enc)
        return b''.join(buff)

    def decode_bin(self, types, buff, length=1):
        '''Decode binary data according to data type.'''
        offset = 0  # offset into buffer
        values = []  # list of values to return
        for type_ in types:
            # get default format and size for Type
            fmt = self.DATATYPE[type_]['fmt']
            size = self.DATATYPE[type_]['size']

            if type_ == 'ASCIIZ':
                # special handling: nul-terminated string
                nul = buff.index(b'\0', offset)
                # find first '\0' after offset
                if nul == -1:
                    value = buff[offset:]
                else:
                    value = buff[offset:nul]
                # return string without trailing '\0'
                size = len(value) + 1
            elif type_ == 'ASCII':
                # special handling: fixed-length string
                size = length
                value = buff[offset:offset + size]
                # return fixed-length string
            elif type_ == 'FP2':
                # special handling: FP2 floating point number
                fp2 = struct.unpack(str(fmt), buff[offset:offset + size])
                mant = fp2[0] & 0x1FFF    # mantissa is in bits 1-13
                exp = fp2[0] >> 13 & 0x3  # exponent is in bits 14-15
                sign = fp2[0] >> 15       # sign is in bit 16
                value = ((-1) ** sign * float(mant) / 10 ** exp, )
            else:
                # default decoding scheme
                if buff[offset:offset + size]:
                    value = struct.unpack(str(fmt), buff[offset:offset + size])
                else:
                    value = ''

            # un-tuple single values
            if len(value) == 1:
                value = value[0]

            values.append(value)
            offset += size
        # Return decoded values and current offset into buffer (size)
        return values, offset

    def decode_packet(self, data):
        '''Decode packet from raw data.'''
        LOGGER.info('Decode packet')
        # pkt: buffer containing unquoted packet, signature nullifier stripped
        # Initialize output variables
        hdr = {'LinkState': None, 'DstPhyAddr': None, 'ExpMoreCode': None,
               'Priority': None, 'SrcPhyAddr': None, 'HiProtoCode': None,
               'DstNodeId': None, 'HopCnt': None, 'SrcNodeId': None}
        msg = {'MsgType': None, 'TranNbr': None, 'raw': None}

        # decode PakBus header
        rawhdr = struct.unpack(str('>4H'), data[0:8])  # raw header bits
        hdr['LinkState'] = rawhdr[0] >> 12
        hdr['DstPhyAddr'] = rawhdr[0] & 0x0FFF
        hdr['ExpMoreCode'] = (rawhdr[1] & 0xC000) >> 14
        hdr['Priority'] = (rawhdr[1] & 0x3000) >> 12
        hdr['SrcPhyAddr'] = rawhdr[1] & 0x0FFF
        hdr['HiProtoCode'] = rawhdr[2] >> 12
        hdr['DstNodeId'] = rawhdr[2] & 0x0FFF
        hdr['HopCnt'] = rawhdr[3] >> 12
        hdr['SrcNodeId'] = rawhdr[3] & 0x0FFF

        # decode default message fields:
        # raw message, message type and transaction number
        msg['raw'] = data[8:]
        values, size = self.decode_bin(('Byte', 'Byte'), msg['raw'][:2])
        msg['MsgType'], msg['TranNbr'] = values
        LOGGER.info('HiProtoCode, MsgType = <%x, %x>' %
                    (hdr['HiProtoCode'], msg['MsgType']))

        # PakBus Control Packets
        if hdr['HiProtoCode'] == 0 and msg['MsgType'] in (0x09, 0x89):
            msg = self.unpack_hello_response(msg)
        elif hdr['HiProtoCode'] == 0 and msg['MsgType'] == 0x81:
            msg = self.unpack_failure_response(msg)
        elif hdr['HiProtoCode'] == 0 and msg['MsgType'] == 0x8f:
            msg = self.unpack_getsettings_response(msg)
        # BMP5 Application Packets
        elif hdr['HiProtoCode'] == 1 and msg['MsgType'] == 0x89:
            msg = self.unpack_collectdata_response(msg)
        elif hdr['HiProtoCode'] == 1 and msg['MsgType'] == 0x97:
            msg = self.unpack_clock_response(msg)
        elif hdr['HiProtoCode'] == 1 and msg['MsgType'] == 0x98:
            msg = self.unpack_getprogstat_response(msg)
        elif hdr['HiProtoCode'] == 1 and msg['MsgType'] == 0x9d:
            msg = self.unpack_fileupload_response(msg)
        elif hdr['HiProtoCode'] == 1 and msg['MsgType'] == 0xa1:
            msg = self.unpack_pleasewait_response(msg)
        else:
            LOGGER.error('No implementation for <(%r, %r)> packet type'
                         % (hdr['HiProtoCode'], msg['MsgType']))
        return hdr, msg

    def get_hello_cmd(self):
        '''Create Hello Command packet.'''
        transac_id = self.transaction.next_id()
        hdr = self.pack_header(0x0, 0x1, self.RING)
        msg = self.encode_bin(['Byte', 'Byte', 'Byte', 'Byte', 'UInt2'],
                              [0x09, transac_id, 0x00, 0x02, 1800])
        return b''.join((hdr, msg)), transac_id

    def get_hello_response(self, transac_id):
        '''Create Hello Response packet.'''
        hdr = self.pack_header(0x0)
        msg = self.encode_bin(['Byte', 'Byte', 'Byte', 'Byte', 'UInt2'],
                              [0x89, transac_id, 0x00, 0x02, 1800])
        return b''.join([hdr, msg])

    def unpack_hello_response(self, msg):
        '''Create Hello Response packet.'''
        raw = msg['raw'][2:]
        values, size = self.decode_bin(['Byte', 'Byte', 'UInt2'], raw)
        msg['IsRouter'], msg['HopMetric'], msg['VerifyIntv'] = values
        return msg

    def unpack_failure_response(self, msg):
        '''Unpack Failure Response packet.'''
        (msg['ErrCode'],), size = self.decode_bin(['Byte'], msg['raw'][2:])
        return msg

    def get_getsettings_cmd(self):
        '''Create Getsettings Command packet.'''
        transac_id = self.transaction.next_id()
        hdr = self.pack_header(0x0)
        msg = self.encode_bin(['Byte', 'Byte'], [0x0f, transac_id])
        return b''.join([hdr, msg]), transac_id

    def unpack_getsettings_response(self, msg):
        '''Unpack Getsettings Response packet.'''
        (msg['Outcome'],), size = self.decode_bin(['Byte'], msg['raw'][2:])
        offset = size + 2

        # Generate dictionary of all settings
        msg['Settings'] = []
        if msg['Outcome'] == 0x01:
            values, size = self.decode_bin(['UInt2', 'Byte', 'Byte', 'Byte'],
                                           msg['raw'][offset:])
            msg['DeviceType'] = values[0]
            msg['MajorVersion'] = values[1]
            msg['MinorVersion'] = values[2]
            msg['MoreSettings'] = values[3]
            offset += size

            while offset < len(msg['raw']):
                # Get setting ID
                [SettingId], size = self.decode_bin(['UInt2'],
                                                    msg['raw'][offset:])
                offset += size
                if not msg['raw'][offset:]:
                    break
                # Get flags and length
                [bit16], size = self.decode_bin(['UInt2'], msg['raw'][offset:])
                LargeValue = (bit16 & 0x8000) >> 15
                ReadOnly = (bit16 & 0x4000) >> 14
                SettingLen = bit16 & 0x3FFF
                offset += size

                # Get value
                SettingValue = msg['raw'][offset:offset + SettingLen]
                offset += SettingLen
                item = {'SettingId': SettingId,
                        'SettingValue': SettingValue,
                        'LargeValue': LargeValue,
                        'ReadOnly': ReadOnly}
                msg['Settings'].append(item)
        return msg

    def get_collectdata_cmd(self, tablenbr, tabledefsig, mode=0x04, p1=0,
                            p2=0):
        '''Create Collect Data Command packet

        :param tablenbr: Table number that contain data.
        :param tabledefsig: Table definition signature.
        :param mode: Collection mode code (p1 and p2 will be used depending on
                    value).
        :param p1: 1st parameter used to specify what to collect (optional)
        :param p2: 2nd parameter used to specify what to collect (optional)
        '''
        transac_id = self.transaction.next_id()
        # BMP5 Application Packet
        hdr = self.pack_header(0x1)
        msg = self.encode_bin(['Byte', 'Byte', 'UInt2', 'Byte'],
                              [0x09, transac_id, self.security_code,
                               mode])
        # encode table number and signature
        msg += self.encode_bin(['UInt2', 'UInt2'], [tablenbr, tabledefsig])
        # add p1 and p2 according to collect mode
        if (mode == 0x04) | (mode == 0x05):
            # only P1 used (type UInt4)
            msg += self.encode_bin(['UInt4'], [p1])
        elif (mode == 0x06) | (mode == 0x08):
            # P1 and P2 used (type UInt4)
            msg += self.encode_bin(['UInt4', 'UInt4'], [p1, p2])
        elif mode == 0x07:
            # P1 and P2 used (type NSec)
            msg += self.encode_bin(['NSec', 'NSec'], [p1, p2])
        # add field list = all fields
        msg += self.encode_bin(['UInt2'], [0])
        return b''.join((hdr, msg)), transac_id

    def unpack_collectdata_response(self, msg):
        '''Unpack Collect Data Response body.'''
        (msg['RespCode'],), size = self.decode_bin(['Byte'], msg['raw'][2:])
        # return raw record data for later parsing
        msg['RecData'] = msg['raw'][size + 2:]
        return msg

    def get_clock_cmd(self, adjustment=(0, 0)):
        '''Create Clock Command packet.

        :param adjustment: Clock adjustment (seconds, nanoseconds).
        '''
        transac_id = self.transaction.next_id()
        # BMP5 Application Packet
        hdr = self.pack_header(0x1)
        msg = self.encode_bin(['Byte', 'Byte', 'UInt2', 'NSec'],
                              [0x17, transac_id, self.security_code,
                               adjustment])
        return b''.join((hdr, msg)), transac_id

    def unpack_clock_response(self, msg):
        '''Unpack Clock Response packet.'''
        values, size = self.decode_bin(['Byte', 'NSec'],  msg['raw'][2:])
        msg['RespCode'], msg['Time'] = values
        return msg

    def get_getprogstat_cmd(self):
        '''Create Get Programming Statistics Transaction packet.'''
        transac_id = self.transaction.next_id()
        # BMP5 Application Packet
        hdr = self.pack_header(0x1)
        msg = self.encode_bin(['Byte', 'Byte', 'UInt2'],
                              [0x18, transac_id, self.security_code])
        return b''.join((hdr, msg)), transac_id

    def unpack_getprogstat_response(self, msg):
        '''Unpack Get Programming Statistics Response packet.'''
        # Get response code
        (msg['RespCode'], ), size = self.decode_bin(['Byte'], msg['raw'][2:])

        # Get report data if RespCode == 0
        if msg['RespCode'] == 0:
            types = ['ASCIIZ', 'UInt2', 'ASCIIZ', 'ASCIIZ', 'Byte', 'ASCIIZ',
                     'UInt2', 'NSec', 'ASCIIZ']
            values, size = self.decode_bin(types, msg['raw'][3:])
            item = {'OSVer': values[0], 'OSSig': values[1],
                    'SerialNbr': values[2], 'PowUpProg': values[3],
                    'CompState': values[4], 'ProgName': values[5],
                    'ProgSig': values[6], 'CompTime': values[7],
                    'CompResult': values[8]}
            msg['Stats'] = item
        return msg

    def get_fileupload_cmd(self, filename, offset=0x00000000, swath=0x0200,
                           closeflag=0x01, transac_id=None):
        '''Create Fileupload Command packet.

        :param filename: File name as string
        :param offset: Byte offset into the file or fragment
        :param swath: Number of bytes to read
        :param closeflag: Flag if file should be closed after this transaction
        :param transac_id: Transaction number for continuing partial reads
                           (required by OS>=17!)
        '''
        if  transac_id is None:
            transac_id = self.transaction.next_id()
        # BMP5 Application Packet
        hdr = self.pack_header(0x1)
        types = ['Byte', 'Byte', 'UInt2', 'ASCIIZ', 'Byte', 'UInt4', 'UInt2']
        values = [0x1d, transac_id, self.security_code, filename, closeflag,
                  offset, swath]
        msg = self.encode_bin(types, values)
        return b''.join((hdr, msg)), transac_id

    def unpack_fileupload_response(self, msg):
        '''Unpack Fileupload Response packet.'''
        values, size = self.decode_bin(['Byte', 'UInt4'], msg['raw'][2:7])
        msg['RespCode'], msg['FileOffset'] = values
        msg['FileData'] = msg['raw'][7:]
        return msg

    def unpack_pleasewait_response(self, msg):
        '''Unpack PeaseWait Response packet.'''
        values, size = self.decode_bin(['Byte', 'UInt2'], msg['raw'][2:])
        msg['CmdMsgType'], msg['WaitSec'] = values
        return msg

    def get_bye_cmd(self):
        '''Create Bye Command packet.'''
        transac_id = self.transaction.next_id()
        # PakBus Control Packet
        hdr = self.pack_header(0x0, 0x0, self.FINISHED)
        msg = self.encode_bin(['Byte', 'Byte'], [0x0d, 0x0])
        return b''.join((hdr, msg)), transac_id

    def parse_filedir(self, data):
        '''Parse file directory format.'''
        offset = 0  # offset into raw buffer
        fd = {'files': []}  # initialize file directory structure
        [fd['DirVersion']], size = self.decode_bin(['Byte'], data[offset:])
        offset += size
        # Extract file entries
        while len(data) > offset:
            file_ = {}  # file description
            [filename], size = self.decode_bin(['ASCIIZ'], data[offset:])
            offset += size

            # end loop when file attribute list terminator reached
            if filename == '':
                break

            file_['FileName'] = filename
            values, size = self.decode_bin(['UInt4', 'ASCIIZ'], data[offset:])
            file_['FileSize'], file_['LastUpdate'] = values
            offset += size

            # Read file attribute list
            file_['Attribute'] = []
            # initialize file attribute list (up to 12)
            for i in range(12):
                [attribute], size = self.decode_bin(['Byte'], data[offset:])
                offset += size
                if attribute:
                    # append file attribute to list
                    file_['Attribute'].append(attribute)
                else:
                    break  # End of attribute list reached
            fd['files'].append(file_)  # add file entry to list
        return fd

    def parse_tabledef(self, raw):
        '''Parse table definition.'''
        tabledef = []  # List of table definitions
        offset = 0  # offset into raw buffer
        fslversion, size = self.decode_bin(['Byte'], raw[offset:])
        offset += size

        # Parse list of table definitions
        while offset < len(raw):

            tblhdr = {}  # table header
            tblfld = []  # table field definitions
            start = offset  # start of table definition

            # Extract table header data
            types = ['ASCIIZ', 'UInt4', 'Byte', 'NSec', 'NSec']
            values, size = self.decode_bin(types, raw[offset:])
            tblhdr['TableName'] = values[0]
            tblhdr['TableSize'] = values[1]
            tblhdr['TimeType'] = values[2]
            tblhdr['TblTimeInto'] = values[3]
            tblhdr['TblInterval'] = values[4]

            offset += size

            # Extract field definitions
            (fieldtype,), size = self.decode_bin(['Byte'], raw[offset:])
            offset += size
            while fieldtype != 0:
                fld = {}

                # Extract bits from fieldtype
                fld['ReadOnly'] = fieldtype >> 7  # only Bit 7

                # Convert fieldtype to ASCII FieldType (e.g. 'FP4') if possible
                # else return numerical value
                fld['FieldType'] = fieldtype & 0x7F  # only Bits 0..6
                for Type in self.DATATYPE.keys():
                    if fld['FieldType'] == self.DATATYPE[Type]['code']:
                        fld['FieldType'] = Type
                        break

                # Extract field name
                values, size = self.decode_bin(['ASCIIZ'], raw[offset:])
                fld['FieldName'] = values[0]
                offset += size

                # Extract AliasName list
                fld['AliasName'] = []
                aliasname = b'00'
                # Alias names list terminator reached
                while aliasname != b'':
                    values, size = self.decode_bin(['ASCIIZ'], raw[offset:])
                    aliasname = values[0]
                    offset += size
                    if aliasname != b'':
                        fld['AliasName'].append(aliasname)

                # Extract other mandatory field definition items
                types = ['ASCIIZ', 'ASCIIZ', 'ASCIIZ', 'UInt4', 'UInt4']
                values, size = self.decode_bin(types, raw[offset:])
                fld['Processing'] = values[0]
                fld['Units'] = values[1]
                fld['Description'] = values[2]
                fld['BegIdx'] = values[3]
                fld['Dimension'] = values[4]
                offset += size

                # Extract sub dimension (if any)
                fld['SubDim'] = []
                subdim = 1
                # sub-dimension list terminator reached
                while subdim != 0:
                    (subdim,), size = self.decode_bin(['UInt4'], raw[offset:])
                    offset += size
                    if subdim != 0:
                        fld['SubDim'].append(subdim)

                # append current field definition to list
                tblfld.append(fld)

                (fieldtype,), size = self.decode_bin(['Byte'], raw[offset:])
                offset += size
            # calculate table signature
            tblsig = self.compute_signature(raw[start:offset])

            # Append header, field list and signature to table definition list
            item = {'Header': tblhdr, 'Fields': tblfld, 'Signature': tblsig}
            tabledef.append(item)
        return tabledef

    def parse_collectdata(self, raw, tabledef, fieldnbr=[]):
        '''Parse data returned by Collectdata Response.'''
        offset = 0
        recdata = []  # output structure

        while offset < len(raw) - 1:
            frag = {}  # record fragment

            values, size = self.decode_bin(['UInt2', 'UInt4'], raw[offset:])
            frag['TableNbr'], frag['BegRecNbr'] = values
            offset += size

            # Provide table name
            t_frag = tabledef[frag['TableNbr'] - 1]
            tablename = t_frag['Header']['TableName']
            frag['TableName'] = tablename

            # Decode number of records (16 bits) or ByteOffset (32 Bits)
            (isoffset,), size = self.decode_bin(['Byte'], raw[offset:])
            frag['IsOffset'] = isoffset >> 7

            # Handle fragmented records
            if frag['IsOffset']:
                (byteoffset,), size = self.decode_bin(['UInt4'], raw[offset:])
                offset += size
                frag['ByteOffset'] = byteoffset & 0x7FFFFFFF
                frag['NbrOfRecs'] = None
                # Copy remaining raw data into RecFrag
                frag['RecFrag'] = raw[offset:-1]
                offset += len(frag['RecFrag'])

            # Handle complete records (standard case)
            else:
                (nbrofrecs,), size = self.decode_bin(['UInt2'], raw[offset:])
                offset += size
                frag['NbrOfRecs'] = nbrofrecs & 0x7FFF
                frag['ByteOffset'] = None

                # Get time of first record and time interval information
                interval = t_frag['Header']['TblInterval']
                if interval == (0, 0):  # event-driven table
                    timeofrec = None
                else:
                    # interval data, read time of first record
                    [timeofrec], size = self.decode_bin(['NSec'], raw[offset:])
                    offset += size

                # Loop over all records
                frag['RecFrag'] = []
                for n in range(frag['NbrOfRecs']):
                    record = {}

                    # Calculate current record number
                    record['RecNbr'] = frag['BegRecNbr'] + n

                    # Get TimeOfRec for interval data or event-driven tables
                    if timeofrec:  # interval data
                        next_timeofrec = (timeofrec[0] + n * interval[0],
                                          timeofrec[1] + n * interval[1])
                        record['TimeOfRec'] = nsec_to_time(next_timeofrec)
                    else:
                        # event-driven, time data precedes each record
                        values, size = self.decode_bin(['NSec'], raw[offset:])
                        record['TimeOfRec'] = values[0]
                        record['TimeOfRec'] = nsec_to_time(record['TimeOfRec'])
                        offset += size

                    # Loop over all field indices
                    record['Fields'] = {}
                    if fieldnbr:
                        # explicit field numbers provided
                        fields = fieldnbr
                    else:
                        # default: generate list of all fields in table
                        fields = t_frag['Fields']
                        fields = range(1, len(fields) + 1)

                    for field in fields:
                        fieldname = t_frag['Fields'][field - 1]['FieldName']
                        fieldtype = t_frag['Fields'][field - 1]['FieldType']
                        dimension = t_frag['Fields'][field - 1]['Dimension']
                        if fieldtype == 'ASCII':
                            values, size = self.decode_bin([fieldtype],
                                                           raw[offset:],
                                                           dimension)
                            record['Fields'][fieldname] = values[0]
                        else:
                            values, size = \
                                self.decode_bin(dimension * [fieldtype],
                                                raw[offset:])
                            record['Fields'][fieldname] = values[0]
                        offset += size
                    frag['RecFrag'].append(record)

            recdata.append(frag)

        # Get flag if more records exist
        (more_rec,), size = self.decode_bin(['Bool'], raw[offset:])
        return recdata, more_rec

    def __del__(self):
        self.link.close()

    def __str__(self):
        name = self.__class__.__name__
        return '<%s %s>' % (name, self.link)

    def __repr__(self):
        return '%s' % self.__str__()
