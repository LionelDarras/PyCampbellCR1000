# coding: utf8
'''
    PyCampbellCRX.tests.test_pakbus
    -------------------------------

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import datetime

from ..pakbus import PakBus
from ..utils import hex_to_bytes, bytes_to_hex
from .ressources import TABLEDEF


class FakeLink(object):
    def open(self):
        pass

    def close(self):
        pass

    def write(self, data):
        pass

    def read(self, data):
        pass


def test_pack_header():
    pakbus = PakBus(FakeLink())
    header = bytes_to_hex(pakbus.pack_header(0x0))
    assert header == 'A0 01 98 02 00 01 08 02'
    header = bytes_to_hex(pakbus.pack_header(0x0, 0x1, pakbus.RING))
    assert header == '90 01 58 02 00 01 08 02'
    header = bytes_to_hex(pakbus.pack_header(0x1))
    assert header == 'A0 01 98 02 10 01 08 02'
    header = bytes_to_hex(pakbus.pack_header(0x0, 0x0, pakbus.FINISHED))
    assert header == 'B0 01 18 02 00 01 08 02'


def test_compute_signature():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 18 02 00 01 9D 05 0D 00 00 00 6C 8E 14'
    packet = packet.replace(' ', '')
    assert not pakbus.compute_signature(hex_to_bytes(packet))
    packet = packet.replace('A8', 'D7')
    assert pakbus.compute_signature(hex_to_bytes(packet))


def test_compute_signature_nullifier():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 18 02 00 01 9D 05 0D 00 00 00 6C 8E 14'
    packet = packet.replace(' ', '')
    assert not pakbus.compute_signature(hex_to_bytes(packet))

    packet = packet.replace('A8', 'D7')
    sign = pakbus.compute_signature(hex_to_bytes(packet))
    assert sign
    nullifier = pakbus.compute_signature_nullifier(sign)
    assert nullifier == b'2h'


def test_get_hello_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_hello_cmd()[0])
    assert cmd == '90 01 58 02 00 01 08 02 09 01 00 02 07 08'


def test_get_hello_response():
    pakbus = PakBus(FakeLink())
    response = bytes_to_hex(pakbus.get_hello_response(1))
    assert response == 'A0 01 98 02 00 01 08 02 89 01 00 02 07 08'


def test_get_getsettings_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_getsettings_cmd()[0])
    assert cmd == 'A0 01 98 02 00 01 08 02 0F 02'


def test_get_collectdata_cmd():
    pakbus = PakBus(FakeLink())
    tablenbr = 2
    tabledefsig = 40615
    mode = 0x07
    p1 = (712142640, 0)
    p2 = (712142644, 0)
    cmd = pakbus.get_collectdata_cmd(tablenbr, tabledefsig, mode, p1, p2)[0]
    cmd = bytes_to_hex(cmd)
    assert cmd == 'A0 01 98 02 10 01 08 02 09 03 00 00 07 00 02 9E A7 2A'\
                  ' 72 6F 30 00 00 00 00 2A 72 6F 34 00 00 00 00 00 00'


def test_get_clock_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_clock_cmd()[0])
    assert cmd == 'A0 01 98 02 10 01 08 02 17 04 00 00 00 00 00 00 00 00 00 00'


def test_get_getprogstat_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_getprogstat_cmd()[0])
    assert cmd == 'A0 01 98 02 10 01 08 02 18 05 00 00'


def test_get_fileupload_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_fileupload_cmd('Filename')[0])
    assert cmd == 'A0 01 98 02 10 01 08 02 1D 06 00 00 46 69 6C 65 6E 61 6D'\
                  ' 65 00 01 00 00 00 00 02 00'


def test_get_bye_cmd():
    pakbus = PakBus(FakeLink())
    cmd = bytes_to_hex(pakbus.get_bye_cmd()[0])
    assert cmd == 'B0 01 18 02 00 01 08 02 0D 00'


def test_hello_response():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 08 02 00 01 89 02 00 01 FF FF 24 57'
    hdr, msg = pakbus.decode_packet(hex_to_bytes(packet.replace(' ', '')))
    assert msg['HopMetric'] == 1
    assert msg['VerifyIntv'] == 65535
    assert msg['TranNbr'] == 2
    assert msg['MsgType'] == 137
    assert msg['IsRouter'] == 0


def test_parse_filedir():
    pakbus = PakBus(FakeLink())
    data = '01 43 50 55 3A 00 00 07 6E 00 00 00 43 50 55 3A 74 65 6D'\
           '70 6C 61 74 65 65 78 61 6D 70 6C 65 2E 63 72 31 00 00 00'\
           '02 CB 32 30 31 32 2D 30 33 2D 31 36 20 31 33 3A 32 32 3A'\
           '34 32 00 00 43 50 55 3A 43 52 31 30 30 30 5F 4C 41 42 4F'\
           '2E 43 52 31 00 00 00 0C 5E 32 30 31 32 2D 30 35 2D 32 33'\
           '20 31 31 3A 32 35 3A 33 38 00 01 02 00'

    files = pakbus.parse_filedir(hex_to_bytes(data))['files']

    files[0]['FileName'] == b'CPU:'
    files[1]['LastUpdate'] == b'2012-03-16 13:22:42'
    files[1]['FileSize'] == 715
    files[1]['FileName'] == b'CPU:templateexample.cr1'


def test_parse_tabledef():
    pakbus = PakBus(FakeLink())
    tabledef = pakbus.parse_tabledef(hex_to_bytes(TABLEDEF))
    assert tabledef[0]['Header']['TableName'] == b'Status'
    assert tabledef[0]['Signature'] == 14472


def test_parse_collectdata():
    pakbus = PakBus(FakeLink())
    tabledef = pakbus.parse_tabledef(hex_to_bytes(TABLEDEF))
    raw = '00 02 00 01 5B DC 00 06 2A 72 AB 30 00 00 00 00 45 51 13'\
          '90 09 CA 09 B1 09 CB 09 DE A7 E0 BE AC 47 74 24 BD 45 51'\
          '13 90 09 CA 09 B1 09 CB 09 DE A7 DB BE A4 47 50 24 C7 45'\
          '51 13 90 09 CA 09 B1 09 CB 09 DE A7 D5 BE B0 47 6F 24 BF'\
          '45 51 13 90 09 CB 09 B1 09 CB 09 DE A7 B0 BE B6 47 4A 24'\
          'C2 45 51 13 90 09 CA 09 B1 09 CB 09 DE A7 D0 BE AD 47 CB'\
          '24 BD 45 51 13 90 09 CA 09 B1 09 CB 09 DE A7 C8 BE D4 47'\
          '64 24 B3 00'
    data, more = pakbus.parse_collectdata(hex_to_bytes(raw), tabledef)

    assert more == 0
    assert data[0]['IsOffset'] == 0
    assert data[0]['TableName'] == b'Table1'
    assert data[0]['BegRecNbr'] == 89052
    assert data[0]['RecFrag'][0]['Fields'][b'CurSensor1_mVolt_Avg'] == 2506.0
    assert data[0]['RecFrag'][0]['Fields'][b'Batt_Volt_Avg'] == 13.61
    dtime = datetime.datetime(2012, 7, 26, 13, 40)
    assert data[0]['RecFrag'][0]['TimeOfRec'] == dtime


def test_getprogstat_response():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 18 02 00 01 98 05 00 43 52 31 30 30 30 2E 53'\
             '74 64 2E 32 34 00 30 00 45 34 36 36 38 00 43 50 55 3A 43'\
             '52 31 30 30 30 5F 4C 41 42 4F 2E 43 52 31 00 01 43 50 55'\
             '3A 43 52 31 30 30 30 5F 4C 41 42 4F 2E 43 52 31 00 0B B1'\
             '2A 61 51 8E 00 98 96 80 43 50 55 3A 43 52 31 30 30 30 5F'\
             '4C 41 42 4F 2E 43 52 31 20 2D 2D 20 43 6F 6D 70 69 6C 65'\
             '64 20 69 6E 20 50 69 70 65 6C 69 6E 65 4D 6F 64 65 2E 0D'\
             '0A 00 D3 41'
    packet = pakbus.unquote(hex_to_bytes(packet.replace(' ', '')))
    hdr, msg = pakbus.decode_packet(packet)
    assert msg['MsgType'] == 152
    assert msg['RespCode'] == 0
    assert msg['Stats']['ProgSig'] == 2993
    assert msg['Stats']['CompState'] == 1
    assert msg['Stats']['OSVer'] == b'CR1000.Std.24'
    assert msg['Stats']['PowUpProg'] == b'CPU:CR1000_LABO.CR1'
    assert msg['Stats']['OSSig'] == 12288
    assert msg['Stats']['CompTime'] == (711020942, 10000000)
    assert msg['Stats']['CompResult'] == b'CPU:CR1000_LABO.CR1 -- Compiled '\
                                         b'in PipelineMode.\r\n'
    assert msg['Stats']['ProgName'] == b'CPU:CR1000_LABO.CR1'
    assert msg['Stats']['SerialNbr'] == b'E4668'


def test_clock_response():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 18 02 00 01 97 05 00 2A 72 73 0A 3B 02 33 80 8D 6D'
    packet = pakbus.unquote(hex_to_bytes(packet.replace(' ', '')))
    hdr, msg = pakbus.decode_packet(packet)
    assert msg['MsgType'] == 151
    assert msg['Time'] == (712143626, 990000000)


def test_collectdata_response():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 18 02 00 01 9D 06 00 00 00 00 00 01 53 74 61'\
             '74 75 73 00 00 00 00 01 0E 00 00 00 00 00 00 00 00 00 00'\
             '00 00 00 00 00 00 8B 4F 53 56 65 72 73 69 6F 6E 00 00 00'\
             '00 00 00 00 00 01 00 00 00 20 00 00 00 20 00 00 00 00 8B'\
             '4F 53 44 61 74 65 00 00 00 00 00 00 00 00 01 00 00 00 08'\
             '00 00 00 08 00 00 00 00 86 4F 53 53 69 67 6E 61 74 75 72'\
             '65 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 00 8B'\
             '53 65 72 69 61 6C 4E 75 6D 62 65 72 00 00 00 00 00 00 00'\
             '00 01 00 00 00 08 00 00 00 08 00 00 00 00 8B 52 65 76 42'\
             '6F 61 72 64 00 00 00 00 00 00 00 00 01 00 00 00 08 00 00'\
             '00 08 00 00 00 00 0B 53 74 61 74 69 6F 6E 4E 61 6D 65 00'\
             '00 00 00 00 00 00 00 01 00 00 00 40 00 00 00 40 00 00 00'\
             '00 06 50 61 6B 42 75 73 41 64 64 72 65 73 73 00 00 00 00'\
             '00 00 00 00 01 00 00 00 01 00 00 00 00 8B 50 72 6F 67 4E'\
             '61 6D 65 00 00 00 00 00 00 00 00 01 00 00 00 40 00 00 00'\
             '40 00 00 00 00 8E 53 74 61 72 74 54 69 6D 65 00 00 00 64'\
             '61 74 65 00 00 00 00 00 01 00 00 00 01 00 00 00 00 86 52'\
             '75 6E 53 69 67 6E 61 74 75 72 65 00 00 00 00 00 00 00 00'\
             '01 00 00 00 01 00 00 00 00 86 50 72 6F 67 53 69 67 6E 61'\
             '74 75 72 65 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00'\
             '00 00 89 42 61 74 74 65 72 79 00 00 00 56 6F 6C 74 73 00'\
             '00 00 00 00 01 00 00 00 01 00 00 00 00 89 50 61 6E 65 6C'\
             '54 65 6D 70 00 00 00 44 65 67 43 00 00 00 00 00 01 00 00'\
             '00 01 00 00 00 00 06 57 61 74 63 68 64 6F 67 45 72 72 6F'\
             '72 73 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 00'\
             '89 4C 69 74 68 69 75 6D 42 61 74 74 65 72 79 00 00 00 00'\
             '00 00 00 00 01 00 00 00 01 00 00 00 00 06 4C 6F 77 31 32'\
             '56 43 6F 75 6E 74 00 00 00 00 00 00 00 00 2A 3E'
    packet = pakbus.unquote(hex_to_bytes(packet.replace(' ', '')))
    hdr, msg = pakbus.decode_packet(packet)
    assert msg['MsgType'] == 157
    assert msg['FileOffset'] == 0
    assert msg['RespCode'] == 0

    filedata = pakbus.parse_filedir(msg['FileData'])
    assert filedata['DirVersion'] == 1
    assert filedata['files'][0]['Attribute'] == []
    assert filedata['files'][0]['FileSize'] == 1
    assert filedata['files'][0]['FileName'] == b'Status'


def test_getsettings_response():
    pakbus = PakBus(FakeLink())
    packet = 'A8 02 10 01 08 02 00 01 8F 05 01 00 0C 05 00 01 00 00 40 0E'\
             '43 52 31 30 30 30 2E 53 74 64 2E 32 34 00 00 01 40 04 45 00'\
             '12 3C 00 02 00 05 4C 41 42 4F 00 00 03 00 02 00 01 00 04 00'\
             '06 00 00 00 00 00 00 00 56 00 04 FF FF FF FF 00 05 00 01 00'\
             '00 06 00 02 00 32 00 53 00 00 00 07 00 04 FF FF 6A 00 00 08'\
             '00 04 FF FE 3E 00 00 49 00 04 00 01 C2 00 00 0C 00 04 00 00'\
             '00 00 00 0D 00 04 00 00 00 00 00 0E 00 04 00 00 00 00 00 0F'\
             '00 04 00 00 00 00 00 11 00 02 00 00 00 12 00 02 00 00 00 14'\
             '00 02 00 00 00 15 00 02 00 00 00 4A 00 02 00 00 00 4B 00 02'\
             '00 00 00 16 00 02 00 00 00 17 00 02 00 00 00 18 00 02 00 00'\
             '00 19 00 02 00 00 00 1B 00 02 00 00 00 1C 00 02 00 00 00 1E'\
             '00 02 00 00 00 1F 00 02 00 00 00 4D 00 02 00 00 00 4E 00 02'\
             '00 00 00 20 00 02 00 00 00 21 00 02 00 00 00 22 00 02 00 00'\
             '00 23 00 02 00 00 00 25 00 00 00 26 00 00 00 28 00 00 00 29'\
             '00 00 00 50 00 00 00 51 00 00 00 2A 00 00 00 2B 00 00 00 2C'\
             '00 00 00 2D 00 00 00 2F 00 00 00 30 40 07 01 08 02 08 02 13'\
             '88 00 37 00 04 00 00 00 00 00 32 00 00 00 54 00 01 00 00 31'\
             '00 02 03 E8 00 3D 00 05 00 00 00 00 00 00 33 00 08 30 2E 30'\
             '2E 30 2E 30 00 00 35 00 0E 32 35 35 2E 32 35 35 2E 32 35 35'\
             '2E 30 00 00 34 00 08 30 2E 30 2E 30 2E 30 00 00 59 00 08 30'\
             '2E 30 2E 30 2E 30 00 00 5B 00 0E 32 35 35 2E 32 35 35 2E 32'\
             '35 35 2E 30 00 00 5A 00 08 30 2E 30 2E 30 2E 30 00 00 42 00'\
             '08 00 00 00 00 00 00 00 00 00 38 00 15 00 30 2E 30 2E 30 2E'\
             '30 00 00 00 00 00 43 4F 4E 4E 45 43 54 00 00 36 00 02 1A 81'\
             '00 41 00 00 00 55 00 01 00 00 3F 00 02 00 50 00 40 00 02 00'\
             '15 00 3A 00 0C 61 6E 6F 6E 79 6D 6F 75 73 00 2A 00 00 3C 00'\
             '01 FF 00 57 00 02 00 00 00 58 00 03 00 00 00 00 39 00 03 00'\
             '00 00 00 3B 40 01 00 5D 1B'
    packet = pakbus.unquote(hex_to_bytes(packet.replace(' ', '')))
    hdr, msg = pakbus.decode_packet(packet)
    assert msg['MsgType'] == 143
    assert msg['DeviceType'] == 12
    assert msg['MoreSettings'] == 1
    assert msg['TranNbr'] == 5
    assert msg['Outcome'] == 1
    assert msg['MajorVersion'] == 5
    assert msg['MinorVersion'] == 0
    assert msg['Settings'][0]['SettingId'] == 0
    assert msg['Settings'][0]['SettingValue'] == b'CR1000.Std.24\x00'


def test_fileupload_response():
    '''Tests fileupload response.'''
    pakbus = PakBus(FakeLink())
    packet = 'A8021001180200019D0500000000000153746174757300000000010'\
             'E000000000000000000000000000000008B4F5356657273696F6E00'\
             '00000000000000010000002000000020000000008B4F53446174650'\
             '00000000000000001000000080000000800000000864F535369676E'\
             '617475726500000000000000000100000001000000008B536572696'\
             '16C4E756D6265720000000000000000010000000800000008000000'\
             '008B526576426F61726400000000000000000100000008000000080'\
             '00000000B53746174696F6E4E616D65000000000000000001000000'\
             '4000000040000000000650616B42757341646472657373000000000'\
             '00000000100000001000000008B50726F674E616D65000000000000'\
             '0000010000004000000040000000008E537461727454696D6500000'\
             '06461746500000000000100000001000000008652756E5369676E61'\
             '7475726500000000000000000100000001000000008650726F67536'\
             '9676E61747572650000000000000000010000000100000000894261'\
             '7474657279000000566F6C747300000000000100000001000000008'\
             '950616E656C54656D70000000446567430000000000010000000100'\
             '000000065761746368646F674572726F72730000000000000000010'\
             '000000100000000894C69746869756D426174746572790000000000'\
             '000000010000000100000000064C6F77313256436F756E740000000'\
             '0000000007E4B'
    hdr, msg = pakbus.decode_packet(hex_to_bytes(packet))
    assert hdr['Priority'] == 1
    assert hdr['HiProtoCode'] == 1
    assert hdr['ExpMoreCode'] == 0
    assert hdr['SrcNodeId'] == 1
    assert hdr['HopCnt'] == 0
    assert hdr['DstNodeId'] == 2050
    assert hdr['SrcPhyAddr'] == 1
    assert hdr['DstPhyAddr'] == 2050
    assert hdr['LinkState'] == 10

    assert msg['FileOffset'] == 0
    assert msg['RespCode'] == 0
    assert msg['TranNbr'] == 5
    assert msg['MsgType'] == 157

    filedata = pakbus.parse_filedir(msg['FileData'])
    assert filedata['DirVersion'] == 1
    assert filedata['files'][0]['Attribute'] == []
    assert filedata['files'][0]['FileSize'] == 1
    assert filedata['files'][0]['FileName'] == b'Status'
