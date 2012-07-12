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
#from .compat import stdout


NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def main():
    '''Parse command-line arguments and execute CR1000 command.'''
    parser = argparse.ArgumentParser(prog='PyCR1000',
                                     description='Communication tools for '
                                                 'Campbell CR1000-type '
                                                 'Datalogger')

    parser.add_argument('--version', action='version',
                        version='PyCR1000 version %s' % VERSION,
                        help='Print PyCR1000’s version number and exit.')

    args = parser.parse_args()
    if args.debug:
        active_logger()

if __name__ == '__main__':
    main()
