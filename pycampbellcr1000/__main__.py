# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.main
    ---------------------

    The public API and command-line interface to PyCampbellCR1000.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
import os
import argparse

from datetime import datetime

# Make sure the logger is configured early:
from . import VERSION
from .logger import active_logger
from .compat import stdout
from .device import CR1000
from .utils import csv_to_dict, ListDict


NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def gettime_cmd(args, device):
    '''Gettime command.'''
    print("%s" % (device.gettime()))


def settime_cmd(args, device):
    '''Settime command.'''
    old_time = device.gettime()
    device.settime(datetime.strptime(args.datetime, "%Y-%m-%d %H:%M"))
    print("Old Time : %s" % old_time.strftime("%Y-%m-%d %H:%M"))
    print("Current Time : %s" % device.gettime().strftime("%Y-%m-%d %H:%M"))


def getprogstat_cmd(args, device):
    '''Getprogstat command.'''
    data = device.getprogstat()
    for key in data.keys():
        print("%s : %s" % (key, ("%s" % data[key]).strip('\r\n')))


def getsettings_cmd(args, device):
    '''Getsettings command.'''
    args.delim = args.delim.decode("string-escape")
    data = device.settings
    for item in data:
        item["SettingValue"] = repr(item["SettingValue"])
    args.output.write("%s" % data.to_csv(delimiter=args.delim))


def listfiles_cmd(args, device):
    '''Listfiles command.'''
    for filename in device.list_files():
        print(filename.decode('utf-8'))


def getfile_cmd(args, device):
    '''Getfile command.'''
    args.output.write("%s" % device.getfile(args.filename.decode('utf-8')))


def listtables_cmd(args, device):
    '''Listtables command.'''
    for tablename in device.list_tables():
        print(tablename.decode('utf-8'))


def getdata_cmd(args, device, header=True, exclude_first=False):
    '''Getdata command.'''
    args.delim = args.delim.decode("string-escape")
    if args.start is not None:
        args.start = datetime.strptime(args.start, "%Y-%m-%d %H:%M")
    if args.stop is not None:
        args.stop = datetime.strptime(args.stop, "%Y-%m-%d %H:%M")
    print("Your download is starting.")
    total_records = 0
    generator = device.get_data_generator(args.table, args.start, args.stop)
    for i, records in enumerate(generator):
        if exclude_first:
            records = ListDict(records[1:])
            exclude_first = False
        total_records += len(records)
        print("Packet %d with %d records" % (i, len(records)))
        args.output.write("%s" % records.to_csv(delimiter=args.delim,
                                                header=header))
        if header:
            header = False

    print("---------------------------")
    if total_records == 0:
        print("No new records were found﻿")
    elif total_records == 1:
        print("1 new record was found")
    else:
        print("%d new records were found" % total_records)


def update_cmd(args, device):
    '''Update command.'''
    # create file if not exist
    with file(args.db, 'a'):
        os.utime(args.db, None)
    with open(args.db, 'r') as file_db:
        db = csv_to_dict(file_db, delimiter=args.delim)
    with open(args.db, 'a') as file_db:
        args.start = None
        args.stop = None
        if len(db) > 0:
            db = db.sorted_by("Datetime", reverse=True)
            format = "%Y-%m-%d %H:%M:%S"
            start_date = datetime.strptime(db[0]['Datetime'], format)
            # exclude this record
            args.start = start_date.strftime("%Y-%m-%d %H:%M")
            args.output = file_db
            getdata_cmd(args, device, header=False, exclude_first=True)
        else:
            args.output = file_db
            getdata_cmd(args, device, header=True)


def get_cmd_parser(cmd, subparsers, help, func):
    '''Make a subparser command.'''
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = subparsers.add_parser(cmd, help=help, description=help,
                                   formatter_class=formatter_class)
    parser.add_argument('--timeout', default=10.0, type=float,
                        help="Connection link timeout")
    parser.add_argument('--src', default=0x802, type=int,
                        help='Source node ID')
    parser.add_argument('--dest', default=0x001, type=int,
                        help='Destination node ID')
    parser.add_argument('--code', default=0x0000, type=int,
                        help='Datalogger security code')
    parser.add_argument('--debug', action="store_true", default=False,
                        help='Display log')
    parser.add_argument('url', action="store",
                        help="Specifiy URL for connection link. "
                        "E.g. tcp:iphost:port "
                        "or serial:/dev/ttyUSB0:19200:8N1")
    parser.set_defaults(func=func)
    return parser


def main():
    '''Parse command-line arguments and execute CR1000 command.'''

    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(prog='pycr1000',
                                     description='Communication tools for '
                                                 'Campbell CR1000-type '
                                                 'Datalogger',
                                     formatter_class=formatter_class)

    parser.add_argument('--version', action='version',
                        version='PyCR1000 version %s' % VERSION,
                        help='Print PyCR1000’s version number and exit.')

    subparsers = parser.add_subparsers(title='The PyCR1000 commands')
    # gettime command
    subparser = get_cmd_parser('gettime', subparsers,
                               help='Print the current datetime of the'
                                    ' datalogger.',
                               func=gettime_cmd)

    # settime command
    subparser = get_cmd_parser('settime', subparsers,
                               help='Set the given datetime argument on the'
                                    ' datalogger.',
                               func=settime_cmd)
    subparser.add_argument('datetime', help='The chosen datetime value. '
                                            '(like : "%s")' % NOW)

    # getprogstat command
    subparser = get_cmd_parser('getprogstat', subparsers,
                               help='Retrieve available programming '
                                    'statistics information from the '
                                    'datalogger.',
                               func=getprogstat_cmd)

    # getsettings command
    subparser = get_cmd_parser('getsettings', subparsers,
                               help='Retrieve the datalogger settings.',
                               func=getsettings_cmd)
    subparser.add_argument('--output', action='store', default=stdout,
                           type=argparse.FileType('w', 0),
                           help='Filename where output is written')
    subparser.add_argument('--delim', action='store', default=",",
                           help='CSV char delimiter')

    # listfiles command
    subparser = get_cmd_parser('listfiles', subparsers,
                               help='List all files stored in the datalogger.',
                               func=listfiles_cmd)

    # getfile command
    subparser = get_cmd_parser('getfile', subparsers,
                               help='Get the file content from the '
                                    'datalogger.',
                               func=getfile_cmd)
    subparser.add_argument('filename', action="store",
                           help="Filename to be downloaded.")
    subparser.add_argument('output', action='store',
                           type=argparse.FileType('w', 0),
                           help='Filename where output is written')

    # listtables command
    subparser = get_cmd_parser('listtables', subparsers,
                               help='List all tables stored in '
                                    'the datalogger.',
                               func=listtables_cmd)

    # getdata command
    subparser = get_cmd_parser('getdata', subparsers,
                               help='Extract data from the datalogger '
                                    'between start datetime and stop datetime.'
                                    'By default the entire contents will be '
                                    'downloaded.',
                               func=getdata_cmd)
    subparser.add_argument('table', action="store",
                           help="The table name used for data collection")
    subparser.add_argument('output', action='store',
                           type=argparse.FileType('w', 0),
                           help='Filename where output is written')
    subparser.add_argument('--start', help='The beginning datetime record '
                                           '(like : "%s")' % NOW)
    subparser.add_argument('--stop', help='The stopping datetime record '
                                          '(like : "%s")' % NOW)
    subparser.add_argument('--delim', action='store', default=",",
                           help='CSV char delimiter')

    # update command
    subparser = get_cmd_parser('update', subparsers,
                               help='Update CSV database records by getting '
                               'automatically new records.',
                               func=update_cmd)
    subparser.add_argument('table', action="store",
                           help="The table name used for data collection")
    subparser.add_argument('--delim', action="store", default=",",
                           help='CSV char delimiter')
    subparser.add_argument('db', action="store", help='The CSV file database')

    # Parse argv arguments
    args = parser.parse_args()

    if args.debug:
        active_logger()
        device = CR1000.from_url(args.url, args.timeout, args.dest, args.src,
                                 args.code)
        args.func(args, device)
    else:
        try:
            device = CR1000.from_url(args.url, args.timeout, args.dest,
                                     args.src, args.code)
            args.func(args, device)
        except Exception as e:
            parser.error('%s' % e)


if __name__ == '__main__':
    main()
