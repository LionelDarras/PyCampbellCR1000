# -*- coding: utf-8 -*-
'''
    pycr1000
    --------

    The public API and command-line interface to PyVPDriver.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

'''
import os
import argparse

from datetime import datetime

# Make sure the logger is configured early:
from . import VERSION
from .logger import active_logger
from .compat import stdout

NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def main():
    '''Parse command-line arguments and execute CR1000 command.'''
    parser = argparse.ArgumentParser(prog='pycr1000',
                        description='CR1000 communication tools')

    parser.add_argument('--version', action='version',
                        version='PyCR1000 version %s' % VERSION,
                        help='Print PyCR1000’s version number and exit.')

    args = parser.parse_args()


if __name__ == '__main__':
    main()
