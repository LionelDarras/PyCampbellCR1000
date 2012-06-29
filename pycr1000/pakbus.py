# -*- coding: utf-8 -*-
'''
    pycr1000.pakbus
    ---------------

    Pakbus client

    Original Authors: Dietrich Feist, Max Planck, Jena Germany (PyPak)
    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

'''
from __future__ import division, unicode_literals

import struct
import string

from .logger import LOGGER
from .utils import Singleton


class Transaction(Singleton):
    id = 0

    def next_id(self):
        self.id += 1
        self.id &= 0xFF
        return self._id


class Pakbus(object):
    '''Inteface for a pakbus client. Defined here are all the
    methods for performing the related request methods.

    :param url: A `PyLink` connection URL.
    '''
    DATATYPE = {
        'Byte':     { 'code':  1, 'fmt': 'B',   'size': 1 },
        'UInt2':    { 'code':  2, 'fmt': '>H',  'size': 2 },
        'UInt4':    { 'code':  3, 'fmt': '>L',  'size': 4 },
        'Int1':     { 'code':  4, 'fmt': 'b',   'size': 1 },
        'Int2':     { 'code':  5, 'fmt': '>h',  'size': 2 },
        'Int4':     { 'code':  6, 'fmt': '>l',  'size': 4 },
        'FP2':      { 'code':  7, 'fmt': '>H',  'size': 2 },
        'FP3':      { 'code': 15, 'fmt': '3c',  'size': 3 },
        'FP4':      { 'code':  8, 'fmt': '4c',  'size': 4 },
        'IEEE4B':   { 'code':  9, 'fmt': '>f',  'size': 4 },
        'IEEE8B':   { 'code': 18, 'fmt': '>d',  'size': 8 },
        'Bool8':    { 'code': 17, 'fmt': 'B',   'size': 1 },
        'Bool':     { 'code': 10, 'fmt': 'B',   'size': 1 },
        'Bool2':    { 'code': 27, 'fmt': '>H',  'size': 2 },
        'Bool4':    { 'code': 28, 'fmt': '>L',  'size': 4 },
        'Sec':      { 'code': 12, 'fmt': '>l',  'size': 4 },
        'USec':     { 'code': 13, 'fmt': '6c',  'size': 6 },
        'NSec':     { 'code': 14, 'fmt': '>2l', 'size': 8 },
        'ASCII':    { 'code': 11, 'fmt': 's',   'size': None },
        'ASCIIZ':   { 'code': 16, 'fmt': 's',   'size': None },
        'Short':    { 'code': 19, 'fmt': '<h',  'size': 2 },
        'Long':     { 'code': 20, 'fmt': '<l',  'size': 4 },
        'UShort':   { 'code': 21, 'fmt': '<H',  'size': 2 },
        'ULong':    { 'code': 22, 'fmt': '<L',  'size': 4 },
        'IEEE4L':   { 'code': 24, 'fmt': '<f',  'size': 4 },
        'IEEE8L':   { 'code': 25, 'fmt': '<d',  'size': 8 },
        'SecNano':  { 'code': 23, 'fmt': '<2l', 'size': 8 },
    }

    # link state
    RING = 0x9
    READY = 0xA
    FINISHED = 0xB
    PAUSE = 0xC

    def __init__(self, link):
        self.link = link
        self.transaction = Transaction()

    def pack_header(self, dest_node, src_node, hi_proto, exp_more = 0x2,
                    link_state = None, hops = 0x0):
        '''Generate PakBus header.

        :param dest_node: Node ID of the message destination.
        :param src_node: Node ID of the message source
        :param hi_proto: Higher level protocol code (4 bits);
                     0x0: PakCtrl, 0x1: BMP5
        :param exp_more: Whether client should expect another packet (2 bits)
        :param link_state: Link state (4 bits)
        :param hops: Number of hops to destination (4 bits)
        '''
        priority = 0x1
        link_state = link_state or self.READY
        # bitwise encoding of header fields
        hdr = struct.pack('>4H',
            (link_state & 0xF) << 12   | (dest_node & 0xFFF),
            (exp_more & 0x3) << 14 | (priority & 0x3) << 12
            | (src_node & 0xFFF), (hi_proto & 0xF) << 12 | (dest_node & 0xFFF),
            (hops & 0xF) << 12     | (src_node & 0xFFF)
        )
        return hdr

    def compute_signature(self, buff, seed = 0xAAAA):
        '''Compute signature for PakBus packets.'''
        sig = seed
        for x in buff:
            x = ord(x)
            j = sig
            sig = (sig <<1) & 0x1FF
            if sig >= 0x100: sig += 1
            sig = ((((sig + (j >>8) + x) & 0xFF) | (j << 8))) & 0xFFFF
        return sig

    def compute_signatur_nullifier(self, sig):
        '''Calculate signature nullifier needed to create valid PakBus
        packets.'''
        nulb = nullif = b''
        for i in 1,2:
            sig = self.compute_signature(nulb, sig)
            sig2 = (sig<<1) & 0x1FF
            if sig2 >= 0x100: sig2 += 1
            nulb = chr((0x100 - (sig2 + (sig >> 8))) & 0xFF)
            nullif += nulb
        return nullif

    def quote(self, packet):
        '''Quote PakBus packet.'''
        packet = packet.replace(b'\xBC', b'\xBC\xDC')
        packet = packet.replace(b'\xBD', b'\xBC\xDD')
        return packet

    def unquote(self, packet):
        '''Unquote PakBus packet.'''
        packet = packet.replace(b'\xBC\xDD', b'\xBD')
        packet = packet.replace(b'\xBC\xDC', b'\xBC')
        return packet

    def get_hello_cmd(self, dest_node, src_node):
        '''Create Hello Command packet.'''
        transac_id = self.transaction.next_id()
        hdr = PakBus_hdr(dest_node, src_node, 0x0, 0x1, self.RING)
        msg = self.encode_bin(['Byte', 'Byte', 'Byte', 'Byte', 'UInt2'],
                         [0x09, transac_id, 0x00, 0x02, 1800])
        return b''.join([hdr, msg]), transac_id

    def get_hello_response(self, dest_node, src_node, transac_id):
        '''Create Hello Response packet.'''
        hdr = self.pack_header(dest_node, src_node, 0x0)
        msg = self.encode_bin(['Byte', 'Byte', 'Byte', 'Byte', 'UInt2'],
                         [0x89, transac_id, 0x00, 0x02, 1800])
        return b''.join([hdr, msg])

    def encode_bin(self, types, values):
        '''Encode binary data according to data type.'''
        buff = [] # buffer for binary data
        for i, type_ in enumerate(types):
            fmt = self.DATATYPE[type_]['fmt'] # get default format for type_
            value = values[i]

            if type_ == 'ASCIIZ':   # special handling: nul-terminated string
                value += '\0' # Add nul to end of string
                enc = struct.pack(str('%d%s') % (len(value), fmt), value)
            elif type_ == 'ASCII':   # special handling: fixed-length string
                enc = struct.pack(str('%d%s') % (len(value), fmt), value)
            elif type_ == 'NSec':   # special handling: NSec time
                enc = struct.pack(str(fmt), value[0], value[1])
            else:                  # default encoding scheme
                enc = struct.pack(str(fmt), value)

            buff.append(buff)
        return b''.join(buff)

    def ping_node(self, dest_node, src_node):
        '''Check if remote host is available.'''
        # send hello command and wait for response packet
        packet, transac_id = self.get_hello_cmd(dest_node, src_node)
        self.send(packet)
        hdr, msg = self.wait_packet(dest_node, src_node, transac_id)

        return msg

    def wait_packet(self, dest_node, src_node, transac_id):
        data = self.read()
        hdr, msg = self.decode_pkt(data)
        if hdr == {} or msg == {}:
            return hdr, msg

        # ignore packets that are not for us
        if hdr['DstNodeId'] != dest_node or hdr['SrcNodeId'] != src_node:
            return {}, {}

        # Respond to incoming hello command packets
        if msg['MsgType'] == 0x09:
            pkt = self.get_hello_response(hdr['SrcNodeId'], hdr['DstNodeId'],
                                          msg['TranNbr'])
            self.send(pkt)
            return self.wait_packet(dest_node, src_node)

        # Handle "please wait" packets
        if msg['TranNbr'] == transac_id and msg['MsgType'] == 0xa1:
            timeout = msg['WaitSec']
            time.sleep(timeout)
            return self.wait_packet(dest_node, src_node)

        # this should be the packet we are waiting for
        if msg['TranNbr'] == transac_id:
            return hdr, msg
