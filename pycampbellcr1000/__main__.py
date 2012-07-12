# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.main
    ---------------------

    The public API and command-line interface to PyCampbellCR1000.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
import argparse

from datetime import datetime

# Make sure the logger is configured early:
from . import VERSION
from .logger import active_logger
from .compat import stdout
from .device import CR1000


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
    pass


def listfiles_cmd(args, device):
    pass


def listtables_cmd(args, device):
    pass


def getdata_cmd(args, device):
    pass


def update_cmd(args, device):
    pass



def get_cmd_parser(cmd, subparsers, help, func):
    '''Make a subparser command.'''
    parser = subparsers.add_parser(cmd, help=help, description=help)
    parser.add_argument('--timeout', default=10.0, type=float,
                        help="Connection link timeout")
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

    parser = argparse.ArgumentParser(prog='PyCR1000',
                                     description='Communication tools for '
                                                 'Campbell CR1000-type '
                                                 'Datalogger')

    parser.add_argument('--version', action='version',
                        version='PyCR1000 version %s' % VERSION,
                        help='Print PyCR1000’s version number and exit.')

    subparsers = parser.add_subparsers(title='The PyVantagePro commands')
    # gettime command
    subparser = get_cmd_parser('gettime', subparsers,
                               help='Print the current datetime of the'
                                    ' station.',
                               func=gettime_cmd)

    # settime command
    subparser = get_cmd_parser('settime', subparsers,
                               help='Set the given datetime argument on the'
                                    ' station.',
                               func=settime_cmd)
    subparser.add_argument('datetime', help='The chosen datetime value. '
                                            '(like : "%s")' % NOW)

    # getprogstat command
    subparser = get_cmd_parser('getprogstat', subparsers,
                               help='Retrieves available programming '
                                    'statistics information from the '
                                    'datalogger.',
                               func=getprogstat_cmd)

    # getsettings command
    subparser = get_cmd_parser('getsettings', subparsers,
                               help='Retrieves the datalogger settings.',
                               func=getsettings_cmd)

    # listfiles command
    subparser = get_cmd_parser('listfiles', subparsers,
                               help='List all files stored in the datalogger.',
                               func=listfiles_cmd)

    # listtables command
    subparser = get_cmd_parser('listtables', subparsers,
                               help='List all tables stored in the datalogger.',
                               func=listtables_cmd)

    # getdata command
    subparser = get_cmd_parser('getdata', subparsers,
                               help='Extract data from the datalogger '
                                    'between start datetime and stop datetime.'
                                    'By default the entire contents of the '
                                    'data archive will be downloaded.',
                               func=getdata_cmd)
    subparser.add_argument('--table', action="store",
                        help="The table name used for data collection")
    subparser.add_argument('--output', action='store', default=stdout,
                           type=argparse.FileType('w', 0),
                           help='Filename where output is written')
    subparser.add_argument('--start', help='The beginning datetime record '
                                           '(like : "%s")' % NOW)
    subparser.add_argument('--stop', help='The stopping datetime record '
                                          '(like : "%s")' % NOW)
    subparser.add_argument('--delim', action='store', default=",",
                           help='CSV char delimiter')

#    # update command
#    subparser = get_cmd_parser('update', subparsers,
#                               help='Update CSV database records with getting '
#                                    'automatically new archive records.',
#                               func=update_cmd)
#    subparser.add_argument('--delim', action="store", default=",",
#                           help='CSV char delimiter')
#    subparser.add_argument('db', action="store", help='The CSV file database')

    # Parse argv arguments
    args = parser.parse_args()

    if args.debug:
        active_logger()
        device = CR1000.from_url(args.url, args.timeout)
        args.func(args, device)
    else:
        try:
            device = CR1000.from_url(args.url, args.timeout)
            args.func(args, device)
        except Exception as e:
            parser.error('%s' % e)


if __name__ == '__main__':
    main()
